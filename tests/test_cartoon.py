# -*- coding: utf-8 -*-
"""卡通造型自测：每个造型都能画、热点在网格内、按下态确实不一样。"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cursorlab import cartoon  # noqa: E402


def _diff(a, b):
    """两张图有多少像素不同（0..255 的 alpha 差异总和）。"""
    if a.size != b.size:
        return 999
    pa, pb = a.load(), b.load()
    total = 0
    for y in range(a.size[1]):
        for x in range(a.size[0]):
            if pa[x, y] != pb[x, y]:
                total += 1
    return total


def test_sprites_have_required_fields():
    for key, spec in cartoon.SPRITES.items():
        assert callable(spec["fn"]), key
        assert spec["frames"] >= 1, key
        hot = spec["hot"]
        assert 0 <= hot[0] <= cartoon.N and 0 <= hot[1] <= cartoon.N, key
    for key, spec in cartoon.EXTRA.items():
        assert callable(spec["fn"]), key
        assert "press" in key


def test_registry_has_17_roles():
    assert len(cartoon.SPRITES) == 17


def test_render_unknown_key_mentions_valid_names():
    try:
        cartoon.render("arrow_pres", 32)
    except KeyError as exc:
        msg = str(exc)
        assert "arrow_pres" in msg and "arrow_press" in msg
    else:
        raise AssertionError("拼错的造型名应该报错")


def test_render_extra_sprite():
    im = cartoon.render("hand_press", 32)
    assert im.size == (32, 32) and im.getbbox() is not None


def test_press_variants_differ_from_idle():
    for idle, pressed in (("arrow", "arrow_press"), ("hand", "hand_press"),
                          ("ibeam", "ibeam_press")):
        a = cartoon.render(idle, 32)
        b = cartoon.render(pressed, 32)
        assert _diff(a, b) > 30, "%s 和 %s 几乎一样，按下态没生效" % (idle, pressed)


def test_arrow_animation_frames_differ():
    frames = [cartoon.render("arrow", 32, f) for f in range(12)]
    assert _diff(frames[0], frames[3]) > 5, "12 帧微动画应该有差别"
    assert _diff(frames[3], frames[9]) > 5, "尾巴摆动的两个极点应该不同"
    # 正弦相位：f=0 和 f=6 的 phase 都是 0，本来就该是同一帧
    assert _diff(frames[0], frames[6]) == 0


def test_wait_spinner_rotates():
    frames = [cartoon.render("wait", 32, f) for f in range(8)]
    assert _diff(frames[0], frames[1]) > 5, "转圈每帧都应该动"
    assert _diff(frames[0], frames[4]) > 5


def test_render_scales_with_size():
    small = cartoon.render("arrow", 32)
    big = cartoon.render("arrow", 64)
    assert big.size == (64, 64)
    bs, bb = small.getbbox(), big.getbbox()
    assert bb[2] - bb[0] > (bs[2] - bs[0]) * 1.6, "64px 的墨迹应该差不多是两倍宽"


def test_all_sprites_have_ink_inside_canvas():
    for key in cartoon.SPRITES:
        im = cartoon.render(key, 32)
        bb = im.getbbox()
        assert bb is not None, "%s 渲染成空图" % key
        assert 0 <= bb[0] and 0 <= bb[1] and bb[2] <= 32 and bb[3] <= 32, key


if __name__ == "__main__":
    from _runner import run
    sys.exit(run())
