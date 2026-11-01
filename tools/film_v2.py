# -*- coding: utf-8 -*-
"""
銆婁竴鍙尗銆嬪叏鐗?v2锛堝畾绋跨増锛夆€斺€?44 闀?/ 126.9 绉?/ 1920脳1080 / 30fps / 鏃犳梺鐧?

缁熶竴瑙勮寖锛?
  * 鐚細鐢ㄦ埛璁ゅ彲鐨?鏈夎壊鐗?锛堟殩妫曟弿杈?濂舵补鐪?绮夐蓟锛宨mage-ae62bcf8锛夛紝
    缁熶竴璋冭壊 = 鍙充晶纭厜鍘嬫殫 + bloom 婧㈠厜 + 鏆楄锛坒rame105g 閭ｅ锛?
  * 鎺掔増锛氬乏涓婃爣棰樺潡锛堜腑鏂?+ 鑻辨枃鏂滀綋 + 缁嗙嚎锛? 椤堕儴杩涘害绾?+ 鍙充笂瑙掓爣 + 搴曢儴涓嫳瀛楀箷
  * 瀛椾綋锛氫腑鏂?Noto Sans SC / 鑻辨枃 Bodoni 鏂滀綋
  * 鑺傚锛氭瘡闀?4 鎷?鈮?2.14 绉掞紙浜у搧娈?4.28 / 鐜舰 6.4锛夛紝鍖€閫熸帹杩?
  * 闊充箰锛氱敤鎴锋彁渚涚殑 BGM锛?12.3 BPM锛夛紝鍏抽敭澶?whoosh / impact

鐢ㄦ硶锛歱ython tools/film_v2.py [璧风偣绉抅 [缁堢偣绉抅
浜х墿锛欵:\deepseek\.tmp\vibe\film_v2.mp4
"""
import math
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cursorlab import cartoon  # noqa: E402

W, H, FPS = 1920, 1080, 30
WORK = r"E:\deepseek\.tmp\vibe"
FF = r"D:\python\huanjing\ffmpeg.exe"
F_CN = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"
F_EN_I = r"C:\Windows\Fonts\BOD_I.TTF"
F_EN = r"C:\Windows\Fonts\BOD_R.TTF"
F_MONO = r"C:\Windows\Fonts\consola.ttf"
CAT_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "cat-source.png")
TOTAL = 126.9

INK = (252, 251, 249)
WARM = (234, 218, 202)
G2 = (150, 146, 140)
G3 = (116, 112, 106)
ACC = (240, 150, 120)

BM = np.load(os.path.join(WORK, "beatmap.npz"))
BEATS, STRENGTH = BM["beats"], BM["strength"]


_FONT_CACHE = {}


def f(p, s):
    key = (p, s)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(p, s)
    return _FONT_CACHE[key]


# ---------------------------------------------------------------- 鑳屾櫙
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
_d = np.sqrt(((xx - W * 0.5) / (W * 0.66)) ** 2 + ((yy - H * 0.46) / (H * 0.66)) ** 2)
_bg = (np.clip(1 - _d, 0, 1) ** 2.8)[:, :, None] * np.array([18, 18, 22], dtype=np.float32)
BG = Image.fromarray(np.clip(_bg, 0, 255).astype(np.uint8), "RGB")


