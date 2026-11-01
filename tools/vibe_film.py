# -*- coding: utf-8 -*-
"""
《指针简史》全片（vibe知识大赏风格 / 1920x1080 / 30fps / 无旁白 / 跟 BGM 律动）

六段：
  A 冷开场      0 – 12s   白箭头浮现 + 「每一次点击」
  B 历史锚点   12 – 42s   1981 Xerox Star / 1984 Mac / 1995 Windows 95 沙漏
  C 拆 .cur    42 – 85s   三档尺寸分裂、热点坐标、DPI 100→200% 变糊
  D 转折       85 – 105s  白箭头粒子碎裂 → 聚成一只黑猫
  E 落点      105 – 122s  17 个角色网格逐拍点亮
  F 收尾      122 – 127s  引用来源 + 示意图声明

字体：中文 = 仓耳舒圆体（TsangerShuYuanT，官方免费商用）；英文 = Bodoni Italic
律动：beatmap.npz（112.3 BPM / 首拍 0.100s / 238 拍）

用法：python tools/vibe_film.py [起点秒 终点秒]   不给参数就出全片
产物：E:\deepseek\.tmp\vibe\film_v1.mp4
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
FDIR = r"E:\deepseek\.tmp\fonts"

F_CN = os.path.join(FDIR, "仓耳舒圆体W05.ttf")
F_CN_L = os.path.join(FDIR, "仓耳舒圆体W03.ttf")
F_EN_I = r"C:\Windows\Fonts\BOD_I.TTF"
F_EN = r"C:\Windows\Fonts\BOD_R.TTF"
F_MONO = r"C:\Windows\Fonts\consola.ttf"

BM = np.load(os.path.join(WORK, "beatmap.npz"))
BPM = float(BM["bpm"])
BEAT = float(BM["beat"])
BEATS = BM["beats"]
STRENGTH = BM["strength"]
TOTAL = 126.9

INK = (242, 242, 246)
G1 = (196, 198, 206)
G2 = (146, 149, 158)
G3 = (104, 107, 116)
G4 = (70, 73, 82)
ORANGE = (240, 138, 82)


def font(path, size):
    return ImageFont.truetype(path, size) if os.path.exists(path) else ImageFont.load_default()


# ------------------------------------------------------------------ 背景
def make_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    bg = np.zeros((H, W, 3), dtype=np.float32)

    def glow(cx, cy, rx, ry, amp):
        d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
        return (np.clip(1 - d, 0, 1) ** 2.2) * amp

    bg += glow(W * 0.62, H * 0.28, W * 0.55, H * 0.6, 26)[:, :, None]
    bg += glow(W * 0.28, H * 0.85, W * 0.45, H * 0.4, 11)[:, :, None]
    bg += glow(W * 0.5, H * 0.5, W * 0.9, H * 0.9, 6)[:, :, None]
    dv = np.sqrt((xx - W / 2) ** 2 + (yy - H / 2) ** 2) / (W * 0.72)
    bg *= np.clip(1.05 - dv * 0.72, 0.18, 1.0)[:, :, None]
    return Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8), "RGB")


BG_IMG = make_bg()


def make_beam(length, width, angle_deg, alpha=96):
    pad = 200
    size = int(length + pad * 2)
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = size / 2, size / 2
    half = width / 2
    d.polygon([(cx - length / 2, cy), (cx + length / 2, cy - half),
               (cx + length / 2, cy + half)], fill=(214, 218, 232, alpha))
    return im.filter(ImageFilter.GaussianBlur(46)).rotate(angle_deg, resample=Image.BICUBIC, expand=False)


BEAMS = [
    (make_beam(2600, 150, -14), W * 0.72, H * -0.05, 0.9),
    (make_beam(2400, 92, -8), W * 0.55, H * -0.10, 0.7),
    (make_beam(2200, 60, -20), W * 0.86, H * 0.02, 0.55),
    (make_beam(2000, 210, 4), W * 0.45, H * -0.12, 0.55),
    (make_beam(2300, 130, 26), W * 0.12, H * -0.06, 0.5),      # 新增：左侧斜光
    (make_beam(1500, 260, 90, 70), W * 0.50, H * 0.98, 0.5),   # 新增：箭头背后的逆光
]
BEAM_ALPHA = [b.split()[3] for b, _, _, _ in BEAMS]

RNG = np.random.default_rng(20261102)
MOTE_N = 170
mote_x = RNG.uniform(0, W, MOTE_N)
mote_y = RNG.uniform(0, H, MOTE_N)
mote_r = RNG.uniform(0.5, 1.7, MOTE_N)
mote_v = RNG.uniform(3, 13, MOTE_N)
mote_a = RNG.uniform(8, 44, MOTE_N)


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
CAT = cartoon.render("arrow", 620)
CAT_GLOW = CAT.filter(ImageFilter.GaussianBlur(18))


def grain(seed):
    return np.random.default_rng(seed).normal(0, 2.6, (H, W, 1)).astype(np.float32)


def since_beat(t):
    i = np.searchsorted(BEATS, t) - 1
    if i < 0:
        return 9.9, 0.0
    return t - BEATS[i], float(STRENGTH[i])


def beat_index(t):
    return int(np.searchsorted(BEATS, t))


# ------------------------------------------------------------------ 公共绘制
def draw_light(img, t):
    sb, sstr = since_beat(t)
    breath = 0.85 + 0.35 * math.exp(-sb / 0.35) * (0.4 + 0.6 * sstr)
    for idx, (beam, bx, by, strength) in enumerate(BEAMS):
        dy = math.sin(t * 0.22 + idx * 1.7) * 10
        dx = math.cos(t * 0.17 + idx) * 6
        a = BEAM_ALPHA[idx].point(lambda v: int(v * breath * strength))
        b = beam.copy()
        b.putalpha(a)
        img.alpha_composite(b, (int(bx - b.width / 2 + dx), int(by - b.height / 2 + dy)))

    pool_a = int(24 + 9 * math.sin(t * 0.7))
    pool = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(pool).ellipse([W * 0.26, H * 0.80, W * 0.74, H * 1.02],
                                 fill=(196, 200, 214, pool_a))
    img.alpha_composite(pool.filter(ImageFilter.GaussianBlur(70)))
    ImageDraw.Draw(img).line([(W * 0.14, H * 0.815), (W * 0.86, H * 0.815)],
                             fill=(180, 184, 198, 24), width=1)


def draw_dust(img, t):
    d = ImageDraw.Draw(img)
    for k in range(MOTE_N):
        y = (mote_y[k] - mote_v[k] * t) % H
        x = mote_x[k] + math.sin(t * 0.5 + k) * 7
        a = int(mote_a[k] * (0.45 + 0.55 * math.sin(t * 0.9 + k)))
        d.ellipse([x, y, x + mote_r[k], y + mote_r[k]],
                  fill=(208, 211, 226, max(0, min(255, a))))


def top_block(img, act_no, cn, en, t, t0):
    d = ImageDraw.Draw(img)
    a = int(200 * min(1.0, max(0.0, (t - t0) / 0.8)))
    if a <= 0:
        return
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dl = ImageDraw.Draw(layer)
    dl.text((96, 82), cn, font=font(F_CN_L, 36), fill=G1 + (a,))
    dl.text((96, 132), en, font=font(F_EN_I, 26), fill=G3 + (int(a * 0.95),))
    dl.line([(96, 180), (330, 180)], fill=G3 + (int(a * 0.5),), width=1)
    dl.text((W - 330, 84), "CURSORLAB", font=font(F_EN, 24), fill=G3 + (int(a * 0.85),))
    dl.text((W - 330, 118), "%02d / 06" % act_no, font=font(F_EN, 22), fill=G3 + (int(a * 0.6),))
    # 进度线
    pw = int(1180 * min(1.0, t / TOTAL))
    dl.line([(96, 196), (96 + 1180, 196)], fill=(90, 93, 102, 40), width=1)
    dl.line([(96, 196), (96 + pw, 196)], fill=(178, 182, 196, 70), width=1)
    img.alpha_composite(layer)


def text_block(img, cn, en, t, t0, y=H * 0.34, size=132, spacing=0.14,
               per_char=(BEAT * 0.55), hot=(), hot_color=ORANGE, en_delay=0.3):
    """中文主行（逐字由虚到实）+ 英文意大利体副行"""
    d = ImageDraw.Draw(img)
    f = font(F_CN, size)
    fe = font(F_EN_I, int(size * 0.30))
    gap = int(size * spacing)
    widths = [d.textlength(ch, font=f) for ch in cn]
    total = sum(widths) + gap * (len(cn) - 1)
    x = (W - total) / 2
    for i, ch in enumerate(cn):
        local = t - (t0 + i * per_char)
        if local <= 0:
            x += widths[i] + gap
            continue
        k = min(1.0, local / 0.65)
        k = 1 - (1 - k) ** 3
        a = int(250 * k)
        blur = (1 - k) * 9
        col = (hot_color if ch in hot else INK) + (a,)
        layer = Image.new("RGBA", (int(widths[i]) + 80, size * 2), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((40, size * 0.32), ch, font=f, fill=col)
        if blur > 0.5:
            layer = layer.filter(ImageFilter.GaussianBlur(blur))
        img.alpha_composite(layer, (int(x) - 40, int(y - size * 0.32)))
        x += widths[i] + gap

    if en and t > t0 + len(cn) * per_char + en_delay:
        k = min(1.0, (t - (t0 + len(cn) * per_char + en_delay)) / 0.9)
        a = int(150 * k)
        w = d.textlength(en, font=fe) + 6 * (len(en) - 1)
        sx = (W - w) / 2
        for ch in en:
            d.text((sx, y + size * 0.86), ch, font=fe, fill=G2 + (a,))
            sx += d.textlength(ch, font=fe) + 6


def small_center(img, text, y, size=34, color=G3, alpha=120):
    d = ImageDraw.Draw(img)
    w = d.textlength(text, font=font(F_MONO, size))
    d.text(((W - w) / 2, y), text, font=font(F_MONO, size), fill=color + (alpha,))


# ------------------------------------------------------------------ A 冷开场
def act_a(img, t, lt):
    draw_light(img, t)
    draw_dust(img, t)
    if lt > 0.2:
        k = min(1.0, (lt - 0.2) / 1.1)
        k = 1 - (1 - k) ** 3
        scale = 0.24 + 0.16 * k
        size = int(ARROW.width * scale)
        art = ARROW.resize((size, size), Image.LANCZOS)
        gl = ARROW_GLOW.resize((size, size), Image.LANCZOS)
        alpha = int(240 * k)
        left, top = int(W / 2 - size / 2), int(H * 0.735 - size / 2 + math.sin(t * 1.1) * 3)
        for layer, mul in ((gl, 0.55), (art, 1.0)):
            a2 = layer.copy()
            a2.putalpha(a2.split()[3].point(lambda v: int(v * mul * alpha / 255)))
            img.alpha_composite(a2, (left, top))
    text_block(img, "每一次点击", "every single click", t, 1.2, y=H * 0.34)
    top_block(img, 1, "指针简史", "A Brief History of the Cursor", t, 0.2)


# ------------------------------------------------------------------ B 历史锚点
def device_arrow(d, cx, cy, s, color):
    pts = [(cx - 26 * s, cy - 40 * s), (cx - 26 * s, cy + 30 * s), (cx - 6 * s, cy + 10 * s),
           (cx + 8 * s, cy + 44 * s), (cx + 24 * s, cy + 36 * s), (cx + 10 * s, cy + 2 * s),
           (cx + 34 * s, cy + 2 * s)]
    d.polygon(pts, outline=color, width=3)


def device_hourglass(d, cx, cy, s, color):
    d.line([(cx - 26 * s, cy - 38 * s), (cx + 26 * s, cy - 38 * s)], fill=color, width=3)
    d.line([(cx - 26 * s, cy + 38 * s), (cx + 26 * s, cy + 38 * s)], fill=color, width=3)
    d.line([(cx - 22 * s, cy - 36 * s), (cx, cy), (cx + 22 * s, cy - 36 * s)], fill=color, width=3)
    d.line([(cx - 22 * s, cy + 36 * s), (cx, cy), (cx + 22 * s, cy + 36 * s)], fill=color, width=3)


def device_star(d, cx, cy, s, color):
    for i in range(8):
        a = i * math.pi / 4
        d.line([(cx, cy), (cx + 34 * s * math.cos(a), cy + 34 * s * math.sin(a))], fill=color, width=2)


def act_b(img, t, lt):
    draw_light(img, t)
    draw_dust(img, t)
    d = ImageDraw.Draw(img)
    seq = [(0.6, 9.5, "1981", "Xerox Star", device_star, "第一次，屏幕上出现了一个箭头"),
           (9.5, 20.0, "1984", "Macintosh", device_arrow, "一个箭头，指向你要去的地方"),
           (20.0, 30.0, "1995", "Windows 95", device_hourglass, "沙漏转起来，电脑在忙")]
    for (t0, t1, year, name, drawfn, cap) in seq:
        if not (t0 <= lt < t1):
            continue
        k_in = min(1.0, (lt - t0) / 1.2)
        k_in = 1 - (1 - k_in) ** 3
        a = int(230 * k_in)
        cx, cy = W * 0.5, H * 0.56
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(layer)
        drawfn(dl, cx, cy, 1.5 + 0.35 * math.sin(lt * 1.2), (200, 204, 218, a))
        glow = layer.filter(ImageFilter.GaussianBlur(10))
        img.alpha_composite(glow)
        img.alpha_composite(layer)
        # 年份与名称
        dl2 = ImageDraw.Draw(img)
        fy = font(F_EN, 82)
        yw = dl2.textlength(year, font=fy)
        dl2.text(((W - yw) / 2, H * 0.24), year, font=fy, fill=G1 + (a,))
        fn = font(F_CN_L, 36)
        nw = dl2.textlength(name, font=fn)
        dl2.text(((W - nw) / 2, H * 0.36), name, font=fn, fill=G3 + (int(a * 0.85),))
        # 字幕
        text_block(img, cap, "", t, t0 + 1.0, y=H * 0.70, size=54, spacing=0.10)
    top_block(img, 2, "历史锚点", "Where the arrow came from", t, 12.6)


# ------------------------------------------------------------------ C 拆 .cur
def act_c(img, t, lt):
    draw_light(img, t)
    draw_dust(img, t)
    d = ImageDraw.Draw(img)
    cx, cy = W * 0.5, H * 0.56
    sb, sstr = since_beat(t)

    # 三档尺寸：从中心分裂出三块
    for i, (sz, label, delay) in enumerate(((300, "64 px", 0.4), (210, "48 px", 1.4), (140, "32 px", 2.4))):
        k = min(1.0, max(0.0, (lt - delay) / 1.0))
        k = 1 - (1 - k) ** 3
        if k <= 0:
            continue
        off = (1 - k) * 30
        box = [cx - sz / 2 + off + i * 46, cy - sz / 2 + off + i * 40,
               cx + sz / 2 + off + i * 46, cy + sz / 2 + off + i * 40]
        a = int(150 * k)
        d.rectangle(box, outline=(180, 184, 198, a), width=2)
        dl = ImageDraw.Draw(img)
        dl.text((box[0] + 10, box[1] + 8), label, font=font(F_MONO, 24), fill=G3 + (a,))

    # 热点坐标
    if lt > 4.0:
        k = min(1.0, (lt - 4.0) / 0.8)
        hx, hy = cx - 128, cy - 128
        r = 6 + 4 * math.exp(-sb / 0.25)
        d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=(226, 232, 244, int(220 * k)))
        d.line([(hx, hy), (hx + 150, hy - 60)], fill=(160, 164, 178, int(120 * k)), width=1)
        d.text((hx + 156, hy - 74), "hotspot (x, y)", font=font(F_MONO, 28),
               fill=G2 + (int(200 * k),))

    # hex 味的信息块
    if lt > 6.0:
        lines = ["ICONDIR   type=2  count=3",
                 "  entry0  32x32   hotspot(2,2)",
                 "  entry1  48x48   hotspot(3,3)",
                 "  entry2  64x64   hotspot(4,4)",
                 "BITMAPINFOHEADER  biHeight = h*2"]
        done = int(min(len(lines), (lt - 6.0) / 0.9))
        for i in range(done):
            small_center(img, lines[i], H * 0.795 + i * 34, 26, G3, 150)

    # DPI 演示：100% → 200%
    if lt > 30.0:
        k = min(1.0, (lt - 30.0) / 4.0)
        pct = 100 + int(100 * k)
        bx0, bx1 = W * 0.62, W * 0.88
        d.line([(bx0, H * 0.30), (bx1, H * 0.30)], fill=(90, 94, 104, 90), width=2)
        px = bx0 + (bx1 - bx0) * k
        d.ellipse([px - 9, H * 0.30 - 9, px + 9, H * 0.30 + 9], fill=(226, 230, 242, 220))
        d.text((bx0, H * 0.24), "DPI  %d%%" % pct, font=font(F_MONO, 30), fill=G1 + (200,))
        # 32px 层在高 DPI 下变糊 / 48px 层清晰
        small = ARROW.resize((36, 36), Image.LANCZOS)
        if k > 0.7:
            small = small.filter(ImageFilter.GaussianBlur(2.2 * (k - 0.7) / 0.3))
        img.alpha_composite(small, (int(bx1 - 40), int(H * 0.36)))
        big = ARROW.resize((72, 72), Image.LANCZOS)
        img.alpha_composite(big, (int(bx1 - 90), int(H * 0.36)))

    text_block(img, "它不是一个图片", "it is a container", t, 42.6, y=H * 0.16, size=96, spacing=0.12)
    top_block(img, 3, "拆开一个光标文件", "What is inside a .cur", t, 42.6)


# ------------------------------------------------------------------ D 转折
def _sample_points(mask_img, n):
    a = np.asarray(mask_img.split()[3])
    ys, xs = np.nonzero(a > 128)
    if len(xs) == 0:
        return np.zeros((n, 2))
    idx = np.random.default_rng(7).integers(0, len(xs), n)
    return np.stack([xs[idx], ys[idx]], axis=1).astype(np.float32)


P_ARROW = _sample_points(ARROW.resize((420, 420)), 2600) + np.array(
    [W / 2 - 210, H * 0.5 - 210], dtype=np.float32)
P_CAT = _sample_points(CAT.resize((420, 420)), 2600) + np.array(
    [W / 2 - 210, H * 0.5 - 210], dtype=np.float32)
_rng = np.random.default_rng(11)
P_DELAY = _rng.uniform(0, 0.55, 2600)
P_JIT = _rng.normal(0, 26, (2600, 2)).astype(np.float32)


def act_d(img, t, lt):
    draw_light(img, t)
    draw_dust(img, t)
    d = ImageDraw.Draw(img)
    k = min(1.0, max(0.0, (lt - 1.6) / 5.2))
    if k <= 0:
        # 完整箭头
        size = 400
        art = ARROW.resize((size, size), Image.LANCZOS)
        gl = ARROW_GLOW.resize((size, size), Image.LANCZOS)
        left, top = int(W / 2 - size / 2), int(H * 0.5 - size / 2)
        img.alpha_composite(gl, (left, top))
        img.alpha_composite(art, (left, top))
    else:
        ease = np.clip((k - P_DELAY * 0) / 1.0, 0, 1)
        e = 1 - (1 - ease) ** 3
        pts = P_ARROW * (1 - e[:, None]) + (P_CAT + P_JIT * (1 - e[:, None])) * e[:, None]
        # 中段加一点爆散
        burst = math.sin(math.pi * min(1.0, k)) * 40
        n = np.random.default_rng(3).normal(0, burst * 0.5, (2600, 2))
        pts = pts + n
        alpha = int(210 * (1 - 0.35 * k))
        for i in range(2600):
            x, y = pts[i]
            d.point((x, y), fill=(236, 238, 244, alpha))
        if k > 0.92:
            img.alpha_composite(CAT_GLOW, (int(W / 2 - CAT.width / 2), int(H * 0.5 - CAT.height / 2)))
            img.alpha_composite(CAT, (int(W / 2 - CAT.width / 2), int(H * 0.5 - CAT.height / 2)))
    if lt < 8.0:
        text_block(img, "可它本来可以不是箭头", "it could have been a cat", t, 85.4, y=H * 0.82, size=60, spacing=0.10)
    top_block(img, 4, "转折", "What if the arrow were a cat", t, 85.4)


# ------------------------------------------------------------------ E 落点
ROLES = ["arrow", "help", "wait", "appstarting", "crosshair", "ibeam", "nwpen", "no",
         "sizeall", "sizens", "sizewe", "sizenwse", "sizenesw", "uparrow", "hand",
         "pin", "person"]
_TILES = {r: cartoon.render(r, 150) for r in ROLES}


def act_e(img, t, lt):
    draw_light(img, t)
    draw_dust(img, t)
    d = ImageDraw.Draw(img)
    cols, cell, pad = 6, 168, 20
    rows = (len(ROLES) + cols - 1) // cols
    gw = cols * cell + (cols - 1) * pad
    gh = rows * cell + (rows - 1) * pad
    x0 = (W - gw) / 2
    y0 = H * 0.30
    b = beat_index(t)
    for i, r in enumerate(ROLES):
        row, col = divmod(i, cols)
        appear = 0.3 + i * (BEAT * 0.5)
        if lt < appear:
            continue
        k = min(1.0, (lt - appear) / 0.6)
        k = 1 - (1 - k) ** 3
        x = x0 + col * (cell + pad)
        y = y0 + row * (cell + pad)
        drift = math.sin(t * 0.9 + i) * 2.5
        tile = _TILES[r].copy()
        a = int(238 * k)
        tile.putalpha(tile.split()[3].point(lambda v: int(v * a / 255)))
        img.alpha_composite(tile, (int(x + (cell - 150) / 2), int(y + drift + (cell - 150) / 2)))
    text_block(img, "十七个动作，一只猫", "seventeen cursors, one cat", t, 105.4, y=H * 0.14, size=64, spacing=0.10)
    top_block(img, 5, "落点", "The whole set", t, 105.4)


# ------------------------------------------------------------------ F 收尾
def act_f(img, t, lt):
    draw_light(img, t)
    draw_dust(img, t)
    d = ImageDraw.Draw(img)
    cx = W / 2
    size = 260
    art = CAT.resize((size, size), Image.LANCZOS)
    img.alpha_composite(art, (int(cx - size / 2), int(H * 0.42 - size / 2)))
    lines = ["资料来源：Xerox Star (1981) · Apple Macintosh (1984)",
             "Windows 95 沙漏图标 · Windows .cur / .ani 文件格式",
             "画面为示意图 · CursorLab · MIT License"]
    for i, ln in enumerate(lines):
        if lt < 0.3 + i * 0.7:
            continue
        a = int(160 * min(1.0, (lt - 0.3 - i * 0.7) / 0.8))
        w = d.textlength(ln, font=font(F_CN_L, 26))
        d.text(((W - w) / 2, H * 0.70 + i * 42), ln, font=font(F_CN_L, 26), fill=G3 + (a,))
    top_block(img, 6, "收尾", "Sources & disclaimer", t, 122.4)


# ------------------------------------------------------------------ 调度
ACTS = [(0.0, 12.0, act_a), (12.0, 42.0, act_b), (42.0, 85.0, act_c),
        (85.0, 105.0, act_d), (105.0, 122.0, act_e), (122.0, TOTAL, act_f)]


def frame(i):
    t = i / FPS
    img = BG_IMG.convert("RGBA").copy()
    for t0, t1, fn in ACTS:
        if t0 <= t < t1:
            fn(img, t, t - t0)
            break
    arr = np.asarray(img.convert("RGB"), dtype=np.float32) + grain(i)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
    fade = 1.0
    if t < 0.6:
        fade = t / 0.6
    if t > TOTAL - 1.6:
        fade = max(0.0, (TOTAL - t) / 1.6)
    if fade < 1.0:
        img = Image.eval(img, lambda v: int(v * fade))
    return img


def main():
    a = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    b = float(sys.argv[2]) if len(sys.argv) > 2 else TOTAL
    out = os.path.join(WORK, "film_v1.mp4" if (a == 0 and b >= TOTAL) else
                       "film_part_%d_%d.mp4" % (a, b))
    audio = os.path.join(WORK, "film_audio.wav")
    subprocess.run([FF, "-y", "-i", os.path.join(WORK, "bgm.wav"), "-ss", "%.2f" % a,
                    "-t", "%.2f" % (b - a), audio], check=True, capture_output=True)
    n0, n1 = int(a * FPS), int(b * FPS)
    cmd = [FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
           "-r", str(FPS), "-i", "-", "-i", audio,
           "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    total = n1 - n0
    for idx, i in enumerate(range(n0, n1)):
        p.stdin.write(frame(i).tobytes())
        if idx % 150 == 0:
            print("  %d/%d (%.1fs)" % (idx, total, i / FPS), flush=True)
    p.stdin.close()
    p.wait()
    print("saved", out)


if __name__ == "__main__":
    main()
