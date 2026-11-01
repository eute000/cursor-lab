# -*- coding: utf-8 -*-
"""
按下变握爪 —— CursorLab 点击动态小助手。

Windows 的光标没有"按下"状态，.ani 只会循环播放。所以这里用 30ms 轮询
鼠标左右键，按下时把系统箭头临时换成 arrow_press.cur（猫低头眯眼握爪），
松开时调 SPI_SETCURSORS 从当前方案恢复。

只影响当前登录会话，不写注册表、不需要管理员。Ctrl+C 或关窗口即恢复。

用法：
    python tools/click_fx.py
"""

import atexit
import ctypes
import os
import sys
import time
from ctypes import wintypes

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

user32 = ctypes.windll.user32

SPI_SETCURSORS = 0x0057
OCR_NORMAL = 32512          # 系统箭头
IMAGE_CURSOR = 2
LR_LOADFROMFILE = 0x0010
VK_LBUTTON, VK_RBUTTON = 0x01, 0x02

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _find_press():
    """仓库内 / 发行包里 / 手动放置，都能找到按下态文件"""
    cands = [
        os.path.join(HERE, "out", "cartoon-cat", "arrow_press.cur"),
        os.path.join(HERE, "cursors", "arrow_press.cur"),
        os.path.join(HERE, "arrow_press.cur"),
        os.path.join(os.path.dirname(HERE), "cursors", "arrow_press.cur"),
    ]
    for c in cands:
        if os.path.exists(c):
            return c
    raise SystemExit("找不到 arrow_press.cur（试过：%s）" % "\n  ".join(cands))


PRESS_CUR = _find_press()


def _restore():
    """从当前指针方案恢复（SetSystemCursor 会接管句柄，不能自己留着）"""
    try:
        user32.SystemParametersInfoW(SPI_SETCURSORS, 0, None, 3)
    except Exception:
        pass


def _load_cursor(path):
    h = user32.LoadImageW(None, path, IMAGE_CURSOR, 0, 0, LR_LOADFROMFILE)
    if not h:
        raise OSError("加载光标失败：%s" % path)
    return h


def _pressed():
    return bool(user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000 or
                user32.GetAsyncKeyState(VK_RBUTTON) & 0x8000)


def main():
    if not os.path.exists(PRESS_CUR):
        raise SystemExit("找不到 %s\n先跑 python -m cursorlab.build" % PRESS_CUR)

    atexit.register(_restore)
    print("CursorLab 点击动态已启动（Ctrl+C 退出）")
    print("  按下 → %s" % os.path.basename(PRESS_CUR))
    print("  松开 → 恢复方案光标")

    holding = False
    try:
        while True:
            down = _pressed()
            if down and not holding:
                # SetSystemCursor 会销毁句柄，所以每次按下都重新加载
                user32.SetSystemCursor(_load_cursor(PRESS_CUR), OCR_NORMAL)
                holding = True
            elif not down and holding:
                _restore()
                holding = False
            time.sleep(0.03)
    except KeyboardInterrupt:
        pass
    finally:
        _restore()
        print("已退出，指针已恢复")


def selftest():
    """自检：加载按下态 → 换上 → 1 秒 → 恢复。用来确认机制能跑通。"""
    if not os.path.exists(PRESS_CUR):
        raise SystemExit("找不到 %s\n先跑 python -m cursorlab.build" % PRESS_CUR)
    h = _load_cursor(PRESS_CUR)
    print("LoadImage 成功，句柄 =", h)
    user32.SetSystemCursor(h, OCR_NORMAL)
    print("已切到按下态，1 秒后恢复……")
    time.sleep(1.0)
    _restore()
    print("已恢复 ✅")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        main()
