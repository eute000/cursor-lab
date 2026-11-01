# -*- coding: utf-8 -*-
"""
把一堆 png 变成一套主题（自定义指针的主入口）。

用法：
    python tools/make_theme.py --name my-cat --src assets/my-cat
    python tools/make_theme.py --name my-cat --src assets/my-cat --hot arrow=2,2 hand=16,8

素材要求：
    * 放在 --src 目录里，按角色名命名：arrow.png / hand.png / ibeam.png ...
      角色名见 cursorlab/build.py 的 ROLE_KEY（17 个）
    * 动画指针给一组帧：wait_0.png wait_1.png ... 或 wait/ 子目录
    * 透明底最好；白底也行，会自动抠（theme.json 的 cut_background）

生成 themes/<name>/theme.json，然后自动构建到 out/<name>/ 和 dist/<name>.zip
"""

import argparse
import json
import os
import shutil
import sys

# Windows 控制台默认 GBK，打印 [ok] 这类字符会崩，统一转 UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from cursorlab.build import ROLE_KEY, build_theme, load_themes, package  # noqa: E402
from cursorlab.cat import SPRITES  # noqa: E402

# 角色默认热点（沿用像素小猫的手感，可在 hotspot.html 里改）
DEFAULT_HOT = {k: list(v["hot"]) for k, v in SPRITES.items()}


def find_frames(src, key):
    sub = os.path.join(src, key)
    if os.path.isdir(sub):
        fs = sorted(f for f in os.listdir(sub) if f.lower().endswith(".png"))
        return fs and ["%s/%s" % (key, f) for f in fs]
    fs = sorted(f for f in os.listdir(src)
                if f.lower().endswith(".png") and f.lower().startswith(key + "_"))
    return fs or None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="主题名，也是目录名")
    ap.add_argument("--src", required=True, help="png 素材目录")
    ap.add_argument("--title", default="", help="显示名")
    ap.add_argument("--hot", nargs="*", default=[], help="热点覆盖，如 arrow=2,2")
    ap.add_argument("--no-outline", action="store_true", help="不要自动白描边")
    ap.add_argument("--keep-bg", action="store_true", help="不要自动抠背景")
    ap.add_argument("--sizes", default="32,48", help="多尺寸，逗号分隔")
    args = ap.parse_args()

    src = os.path.abspath(args.src)
    if not os.path.isdir(src):
        raise SystemExit("素材目录不存在: %s" % src)

    hot = {k: list(v) for k, v in DEFAULT_HOT.items()}
    for item in args.hot:
        k, v = item.split("=")
        hot[k] = [float(n) for n in v.split(",")]

    tdir = os.path.join(ROOT, "themes", args.name)
    if os.path.isdir(tdir):
        shutil.rmtree(tdir)
    os.makedirs(tdir)

    roles, copied = {}, 0
    for role, key in ROLE_KEY.items():
        frames = find_frames(src, key)
        if frames:
            for rel in frames:
                shutil.copy2(os.path.join(src, rel),
                             os.path.join(tdir, os.path.basename(rel)))
                copied += 1
            roles[key] = {"frames": [os.path.basename(f) for f in frames],
                          "hot": hot.get(key, [0, 0])}
            continue
        one = os.path.join(src, key + ".png")
        if os.path.exists(one):
            shutil.copy2(one, os.path.join(tdir, key + ".png"))
            copied += 1
            roles[key] = {"src": key + ".png", "hot": hot.get(key, [0, 0])}

    if not roles:
        raise SystemExit("素材目录里没有认出任何角色（需要 arrow.png 这类命名）")
    missing = [k for k in ROLE_KEY.values() if k not in roles]
    if missing:
        print("[!] 缺 %d 个角色，构建会失败：%s" % (len(missing), ", ".join(missing)))

    cfg = {
        "name": args.name,
        "title": args.title or args.name,
        "sizes": [int(s) for s in args.sizes.split(",") if s.strip()],
        "outline": not args.no_outline,
        "cut_background": not args.keep_bg,
        "delay_ms": 90,
        "roles": roles,
    }
    with open(os.path.join(tdir, "theme.json"), "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=2)
    print("[ok] 写入 themes/%s/theme.json（%d 个角色，%d 张图）" % (args.name, len(roles), copied))
    print("  热点默认沿用像素小猫，想精确调整：打开 tools/hotspot.html 点一下再回车")

    if missing:
        return 1
    theme = load_themes()[args.name]
    outdir = build_theme(theme)
    package(theme, outdir)
    print("[ok] 装到系统：powershell -ExecutionPolicy Bypass -File install.ps1 -Dir out\\%s -Name \"%s\""
          % (args.name, args.name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
