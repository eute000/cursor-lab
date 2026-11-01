# -*- coding: utf-8 -*-
"""
第 31 镜试做：3D 玻璃环形相册（一个光点炸开 → 17 张卡片甩出 → 自转）
规范：docs/design-brief-vibe-v3.md
音效：whoosh（展开）+ impact（砸入）+ tick（逐个点亮），numpy 合成

用法：python tools/seg6_ring.py [开始秒] [时长秒]
"""
import math
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cursorlab import cartoon  # noqa: E402

W, H, FPS = 1920, 1080, 30
WORK = r"E:\deepseek\.tmp\vibe"
FF = r"D:\python\huanjing\ffmpeg.exe"
F_UI = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"

BM = np.load(os.path.join(WORK, "beatmap.npz"))
BEATS = BM["beats"]
INK = (242, 242, 246)
G2 = (150, 153, 162)

ROLES = ["arrow", "help", "wait", "appstarting", "crosshair", "ibeam", "nwpen", "no",
         "sizeall", "sizens", "sizewe", "sizenwse", "sizenesw", "uparrow", "hand",
         "pin", "person"]
CARDS = [cartoon.render(r, 150) for r in ROLES]

# ---------------- 背景
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
_d = np.sqrt(((xx - W * 0.5) / (W * 0.7)) ** 2 + ((yy - H * 0.5) / (H * 0.7)) ** 2)
_bg = (np.clip(1 - _d, 0, 1) ** 2.6)[:, :, None] * np.array([22, 22, 28], dtype=np.float32)
BG = Image.fromarray(np.clip(_bg, 0, 255).astype(np.uint8), "RGB")

CX, CY = W * 0.5, H * 0.52
R = 560
SQUASH = 0.38


def font(size):
    return ImageFont.truetype(F_UI, size)


