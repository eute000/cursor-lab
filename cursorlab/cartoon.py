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


def rim(c, color=CREAM, w=1.0):
    """给整层套外描边（按设计单位精确膨胀，不靠模糊阈值）。

    之前用「高斯模糊 + 阈值」，实际膨胀出 3px 的白边，把 16.5px 的图形
    撑成 26px 的"贴纸"—— 用户会觉得"I 型还是那么大"。
    改成反复用 3×3 MaxFilter 膨胀，每轮正好 1 个画布像素，粗细分毫不差。
    """
    a = c.img.split()[3]
    passes = max(1, int(round(c.s(w))))          # 设计单位 -> 画布像素
    grown = a
    for _ in range(passes):
        grown = grown.filter(ImageFilter.MaxFilter(3))
    ring = ImageChops.subtract(grown, a)
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
def cat(c, s=0.72, dx=8.0, dy=7.0, tail=True, phase=0.0, pose="normal"):
    """参考图里那只黑猫。

    phase：-1..1 的相位，驱动尾巴摆动 + 轻微呼吸（arrow 的常驻微动画用）
    pose ："normal" 或 "press"（按下时低头 + 眯眼 + 握爪）
    """
    def T(x, y):
        return (dx + x * s, dy + y * s)

    breathe = phase * 0.20                      # 整只猫上下浮动 0.2 格
    head_drop = 0.45 if pose == "press" else 0.0
    dy = dy + breathe

    if tail:
        sway = phase * 0.55
        c.line([T(20.5, 22.0), T(26.5, 22.6 + sway * 0.6), T(29.6, 18.6 + sway)],
               fill=BODY, w=2.4 * s)

    # 身体 + 两只小爪（按下时收成握拳的小圆）
    cx, cy = T(16, 21.6)
    c.ell(cx, cy, 6.6 * s, 6.0 * s, fill=BODY)
    if pose == "press":
        for px in (12.8, 19.2):
            cx2, cy2 = T(px, 26.3)
            c.ell(cx2, cy2, 1.5 * s, 1.5 * s, fill=BODY)
    else:
        for px in (12.2, 19.8):
            cx2, cy2 = T(px, 26.8)
            c.ell(cx2, cy2, 2.1 * s, 1.8 * s, fill=BODY)

    # 两只小三角耳（先画，被头盖住底边）
    for sx in (-1, 1):
        c.poly([T(16 + sx * 7.6, 6.6), T(16 + sx * 10.6, 0.8), T(16 + sx * 2.6, 4.6)],
               fill=BODY, outline=LINE, w=1.1 * s)

    # 头（按下时整体下移，像被摸头）
    cx, cy = T(16, 12.0 + head_drop)
    c.ell(cx, cy, 9.6 * s, 8.6 * s, fill=BODY, outline=LINE, w=1.1 * s)

    # 眼睛：两眼白几乎相触；按下时眯起来
    eye_ry = 3.2 if pose == "press" else 4.8
    for ex in (12.0, 20.0):
        cx2, cy2 = T(ex, 12.4 + head_drop)
        c.ell(cx2, cy2, 3.8 * s, eye_ry * s, fill=WHITE, outline=LINE, w=0.75 * s)
    for ex in (12.3, 19.7):
        cx2, cy2 = T(ex, 13.2 + head_drop)
        c.ell(cx2, cy2, 2.1 * s, min(3.0, eye_ry - 0.6) * s, fill=BODY)
    for ex in (11.1, 18.5):
        cx2, cy2 = T(ex, 11.5 + head_drop)
        c.ell(cx2, cy2, 0.95 * s, 0.95 * s, fill=WHITE)


# ------------------------------------------------------------------ 符号
def sym_tri(c):
    """左上角空心小三角 ▷（尖端 = 热点）"""
    c.poly([(2.3, 2.3), (10.9, 6.1), (6.1, 10.9)], fill=None, outline=BODY, w=1.9)


def sym_cross(c):
    for a, b in [((16, 4.2), (16, 11.8)), ((16, 20.2), (16, 27.8)),
                 ((4.2, 16), (11.8, 16)), ((20.2, 16), (27.8, 16))]:
        c.line([a, b], fill=BODY, w=2.0)
    c.ell(16, 16, 1.9, 1.9, fill=BODY)


