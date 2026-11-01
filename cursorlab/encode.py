# -*- coding: utf-8 -*-
"""
Cursor 文件编码器 —— 不依赖 Pillow 的 ICO 插件自己拼二进制。

要点（踩过的坑）：
  * .cur 里只能放 DIB 位图；Pillow 存大尺寸时会用 PNG 压缩，塞进 .cur 就是坏文件
  * 光标目录项里 planes / bitCount 两个字段被挪用存热点 (x, y)
  * .ani 是 RIFF/ACON：anih + rate + seq + LIST('fram') 里若干个 icon 块
"""

import struct

DESIGN = 32.0

# 注册表标准顺序（
ROLES = [
    "Arrow", "Help", "AppStarting", "Wait", "Crosshair", "IBeam", "NWPen",
    "No", "SizeNS", "SizeWE", "SizeNWSE", "SizeNESW", "SizeAll", "UpArrow",
    "Hand", "Pin", "Person",
]


def dib32(im):
    """32bpp DIB：高度写 2*h（上半 XOR 颜色，下半 AND 透明掩码）。"""
    w, h = im.size
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


def cur_bytes(images, hotspot):
    """images: 同一造型的多尺寸 PIL 图；hotspot: 设计网格(0..32) 坐标。"""
    entries, body = [], b""
    for im in images:
        blob = dib32(im)
        w, h = im.size
        hx = int(round(hotspot[0] / DESIGN * w))
        hy = int(round(hotspot[1] / DESIGN * h))
        entries.append((w, h, hx, hy, len(blob)))
        body += blob

    out = struct.pack("<HHH", 0, 2, len(entries))       # type=2 => cursor
    dirs, off = b"", 6 + 16 * len(entries)
    for (w, h, hx, hy, n) in entries:
        dirs += struct.pack("<BBBBHHII", w % 256, h % 256, 0, 0, hx, hy, n, off)
        off += n
    return out + dirs + body


def _chunk(cid, data):
    """RIFF chunk：块长度写原始长度，数据为奇数时补一个 0 对齐。"""
    pad = b"\x00" if len(data) & 1 else b""
    return cid + struct.pack("<I", len(data)) + data + pad


def ani_bytes(frames, delay_ms=90):
    """frames: 若干个 .cur 字节串。"""
    jif = max(1, int(round(delay_ms / 1000.0 * 60)))
    n = len(frames)
    anih = struct.pack("<9I", 36, n, n, 0, 0, 0, 0, jif, 1)
    rate = b"".join(struct.pack("<I", jif) for _ in frames)
    seq = b"".join(struct.pack("<I", i) for i in range(n))
    icons = b"".join(_chunk(b"icon", f) for f in frames)
    fram = b"LIST" + struct.pack("<I", 4 + len(icons)) + b"fram" + icons
    body = _chunk(b"anih", anih) + _chunk(b"rate", rate) + _chunk(b"seq ", seq) + fram
    return b"RIFF" + struct.pack("<I", 4 + len(body)) + b"ACON" + body
