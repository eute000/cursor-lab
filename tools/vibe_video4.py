# -*- coding: utf-8 -*-
"""
vibe知识大赏 · 冷开场 v4「高级酒店光感」（20 秒试片）

本版按用户 2026-11-01 反馈重做：
  * 去掉杂乱涟漪（改为极淡的整体"呼吸"，不再堆同心圆）
  * 字体换艺术字体：中文＝霞鹜文楷（LXGW WenKai，OFL）、英文＝Bodoni Italic
  * 顶部不再空：左上角加"标题块"（中文小字 + 英文意大利体 + 细横线）
  * 鼠标去掉黑描边（只留柔和投影），去掉橙色热点
  * 用**灰色层次 + 体积光射线 + 柔光**营造高级感（参考酒店大堂光）
  * 轻微动态：光束缓慢摆动、尘埃上浮、鼠标 2px 浮动、文字由虚到实

用法：python tools/vibe_video4.py [秒数]
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1920, 1080, 30
WORK = r"E:\deepseek\.tmp\vibe"
FF = r"D:\python\huanjing\ffmpeg.exe"
FONT_CN = r"E:\deepseek\.tmp\fonts\LXGWWenKai-Regular.ttf"
FONT_EN_I = r"C:\Windows\Fonts\BOD_I.TTF"      # Bodoni Italic
FONT_EN = r"C:\Windows\Fonts\BOD_R.TTF"
FONT_EN_CAPS = r"C:\Windows\Fonts\BOD_R.TTF"

BM = np.load(os.path.join(WORK, "beatmap.npz"))
BPM = float(BM["bpm"])
BEAT = float(BM["beat"])
BEATS = BM["beats"]
STRENGTH = BM["strength"]

INK = (240, 240, 244)
GRAY1 = (188, 190, 198)
GRAY2 = (140, 143, 152)
GRAY3 = (96, 99, 108)


def font(path, size):
    return ImageFont.truetype(path, size) if os.path.exists(path) else ImageFont.load_default()


# ---------------------------------------------------------------- 背景：多层灰
def make_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    bg = np.zeros((H, W, 3), dtype=np.float32)

    # 三层柔光（不同位置/半径，制造纵深）
    def glow(cx, cy, rx, ry, amp):
        d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
        return (np.clip(1 - d, 0, 1) ** 2.2) * amp

    bg += glow(W * 0.62, H * 0.30, W * 0.55, H * 0.60, 26)[:, :, None]
    bg += glow(W * 0.30, H * 0.85, W * 0.45, H * 0.40, 12)[:, :, None]
    bg += glow(W * 0.5, H * 0.55, W * 0.9, H * 0.9, 6)[:, :, None]

    # 暗角
    dv = np.sqrt((xx - W / 2) ** 2 + (yy - H / 2) ** 2) / (W * 0.72)
    bg *= np.clip(1.05 - dv * 0.75, 0.18, 1.0)[:, :, None]
    return Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8), "RGB")


BG_IMG = make_bg()

# ---------------------------------------------------------------- 体积光射线
def make_beam(length, width, angle_deg):
    """一条从屏幕外射入的柔光带（三角形 + 重度模糊）"""
    pad = 200
    size = int(length + pad * 2)
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = size / 2, size / 2
    half = width / 2
    d.polygon([(cx - length / 2, cy), (cx + length / 2, cy - half),
               (cx + length / 2, cy + half)], fill=(214, 218, 232, 96))
    im = im.filter(ImageFilter.GaussianBlur(46))
    return im.rotate(angle_deg, resample=Image.BICUBIC, expand=False)


BEAMS = [
    (make_beam(2600, 150, -14), W * 0.72, H * -0.05, 0.9),
    (make_beam(2400, 92, -8), W * 0.55, H * -0.10, 0.7),
    (make_beam(2200, 60, -20), W * 0.86, H * 0.02, 0.55),
    (make_beam(2000, 210, 4), W * 0.45, H * -0.12, 0.55),
]

BEAM_ALPHA = [b.split()[3] for b, _, _, _ in BEAMS]

RNG = np.random.default_rng(20261102)
MOTE_N = 170
mote_x = RNG.uniform(0, W, MOTE_N)
mote_y = RNG.uniform(0, H, MOTE_N)
mote_r = RNG.uniform(0.5, 1.7, MOTE_N)
mote_v = RNG.uniform(3, 13, MOTE_N)
mote_a = RNG.uniform(8, 44, MOTE_N)


# ---------------------------------------------------------------- 指针（无黑边）
def arrow_sprite(px):
    base = 512
    im = Image.new("RGBA", (base, base), (0, 0, 0, 0))
    pts = [(150, 88), (150, 356), (222, 286), (286, 408), (338, 382),
           (274, 262), (356, 262)]

    # 柔和投影（代替黑描边）
    sh = Image.new("RGBA", (base, base), (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon([(x + 6, y + 12) for x, y in pts], fill=(0, 0, 0, 110))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(26)))

    face = Image.new("RGBA", (base, base), (0, 0, 0, 0))
    ImageDraw.Draw(face).polygon(pts, fill=(238, 239, 243, 255))
    # 竖向渐变：上亮下暗，制造层次（不用描边）
    grad = Image.new("L", (1, base))
    for y in range(base):
        grad.putpixel((0, y), int(255 - 46 * (y / base)))
    grad = grad.resize((base, base))
    mask = face.split()[3]
    shade = Image.composite(Image.new("RGBA", (base, base), (255, 255, 255, 255)),
                            Image.new("RGBA", (base, base), (176, 178, 188, 255)), grad)
    face = Image.composite(shade, Image.new("RGBA", (base, base), (0, 0, 0, 0)), mask)
    im.alpha_composite(face)
    return im.resize((px, px), Image.LANCZOS)


ARROW = arrow_sprite(760)
ARROW_GLOW = ARROW.filter(ImageFilter.GaussianBlur(26))


def grain(seed):
    return np.random.default_rng(seed).normal(0, 2.6, (H, W, 1)).astype(np.float32)


def since_beat(t):
    i = np.searchsorted(BEATS, t) - 1
    if i < 0:
        return 9.9, 0.0
    return t - BEATS[i], float(STRENGTH[i])


# ---------------------------------------------------------------- 排版
def top_block(img, t):
    """左上角标题块：中文小字 + 英文意大利体 + 细线（填掉顶部的空）"""
    d = ImageDraw.Draw(img)
    x, y = 96, 88
    a = int(190 * min(1.0, max(0.0, (t - 0.2) / 1.2)))
    if a <= 0:
        return
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dl = ImageDraw.Draw(layer)
    dl.text((x, y), "指针简史", font=font(FONT_CN, 34), fill=GRAY1 + (a,))
    dl.text((x, y + 46), "A Brief History of the Cursor", font=font(FONT_EN_I, 26),
            fill=GRAY3 + (int(a * 0.9),))
    dl.line([(x, y + 92), (x + 210, y + 92)], fill=GRAY3 + (int(a * 0.55),), width=1)
    # 右上：角标（仿片头卡）
    dl.text((W - 300, y + 8), "CURSORLAB", font=font(FONT_EN_CAPS, 24),
            fill=GRAY3 + (int(a * 0.8),))
    dl.text((W - 300, y + 42), "01 / 06", font=font(FONT_EN, 22), fill=GRAY3 + (int(a * 0.55),))
    img.alpha_composite(layer)


def main_title(img, t):
    """中文艺术体大标题 + 英文意大利体副行，逐字由虚到实"""
    d = ImageDraw.Draw(img)
    text = "每一次点击"
    size = 150
    f = font(FONT_CN, size)
    fe = font(FONT_EN_I, 40)
    spacing = 0.16
    gap = int(size * spacing)
    widths = [d.textlength(ch, font=f) for ch in text]
    total = sum(widths) + gap * (len(text) - 1)
    x = (W - total) / 2
    y = H * 0.34
    for i, ch in enumerate(text):
        local = t - (1.2 + i * BEAT * 0.55)
        if local <= 0:
            x += widths[i] + gap
            continue
        k = min(1.0, local / 0.7)
        k = 1 - (1 - k) ** 3
        a = int(252 * k)
        blur = (1 - k) * 9
        layer = Image.new("RGBA", (int(widths[i]) + 80, size * 2), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((40, size * 0.32), ch, font=f, fill=INK + (a,))
        if blur > 0.5:
            layer = layer.filter(ImageFilter.GaussianBlur(blur))
        img.alpha_composite(layer, (int(x) - 40, int(y - size * 0.32)))
        x += widths[i] + gap

    # 英文副行（意大利体，宽字距）
    if t > 1.2 + len(text) * BEAT * 0.55 + 0.3:
        sub = "every single click"
        k = min(1.0, (t - (1.2 + len(text) * BEAT * 0.55 + 0.3)) / 0.9)
        a = int(150 * k)
        w = d.textlength(sub, font=fe) + 8 * (len(sub) - 1)
        sx = (W - w) / 2
        for i, ch in enumerate(sub):
            d.text((sx, y + size * 0.92), ch, font=fe, fill=GRAY2 + (a,))
            sx += d.textlength(ch, font=fe) + 8


def bottom_label(img, t):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    a = int(80 * min(1.0, t / 2.0))
    ImageDraw.Draw(layer).text((W - 330, H - 74), "示意图 · 仅供示意", font=font(FONT_CN, 24),
                               fill=GRAY3 + (a,))
    img.alpha_composite(layer)


ARROW_CX, ARROW_CY = W * 0.5, H * 0.735


def frame(i, dur):
    t = i / FPS
    img = BG_IMG.convert("RGBA").copy()

    # 体积光：只做平移 + 呼吸（每帧旋转大图太慢，观感几乎无差）
    sb, sstr = since_beat(t)
    breath = 0.85 + 0.35 * math.exp(-sb / 0.35) * (0.4 + 0.6 * sstr)
    for idx, (beam, bx, by, strength) in enumerate(BEAMS):
        dy = math.sin(t * 0.22 + idx * 1.7) * 10
        dx = math.cos(t * 0.17 + idx) * 6
        a = BEAM_ALPHA[idx].point(lambda v: int(v * breath * strength))
        b = beam.copy()
        b.putalpha(a)
        img.alpha_composite(b, (int(bx - b.width / 2 + dx), int(by - b.height / 2 + dy)))

    d = ImageDraw.Draw(img)

    # 地面光池（酒店大堂感）：椭圆柔光 + 一条极淡地平线
    pool_a = int(26 + 10 * math.sin(t * 0.7))
    pool = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(pool).ellipse([W * 0.28, H * 0.80, W * 0.72, H * 1.02],
                                 fill=(196, 200, 214, pool_a))
    img.alpha_composite(pool.filter(ImageFilter.GaussianBlur(70)))
    d.line([(W * 0.16, H * 0.815), (W * 0.84, H * 0.815)],
           fill=(180, 184, 198, 26), width=1)

    # 尘埃
    for k in range(MOTE_N):
        y = (mote_y[k] - mote_v[k] * t) % H
        x = mote_x[k] + math.sin(t * 0.5 + k) * 7
        a = int(mote_a[k] * (0.45 + 0.55 * math.sin(t * 0.9 + k)))
        d.ellipse([x, y, x + mote_r[k], y + mote_r[k]],
                  fill=(208, 211, 226, max(0, min(255, a))))

    # 鼠标：无黑边、2px 浮动
    if t > 0.2:
        k = min(1.0, (t - 0.2) / 1.1)
        k = 1 - (1 - k) ** 3
        float_y = math.sin(t * 1.1) * 3
        scale = (0.24 + 0.16 * k)
        size = int(ARROW.width * scale)
        art = ARROW.resize((size, size), Image.LANCZOS)
        gl = ARROW_GLOW.resize((size, size), Image.LANCZOS)
        alpha = int(240 * k)
        left = int(ARROW_CX - size / 2)
        top = int(ARROW_CY - size / 2 + float_y)
        for layer, mul in ((gl, 0.55), (art, 1.0)):
            a2 = layer.copy()
            a2.putalpha(a2.split()[3].point(lambda v: int(v * mul * alpha / 255)))
            img.alpha_composite(a2, (left, top))

    main_title(img, t)
    top_block(img, t)
    bottom_label(img, t)

    arr = np.asarray(img.convert("RGB"), dtype=np.float32) + grain(i)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")

    fade = 1.0
    if t < 0.6:
        fade = t / 0.6
    if t > dur - 1.3:
        fade = max(0.0, (dur - t) / 1.3)
    if fade < 1.0:
        img = Image.eval(img, lambda v: int(v * fade))
    return img


def main():
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0
    n = int(dur * FPS)
    out = os.path.join(WORK, "cold_open_v4_%ds.mp4" % int(dur))
    audio = os.path.join(WORK, "bgm_head.wav")
    subprocess.run([FF, "-y", "-i", os.path.join(WORK, "bgm.wav"), "-t", "%.2f" % dur,
                    "-af", "afade=t=out:st=%.2f:d=1.3" % (dur - 1.3), audio],
                   check=True, capture_output=True)
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
