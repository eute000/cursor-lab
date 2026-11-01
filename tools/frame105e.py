# -*- coding: utf-8 -*-
"""
105.0s 帧 · 用"上一版有色猫"（暖棕描边 + 粉鼻头）+ 猫头椭圆裁切（顺带切掉外侧胡须）
用法：python tools/frame105e.py <图片> <输出> [缩放比]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
F_CN = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"
F_EN_I = r"C:\Windows\Fonts\BOD_I.TTF"
F_EN = r"C:\Windows\Fonts\BOD_R.TTF"
INK = (246, 244, 240)
WHITE = (234, 232, 228)
G3 = (120, 116, 110)


def f(p, s):
    return ImageFont.truetype(p, s)


def main():
    src, out = sys.argv[1], sys.argv[2]
    ratio = float(sys.argv[3]) if len(sys.argv) > 3 else 0.56

    cat = Image.open(src).convert("RGB")
    arr = np.asarray(cat, dtype=np.float32)
    arr = np.where(arr < 46, 0, arr)

    # 用棕色描边定位猫头，再按头做椭圆裁切（外侧胡须被切掉）
    R, G, B = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    brown = (R - B > 35) & (R > 100)
    ys, xs = np.nonzero(brown)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    cxm, cym = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = (x1 - x0) * 0.502, (y1 - y0) * 0.502

    # 环带清扫：头轮廓外一圈里的高亮细线（胡须/眉毛残段）直接抹黑
    gy, gx = np.mgrid[0:arr.shape[0], 0:arr.shape[1]].astype(np.float32)
    rr = np.sqrt(((gx - cxm) / rx) ** 2 + ((gy - cym) / ry) ** 2)
    band = (rr > 0.94)
    mn = arr.min(axis=2)
    arr[np.logical_and(band, mn > 110)] = 0

    cat_im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    mask = Image.new("L", cat_im.size, 0)
    ImageDraw.Draw(mask).ellipse([cxm - rx, cym - ry, cxm + rx, cym + ry], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(3))
    cat_im.putalpha(mask)
    cat_im = cat_im.crop((int(cxm - rx), int(cym - ry), int(cxm + rx), int(cym + ry)))

    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    tw = int(W * ratio)
    cat_im = cat_im.resize((tw, int(cat_im.height * tw / cat_im.width)), Image.LANCZOS)
    img.alpha_composite(cat_im, ((W - cat_im.width) // 2, 46))

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text((96, 78), "结语", font=f(F_CN, 40), fill=WHITE + (232,))
    d.text((96, 132), "Epilogue", font=f(F_EN_I, 30), fill=G3 + (215,))
    d.line([(96, 182), (330, 182)], fill=(150, 147, 142, 120), width=1)
    d.text((W - 300, 82), "CURSORLAB", font=f(F_EN, 24), fill=G3 + (175,))
    d.text((W - 300, 116), "06 / 06", font=f(F_EN, 22), fill=G3 + (125,))
    d.line([(96, 200), (W - 300, 200)], fill=(80, 78, 76, 90), width=1)
    d.line([(96, 200), (96 + int((W - 396) * 105.0 / 126.9), 200)], fill=(224, 222, 218, 130), width=1)

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
