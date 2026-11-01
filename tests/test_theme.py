# -*- coding: utf-8 -*-
"""主题生成（png -> theme.json -> 构建）自测。"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw  # noqa: E402

from cursorlab import build, cartoon, theme as thememod, verify  # noqa: E402

from _runner import cleanup, tmpdir  # noqa: E402


class sandbox:
    """theme.main() 只认模块级 THEMES_DIR 和 build 的 OUT/DIST，一起指到临时目录。"""

    def __enter__(self):
        self.dir = tmpdir()
        self.saved = (thememod.THEMES_DIR, build.OUT, build.DIST, build.THEMES_DIR)
        themes = os.path.join(self.dir, "themes")
        thememod.THEMES_DIR = themes
        build.THEMES_DIR = themes
        build.OUT = os.path.join(self.dir, "out")
        build.DIST = os.path.join(self.dir, "dist")
        os.makedirs(themes)
        return self.dir

    def __exit__(self, *exc):
        (thememod.THEMES_DIR, build.OUT, build.DIST, build.THEMES_DIR) = self.saved
        cleanup(self.dir)
        return False


def _png(path, color=(20, 20, 20, 255), size=(64, 64)):
    im = Image.new("RGBA", size, (255, 255, 255, 255))
    ImageDraw.Draw(im).ellipse([8, 8, size[0] - 8, size[1] - 8], fill=color)
    im.save(path)


def test_natural_sort_orders_numbers_by_value():
    names = ["wait_10.png", "wait_2.png", "wait_1.png", "wait_0.png"]
    got = sorted(names, key=thememod._natural)
    assert got == ["wait_0.png", "wait_1.png", "wait_2.png", "wait_10.png"]


def test_find_frames_prefix_and_subdir():
    d = tmpdir()
    try:
        _png(os.path.join(d, "wait_1.png"))
        _png(os.path.join(d, "wait_0.png"))
        _png(os.path.join(d, "wait_10.png"))
        assert thememod.find_frames(d, "wait") == [
            "wait_0.png", "wait_1.png", "wait_10.png"]
        os.makedirs(os.path.join(d, "hand"))
        _png(os.path.join(d, "hand", "b.png"))
        _png(os.path.join(d, "hand", "a.png"))
        got = thememod.find_frames(d, "hand")
        assert got == ["hand/a.png", "hand/b.png"], got
    finally:
        cleanup(d)


def test_find_frames_empty_subdir_falls_back_to_none():
    d = tmpdir()
    try:
        os.makedirs(os.path.join(d, "pin"))
        assert thememod.find_frames(d, "pin") is None
        assert thememod.find_frames(d, "arrow") is None
    finally:
        cleanup(d)


def test_parse_hotspots_ok():
    hot = thememod.parse_hotspots(["arrow=2.5,3", "hand=16,10.4"])
    assert hot["arrow"] == [2.5, 3.0]
    assert hot["hand"] == [16.0, 10.4]
    assert hot["pin"] == list(cartoon.SPRITES["pin"]["hot"]), "没覆盖的角色应该保留默认值"


def test_parse_hotspots_rejects_bad_input():
    for bad in (["arrow"], ["nope=1,2"], ["arrow=1"], ["arrow=a,b"], ["arrow=1,2,3"],
                ["arrow=99,0"], ["arrow=-1,0"]):
        try:
            thememod.parse_hotspots(bad)
        except ValueError:
            continue
        raise AssertionError("--hot %r 应该被拒绝" % (bad,))


def test_default_hotspots_cover_every_sprite():
    assert set(thememod.DEFAULT_HOT) == set(cartoon.SPRITES)
    for key, hot in thememod.DEFAULT_HOT.items():
        assert 0 <= hot[0] <= 32 and 0 <= hot[1] <= 32, key


def test_collect_roles_counts_and_missing():
    d = tmpdir()
    try:
        _png(os.path.join(d, "arrow.png"))
        _png(os.path.join(d, "hand.png"))
        _png(os.path.join(d, "wait_0.png"))
        _png(os.path.join(d, "wait_1.png"))
        roles, copied, missing = thememod.collect_roles(d, thememod.DEFAULT_HOT)
        assert copied == 4
        assert roles["wait"]["frames"] == ["wait_0.png", "wait_1.png"]
        assert roles["arrow"]["src"] == "arrow.png"
        assert "person" in missing
        assert len(missing) == 14, missing
    finally:
        cleanup(d)


def test_write_theme_config_copies_files():
    d = tmpdir()
    try:
        src = os.path.join(d, "src")
        os.makedirs(src)
        keys = list(build.ROLE_KEY.values())
        for k in keys:
            _png(os.path.join(src, k + ".png"))
        tdir = os.path.join(d, "themes", "mine")
        cfg, copied, missing = thememod.write_theme_config(
            src, tdir, "mine", "Mine", thememod.DEFAULT_HOT, sizes=(32, 48))
        assert copied == 17 and not missing
        assert cfg["sizes"] == [32, 48] and cfg["outline"] is True
        assert os.path.exists(os.path.join(tdir, "theme.json"))
        assert os.path.exists(os.path.join(tdir, "arrow.png"))
        loaded = json.load(open(os.path.join(tdir, "theme.json"), encoding="utf-8"))
        assert loaded["roles"]["arrow"]["hot"] == list(cartoon.SPRITES["arrow"]["hot"])
    finally:
        cleanup(d)


def test_main_end_to_end():
    with sandbox() as d:
        src = os.path.join(d, "src")
        os.makedirs(src)
        for k in list(build.ROLE_KEY.values()):
            _png(os.path.join(src, k + ".png"))
        for f in range(3):
            _png(os.path.join(src, "wait_%d.png" % f), color=(200, 30, 30, 255))
        code = thememod.main(["--name", "mypet", "--src", src, "--sizes", "16,32"])
        assert code == 0
        outdir = os.path.join(build.OUT, "mypet")
        assert os.path.isdir(outdir)
        assert os.path.exists(os.path.join(outdir, "wait.ani"))
        assert verify.verify_dir(outdir) == {}, verify.verify_dir(outdir)
        assert os.path.exists(os.path.join(build.DIST, "mypet.zip"))


def test_main_missing_roles_exits_1():
    with sandbox() as d:
        src = os.path.join(d, "src")
        os.makedirs(src)
        _png(os.path.join(src, "arrow.png"))
        assert thememod.main(["--name", "thin", "--src", src, "--no-build"]) == 1


def test_main_nobuild_only_writes_json():
    with sandbox() as d:
        src = os.path.join(d, "src")
        os.makedirs(src)
        for k in list(build.ROLE_KEY.values()):
            _png(os.path.join(src, k + ".png"))
        assert thememod.main(["--name", "jsononly", "--src", src, "--no-build"]) == 0
        assert os.path.exists(os.path.join(build.THEMES_DIR, "jsononly", "theme.json"))
        assert not os.path.isdir(os.path.join(build.OUT, "jsononly"))


def test_main_rejects_bad_paths_and_hotspots():
    with sandbox() as d:
        try:
            thememod.main(["--name", "x", "--src", os.path.join(d, "nope")])
        except SystemExit as exc:
            assert "素材目录不存在" in str(exc)
        else:
            raise AssertionError("不存在的素材目录应该退出")
        src = os.path.join(d, "src")
        os.makedirs(src)
        _png(os.path.join(src, "arrow.png"))
        try:
            thememod.main(["--name", "x", "--src", src, "--hot", "arrow=99,0"])
        except SystemExit as exc:
            assert "热点" in str(exc) or "设计网格" in str(exc)
        else:
            raise AssertionError("越界热点应该退出")


if __name__ == "__main__":
    from _runner import run
    sys.exit(run())
