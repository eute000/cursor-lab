# -*- coding: utf-8 -*-
"""不装 pytest 也能跑全部用例（CI 里就是 `python tests/test_encode.py`）。

用法：
    python tests/test_encode.py     # 跑 tests/ 下所有 test_*.py
    python tests/_runner.py         # 同上
    python tests/_runner.py tests/test_encode.py   # 只跑一个文件

约定：用例函数不接受参数、不用 fixture（临时目录用 _tmpdir() 自己开自己删），
这样同一套用例既能被 pytest 收集，也能被这个 runner 直接跑。
"""

import importlib.util
import os
import shutil
import sys
import tempfile
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (HERE, ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def tmpdir():
    """建一个临时目录，调用方负责用 rmtree 收拾。"""
    return tempfile.mkdtemp(prefix="cursorlab-test-")


def cleanup(path):
    shutil.rmtree(path, ignore_errors=True)


def _load(path):
    name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError("加载不了用例文件: %s" % path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def run(paths=None, verbose=True):
    if not paths:
        paths = [os.path.join(HERE, n) for n in sorted(os.listdir(HERE))
                 if n.startswith("test_") and n.endswith(".py")]
    fails = 0
    total = 0
    for path in paths:
        mod = _load(os.path.abspath(path))
        for name in sorted(dir(mod)):
            if not name.startswith("test_"):
                continue
            fn = getattr(mod, name)
            if not callable(fn):
                continue
            total += 1
            try:
                fn()
                if verbose:
                    print("PASS %s" % name)
            except Exception:
                fails += 1
                print("FAIL %s (%s)" % (name, os.path.basename(path)))
                traceback.print_exc()
    print("\n%d 个用例，%d 个失败" % (total, fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:] or None))
