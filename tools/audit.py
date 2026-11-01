# -*- coding: utf-8 -*-
"""体检：量每个造型在 150% 缩放下（48px 层）的深色本体尺寸、留白、热点。

用来抓"某个图标偏大/偏小/贴边"这类问题，而不是靠眼睛猜。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cursorlab import cartoon

LAYER = 48
EDGE_WARN = 1.0     # 设计格，四周留白少于这个就警告


def dark_bbox(im):
    px = im.load()
    w, h = im.size
    xs, ys = [], []
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 200 and r < 90 and g < 90:      # 深色本体（不含米白描边）
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def main():
    scale = LAYER / 32.0
    print("%-11s %-9s %-9s %-9s %s" % ("角色", "深色宽", "深色高", "留白(最小)", "热点"))
    print("-" * 56)
    for key in cartoon.SPRITES:
        im = cartoon.render(key, LAYER)
        bb = dark_bbox(im)
        if bb is None:
            print("%-11s 渲染为空！" % key)
            continue
        x0, y0, x1, y1 = bb
        margin = min(x0, y0, LAYER - 1 - x1, LAYER - 1 - y1) / scale
        flag = "  ← 贴边" if margin < EDGE_WARN else ""
        hot = cartoon.SPRITES[key]["hot"]
        print("%-11s %-9.1f %-9.1f %-9.1f %s%s"
              % (key, (x1 - x0 + 1) / scale, (y1 - y0 + 1) / scale, margin, hot, flag))


if __name__ == "__main__":
    main()