def draw_ibeam_press(c, f=0):
    """I 型按下态：I 加粗下沉（像压进纸里）+ 猫低头眯眼握爪"""
    stamp(c, layer(c.size, sym_ibeam_press))
    stamp(c, layer(c.size, cat, 0.73, 7.6, 6.4, True, 0.0, "press"))


def sym_ibeam_press(c):
    c.line([(6.2, 3.2), (6.2, 10.0)], fill=BODY, w=2.4, caps=False)
    c.line([(3.8, 3.2), (8.6, 3.2)], fill=BODY, w=2.4)
    c.line([(3.8, 10.0), (8.6, 10.0)], fill=BODY, w=2.4)


def sym_ibeam(c):
    """角标位的 I 型（和 ▷ / ？ 同一个槽位），深色本体 8.7 格高。

    之前是居中的大 I；用户要求统一版式：猫仍在右下，左上角标位换成 I。
    """
    c.line([(6.2, 2.8), (6.2, 9.6)], fill=BODY, w=1.9, caps=False)
    c.line([(4.0, 2.8), (8.4, 2.8)], fill=BODY, w=1.9)
    c.line([(4.0, 9.6), (8.4, 9.6)], fill=BODY, w=1.9)


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


def sym_paw(c, s=1.0, grip=False):
    """猫爪印；s 用于"抓取"动画的缩放（锚点 16,16）"""
    def X(x):
        return 16 + (x - 16) * s

    def Y(y):
        return 16 + (y - 16) * s

    pull = 0.76 if grip else 1.0          # 握爪时趾垫向掌心收拢
    grow = 1.07 if grip else 1.0          # 掌垫同时放大一点

    def G(x, y):
        return (16 + (x - 16) * pull, 20.6 + (y - 20.6) * pull)

    toes = ((9.2, 13.6, 2.6), (13.6, 10.4, 2.8),
            (18.4, 10.4, 2.8), (22.8, 13.6, 2.6))
    inner = ((9.2, 13.9, 0.9), (13.7, 10.9, 1.0),
             (18.3, 10.9, 1.0), (22.8, 13.9, 0.9))
    for x, y, r in toes:
        gx, gy = G(x, y)
        c.ell(X(gx), Y(gy), r * s * (0.92 if grip else 1.0), r * s * (0.92 if grip else 1.0),
              fill=BODY)
    c.ell(16, Y(20.6), 6.4 * s * grow, 5.4 * s * grow, fill=BODY)
    for x, y, r in inner:
        gx, gy = G(x, y)
        c.ell(X(gx), Y(gy), r * s, r * s, fill=CREAM)
    c.ell(16, Y(20.6), 2.6 * s * grow, 2.2 * s * grow, fill=CREAM)


def sym_no(c):
    c.ell(16, 16, 9.6, 9.6, fill=None, outline=RED, w=2.6)
    c.line([(9.4, 22.6), (22.6, 9.4)], fill=RED, w=2.6)


def sym_help(c):
    """角标位的手写感问号（不要圆框，照箭头版式）"""
    c.text(6.4, 6.2, "?", 10.0, fill=BODY)


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


def sym_cycle(c, f, cx=6.6, cy=6.6, r=5.8, w=1.8, head=3.3):
    """带箭头的圆环箭头（转圈/加载感）：110° 缺口 + 三角箭头，45°/帧转 8 帧"""
    start = -60 + f * 45
    end = start + 265
    c.arc(cx, cy, r, start, end, fill=BODY, w=w)
    a = math.radians(end)
    ex, ey = cx + r * math.cos(a), cy + r * math.sin(a)
    tx, ty = -math.sin(a), math.cos(a)      # 切向
    nx, ny = math.cos(a), math.sin(a)       # 径向
    c.poly([(ex + tx * head, ey + ty * head),
            (ex + nx * head * 0.60, ey + ny * head * 0.60),
            (ex - nx * head * 0.60, ey - ny * head * 0.60)], fill=BODY)


def sym_spin_small(c, f, cx=23.0, cy=23.0, r=4.4):
    """角标处的小转圈（appstarting 用，尾巴收口）"""
    start = f * 45
    c.arc(cx, cy, r, start, start + 250, fill=BODY, w=1.9)
    for ang in (start, start + 250):
        a = math.radians(ang)
        c.ell(cx + r * math.cos(a), cy + r * math.sin(a), 0.95, 0.95, fill=BODY)


