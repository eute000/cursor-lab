# -*- coding: utf-8 -*-
"""
统一构建器：主题 -> .cur/.ani + 预览图 + zip 发行包。

主题分两种：
  procedural —— 代码画的（卡通风小黑猫就是这个，见 cartoon.py）
  assets     —— 用图片做的，看 themes/<name>/theme.json
"""

import argparse
import json
import os
import shutil
import sys
import zipfile

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from . import cartoon as cartoonmod
from .encode import MAX_DIM, ROLES, ani_bytes, check_hotspot, cur_bytes


def base_dir():
    """源码树里有 install.ps1 就用源码树，否则（pip 装进 site-packages）用当前目录。

    不这么判断的话，pip 装的 cursorlab-build 会把 out/ 和 dist/ 写到
    site-packages 里 —— 用户根本找不到。
    """
    pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.path.exists(os.path.join(pkg_root, "install.ps1")):
        return pkg_root
    return os.getcwd()


ROOT = base_dir()
OUT = os.path.join(ROOT, "out")
DIST = os.path.join(ROOT, "dist")
THEMES_DIR = os.path.join(ROOT, "themes")

# 注册表角色 -> 造型 key
ROLE_KEY = {
    "Arrow": "arrow", "Help": "help", "AppStarting": "appstarting",
    "Wait": "wait", "Crosshair": "crosshair", "IBeam": "ibeam",
    "NWPen": "nwpen", "No": "no", "SizeNS": "sizens", "SizeWE": "sizewe",
    "SizeNWSE": "sizenwse", "SizeNESW": "sizenesw", "SizeAll": "sizeall",
    "UpArrow": "uparrow", "Hand": "hand", "Pin": "pin", "Person": "person",
}
KEY_ROLE = {v: k for k, v in ROLE_KEY.items()}

SHEET_BG = (32, 34, 40, 255)
LIGHT = (246, 247, 250, 255)
DARK = (24, 26, 32, 255)
FONT = r"C:\Windows\Fonts\segoeuib.ttf"


def _font(size):
    if os.path.exists(FONT):
        return ImageFont.truetype(FONT, size)
    return ImageFont.load_default()


# ------------------------------------------------------------------ 主题
class ProceduralTheme:
    kind = "procedural"

    def __init__(self, key, title, sprites, sizes, delay_ms=90, render_fn=None):
        self.key = key
        self.title = title
        self.sprites = sprites
        self.sizes = sizes
        self.delay_ms = delay_ms
        self._render = render_fn or cartoonmod.render

    def has(self, role_key):
        # 附加造型（按下态）不在 SPRITES 里，但在 EXTRA 里，构建时要一起出
        return role_key in self.sprites or role_key in getattr(cartoonmod, "EXTRA", {})

    def render(self, role_key, size, frame=0):
        return self._render(role_key, size, frame)

    def hotspot(self, role_key):
        return self.sprites[role_key]["hot"]

    def frames(self, role_key):
        return self.sprites[role_key]["frames"]


class AssetTheme:
    """用图片做主题：themes/<name>/theme.json + 同目录的 png。"""

    kind = "assets"

    def __init__(self, path):
        self.dir = os.path.dirname(path)
        with open(path, encoding="utf-8") as fh:
            cfg = json.load(fh)
        self.key = cfg.get("name") or os.path.basename(self.dir)
        self.title = cfg.get("title", self.key)
        self.sizes = cfg.get("sizes", [32, 48])
        self.delay_ms = cfg.get("delay_ms", 90)
        self.outline = cfg.get("outline", True)
        self.cut_bg = cfg.get("cut_background", True)
        self.items = cfg.get("roles", {})
        self.sprites = {k: {"hot": tuple(v.get("hot", [0, 0])),
                            "frames": len(v["frames"]) if "frames" in v else 1}
                        for k, v in self.items.items()}

    def has(self, role_key):
        return role_key in self.items

    def _load(self, rel):
        im = Image.open(os.path.join(self.dir, rel)).convert("RGBA")
        if self.cut_bg:
            im = cut_background(im)
        if self.outline:
            im = add_rim(im)
        return im

    def render(self, role_key, size, frame=0):
        spec = self.items[role_key]
        rel = spec["frames"][frame] if "frames" in spec else spec["src"]
        return fit_square(self._load(rel), size)

    def hotspot(self, role_key):
        return self.sprites[role_key]["hot"]

    def frames(self, role_key):
        return self.sprites[role_key]["frames"]


