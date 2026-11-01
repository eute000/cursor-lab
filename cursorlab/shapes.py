# -*- coding: utf-8 -*-
"""箭头 / I 型 / 双箭头 的像素级实现（32 网格直接排坐标）。"""

import math

from .pixel import K, P, P2, W, Pixel


def rot(pts, deg, cx=16.0, cy=16.0):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * ca - (y - cy) * sa,
             cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]


def band(a, b, w):
    """a->b 的加宽带状多边形（画尾巴 / 笔身用）。"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln * w / 2.0, dx / ln * w / 2.0
    return [(a[0] + nx, a[1] + ny), (a[0] - nx, a[1] - ny),
            (b[0] - nx, b[1] - ny), (b[0] + nx, b[1] + ny)]


def ear(c, tip, a, b, inner=P2):
    """三角猫耳 + 细一条粉色内耳。"""
    c.poly([tip, a, b], K)
    cx = (tip[0] + a[0] + b[0]) / 3.0
    cy = (tip[1] + a[1] + b[1]) / 3.0

    def sh(p, t):
        return (p[0] + (cx - p[0]) * t, p[1] + (cy - p[1]) * t)

    c.poly([sh(tip, 0.46), sh(a, 0.78), sh(b, 0.78)], inner)


def arrow(c):
    """指针 = 猫头（左上角就是点击点）+ 卷起来的猫尾巴当杆。"""
    c.poly(band((18.0, 16.0), (25.5, 26.5), 4.8), K)      # 尾巴
    c.circle(25.8, 27.6, 2.5, K)
    ear(c, (4.5, 0), (6.5, 9), (12.5, 6))                 # 左耳
    ear(c, (20.5, 0), (18.5, 9), (12.5, 6))               # 右耳
    c.ellipse(4, 4, 21, 21, K)                            # 头
    # 眼睛（占比放大，可爱感主要来自这里）
    for x in (7, 13):
        c.rect(x, 10, x + 3, 15, W)
        c.rect(x + 1, 12, x + 2, 14, K)
        c.point(x + 1, 10, W)
    c.rect(11, 17, 13, 18, P)                             # 鼻头
    c.line([(11, 19), (10, 20)], P2, 1)
    c.line([(13, 19), (14, 20)], P2, 1)
    c.rim(W)


def ibeam(c):
    """I 型文本光标：竖杆 + 上下横，中间一颗粉肉垫。"""
    c.rect(14, 3, 17, 27, K)
    c.rect(10, 2, 21, 5, K)
    c.rect(10, 25, 21, 28, K)
    c.rect(15, 14, 16, 17, P)
    c.rim(W)


def double_arrow(c, deg=0):
    """双头箭头：竖版多边形，按需要旋转（0 / 90 / 45 / -45）。"""
    base = [(16, 2), (21, 8), (18, 8), (18, 24), (21, 24), (16, 30),
            (11, 24), (14, 24), (14, 8), (11, 8)]
    c.poly(rot(base, deg) if deg else base, K)
    c.rect(15, 15, 17, 17, P)
    c.rim(W)


def four_arrow(c):
    base = [(16, 2), (21, 8), (18, 8), (18, 14), (24, 14), (24, 11), (30, 16),
            (24, 21), (24, 18), (18, 18), (18, 24), (21, 24), (16, 30),
            (11, 24), (14, 24), (14, 18), (8, 18), (8, 21), (2, 16),
            (8, 11), (8, 14), (14, 14), (14, 8), (11, 8)]
    c.poly(base, K)
    c.rect(15, 15, 17, 17, P)
    c.rim(W)
