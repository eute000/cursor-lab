# -*- coding: utf-8 -*-
"""
vibe知识大赏风格 · 冷开场 v2（20 秒 / 1920x1080 / 30fps / 无旁白）

相对 v1 的改动：
  * 底色改成**纯黑**（#000000），只留极淡的径向微光与暗角
  * 鼠标图案重画：细描边 + 内高光 + 底部投影，放大不糊
  * 加入**律动元素**：每拍一圈扩散涟漪 + 8 分音符网格呼吸 + 拍点粒子加速
  * BGM 改成 92 BPM 有律动的电子床（kick / 反拍 noise / 8 分 hat / drone / arp）
  * 视觉与音乐共用同一 BPM 网格：涟漪、粒子、文字浮现都落在拍点上

用法：python tools/vibe_video.py
产物：E:\deepseek\.tmp\vibe\cold_open_v2.mp4
"""
import math
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1920, 1080, 30
DUR = 20.0
N = int(DUR * FPS)
BPM = 92.0
BEAT = 60.0 / BPM
WORK = r"E:\deepseek\.tmp\vibe"
FF = r"D:\python\huanjing\ffmpeg.exe"
OUT = os.path.join(WORK, "cold_open_v2.mp4")
BGM = os.path.join(WORK, "cold_open_v2.wav")

INK = (245, 245, 248)
DIM = (110, 110, 120)

FONT_SERIF = [r"C:\Windows\Fonts\STZHONGS.TTF", r"C:\Windows\Fonts\simsun.ttc",
              r"C:\Windows\Fonts\msyhbd.ttc"]
FONT_SANS = [r"C:\Windows\Fonts\msyh.ttc"]


def font(paths, size):
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def make_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W * 0.5) / (W * 0.62)) ** 2 + ((yy - H * 0.46) / (H * 0.62)) ** 2)
    glow = np.clip(1.0 - d, 0, 1) ** 2.6
    bg = glow[:, :, None] * np.array([18, 18, 22], dtype=np.float32)
    vig = np.clip(1.1 - d * 0.85, 0.25, 1.0)
    bg *= vig[:, :, None]
    return Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8), "RGB")


BG_IMG = make_bg()

RNG = np.random.default_rng(20261101)
MOTE_N = 220
mote_x = RNG.uniform(0, W, MOTE_N)
mote_y = RNG.uniform(0, H, MOTE_N)
mote_r = RNG.uniform(0.5, 2.0, MOTE_N)
mote_v = RNG.uniform(4, 18, MOTE_N)
mote_a = RNG.uniform(14, 60, MOTE_N)


