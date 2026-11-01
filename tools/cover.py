# -*- coding: utf-8 -*-
"""出投稿封面图（16:9）：左英雄图 + 右标题与光标小样。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont

from cursorlab import cartoon

W, H = 1600, 900
BG_TOP = (18, 20, 26)
BG_BOT = (30, 34, 44)
INK = (238, 240, 246)
MUT = (150, 156, 170)
ACCENT = (255, 138, 170)
CREAM = (250, 250, 252)

F_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
F_REG = r"C:\Windows\Fonts\msyh.ttc"


def font(path, size):
    return ImageFont.truetype(path, size) if os.path.exists(path) else ImageFont.load_default()


def vgrad(size, top, bot):
    w, h = size
    img = Image.new("RGB", (w, h), top)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / float(h - 1)
        d.line([(0, y), (w, y)],
               fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return img


def main():
    img = vgrad((W, H), BG_TOP, BG_BOT).convert("RGBA")

    # 背景淡淡的光斑
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-200, -260, 900, 700], fill=(255, 138, 170, 16))
    gd.ellipse([900, 420, 1900, 1200], fill=(120, 226, 255, 14))
    img.alpha_composite(glow.filter(__import__("PIL.ImageFilter", fromlist=["x"]).GaussianBlur(90)))

    # 左：大猫（person 全身）+ 箭头光标叠在左上
    big = cartoon.render("person", 560)
    img.alpha_composite(big, (60, 250))
    arrow = cartoon.render("arrow", 300)
    img.alpha_composite(arrow, (120, 40))

    d = ImageDraw.Draw(img)

    # 右：标题
    x = 760
    d.text((x, 150), "Cartoon Cat", font=font(F_BOLD, 112), fill=INK)
    d.text((x, 275), "Cute black-cat cursor set for Windows", font=font(F_REG, 34), fill=MUT)

    # 卖点
    lines = [
        ("17 cursors", "all Windows roles, 32/48/64 px"),
        ("Animated", "arrow sways its tail, busy spins"),
        ("Click effect", "cat squints & grips while you hold"),
        ("Unified layout", "cat fixed, only the corner mark changes"),
    ]
    y = 360
    for head, tail in lines:
        d.ellipse([x, y + 10, x + 12, y + 22], fill=ACCENT)
        d.text((x + 26, y), head, font=font(F_BOLD, 32), fill=INK)
        d.text((x + 26 + font(F_BOLD, 32).getlength(head) + 14, y + 4), tail,
               font=font(F_REG, 26), fill=MUT)
        y += 62

    # 底部：几个小样（浅底深底各一）
    keys = ["arrow", "ibeam", "hand", "wait", "no", "sizeall"]
    x0, y0, cell = 700, 650, 92
    d.text((700, 610), "sample", font=font(F_REG, 22), fill=MUT)
    for i, k in enumerate(keys):
        art = cartoon.render(k, cell)
        bg = (238, 240, 246, 255) if i % 2 == 0 else (44, 48, 58, 255)
        tx = x0 + i * (cell + 14)
        tile = Image.new("RGBA", (cell, cell), bg)
        tile.alpha_composite(art)
        img.alpha_composite(tile, (tx, y0))
    img.alpha_composite(Image.new("RGBA", (0, 0)))

    # 右下角仓库地址
    d.text((760, 800), "github.com/eute000/cursor-lab", font=font(F_REG, 30), fill=(140, 200, 255))
    d.text((760, 840), "MIT License · free to remix", font=font(F_REG, 22), fill=MUT)

    out = r"E:\deepseek\cursor-lab\dist\cover-1600x900.png"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.convert("RGB").save(out, quality=95)
    img.resize((800, 450), Image.LANCZOS).convert("RGB").save(
        out.replace("1600x900", "800x450"), quality=95)
    print("saved", out)


if __name__ == "__main__":
    main()
