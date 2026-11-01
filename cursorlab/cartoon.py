# -*- coding: utf-8 -*-
"""
卡通风小黑猫指针 —— 8 倍超采样矢量化绘制（不是像素画）。

造型来自用户给的参考图：黑身、两只超大白眼睛、棕黑描边、小三角耳、细尾巴。
每个元素单独成层、单独加 1px 米白外描边，再叠一起 ——
这样放在任何壁纸上都不会糊成一团，元素之间也不会粘住。
"""

import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

N = 32.0       # 设计网格
SS = 8         # 超采样倍数

BODY = (26, 24, 28, 255)      # 身体近黑
LINE = (48, 36, 30, 255)      # 棕黑描边
CREAM = (250, 250, 252, 255)  # 米白外描边
WHITE = (255, 255, 255, 255)
RED = (222, 62, 62, 255)
PINK = (240, 148, 168, 255)
GOLD = (255, 198, 80, 255)

FONT = r"C:\Windows\Fonts\segoeuib.ttf"


# ------------------------------------------------------------------ 画布
class Canvas:
    def __init__(self, size, ss=SS):
        self.size = size
        self.W = int(round(size * ss))
        self.k = self.W / N
        self.img = Image.new("RGBA", (self.W, self.W), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def s(self, v):
        return v * self.k

    def box(self, x, y, rx, ry):
        return [self.s(x - rx), self.s(y - ry), self.s(x + rx), self.s(y + ry)]

    def ell(self, x, y, rx, ry, fill=None, outline=None, w=1.2):
        self.d.ellipse(self.box(x, y, rx, ry), fill=fill, outline=outline,
                       width=int(round(self.s(w))) if outline else 0)

    def poly(self, pts, fill=None, outline=None, w=1.2):
        p = [(self.s(x), self.s(y)) for x, y in pts]
        if fill:
            self.d.polygon(p, fill=fill)
        if outline:
            self.d.line(p + [p[0]], fill=outline, width=int(round(self.s(w))),
                        joint="curve")

    def line(self, pts, fill=BODY, w=1.2, caps=True):
        p = [(self.s(x), self.s(y)) for x, y in pts]
        ww = max(1, int(round(self.s(w))))
        self.d.line(p, fill=fill, width=ww, joint="curve")
        if caps:
            r = ww / 2.0
            for c in (p[0], p[-1]):
                self.d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=fill)

    def arc(self, x, y, r, start, end, fill=BODY, w=2.2):
        self.d.arc(self.box(x, y, r, r), start, end, fill=fill,
                   width=max(1, int(round(self.s(w)))))

    def text(self, x, y, s, size, fill=BODY, anchor="mm"):
        font = (ImageFont.truetype(FONT, int(self.s(size)))
                if os.path.exists(FONT) else ImageFont.load_default())
        self.d.text((self.s(x), self.s(y)), s, font=font, fill=fill, anchor=anchor)


def rim(c, color=CREAM, w=1.1):
    """给整层套 1px 米白外描边。

    用「高斯模糊 alpha 再阈值」代替大核 MaxFilter —— 后者在 35×35 核上
    慢到不可用（17 个造型 × 3 档尺寸要跑几分钟）。
    """
    a = c.img.split()[3]
    grown = a.filter(ImageFilter.GaussianBlur(max(0.8, c.s(w) * 0.60)))
    band = grown.point(lambda v: 255 if v > 10 else 0)
    ring = ImageChops.subtract(band, a)
    layer = Image.new("RGBA", c.img.size, color[:3] + (0,))
    layer.putalpha(ring)
    out = Image.new("RGBA", c.img.size, (0, 0, 0, 0))
    out.alpha_composite(layer)
    out.alpha_composite(c.img)
    c.img = out
    c.d = ImageDraw.Draw(c.img)


def layer(size, fn, *a, **kw):
    """画一层并单独加外描边"""
    sub = Canvas(size)
    fn(sub, *a, **kw)
    rim(sub)
    return sub


def stamp(base, sub):
    base.img.alpha_composite(sub.img)
    base.d = ImageDraw.Draw(base.img)


# ------------------------------------------------------------------ 小黑猫
def cat(c, s=0.72, dx=8.0, dy=7.0, tail=True):
    """参考图里那只黑猫：大头 + 超大白眼 + 小身体 + 细尾巴。"""
    def T(x, y):
        return (dx + x * s, dy + y * s)

    if tail:
        c.line([T(20.5, 22.0), T(26.5, 22.6), T(29.6, 18.6)], fill=BODY, w=2.4 * s)

    # 身体 + 两只小爪
    cx, cy = T(16, 21.6)
    c.ell(cx, cy, 6.6 * s, 6.0 * s, fill=BODY)
    for px in (12.2, 19.8):
        cx2, cy2 = T(px, 26.8)
        c.ell(cx2, cy2, 2.1 * s, 1.8 * s, fill=BODY)

    # 两只小三角耳（先画，被头盖住底边）
    for sx in (-1, 1):
        c.poly([T(16 + sx * 7.6, 6.6), T(16 + sx * 10.6, 0.8), T(16 + sx * 2.6, 4.6)],
               fill=BODY, outline=LINE, w=1.1 * s)

    # 头
    cx, cy = T(16, 12.0)
    c.ell(cx, cy, 9.6 * s, 8.6 * s, fill=BODY, outline=LINE, w=1.1 * s)

    # 眼睛：两眼白几乎相触，各占脸宽 1/3 以上
    for ex in (12.0, 20.0):
        cx2, cy2 = T(ex, 12.4)
        c.ell(cx2, cy2, 3.8 * s, 4.8 * s, fill=WHITE, outline=LINE, w=0.75 * s)
    for ex in (12.3, 19.7):
        cx2, cy2 = T(ex, 13.2)
        c.ell(cx2, cy2, 2.1 * s, 3.0 * s, fill=BODY)
    for ex in (11.1, 18.5):
        cx2, cy2 = T(ex, 11.5)
        c.ell(cx2, cy2, 0.95 * s, 0.95 * s, fill=WHITE)


