# -*- coding: utf-8 -*-
"""CursorLab —— 自己画、自己打包的 Windows 鼠标指针工具链。"""

__version__ = "2.1.0"

__all__ = [
    "__version__",
    "ROLES",
    "DESIGN",
    "dib32",
    "cur_bytes",
    "ani_bytes",
    "check_hotspot",
    "render",
    "SPRITES",
    "EXTRA",
    "load_themes",
    "build_theme",
    "verify_cur",
    "verify_ani",
    "verify_dir",
]


def __getattr__(name):
    """按需导入，让 `import cursorlab` 不强制拉 Pillow。"""
    if name in ("ROLES", "DESIGN", "dib32", "cur_bytes", "ani_bytes", "check_hotspot"):
        from . import encode
        return getattr(encode, name)
    if name in ("render", "SPRITES", "EXTRA"):
        from . import cartoon
        return getattr(cartoon, name)
    if name in ("load_themes", "build_theme"):
        from . import build
        return getattr(build, name)
    if name in ("verify_cur", "verify_ani", "verify_dir"):
        from . import verify
        return getattr(verify, name)
    raise AttributeError("module %r has no attribute %r" % (__name__, name))
