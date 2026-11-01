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

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# pythonw（无控制台）下 stdout/stderr 是 None，print 会抛异常，先兜到 null
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

user32 = ctypes.windll.user32

SPI_SETCURSORS = 0x0057
OCR_NORMAL = 32512          # 系统箭头
OCR_IBEAM = 32513           # 文本 I 型
OCR_HAND = 32649            # 链接手型
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
PRESS_IBEAM = os.path.join(os.path.dirname(PRESS_CUR), "ibeam_press.cur")
PRESS_HAND = os.path.join(os.path.dirname(PRESS_CUR), "hand_press.cur")


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
    tick = 0
    try:
        while True:
            down = _pressed()
            if down:
                # 关键：窗口在鼠标移动/重绘时会用自己的光标覆盖 SetSystemCursor，
                # 所以按住期间每 ~40ms 重新压一次，才能稳定显示握爪。
                if not holding:
                    print("[%s] 按下 → 握爪" % time.strftime("%H:%M:%S"))
                    holding = True
                if tick % 2 == 0:
                    user32.SetSystemCursor(_load_cursor(PRESS_CUR), OCR_NORMAL)
                    if os.path.exists(PRESS_IBEAM):
                        user32.SetSystemCursor(_load_cursor(PRESS_IBEAM), OCR_IBEAM)
                    if os.path.exists(PRESS_HAND):
                        user32.SetSystemCursor(_load_cursor(PRESS_HAND), OCR_HAND)
            elif holding:
                _restore()
                holding = False
                print("[%s] 松开 → 恢复" % time.strftime("%H:%M:%S"))
            tick += 1
            time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    finally:
        _restore()
        print("已退出，指针已恢复")


def hold_test(seconds=4.0):
    """把握爪态维持 N 秒（持续压制覆盖），用来肉眼确认效果。"""
    if not os.path.exists(PRESS_CUR):
        raise SystemExit("找不到 %s" % PRESS_CUR)
    print("接下来 %.0f 秒光标会强制显示为握爪态，看清楚了……" % seconds)
    end = time.time() + seconds
    while time.time() < end:
        user32.SetSystemCursor(_load_cursor(PRESS_CUR), OCR_NORMAL)
        time.sleep(0.02)
    _restore()
    print("已恢复 ✅")


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "CursorLabClickFx"


def _autostart_cmd():
    """优先用 pythonw.exe（无黑窗口），没有就退回 python.exe"""
    pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    exe = pyw if os.path.exists(pyw) else sys.executable
    return '"%s" "%s"' % (exe, os.path.abspath(__file__))


def autostart_install():
    import winreg
    cmd = _autostart_cmd()
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
        winreg.SetValueEx(k, RUN_NAME, 0, winreg.REG_SZ, cmd)
    print("已设为开机自启（无窗口）：", cmd)


def autostart_remove():
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                            winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, RUN_NAME)
        print("已取消开机自启")
    except FileNotFoundError:
        print("本来就没有开机自启项")


def autostart_status():
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            v, _ = winreg.QueryValueEx(k, RUN_NAME)
        print("开机自启：已开启")
        print("  ", v)
    except FileNotFoundError:
        print("开机自启：未开启")


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
    args = sys.argv[1:]
    if "--selftest" in args:
        selftest()
    elif "--hold-test" in args:
        hold_test()
    elif "--autostart-install" in args:
        autostart_install()
    elif "--autostart-remove" in args:
        autostart_remove()
    elif "--autostart-status" in args:
        autostart_status()
    else:
        main()
