# -*- coding: utf-8 -*-
"""
把一堆 png 变成一套主题（自定义指针的主入口，也就是 tools/make_theme.py）。

素材要求：
    * 放在 --src 目录里，按角色名命名：arrow.png / hand.png / ibeam.png ...
      角色名见 cursorlab/build.py 的 ROLE_KEY（17 个）
    * 动画指针给一组帧：wait_0.png wait_1.png ... 或 wait/ 子目录
    * 透明底最好；白底也行，会自动抠（theme.json 的 cut_background）

命令行等价形式：
    python -m cursorlab.theme --name my-cat --src assets/my-cat
    python -m cursorlab.theme --name my-cat --src assets/my-cat --hot arrow=2,2
"""

import argparse
import json
import os
import re
import shutil
import sys

from .build import ROLE_KEY, base_dir, build_theme, load_themes, package
from .cartoon import SPRITES
from .encode import DESIGN

# 角色默认热点（沿用像素小猫的手感，可在 hotspot.html 里改）
DEFAULT_HOT = {k: list(v["hot"]) for k, v in SPRITES.items()}

ROOT = base_dir()
THEMES_DIR = os.path.join(ROOT, "themes")

MAX_ROLE_FRAMES = 64


def _natural(name):
    """wait_2.png 要排在 wait_10.png 前面 —— sorted() 会按字符串排成 10, 2。"""
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", name)]


def find_frames(src, key):
    """找某个角色的动画帧：key/ 子目录优先，其次 key_*.png。没有就返回 None。"""
    sub = os.path.join(src, key)
    if os.path.isdir(sub):
        fs = sorted((f for f in os.listdir(sub) if f.lower().endswith(".png")),
                    key=_natural)
        if fs:
            return ["%s/%s" % (key, f) for f in fs]
    fs = sorted((f for f in os.listdir(src)
                 if f.lower().endswith(".png") and f.lower().startswith(key + "_")),
                key=_natural)
    return fs or None


def parse_hotspots(items, default=None):
    """解析 --hot 的 "arrow=2,2" 形式，返回 {角色: [x, y]}。"""
    hot = {k: list(v) for k, v in (default or DEFAULT_HOT).items()}
    for item in items or []:
        if "=" not in item:
            raise ValueError("--hot 要写成 角色=x,y（例：arrow=2,2），收到 %r" % item)
        k, v = item.split("=", 1)
        k = k.strip()
        if k not in ROLE_KEY.values():
            raise ValueError("--hot 里的角色 %r 不认识（可选：%s）"
                             % (k, ", ".join(sorted(ROLE_KEY.values()))))
        parts = [p for p in v.replace(" ", "").split(",") if p]
        if len(parts) != 2:
            raise ValueError("--hot %s= 需要两个数（x,y），收到 %r" % (k, v))
        try:
            x, y = (float(p) for p in parts)
        except ValueError:
            raise ValueError("--hot %s= 里有非数字: %r" % (k, v)) from None
        for axis, val in (("x", x), ("y", y)):
            if not 0.0 <= val <= DESIGN:
                raise ValueError("--hot %s 的 %s=%g 超出 0..%g 的设计网格"
                                 % (k, axis, val, DESIGN))
        hot[k] = [x, y]
    return hot


def collect_roles(src, hotspot):
    """按 ROLE_KEY 收集素材，返回 ({角色: 配置}, 拷贝张数, 缺的角色)。"""
    roles = {}
    copied = 0
    for key in ROLE_KEY.values():
        src_file = key + ".png"
        frames = find_frames(src, key)
        if frames:
            if len(frames) > MAX_ROLE_FRAMES:
                raise ValueError("角色 %s 有 %d 帧，超过 %d 帧上限"
                                 % (key, len(frames), MAX_ROLE_FRAMES))
            roles[key] = {"frames": [os.path.basename(f) for f in frames],
                          "hot": list(hotspot.get(key, [0, 0]))}
            copied += len(frames)
            continue
        if os.path.exists(os.path.join(src, src_file)):
            roles[key] = {"src": src_file,
                          "hot": list(hotspot.get(key, [0, 0]))}
            copied += 1
    missing = [k for k in ROLE_KEY.values() if k not in roles]
    return roles, copied, missing


def write_theme_config(src, tdir, name, title=None, hotspot=None,
                       sizes=(32, 48), outline=True, cut_background=True,
                       delay_ms=90):
    """把 --src 里的 png 收进 themes/<name>/，写 theme.json。"""
    os.makedirs(tdir, exist_ok=True)
    roles, copied, missing = collect_roles(src, hotspot or DEFAULT_HOT)
    for role in roles.values():
        for rel in role.get("frames", []) or [role.get("src")]:
            shutil.copy2(os.path.join(src, rel), os.path.join(tdir, os.path.basename(rel)))
    cfg = {
        "name": name,
        "title": title or name,
        "sizes": [int(s) for s in sizes],
        "outline": bool(outline),
        "cut_background": bool(cut_background),
        "delay_ms": int(delay_ms),
        "roles": roles,
    }
    with open(os.path.join(tdir, "theme.json"), "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=2)
    return cfg, copied, missing


def main(argv=None):
    ap = argparse.ArgumentParser(description="把一堆 png 变成 CursorLab 主题")
    ap.add_argument("--name", required=True, help="主题名，也是目录名")
    ap.add_argument("--src", required=True, help="png 素材目录")
    ap.add_argument("--title", default="", help="显示名")
    ap.add_argument("--hot", nargs="*", default=[], help="热点覆盖，如 arrow=2,2")
    ap.add_argument("--no-outline", action="store_true", help="不要自动白描边")
    ap.add_argument("--keep-bg", action="store_true", help="不要自动抠背景")
    ap.add_argument("--sizes", default="32,48", help="多尺寸，逗号分隔")
    ap.add_argument("--delay-ms", type=int, default=90, help="动画帧间隔（毫秒）")
    ap.add_argument("--no-build", action="store_true", help="只写 theme.json，不构建")
    args = ap.parse_args(argv)

    src = os.path.abspath(args.src)
    if not os.path.isdir(src):
        raise SystemExit("素材目录不存在: %s" % src)
    try:
        hotspot = parse_hotspots(args.hot)
        sizes = [int(s) for s in args.sizes.split(",") if s.strip()]
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
    if not sizes:
        raise SystemExit("--sizes 不能为空")

    tdir = os.path.join(THEMES_DIR, args.name)
    if os.path.isdir(tdir):
        shutil.rmtree(tdir)
    cfg, copied, missing = write_theme_config(
        src, tdir, args.name, args.title or args.name, hotspot, sizes,
        outline=not args.no_outline, cut_background=not args.keep_bg,
        delay_ms=args.delay_ms)
    print("[ok] 写入 themes/%s/theme.json（%d 个角色，%d 张图）"
          % (args.name, len(cfg["roles"]), copied))
    if missing:
        print("[!] 缺 %d 个角色，构建会失败：%s"
              % (len(missing), ", ".join(missing)))
        return 1
    if args.no_build:
        return 0

    print("  热点默认沿用像素小猫，想精确调整：打开 tools/hotspot.html 点一下再回车")
    theme = load_themes()[args.name]
    outdir = build_theme(theme)
    package(theme, outdir)
    print("[ok] 装到系统：powershell -ExecutionPolicy Bypass -File install.ps1 "
          "-Dir out\\%s -Name \"%s\"" % (args.name, args.name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
