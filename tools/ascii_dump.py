# -*- coding: utf-8 -*-
"""把任意造型打成 ASCII 像素图，方便在终端里逐像素调（不依赖看图）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cursorlab import cat
from cursorlab.pixel import G, K, N, P, P2, W, Pixel

SYM = {K: "#", P: "p", P2: "P", W: ".", G: "*"}


def dump(name, frame=0, show_symbols=True):
    c = Pixel(N)
    cat.SPRITES[name]["fn"](c, frame)
    px = c.img.load()
    print("--- %s  hotspot=%s  frames=%d ---"
          % (name, cat.SPRITES[name]["hot"], cat.SPRITES[name]["frames"]))
    for y in range(N):
        row = ""
        for x in range(N):
            col = px[x, y]
            if col[3] == 0:
                row += " "
            elif show_symbols:
                row += SYM.get(col, "?")
            else:
                row += "#"
        print("%2d|%s|" % (y, row))


if __name__ == "__main__":
    names = sys.argv[1:] or ["arrow"]
    for nm in names:
        dump(nm)