# ---------------------------------------------------------------- 鐚紙缁熶竴璋冭壊锛?
def treat_cat(px=1200):
    im = Image.open(CAT_SRC).convert("RGB")
    im = im.resize((px, int(im.height * px / im.width)), Image.LANCZOS)
    arr = np.asarray(im, dtype=np.float32)
    w = arr.shape[1]
    xs = np.arange(w, dtype=np.float32)[None, :]
    t = np.clip((xs / w - 0.72) / 0.28, 0, 1)
    arr *= (1 - 0.55 * (t ** 1.6))[:, :, None]
    lum = arr.max(axis=2)
    bright = np.clip((lum - 120) / 135, 0, 1)[:, :, None] * arr
    bloom = Image.fromarray(np.clip(bright, 0, 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(30))
    arr = np.clip(arr + np.asarray(bloom, dtype=np.float32) * 0.55, 0, 255)

    # 鏆楅儴鍘嬮浂锛堣儗鏅伆鍧楁秷澶憋級+ 涓績妞渾缇藉寲锛堝洓鍛ㄦ贰鍑哄埌閫忔槑锛?
    arr[np.max(arr, axis=2) < 46] = 0
    hh, ww = arr.shape[:2]
    gy, gx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    rr = np.sqrt(((gx - ww / 2) / (ww * 0.52)) ** 2 + ((gy - hh / 2) / (hh * 0.52)) ** 2)
    alpha = np.clip((1.0 - rr) / 0.22, 0, 1)[:, :, None]
    rgba = np.concatenate([arr, alpha * 255.0], axis=2).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


CAT = treat_cat()
CAT_SMALL = CAT.resize((CAT.width // 2, CAT.height // 2), Image.LANCZOS)


_CAT_CACHE = {}


def put_cat(img, scale=1.0, cy=None, cx=None, alpha=255, blur=0.0):
    if scale <= 0.03:
        return
    qs = round(scale * 50) / 50
    key = (qs, blur, alpha // 16)
    if key not in _CAT_CACHE:
        c0 = CAT if scale >= 0.9 else CAT_SMALL
        sz = int(c0.width * (scale if scale >= 0.9 else scale * 2))
        c0 = c0.resize((sz, int(c0.height * sz / c0.width)), Image.LANCZOS)
        if blur:
            c0 = c0.filter(ImageFilter.GaussianBlur(blur))
        _CAT_CACHE[key] = c0
    c = _CAT_CACHE[key]
    if alpha < 255:
        k2 = (qs, blur, alpha // 16, "a")
        if k2 not in _CAT_CACHE:
            c2 = c.copy()
            c2.putalpha(c2.split()[3].point(lambda v: int(v * alpha / 255)))
            _CAT_CACHE[k2] = c2
        c = _CAT_CACHE[k2]
    x = (W - c.width) // 2 if cx is None else cx
    y = (H * 0.42 - c.height / 2) if cy is None else cy
    img.alpha_composite(c, (int(x), int(y)))


_ART_CACHE = {}


def cur_render(name, px, press=False):
    key = (name + ("_press" if press else ""), px)
    if key not in _ART_CACHE:
        _ART_CACHE[key] = cartoon.render(key[0], px)
    return _ART_CACHE[key]


_ARROW_MASTER = {}


def arrow_img(px=420, press=False):
    # 鍏堟覆鏌撲竴寮?640 鐨勪富鍥撅紝閫愬抚鍙仛 resize锛堝惁鍒欒繛缁彉鍖栫殑 px 浼氭瘡甯ч噸娓叉煋锛?
    key = press
    if key not in _ARROW_MASTER:
        _ARROW_MASTER[key] = cartoon.render("arrow_press" if press else "arrow", 640)
    return _ARROW_MASTER[key].resize((int(px), int(px)), Image.LANCZOS)



def plain_arrow(px):
    """缁忓吀绯荤粺鎸囬拡锛堢櫧闈?+ 缁嗘弿杈癸級锛屼笉甯﹀ご鍍忕尗"""
    base = 512
    im = Image.new("RGBA", (base, base), (0, 0, 0, 0))
    pts = [(150, 88), (150, 356), (222, 286), (286, 408), (338, 382),
           (274, 262), (356, 262)]
    sh = Image.new("RGBA", (base, base), (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon([(x + 6, y + 12) for x, y in pts], fill=(0, 0, 0, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    ImageDraw.Draw(im).polygon(pts, fill=(246, 246, 250, 255))
    ImageDraw.Draw(im).line(pts + [pts[0]], fill=(14, 14, 18, 200), width=5, joint="curve")
    return im.resize((px, px), Image.LANCZOS)


_PLAIN = {}


def plain(px):
    k = int(px)
    if k not in _PLAIN:
        _PLAIN[k] = plain_arrow(k)
    return _PLAIN[k]


# ---------------------------------------------------------------- 鎺掔増
def typo(img, t, cn="", en="", act=None, big=False, sub_y=None):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if act:
        d.text((96, 74), act[0], font=f(F_CN, 38), fill=WARM + (228,))
        d.text((96, 128), act[1], font=f(F_EN_I, 28), fill=G3 + (212,))
        d.line([(96, 176), (330, 176)], fill=(150, 143, 133, 110), width=1)
        d.line([(96, 194), (W - 300, 194)], fill=(80, 78, 74, 85), width=1)
        d.line([(96, 194), (96 + int((W - 396) * min(1.0, t / TOTAL)), 194)],
               fill=(228, 212, 196, 120), width=1)
        d.text((W - 300, 78), "CURSORLAB", font=f(F_EN, 23), fill=G3 + (170,))
        d.text((W - 300, 112), "%02d / 06" % act[2], font=f(F_EN, 21), fill=G3 + (120,))

    if cn:
        size = 78 if big else 64
        fc = f(F_CN, size)
        mw = d.textlength(cn, font=fc)
        y = sub_y if sub_y is not None else (H * 0.50 if big else H - 150)
        d.text(((W - mw) / 2, y), cn, font=fc, fill=INK + (255,))
        if en:
            fe = f(F_EN_I, int(size * 0.46))
            ew = sum(d.textlength(c, font=fe) + 4 for c in en)
            sx = (W - ew) / 2
            for ch in en:
                d.text((sx, y + size + 14), ch, font=fe, fill=(214, 200, 188) + (215,))
                sx += d.textlength(ch, font=fe) + 4
    img.alpha_composite(layer)


def mono_center(img, lines, y0, size=26, color=G3, alpha=150, lh=34):
    d = ImageDraw.Draw(img)
    for i, ln in enumerate(lines):
        w = d.textlength(ln, font=f(F_MONO, size))
        d.text(((W - w) / 2, y0 + i * lh), ln, font=f(F_MONO, size), fill=color + (alpha,))


_dv = np.sqrt(((xx - W * 0.5) / (W * 0.62)) ** 2 + ((yy - H * 0.46) / (H * 0.62)) ** 2)
VIG = np.clip(1.05 - _dv * 0.45, 0.45, 1.0).astype(np.float32)[:, :, None]
NOISE = [np.random.default_rng(k).normal(0, 1.9, (H, W, 1)).astype(np.float32)
         for k in range(16)]


def grain_and_vignette(img, seed, amt=1.9):
    a = np.asarray(img.convert("RGB"), dtype=np.float32)
    a *= VIG
    a += NOISE[seed % 16]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


# ---------------------------------------------------------------- 闀滃ご瀹炵幇
def s_arrow_in(img, lt, dur):
    k = min(1.0, lt / 1.0)
    art = plain(430)
    a = int(240 * k)
    art = art.copy()
    art.putalpha(art.split()[3].point(lambda v: int(v * a / 255)))
    glow = art.filter(ImageFilter.GaussianBlur(22))
    img.alpha_composite(glow, (W // 2 - 215, int(H * 0.40) - 215))
    img.alpha_composite(art, (W // 2 - 215, int(H * 0.40) - 215))


def s_arrow_close(img, lt, dur):
    k = min(1.0, lt / (dur * 0.9))
    sc = 1.0 + 0.06 * k
    art = plain(int(560 * sc))
    img.alpha_composite(art, (W // 2 - art.width // 2, int(H * 0.42) - art.height // 2))


def s_sysrow(img, lt, dur):
    d = ImageDraw.Draw(img)
    def _hour(d, cx, cy, sz=70, col=(235, 233, 230, 225)):
        d.line([(cx - sz * 0.55, cy - sz * 0.8), (cx + sz * 0.55, cy - sz * 0.8)], fill=col, width=6)
        d.line([(cx - sz * 0.55, cy + sz * 0.8), (cx + sz * 0.55, cy + sz * 0.8)], fill=col, width=6)
        d.line([(cx - sz * 0.45, cy - sz * 0.72), (cx, cy), (cx + sz * 0.45, cy - sz * 0.72)], fill=col, width=6)
        d.line([(cx - sz * 0.45, cy + sz * 0.72), (cx, cy), (cx + sz * 0.45, cy + sz * 0.72)], fill=col, width=6)

    def _ibeam(d, cx, cy, sz=70, col=(235, 233, 230, 225)):
        d.line([(cx, cy - sz), (cx, cy + sz)], fill=col, width=8)
        d.line([(cx - sz * 0.42, cy - sz), (cx + sz * 0.42, cy - sz)], fill=col, width=6)
        d.line([(cx - sz * 0.42, cy + sz), (cx + sz * 0.42, cy + sz)], fill=col, width=6)

    def _hand(d, cx, cy, sz=70, col=(235, 233, 230, 225)):
        d.line([(cx - sz * 0.5, cy + sz * 0.5), (cx - sz * 0.5, cy - sz * 0.2)], fill=col, width=8)
        for i in range(3):
            x = cx - sz * 0.5 + i * sz * 0.34
            d.line([(x, cy + sz * 0.55), (x, cy - sz * 0.55 - i * sz * 0.1)], fill=col, width=8)

    def _cross(d, cx, cy, sz=70, col=(235, 233, 230, 225)):
        d.line([(cx - sz, cy), (cx + sz, cy)], fill=col, width=6)
        d.line([(cx, cy - sz), (cx, cy + sz)], fill=col, width=6)
        d.ellipse([cx - sz * 0.34, cy - sz * 0.34, cx + sz * 0.34, cy + sz * 0.34],
                  outline=col, width=4)

    base_y = H * 0.40
    for i, kind in enumerate(["arrow", "hour", "ibeam", "cross"]):
        x = int(W * 0.18 + i * 380 + math.sin(lt * 0.9 + i) * 6)
        cx, cy = x + 70, int(base_y + 66)
        if kind == "arrow":
            img.alpha_composite(plain(150), (x, int(base_y) - 4))
        elif kind == "hour":
            _hour(d, cx, cy)
        elif kind == "ibeam":
            _ibeam(d, cx, cy)
        elif kind == "hand":
            _hand(d, cx, cy)
        else:
            _cross(d, cx, cy)
    d.line([(W * 0.14, H * 0.66), (W * 0.86, H * 0.66)], fill=(120, 116, 110, 60), width=1)


def s_dim(img, lt, dur):
    k = min(1.0, lt / 1.2)
    art = plain(300)
    a = art.copy()
    a.putalpha(a.split()[3].point(lambda v: int(v * (0.35 + 0.5 * (1 - k)))))
    img.alpha_composite(a, (W // 2 - 150, int(H * 0.42) - 150))


P_CAT_SRC = None
P_A = P_C = P_DELAY = P_JIT = None


def _init_morph():
    global P_A, P_C, P_DELAY, P_JIT
    if P_A is not None:
        return
    def sample(im, n, seed):
        arr = np.asarray(im.split()[3])
        ys, xs = np.nonzero(arr > 128)
        idx = np.random.default_rng(seed).integers(0, len(xs), n)
        return np.stack([xs[idx], ys[idx]], axis=1).astype(np.float32)

    a = plain(720)
    c = CAT.resize((720, int(CAT.height * 720 / CAT.width)), Image.LANCZOS)
    P_A = sample(a, 2600, 7) + np.array([W / 2 - 360, H * 0.44 - 360], dtype=np.float32)
    P_C = sample(c, 2600, 9) + np.array([W / 2 - 360, H * 0.44 - 360], dtype=np.float32)
    r = np.random.default_rng(21)
    P_DELAY = r.uniform(0, 0.5, 2600)
    P_JIT = r.normal(0, 1, (2600, 2)).astype(np.float32)


def s_morph(img, lt, dur):
    _init_morph()
    d = ImageDraw.Draw(img)
    k = float(np.clip((lt - 1.2) / (dur - 2.2), 0, 1))
    if k <= 0.01:
        art = plain(380)
        img.alpha_composite(art, (W // 2 - 190, int(H * 0.42) - 190))
        return
    e = 1 - (1 - np.clip((k - P_DELAY * 0.5) / 0.9, 0, 1)) ** 3
    burst = math.sin(math.pi * k) ** 0.8
    pts = P_A * (1 - e[:, None]) + P_C * e[:, None]
    pts = pts + P_JIT * (18 + 40 * burst) * (1 - e[:, None])
    col = (238, 236, 232, int(225 * (1 - 0.3 * burst)))
    for i in range(2600):
        x, y = pts[i]
        d.point((x, y), fill=col)
    if k > 0.97:
        pass


def s_cat_in(img, lt, dur):
    k = min(1.0, lt / 1.4)
    put_cat(img, 0.72, cy=int(H * 0.40 - 240), alpha=int(255 * k))


def s_title(img, lt, dur):
    put_cat(img, 0.30, cy=int(H * 0.30))


def s_ref(img, lt, dur):
    k = min(1.0, lt / 1.2)
    put_cat(img, 0.62 + 0.05 * k, cy=int(H * 0.36))


def s_words(img, lt, dur):
    words = ["澶х溂鐫?, "閫氫綋婕嗛粦", "鐚埅"]
    d = ImageDraw.Draw(img)
    for i, w in enumerate(words):
        t0 = i * 0.55
        if lt < t0:
            continue
        kk = min(1.0, (lt - t0) / 0.5)
        a = int(235 * kk)
        fc = f(F_CN, 64)
        ww = d.textlength(w, font=fc)
        d.text((W / 2 - ww / 2, H * 0.34 + i * 110), w, font=fc, fill=INK + (a,))


def s_version(img, lt, dur, idx):
    k = min(1.0, lt / 1.0)
    d = ImageDraw.Draw(img)
    # 涓変釜"鐗堟湰鍗?鐨勪綅缃殢 idx 楂樹寒
    for i in range(4):
        x = W * 0.14 + i * (W * 0.18)
        y = H * 0.34
        on = (i == idx)
        a = int((150 if on else 60) * k)
        d.rounded_rectangle([x, y, x + 260, y + 260], radius=18,
                            outline=(220, 210, 198, a), width=2)
        d.text((x + 18, y + 16), "V%d" % (i + 1), font=f(F_MONO, 26), fill=G3 + (a + 40,))
        if i <= idx:
            mark = "OK" if i == idx else "X"
            col = (200, 232, 190, a) if i == idx else (230, 150, 140, a)
            d.text((x + 96, y + 104), mark, font=f(F_EN, 64), fill=col)


def s_closeup(img, lt, dur):
    sc = 0.56 + 0.06 * min(1.0, lt / dur)
    put_cat(img, sc, cy=int(H * 0.36))


def s_line(img, lt, dur):
    pass


def s_cmd(img, lt, dur):
    d = ImageDraw.Draw(img)
    box = [W * 0.18, H * 0.32, W * 0.82, H * 0.60]
    d.rounded_rectangle(box, radius=16, fill=(10, 10, 12, 235), outline=(90, 86, 80, 160), width=1)
    text = "> 鎴戞兂瑕佷竴鍙粦鐚紝澶х溂鐫涳紝鍙埍涓€鐐?
    n = int(min(len(text), lt / dur * len(text) * 1.05))
    d.text((box[0] + 34, box[1] + 40), text[:n], font=f(F_CN, 34), fill=(220, 224, 210, 235))
    if n >= len(text):
        d.text((box[0] + 34, box[1] + 106), "鉁?鏀跺埌锛屾垜鍋氫竴鐗堢粰浣犵湅",
               font=f(F_CN, 30), fill=(150, 210, 160, 220))


def s_code(img, lt, dur):
    d = ImageDraw.Draw(img)
    lines = ["def draw_cat(r, iris, rim):",
             "    for eye in (left, right):",
             "        canvas.ellipse(eye, cream)",
             "        canvas.ellipse(pupil, iris)",
             "    return canvas.build()"]
    n = int(min(len(lines), (lt / dur) * (len(lines) + 1)))
    for i in range(n):
        d.text((W * 0.20, H * 0.34 + i * 52), lines[i], font=f(F_MONO, 30),
               fill=(180, 200, 185, 210))


def s_split17(img, lt, dur):
    d = ImageDraw.Draw(img)
    k = min(1.0, lt / (dur * 0.9))
    d.rectangle([W / 2 - 150, H * 0.20, W / 2 + 150, H * 0.44],
                outline=(200, 190, 180, 200), width=2)
    roles = ["arrow", "ibeam", "hand", "wait", "help"]
    for i, r in enumerate(roles):
        art = cur_render(r, 90)
        a = art.copy()
        alpha = int(220 * min(1.0, max(0.0, k * 5 - i)))
        a.putalpha(a.split()[3].point(lambda v: int(v * alpha / 255)))
        img.alpha_composite(a, (int(W * 0.16 + i * 300), int(H * 0.56)))


def s_grid17(img, lt, dur):
    roles = ["arrow", "help", "wait", "appstarting", "crosshair", "ibeam", "nwpen", "no",
             "sizeall", "sizens", "sizewe", "sizenwse", "sizenesw", "uparrow", "hand",
             "pin", "person"]
    cols, cell, pad = 6, 150, 18
    b = np.searchsorted(BEATS, lt)
    for i, r in enumerate(roles):
        appear = (i + 1) * 0.06
        if lt < appear:
            continue
        row, col = divmod(i, cols)
        x = W / 2 - (cols * cell + (cols - 1) * pad) / 2 + col * (cell + pad)
        y = H * 0.28 + row * (cell + pad)
        art = cur_render(r, 130)
        a = art.copy()
        kk = min(1.0, (lt - appear) / 0.3)
        a.putalpha(a.split()[3].point(lambda v: int(v * 235 * kk / 255)))
        img.alpha_composite(a, (int(x + 10), int(y + 10)))


def s_sizes(img, lt, dur):
    d = ImageDraw.Draw(img)
    for i, (sz, lbl, dly) in enumerate(((300, "64 px", 0.2), (210, "48 px", 0.9), (140, "32 px", 1.6))):
        k = min(1.0, max(0.0, (lt - dly) / 0.7))
        if k <= 0:
            continue
        box = [W / 2 - sz / 2 + i * 44, H * 0.36 - sz / 2 + i * 40,
               W / 2 + sz / 2 + i * 44, H * 0.36 + sz / 2 + i * 40]
        d.rectangle(box, outline=(210, 200, 190, int(170 * k)), width=2)
        d.text((box[0] + 10, box[1] + 8), lbl, font=f(F_MONO, 24), fill=G3 + (int(210 * k),))


def s_hotspot(img, lt, dur):
    d = ImageDraw.Draw(img)
    cx, cy = W / 2 - 120, H * 0.38 - 100
    d.rectangle([W / 2 - 170, H * 0.38 - 150, W / 2 + 170, H * 0.38 + 150],
                outline=(200, 190, 180, 150), width=2)
    if lt > 0.5:
        r = 8 + 5 * math.exp(-((lt - 0.5) % 0.53) / 0.2)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(240, 170, 140, 235))
        d.line([(cx, cy), (cx + 210, cy - 90)], fill=(180, 172, 162, 150), width=1)
        d.text((cx + 220, cy - 108), "hotspot (2, 2)", font=f(F_MONO, 28), fill=G2 + (210,))


def s_press3(img, lt, dur):
    seg = dur / 3
    i = min(2, int(lt / seg))
    names = ["arrow_press", "ibeam_press", "hand_press"]
    labels = ["鎸変綇锛氱湳鐪兼敹鐖?, "鎵撳瓧锛氱瑪鐢诲彉绮?, "鐐归摼鎺ワ細鐖嵃鎻＄揣"]
    art = cur_render(names[i], 420)
    img.alpha_composite(art, (W // 2 - art.width // 2, int(H * 0.38) - art.height // 2))
    d = ImageDraw.Draw(img)
    w = d.textlength(labels[i], font=f(F_CN, 34))
    d.text(((W - w) / 2, H * 0.62), labels[i], font=f(F_CN, 34), fill=G2 + (220,))


def s_onecmd(img, lt, dur):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([W * 0.16, H * 0.34, W * 0.84, H * 0.58], radius=14,
                        fill=(10, 10, 12, 235), outline=(90, 86, 80, 160), width=1)
    d.text((W * 0.16 + 32, H * 0.34 + 34), "> python -m cursorlab.build",
           font=f(F_MONO, 34), fill=(160, 220, 170, 235))
    if lt > 0.7:
        d.text((W * 0.16 + 32, H * 0.34 + 96), "cartoon-cat   44 files   1.3 MB",
               font=f(F_MONO, 28), fill=(180, 176, 170, 220))


def s_install(img, lt, dur):
    d = ImageDraw.Draw(img)
    rows = ["榧犳爣璁剧疆 鈥?鎸囬拡", "鏂规锛欳artoon Cat", "搴旂敤 鉁?]
    for i, r in enumerate(rows):
        if lt < i * 0.4:
            continue
        a = int(220 * min(1.0, (lt - i * 0.4) / 0.4))
        d.text((W * 0.26, H * 0.36 + i * 74), r, font=f(F_CN, 40), fill=INK + (a,))


def s_tray(img, lt, dur):
    d = ImageDraw.Draw(img)
    art = cur_render("person", 220)
    img.alpha_composite(art, (W - 420, H - 320))
    if lt > 0.5:
        d.text((W - 640, H - 300), "鎵樼洏甯搁┗ 路 鏃犵獥鍙?, font=f(F_CN, 32), fill=G2 + (210,))


def s_repo(img, lt, dur):
    d = ImageDraw.Draw(img)
    lines = ["repo   eute000/cursor-lab", "tag    v2.1.0", "site   eute000.github.io/cursor-lab"]
    for i, ln in enumerate(lines):
        if lt < i * 0.45:
            continue
        a = int(220 * min(1.0, (lt - i * 0.45) / 0.4))
        d.text((W * 0.22, H * 0.34 + i * 66), ln, font=f(F_MONO, 32), fill=G2 + (a,))


def s_submit(img, lt, dur):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([W * 0.26, H * 0.36, W * 0.74, H * 0.52], radius=12,
                        outline=(200, 190, 180, 150), width=2)
    d.text((W * 0.28, H * 0.39), "Set submitted for review.", font=f(F_MONO, 30),
           fill=(190, 210, 190, 225))


def s_bridge(img, lt, dur):
    pass


# --- 鐜舰鐩稿唽锛堝鐢?seg6 閫昏緫锛岀畝鍖栵級
RING_ROLES = ["arrow", "help", "wait", "appstarting", "crosshair", "ibeam", "nwpen", "no",
              "sizeall", "sizens", "sizewe", "sizenwse", "sizenesw", "uparrow", "hand",
              "pin", "person"]
RING_ART = [cur_render(r, 150) for r in RING_ROLES]


def s_ring(img, lt, dur, speed=1.0):
    d = ImageDraw.Draw(img)
    cx, cy, R = W * 0.5, H * 0.47, 560
    reveal = float(np.clip((lt - 0.2) / 0.9, 0, 1))
    ease = 1 - (1 - reveal) ** 3
    spin = (26 * lt + 90 * ease) * speed
    items = []
    for i, art in enumerate(RING_ART):
        th = math.radians(spin + i * (360 / len(RING_ART)))
        z = math.cos(th)
        x = cx + R * (0.15 + 0.85 * ease) * math.sin(th)
        y = cy + R * (0.15 + 0.85 * ease) * z * 0.38
        items.append((z, x, y, i))
    items.sort(key=lambda it: it[0])
    if reveal > 0.55:
        a0 = int(40 * (reveal - 0.55) / 0.45)
        d.ellipse([cx - R, cy - R * 0.38, cx + R, cy + R * 0.38],
                  outline=(150, 146, 140, a0), width=1)
    for z, x, y, i in items:
        sz = int(150 * (0.42 + 0.58 * (z + 1) / 2) * (0.55 + 0.45 * ease))
        if sz < 12:
            continue
        art = RING_ART[i].resize((sz, sz), Image.LANCZOS)
        if z < 0:
            art = art.filter(ImageFilter.GaussianBlur(min(5.0, -z * 4.5)))
        al = int(255 * (0.22 + 0.78 * (z + 1) / 2) * ease)
        art = art.copy()
        art.putalpha(art.split()[3].point(lambda v: int(v * al / 255)))
        img.alpha_composite(art, (int(x - sz / 2), int(y - sz / 2)))


def s_compare(img, lt, dur):
    d = ImageDraw.Draw(img)
    d.line([(W / 2, H * 0.18), (W / 2, H * 0.68)], fill=(120, 116, 110, 90), width=1)
    left = plain(240)
    img.alpha_composite(left, (int(W * 0.25 - 120), int(H * 0.36)))
    put_cat(img, 0.26, cy=int(H * 0.30), cx=int(W * 0.66))


def s_desktop(img, lt, dur):
    d = ImageDraw.Draw(img)
    for i in range(5):
        x = W * 0.16 + i * 160
        d.rounded_rectangle([x, H * 0.30, x + 110, H * 0.30 + 110], radius=14,
                            outline=(110, 106, 100, 90), width=1)
    art = cur_render("arrow", 90)
    px = W * 0.22 + (lt / dur) * W * 0.5
    img.alpha_composite(art, (int(px), int(H * 0.46)))


def s_eye(img, lt, dur):
    put_cat(img, 0.78, cy=int(H * 0.30))


def s_big(img, lt, dur):
    pass


def s_citations(img, lt, dur):
    d = ImageDraw.Draw(img)
    lines = ["璧勬枡鏉ユ簮锛歑erox Star (1981) 路 Apple Macintosh (1984)",
             "Windows 95 娌欐紡鍥炬爣 路 Windows .cur / .ani 鏂囦欢鏍煎紡",
             "鐢婚潰涓虹ず鎰忓浘 路 CursorLab 路 MIT License"]
    for i, ln in enumerate(lines):
        if lt < 0.2 + i * 0.5:
            continue
        a = int(170 * min(1.0, (lt - 0.2 - i * 0.5) / 0.6))
        w = d.textlength(ln, font=f(F_CN, 26))
        d.text(((W - w) / 2, H * 0.58 + i * 40), ln, font=f(F_CN, 26), fill=G3 + (a,))


def s_end(img, lt, dur):
    put_cat(img, 0.34, cy=int(H * 0.26))


# ---------------------------------------------------------------- 闀滃ご琛?
U = 2.14
SHOTS = [
    # (start, dur, render, cn, en, act, big)
    (0.00, U, s_arrow_in, "姣忓ぉ锛屼綘鐐瑰畠鍑犲崈娆?, "every day, thousands of clicks", ("鎸囬拡绠€鍙?, "A brief history", 1), False),
    (2.14, U, s_arrow_close, "鍙畠鍥涘崄骞存病鍙樿繃", "unchanged for forty years", None, False),
    (4.28, U, s_sysrow, "杩樻槸杩欎釜鏍峰瓙", "still the same", None, False),
    (6.42, U, s_dim, "鎴戞兂鏀?, "I wanted to change it", None, False),
    (8.56, 4.34, s_morph, "浜庢槸锛屾垜鑷繁鍋氫簡涓€鍙?, "so I made one myself", None, False),
    (12.90, U, s_cat_in, "涓€鍙尗锛屾浛鎺変簡绠ご", "a cat, instead of an arrow", None, False),
    (15.04, U, s_title, "涓€鍙尗", "A Cat", ("涓€鍙尗", "A cat", 1), True),
    (17.18, U, s_ref, "鎴戞兂瑕佷竴鍙粦鐚?, "I wanted a black cat", ("鎯虫硶", "The idea", 2), False),
    (19.32, U, s_words, "澶х溂鐫?路 閫氫綋婕嗛粦 路 鐚埅", "big eyes 路 all black 路 paw", None, False),
    (21.46, U, lambda i, l, d: s_version(i, l, d, 0), "绗竴鐗堬紝澶‖", "too hard", None, False),
    (23.60, U, lambda i, l, d: s_version(i, l, d, 1), "绗簩鐗堬紝澶崟钖?, "too thin", None, False),
    (25.74, U, lambda i, l, d: s_version(i, l, d, 2), "绗笁鐗堬紝璁や笉鍑?, "unreadable", None, False),
    (27.88, U, lambda i, l, d: s_version(i, l, d, 3), "绗洓鐗堬紝瀵逛簡", "the fourth one", None, False),
    (30.02, U, s_closeup, "灏卞畠浜?, "that's the one", None, False),
    (32.16, U, s_line, "杩斿伐鍥涙锛岄兘鏄垜涓€鍙ヨ瘽涓€鍙ヨ瘽璇寸殑", "four rounds, all by saying it", None, False),
    (34.30, U, s_cmd, "鎴戞妸瀹冧氦缁?AI", "I handed it to AI", ("鍋氭硶", "How", 3), False),
    (36.44, U, s_code, "鐢诲浘銆佸啓浠ｇ爜銆佹墦鍖咃紝瀹冨叏鍖?, "draw, code, package 鈥?all of it", None, False),
    (38.58, U, s_split17, "涓€寮犲浘锛屽彉鎴愪竴鏁村", "one image, a whole set", None, False),
    (40.72, U, s_grid17, "鍗佷竷涓鑹?, "seventeen roles", None, False),
    (42.86, U, s_sizes, "涓€濂楀浘锛屼笁绉嶅ぇ灏?, "one set, three sizes", None, False),
    (45.00, U, s_hotspot, "鐐瑰緱鍑嗭紝闈犺繖涓偣", "accuracy lives in this dot", None, False),
    (47.14, 2 * U, s_press3, "浼氬洖搴斾綘鐨勬墜", "it answers your hand", None, False),
    (51.42, U, s_onecmd, "涓€鏉″懡浠わ紝鍏ㄩ儴鐢熸垚", "one command, the whole set", None, False),
    (53.56, U, s_install, "涓や笅瑁呭ソ", "installed in two clicks", None, False),
    (55.70, U, s_tray, "寮€鏈哄氨鍦紝涓嶅崰灞忓箷", "always there, no window", None, False),
    (57.84, U, s_repo, "浠ｇ爜寮€婧愶紝缃戦〉鑳借瘯", "open source, try it live", None, False),
    (60.00, U, s_submit, "鎶曠粰浜嗗浗澶栫殑鏀跺綍绔?, "submitted to a cursor archive", None, False),
    (62.14, U, s_bridge, "浠庛€屾兂銆嶏紝鍒般€岃兘鐢ㄣ€?, "from an idea to something you use", None, False),
    (64.28, 6.42, s_ring, "鍗佷竷涓鑹?, "seventeen cursors", ("浜у搧", "The set", 4), False),
    (70.70, 2 * U, lambda i, l, d: s_ring(i, l, d, 0.6), "姣忎竴涓兘鍗曠嫭鐢昏繃", "every one drawn by hand", None, False),
    (74.98, 2 * U, lambda i, l, d: s_ring(i, l, d, 1.6), "鍚屼竴濂楅鏋?, "one skeleton, seventeen faces", None, False),
    (79.26, 2 * U, s_grid17, "鍗佷竷涓紝涓€涓笉灏?, "seventeen, none missing", None, False),
    (83.54, 2 * U, s_press3, "浼氬洖搴斾綘鐨勬墜", "it answers your hand", None, False),
    (87.82, 2 * U, s_desktop, "瀹冨氨鍦ㄤ綘鎵嬭竟", "right under your hand", None, False),
    (92.10, 2 * U, s_compare, "鎹㈡帀瀹冿紝鍙渶瑕佷竴涓喅瀹?, "one decision and it's gone", None, False),
    (96.38, 2 * U, s_end, "涓€鍙尗锛屼粠涓€涓康澶村紑濮?, "a cat, from a single thought", None, False),
    (100.66, 2 * U, s_eye, "鍏ㄧ▼锛屾垜鍙浜嗘垜鎯宠浠€涔?, "all I said was what I wanted", ("缁撹", "Epilogue", 6), False),
    (104.94, U, s_line, "鐢汇€佸啓浠ｇ爜銆佹墦鍖呫€佸彂甯冿紝閮芥槸瀹冨仛鐨?, "draw, code, ship 鈥?it did it all", None, False),
    (107.08, U, s_line, "鎴戝彧鍋氫簡涓変欢浜嬶細鎯炽€佺湅銆佽銆屼笉瀵广€?, "think, look, and say 'not quite'", None, False),
    (109.22, U, s_line, "杩欏氨鏄?AI 鏃朵唬鐨勯棬妲?, "that is the bar, now", None, False),
    (111.36, 2 * U, s_big, "浣犱笉闇€瑕佷細鍋氾紝浣犲彧闇€瑕佹兂瑕?, "you don't need the skill, only the want", None, True),
    (115.64, 2 * U, s_citations, "CursorLab 路 MIT 路 寮€婧?, "CursorLab 路 MIT 路 open source", None, False),
    (119.92, TOTAL - 119.92, s_end, "涓€鍙尗锛屼粠涓€涓康澶村紑濮?, "an idea is enough", None, False),
]


# ---------------------------------------------------------------- 甯?
def frame(i):
    t = i / FPS
    img = BG.convert("RGBA").copy()
    for (st, dur, fn, cn, en, act, big) in SHOTS:
        if st <= t < st + dur:
            fn(img, t - st, dur)
            typo(img, t, cn, en, act, big)
            break
    img = grain_and_vignette(img, i)
    fade = 1.0
    if t < 0.6:
        fade = t / 0.6
    if t > TOTAL - 1.2:
        fade = max(0.0, (TOTAL - t) / 1.2)
    if fade < 1.0:
        img = Image.eval(img, lambda v: int(v * fade))
    return img


def main():
    a = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    b = float(sys.argv[2]) if len(sys.argv) > 2 else TOTAL
    full = (a == 0 and b >= TOTAL)
    out = os.path.join(WORK, "film_v2.mp4" if full else "film_v2_part_%d_%d.mp4" % (a, b))
    audio = os.path.join(WORK, "film2_audio.wav")
    subprocess.run([FF, "-y", "-i", os.path.join(WORK, "bgm.wav"), "-ss", "%.2f" % a,
                    "-t", "%.2f" % (b - a), "-af", "volume=1.0", audio],
                   check=True, capture_output=True)
    cmd = [FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
           "-r", str(FPS), "-i", "-", "-i", audio,
           "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    n0, n1 = int(a * FPS), int(b * FPS)
    for idx, i in enumerate(range(n0, n1)):
        p.stdin.write(frame(i).tobytes())
        if idx % 200 == 0:
            print("  %d/%d (%.1fs)" % (idx, n1 - n0, i / FPS), flush=True)
    p.stdin.close()
    p.wait()
    print("saved", out)


if __name__ == "__main__":
    main()
