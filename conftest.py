# -*- coding: utf-8 -*-
"""让 `pytest` 和 `python -m pytest` 都能从仓库根目录 import cursorlab。

仓库是 pkg/ + tests/ 平铺结构（没有 __init__.py），bare `pytest` 不会把
仓库根塞进 sys.path，收集阶段就会报 ModuleNotFoundError。
"""

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
for path in (ROOT, os.path.join(ROOT, "tests")):
    if path not in sys.path:
        sys.path.insert(0, path)
