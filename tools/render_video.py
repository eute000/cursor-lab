# -*- coding: utf-8 -*-
"""
一键出片：渲染 8 个画面帧 → 编码 → 按时间轴合入配音 → 输出 mp4。

前置：配音 vo1..vo8.mp3 用 voice_tts 生成到 WORK 目录。
跑法：python tools/render_video.py
产物：WORK/cursorlab_vibe_final.mp4（9:16 / 1080x1920 / 30fps）

踩过的坑（都写在代码里了）：
  1. ffmpeg 的 zoompan 用 d=frames 会让时长翻几十倍 → 用 d=1 + zoom+ 递增
  2. mp3 用 concat demuxer 拼会有时长错乱 → 用 concat 滤镜，静音先 asplit 复制
  3. concat 列表文件必须 UTF-8 无 BOM，否则 ffmpeg 报 Invalid argument
  4. cartoon.render 在高分辨率下会触发 8x 超采样+上百次描边膨胀 → 先渲染 160px 再放大
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib.util

spec = importlib.util.spec_from_file_location(
    "mv", os.path.join(os.path.dirname(os.path.abspath(__file__)), "make_video.py"))
mv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mv)

FF, FP, WORK, FPS = mv.FF, mv.FP, mv.WORK, mv.FPS
GAP = 0.32
N = 8


def dur(p):
    return float(subprocess.check_output(
        [FP, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", p], text=True).strip())


def probe_audio(p):
    out = subprocess.check_output(
        [FP, "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=sample_rate,channels", "-of", "csv=p=0", p], text=True)
    sr, ch = out.strip().split(",")[:2]
    return int(sr), int(ch)


def main():
    subs = [
        "Windows 的鼠标指针太丑了，我让 AI 给我做了一整套。",
        "按住鼠标，它会眯眼、收爪子。",
        "桌面、输入框、链接，三处都有反应。",
        "一共 17 个，Windows 要的它全齐了。",
        "参考图发过去，第一版太像素，打回重做，改到第四版才满意。",
        "冷知识：鼠标指针不是普通图片，里面塞了三张不同大小的图，还有一个点击点。",
        "一条命令生成全套，传到 GitHub，还做了网页能直接试。",
        "从我想要一只猫，到别人能下载，我只负责说：我想要什么。",
    ]
    vos = [os.path.join(WORK, "vo%d.mp3" % (i + 1)) for i in range(N)]
    for p in vos:
        if not os.path.exists(p):
            raise SystemExit("缺配音：%s" % p)

    for i, s in enumerate(subs):
        mv.render_scene(i, s).save(os.path.join(WORK, "s%02d.png" % (i + 1)))
    print("帧 OK")

    lines, total = [], 0.0
    for i in range(N):
        d = dur(vos[i]) + GAP
        total += d
        lines.append("file '%s'" % os.path.join(WORK, "s%02d.png" % (i + 1)).replace("\\", "/"))
        lines.append("duration %.3f" % d)
    lines.append("file '%s'" % os.path.join(WORK, "s%02d.png" % N).replace("\\", "/"))
    lst = os.path.join(WORK, "img.txt")
    with open(lst, "w", encoding="utf-8", newline="\n") as fh:   # 必须无 BOM
        fh.write("\n".join(lines) + "\n")

    v4 = os.path.join(WORK, "v4.mp4")
    mv.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst,
            "-vf", "fps=%d,format=yuv420p" % FPS,
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22", "-an", v4])

    sr, ch = probe_audio(vos[0])
    sil = os.path.join(WORK, "silence.mp3")
    subprocess.run([FF, "-y", "-f", "lavfi", "-i",
                    "anullsrc=r=%d:cl=%s" % (sr, "mono" if ch == 1 else "stereo"),
                    "-t", str(GAP), "-c:a", "libmp3lame", sil], check=True,
                   capture_output=True)

    inputs = ["-i", v4]
    for p in vos:
        inputs += ["-i", p]
    inputs += ["-i", sil]
    sil_idx = N + 1
    parts = ["[%d:a]aresample=%d[a%d]" % (i + 1, sr, i) for i in range(N)]
    parts.append("[%d:a]aresample=%d,asplit=%d%s" %
                 (sil_idx, sr, N, "".join("[s%d]" % i for i in range(N))))
    seq = "".join("[a%d][s%d]" % (i, i) for i in range(N))
    filt = ";".join(parts) + ";" + seq + "concat=n=%d:v=0:a=1[a]" % (N * 2)

    out = os.path.join(WORK, "cursorlab_vibe_final.mp4")
    mv.run([FF, "-y"] + inputs + [
        "-filter_complex", filt, "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", out])
    print("成片 %.2f 秒 -> %s" % (dur(out), out))


if __name__ == "__main__":
    main()
