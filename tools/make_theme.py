# -*- coding: utf-8 -*-
"""
把一堆 png 变成一套主题（自定义指针的主入口）。

用法：
    python tools/make_theme.py --name my-cat --src assets/my-cat
    python tools/make_theme.py --name my-cat --src assets/my-cat --hot arrow=2,2 hand=16,8

真正的实现在 cursorlab/theme.py —— 这里只是保持 README 里那条命令还能用。
（以前这个文件写的是 `from cursorlab.cat import SPRITES`，模块名根本不存在，
 所以这条命令一执行就 ModuleNotFoundError。）
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cursorlab.theme import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
