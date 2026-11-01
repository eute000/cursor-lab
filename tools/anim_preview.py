# -*- coding: utf-8 -*-
"""出动态预览：箭头 12 帧微动画 + 按下态对比，存成 GIF。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont

from cursorlab import cartoon

CELL = 128
BG = (245, 246, 250)
FONT = r"C:\Windows\Fonts\msyh.ttc"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_anim_preview.gif")


def frame_image(f):
    im = Image.new("RGB", (CELL, CELL), BG)
    im.paste(cartoon.render("arrow", CELL, f), (0, 0), cartoon.render("arrow", CELL, f))
    return im


def main():
    frames = [frame_image(f) for f in range(12)]

    # 按下态单独一帧，插在最后并停久一点
    press = Image.new("RGB", (CELL, CELL), BG)
    art = cartoon.render("arrow_press", CELL)
    press.paste(art, (0, 0), art)
    frames.append(press)

    frames[0].save(OUT, save_all=True, append_images=frames[1:],
                   duration=[90] * 12 + [700], loop=0, optimize=True)
    print("saved", OUT, os.path.getsize(OUT) // 1024, "KB")

    # 静态对照：第 1 / 第 4 / 按下
    strip = Image.new("RGB", (CELL * 3 + 40, CELL + 34), (255, 255, 255))
    for i, (label, img) in enumerate((
            ("尾巴偏左", frame_image(3)),
            ("尾巴偏右", frame_image(9)),
            ("按下：低头+眯眼+握爪", press))):
        strip.paste(img, (i * (CELL + 20), 0))
        ImageDraw.Draw(strip).text((i * (CELL + 20), CELL + 8), label,
                                   font=ImageFont.truetype(FONT, 11), fill=(90, 94, 102))
    strip.save(OUT.replace(".gif", "_strip.png"))
    print("saved strip")


if __name__ == "__main__":
    main()