def arrow_sprite(px):
    """经典指针重画：白面 + 细描边 + 内高光 + 投影"""
    base = 512
    im = Image.new("RGBA", (base, base), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = [(150, 88), (150, 356), (222, 286), (286, 408), (338, 382),
           (274, 262), (356, 262)]

    sh = Image.new("RGBA", (base, base), (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon([(x + 8, y + 14) for x, y in pts], fill=(0, 0, 0, 130))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))

    d.polygon(pts, fill=(246, 246, 250, 255))
    hi = Image.new("RGBA", (base, base), (0, 0, 0, 0))
    ImageDraw.Draw(hi).polygon([(162, 104), (162, 320), (206, 274), (250, 264)],
                               fill=(255, 255, 255, 120))
    im.alpha_composite(hi.filter(ImageFilter.GaussianBlur(10)))
    d.line(pts + [pts[0]], fill=(12, 12, 16, 210), width=5, joint="curve")

    # 轻扫一下：右上角留一点冷光高光
    return im.resize((px, px), Image.LANCZOS)


ARROW = arrow_sprite(820)
ARROW_GLOW = ARROW.filter(ImageFilter.GaussianBlur(34))


def grain(seed):
    r = np.random.default_rng(seed)
    return r.normal(0, 3.2, (H, W, 1)).astype(np.float32)


def beat_pulses(t, cx, cy, life=1.2, max_r=760):
    out = []
    k = int(t // BEAT)
    for b in range(max(0, k - 3), k + 1):
        age = t - b * BEAT
        if 0 <= age < life:
            p = age / life
            out.append((120 + max_r * (p ** 0.62), int(60 * (1 - p) ** 1.9)))
    return out


def grid_lines(img, t, strength=1.0):
    d = ImageDraw.Draw(img)
    phase = math.sin(2 * math.pi * t / (BEAT / 2))
    for i, y in enumerate((H * 0.30, H * 0.86)):
        a = int((7 + 6 * phase) * strength * (1.0 - 0.25 * i))
        if a > 0:
            d.line([(0, y), (W, y)], fill=(200, 205, 235, a), width=1)


def eq_strip(img, t):
    """底部一条细密律动条：随拍点起伏（音频可视化感）"""
    d = ImageDraw.Draw(img)
    bars = 56
    step = W / bars
    kick = math.exp(-((t % BEAT) / 0.22))
    for i in range(bars):
        env = 0.35 + 0.65 * abs(math.sin(t * (2.1 + (i % 7) * 0.35) + i * 0.7))
        hgt = (6 + 30 * env * (0.45 + 0.75 * kick))
        x = i * step + 6
        a = int(48 + 55 * env * kick)
        d.rectangle([x, H - 34 - hgt, x + step * 0.42, H - 34], fill=(200, 206, 235, a))

def draw_line(img, text, cy, t, t0, stagger=None, size=124, spacing=0.14,
              color=INK, alpha_max=255, rise=26):
    d = ImageDraw.Draw(img)
    f = font(FONT_SERIF, size)
    gap = int(size * spacing)
    widths = [d.textlength(ch, font=f) for ch in text]
    total = sum(widths) + gap * (len(text) - 1)
    x = (W - total) / 2
    breathe = math.sin(t * 0.85) * 2.0
    step = stagger if stagger is not None else (BEAT / 2)
    for i, ch in enumerate(text):
        local = t - (t0 + i * step)
        if local <= 0:
            x += widths[i] + gap
            continue
        k = min(1.0, local / 0.5)
        k = 1 - (1 - k) ** 3
        a = int(alpha_max * k)
        dy = (1 - k) * rise + breathe
        layer = Image.new("RGBA", (int(widths[i]) + 48, size * 2), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((24, size * 0.35), ch, font=f, fill=color + (a,))
        gl = layer.filter(ImageFilter.GaussianBlur(9))
        pos = (int(x) - 24, int(cy - size * 0.35 + dy) - 24)
        img.alpha_composite(gl, pos)
        img.alpha_composite(layer, pos)
        x += widths[i] + gap


def label(img, text, xy, size=30, color=DIM, alpha=110):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(xy, text, font=font(FONT_SANS, size), fill=color + (alpha,))
    img.alpha_composite(layer)


def gen_bgm(path, dur=DUR, bpm=BPM):
    sr = 44100
    n = int(sr * dur)
    t = np.arange(n) / sr
    out = np.zeros(n, dtype=np.float64)
    beat = 60.0 / bpm
    rng = np.random.default_rng(5)

    for k, b in enumerate(np.arange(0, dur, beat)):
        if k % 4 in (0, 2):
            idx = (t >= b)
            age = t[idx] - b
            f = 118 * np.exp(-age * 26) + 44
            out[idx] += 0.5 * np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-age * 7.5)

    for k, b in enumerate(np.arange(beat, dur, beat)):
        if k % 4 in (1, 3):
            idx = (t >= b)
            age = t[idx] - b
            nz = np.convolve(rng.normal(0, 1, age.size), np.ones(90) / 90, mode="same")
            out[idx] += 0.18 * nz * np.exp(-age * 22)

    for b in np.arange(0, dur, beat / 2):
        idx = (t >= b)
        age = t[idx] - b
        nz = np.convolve(rng.normal(0, 1, age.size), np.ones(8) / 8, mode="same")
        out[idx] += 0.055 * nz * np.exp(-age * 60)

    out += 0.10 * np.sin(2 * np.pi * 46 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * t / 8))
    scale = [293.66, 349.23, 440.00, 523.25, 587.33]
    for b in np.arange(beat * 2, dur - 1.0, beat * 2):
        f0 = scale[rng.integers(0, len(scale))] * (2 if rng.random() < 0.35 else 1)
        idx = (t >= b)
        age = t[idx] - b
        tone = np.sin(2 * np.pi * f0 * age) + 0.3 * np.sin(2 * np.pi * 2 * f0 * age)
        out[idx] += 0.075 * tone * np.exp(-age * 3.2)

    out *= np.clip(t / 1.5, 0, 1) ** 0.9
    out *= np.clip((dur - t) / 2.5, 0, 1) ** 0.8
    out = out / max(1e-9, np.abs(out).max()) * 0.62
    stereo = np.stack([out, np.roll(out, 17)], axis=1)
    pcm = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)
    import wave
    with wave.open(path, "wb") as fh:
        fh.setnchannels(2)
        fh.setsampwidth(2)
        fh.setframerate(sr)
        fh.writeframes(pcm.tobytes())


