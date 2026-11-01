# -*- coding: utf-8 -*-
"""verify 模块自测：喂它坏文件，确认能报出来；喂好文件，确认不误报。"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image  # noqa: E402

from cursorlab import cartoon, verify  # noqa: E402
from cursorlab.encode import ani_bytes, cur_bytes  # noqa: E402


def _cur(size=32, hot=(2, 2)):
    return cur_bytes([Image.new("RGBA", (size, size), (0, 0, 0, 0))], hot)


def _ani(n=3):
    frame = _cur()
    return ani_bytes([frame] * n)


def _patch(data, off, fmt="<H", value=0):
    out = bytearray(data)
    struct.pack_into(fmt, out, off, value)
    return bytes(out)


def test_good_cur_and_ani_have_no_issues():
    assert verify.verify_cur(_cur()) == []
    assert verify.verify_cur(cur_bytes([Image.new("RGBA", (s, s)) for s in (16, 32, 48)], (0, 0))) == []
    assert verify.verify_ani(_ani()) == []


def test_dispatch_by_magic():
    assert verify.verify_bytes(_cur()) == []
    assert verify.verify_bytes(_ani()) == []


def test_short_file():
    assert verify.verify_cur(b"\x00\x00")
    assert verify.verify_ani(b"RIFF")


def test_bad_type_field():
    # 1 是 .ico；.cur 必须是 2
    data = _patch(_cur(), 2, "<H", 1)
    assert any("必须是 2" in m for m in verify.verify_cur(data))


def test_reserved_not_zero():
    data = _patch(_cur(), 0, "<H", 7)
    assert any("保留位" in m for m in verify.verify_cur(data))


def test_count_beyond_eof():
    # 目录头说 3 层，但文件只有 6 字节，装不下目录项
    data = b"\x00\x00\x02\x00" + struct.pack("<H", 3)
    assert any("目录声明" in m for m in verify.verify_cur(data))


def test_zero_layers():
    assert any("一张图都没有" in m for m in verify.verify_cur(_patch(_cur(), 4, "<H", 0)))


def test_layer_offset_out_of_range():
    data = bytearray(_cur())
    struct.pack_into("<I", data, 6 + 12, 10_000)          # 第 0 层偏移
    assert any("越界" in m for m in verify.verify_cur(bytes(data)))


def test_hotspot_outside_image():
    data = bytearray(_cur())
    struct.pack_into("<H", data, 6 + 4, 99)               # hotspot x
    assert any("热点" in m for m in verify.verify_cur(bytes(data)))


def test_dib_header_size():
    data = bytearray(_cur())
    off = struct.unpack_from("<I", data, 6 + 12)[0]
    struct.pack_into("<I", data, off, 12)                 # BITMAPCOREHEADER
    assert any("DIB 头长度" in m for m in verify.verify_cur(bytes(data)))


def test_dib_dimensions_mismatch():
    data = bytearray(_cur())
    off = struct.unpack_from("<I", data, 6 + 12)[0]
    struct.pack_into("<i", data, off + 8, 63)             # biHeight 应为 64
    assert any("不一致" in m for m in verify.verify_cur(bytes(data)))


def test_dib_bitcount_and_planes():
    data = bytearray(_cur())
    off = struct.unpack_from("<I", data, 6 + 12)[0]
    struct.pack_into("<H", data, off + 14, 24)
    assert any("biBitCount" in m for m in verify.verify_cur(bytes(data)))
    data2 = bytearray(_cur())
    struct.pack_into("<H", data2, off + 12, 2)
    assert any("biPlanes" in m for m in verify.verify_cur(bytes(data2)))


def test_dib_compression():
    data = bytearray(_cur())
    off = struct.unpack_from("<I", data, 6 + 12)[0]
    struct.pack_into("<I", data, off + 16, 3)             # BI_BITFIELDS
    assert any("压缩" in m for m in verify.verify_cur(bytes(data)))


def test_dib_size_image():
    data = bytearray(_cur())
    off = struct.unpack_from("<I", data, 6 + 12)[0]
    struct.pack_into("<I", data, off + 20, 1)
    assert any("biSizeImage" in m for m in verify.verify_cur(bytes(data)))


def test_overlapping_layers():
    data = bytearray(cur_bytes([Image.new("RGBA", (32, 32)) for _ in range(2)], (0, 0)))
    first_off = struct.unpack_from("<I", data, 6 + 12)[0]
    struct.pack_into("<I", data, 6 + 16 + 12, first_off)  # 第二层也指向第一层
    assert any("重叠" in m for m in verify.verify_cur(bytes(data)))


def test_ani_riff_size():
    data = _ani()
    assert any("RIFF 长度" in m for m in verify.verify_ani(data[:-1]))


def test_ani_type_not_acon():
    data = bytearray(_ani())
    data[8:12] = b"WAVE"
    assert any("ACON" in m for m in verify.verify_ani(bytes(data)))


def test_ani_frame_count_mismatch():
    data = bytearray(_ani(3))
    # 顶层第一个 chunk 是 anih（12 起），帧数在 payload +4
    struct.pack_into("<I", data, 12 + 8 + 4, 5)
    assert any("帧" in m for m in verify.verify_ani(bytes(data)))


def test_ani_seq_index_out_of_range():
    data = bytearray(_ani(2))
    text = bytes(data)
    pos = text.find(b"seq ")
    assert pos > 0
    struct.pack_into("<I", data, pos + 8, 9)
    assert any("seq[0]" in m for m in verify.verify_ani(bytes(data)))


def test_ani_missing_seq():
    frame = _cur()
    icons = b"icon" + struct.pack("<I", len(frame)) + frame
    fram = b"LIST" + struct.pack("<I", 4 + len(icons)) + b"fram" + icons
    anih = struct.pack("<9I", 36, 1, 1, 0, 0, 0, 0, 5, 1)
    body = b"anih" + struct.pack("<I", 36) + anih + fram
    data = b"RIFF" + struct.pack("<I", 4 + len(body)) + b"ACON" + body
    assert any("seq" in m for m in verify.verify_ani(data))


def test_ani_frame_not_cur():
    bad = b"\x00" * 8
    icons = b"icon" + struct.pack("<I", len(bad)) + bad
    fram = b"LIST" + struct.pack("<I", 4 + len(icons)) + b"fram" + icons
    anih = struct.pack("<9I", 36, 1, 1, 0, 0, 0, 0, 5, 1)
    rate = struct.pack("<I", 5)
    seq = struct.pack("<I", 0)
    body = (b"anih" + struct.pack("<I", 36) + anih
            + b"rate" + struct.pack("<I", 4) + rate
            + b"seq " + struct.pack("<I", 4) + seq + fram)
    data = b"RIFF" + struct.pack("<I", 4 + len(body)) + b"ACON" + body
    assert data is not None and data
    assert any("不是 .cur" in m for m in verify.verify_ani(data))


def test_verify_file_and_dir():
    from _runner import cleanup, tmpdir
    d = tmpdir()
    try:
        good = os.path.join(d, "arrow.cur")
        with open(good, "wb") as fh:
            fh.write(_cur())
        bad = os.path.join(d, "broken.cur")
        with open(bad, "wb") as fh:
            fh.write(_patch(_cur(), 2, "<H", 1))
        with open(os.path.join(d, "note.txt"), "w") as fh:
            fh.write("ignore me")
        assert verify.verify_file(good) == []
        problems = verify.verify_dir(d)
        assert list(problems) == ["broken.cur"], problems
    finally:
        cleanup(d)


def test_cli_exit_codes():
    from _runner import cleanup, tmpdir
    d = tmpdir()
    try:
        with open(os.path.join(d, "ok.cur"), "wb") as fh:
            fh.write(_cur())
        assert verify.main([d]) == 0
        with open(os.path.join(d, "bad.cur"), "wb") as fh:
            fh.write(_patch(_cur(), 2, "<H", 1))
        assert verify.main([d]) == 1
    finally:
        cleanup(d)


def test_all_cartoon_files_verify():
    """真跑一遍编码器产物：17 个角色两档尺寸，必须全部干净。"""
    for key in sorted(cartoon.SPRITES):
        data = cur_bytes([cartoon.render(key, s) for s in (32, 48)],
                         cartoon.SPRITES[key]["hot"])
        assert verify.verify_cur(data) == [], key


if __name__ == "__main__":
    from _runner import run
    sys.exit(run())
