# -*- coding: utf-8 -*-
"""
105.0s 帧（终版）：罗小黑风格黑白猫 + 中英双字体排版
- 纯黑底图（生成时已要求零光晕），只做"压黑 + 缩放到 60% 宽度"
- 左上角标题块 / 右上角标 / 进度线 / 底部中英字幕
用法：python tools/frame105d.py <图片> <输出>
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080
F_CN = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"
F_EN_I = r"C:\Windows\Fonts\BOD_I.TTF"
F_EN = r"C:\Windows\Fonts\BOD_R.TTF"
INK = (246, 244, 240)
WHITE = (234, 232, 228)
G3 = (118, 115, 110)


def f(p, s):
    return ImageFont.truetype(p, s)


def main():
    src, out = sys.argv[1], sys.argv[2]
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))

    cat = Image.open(src).convert("RGB")
    arr = np.asarray(cat, dtype=np.float32)
    arr = np.where(arr < 40, 0, arr)          # 压黑：背景归零

    # 去掉胡须：只擦"脸轮廓之外"的近白色细线（棕描边、粉鼻、眼白都保留）
    # 用"棕色描边"求出猫头包围盒，盒子外的一切高亮像素＝胡须/杂线，全部擦掉
    R, G, B = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    brown = (R - B > 35) & (R > 100)
    ys, xs = np.nonzero(brown)
    if len(xs):
        x0, x1 = xs.min(), xs.max()
        y0, y1 = ys.min(), ys.max()
        inset_x = (x1 - x0) * 0.06
        inset_y = (y1 - y0) * 0.06
        outside = np.ones(arr.shape[:2], dtype=bool)
        outside[int(y0 + inset_y):int(y1 - inset_y), int(x0 + inset_x):int(x1 - inset_x)] = False
        mn = arr.min(axis=2)
        arr[np.logical_and(outside, mn > 120)] = 0
    arr = np.clip(arr * 1.05, 0, 255)
    cat = Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")

    target_w = int(W * 0.60)
    cat = cat.resize((target_w, int(cat.height * target_w / cat.width)), Image.LANCZOS)
    cx, cy = (W - cat.width) // 2, 60
    img.alpha_composite(cat, (cx, cy))

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    d.text((96, 78), "结语", font=f(F_CN, 40), fill=WHITE + (232,))
    d.text((96, 132), "Epilogue", font=f(F_EN_I, 30), fill=G3 + (215,))
    d.line([(96, 182), (330, 182)], fill=(150, 147, 142, 120), width=1)

    d.text((W - 300, 82), "CURSORLAB", font=f(F_EN, 24), fill=G3 + (175,))
    d.text((W - 300, 116), "06 / 06", font=f(F_EN, 22), fill=G3 + (125,))

    d.line([(96, 200), (W - 300, 200)], fill=(80, 78, 76, 90), width=1)
    d.line([(96, 200), (96 + int((W - 396) * 105.0 / 126.9), 200)],
           fill=(224, 222, 218, 130), width=1)

    main_cn = "全程，我只说了我想要什么"
    fc = f(F_CN, 66)
    mw = d.textlength(main_cn, font=fc)
    d.text(((W - mw) / 2, H - 176), main_cn, font=fc, fill=INK + (244,))

    sub = "all I ever said was: this is what I want"
    fe = f(F_EN_I, 32)
    ew = sum(d.textlength(c, font=fe) + 4 for c in sub)
    sx = (W - ew) / 2
    for ch in sub:
        d.text((sx, H - 96), ch, font=fe, fill=WHITE + (168,))
        sx += d.textlength(ch, font=fe) + 4

    img.alpha_composite(layer)

    a = np.asarray(img.convert("RGB"), dtype=np.float32)
    a += np.random.default_rng(105).normal(0, 1.8, (H, W, 1))
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB").save(out)
    print("saved", out)


if __name__ == "__main__":
    main()