# ------------------------------------------------------------------ 符号
def sym_tri(c):
    """左上角空心小三角 ▷（尖端 = 热点）"""
    c.poly([(1.8, 1.8), (10.6, 5.6), (5.6, 10.6)], fill=None, outline=BODY, w=1.9)


def sym_cross(c):
    for a, b in [((16, 4.2), (16, 11.8)), ((16, 20.2), (16, 27.8)),
                 ((4.2, 16), (11.8, 16)), ((20.2, 16), (27.8, 16))]:
        c.line([a, b], fill=BODY, w=2.0)
    c.ell(16, 16, 1.9, 1.9, fill=BODY)


def sym_ibeam(c):
    c.line([(16, 5.0), (16, 27.0)], fill=BODY, w=2.0, caps=False)
    c.line([(11.5, 4.6), (20.5, 4.6)], fill=BODY, w=2.2)
    c.line([(11.5, 27.4), (20.5, 27.4)], fill=BODY, w=2.2)


def sym_pen(c):
    c.line([(9.6, 9.6), (21.4, 21.4)], fill=BODY, w=4.4)
    c.poly([(3.4, 3.4), (11.2, 6.4), (6.4, 11.2)], fill=BODY)
    c.line([(17.6, 17.6), (20.8, 20.8)], fill=PINK, w=3.2)


def sym_uparrow(c):
    c.poly([(16, 4.0), (24.4, 13.2), (18.6, 13.2), (18.6, 27.6),
            (13.4, 27.6), (13.4, 13.2), (7.6, 13.2)], fill=BODY)


def sym_pin(c):
    c.poly([(16, 30.0), (13.0, 17.0), (19.0, 17.0)], fill=BODY)
    c.ell(16, 12.0, 6.4, 6.4, fill=BODY)
    c.ell(16, 12.0, 2.3, 2.3, fill=CREAM)


def sym_paw(c):
    for x, y, r in ((9.2, 13.6, 2.6), (13.6, 10.4, 2.8),
                    (18.4, 10.4, 2.8), (22.8, 13.6, 2.6)):
        c.ell(x, y, r, r, fill=BODY)
    c.ell(16, 20.6, 6.4, 5.4, fill=BODY)
    for x, y, r in ((9.2, 13.9, 0.9), (13.7, 10.9, 1.0),
                    (18.3, 10.9, 1.0), (22.8, 13.9, 0.9)):
        c.ell(x, y, r, r, fill=CREAM)
    c.ell(16, 20.6, 2.6, 2.2, fill=CREAM)


def sym_no(c):
    c.ell(16, 16, 9.6, 9.6, fill=None, outline=RED, w=2.6)
    c.line([(9.4, 22.6), (22.6, 9.4)], fill=RED, w=2.6)


def sym_help(c):
    c.ell(16, 16, 9.8, 9.8, fill=None, outline=BODY, w=1.9)
    c.text(16, 15.6, "?", 15.0, fill=BODY)


def double_arrow(c, deg=0):
    pts = [(16, 3.2), (21.0, 9.0), (17.6, 9.0), (17.6, 23.0), (21.0, 23.0),
           (16, 28.8), (11.0, 23.0), (14.4, 23.0), (14.4, 9.0), (11.0, 9.0)]
    if deg:
        a = math.radians(deg)
        ca, sa = math.cos(a), math.sin(a)
        pts = [(16 + (x - 16) * ca - (y - 16) * sa,
                16 + (x - 16) * sa + (y - 16) * ca) for x, y in pts]
    c.poly(pts, fill=BODY)


def four_arrow(c):
    pts = [(16, 3.2), (20.8, 8.8), (17.6, 8.8), (17.6, 14.2), (23.2, 14.2),
           (23.2, 11.2), (28.8, 16), (23.2, 20.8), (23.2, 17.6), (17.6, 17.6),
           (17.6, 23.2), (20.8, 23.2), (16, 28.8), (11.2, 23.2), (14.4, 23.2),
           (14.4, 17.6), (8.8, 17.6), (8.8, 20.8), (3.2, 16), (8.8, 11.2),
           (8.8, 14.2), (14.4, 14.2), (14.4, 8.8), (11.2, 8.8)]
    c.poly(pts, fill=BODY)


