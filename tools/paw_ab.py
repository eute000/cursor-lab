# -*- coding: utf-8 -*-
"""手型：平时 vs 按住握爪 的对照图。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont

from cursorlab import cartoon

CELL = 128
BG = (245, 246, 250)
FONT = r"C:\Windows\Fonts\msyh.ttc"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_paw_ab.png")


def tile(name):
    im = Image.new("RGB", (CELL, CELL), BG)
    a = cartoon.render(name, CELL)
    im.paste(a, (0, 0), a)
    return im


def main():
    items = [("平时：完全静止", "hand"), ("按住：趾垫收拢 + 掌垫放大", "hand_press")]
    W = CELL * len(items) + 20 * (len(items) - 1)
    img = Image.new("RGB", (W, CELL + 32), (255, 255, 255))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT, 11)
    for i, (label, name) in enumerate(items):
        x = i * (CELL + 20)
        img.paste(tile(name), (x, 0))
        d.text((x, CELL + 8), label, font=f, fill=(90, 94, 102))
    img.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    main()