ARROW_CX, ARROW_CY = W * 0.5, H * 0.735


def frame(i):
    t = i / FPS
    img = BG_IMG.convert("RGBA").copy()
    d = ImageDraw.Draw(img)

    grid_lines(img, t, 1.0)
    eq_strip(img, t)
    for r, a in beat_pulses(t, ARROW_CX, ARROW_CY):
        if a > 3:
            d.ellipse([ARROW_CX - r, ARROW_CY - r * 0.34, ARROW_CX + r, ARROW_CY + r * 0.34],
                      outline=(190, 196, 230, a), width=2)

    kick_env = math.exp(-((t % BEAT) / 0.16))
    for k in range(MOTE_N):
        y = (mote_y[k] - mote_v[k] * (1 + 0.8 * kick_env) * t) % H
        x = mote_x[k] + math.sin(t * 0.7 + k) * 5
        a = int(mote_a[k] * (0.45 + 0.55 * math.sin(t * 1.1 + k)) * (0.7 + 0.6 * kick_env))
        d.ellipse([x, y, x + mote_r[k], y + mote_r[k]],
                  fill=(215, 218, 240, max(0, min(255, a))))

    if t > 0.4:
        k = min(1.0, (t - 0.4) / (BEAT * 2.6))
        k = 1 - (1 - k) ** 3
        pulse = 1 + 0.012 * math.exp(-((t % BEAT) / 0.18))
        scale = (0.30 + 0.30 * k) * pulse
        rot = -6 * (1 - k)
        size = int(ARROW.width * scale)
        art = ARROW.resize((size, size), Image.LANCZOS).rotate(rot, resample=Image.BICUBIC)
        gl = ARROW_GLOW.resize((size, size), Image.LANCZOS).rotate(rot, resample=Image.BICUBIC)
        alpha = int(245 * min(1.0, (t - 0.4) / 0.7))
        for layer, mul in ((gl, 0.9), (art, 1.0)):
            a2 = layer.copy()
            a2.putalpha(a2.split()[3].point(lambda v: int(v * mul * alpha / 255)))
            img.alpha_composite(a2, (int(ARROW_CX - size / 2), int(ARROW_CY - size / 2)))

    if t > BEAT * 2.2:
        draw_line(img, "每一次点击，", H * 0.28, t, BEAT * 2.2, size=118)
    if t > BEAT * 5.0:
        draw_line(img, "都经过它。", H * 0.41, t, BEAT * 5.0, size=118, alpha_max=230, rise=18)

    label(img, "CURSORLAB  ·  A CURSOR STORY", (72, 52), 28, alpha=95)
    label(img, "示意图  |  01 / 06", (W - 420, H - 70), 26, alpha=85)

    arr = np.asarray(img.convert("RGB"), dtype=np.float32) + grain(i)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")

    fade = 1.0
    if t < 0.5:
        fade = t / 0.5
    if t > DUR - 1.4:
        fade = max(0.0, (DUR - t) / 1.4)
    if fade < 1.0:
        img = Image.eval(img, lambda v: int(v * fade))
    return img


def main():
    os.makedirs(WORK, exist_ok=True)
    print("BGM 92BPM ...")
    gen_bgm(BGM)
    print("画帧 ...")
    cmd = [FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
           "-r", str(FPS), "-i", "-", "-i", BGM,
           "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    for i in range(N):
        p.stdin.write(frame(i).tobytes())
        if i % 120 == 0:
            print("  %d/%d" % (i, N), flush=True)
    p.stdin.close()
    p.wait()
    print("saved", OUT)


if __name__ == "__main__":
    main()
