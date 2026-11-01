# -*- coding: utf-8 -*-
"""
105.0s 帧 v4：罗小黑风格黑白猫脸（缩小居中）+ 中英双字体排版
- 猫脸只占画面约 55% 宽度，四周留黑，标题块与字幕都落在黑底上
用法：python tools/frame105c.py <图片> <输出>
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
F_CN = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"
F_EN_I = r"C:\Windows\Fonts\BOD_I.TTF"
F_EN = r"C:\Windows\Fonts\BOD_R.TTF"
INK = (246, 244, 240)
WHITE = (236, 234, 230)
G3 = (120, 117, 112)


def f(p, s):
    return ImageFont.truetype(p, s)


def main():
    src = sys.argv[1]
    out = sys.argv[2]

    img = Image.new("RGBA", (W, H), (2, 2, 3, 255))

    # 猫脸：按宽度铺到 55%，垂直略偏上
    cat = Image.open(src).convert("RGBA")
    cw, chh = cat.size
    cat = cat.crop((int(cw * 0.21), 0, int(cw * 0.79), int(chh * 0.96)))   # 裁掉右侧光柱
    target_w = int(W * 0.55)
    cat = cat.resize((target_w, int(cat.height * target_w / cat.width)), Image.LANCZOS)
    cx = (W - cat.width) // 2
    cy = 118

    # 生成图自带灰底/光晕会露出"矩形边界"：用径向衰减把四周亮度压到 0
    arr = np.asarray(cat.convert("RGB"), dtype=np.float32)
    hh, ww = arr.shape[:2]
    gy, gx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    r = np.sqrt(((gx - ww / 2) / (ww / 2)) ** 2 + ((gy - hh / 2) / (hh / 2)) ** 2)
    falloff = np.clip((1.02 - r) / 0.55, 0, 1) ** 1.5
    arr = np.clip((arr - 20) * 1.18, 0, 255)
    lum = arr.max(axis=2)
    line = arr * (lum > 172)[:, :, None]                 # 只有近白线条保持满亮度
    bg = arr * ((lum <= 172)[:, :, None]) * falloff[:, :, None]   # 灰底/光晕：只衰减背景
    arr = np.maximum(line, bg)
    cat = Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")

    img.alpha_composite(cat, (cx, cy))

    # 四周压黑（让猫的边缘融进黑底）
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.rectangle([cx + 30, cy + 30, cx + cat.width - 30, cy + cat.height - 30], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(60))
    dark = Image.new("RGBA", (W, H), (2, 2, 3, 255))
    img = Image.composite(img, dark, mask.point(lambda v: 255)) if False else img
    edge = Image.new("RGBA", (W, H), (2, 2, 3, 0))
    ed = ImageDraw.Draw(edge)
    for i in range(90):
        a = int(2 + i * 1.2)
        ed.rectangle([cx - i, cy - i, cx + cat.width + i, cy + cat.height + i],
                     outline=(2, 2, 3, min(120, a)))
    img.alpha_composite(edge)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    d.text((96, 78), "结语", font=f(F_CN, 40), fill=WHITE + (232,))
    d.text((96, 132), "Epilogue", font=f(F_EN_I, 30), fill=G3 + (215,))
    d.line([(96, 182), (330, 182)], fill=(150, 147, 142, 120), width=1)

    d.text((W - 300, 82), "CURSORLAB", font=f(F_EN, 24), fill=G3 + (175,))
    d.text((W - 300, 116), "06 / 06", font=f(F_EN, 22), fill=G3 + (125,))

    d.line([(96, 200), (W - 300, 200)], fill=(80, 78, 76, 90), width=1)
    pw = int((W - 396) * (105.0 / 126.9))
    d.line([(96, 200), (96 + pw, 200)], fill=(224, 222, 218, 130), width=1)

    main_cn = "全程，我只说了我想要什么"
    fc = f(F_CN, 68)
    mw = d.textlength(main_cn, font=fc)
    d.text(((W - mw) / 2, H - 196), main_cn, font=fc, fill=INK + (244,))

    sub = "all I ever said was: this is what I want"
    fe = f(F_EN_I, 33)
    ew = sum(d.textlength(c, font=fe) + 4 for c in sub)
    sx = (W - ew) / 2
    for ch in sub:
        d.text((sx, H - 110), ch, font=fe, fill=WHITE + (170,))
        sx += d.textlength(ch, font=fe) + 4

    img.alpha_composite(layer)

    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    arr += np.random.default_rng(105).normal(0, 2.0, (H, W, 1))
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").save(out)
    print("saved", out)


if __name__ == "__main__":
    main()