def sym_spinner(c, f, r=11.4, w=2.0, cx=16, cy=16):
    start = -90 + f * 45
    c.arc(cx, cy, r, start, start + 270, fill=BODY, w=w)
    for ang in (start, start + 270):
        a = math.radians(ang)
        c.ell(cx + r * math.cos(a), cy + r * math.sin(a), w / 2.0, w / 2.0, fill=BODY)


def sym_spin_small(c, f, cx=23.0, cy=23.0, r=4.4):
    """角标处的小转圈（appstarting）"""
    start = f * 45
    c.arc(cx, cy, r, start, start + 250, fill=BODY, w=1.9)
    for ang in (start, start + 250):
        a = math.radians(ang)
        c.ell(cx + r * math.cos(a), cy + r * math.sin(a), 0.95, 0.95, fill=BODY)


# ------------------------------------------------------------------ 角色
def draw_arrow(c, f=0):
    stamp(c, layer(c.size, sym_tri))
    stamp(c, layer(c.size, cat, 0.78, 7.8, 6.2))


def draw_help(c, f=0):
    stamp(c, layer(c.size, sym_help))


def draw_appstarting(c, f=0):
    stamp(c, layer(c.size, sym_tri))
    stamp(c, layer(c.size, cat, 0.64, 4.4, 5.2, False))
    stamp(c, layer(c.size, sym_spin_small, f, 24.6, 24.2, 4.2))


def draw_wait(c, f=0):
    stamp(c, layer(c.size, cat, 0.62, 6.1, 5.6, False))
    stamp(c, layer(c.size, sym_spinner, f, 14.2, 1.7))


def draw_crosshair(c, f=0):
    stamp(c, layer(c.size, sym_cross))


def draw_ibeam(c, f=0):
    stamp(c, layer(c.size, sym_ibeam))


def draw_nwpen(c, f=0):
    stamp(c, layer(c.size, sym_pen))


def draw_no(c, f=0):
    stamp(c, layer(c.size, cat, 0.66, 3.0, 9.4))
    stamp(c, layer(c.size, sym_no_at_corner))


def sym_no_at_corner(c):
    c.ell(23.4, 8.8, 6.4, 6.4, fill=None, outline=RED, w=2.4)
    c.line([(18.8, 13.4), (28.0, 4.2)], fill=RED, w=2.4)


def draw_size_ns(c, f=0):
    stamp(c, layer(c.size, double_arrow, 0))


def draw_size_we(c, f=0):
    stamp(c, layer(c.size, double_arrow, 90))


def draw_size_nwse(c, f=0):
    stamp(c, layer(c.size, double_arrow, 45))


def draw_size_nesw(c, f=0):
    stamp(c, layer(c.size, double_arrow, -45))


def draw_sizeall(c, f=0):
    stamp(c, layer(c.size, four_arrow))


def draw_uparrow(c, f=0):
    stamp(c, layer(c.size, sym_uparrow))


def draw_hand(c, f=0):
    stamp(c, layer(c.size, sym_paw))


def draw_pin(c, f=0):
    stamp(c, layer(c.size, sym_pin))


def draw_person(c, f=0):
    stamp(c, layer(c.size, cat, 0.90, 1.6, 2.2))


SPRITES = {
    "arrow":       dict(fn=draw_arrow,       hot=(1.8, 1.8), frames=1),
    "help":        dict(fn=draw_help,        hot=(16, 16),   frames=1),
    "appstarting": dict(fn=draw_appstarting, hot=(1.8, 1.8), frames=8),
    "wait":        dict(fn=draw_wait,        hot=(16, 16),   frames=8),
    "crosshair":   dict(fn=draw_crosshair,   hot=(16, 16),   frames=1),
    "ibeam":       dict(fn=draw_ibeam,       hot=(16, 16),   frames=1),
    "nwpen":       dict(fn=draw_nwpen,       hot=(3.4, 3.4), frames=1),
    "no":          dict(fn=draw_no,          hot=(16, 16),   frames=1),
    "sizens":      dict(fn=draw_size_ns,     hot=(16, 16),   frames=1),
    "sizewe":      dict(fn=draw_size_we,     hot=(16, 16),   frames=1),
    "sizenwse":    dict(fn=draw_size_nwse,   hot=(16, 16),   frames=1),
    "sizenesw":    dict(fn=draw_size_nesw,   hot=(16, 16),   frames=1),
    "sizeall":     dict(fn=draw_sizeall,     hot=(16, 16),   frames=1),
    "uparrow":     dict(fn=draw_uparrow,     hot=(16, 4.0),  frames=1),
    "hand":        dict(fn=draw_hand,        hot=(16, 10.4), frames=1),
    "pin":         dict(fn=draw_pin,         hot=(16, 29.0), frames=1),
    "person":      dict(fn=draw_person,      hot=(16, 3.0),  frames=1),
}


def render(name, size, frame=0):
    spec = SPRITES[name]
    c = Canvas(size)
    spec["fn"](c, frame)
    return c.img.resize((size, size), Image.LANCZOS)