def fit_square(im, size):
    """等比缩放后居中放进 size×size 的透明画布。

    直接把非正方形素材 resize 成正方形会横向压扁 —— 用户的 logo、
    截图基本都是非正方形，等比缩放才是他们想要的。
    """
    w, h = im.size
    if (w, h) == (size, size):
        return im
    scale = min(size / float(w), size / float(h))
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    art = im.resize((nw, nh), Image.LANCZOS)
    if (nw, nh) == (size, size):
        return art
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.alpha_composite(art, ((size - nw) // 2, (size - nh) // 2))
    return out


def _band(channel, value, tol):
    """单通道「接近 value」的二值图。"""
    return channel.point(lambda p: 255 if abs(p - value) <= tol else 0)


def cut_background(im, tol=26):
    """抠掉**连通到画布边缘**的近似纯色背景（AI 出图常见白底）。

    只从四条边泛洪，图像内部的同色区域（白眼睛、高光、镂空、描边里的
    留白）一律不动。之前是「凡是接近背景色就抠」，白底素材里猫的白眼睛
    会被一起抠穿，放到深色壁纸上就是个透明的洞。
    """
    im = im.copy()
    w, h = im.size
    px = im.load()
    seed = px[0, 0]
    if seed[3] == 0:
        return im
    bg = seed[:3]

    r, g, b = im.convert("RGB").split()
    near = ImageChops.multiply(
        ImageChops.multiply(_band(r, bg[0], tol), _band(g, bg[1], tol)),
        _band(b, bg[2], tol))

    # 128 = 从外面泛洪到的背景像素
    starts = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
              (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]
    for xy in starts:
        if near.getpixel(xy) == 255:
            ImageDraw.floodfill(near, xy, 128)

    outer = near.point(lambda p: 255 if p == 128 else 0)
    if outer.getbbox() is None:
        return im
    alpha = ImageChops.multiply(im.split()[3], ImageChops.invert(outer))
    im.putalpha(alpha)
    return im


def add_rim(im, color=(255, 255, 255, 255), grow=1):
    """给抠好的图加一圈描边，暗色桌面上才看得见。"""
    a = im.split()[3]
    grown = a
    for _ in range(grow):
        grown = grown.filter(ImageFilter.MaxFilter(3))
    ring = ImageChops.subtract(grown, a)
    out = Image.new("RGBA", im.size, color)
    out.putalpha(ring)
    out.alpha_composite(im)
    return out


def load_themes():
    themes = {}
    t = ProceduralTheme("cartoon-cat", "Cartoon Cat 卡通小黑猫",
                        cartoonmod.SPRITES, [32, 48, 64],
                        render_fn=cartoonmod.render)
    themes[t.key] = t
    if os.path.isdir(THEMES_DIR):
        for name in sorted(os.listdir(THEMES_DIR)):
            cfg = os.path.join(THEMES_DIR, name, "theme.json")
            if os.path.exists(cfg):
                t = AssetTheme(cfg)
                themes[t.key] = t
    return themes


# ------------------------------------------------------------------ 输出
def check_sizes(sizes, key="主题"):
    """尺寸必须是 1..256 的整数，否则 .cur 目录项存不下。"""
    out = []
    for s in sizes:
        try:
            v = int(s)
        except (TypeError, ValueError):
            raise ValueError("%s 的 sizes 里有非整数: %r" % (key, s)) from None
        if not 1 <= v <= MAX_DIM:
            raise ValueError("%s 的 size=%d 超出 1..%d" % (key, v, MAX_DIM))
        out.append(v)
    if not out:
        raise ValueError("%s 的 sizes 是空的" % key)
    return out


def role_hotspot(theme, key):
    """取角色的设计网格热点并校验，报错时带上角色名。"""
    try:
        return check_hotspot(theme.hotspot(key))
    except ValueError as exc:
        raise ValueError("角色 %s 的热点不合法: %s" % (key, exc)) from None


def build_theme(theme, verbose=True, preview_size=128, sheet_cell=128):
    """theme -> out/<key>/ 里的 .cur/.ani + png/ 单图 + preview.png。

    preview_size / sheet_cell 只是给测试用的快捷开关（预览图和大图无关，
    但 128px 的 8 倍超采样渲染很慢，90 多个用例里没必要每次都画）。
    """
    outdir = os.path.join(OUT, theme.key)
    pngdir = os.path.join(outdir, "png")
    if os.path.isdir(outdir):
        shutil.rmtree(outdir)
    os.makedirs(pngdir)

    sizes = check_sizes(theme.sizes, theme.key)
    missing = [k for k in ROLE_KEY.values() if not theme.has(k)]
    if missing:
        raise SystemExit("主题 %s 缺这些角色: %s" % (theme.key, ", ".join(missing)))

    files = []
    for role in ROLES:
        key = ROLE_KEY[role]
        hot = role_hotspot(theme, key)
        nframes = theme.frames(key)
        if nframes > 1:
            frames = [cur_bytes([theme.render(key, s, f) for s in sizes], hot)
                      for f in range(nframes)]
            data = ani_bytes(frames, theme.delay_ms)
            ext = "ani"
        else:
            data = cur_bytes([theme.render(key, s, 0) for s in sizes], hot)
            ext = "cur"
        name = "%s.%s" % (key, ext)
        with open(os.path.join(outdir, name), "wb") as fh:
            fh.write(data)
        theme.render(key, preview_size, 0).save(os.path.join(pngdir, "%s.png" % key))
        files.append((name, len(data)))

    # 附加造型（不属于 17 项注册表角色，由小助手程序按需切换，如按下态）。
    # 图片主题没有这些造型，跳过 —— 以前是无条件渲染，任何自定义主题都会
    # 在建到这一步时 KeyError: 'arrow_press'。
    for key, spec in getattr(cartoonmod, "EXTRA", {}).items():
        if not theme.has(key):
            continue
        hot = role_hotspot(theme, key) if theme.kind == "assets" else spec["hot"]
        data = cur_bytes([theme.render(key, s, 0) for s in sizes], hot)
        with open(os.path.join(outdir, "%s.cur" % key), "wb") as fh:
            fh.write(data)
        files.append(("%s.cur" % key, len(data)))

    sheet = build_sheet(theme, cell=sheet_cell)
    sheet.save(os.path.join(outdir, "preview.png"))
    if verbose:
        print("  %-12s %2d 个文件  %5.1f KB" %
              (theme.key, len(files), sum(f[1] for f in files) / 1024.0))
    return outdir


def sheet_order(theme):
    """预览图顺序：先 17 个注册表角色，再附加造型。"""
    known = [ROLE_KEY[r] for r in ROLES if ROLE_KEY[r] in theme.sprites]
    return known + [k for k in theme.sprites if k not in known]


def build_sheet(theme, cell=128, gap=8, pad=18, cols=6):
    items = sheet_order(theme)
    rows = (len(items) + cols - 1) // cols
    # 一行 = cols 个「两联」格子，格子之间只有 cols-1 个 gap；
    # 以前多算了一个 gap，预览图右边留一条空白。
    W = pad * 2 + cols * (cell * 2 + gap) - gap
    H = pad * 2 + 46 + rows * (cell + 20 + gap) - gap
    img = Image.new("RGBA", (W, H), SHEET_BG)
    d = ImageDraw.Draw(img)
    d.text((pad, pad), "CursorLab · %s  ·  %d 角色" % (theme.title, len(items)),
           font=_font(17), fill=(120, 226, 255, 255))
    for i, key in enumerate(items):
        col, row = i % cols, i // cols
        x = pad + col * (cell * 2 + gap)
        y = pad + 46 + row * (cell + 20 + gap)
        art = theme.render(key, cell, 0)
        for j, bg in enumerate([LIGHT, DARK]):
            tile = Image.new("RGBA", (cell, cell), bg)
            ImageDraw.Draw(tile).rectangle([0, 0, cell - 1, cell - 1],
                                           outline=(120, 124, 136, 90))
            tile.alpha_composite(art)
            img.alpha_composite(tile, (x + j * (cell + gap), y))
        # 自定义主题可能有不在 17 项里的造型，标签退化成 key 自己
        d.text((x, y + cell + 3), "%s  (%s)" % (key, KEY_ROLE.get(key, "-")),
               font=_font(12), fill=(190, 194, 204, 255))
    return img


def package(theme, outdir):
    """打出发行 zip：光标 + 安装脚本 + 说明，解压双击就能装。"""
    os.makedirs(DIST, exist_ok=True)
    zpath = os.path.join(DIST, "%s.zip" % theme.key)
    readme = """CursorLab · %s
==================================================
1) 双击 安装.bat（被策略拦了就用：powershell -ExecutionPolicy Bypass -File install.ps1）
2) 还原：运行 uninstall.ps1（读 install 时写的 backup-cursors.json）
3) 装好后在 设置 -> 蓝牙和其他设备 -> 鼠标 -> 其他鼠标设置 -> 指针，
   主题下拉里能看到 "CursorLab %s"

不需要管理员权限（只写 HKCU\\Control Panel\\Cursors）。
如果移动了文件夹，重新运行一次 install.ps1 即可。
""" % (theme.title, theme.key)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for fn in sorted(os.listdir(outdir)):
            if fn.endswith((".cur", ".ani")):
                z.write(os.path.join(outdir, fn), "cursors/" + fn)
        z.writestr("README.txt", readme)
        for fn in ("install.ps1", "uninstall.ps1"):
            src = os.path.join(ROOT, fn)
            if os.path.exists(src):
                z.write(src, fn)
        # 点击特效小助手
        fx = os.path.join(ROOT, "tools", "click_fx.py")
        if os.path.exists(fx):
            z.write(fx, "click_fx.py")
            z.writestr("点击特效.bat",
                       "@echo off\r\ncd /d \"%~dp0\"\r\n"
                       "start \"CursorLab click-fx\" /min python click_fx.py\r\n")
        bat = ("@echo off\r\n"
               "powershell -ExecutionPolicy Bypass -File \"%%~dp0install.ps1\"\r\npause\r\n")
        z.writestr("安装.bat", bat)
    print("  zip: dist/%s.zip (%.1f KB)" % (theme.key, os.path.getsize(zpath) / 1024.0))
    return zpath


def main(argv=None):
    ap = argparse.ArgumentParser(description="构建 CursorLab 主题")
    ap.add_argument("--theme", default="all", help="主题名，默认 all")
    ap.add_argument("--no-zip", action="store_true", help="只出光标，不打 zip")
    ap.add_argument("--verify", action="store_true",
                    help="构建后校验 .cur/.ani 结构，有问题以退出码 1 结束")
    ap.add_argument("--list", action="store_true", help="列出可用主题后退出")
    args = ap.parse_args(argv)

    themes = load_themes()
    if args.list:
        for name in sorted(themes):
            print("%-14s %s" % (name, themes[name].title))
        return 0

    names = sorted(themes) if args.theme == "all" else [args.theme]
    for name in names:
        if name not in themes:
            raise SystemExit("没有这个主题：%s（可选：%s）" % (name, ", ".join(sorted(themes))))
    print("构建 %d 个主题" % len(names))
    bad = 0
    for name in names:
        outdir = build_theme(themes[name])
        if not args.no_zip:
            package(themes[name], outdir)
        if args.verify:
            from .verify import verify_dir
            problems = verify_dir(outdir)
            for fn, msgs in sorted(problems.items()):
                for msg in msgs:
                    print("  [!] %s: %s" % (fn, msg))
            bad += sum(len(m) for m in problems.values())
    if bad:
        print("校验发现 %d 个问题" % bad)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
