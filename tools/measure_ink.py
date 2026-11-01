# -*- coding: utf-8 -*-
"""量一下：I 型光标在本机实际多少像素高，对比正文墨高。"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont

from cursorlab import cartoon
from cursorlab.cartoon import Canvas

DPI_SCALE = 1.5          # 144 DPI
LAYER = 48               # Windows 在 150% 下取的层


def ink_height(im):
    bb = im.split()[3].getbbox()
    return 0 if not bb else bb[3] - bb[1]


def main():
    art = cartoon.render("ibeam", LAYER)
    print("I 型 @%dpx 层：%d px 高" % (LAYER, ink_height(art)))

    font_path = r"C:\Windows\Fonts\msyh.ttc"
    for css in (12, 13, 14, 15, 16):
        px = int(round(css * DPI_SCALE))
        f = ImageFont.truetype(font_path, px)
        im = Image.new("L", (300, 80), 0)
        ImageDraw.Draw(im).text((4, 4), "中文示例", font=f, fill=255)
        bb = im.getbbox()
        print("正文 %dpx(CSS) = %d 设备px，汉字墨高 %d px" %
              (css, px, (bb[3] - bb[1]) if bb else 0))


if __name__ == "__main__":
    main()
