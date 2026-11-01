# -*- coding: utf-8 -*-
"""
单镜试做：8.5–10.7s「白箭头炸成粒子 → 重组成黑猫」
字体：Noto Sans SC（与 DSH 界面同款，NotoSansSC-VF.ttf）
用法：python tools/seg5.py [开始] [结束]
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cursorlab import cartoon  # noqa: E402

W, H, FPS = 1920, 1080, 30
WORK = r"E:\deepseek\.tmp\vibe"
FF = r"D:\python\huanjing\ffmpeg.exe"
F_UI = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"

BM = np.load(os.path.join(WORK, "beatmap.npz"))
BEATS, STRENGTH = BM["beats"], BM["strength"]
INK = (242, 242, 246)
G3 = (104, 107, 116)


def fnt(size, weight=None):
    f = ImageFont.truetype(F_UI, size)
    return f


# ---------------- 背景（同全片：纯黑 + 淡径向 + 暗角）
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
_d = np.sqrt(((xx - W * 0.5) / (W * 0.66)) ** 2 + ((yy - H * 0.46) / (H * 0.66)) ** 2)
_bg = (np.clip(1 - _d, 0, 1) ** 2.8)[:, :, None] * np.array([20, 20, 25], dtype=np.float32)
_bg *= np.clip(1.06 - _d * 0.8, 0.2, 1.0)[:, :, None]
BG = Image.fromarray(np.clip(_bg, 0, 255).astype(np.uint8), "RGB")

BEAM = Image.new("RGBA", (W, H), (0, 0, 0, 0))
_bd = ImageDraw.Draw(BEAM)
_bd.polygon([(W * 0.30, H * 1.15), (W * 0.62, -H * 0.15), (W * 0.86, -H * 0.15)],
            fill=(214, 218, 232, 60))
BEAM = BEAM.filter(ImageFilter.GaussianBlur(60))


def arrow_sprite(px):
    base = 512
    im = Image.new("RGBA", (base, base), (0, 0, 0, 0))
    pts = [(150, 88), (150, 356), (222, 286), (286, 408), (338, 382),
           (274, 262), (356, 262)]
    sh = Image.new("RGBA", (base, base), (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon([(x + 6, y + 12) for x, y in pts], fill=(0, 0, 0, 110))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(26)))
    face = Image.new("RGBA", (base, base), (0, 0, 0, 0))
    ImageDraw.Draw(face).polygon(pts, fill=(238, 239, 243, 255))
    im.alpha_composite(face)
    return im.resize((px, px), Image.LANCZOS)


def crop_square(im):
    bb = im.split()[3].getbbox()
    im = im.crop(bb)
    side = max(im.size)
    out = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    out.alpha_composite(im, ((side - im.width) // 2, (side - im.height) // 2))
    return out


ARROW = crop_square(arrow_sprite(420))
CAT = crop_square(cartoon.render("arrow", 420))
SIDE = max(ARROW.width, CAT.width)
ARROW = ARROW.resize((SIDE, SIDE), Image.LANCZOS) if ARROW.size != (SIDE, SIDE) else ARROW
CAT = CAT.resize((SIDE, SIDE), Image.LANCZOS) if CAT.size != (SIDE, SIDE) else CAT
CAT_GLOW = CAT.filter(ImageFilter.GaussianBlur(14))


def sample(img, n, seed):
    a = np.asarray(img.split()[3])
    ys, xs = np.nonzero(a > 128)
    idx = np.random.default_rng(seed).integers(0, len(xs), n)
    return np.stack([xs[idx], ys[idx]], axis=1).astype(np.float32)


N = 3000
ORIGIN = np.array([W / 2 - SIDE / 2, H * 0.46 - SIDE / 2], dtype=np.float32)
P_A = sample(ARROW, N, 7) + ORIGIN
P_C = sample(CAT, N, 9) + ORIGIN
_r = np.random.default_rng(21)
D = _r.uniform(0, 0.45, N)           # 每颗粒子的出发延迟
JIT = _r.normal(0, 1, (N, 2)).astype(np.float32)
BURST = _r.normal(0, 1, (N, 2)).astype(np.float32)


def ease(x):
    x = np.clip(x, 0, 1)
    return 1 - (1 - x) ** 3


def frame_at(t, t0=8.5, t1=10.75):
    lt = t - t0
    img = BG.convert("RGBA").copy()
    img.alpha_composite(BEAM)
    d = ImageDraw.Draw(img)

    # 时间轴（本地秒）：0-0.5 箭头完整 → 0.5-1.0 炸开 → 1.0-1.9 聚成猫 → 1.9+ 定型
    # 顿挫：炸开(0.45-0.95) → 停顿(0.95-1.45) → 三帧速合(1.45-1.55) → 定型
    k = float(np.interp(lt, [0.0, 0.45, 0.95, 1.45, 1.55, 9.0],
                        [0.0, 0.0, 0.42, 0.50, 1.0, 1.0]))

    if k <= 0.01:
        img.alpha_composite(ARROW, (int(ORIGIN[0]), int(ORIGIN[1])))
    else:
        # 炸开量：先大后收
        burst = math.sin(math.pi * min(1.0, k)) ** 0.8
        e = ease(np.clip((k - D * 0.55) / 0.9, 0, 1))
        pts = P_A * (1 - e[:, None]) + P_C * e[:, None]
        pts = pts + BURST * (26 + 90 * burst) * (1 - e[:, None] * 0.85)
        trail = 1 if k < 0.9 else 2
        alpha = int(235 * (1 - 0.25 * burst))
        for s in range(trail):
            off = s * 3 * burst
            col = (238, 240, 246, int(alpha * (1 - 0.35 * s)))
            for i in range(0, N, 1):
                x, y = pts[i]
                d.ellipse([x - 1.4 - off * 0.2, y - 1.4 - off * 0.2,
                           x + 1.4 + off * 0.2, y + 1.4 + off * 0.2], fill=col)
        if k > 0.93:
            a = int(255 * min(1.0, (k - 0.93) / 0.07))
            cg, ca = CAT_GLOW.copy(), CAT.copy()
            cg.putalpha(cg.split()[3].point(lambda v: int(v * a / 255)))
            ca.putalpha(ca.split()[3].point(lambda v: int(v * a / 255)))
            img.alpha_composite(cg, (int(ORIGIN[0]), int(ORIGIN[1])))
            img.alpha_composite(ca, (int(ORIGIN[0]), int(ORIGIN[1])))

    # 字幕（与界面同款字体）
    if lt > 1.15:
        a = int(240 * min(1.0, (lt - 1.15) / 0.35))
        txt = "于是，我自己做了一只"
        f = fnt(66)
        w = d.textlength(txt, font=f)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text(((W - w) / 2, H * 0.82), txt, font=f, fill=INK + (a,))
        img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.4)))

    # 合体瞬间的白闪（2 帧）
    if 1.45 <= lt < 1.52:
        flash = Image.new("RGBA", (W, H), (255, 255, 255, 38))
        img.alpha_composite(flash)

    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    arr += np.random.default_rng(int(t * 1000)).normal(0, 2.6, (H, W, 1))
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def main():
    a = float(sys.argv[1]) if len(sys.argv) > 1 else 8.5
    b = float(sys.argv[2]) if len(sys.argv) > 2 else 10.75
    out = os.path.join(WORK, "seg5_%.1f_%.1f.mp4" % (a, b))
    audio = os.path.join(WORK, "seg5.wav")
    subprocess.run([FF, "-y", "-i", os.path.join(WORK, "bgm.wav"), "-ss", "%.2f" % a,
                    "-t", "%.2f" % (b - a), audio], check=True, capture_output=True)
    cmd = [FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
           "-r", str(FPS), "-i", "-", "-i", audio,
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    for i in range(int(a * FPS), int(b * FPS)):
        p.stdin.write(frame_at(i / FPS).tobytes())
    p.stdin.close()
    p.wait()
    print("saved", out)


if __name__ == "__main__":
    main()
