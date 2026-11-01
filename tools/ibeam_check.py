# -*- coding: utf-8 -*-
"""I 型光标与正文大小对比（按本机实际 DPI 渲染，所见即屏幕所见）。

Windows 会按缩放比例挑选 .cur 里的层：100% 用 32、125% 用 40、150% 用 48、
200% 用 64。这里直接读注册表里的 AppliedDPI，把光标渲染成实际显示的那一层，
旁边摆不同字号正文（同样按缩放放大），方便一眼比高低。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont

from cursorlab import cartoon

FONT = r"C:\Windows\Fonts\msyh.ttc"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ibeam_check.png")


def applied_dpi():
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           r"Control Panel\Desktop\WindowMetrics")
        v, _ = winreg.QueryValueEx(k, "AppliedDPI")
        return int(v)
    except Exception:
        return 96


def cursor_px(dpi):
    """按 DPI 选 Windows 实际会用的那一层"""
    for target in (32, 40, 48, 64, 96):
        if target >= round(32 * dpi / 96.0):
            return target
    return 96


def main():
    dpi = applied_dpi()
    scale = dpi / 96.0
    px = cursor_px(dpi)
    ibeam = cartoon.render("ibeam", px)

    W, H = 760, 340
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    f15 = ImageFont.truetype(FONT, int(15 * scale))
    f12 = ImageFont.truetype(FONT, int(12 * scale))
    d.text((24, 14), "I 型光标 vs 正文（%d DPI / %d%% 缩放，实际取 %dpx 层，1:1）"
           % (dpi, round(scale * 100), px), font=f15, fill=(40, 40, 46))

    y = 62
    for css in (12, 13, 14, 15, 16):
        font = ImageFont.truetype(FONT, int(round(css * scale)))
        d.text((24, y + 4), "正文 %dpx：中文示例 sample" % css, font=font, fill=(30, 30, 36))
        img.paste(ibeam, (330, y), ibeam)
        d.text((330 + px + 14, y + px // 2 - 7), "← 光标", font=f12, fill=(130, 134, 142))
        y += int(round(px * 0.78)) + 10

    big = ibeam.resize((px * 3, px * 3), Image.NEAREST)
    img.paste(big, (560, 62), big)
    d.text((560, 62 + px * 3 + 4), "3 倍放大", font=f12, fill=(130, 134, 142))
    d.text((24, H - 30), "目标：光标高度 ≈ 14px 正文的汉字墨高", font=f12, fill=(130, 134, 142))

    img.save(OUT)
    print("saved %s (dpi=%d, cursor layer=%dpx)" % (OUT, dpi, px))


if __name__ == "__main__":
    main()
