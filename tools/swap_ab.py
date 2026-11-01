# -*- coding: utf-8 -*-
"""两种对调方案的效果图，让用户一眼选。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont

from cursorlab.cartoon import Canvas, cat, layer, stamp, sym_cycle, sym_tri

FONT = r"C:\Windows\Fonts\msyh.ttc"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_swap_ab.png")
CELL = 120


def make(fn, frame=0):
    c = Canvas(CELL)
    fn(c, frame, CELL)
    return c.img.resize((CELL, CELL), Image.LANCZOS)


def a_appstarting(style):
    """style='now' 现状：appstarting = ▷+猫+右下小环；wait = 左转圈+猫"""
    def app(c_, f, size):
        if style == "now":
            stamp(c_, layer(size, sym_tri))
            stamp(c_, layer(size, cat, 0.73, 7.6, 6.4))
            stamp(c_, layer(size, sym_cycle, f, 27.0, 26.6, 3.4, 1.55, 2.1))
        else:
            stamp(c_, layer(size, cat, 0.73, 7.6, 6.4))
            stamp(c_, layer(size, sym_cycle, f, 7.2, 7.2, 5.0))
    return app


def b_wait(style):
    def wt(c_, f, size):
        if style == "now":
            stamp(c_, layer(size, cat, 0.73, 7.6, 6.4))
            stamp(c_, layer(size, sym_cycle, f, 7.2, 7.2, 5.0))
        else:
            stamp(c_, layer(size, sym_tri))
            stamp(c_, layer(size, cat, 0.73, 7.6, 6.4))
    return wt


def main():
    W, H = 620, 380
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    f16 = ImageFont.truetype(FONT, 16)
    f13 = ImageFont.truetype(FONT, 13)
    d.text((22, 14), "两种对调方案（目前是「方案 1」）", font=f16, fill=(40, 40, 46))

    rows = [
        ("方案 1（保持现状）", "appstarting", a_appstarting("now"), "wait", b_wait("now")),
        ("方案 2（对调后）", "appstarting", a_appstarting("swap"), "wait", b_wait("swap")),
    ]
    y = 52
    for title, n1, f1, n2, f2 in rows:
        d.text((22, y + 44), title, font=f13, fill=(90, 94, 102))
        x = 150
        for name, fn in ((n1, f1), (n2, f2)):
            tile = Image.new("RGBA", (CELL, CELL), (246, 247, 250, 255))
            ImageDraw.Draw(tile).rectangle([0, 0, CELL - 1, CELL - 1],
                                           outline=(150, 154, 162, 120))
            tile.alpha_composite(make(fn))
            img.paste(tile.convert("RGB"), (x, y))
            d.text((x, y + CELL + 2), name, font=f13, fill=(120, 124, 132))
            x += CELL + 30
        y += CELL + 40

    img.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    main()
