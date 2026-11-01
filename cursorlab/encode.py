# -*- coding: utf-8 -*-
"""
Cursor 文件编码器 —— 不依赖 Pillow 的 ICO 插件自己拼二进制。

要点（踩过的坑）：
  * .cur 里只能放 DIB 位图；Pillow 存大尺寸时会用 PNG 压缩，塞进 .cur 就是坏文件
  * 光标目录项里 planes / bitCount 两个字段被挪用存热点 (x, y)
  * .ani 是 RIFF/ACON：anih + rate + seq + LIST('fram') 里若干个 icon 块

对外只暴露四个东西：dib32()、cur_bytes()、ani_bytes()、check_hotspot()。
输入不合法一律抛 ValueError 并说明是哪个值坏了 —— 不要让它变成
struct.error: 'H' format requires 0 <= number <= 65535 这种，没人看得懂。
"""

import struct

DESIGN = 32.0          # 设计网格（热点坐标按这个网格给）
MAX_DIM = 256          # 目录项宽高各占 1 字节，0 表示 256

# 注册表标准顺序（install.ps1 里的 $map 必须与之一致）
ROLES = [
    "Arrow", "Help", "AppStarting", "Wait", "Crosshair", "IBeam", "NWPen",
    "No", "SizeNS", "SizeWE", "SizeNWSE", "SizeNESW", "SizeAll", "UpArrow",
    "Hand", "Pin", "Person",
]


def dib32(im):
    """32bpp DIB：高度写 2*h（上半 XOR 颜色，下半 AND 透明掩码）。

    DIB 是自下而上存的：第一行是图像最底下那一行。
    AND 掩码按 4 字节对齐（宽度不是 32 的倍数时后面要补 0）。
    """
    w, h = im.size
    if w <= 0 or h <= 0:
        raise ValueError("图像尺寸非法: %dx%d" % (w, h))
    if w > MAX_DIM or h > MAX_DIM:
        raise ValueError("图像尺寸超过 %d: %dx%d（.cur 目录项存不下）"
                         % (MAX_DIM, w, h))
    px = im.convert("RGBA").load()

    rows = []
    for y in range(h - 1, -1, -1):          # DIB 自下而上
        row = bytearray()
        for x in range(w):
            r, g, b, a = px[x, y]
            row += bytes((b, g, r, a))      # BGRA
        rows.append(bytes(row))
    xor = b"".join(rows)

    stride = ((w + 31) // 32) * 4           # AND 掩码行按 4 字节对齐
    rows = []
    for y in range(h - 1, -1, -1):
        row = bytearray(stride)
        for x in range(w):
            if px[x, y][3] < 128:
                row[x // 8] |= 0x80 >> (x % 8)
        rows.append(bytes(row))
    andmask = b"".join(rows)

    header = struct.pack("<IiiHHIIiiII", 40, w, h * 2, 1, 32, 0,
                         len(xor) + len(andmask), 0, 0, 0, 0)
    return header + xor + andmask


def check_hotspot(hotspot):
    """校验设计网格热点，返回 (x, y) 两个 float。

    合法范围是 0..DESIGN（含端点）。给负数或超出 32 的值说明调用方算错了，
    直接报错比让 struct.pack 抛 "H format requires 0 <= number <= 65535" 强。
    """
    try:
        x, y = hotspot
    except (TypeError, ValueError):
        raise ValueError("热点必须是 (x, y) 两个数，收到 %r" % (hotspot,)) from None
    out = []
    for name, v in (("x", x), ("y", y)):
        try:
            f = float(v)
        except (TypeError, ValueError):
            raise ValueError("热点 %s 不是数字: %r" % (name, v)) from None
        if not 0.0 <= f <= DESIGN:
            raise ValueError("热点 %s=%r 超出 0..%g 的设计网格"
                             % (name, v, DESIGN))
        out.append(f)
    return out[0], out[1]


def _layer_hotspot(hotspot, w, h):
    """设计网格 -> 某一档像素尺寸的热点，四舍五入后夹在图像内。

    hot=32 舍入到 32 会落到图像外面（最后一个像素是 31），夹一下。
    """
    hx = int(round(hotspot[0] / DESIGN * w))
    hy = int(round(hotspot[1] / DESIGN * h))
    return min(max(hx, 0), w - 1), min(max(hy, 0), h - 1)


def cur_bytes(images, hotspot):
    """images: 同一造型的多尺寸 PIL 图；hotspot: 设计网格(0..32) 坐标。"""
    images = list(images)
    if not images:
        raise ValueError("cur_bytes 至少要一张图")
    hotspot = check_hotspot(hotspot)

    entries, body = [], b""
    for im in images:
        blob = dib32(im)
        w, h = im.size
        hx, hy = _layer_hotspot(hotspot, w, h)
        entries.append((w, h, hx, hy, len(blob)))
        body += blob

    out = struct.pack("<HHH", 0, 2, len(entries))       # type=2 => cursor
    dirs, off = b"", 6 + 16 * len(entries)
    for (w, h, hx, hy, n) in entries:
        # 0 表示 256（目录项只有 1 字节）
        dirs += struct.pack("<BBBBHHII", w % 256, h % 256, 0, 0, hx, hy, n, off)
        off += n
    return out + dirs + body


def _chunk(cid, data):
    """RIFF chunk：块长度写原始长度，数据为奇数时补一个 0 对齐。"""
    pad = b"\x00" if len(data) & 1 else b""
    return cid + struct.pack("<I", len(data)) + data + pad


def ani_bytes(frames, delay_ms=90):
    """frames: 若干个 .cur 字节串。delay_ms 会被换算成 jiffies（1/60 秒）。"""
    frames = list(frames)
    if not frames:
        raise ValueError("ani_bytes 至少要一帧")
    if delay_ms <= 0:
        raise ValueError("delay_ms 必须为正数，收到 %r" % (delay_ms,))
    for i, f in enumerate(frames):
        if len(f) < 6 or f[:4] != b"\x00\x00\x02\x00":
            raise ValueError("第 %d 帧不是 .cur 数据（应以 00 00 02 00 开头）" % i)

    jif = max(1, int(round(delay_ms / 1000.0 * 60)))
    n = len(frames)
    anih = struct.pack("<9I", 36, n, n, 0, 0, 0, 0, jif, 1)
    rate = b"".join(struct.pack("<I", jif) for _ in frames)
    seq = b"".join(struct.pack("<I", i) for i in range(n))
    icons = b"".join(_chunk(b"icon", f) for f in frames)
    fram = b"LIST" + struct.pack("<I", 4 + len(icons)) + b"fram" + icons
    body = _chunk(b"anih", anih) + _chunk(b"rate", rate) + _chunk(b"seq ", seq) + fram
    return b"RIFF" + struct.pack("<I", 4 + len(body)) + b"ACON" + body
