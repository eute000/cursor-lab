# -*- coding: utf-8 -*-
"""I 型光标 A/B 对比：旧版(21px) vs 新版(16px)，旁边放 14 号正文（按 150% 缩放）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont

from cursorlab import cartoon
from cursorlab.cartoon import BODY, Canvas

FONT = r"C:\Windows\Fonts\msyh.ttc"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ibeam_ab.png")
SCALE = 1.5          # 150% 缩放
LAYER = 48           # Windows 在该缩放下取 48px 层


def old_ibeam():
    """按第一版尺寸复刻：杆 5→27、横杠 11.5→20.5、笔画 2.0"""
    c = Canvas(LAYER)
    c.line([(16, 5.0), (16, 27.0)], fill=BODY, w=2.0, caps=False)
    c.line([(11.5, 4.6), (20.5, 4.6)], fill=BODY, w=2.2)
    c.line([(11.5, 27.4), (20.5, 27.4)], fill=BODY, w=2.2)
    return c.img.resize((LAYER, LAYER), Image.LANCZOS)


def dark_h(im):
    px = im.load()
    w, h = im.size
    ys = [y for y in range(h) for x in range(w) if px[x, y][3] > 200 and px[x, y][0] < 80]
    return (max(ys) - min(ys) + 1) if ys else 0


def main():
    new = cartoon.render("ibeam", LAYER)
    old = old_ibeam()
    print("旧版深色高 %dpx / 新版深色高 %dpx (都按 %dpx 层)" % (dark_h(old), dark_h(new), LAYER))

    W, H = 720, 300
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    f16 = ImageFont.truetype(FONT, int(15 * SCALE))
    f13 = ImageFont.truetype(FONT, int(12 * SCALE))
    d.text((24, 16), "I 型光标 A/B（%dpx 层，150%% 缩放，1:1）" % LAYER, font=f16, fill=(40, 40, 46))

    y = 70
    for label, im, note in (("旧版", old, "深色 %dpx" % dark_h(old)),
                            ("新版", new, "深色 %dpx" % dark_h(new))):
        d.text((24, y + 10), label, font=f13, fill=(90, 94, 102))
        img.paste(im, (90, y), im)
        d.text((90 + LAYER + 10, y + 8), note, font=f13, fill=(130, 134, 142))
        y += LAYER + 24

    # 正文参照
    y = 70
    for css in (12, 14, 16):
        font = ImageFont.truetype(FONT, int(round(css * SCALE)))
        d.text((330, y + 6), "正文 %dpx：中文 text" % css, font=font, fill=(30, 30, 36))
        y += int(round(css * SCALE)) + 26

    d.text((24, H - 28), "目标：光标深色本体 ≈ 14 号正文的汉字墨高（约 22px）",
           font=f13, fill=(130, 134, 142))
    img.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    main()
