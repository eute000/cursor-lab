# -*- coding: utf-8 -*-
"""
vibe知识大赏 · 冷开场 v3（跟随真实 BGM 的拍点 / 橙色点缀 / 水波涟漪）

改动（对应用户意见）：
  * 重点字放大 + 橙色强调（#FF7A2F），整体只做"点缀"，不铺满
  * 开场鼠标缩小（0.26→0.46），并给它加一个橙色热点
  * 涟漪改成水波：每拍 4 层同心椭圆，越外越淡，带轻微竖向压扁
  * 律动条更灵性：高度由 BGM 每拍强度插值驱动，强拍染橙，带轻微横向抖动
  * 时间轴改用 beatmap.npz（112.3 BPM / 首拍 0.100s）

用法：python tools/vibe_video3.py [秒数]
"""
import math
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1920, 1080, 30
WORK = r"E:\deepseek\.tmp\vibe"
FF = r"D:\python\huanjing\ffmpeg.exe"

BM = np.load(os.path.join(WORK, "beatmap.npz"))
BPM = float(BM["bpm"])
BEAT = float(BM["beat"])
PHASE = float(BM["phase"])
BEATS = BM["beats"]
STRENGTH = BM["strength"]

INK = (245, 245, 248)
DIM = (108, 108, 118)
ORANGE = (255, 122, 47)
ORANGE_DIM = (255, 122, 47)

FONT_SERIF = [r"C:\Windows\Fonts\STZHONGS.TTF", r"C:\Windows\Fonts\simsun.ttc",
              r"C:\Windows\Fonts\msyhbd.ttc"]
FONT_SANS = [r"C:\Windows\Fonts\msyh.ttc"]


def font(paths, size):
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


# ------------------------------------------------------------------ 背景
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
_d = np.sqrt(((xx - W * 0.5) / (W * 0.66)) ** 2 + ((yy - H * 0.46) / (H * 0.66)) ** 2)
_glow = np.clip(1.0 - _d, 0, 1) ** 2.8
_bg = _glow[:, :, None] * np.array([16, 16, 20], dtype=np.float32)
_bg *= np.clip(1.06 - _d * 0.8, 0.22, 1.0)[:, :, None]
BG_IMG = Image.fromarray(np.clip(_bg, 0, 255).astype(np.uint8), "RGB")

RNG = np.random.default_rng(20261101)
MOTE_N = 200
mote_x = RNG.uniform(0, W, MOTE_N)
mote_y = RNG.uniform(0, H, MOTE_N)
mote_r = RNG.uniform(0.5, 1.9, MOTE_N)
mote_v = RNG.uniform(4, 16, MOTE_N)
mote_a = RNG.uniform(12, 55, MOTE_N)


