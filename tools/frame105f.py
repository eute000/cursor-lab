# -*- coding: utf-8 -*-
"""
105.0s 帧 v-final：代码直绘猫头（暖棕描边 + 奶油眼白 + 粉鼻头，无胡须/无眉毛/无爪子/无亮弧）
排版：左上「结语 / Epilogue」标题块 + 右上角标 + 进度线 + 底部中英双字体
用法：python tools/frame105f.py [输出路径]
"""
import math
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
S = 2  # 超采样倍数
F_CN = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"
F_EN_I = r"C:\Windows\Fonts\BOD_I.TTF"
F_EN = r"C:\Windows\Fonts\BOD_R.TTF"

INK = (246, 244, 240)
WHITE = (234, 232, 228)
G3 = (120, 116, 110)
BROWN = (176, 128, 96)
CREAM = (246, 239, 226)
IRIS = (58, 32, 24)
PINK = (232, 160, 168)


def f(p, s):
    return ImageFont.truetype(p, s)


def draw_cat(canvas):
    """在超采样画布上画猫头（坐标按 1920x1080 设计，乘 S）"""
    c = Image.new("RGBA", canvas, (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    cx, cy = 960 * S, 430 * S
    rx, ry = 252 * S, 232 * S

    # 耳朵（圆角三角）：用多边形 + 粗描边模拟
    def ear(sign):
        bx = cx + sign * 150 * S
        pts = [(bx - sign * 78 * S, cy - 150 * S),
               (bx + sign * 12 * S, cy - 268 * S),
               (bx + sign * 96 * S, cy - 132 * S)]
        d.polygon(pts, fill=(6, 5, 5, 255))
        d.line(pts + [pts[0]], fill=BROWN, width=13 * S, joint="curve")
        inner = [(bx - sign * 40 * S, cy - 168 * S),
                 (bx + sign * 10 * S, cy - 236 * S),
                 (bx + sign * 58 * S, cy - 150 * S)]
        d.polygon(inner, fill=(22, 17, 17, 255))

    ear(-1)
    ear(1)

    # 头
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(6, 5, 5, 255),
              outline=BROWN, width=13 * S)

    # 眼睛
    for sign in (-1, 1):
        ex = cx + sign * 104 * S
        ey = cy - 6 * S
        ew, eh = 96 * S, 108 * S
        d.ellipse([ex - ew, ey - eh, ex + ew, ey + eh], fill=CREAM, outline=BROWN, width=9 * S)
        ix, iy, ir = ex + sign * 8 * S, ey + 14 * S, 62 * S
        d.ellipse([ix - ir, iy - ir * 1.08, ix + ir, iy + ir * 1.08], fill=IRIS)
        hr = 17 * S
        d.ellipse([ix - 34 * S - hr, iy - 40 * S - hr, ix - 34 * S + hr, iy - 40 * S + hr],
                  fill=(255, 255, 255, 235))

    # 鼻子：小小的圆润倒三角（不是蝴蝶结）
    ny = cy + 84 * S
    w2, h2 = 24 * S, 18 * S
    d.polygon([(cx - w2, ny - h2 * 0.55), (cx + w2, ny - h2 * 0.55), (cx, ny + h2)],
              fill=PINK)
    d.ellipse([cx - w2, ny - h2 * 0.95, cx + w2, ny + h2 * 0.95], fill=PINK)

    # 嘴：鼻子下方一个小小的 ω（两个短弧 + 一竖）
    my = ny + 26 * S
    d.line([(cx, ny + 12 * S), (cx, my)], fill=CREAM, width=8 * S)
    aw = 30 * S
    d.arc([cx - aw * 2, my - aw, cx, my + aw * 1.2], 350, 140, fill=CREAM, width=8 * S)
    d.arc([cx, my - aw, cx + aw * 2, my + aw * 1.2], 40, 190, fill=CREAM, width=8 * S)

    return c


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else r"E:\deepseek\.tmp\vibe\frame105_vfinal.png"

    big = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 255))
    # 背景极淡径向光
    yy, xx = np.mgrid[0:H * S, 0:W * S].astype(np.float32)
    d = np.sqrt(((xx - W * S * 0.5) / (W * S * 0.62)) ** 2 + ((yy - H * S * 0.42) / (H * S * 0.62)) ** 2)
    glow = (np.clip(1 - d, 0, 1) ** 2.8) * 16
    bg = glow[:, :, None] * np.array([1.0, 1.0, 1.08])
    big = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert("RGBA")

    cat = draw_cat((W * S, H * S))
    # 整体轻微歪头
    cat = cat.rotate(-2.2, resample=Image.BICUBIC, center=(960 * S, 430 * S))
    big.alpha_composite(cat)

    img = big.resize((W, H), Image.LANCZOS)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(layer)
    dr.text((96, 78), "结语", font=f(F_CN, 40), fill=WHITE + (232,))
    dr.text((96, 132), "Epilogue", font=f(F_EN_I, 30), fill=G3 + (215,))
    dr.line([(96, 182), (330, 182)], fill=(150, 147, 142, 120), width=1)
    dr.text((W - 300, 82), "CURSORLAB", font=f(F_EN, 24), fill=G3 + (175,))
    dr.text((W - 300, 116), "06 / 06", font=f(F_EN, 22), fill=G3 + (125,))
    dr.line([(96, 200), (W - 300, 200)], fill=(80, 78, 76, 90), width=1)
    dr.line([(96, 200), (96 + int((W - 396) * 105.0 / 126.9), 200)], fill=(224, 222, 218, 130), width=1)

    main_cn = "全程，我只说了我想要什么"
    fc = f(F_CN, 66)
    mw = dr.textlength(main_cn, font=fc)
    dr.text(((W - mw) / 2, H - 176), main_cn, font=fc, fill=INK + (244,))

    sub = "all I ever said was: this is what I want"
    fe = f(F_EN_I, 32)
    ew = sum(dr.textlength(ch, font=fe) + 4 for ch in sub)
    sx = (W - ew) / 2
    for ch in sub:
        dr.text((sx, H - 96), ch, font=fe, fill=WHITE + (168,))
        sx += dr.textlength(ch, font=fe) + 4

    img.alpha_composite(layer)

    a = np.asarray(img.convert("RGB"), dtype=np.float32)
    a += np.random.default_rng(105).normal(0, 1.6, (H, W, 1))
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB").save(out)
    print("saved", out)


if __name__ == "__main__":
    main()
