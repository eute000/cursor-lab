# -*- coding: utf-8 -*-
"""
像素画布：所有造型都在 32x32 网格上按整数像素画，绝不做抗锯齿。
输出时用 NEAREST 整数倍放大，保持像素颗粒。
"""

from PIL import Image, ImageDraw

N = 32

# ---- 调色板（黑为主，粉做肉垫/鼻头，金做小星星）----
K = (18, 18, 23, 255)        # 主黑
K2 = (46, 46, 57, 255)       # 次黑
W = (252, 252, 255, 255)     # 白（眼白、外描边）
P = (255, 138, 170, 255)     # 粉（肉垫、鼻头）
P2 = (214, 74, 114, 255)     # 深粉
G = (255, 208, 88, 255)      # 金
G2 = (168, 130, 52, 255)     # 暗金（拖尾）
CLEAR = (0, 0, 0, 0)


class Pixel:
    def __init__(self, n=N):
        self.n = n
        self.img = Image.new("RGBA", (n, n), CLEAR)
        self.d = ImageDraw.Draw(self.img)

    # ---------- 基础 ----------
    def point(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.n and 0 <= y < self.n:
            self.img.putpixel((x, y), c)

    def rect(self, x0, y0, x1, y1, c):
        self.d.rectangle([int(x0), int(y0), int(x1), int(y1)], fill=c)

    def ellipse(self, x0, y0, x1, y1, c):
        self.d.ellipse([int(x0), int(y0), int(x1), int(y1)], fill=c)

    def circle(self, cx, cy, r, c):
        self.ellipse(cx - r, cy - r, cx + r, cy + r, c)

    def poly(self, pts, c):
        self.d.polygon([(int(x), int(y)) for x, y in pts], fill=c)

    def line(self, pts, c, w=1):
        self.d.line([(int(x), int(y)) for x, y in pts], fill=c, width=int(w))

    def glyph(self, rows, x, y, c):
        """rows 是 '01101' 这样的字符串数组，1 表示上色。"""
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch == "1":
                    self.point(x + i, y + j, c)

    # ---------- 组合 ----------
    def rim(self, color=W, diag=False):
        """给所有实心像素外面套 1px 边——像素风里让黑猫在任何背景上都看得见。"""
        src = self.img.copy().load()
        dst = self.img.load()
        offs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if diag:
            offs += [(-1, -1), (1, -1), (-1, 1), (1, 1)]
        n = self.n
        for y in range(n):
            for x in range(n):
                if src[x, y][3] != 0:
                    continue
                for dx, dy in offs:
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < n and 0 <= yy < n and src[xx, yy][3] > 0:
                        dst[x, y] = color
                        break

    def blit(self, other, dx=0, dy=0):
        self.img.alpha_composite(other.img, (int(dx), int(dy)))

    def image(self, size):
        """整数倍 NEAREST 放大，保持像素边缘。"""
        if size % self.n:
            raise ValueError("尺寸要能被 %d 整除：%d" % (self.n, size))
        return self.img.resize((size, size), Image.NEAREST)


# ---------- 可复用零件 ----------
def paw(c, cx, cy, scale=1.0, pad=P, dark=K):
    """猫爪印：一个大肉垫 + 四个趾垫。cx,cy 是爪心。"""
    s = scale
    c.ellipse(cx - 5.5 * s, cy - 1.5 * s, cx + 5.5 * s, cy + 5.5 * s, dark)   # 掌垫
    for dx, dy, r in [(-6.4, -6.0, 2.2), (-2.2, -8.4, 2.3),
                      (2.2, -8.4, 2.3), (6.4, -6.0, 2.2)]:
        c.circle(cx + dx * s, cy + dy * s, r * s, dark)
    # 粉色内垫
    c.ellipse(cx - 3.2 * s, cy - 0.4 * s, cx + 3.2 * s, cy + 3.4 * s, pad)
    for dx, dy, r in [(-6.4, -6.0, 1.1), (-2.2, -8.2, 1.1),
                      (2.2, -8.2, 1.1), (6.4, -6.0, 1.1)]:
        c.circle(cx + dx * s, cy + dy * s, r * s, pad)


def orbit(c, cx, cy, r, f, n=8, dot=1.6, main=G, dim=G2):
    """转圈的小星星：f 帧时最亮的在最上面，后面三段渐暗。"""
    import math
    for i in range(n):
        a = -math.pi / 2 + i * 2 * math.pi / n
        x = cx + r * math.cos(a)
        y = cy + r * math.sin(a)
        lag = (i - f) % n
        if lag == 0:
            c.circle(x, y, dot + 1.0, W)
            c.circle(x, y, dot, main)
        elif lag <= 3:
            c.circle(x, y, max(0.9, dot - 0.2 * lag), dim)


QMARK = ["01110",
         "10001",
         "00001",
         "00110",
         "00100",
         "00000",
         "00100"]
