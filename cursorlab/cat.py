# -*- coding: utf-8 -*-
"""
像素小猫主题 —— 黑猫 + 大眼睛 + 猫爪，全部在 32x32 网格上手工排像素。

造型约定：
  * 主体纯黑，粉只做肉垫 / 内耳 / 鼻头，最后统一加 1px 白边（暗色桌面也看得见）
  * 眼睛一律放大，瞳孔朝尖端方向 —— 可爱感主要来自眼睛比例
  * 32px 里元素要少而粗，细节多了就糊
"""

import math

from . import shapes
from .pixel import (CLEAR, G, K, K2, N, P, P2, W, Pixel, orbit)

# 问号（7x10），比 PIL 字体更像素
QMARK = ["0111100",
         "1100110",
         "0000110",
         "0001100",
         "0011000",
         "0011000",
         "0000000",
         "0011000",
         "0011000"]


# --------------------------------------------------------------- 通用零件
def ears_on(c, x0, x1, ytop):
    """一对三角猫耳：x0/x1 是头部左右边界，ytop 是头顶，耳朵往外上方支棱。"""
    for sx, xb in ((1, x0 + 1), (-1, x1 - 1)):
        c.poly([(xb, ytop + 4), (xb - sx * 3.2, ytop - 4.5), (xb + sx * 6.4, ytop + 1)], K)
        c.poly([(xb + sx * 1.0, ytop + 3.2),
                (xb - sx * 0.8, ytop - 2.2),
                (xb + sx * 4.6, ytop + 1.6)], P2)


def big_eyes(c, lx, rx, y, w=4, h=5, look=(0, 1)):
    """大眼睛：眼白 + 瞳孔 + 左上高光。"""
    for x in (lx, rx):
        c.rect(x, y, x + w - 1, y + h - 1, W)
        px, py = x + 1 + look[0], y + 1 + look[1]
        c.rect(px, py, px + 1, py + min(2, h - 3), K)
        c.point(x + 1, y + 1, (255, 255, 255, 255))


def head(c, cx, cy, r):
    c.ellipse(cx - r, cy - r, cx + r, cy + r, K)


def paw_big(c, cx=16, cy=18):
    """大猫爪：四个趾垫 + 掌垫。"""
    c.ellipse(cx - 7, cy - 2, cx + 7, cy + 7, K)
    c.ellipse(cx - 4, cy + 0.5, cx + 4, cy + 5, P)
    for dx, dy in [(-8.5, -5.5), (-3, -8.5), (3, -8.5), (8.5, -5.5)]:
        c.circle(cx + dx, cy + dy, 3.0, K)
        c.circle(cx + dx, cy + dy, 1.5, P)


def paw_small(c, cx=16, cy=18):
    c.ellipse(cx - 5, cy - 1.5, cx + 5, cy + 4.5, K)
    c.ellipse(cx - 3, cy - 0.5, cx + 3, cy + 3.5, P)
    for dx, dy in [(-6, -4), (-2, -6.5), (2, -6.5), (6, -4)]:
        c.circle(cx + dx, cy + dy, 2.3, K)
        c.circle(cx + dx, cy + dy, 1.1, P)


# --------------------------------------------------------------- 角色
def draw_arrow(c, f=0):
    shapes.arrow(c)

def draw_help(c, f=0):
    head(c, 9, 11, 7)
    ears_on(c, 2, 16, 4)
    big_eyes(c, 5, 11, 9, w=3, h=4, look=(1, 1))
    c.rect(8, 15, 10, 16, P)
    c.rim(W)
    c.circle(24, 22, 7.5, K)                     # 问号气泡
    c.glyph(QMARK, 21, 18, P)
    c.rim(W)


def draw_appstarting(c, f=0):
    draw_arrow(c, f)
    orbit(c, 25.5, 7.5, 4.5, f, dot=1.4)


def draw_wait(c, f=0):
    paw_small(c, 16, 19)
    c.rim(W)
    orbit(c, 16, 17, 12.0, f, dot=1.5)


