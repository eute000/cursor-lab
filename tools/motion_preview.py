# -*- coding: utf-8 -*-
"""出动态预览：手型抓取动画 GIF + I 型按下对比。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont

from cursorlab import cartoon

CELL = 128
BG = (245, 246, 250)
FONT = r"C:\Windows\Fonts\msyh.ttc"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)))


def art(name, f=0):
    return cartoon.render(name, CELL, f)


def on_bg(name, f=0):
    im = Image.new("RGB", (CELL, CELL), BG)
    a = art(name, f)
    im.paste(a, (0, 0), a)
    return im


def main():
    # --- 手型：8 帧抓取动画
    frames = [on_bg("hand", f) for f in range(8)]
    gif = os.path.join(OUT, "_hand_anim.gif")
    frames[0].save(gif, save_all=True, append_images=frames[1:],
                   duration=[90] * 8, loop=0, optimize=True)
    print("saved", gif, os.path.getsize(gif) // 1024, "KB")

    # --- 对照条：爪最小 / 爪最大 / I 平时 / I 按下
    items = [("爪 1.00", on_bg("hand", 0)), ("爪 1.11（抓）", on_bg("hand", 4)),
             ("I 平时", on_bg("ibeam")), ("I 按下", on_bg("ibeam_press"))]
    strip = Image.new("RGB", (CELL * 4 + 60, CELL + 34), (255, 255, 255))
    d = ImageDraw.Draw(strip)
    for i, (label, img) in enumerate(items):
        x = i * (CELL + 20)
        strip.paste(img, (x, 0))
        d.text((x, CELL + 8), label, font=ImageFont.truetype(FONT, 11), fill=(90, 94, 102))
    path = os.path.join(OUT, "_v8_strip.png")
    strip.save(path)
    print("saved", path)


if __name__ == "__main__":
    main()
