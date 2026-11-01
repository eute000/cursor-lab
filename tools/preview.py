# -*- coding: utf-8 -*-
"""开发预览（卡通风）：4 倍放大对比图 + 1:1 真实尺寸条。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw, ImageFont

from cursorlab import cartoon

ZOOM = 128
GAP, PAD = 8, 18
LIGHT = (246, 247, 250, 255)
DARK = (26, 28, 34, 255)
FONT = r"C:\Windows\Fonts\segoeuib.ttf"


def font(sz):
    return ImageFont.truetype(FONT, sz) if os.path.exists(FONT) else ImageFont.load_default()


def build():
    items = list(cartoon.SPRITES.items())
    cols = 6
    rows = (len(items) + cols - 1) // cols
    strip_h = 110
    W = PAD * 2 + cols * (ZOOM * 2 + GAP) + (cols - 1) * GAP
    H = PAD * 2 + 40 + rows * (ZOOM + 20 + GAP) + strip_h
    img = Image.new("RGBA", (W, H), (32, 34, 40, 255))
    d = ImageDraw.Draw(img)
    d.text((PAD, PAD), "cartoon cat v5 · 4x", font=font(17), fill=(140, 200, 255, 255))

    for i, (key, _spec) in enumerate(items):
        col, row = i % cols, i // cols
        x = PAD + col * (ZOOM * 2 + GAP)
        y = PAD + 40 + row * (ZOOM + 20 + GAP)
        art = cartoon.render(key, ZOOM, 0)
        for j, bg in enumerate([LIGHT, DARK]):
            tile = Image.new("RGBA", (ZOOM, ZOOM), bg)
            ImageDraw.Draw(tile).rectangle([0, 0, ZOOM - 1, ZOOM - 1],
                                           outline=(120, 124, 136, 90))
            tile.alpha_composite(art)
            img.alpha_composite(tile, (x + j * (ZOOM + GAP), y))
        d.text((x, y + ZOOM + 3), key, font=font(12), fill=(190, 194, 204, 255))

    sy = PAD + 40 + rows * (ZOOM + 20 + GAP) + 10
    d.text((PAD, sy - 20), "真实尺寸 32px（浅底 / 深底）",
           font=font(14), fill=(180, 186, 198, 255))
    x = PAD
    for key, _spec in items:
        tile = Image.new("RGBA", (40, 40), LIGHT)
        tile.alpha_composite(cartoon.render(key, 32, 0), (4, 4))
        img.alpha_composite(tile, (x, sy))
        x += 44
    x = PAD
    for key, _spec in items:
        tile = Image.new("RGBA", (40, 40), DARK)
        tile.alpha_composite(cartoon.render(key, 32, 0), (4, 4))
        img.alpha_composite(tile, (x, sy + 44))
        x += 44

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_preview_cartoon.png")
    img.convert("RGB").save(out)
    print("saved", out)


if __name__ == "__main__":
    build()
