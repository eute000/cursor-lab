# -*- coding: utf-8 -*-
"""
105.0s「猫眼/猫脸特写」帧 v2：用罗小黑风格的猫脸 + 中英双字体排版
输入：paint_image 生成的猫脸（E:\deepseek\copylee-image-gen\image-ae62bcf8.png）
输出：E:\deepseek\.tmp\vibe\frame105_v2.png
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
WORK = r"E:\deepseek\.tmp\vibe"
import sys
SRC = sys.argv[1] if len(sys.argv) > 1 else r"E:\deepseek\copylee-image-gen\image-ae62bcf8.png"
F_CN = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"
F_EN_I = r"C:\Windows\Fonts\BOD_I.TTF"
F_EN = r"C:\Windows\Fonts\BOD_R.TTF"

INK = (246, 244, 240)
WARM = (232, 214, 196)
G3 = (120, 116, 110)


def f(p, s):
    return ImageFont.truetype(p, s)


base = Image.open(SRC).convert("RGB")
# 等比铺满再轻微上移，给底部留字幕区
scale = max(W / base.width, H / base.height) * 1.02
base = base.resize((int(base.width * scale), int(base.height * scale)), Image.LANCZOS)
off_x = (base.width - W) // 2
off_y = int((base.height - H) * 0.42)
img = base.crop((off_x, off_y, off_x + W, off_y + H)).convert("RGBA")

# 底部压暗（字幕区），顶部也压一点让标题块清楚
scrim = Image.new("L", (W, H), 0)
sd = ImageDraw.Draw(scrim)
for y in range(H):
    v = 0
    if y < 260:
        v = int(120 * (1 - y / 260) ** 1.6)
    if y > H - 360:
        v = max(v, int(215 * ((y - (H - 360)) / 360) ** 1.25))
    sd.line([(0, y), (W, y)], fill=v)
dark = Image.new("RGBA", (W, H), (4, 4, 6, 255))
img = Image.composite(dark, img, scrim)

# ---------------- 排版
layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(layer)

d.text((96, 78), "结语", font=f(F_CN, 40), fill=WARM + (225,))
d.text((96, 132), "Epilogue", font=f(F_EN_I, 30), fill=G3 + (215,))
d.line([(96, 182), (330, 182)], fill=(150, 143, 133, 130), width=1)

d.text((W - 300, 82), "CURSORLAB", font=f(F_EN, 24), fill=G3 + (175,))
d.text((W - 300, 116), "06 / 06", font=f(F_EN, 22), fill=G3 + (125,))

d.line([(96, 200), (W - 300, 200)], fill=(90, 87, 82, 70), width=1)
pw = int((W - 396) * (105.0 / 126.9))
d.line([(96, 200), (96 + pw, 200)], fill=(226, 208, 190, 120), width=1)

main = "全程，我只说了我想要什么"
fc = f(F_CN, 68)
mw = d.textlength(main, font=fc)
d.text(((W - mw) / 2, H - 190), main, font=fc, fill=INK + (242,))

sub = "all I ever said was: this is what I want"
fe = f(F_EN_I, 33)
ew = sum(d.textlength(c, font=fe) + 4 for c in sub)
sx = (W - ew) / 2
for ch in sub:
    d.text((sx, H - 104), ch, font=fe, fill=WARM + (165,))
    sx += d.textlength(ch, font=fe) + 4

img.alpha_composite(layer)

# ---------------- 颗粒
arr = np.asarray(img.convert("RGB"), dtype=np.float32)
arr += np.random.default_rng(105).normal(0, 2.2, (H, W, 1))
out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
p = sys.argv[2] if len(sys.argv) > 2 else os.path.join(WORK, "frame105_v2.png")
out.save(p)
print("saved", p)
