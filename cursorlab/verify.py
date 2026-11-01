# -*- coding: utf-8 -*-
"""
结构体检：把 .cur / .ani 当字节读一遍，看 Windows 会不会认。

为什么单独写一个：编码器只负责"写出去"，写出坏文件时它自己是不知道的
（目录项长度算错、热点跑到图像外、RIFF 长度少 4 字节，全都照样返回 bytes）。
CI 里构建完跑一遍 verify，坏文件当场失败，而不是等装到 Windows 上
发现指针变成默认箭头。

用法：
    python -m cursorlab.verify out/cartoon-cat
    python -m cursorlab.verify out/cartoon-cat/arrow.ani
    python -m cursorlab.build --verify
"""

import argparse
import os
import struct
import sys

CUR_MAGIC = b"\x00\x00\x02\x00"


def _u16(data, off):
    return struct.unpack_from("<H", data, off)[0]


def _u32(data, off):
    return struct.unpack_from("<I", data, off)[0]


def verify_cur(data):
    """检查一个 .cur：目录项、DIB 头、热点、层长度。返回问题列表。"""
    bad = []
    if len(data) < 6:
        return ["文件太短（%d 字节），连目录头都不够" % len(data)]
    reserved, kind, count = struct.unpack_from("<HHH", data, 0)
    if reserved != 0:
        return ["保留位应为 0，实际 %d" % reserved]
    if kind != 2:
        return ["类型字段是 %d，.cur 必须是 2（1 是 .ico）" % kind]
    if count == 0:
        return ["一张图都没有（count=0）"]
    if 6 + 16 * count > len(data):
        return ["目录声明 %d 层，但文件只有 %d 字节" % (count, len(data))]

    spans = []
    for i in range(count):
        w, h, colors, reserved2, hx, hy, nbytes, off = struct.unpack_from(
            "<BBBBHHII", data, 6 + 16 * i)
        w = w or 256
        h = h or 256
        tag = "第 %d 层 %dx%d" % (i, w, h)
        if colors or reserved2:
            bad.append("%s: 颜色数/保留位应为 0，实际 %d/%d" % (tag, colors, reserved2))
        if nbytes == 0:
            bad.append("%s: 数据长度是 0" % tag)
            continue
        if off < 6 + 16 * count or off + nbytes > len(data):
            bad.append("%s: 数据区间 %d..%d 越界（文件 %d 字节）"
                       % (tag, off, off + nbytes, len(data)))
            continue
        spans.append((off, off + nbytes, tag))

        blob = data[off:off + nbytes]
        if len(blob) < 40:
            bad.append("%s: DIB 头不完整" % tag)
            continue
        hdr, bw, bh, planes, bpp, comp, size_img = struct.unpack_from("<IiiHHII", blob, 0)
        if hdr != 40:
            bad.append("%s: DIB 头长度 %d，应为 40（BITMAPINFOHEADER）" % (tag, hdr))
        if (bw, bh) != (w, h * 2):
            bad.append("%s: DIB 尺寸 %dx%d 与目录项 %dx%d 不一致（高度要含 AND 掩码）"
                       % (tag, bw, bh, w, h * 2))
        if planes != 1:
            bad.append("%s: biPlanes=%d，应为 1" % (tag, planes))
        if bpp != 32:
            bad.append("%s: biBitCount=%d，应为 32" % (tag, bpp))
        if comp != 0:
            bad.append("%s: 用了压缩（biCompression=%d），.cur 里必须是 BI_RGB"
                       % (tag, comp))
        stride = ((max(bw, 0) + 31) // 32) * 4
        rows = max(int(bh / 2), 0)          # biHeight 把 AND 掩码算进去了
        expect = max(bw, 0) * rows * 4 + stride * rows
        if size_img != expect:
            bad.append("%s: biSizeImage=%d，按像素算应为 %d" % (tag, size_img, expect))
        if 40 + size_img > nbytes:
            bad.append("%s: 目录项长度 %d 装不下 %d 字节位图"
                       % (tag, nbytes, 40 + size_img))
        if not 0 <= hx < w or not 0 <= hy < h:
            bad.append("%s: 热点 (%d,%d) 落在图像外" % (tag, hx, hy))

    spans.sort()
    for (a0, a1, atag), (b0, _b1, btag) in zip(spans, spans[1:]):
        if b0 < a1:
            bad.append("%s 与 %s 的数据区间重叠" % (atag, btag))
    return bad


def _riff_chunks(data, start, end):
    """按 RIFF 规则遍历 chunk：id + 长度 + 数据 + 奇数长度补 1 字节。"""
    off = start
    while off + 8 <= end:
        cid = data[off:off + 4]
        size = _u32(data, off + 4)
        body_start = off + 8
        if body_start + size > end:
            raise ValueError("chunk %r 声明 %d 字节，超出容器" % (cid, size))
        yield cid, data[body_start:body_start + size], body_start
        off = body_start + size + (size & 1)
    if off != end:
        raise ValueError("chunk 列表没有正好铺满容器（余 %d 字节）" % (end - off))


def verify_ani(data):
    """检查一个 .ani：RIFF 头、anih 计数、rate/seq、LIST('fram') 里的帧。"""
    bad = []
    if len(data) < 12:
        return ["文件太短（%d 字节）" % len(data)]
    if data[:4] != b"RIFF":
        return ["不是 RIFF 容器（开头是 %r）" % data[:4]]
    if data[8:12] != b"ACON":
        return ["RIFF 类型是 %r，.ani 必须是 ACON" % data[8:12]]
    riff = _u32(data, 4)
    if riff + 8 != len(data):
        bad.append("RIFF 长度字段 %d 与实际 %d 不符" % (riff, len(data) - 8))
    end = min(len(data), riff + 8) if riff + 8 > 12 else len(data)
    try:
        chunks = list(_riff_chunks(data, 12, end))
    except ValueError as exc:
        return bad + [str(exc)]

    seen = {}
    icons = []
    for cid, body, _off in chunks:
        if cid == b"LIST":
            if body[:4] != b"fram":
                bad.append("LIST 块类型是 %r，只认 'fram'" % body[:4])
                continue
            try:
                for icid, ibody, _ioff in _riff_chunks(body, 4, len(body)):
                    if icid != b"icon":
                        bad.append("LIST('fram') 里有 %r，只认 'icon'" % icid)
                    else:
                        icons.append(ibody)
            except ValueError as exc:
                bad.append("LIST('fram'): %s" % exc)
        else:
            seen[cid] = body

    anih = seen.get(b"anih")
    if anih is None:
        bad.append("缺 anih 块")
    elif len(anih) != 36:
        bad.append("anih 长度 %d，应为 36" % len(anih))
    else:
        (cb, nframes, nsteps, _w, _h, _bpp, _planes, rate, flags) = struct.unpack("<9I", anih)
        if cb != 36:
            bad.append("anih.cbSize=%d，应为 36" % cb)
        if nframes != len(icons):
            bad.append("anih 声明 %d 帧，实际装了 %d 帧" % (nframes, len(icons)))
        if nsteps != nframes:
            bad.append("anih 步数 %d 与帧数 %d 不一致" % (nsteps, nframes))
        if nsteps and rate == 0:
            bad.append("anih.iDispRate=0，动画不会动")
        if not flags & 1:
            bad.append("anih.bfAttributes 没置 AF_ICON(1)")
        seq = seen.get(b"seq ")
        if seq is None:
            bad.append("缺 seq 块")
        else:
            if len(seq) % 4:
                bad.append("seq 长度 %d 不是 4 的倍数" % len(seq))
            idx = [struct.unpack_from("<I", seq, i)[0] for i in range(0, len(seq), 4)]
            if len(idx) != nsteps:
                bad.append("seq 有 %d 项，anih 说 %d 步" % (len(idx), nsteps))
            for j, v in enumerate(idx):
                if v >= nframes:
                    bad.append("seq[%d]=%d 超过帧数 %d" % (j, v, nframes))
        rt = seen.get(b"rate")
        if rt is not None:
            if len(rt) % 4:
                bad.append("rate 长度 %d 不是 4 的倍数" % len(rt))
            elif nsteps and len(rt) // 4 != nsteps:
                bad.append("rate 有 %d 项，应为 %d 项" % (len(rt) // 4, nsteps))

    if not icons:
        bad.append("没有帧")
    for i, f in enumerate(icons):
        if f[:4] != CUR_MAGIC:
            bad.append("第 %d 帧不是 .cur 数据（开头 %r）" % (i, f[:4]))
    return bad


def verify_bytes(data):
    """按内容判断是 .cur 还是 .ani 再校验。"""
    if data[:4] == b"RIFF":
        return verify_ani(data)
    return verify_cur(data)


def verify_file(path):
    with open(path, "rb") as fh:
        return verify_bytes(fh.read())


def verify_dir(path):
    """校验目录下所有 .cur/.ani，返回 {文件名: [问题]}（没问题的文件不出现）。"""
    problems = {}
    for name in sorted(os.listdir(path)):
        if not name.lower().endswith((".cur", ".ani")):
            continue
        msgs = verify_file(os.path.join(path, name))
        if msgs:
            problems[name] = msgs
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description="校验 .cur / .ani 结构")
    ap.add_argument("paths", nargs="+", help="文件或目录")
    args = ap.parse_args(argv)

    total = 0
    checked = 0
    for path in args.paths:
        if os.path.isdir(path):
            problems = verify_dir(path)
            files = [n for n in sorted(os.listdir(path))
                     if n.lower().endswith((".cur", ".ani"))]
            checked += len(files)
            for fn in files:
                for msg in problems.get(fn, []):
                    print("FAIL %s: %s" % (os.path.join(path, fn), msg))
            total += sum(len(m) for m in problems.values())
        else:
            checked += 1
            for msg in verify_file(path):
                print("FAIL %s: %s" % (path, msg))
                total += 1
    if total:
        print("%d 项检查，%d 个问题" % (checked, total))
        return 1
    print("%d 项检查，全部通过" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
