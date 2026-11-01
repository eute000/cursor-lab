# -*- coding: utf-8 -*-
"""构建器自测：主题 -> 文件、抠背景、描边、预览图、zip、CLI 开关。"""

import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw  # noqa: E402

from cursorlab import build, cartoon, verify  # noqa: E402
from cursorlab.encode import ROLES  # noqa: E402

from _runner import cleanup, tmpdir  # noqa: E402


class sandbox:
    """把 out/ dist/ themes/ 全指到临时目录，测试不碰仓库。"""

    def __enter__(self):
        self.dir = tmpdir()
        self.saved = (build.OUT, build.DIST, build.THEMES_DIR)
        build.OUT = os.path.join(self.dir, "out")
        build.DIST = os.path.join(self.dir, "dist")
        build.THEMES_DIR = os.path.join(self.dir, "themes")
        os.makedirs(build.THEMES_DIR)
        return self.dir

    def __exit__(self, *exc):
        build.OUT, build.DIST, build.THEMES_DIR = self.saved
        cleanup(self.dir)
        return False


def make_assets(folder, keys, size=(64, 64), bg=(255, 255, 255, 255)):
    """造一套素材 png，返回 theme.json 路径。"""
    os.makedirs(folder, exist_ok=True)
    roles = {}
    for i, key in enumerate(keys):
        im = Image.new("RGBA", size, bg)
        w, h = size
        d = ImageDraw.Draw(im)
        d.ellipse([w // 6, h // 6, w - w // 6, h - h // 6],
                  fill=(20 + i * 3, 30, 60, 255))
        im.save(os.path.join(folder, key + ".png"))
        roles[key] = {"src": key + ".png", "hot": [16, 16]}
    cfg = {"name": "probe", "roles": roles}
    path = os.path.join(folder, "theme.json")
    with open(path, "w", encoding="utf-8") as fh:
        import json
        json.dump(cfg, fh)
    return path


def test_load_themes_has_cartoon_cat():
    themes = build.load_themes()
    assert "cartoon-cat" in themes
    assert themes["cartoon-cat"].kind == "procedural"
    assert set(build.ROLE_KEY) == set(ROLES), "ROLE_KEY 必须覆盖 17 个注册表角色"


def test_build_procedural_theme():
    with sandbox():
        theme = build.ProceduralTheme("small", "小样", cartoon.SPRITES, [16, 32],
                                      render_fn=cartoon.render)
        outdir = build.build_theme(theme, preview_size=24, sheet_cell=24)
        names = set(os.listdir(outdir))
        assert "arrow.ani" in names, "12 帧的 arrow 应该出 .ani"
        assert "wait.ani" in names and "appstarting.ani" in names
        assert "crosshair.cur" in names
        for key in (*cartoon.EXTRA,):
            assert "%s.cur" % key in names, "按下态 %s 没出" % key
        assert "preview.png" in names
        assert os.path.isdir(os.path.join(outdir, "png"))
        assert len(os.listdir(os.path.join(outdir, "png"))) == len(cartoon.SPRITES)
        assert verify.verify_dir(outdir) == {}, verify.verify_dir(outdir)


def test_build_asset_theme_without_extras():
    """图片主题没有按下态造型，以前会在这一步 KeyError: 'arrow_press'。"""
    with sandbox() as d:
        folder = os.path.join(d, "assets")
        path = make_assets(folder, list(build.ROLE_KEY.values()))
        theme = build.AssetTheme(path)
        outdir = build.build_theme(theme)
        names = set(os.listdir(outdir))
        assert not [n for n in names if n.endswith(("_press.cur",))]
        assert len([n for n in names if n.endswith((".cur", ".ani"))]) == 17
        assert verify.verify_dir(outdir) == {}, verify.verify_dir(outdir)


def test_build_rejects_missing_roles():
    with sandbox() as d:
        folder = os.path.join(d, "assets")
        path = make_assets(folder, ["arrow", "hand"])
        try:
            build.build_theme(build.AssetTheme(path))
        except SystemExit as exc:
            assert "缺这些角色" in str(exc)
        else:
            raise AssertionError("缺角色应该直接退出")


def test_check_sizes():
    assert build.check_sizes([32, "48"]) == [32, 48]
    for bad in ([], [0], [257], ["x"], [None]):
        try:
            build.check_sizes(bad)
        except ValueError:
            continue
        raise AssertionError("sizes=%r 应该被拒绝" % (bad,))


def test_build_reports_bad_hotspot_with_role():
    with sandbox() as d:
        folder = os.path.join(d, "assets")
        path = make_assets(folder, list(build.ROLE_KEY.values()))
        theme = build.AssetTheme(path)
        theme.items["arrow"]["hot"] = [99, 5]
        theme.sprites["arrow"]["hot"] = (99, 5)
        try:
            build.build_theme(theme)
        except ValueError as exc:
            assert "arrow" in str(exc) and "热点" in str(exc)
        else:
            raise AssertionError("越界热点应该报错")


def test_fit_square_keeps_aspect():
    wide = Image.new("RGBA", (64, 16), (0, 0, 0, 0))
    wide.paste((255, 0, 0, 255), (0, 0, 64, 16))
    out = build.fit_square(wide, 32)
    assert out.size == (32, 32)
    bb = out.getbbox()
    assert bb is not None
    w = bb[2] - bb[0]
    h = bb[3] - bb[1]
    assert w == 32 and 7 <= h <= 9, "4:1 的图应该变成 32x8，实际 %dx%d" % (w, h)


def test_fit_square_exact_size_is_identity():
    im = Image.new("RGBA", (32, 32), (1, 2, 3, 255))
    assert build.fit_square(im, 32) is im


def test_cut_background_keeps_interior_white():
    """白底 + 白眼睛：眼睛必须留着，不然深色壁纸上就是个洞。"""
    im = Image.new("RGBA", (48, 48), (255, 255, 255, 255))
    d = ImageDraw.Draw(im)
    d.ellipse([6, 6, 42, 42], fill=(20, 20, 20, 255))
    d.ellipse([16, 14, 32, 30], fill=(255, 255, 255, 255))     # 白眼睛
    out = build.cut_background(im)
    px = out.load()
    assert px[0, 0][3] == 0, "边角背景应该被抠掉"
    assert px[24, 22][3] == 255, "内部白眼睛不能被抠穿"
    assert px[24, 8][3] == 255, "本体应该保留"


def test_cut_background_tolerance_and_untouched_colours():
    im = Image.new("RGBA", (20, 20), (250, 250, 250, 255))     # 近白底
    ImageDraw.Draw(im).rectangle([5, 5, 14, 14], fill=(10, 60, 200, 255))
    out = build.cut_background(im, tol=26)
    assert out.load()[0, 0][3] == 0
    assert out.load()[10, 10] == (10, 60, 200, 255)


def test_cut_background_already_transparent():
    im = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    assert build.cut_background(im).tobytes() == im.tobytes()


def test_add_rim_grows_alpha_by_one_pixel():
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    ImageDraw.Draw(im).rectangle([5, 5, 10, 10], fill=(0, 0, 0, 255))
    out = build.add_rim(im)
    assert out.getbbox() == (4, 4, 12, 12), "描边应该只扩 1px：%r" % (out.getbbox(),)
    assert out.getpixel((5, 5)) == (0, 0, 0, 255), "本体颜色不能被描边盖掉"
    assert out.getpixel((4, 5))[3] == 255, "描边像素应该不透明"


def test_build_sheet_has_no_dead_margin():
    theme = build.ProceduralTheme("t", "标题", cartoon.SPRITES, [16],
                                  render_fn=cartoon.render)
    cell, gap, pad, cols = 16, 4, 6, 6
    sheet = build.build_sheet(theme, cell=cell, gap=gap, pad=pad, cols=cols)
    want_w = pad * 2 + cols * (cell * 2 + gap) - gap
    assert sheet.size[0] == want_w, "预览图宽度 %d，应为 %d" % (sheet.size[0], want_w)
    px = sheet.load()
    bg = build.SHEET_BG
    last = max(x for x in range(sheet.size[0])
               if any(px[x, y] != bg for y in range(sheet.size[1])))
    assert sheet.size[0] - 1 - last <= 2 * pad, "右边留了 %d 像素空白" % (sheet.size[0] - 1 - last)


def test_build_sheet_unknown_role_key():
    with sandbox() as d:
        folder = os.path.join(d, "assets")
        keys = list(build.ROLE_KEY.values()) + ["myextra"]
        path = make_assets(folder, keys)
        theme = build.AssetTheme(path)
        sheet = build.build_sheet(theme)
        assert sheet.size[0] > 0


def test_sheet_order_puts_known_roles_first():
    with sandbox() as d:
        folder = os.path.join(d, "assets")
        keys = ["hand", "myextra", "arrow"]
        path = make_assets(folder, keys)
        theme = build.AssetTheme(path)
        order = build.sheet_order(theme)
        assert order[:2] == ["arrow", "hand"], order
        assert order[-1] == "myextra"


def test_base_dir_prefers_source_tree():
    root = build.base_dir()
    assert os.path.exists(os.path.join(root, "install.ps1")), root
    assert build.OUT == os.path.join(build.ROOT, "out")
    assert build.DIST == os.path.join(build.ROOT, "dist")
    assert build.THEMES_DIR == os.path.join(build.ROOT, "themes")


def test_package_zip_contents():
    with sandbox():
        theme = build.ProceduralTheme("zipme", "打包", cartoon.SPRITES, [16],
                                      render_fn=cartoon.render)
        outdir = build.build_theme(theme, verbose=False, preview_size=8, sheet_cell=8)
        zpath = build.package(theme, outdir)
        assert os.path.exists(zpath)
        with zipfile.ZipFile(zpath) as z:
            names = set(z.namelist())
        assert "README.txt" in names
        assert "install.ps1" in names and "uninstall.ps1" in names
        assert "安装.bat" in names
        assert "click_fx.py" in names
        cursors = [n for n in names if n.startswith("cursors/")]
        assert len(cursors) == 20, len(cursors)


def test_main_list_and_unknown_theme():
    with sandbox():
        assert build.main(["--list"]) == 0
        try:
            build.main(["--theme", "nope", "--no-zip"])
        except SystemExit as exc:
            assert "没有这个主题" in str(exc)
        else:
            raise AssertionError("不存在的主题应该退出")


if __name__ == "__main__":
    from _runner import run
    sys.exit(run())
