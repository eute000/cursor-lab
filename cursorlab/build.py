# -*- coding: utf-8 -*-
"""
统一构建器：主题 -> .cur/.ani + 预览图 + zip 发行包。

主题分两种：
  procedural —— 代码画的（像素小猫就是这个）
  assets     —— 用图片做的，看 themes/<name>/theme.json
"""

import argparse
import json
import os
import shutil
import sys
import zipfile

from PIL import Image, ImageDraw, ImageFont

from . import cat as catmod
from .encode import ROLES, ani_bytes, cur_bytes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    return ImageFont.truetype(FONT, size) if os.path.exists(FONT) else ImageFont.load_default()


# ------------------------------------------------------------------ 主题
class ProceduralTheme:
    kind = "procedural"

    def __init__(self, key, title, sprites, sizes, delay_ms=90):
        self.key = key
        self.title = title
        self.sprites = sprites
        self.sizes = sizes
        self.delay_ms = delay_ms

    def render(self, role_key, size, frame=0):
        return catmod.render(role_key, size, frame)

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
        return self._load(rel).resize((size, size), Image.LANCZOS)

    def hotspot(self, role_key):
        return self.sprites[role_key]["hot"]

    def frames(self, role_key):
        return self.sprites[role_key]["frames"]


def cut_background(im, tol=26):
    """把四周连通的近似纯色背景抠掉（AI 出图常见白底）。"""
    im = im.copy()
    w, h = im.size
    px = im.load()
    seed = px[0, 0]
    if seed[3] == 0:
        return im
    bg = seed[:3]
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a and abs(r - bg[0]) <= tol and abs(g - bg[1]) <= tol and abs(b - bg[2]) <= tol:
                px[x, y] = (r, g, b, 0)
    return im


def add_rim(im, color=(255, 255, 255, 255), grow=1):
    """给抠好的图加一圈描边，暗色桌面上才看得见。"""
    a = im.split()[3]
    grown = a
    for _ in range(grow):
        grown = grown.filter(__import__("PIL.ImageFilter", fromlist=["x"]).MaxFilter(3))
    from PIL import ImageChops
    ring = ImageChops.subtract(grown, a)
    out = Image.new("RGBA", im.size, color)
    out.putalpha(ring)
    out.alpha_composite(im)
    return out


def load_themes():
    themes = {}
    cat = ProceduralTheme("pixel-cat", "Pixel Cat 像素小猫",
                          catmod.SPRITES, [32, 64])
    themes[cat.key] = cat
    if os.path.isdir(THEMES_DIR):
        for name in sorted(os.listdir(THEMES_DIR)):
            cfg = os.path.join(THEMES_DIR, name, "theme.json")
            if os.path.exists(cfg):
                t = AssetTheme(cfg)
                themes[t.key] = t
    return themes


# ------------------------------------------------------------------ 输出
def build_theme(theme, verbose=True):
    outdir = os.path.join(OUT, theme.key)
    pngdir = os.path.join(outdir, "png")
    if os.path.isdir(outdir):
        shutil.rmtree(outdir)
    os.makedirs(pngdir)

    missing = [k for k in ROLE_KEY.values() if k not in theme.sprites]
    if missing:
        raise SystemExit("主题 %s 缺这些角色: %s" % (theme.key, ", ".join(missing)))

    files = []
    for role in ROLES:
        key = ROLE_KEY[role]
        hot = theme.hotspot(key)
        nframes = theme.frames(key)
        if nframes > 1:
            frames = [cur_bytes([theme.render(key, s, f) for s in theme.sizes], hot)
                      for f in range(nframes)]
            data = ani_bytes(frames, theme.delay_ms)
            ext = "ani"
        else:
            data = cur_bytes([theme.render(key, s, 0) for s in theme.sizes], hot)
            ext = "cur"
        name = "%s.%s" % (key, ext)
        with open(os.path.join(outdir, name), "wb") as fh:
            fh.write(data)
        theme.render(key, 128, 0).save(os.path.join(pngdir, "%s.png" % key))
        files.append((name, len(data)))

    sheet = build_sheet(theme)
    sheet.save(os.path.join(outdir, "preview.png"))
    if verbose:
        print("  %-12s %2d 个文件  %5.1f KB" %
              (theme.key, len(files), sum(f[1] for f in files) / 1024.0))
    return outdir


def build_sheet(theme, cell=128, gap=8, pad=18, cols=6):
    items = [(k, v) for k, v in theme.sprites.items()]
    rows = (len(items) + cols - 1) // cols
    W = pad * 2 + cols * (cell * 2 + gap) + (cols - 1) * gap
    H = pad * 2 + 46 + rows * (cell + 20 + gap)
    img = Image.new("RGBA", (W, H), SHEET_BG)
    d = ImageDraw.Draw(img)
    d.text((pad, pad), "CursorLab · %s  ·  %d 角色" % (theme.title, len(items)),
           font=_font(17), fill=(120, 226, 255, 255))
    for i, (key, _spec) in enumerate(items):
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
        d.text((x, y + cell + 3), "%s  (%s)" % (key, KEY_ROLE[key]),
               font=_font(12), fill=(190, 194, 204, 255))
    return img


def package(theme, outdir):
    """打出发行 zip：光标 + 安装脚本 + 说明，解压双击就能装。"""
    os.makedirs(DIST, exist_ok=True)
    zpath = os.path.join(DIST, "%s.zip" % theme.key)
    add = ["install.ps1", "uninstall.ps1"]
    readme = """CursorLab · %s
==================================================
1) 右键 install.ps1 -> 用 PowerShell 运行；或者双击 安装.bat
   （被策略拦了就用：powershell -ExecutionPolicy Bypass -File install.ps1）
2) 还原：运行 uninstall.ps1（会自动读 install 时写的 backup-cursors.json）
3) 装好后在 设置 -> 蓝牙和其他设备 -> 鼠标 -> 其他鼠标设置 -> 指针，
   主题下拉里能看到 "CursorLab %s"

说明：指针文件在 cursors\\ 目录，靠的是用户级注册表 HKCU\\Control Panel\\Cursors，
不需要管理员权限；如果移动了文件夹，重新运行一次 install.ps1 即可。
""" % (theme.title, theme.key)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for fn in os.listdir(outdir):
            if fn.endswith((".cur", ".ani")):
                z.write(os.path.join(outdir, fn), "cursors/" + fn)
        z.writestr("README.txt", readme)
        for fn in add:
            src = os.path.join(ROOT, fn)
            if os.path.exists(src):
                z.write(src, fn)
        bat = "@echo off\r\npowershell -ExecutionPolicy Bypass -File \"%%~dp0install.ps1\"\r\npause\r\n"
        z.writestr("安装.bat", bat)
    print("  zip: dist/%s.zip (%.1f KB)" % (theme.key, os.path.getsize(zpath) / 1024.0))
    return zpath


def main(argv=None):
    ap = argparse.ArgumentParser(description="构建 CursorLab 主题")
    ap.add_argument("--theme", default="all")
    ap.add_argument("--no-zip", action="store_true")
    args = ap.parse_args(argv)

    themes = load_themes()
    names = list(themes) if args.theme == "all" else [args.theme]
    for name in names:
        if name not in themes:
            raise SystemExit("没有这个主题：%s（可选：%s）" % (name, ", ".join(themes)))
    print("构建 %d 个主题" % len(names))
    for name in names:
        outdir = build_theme(themes[name])
        if not args.no_zip:
            package(themes[name], outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