def arrow_sprite(px):
    base = 512
    im = Image.new("RGBA", (base, base), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = [(150, 88), (150, 356), (222, 286), (286, 408), (338, 382),
           (274, 262), (356, 262)]
    sh = Image.new("RGBA", (base, base), (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon([(x + 8, y + 14) for x, y in pts], fill=(0, 0, 0, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    d.polygon(pts, fill=(244, 244, 248, 255))
    hi = Image.new("RGBA", (base, base), (0, 0, 0, 0))
    ImageDraw.Draw(hi).polygon([(162, 104), (162, 320), (206, 274), (250, 264)],
                               fill=(255, 255, 255, 120))
    im.alpha_composite(hi.filter(ImageFilter.GaussianBlur(10)))
    d.line(pts + [pts[0]], fill=(10, 10, 14, 205), width=5, joint="curve")
    return im.resize((px, px), Image.LANCZOS)


ARROW = arrow_sprite(760)
ARROW_GLOW = ARROW.filter(ImageFilter.GaussianBlur(30))


def grain(seed):
    return np.random.default_rng(seed).normal(0, 3.0, (H, W, 1)).astype(np.float32)


# ------------------------------------------------------------------ 律动驱动
def beat_strength(t):
    """把每拍强度插值成连续曲线（0..1），用来驱动律动条"""
    i = np.searchsorted(BEATS, t) - 1
    if i < 0:
        return 0.0
    if i >= len(BEATS) - 1:
        return float(STRENGTH[-1])
    t0, t1 = BEATS[i], BEATS[i + 1]
    k = (t - t0) / max(1e-6, (t1 - t0))
    k = k ** 0.6
    return float(STRENGTH[i] * (1 - k) + STRENGTH[i + 1] * k)


def since_beat(t):
    """距离最近一个拍点的秒数 + 该拍强度"""
    i = np.searchsorted(BEATS, t) - 1
    if i < 0:
        return 9.9, 0.0
    return t - BEATS[i], float(STRENGTH[i])


# ------------------------------------------------------------------ 水波涟漪
def water_ripples(img, cx, cy, t, life=1.8, max_r=1000):
    d = ImageDraw.Draw(img)
    i = np.searchsorted(BEATS, t) - 1
    for j in range(max(0, i - 2), i + 1):
        age = t - BEATS[j]
        if not (0 <= age < life):
            continue
        p = age / life
        s = float(STRENGTH[j])
        base_r = 90 + max_r * (p ** 0.55)
        for k, mul in enumerate((1.0, 0.78, 0.56, 0.34)):
            r = base_r * mul
            a = int((70 + 40 * s) * (1 - p) ** 1.6 * (1 - 0.18 * k))
            if a <= 2:
                continue
            ry = r * 0.30
            col = (205, 210, 235, a) if k % 2 == 0 else (255, 150, 90, int(a * 0.55))
            d.ellipse([cx - r, cy - ry, cx + r, cy + ry], outline=col, width=2)


def eq_strip(img, t, bars=64):
    """更灵性的律动条：高度由拍点强度插值 + 每根条独立相位 + 强拍染橙"""
    d = ImageDraw.Draw(img)
    s_now = beat_strength(t)
    step = W / bars
    for i in range(bars):
        ph = i * 0.37
        wave = 0.55 + 0.45 * abs(math.sin(t * 2.4 + ph))
        h = 5 + 54 * (0.35 * wave + 0.85 * s_now) * (0.55 + 0.45 * math.sin(ph * 2.1))
        h = min(72, max(3, h))
        jitter = math.sin(t * 6 + i) * 1.2
        x = i * step + 5 + jitter
        orange = s_now > 0.42 and i % 3 == 0
        col = (ORANGE[0], ORANGE[1], ORANGE[2], int(70 + 120 * s_now)) if orange \
            else (200, 206, 235, int(40 + 90 * s_now))
        d.rectangle([x, H - 30 - h, x + step * 0.38, H - 30], fill=col)


def label(img, text, xy, size=26, color=DIM, alpha=90):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(xy, text, font=font(FONT_SANS, size), fill=color + (alpha,))
    img.alpha_composite(layer)


# ------------------------------------------------------------------ 文字（橙色重点）
def draw_title(img, parts, cy, t, t0, size=132, spacing=0.13, rise=26):
    """parts = [(文字, 是否橙色)]，逐字浮现，按 8 分音符推进"""
    d = ImageDraw.Draw(img)
    f = font(FONT_SERIF, size)
    gap = int(size * spacing)
    chars = []
    for text, hot in parts:
        for ch in text:
            chars.append((ch, hot))
    widths = [d.textlength(ch, font=f) for ch, _ in chars]
    total = sum(widths) + gap * (len(chars) - 1)
    x = (W - total) / 2
    breathe = math.sin(t * 0.8) * 1.8
    step = BEAT / 2
    for i, (ch, hot) in enumerate(chars):
        local = t - (t0 + i * step)
        if local <= 0:
            x += widths[i] + gap
            continue
        k = min(1.0, local / 0.45)
        k = 1 - (1 - k) ** 3
        a = int(255 * k)
        dy = (1 - k) * rise + breathe
        col = (ORANGE if hot else INK) + (a,)
        layer = Image.new("RGBA", (int(widths[i]) + 64, size * 2), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((32, size * 0.35), ch, font=f, fill=col)
        gl = layer.filter(ImageFilter.GaussianBlur(10 if hot else 7))
        pos = (int(x) - 32, int(cy - size * 0.35 + dy) - 32)
        img.alpha_composite(gl, pos)
        img.alpha_composite(layer, pos)
        x += widths[i] + gap


ARROW_CX, ARROW_CY = W * 0.5, H * 0.70


def frame(i, dur):
    t = i / FPS
    img = BG_IMG.convert("RGBA").copy()
    d = ImageDraw.Draw(img)

    water_ripples(img, ARROW_CX, ARROW_CY, t)
    eq_strip(img, t)

    # 尘埃（拍点加速）
    sb, s_str = since_beat(t)
    kick = math.exp(-sb / 0.18) * (0.4 + 0.6 * s_str)
    for k in range(MOTE_N):
        y = (mote_y[k] - mote_v[k] * (1 + 1.2 * kick) * t) % H
        x = mote_x[k] + math.sin(t * 0.7 + k) * 5
        a = int(mote_a[k] * (0.4 + 0.6 * math.sin(t * 1.1 + k)) * (0.6 + 0.9 * kick))
        d.ellipse([x, y, x + mote_r[k], y + mote_r[k]],
                  fill=(210, 214, 238, max(0, min(255, a))))

    # 鼠标：更小，带橙色热点
    if t > 0.35:
        k = min(1.0, (t - 0.35) / (BEAT * 2.2))
        k = 1 - (1 - k) ** 3
        pulse = 1 + 0.010 * math.exp(-sb / 0.15)
        scale = (0.26 + 0.20 * k) * pulse
        rot = -5 * (1 - k)
        size = int(ARROW.width * scale)
        art = ARROW.resize((size, size), Image.LANCZOS).rotate(rot, resample=Image.BICUBIC)
        gl = ARROW_GLOW.resize((size, size), Image.LANCZOS).rotate(rot, resample=Image.BICUBIC)
        alpha = int(245 * min(1.0, (t - 0.35) / 0.6))
        left, top = int(ARROW_CX - size / 2), int(ARROW_CY - size / 2)
        for layer, mul in ((gl, 0.85), (art, 1.0)):
            a2 = layer.copy()
            a2.putalpha(a2.split()[3].point(lambda v: int(v * mul * alpha / 255)))
            img.alpha_composite(a2, (left, top))
        # 橙色热点（联动"点击点"概念）
        hx = left + size * (150 / 512) * 1.0
        hy = top + size * (88 / 512)
        r = 7 + 5 * math.exp(-sb / 0.2)
        d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=ORANGE + (235,))
        d.ellipse([hx - r * 2.4, hy - r * 2.4, hx + r * 2.4, hy + r * 2.4],
                  outline=ORANGE + (70,), width=2)

    # 标题（重点词橙色 + 更大）
    if t > BEAT * 2.0:
        draw_title(img, [("每一次", False), ("点击", True), ("，", False)],
                   H * 0.30, t, BEAT * 2.0)
    if t > BEAT * 6.0:
        draw_title(img, [("都经过", False), ("它", True), ("。", False)],
                   H * 0.43, t, BEAT * 6.0, size=112, rise=16)

    label(img, "CURSORLAB  ·  A CURSOR STORY", (68, 48), 26, alpha=85)
    label(img, "示意图  |  01 / 06", (W - 400, H - 66), 24, alpha=75)

    arr = np.asarray(img.convert("RGB"), dtype=np.float32) + grain(i)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")

    fade = 1.0
    if t < 0.4:
        fade = t / 0.4
    if t > dur - 1.2:
        fade = max(0.0, (dur - t) / 1.2)
    if fade < 1.0:
        img = Image.eval(img, lambda v: int(v * fade))
    return img


def main():
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0
    n = int(dur * FPS)
    out = os.path.join(WORK, "cold_open_v3_%ds.mp4" % int(dur))
    audio = os.path.join(WORK, "bgm_head.wav")
    subprocess.run([FF, "-y", "-i", os.path.join(WORK, "bgm.wav"), "-t", "%.2f" % dur,
                    "-af", "afade=t=out:st=%.2f:d=1.2" % (dur - 1.2), audio],
                   check=True, capture_output=True)
    print("BPM %.1f / 拍 %.3f 秒 / 时长 %.0f 秒" % (BPM, BEAT, dur))
    cmd = [FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
           "-r", str(FPS), "-i", "-", "-i", audio,
           "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    for i in range(n):
        p.stdin.write(frame(i, dur).tobytes())
        if i % 150 == 0:
            print("  %d/%d" % (i, n), flush=True)
    p.stdin.close()
    p.wait()
    print("saved", out)


if __name__ == "__main__":
    main()
