# -*- coding: utf-8 -*-
"""
单帧效果图：105.0s「猫眼特写 · 几乎静止」
- 中英双字体：中文 Noto Sans SC / 英文 Bodoni Italic
- 左上角恢复"标题块"（用户认可的版式）
- 眼睛程序化绘制（大尺寸下依然锐利），四周留深色毛影与边缘光

用法：python tools/frame105.py
产物：E:\deepseek\.tmp\vibe\frame105.png
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
WORK = r"E:\deepseek\.tmp\vibe"
F_CN = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"
F_EN_I = r"C:\Windows\Fonts\BOD_I.TTF"
F_EN = r"C:\Windows\Fonts\BOD_R.TTF"

INK = (244, 244, 248)
G1 = (198, 200, 208)
G3 = (104, 107, 116)


def f(path, size):
    return ImageFont.truetype(path, size)


# ---------------- 背景
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
d = np.sqrt(((xx - W * 0.52) / (W * 0.62)) ** 2 + ((yy - H * 0.46) / (H * 0.62)) ** 2)
bg = (np.clip(1 - d, 0, 1) ** 2.6)[:, :, None] * np.array([20, 21, 26], dtype=np.float32)
bg *= np.clip(1.06 - d * 0.8, 0.22, 1.0)[:, :, None]
img = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8), "RGB").convert("RGBA")

# 一束斜光
beam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(beam).polygon([(W * 0.28, H * 1.2), (W * 0.60, -H * 0.2), (W * 0.88, -H * 0.2)],
                             fill=(214, 218, 232, 54))
img.alpha_composite(beam.filter(ImageFilter.GaussianBlur(70)))

# ---------------- 猫脸暗影（只留轮廓感）
face = Image.new("RGBA", (W, H), (0, 0, 0, 0))
fd = ImageDraw.Draw(face)
fd.ellipse([W * 0.16, H * 0.02, W * 0.92, H * 1.10], fill=(12, 12, 15, 255))
# 耳朵
fd.polygon([(W * 0.20, H * 0.30), (W * 0.24, H * 0.02), (W * 0.40, H * 0.18)],
           fill=(12, 12, 15, 255))
fd.polygon([(W * 0.76, H * 0.16), (W * 0.90, H * 0.00), (W * 0.90, H * 0.28)],
           fill=(12, 12, 15, 255))
# 边缘光
rim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(rim).ellipse([W * 0.16, H * 0.02, W * 0.92, H * 1.10],
                            outline=(180, 186, 204, 90), width=5)
rim = rim.filter(ImageFilter.GaussianBlur(6))
rim.putalpha(rim.split()[3].point(lambda v: int(v * 0.55)))
img.alpha_composite(face.filter(ImageFilter.GaussianBlur(9)))
img.alpha_composite(rim)

# ---------------- 眼睛（程序化，锐利）
cx, cy = W * 0.50, H * 0.47
EW, EH = 360, 300           # 眼白半径
eye = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ed = ImageDraw.Draw(eye)

# 眼窝阴影
ed.ellipse([cx - EW - 30, cy - EH - 30, cx + EW + 30, cy + EH + 30],
           fill=(8, 8, 10, 160))
# 眼白（略带灰，避免死白）
ed.ellipse([cx - EW, cy - EH, cx + EW, cy + EH], fill=(236, 237, 242, 255))
# 瞳（深色，位置略偏内下，看向镜头）
PW, PH = 200, 236
px, py = cx + 8, cy + 18
ed.ellipse([px - PW, py - PH, px + PW, py + PH], fill=(20, 20, 24, 255))
# 瞳内渐变（上暗下稍亮）
grad = Image.new("L", (1, PH * 2))
for i in range(PH * 2):
    grad.putpixel((0, i), int(255 - 120 * (1 - i / (PH * 2))))
grad = grad.resize((PW * 2, PH * 2))
shade = Image.composite(Image.new("RGBA", (PW * 2, PH * 2), (44, 44, 52, 255)),
                        Image.new("RGBA", (PW * 2, PH * 2), (10, 10, 12, 255)), grad)
mask = Image.new("L", (PW * 2, PH * 2), 0)
ImageDraw.Draw(mask).ellipse([0, 0, PW * 2 - 1, PH * 2 - 1], fill=255)
eye.paste(shade, (int(px - PW), int(py - PH)), mask)

# 高光（两点，主光在左上）
ed = ImageDraw.Draw(eye)
ed.ellipse([px - 96, py - 132, px - 26, py - 62], fill=(255, 255, 255, 235))
ed.ellipse([px + 46, py + 54, px + 92, py + 100], fill=(255, 255, 255, 120))
# 眼白上缘的暖反光
ed.arc([cx - EW, cy - EH, cx + EW, cy + EH], start=196, end=344,
       fill=(206, 212, 230, 150), width=10)
# 眼睑线（上缘一道深色弧）
ed.arc([cx - EW - 6, cy - EH - 10, cx + EW + 6, cy + EH - 10], start=186, end=354,
       fill=(14, 14, 17, 220), width=12)

# 眼白内的柔光
soft = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(soft).ellipse([cx - EW * 0.9, cy - EH * 0.9, cx + EW * 0.3, cy + EH * 0.1],
                             fill=(255, 255, 255, 26))
eye.alpha_composite(soft.filter(ImageFilter.GaussianBlur(40)))
img.alpha_composite(eye)

# 眼睛的高光溢出
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(glow).ellipse([cx - EW * 0.7, cy - EH * 0.8, cx + EW * 0.1, cy + EH * 0.1],
                             fill=(255, 255, 250, 20))
img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(90)))

# ---------------- 排版：左上角标题块 + 中英双字体
layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
dl = ImageDraw.Draw(layer)

# 左上：章节
dl.text((96, 78), "结语", font=f(F_CN, 40), fill=G1 + (215,))
dl.text((96, 132), "Epilogue", font=f(F_EN_I, 30), fill=G3 + (205,))
dl.line([(96, 182), (330, 182)], fill=(110, 113, 124, 130), width=1)
# 右上：角标
dl.text((W - 300, 82), "CURSORLAB", font=f(F_EN, 24), fill=G3 + (170,))
dl.text((W - 300, 116), "06 / 06", font=f(F_EN, 22), fill=G3 + (120,))
# 顶部进度线
dl.line([(96, 200), (W - 300, 200)], fill=(90, 93, 102, 60), width=1)
dl.line([(96, 200), (96 + int((W - 396) * 105 / 126.9), 200)], fill=(180, 184, 196, 110), width=1)

# 主句（中）
main_cn = "全程，我只说了我想要什么"
fc = f(F_CN, 72)
mw = dl.textlength(main_cn, font=fc)
dl.text(((W - mw) / 2, H * 0.835), main_cn, font=fc, fill=INK + (240,))
# 副句（英，斜体衬线）
sub_en = "all I ever said was: this is what I want"
fe = f(F_EN_I, 34)
ew = dl.textlength(sub_en, font=fe) + 4 * (len(sub_en) - 1)
sx = (W - ew) / 2
for ch in sub_en:
    dl.text((sx, H * 0.835 + 84), ch, font=fe, fill=G1 + (150,))
    sx += dl.textlength(ch, font=fe) + 4

img.alpha_composite(layer)

# ---------------- 颗粒 + 暗角
arr = np.asarray(img.convert("RGB"), dtype=np.float32)
arr += np.random.default_rng(105).normal(0, 2.8, (H, W, 1))
img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")

os.makedirs(WORK, exist_ok=True)
p = os.path.join(WORK, "frame105.png")
img.save(p)
print("saved", p)