# ------------------------------------------------------------------ 角色
def _phase(f, frames=12):
    """0..frames-1 -> -1..1 的正弦相位"""
    return math.sin(2 * math.pi * f / frames)


def draw_arrow(c, f=0):
    """主指针：12 帧常驻微动画（尾巴轻摆 + 呼吸 + 偶尔抖耳朵）"""
    stamp(c, layer(c.size, sym_tri))
    stamp(c, layer(c.size, cat, 0.73, 7.6, 6.4, True, _phase(f)))


def draw_arrow_press(c, f=0):
    """按下态：同一版式，低头 + 眯眼 + 握爪（由 tools/click_fx.py 切换）"""
    stamp(c, layer(c.size, sym_tri))
    stamp(c, layer(c.size, cat, 0.73, 7.6, 6.4, True, 0.0, "press"))


def draw_help(c, f=0):
    stamp(c, layer(c.size, sym_help))
    stamp(c, layer(c.size, cat, 0.73, 7.6, 6.4))


def draw_appstarting(c, f=0):
    """后台启动：大转圈 + 猫（方案 2：与 wait 对调后）"""
    stamp(c, layer(c.size, cat, 0.73, 7.6, 6.4))
    stamp(c, layer(c.size, sym_cycle, f, 7.2, 7.2, 5.0))


def draw_wait(c, f=0):
    """系统忙：▷ + 猫 + 右下小转圈（方案 2 对调后，保留小转圈免得和 arrow 撞脸）"""
    stamp(c, layer(c.size, sym_tri))
    stamp(c, layer(c.size, cat, 0.73, 7.6, 6.4))
    stamp(c, layer(c.size, sym_cycle, f, 27.0, 26.6, 3.4, 1.55, 2.1))


def draw_crosshair(c, f=0):
    stamp(c, layer(c.size, sym_cross))


def draw_ibeam(c, f=0):
    stamp(c, layer(c.size, sym_ibeam))
    stamp(c, layer(c.size, cat, 0.73, 7.6, 6.4))


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
    """NW-SE 对轴（↖↘）：屏幕坐标 y 朝下，所以用 -45°"""
    stamp(c, layer(c.size, double_arrow, -45))


def draw_size_nesw(c, f=0):
    """NE-SW 对轴（↗↙）：+45°"""
    stamp(c, layer(c.size, double_arrow, 45))


def draw_sizeall(c, f=0):
    stamp(c, layer(c.size, four_arrow))


def draw_uparrow(c, f=0):
    stamp(c, layer(c.size, sym_uparrow))


def draw_hand(c, f=0):
    """手型：平时完全静止"""
    stamp(c, layer(c.size, sym_paw))


def draw_hand_press(c, f=0):
    """按下时的握爪：趾垫收拢 + 掌垫放大（只在按住时出现）"""
    stamp(c, layer(c.size, sym_paw, 1.0, True))


def draw_pin(c, f=0):
    stamp(c, layer(c.size, sym_pin))


def draw_person(c, f=0):
    stamp(c, layer(c.size, cat, 0.90, 1.6, 2.2))


SPRITES = {
    "arrow":       dict(fn=draw_arrow,       hot=(2.3, 2.3), frames=12),
    "help":        dict(fn=draw_help,        hot=(2.8, 2.8), frames=1),
    "appstarting": dict(fn=draw_appstarting, hot=(16, 16),   frames=8),
    "wait":        dict(fn=draw_wait,        hot=(2.3, 2.3), frames=8),
    "crosshair":   dict(fn=draw_crosshair,   hot=(16, 16),   frames=1),
    "ibeam":       dict(fn=draw_ibeam,       hot=(6.2, 6.2), frames=1),
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


# 不属于注册表 17 项、由助手程序切换的附加造型
EXTRA = {
    "arrow_press": dict(fn=draw_arrow_press, hot=(2.3, 2.3), frames=1),
    "ibeam_press": dict(fn=draw_ibeam_press, hot=(6.2, 6.2), frames=1),
    "hand_press": dict(fn=draw_hand_press, hot=(16, 10.4), frames=1),
}


def render(name, size, frame=0):
    spec = SPRITES.get(name) or EXTRA[name]
    c = Canvas(size)
    spec["fn"](c, frame)
    return c.img.resize((size, size), Image.LANCZOS)
