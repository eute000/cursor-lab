# -*- coding: utf-8 -*-
"""
105.0s 帧 · 回到"改之前"的罗小黑有色版构图，只优化亮光：
  * 右侧那道硬亮弧压暗（横向渐变衰减）
  * 加一层柔光 bloom（亮处溢光），让"光"变成氛围而不是硬条
  * 暗角 + 细颗粒，其余构图与排版不动

用法：python tools/frame105g.py <图片> <输出>
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
F_CN = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"
F_EN_I = r"C:\Windows\Fonts\BOD_I.TTF"
F_EN = r"C:\Windows\Fonts\BOD_R.TTF"

INK = (244, 242, 238)
WARM = (236, 220, 204)
G3 = (118, 114, 108)


def f(p, s):
    return ImageFont.truetype(p, s)


def main():
    src, out = sys.argv[1], sys.argv[2]
    base = Image.open(src).convert("RGB")

    # 与旧版一致：等比铺满 + 轻微上移
    scale = max(W / base.width, H / base.height) * 1.02
    base = base.resize((int(base.width * scale), int(base.height * scale)), Image.LANCZOS)
    ox = (base.width - W) // 2
    oy = int((base.height - H) * 0.42)
    img = base.crop((ox, oy, ox + W, oy + H))

    arr = np.asarray(img, dtype=np.float32)

    # ① 右侧硬亮弧压暗：x 从 0.72 到 1.0 平滑降到 0.45
    xs = np.arange(W, dtype=np.float32)[None, :]
    t = np.clip((xs / W - 0.72) / 0.28, 0, 1)
    right_dim = (1 - 0.55 * (t ** 1.6))
    arr *= right_dim[:, :, None]

    # ② 柔光 bloom：提亮区溢光（光变成氛围，而不是一条硬边）
    lum = arr.max(axis=2)
    bright = np.clip((lum - 120) / 135, 0, 1)[:, :, None] * arr
    bloom = Image.fromarray(np.clip(bright, 0, 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(38))
    arr = np.clip(arr + np.asarray(bloom, dtype=np.float32) * 0.55, 0, 255)

    # ③ 暗角
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dv = np.sqrt(((xx - W * 0.5) / (W * 0.62)) ** 2 + ((yy - H * 0.46) / (H * 0.62)) ** 2)
    arr *= np.clip(1.06 - dv * 0.5, 0.42, 1.0)[:, :, None]

    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")

    # 排版（与旧版一致）
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text((96, 78), "结语", font=f(F_CN, 40), fill=WARM + (230,))
    d.text((96, 132), "Epilogue", font=f(F_EN_I, 30), fill=G3 + (215,))
    d.line([(96, 182), (330, 182)], fill=(150, 143, 133, 120), width=1)
    d.text((W - 300, 82), "CURSORLAB", font=f(F_EN, 24), fill=G3 + (175,))
    d.text((W - 300, 116), "06 / 06", font=f(F_EN, 22), fill=G3 + (125,))
    d.line([(96, 200), (W - 300, 200)], fill=(80, 78, 74, 90), width=1)
    d.line([(96, 200), (96 + int((W - 396) * 105.0 / 126.9), 200)], fill=(228, 212, 196, 130), width=1)

    main_cn = "全程，我只说了我想要什么"
    fc = f(F_CN, 68)
    mw = d.textlength(main_cn, font=fc)
    d.text(((W - mw) / 2, H - 190), main_cn, font=fc, fill=INK + (242,))

    sub = "all I ever said was: this is what I want"
    fe = f(F_EN_I, 33)
    ew = sum(d.textlength(c, font=fe) + 4 for c in sub)
    sx = (W - ew) / 2
    for ch in sub:
        d.text((sx, H - 104), ch, font=fe, fill=WARM + (165,))
        sx += d.textlength(ch, font=fe) + 4

    img.alpha_composite(layer)

    a = np.asarray(img.convert("RGB"), dtype=np.float32)
    a += np.random.default_rng(105).normal(0, 2.0, (H, W, 1))
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB").save(out)
    print("saved", out)


if __name__ == "__main__":
    main()