# ---------------- 玻璃卡片
def make_card(idx):
    """返回一张玻璃卡片（含光标图），尺寸 300x300，可缩放"""
    size = 300
    card = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    box = [8, 8, size - 8, size - 8]
    # 主体：半透明白，上亮下暗
    for i in range(box[1], box[3]):
        t = (i - box[1]) / (box[3] - box[1])
        a = int(14 - 8 * t)
        d.line([(box[0], i), (box[2], i)], fill=(255, 255, 255, max(0, a)))
    # 玻璃斜光
    gl = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(gl).polygon([(20, 250), (120, 20), (170, 20), (70, 250)],
                               fill=(255, 255, 255, 26))
    card.alpha_composite(gl.filter(ImageFilter.GaussianBlur(8)))
    # 边缘高光
    d.rounded_rectangle(box, radius=18, outline=(255, 255, 255, 46), width=2)
    # 内部底光
    inner = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(inner).ellipse([40, 120, size - 40, size + 60],
                                  fill=(180, 200, 235, 16))
    card.alpha_composite(inner.filter(ImageFilter.GaussianBlur(26)))
    # 光标
    art = CARDS[idx]
    card.alpha_composite(art, ((size - art.width) // 2, (size - art.height) // 2))
    return card


GLASS = [make_card(i) for i in range(len(ROLES))]


# ---------------- 音效
def synth(dur=9.0, t0_beat=0.0):
    sr = 44100
    n = int(sr * dur)
    t = np.arange(n) / sr
    out = np.zeros(n, dtype=np.float64)
    rng = np.random.default_rng(4)

    def band_noise(lo, hi, dur_s, env_pow=1.6, amp=0.5, reverse=False):
        m = int(sr * dur_s)
        nz = rng.normal(0, 1, m)
        f = np.fft.rfftfreq(m, 1 / sr)
        nz = np.fft.irfft(np.fft.rfft(nz) * ((f > lo) & (f < hi)), m)
        env = np.linspace(0, 1, m) if reverse else np.linspace(1, 0, m)
        return nz / (np.abs(nz).max() + 1e-9) * (env ** env_pow) * amp

    # whoosh：0.15s 起，0.6s 时长
    w = band_noise(500, 5000, 0.6, 2.0, 0.55, reverse=True)
    i0 = int(0.12 * sr)
    out[i0:i0 + len(w)] += w

    # impact：砸入（1.05s）
    b = 1.05
    idx = t >= b
    age = t[idx] - b
    out[idx] += 0.85 * np.sin(2 * np.pi * (58 * np.exp(-age * 9) + 40) * age) * np.exp(-age * 11)
    tr = band_noise(1500, 9000, 0.06, 1.0, 0.5)
    j = int(b * sr)
    out[j:j + len(tr)] += tr

    # tick：环上逐个点亮
    for k, bt in enumerate(BEATS):
        if bt < 1.2 or bt > dur:
            continue
        m = int(0.05 * sr)
        tick = rng.normal(0, 1, m) * np.exp(-np.linspace(0, 8, m)) * 0.10
        f = np.fft.rfftfreq(m, 1 / sr)
        tick = np.fft.irfft(np.fft.rfft(tick) * (f > 1800), m)
        j = int(bt * sr)
        if j + m < n:
            out[j:j + m] += tick / (np.abs(tick).max() + 1e-9) * 0.16

    out *= np.clip((dur - t) / 0.8, 0, 1)
    return out


def make_audio(a, dur):
    sr = 44100
    with wave.open(os.path.join(WORK, "bgm.wav"), "rb") as fh:
        fh.setpos(int(a * sr))
        raw = fh.readframes(int(dur * sr))
        ch, sw = fh.getnchannels(), fh.getsampwidth()
    bg = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if ch == 2:
        bg = bg.reshape(-1, 2)
    else:
        bg = np.stack([bg, bg], axis=1)
    n = bg.shape[0]
    sfx = synth(dur)[:n]
    mix = bg.copy()
    mix[:, 0] += sfx * 0.85
    mix[:, 1] += sfx * 0.85
    peak = np.abs(mix).max()
    if peak > 0.95:
        mix *= 0.95 / peak
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    p = os.path.join(WORK, "ring_audio.wav")
    with wave.open(p, "wb") as fh:
        fh.setnchannels(2)
        fh.setsampwidth(2)
        fh.setframerate(sr)
        fh.writeframes(pcm.tobytes())
    return p


# ---------------- 帧
def frame(lt, dur):
    img = BG.convert("RGBA").copy()
    d = ImageDraw.Draw(img)

    # 出场：0–0.35 光点；0.35–1.15 甩出；之后自转
    reveal = float(np.clip((lt - 0.30) / 0.85, 0, 1))
    ease = 1 - (1 - reveal) ** 3
    sb = 9.9
    i = np.searchsorted(BEATS, lt) - 1
    if i >= 0:
        sb = lt - BEATS[i]
    kick = math.exp(-sb / 0.16)

    # 中心光点 / 柔光
    if reveal < 0.05:
        r = 10 + 8 * kick
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse([CX - r * 6, CY - r * 6, CX + r * 6, CY + r * 6],
                                     fill=(230, 236, 250, 60))
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(30)))
        d.ellipse([CX - r, CY - r, CX + r, CY + r], fill=(245, 247, 252, 240))
    else:
        halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(halo).ellipse([CX - 320, CY - 200, CX + 320, CY + 200],
                                     fill=(150, 170, 210, int(16 + 14 * kick)))
        img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(90)))

    if reveal <= 0:
        return img.convert("RGB")

    # 轨道椭圆（示意环的透视）
    if reveal > 0.55:
        a0 = int(38 * (reveal - 0.55) / 0.45)
        d.ellipse([CX - R, CY - R * SQUASH, CX + R, CY + R * SQUASH],
                  outline=(150, 156, 172, a0), width=1)

    # 环：基础自转 + 每拍脉冲
    spin = 26 * lt + 8 * sum(1 for b in BEATS if b <= lt) * 0.0 + 90 * ease
    spin += 0.9 * math.sin(lt * 0.8) + 3.5 * ease * math.exp(-1.2 * ease)

    items = []
    for idx in range(len(GLASS)):
        theta = math.radians(spin + idx * (360 / len(GLASS)))
        z = math.cos(theta)                      # 近处 +1，远处 -1
        rad = R * (0.15 + 0.85 * ease)
        x = CX + rad * math.sin(theta)
        y = CY + rad * z * SQUASH
        scale = (0.40 + 0.60 * (z + 1) / 2) * (0.55 + 0.45 * ease)
        alpha = int(255 * (0.22 + 0.78 * (z + 1) / 2) * ease)
        items.append((z, x, y, scale, alpha, idx))
    items.sort(key=lambda it: it[0])

    for z, x, y, scale, alpha, idx in items:
        card = GLASS[idx]
        sz = int(card.width * scale)
        if sz < 8:
            continue
        c = card.resize((sz, sz), Image.LANCZOS)
        if z < 0:                      # 远处的卡片加景深模糊
            c = c.filter(ImageFilter.GaussianBlur(min(6.0, -z * 5.5)))
        c.putalpha(c.split()[3].point(lambda v: int(v * alpha / 255)))
        img.alpha_composite(c, (int(x - sz / 2), int(y - sz / 2)))

    # 底部进度标签
    label = "17 CURSORS  ·  A RING OF ONE IDEA"
    a = int(90 * min(1.0, max(0.0, (lt - 1.4) / 0.8)))
    if a > 0:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((96, H - 92), label, font=font(24), fill=G2 + (a,))
        img.alpha_composite(layer)

    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    arr += np.random.default_rng(int(lt * 1000)).normal(0, 2.4, (H, W, 1))
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def main():
    a = float(sys.argv[1]) if len(sys.argv) > 1 else 64.0
    dur = float(sys.argv[2]) if len(sys.argv) > 2 else 9.0
    out = os.path.join(WORK, "seg6_ring.mp4")
    audio = make_audio(a, dur)
    cmd = [FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
           "-r", str(FPS), "-i", "-", "-i", audio,
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    n = int(dur * FPS)
    for i in range(n):
        p.stdin.write(frame(i / FPS, dur).tobytes())
        if i % 60 == 0:
            print("  %d/%d" % (i, n), flush=True)
    p.stdin.close()
    p.wait()
    print("saved", out)


if __name__ == "__main__":
    main()
