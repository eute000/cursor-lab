# -*- coding: utf-8 -*-
"""编码器自测：不装 Windows 也能验证 .cur / .ani 的二进制结构对不对。

跑法： python tests/test_encode.py        # 跑 tests/ 下全部用例
       python -m pytest tests/            # 或者用 pytest
"""

import io
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image  # noqa: E402

from cursorlab import cartoon  # noqa: E402
from cursorlab.encode import (  # noqa: E402
    DESIGN, ROLES, ani_bytes, check_hotspot, cur_bytes, dib32,
)


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


def _solid(size, color=(20, 20, 20, 255)):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    im.paste(color, (0, 0, size, size))
    return im


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


# ---------------------------------------------------------------- 目录项
def test_cur_dir_entries_are_contiguous():
    data = cur_bytes([_solid(s) for s in (16, 32, 48)], (0, 0))
    count = struct.unpack_from("<H", data, 4)[0]
    off = 6 + 16 * count
    end = off
    for i in range(count):
        _w, _h, _c, _r, _hx, _hy, n, o = struct.unpack_from("<BBBBHHII", data, 6 + 16 * i)
        assert o == end, "第 %d 层偏移 %d 应紧接上一层的 %d" % (i, o, end)
        end += n
    assert end == len(data), "目录声明之外还有 %d 字节残留" % (len(data) - end)


def test_cur_256_size_written_as_zero():
    data = cur_bytes([_solid(256)], (16, 16))
    w, h, _c, _r, hx, hy, n, off = struct.unpack_from("<BBBBHHII", data, 6)
    assert (w, h) == (0, 0), "256 在目录项里必须写成 0"
    assert (hx, hy) == (128, 128), "热点按 256/32=8 倍放大"
    bw, bh = struct.unpack_from("<ii", data, off + 4)
    assert (bw, bh) == (256, 512), "DIB 里写真实尺寸 256x512"


def test_cur_hotspot_clamped_to_last_pixel():
    # 设计网格端点 32 换算到 32px 是 32，落在图像外，必须夹到 31
    data = cur_bytes([_solid(32)], (DESIGN, DESIGN))
    _w, _h, _c, _r, hx, hy, _n, _o = struct.unpack_from("<BBBBHHII", data, 6)
    assert (hx, hy) == (31, 31)


def test_cur_rejects_bad_hotspot():
    im = _solid(32)
    for bad in ((-1, 0), (0, 33), (float("nan"), 0), ("a", 1), (1, 2, 3), None):
        try:
            cur_bytes([im], bad)
        except ValueError:
            continue
        raise AssertionError("热点 %r 应该被拒绝" % (bad,))


def test_cur_rejects_no_images():
    try:
        cur_bytes([], (0, 0))
    except ValueError as exc:
        assert "至少" in str(exc)
    else:
        raise AssertionError("空图列表应该报错")


def test_check_hotspot_accepts_endpoints():
    assert check_hotspot((0, DESIGN)) == (0.0, DESIGN)
    assert check_hotspot([2.5, 7]) == (2.5, 7.0)


# ---------------------------------------------------------------- DIB
def test_dib_andmask_stride_aligned():
    w = 33                                   # 故意不是 32 的倍数
    im = Image.new("RGBA", (w, 7), (0, 0, 0, 0))
    im.putpixel((w - 1, 3), (255, 0, 0, 255))   # 只有一个不透明像素
    im.putpixel((0, 0), (0, 0, 0, 255))
    blob = dib32(im)
    stride = ((w + 31) // 32) * 4
    assert stride == 8, "stride 必须是 4 字节对齐的 8"
    assert len(blob) == 40 + w * 7 * 4 + stride * 7
    mask = blob[40 + w * 7 * 4:]
    assert len(mask) == stride * 7
    # DIB 自下而上：第 3 行（y=3）是倒数第 4 行
    row = mask[(7 - 1 - 3) * stride:(7 - 3) * stride]
    assert row[w // 8] & (0x80 >> (w % 8)) == 0, "不透明像素的 AND 位不该置 1"
    first = mask[(7 - 1) * stride:7 * stride]
    assert first[0] & 0x80 == 0


def test_dib_transparent_pixels_set_and_bit():
    im = Image.new("RGBA", (8, 2), (0, 0, 0, 0))
    blob = dib32(im)
    mask = blob[40 + 8 * 2 * 4:]
    stride = 4
    for row in range(2):
        assert mask[row * stride] == 0xFF, "全透明的行 AND 掩码应全是 1"
        assert mask[row * stride + 1:(row + 1) * stride] == b"\x00" * 3


def test_dib_rejects_oversize_and_empty():
    for size in (0, 257):
        try:
            dib32(Image.new("RGBA", (size, 4)))
        except ValueError:
            continue
        raise AssertionError("尺寸 %d 应该被拒绝" % size)


# ---------------------------------------------------------------- ANI
def test_ani_rejects_bad_input():
    good = cur_bytes([_solid(32)], (0, 0))
    for frames, delay in (([], 90), ([b"garbage"], 90), ([good], 0), ([good], -5)):
        try:
            ani_bytes(frames, delay)
        except ValueError:
            continue
        raise AssertionError("ani_bytes(%r, %r) 应该报错" % (frames, delay))


def test_ani_pads_odd_chunks():
    # 6 字节的假帧：奇数长度 + 1 字节填充，chunk 起点必须保持偶数对齐
    fake = b"\x00\x00\x02\x00\x01\x02"
    data = ani_bytes([fake])
    assert struct.unpack_from("<I", data, 4)[0] == len(data) - 8
    off = 12
    starts = []
    while off + 8 <= len(data):
        _cid = data[off:off + 4]
        size = struct.unpack_from("<I", data, off + 4)[0]
        starts.append(off)
        off += 8 + size + (size & 1)
    assert off == len(data), "chunk 列表没铺满文件"
    assert all(s % 2 == 0 for s in starts), "chunk 起点必须 2 字节对齐"


def test_ani_rate_tracks_delay():
    frame = cur_bytes([_solid(16)], (0, 0))
    for delay, jif in ((1000, 60), (90, 5), (33, 2), (1, 1)):
        seen = {cid: p for cid, p in _chunks(ani_bytes([frame], delay))}
        anih = struct.unpack("<9I", seen[b"anih"])
        assert anih[7] == jif, "%dms 应换算成 %d jiffies" % (delay, jif)
        assert struct.unpack("<I", seen[b"rate"][:4])[0] == jif


def test_roles_match_install_script():
    """编码器里的角色顺序必须和 install.ps1 的 $map 一致，否则装错指针。"""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "install.ps1"), encoding="utf-8-sig") as fh:
        text = fh.read()
    block = re.search(r"\$map = \[ordered\]@\{(.*?)\n\}", text, re.S)
    assert block, "install.ps1 里找不到 $map"
    names = re.findall(r"^\s*([A-Za-z]+)\s*=", block.group(1), re.M)
    assert names == ROLES, "install.ps1 的 $map 与 encode.ROLES 不一致：%r" % (names,)


if __name__ == "__main__":
    from _runner import run
    sys.exit(run())