def draw_crosshair(c, f=0):
    for box in [(14, 2, 16, 10), (14, 22, 16, 30), (2, 14, 10, 16), (22, 14, 30, 16)]:
        c.rect(*box, K)
    c.ellipse(13, 13, 19, 19, P)                 # 中心肉垫
    c.rim(W)


def draw_ibeam(c, f=0):
    shapes.ibeam(c)

def draw_nwpen(c, f=0):
    c.line([(10, 10), (23, 23)], K, 4)           # 笔身
    c.poly([(3, 3), (12, 7), (7, 12)], K)        # 笔尖
    c.rect(4, 4, 5, 5, P)
    c.rect(16, 16, 19, 19, P)                    # 粉握笔环
    c.rim(W)


def draw_no(c, f=0):
    c.circle(16, 18, 10, K)                      # 禁行牌
    c.poly([(7, 12), (6, 2), (14, 8)], K)        # 猫耳
    c.poly([(25, 12), (26, 2), (18, 8)], K)
    c.line([(9, 25), (23, 11)], P, 3)            # 斜杠
    c.rim(W)


def draw_size_ns(c, f=0):
    shapes.double_arrow(c, 0)

def draw_size_we(c, f=0):
    shapes.double_arrow(c, 90)

def draw_size_nwse(c, f=0):
    shapes.double_arrow(c, 45)

def draw_size_nesw(c, f=0):
    shapes.double_arrow(c, -45)

def draw_sizeall(c, f=0):
    shapes.four_arrow(c)

def draw_uparrow(c, f=0):
    c.poly([(16, 5), (25, 15), (19, 15), (19, 27), (13, 27), (13, 15), (7, 15)], K)
    ears_on(c, 8, 24, 9)
    big_eyes(c, 12, 18, 17, w=3, h=3, look=(0, 0))
    c.rim(W)


def draw_hand(c, f=0):
    paw_big(c, 16, 17)
    c.rim(W)


def draw_pin(c, f=0):
    c.poly([(16, 31), (10.5, 19), (21.5, 19)], K)   # 针尖
    paw_small(c, 16, 11)
    c.rim(W)


def draw_person(c, f=0):
    c.ellipse(5, 20, 27, 34, K)                    # 身体
    head(c, 16, 11, 8)
    ears_on(c, 8, 24, 3)
    big_eyes(c, 11, 18, 9, w=4, h=5, look=(0, 1))
    c.rect(15, 16, 17, 17, P)
    c.rim(W)


SPRITES = {
    "arrow":       dict(fn=draw_arrow,       hot=(3, 4),   frames=1),
    "help":        dict(fn=draw_help,        hot=(2, 4),   frames=1),
    "appstarting": dict(fn=draw_appstarting, hot=(3, 4),   frames=8),
    "wait":        dict(fn=draw_wait,        hot=(16, 16), frames=8),
    "crosshair":   dict(fn=draw_crosshair,   hot=(16, 16), frames=1),
    "ibeam":       dict(fn=draw_ibeam,       hot=(16, 12), frames=1),
    "nwpen":       dict(fn=draw_nwpen,       hot=(3, 3),   frames=1),
    "no":          dict(fn=draw_no,          hot=(16, 16), frames=1),
    "sizens":      dict(fn=draw_size_ns,     hot=(16, 16), frames=1),
    "sizewe":      dict(fn=draw_size_we,     hot=(16, 16), frames=1),
    "sizenwse":    dict(fn=draw_size_nwse,   hot=(16, 16), frames=1),
    "sizenesw":    dict(fn=draw_size_nesw,   hot=(16, 16), frames=1),
    "sizeall":     dict(fn=draw_sizeall,     hot=(16, 16), frames=1),
    "uparrow":     dict(fn=draw_uparrow,     hot=(16, 5),   frames=1),
    "hand":        dict(fn=draw_hand,        hot=(16, 7),   frames=1),
    "pin":         dict(fn=draw_pin,         hot=(16, 30), frames=1),
    "person":      dict(fn=draw_person,      hot=(16, 5),   frames=1),
}


def render(name, size, frame=0):
    spec = SPRITES[name]
    c = Pixel(N)
    spec["fn"](c, frame)
    return c.image(size)
