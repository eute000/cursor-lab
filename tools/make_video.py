# -*- coding: utf-8 -*-
"""
生成一条 9:16 竖屏视频：PIL 出画面帧 + ffmpeg 合成 + 配音。

工作目录必须英文路径（libass/中文路径有坑），这里用 E:\deepseek\.tmp\vibe。
用法：python tools/make_video.py
素材：vo1..vo8.mp3 由 voice_tts 生成，脚本自己量时长排时间轴。
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from cursorlab import cartoon

W, H, FPS = 1080, 1920, 30
WORK = r"E:\deepseek\.tmp\vibe"
FF = r"D:\python\huanjing\ffmpeg.exe"
FP = r"D:\python\huanjing\ffprobe.exe"
OUT = os.path.join(WORK, "cursorlab_vibe_v1.mp4")

BG_TOP, BG_BOT = (14, 16, 21), (32, 36, 46)
INK = (240, 242, 248)
MUT = (150, 156, 170)
ACCENT = (255, 138, 170)
CYAN = (120, 226, 255)
GAP = 0.32          # 每句之间留白

F_TITLE = r"C:\Windows\Fonts\msyhbd.ttc"
F_BODY = r"C:\Windows\Fonts\msyh.ttc"


def font(path, size):
    return ImageFont.truetype(path, size) if os.path.exists(path) else ImageFont.load_default()


_BG_CACHE = []


ART_BASE = 160


def art(key, size, frame=0):
    """小尺寸渲染再放大：cartoon.render 在高分辨率下会慢到不可用"""
    im = cartoon.render(key, ART_BASE, frame)
    if size != ART_BASE:
        im = im.resize((size, size), Image.LANCZOS)
    return im


def base_canvas():
    # 渐变 + 大半径光斑很慢，算一次缓存起来（8 个场景共用）
    if _BG_CACHE:
        return _BG_CACHE[0].copy()
    img = Image.new("RGB", (W, H), BG_TOP)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)],
               fill=tuple(int(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * t) for i in range(3)))
    # 光斑
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-420, -260, 720, 780], fill=(255, 138, 170, 26))
    gd.ellipse([520, 1180, 1500, 2080], fill=(120, 226, 255, 22))
    img = img.convert("RGBA")
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120)))
    _BG_CACHE.append(img)
    return img.copy()


def paste_center(img, art, cy, scale=1.0):
    if scale != 1.0:
        art = art.resize((int(art.width * scale), int(art.height * scale)), Image.LANCZOS)
    img.alpha_composite(art, ((W - art.width) // 2, int(cy - art.height / 2)))


def title(img, lines, y=190, size=78, color=INK):
    d = ImageDraw.Draw(img)
    f = font(F_TITLE, size)
    for i, ln in enumerate(lines):
        w = d.textlength(ln, font=f)
        d.text(((W - w) / 2, y + i * (size + 16)), ln, font=f, fill=color)


def subtitle(img, text, size=44):
    """底部字幕：白字黑描边，抖音风格"""
    d = ImageDraw.Draw(img)
    f = font(F_BODY, size)
    max_w = W - 140
    lines, cur = [], ""
    for ch in text:
        if d.textlength(cur + ch, font=f) > max_w:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    y = 1600 - (len(lines) - 1) * (size + 12)
    for i, ln in enumerate(lines):
        w = d.textlength(ln, font=f)
        d.text(((W - w) / 2, y + i * (size + 12)), ln, font=f, fill=(255, 255, 255),
               stroke_width=7, stroke_fill=(0, 0, 0))


def card(img, box, radius=28, fill=(22, 25, 33, 235), outline=(60, 66, 80)):
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=2)
    img.alpha_composite(overlay)


def render_scene(idx, sub):
    img = base_canvas()
    d = ImageDraw.Draw(img)

    if idx == 0:
        title(img, ["Windows 的指针", "太丑了"], 210)
        paste_center(img, art("arrow", 700), 1000)
        d.text((W / 2 - d.textlength("我让 AI 给我做了一整套", font=font(F_TITLE, 52)) / 2, 1420),
               "我让 AI 给我做了一整套", font=font(F_TITLE, 52), fill=ACCENT)

    elif idx == 1:
        title(img, ["按住鼠标"], 210)
        # 左右对比：平时 / 按住
        left, right = art("arrow", 460), art("arrow_press", 460)
        img.alpha_composite(left, (60, 700))
        img.alpha_composite(right, (560, 700))
        for x, t, col in ((150, "平时", MUT), (650, "按住", ACCENT)):
            d.text((x, 1200), t, font=font(F_TITLE, 52), fill=col)
        d.text((120, 1290), "尾巴轻摆", font=font(F_BODY, 34), fill=MUT)
        d.text((620, 1290), "眯眼 · 收爪", font=font(F_BODY, 34), fill=MUT)

    elif idx == 2:
        title(img, ["三处都有反应"], 210)
        keys = [("arrow", "桌面"), ("ibeam", "输入框"), ("hand", "链接")]
        for i, (k, label) in enumerate(keys):
            pic = art(k, 280)
            x = 60 + i * 330
            img.alpha_composite(pic, (x, 760))
            d.text((x + 70, 1090), label, font=font(F_TITLE, 44), fill=INK)

    elif idx == 3:
        title(img, ["17 个角色"], 210)
        keys = ["arrow", "ibeam", "hand", "wait", "no", "sizeall",
                "help", "crosshair", "uparrow", "sizenwse", "pin", "person",
                "appstarting", "nwpen", "sizens", "sizewe", "sizenesw"]
        cell, pad = 150, 18
        cols = 6
        for i, k in enumerate(keys):
            r, c = divmod(i, cols)
            x = 60 + c * (cell + pad)
            y = 620 + r * (cell + pad)
            tile = Image.new("RGBA", (cell, cell), (38, 42, 52, 255))
            tile.alpha_composite(art(k, cell))
            img.alpha_composite(tile, (x, y))

    elif idx == 4:
        title(img, ["改了 4 版"], 210)
        card(img, [70, 620, 520, 1240])
        d.text((150, 670), "第 1 版", font=font(F_TITLE, 42), fill=MUT)
        d.text((150, 740), "像素风 ×", font=font(F_TITLE, 54), fill=(150, 150, 160))
        d.text((150, 880), "太硬、太糊", font=font(F_BODY, 38), fill=MUT)
        card(img, [560, 620, 1010, 1240], fill=(30, 24, 32, 235), outline=ACCENT)
        d.text((640, 670), "第 4 版", font=font(F_TITLE, 42), fill=ACCENT)
        pic = art("person", 330)
        img.alpha_composite(pic, (620, 740))
        d.text((640, 1130), "卡通风 √", font=font(F_TITLE, 46), fill=INK)

    elif idx == 5:
        title(img, ["冷知识"], 210)
        d.text((W / 2 - d.textlength("指针不是普通图片", font=font(F_TITLE, 56)) / 2, 320),
               "指针不是普通图片", font=font(F_TITLE, 56), fill=CYAN)
        # 三层尺寸叠放
        for i, (sz, name) in enumerate(((300, "64"), (220, "48"), (150, "32"))):
            box = [W / 2 - sz / 2 + i * 90, 640 + i * 90, W / 2 + sz / 2 + i * 90, 640 + sz + i * 90]
            ImageDraw.Draw(img).rounded_rectangle(box, radius=18, outline=(90, 96, 112), width=3,
                                                  fill=(26, 30, 40, 210))
            d.text((box[0] + 14, box[1] + 10), name + "px", font=font(F_BODY, 30), fill=MUT)
        # 点击点
        px, py = W / 2 - 150 + 26, 640 + 26
        d.ellipse([px - 12, py - 12, px + 12, py + 12], fill=(255, 80, 90))
        d.text((px + 24, py - 20), "点击点", font=font(F_TITLE, 36), fill=(255, 120, 128))

    elif idx == 6:
        title(img, ["一条命令"], 210)
        card(img, [90, 640, 990, 980], fill=(12, 14, 18, 245))
        d.text((140, 700), "> python -m cursorlab.build", font=font(F_BODY, 44), fill=(150, 240, 180))
        d.text((140, 780), "cartoon-cat  17 个文件  1.3 MB", font=font(F_BODY, 38), fill=MUT)
        d.text((140, 850), "zip: cartoon-cat.zip", font=font(F_BODY, 38), fill=MUT)
        for i, t in enumerate(["github.com/eute000/cursor-lab",
                               "Release v2.1.0",
                               "在线预览页可直接试"]):
            d.text((140, 1080 + i * 80), "· " + t, font=font(F_BODY, 40), fill=INK)

    else:
        title(img, ["从想法到上线"], 210)
        paste_center(img, art("person", 620), 950)
        d.text((W / 2 - d.textlength("我只负责说：我想要什么", font=font(F_TITLE, 54)) / 2, 1400),
               "我只负责说：我想要什么", font=font(F_TITLE, 54), fill=ACCENT)

    subtitle(img, sub)
    return img.convert("RGB")


def dur(path):
    out = subprocess.check_output([FP, "-v", "error", "-show_entries", "format=duration",
                                   "-of", "default=nw=1:nk=1", path], text=True).strip()
    return float(out)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("FAILED:", " ".join(cmd)[:160])
        print(r.stderr[-1200:])
        raise SystemExit(1)


def main():
    os.makedirs(WORK, exist_ok=True)
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
    vos = [os.path.join(WORK, "vo%d.mp3" % (i + 1)) for i in range(len(subs))]
    for p in vos:
        if not os.path.exists(p):
            raise SystemExit("缺少配音：%s（先跑 voice_tts）" % p)

    durs = [dur(p) for p in vos]

    # 1) 出画面
    for i, s in enumerate(subs):
        render_scene(i, s).save(os.path.join(WORK, "s%02d.png" % (i + 1)))
    print("画面帧 OK")

    # 2) 每段做轻微推近，再拼
    clips = []
    for i, d0 in enumerate(durs):
        total = d0 + GAP
        src = os.path.join(WORK, "s%02d.png" % (i + 1))
        clip = os.path.join(WORK, "c%02d.mp4" % (i + 1))
        # d=1：每个输入帧出 1 帧，靠 zoom+ 逐帧递增做推近（d=frames 会让时长翻几十倍）
        vf = ("scale=1242:2208,zoompan=z='min(zoom+0.00045,1.07)':x='iw/2-(iw/zoom/2)':"
              "y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=%d,format=yuv420p" % FPS)
        run([FF, "-y", "-loop", "1", "-i", src, "-t", "%.2f" % total,
             "-vf", vf, "-r", str(FPS), "-c:v", "libx264", "-preset", "ultrafast",
             "-crf", "23", clip])
        clips.append(clip)
        print("  段 %d: %.1fs" % (i + 1, total))

    # 3) 拼视频
    lst = os.path.join(WORK, "video.txt")
    with open(lst, "w", encoding="utf-8") as fh:
        for c in clips:
            fh.write("file '%s'\n" % c.replace("\\", "/"))
    silent = os.path.join(WORK, "v.mp4")
    run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent])

    # 4) 拼配音（句间留白）
    sil = os.path.join(WORK, "sil.mp3")
    if not os.path.exists(sil):
        run([FF, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
             "-t", "%.2f" % GAP, "-c:a", "libmp3lame", sil])
    alst = os.path.join(WORK, "audio.txt")
    with open(alst, "w", encoding="utf-8") as fh:
        for i, p in enumerate(vos):
            fh.write("file '%s'\n" % p.replace("\\", "/"))
            fh.write("file '%s'\n" % sil.replace("\\", "/"))
    a = os.path.join(WORK, "a.mp3")
    run([FF, "-y", "-f", "concat", "-safe", "0", "-i", alst, "-c", "copy", a])

    # 5) 合流
    run([FF, "-y", "-i", silent, "-i", a, "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
         "-shortest", OUT])
    total = dur(OUT)
    print("\n完成: %s" % OUT)
    print("时长 %.1f 秒 / %d 帧 / 1080x1920" % (total, int(total * FPS)))


if __name__ == "__main__":
    main()
