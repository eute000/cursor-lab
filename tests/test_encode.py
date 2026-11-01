# -*- coding: utf-8 -*-
"""编码器自测：不装 Windows 也能验证 .cur / .ani 的二进制结构对不对。

跑法： python tests/test_encode.py
（也可以 pytest 直接收集）
"""

import io
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image  # noqa: E402

from cursorlab import cartoon  # noqa: E402
from cursorlab.encode import ani_bytes, cur_bytes, dib32  # noqa: E402


def _walk(data, off=0):
    """按 RIFF 规则遍历 chunk（块长度之后的 0 填充要跳过）。"""
    while off + 8 <= len(data):
        cid = data[off:off + 4]
        size = struct.unpack_from("<I", data, off + 4)[0]
        yield cid, data[off + 8:off + 8 + size]
        off += 8 + size + (size & 1)


def _chunks(data):
    """遍历 RIFF 顶层 chunk。"""
    return _walk(data, 12)


def test_cur_header():
    data = cur_bytes([cartoon.render("arrow", s) for s in (32, 64)], (3, 4))
    assert data[0:4] == b"\x00\x00\x02\x00", "CUR 魔数/类型位不对"
    assert struct.unpack_from("<H", data, 4)[0] == 2, "层数应为 2"


def test_cur_layers_and_hotspot():
    sizes = (32, 64)
    hot = (3.0, 4.0)
    data = cur_bytes([cartoon.render("arrow", s) for s in sizes], hot)
    for i, size in enumerate(sizes):
        w, h, _c, _r, hx, hy, n, off = struct.unpack_from("<BBBBHHII", data, 6 + 16 * i)
        assert (w, h) == (size, size)
        # 热点按比例缩放到每个尺寸
        assert (hx, hy) == (round(hot[0] / 32 * size), round(hot[1] / 32 * size))
        assert data[off:off + 4] == struct.pack("<I", 40), "必须是 BITMAPINFOHEADER（DIB）"
        bw, bh = struct.unpack_from("<ii", data, off + 4)
        assert (bw, bh) == (size, size * 2), "DIB 高度要把 AND 掩码算进去"
        assert struct.unpack_from("<H", data, off + 14)[0] == 32, "32bpp"
        assert n > 0 and off + n <= len(data)


def test_cur_decodable_by_pillow():
    data = cur_bytes([cartoon.render("hand", 32)], (16, 8))
    im = Image.open(io.BytesIO(data))
    im.load()
    assert im.size == (32, 32)


def test_ani_structure():
    frames = [cur_bytes([cartoon.render("wait", 32, f)], (16, 16)) for f in range(8)]
    data = ani_bytes(frames, delay_ms=90)
    assert data[:4] == b"RIFF" and data[8:12] == b"ACON"
    assert struct.unpack_from("<I", data, 4)[0] == len(data) - 8, "RIFF 长度字段不对"

    seen = {}
    for cid, payload in _chunks(data):
        seen[cid] = payload
    assert b"anih" in seen and b"rate" in seen and b"seq " in seen
    anih = struct.unpack("<9I", seen[b"anih"])
    assert anih[0] == 36 and anih[1] == 8 and anih[2] == 8, "anih: 大小/帧数/步数"
    assert anih[7] == 5, "90ms ≈ 5 jiffies(1/60s)"
    assert anih[8] == 1, "flags 应为 AF_ICON"

    fram = seen[b"LIST"]
    assert fram[:4] == b"fram"
    icons = [p for cid, p in _walk(fram, 4) if cid == b"icon"]
    assert len(icons) == 8, "帧数不对：%d" % len(icons)
    assert icons[0][:4] == b"\x00\x00\x02\x00", "帧必须是完整 .cur"


def test_all_sprites_render():
    for key in cartoon.SPRITES:
        for size in (32, 64):
            im = cartoon.render(key, size, 0)
            assert im.size == (size, size)
            assert im.mode == "RGBA"
            assert im.getbbox() is not None, "%s 是空图" % key


def test_dib_alpha_kept():
    im = cartoon.render("arrow", 32)
    blob = dib32(im)
    w = 32
    xor = blob[40:40 + w * w * 4]
    alphas = xor[3::4]
    assert min(alphas) == 0 and max(alphas) == 255, "alpha 通道没写进 DIB"


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS %s" % name)
            except AssertionError as exc:
                fails += 1
                print("FAIL %s: %s" % (name, exc))
    print("\n%d 个用例，%d 个失败" % (
        len([n for n in globals() if n.startswith("test_")]), fails))
    sys.exit(1 if fails else 0)
