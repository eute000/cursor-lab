<div align="center">

# 🐾 CursorLab · 卡通小黑猫鼠标指针

**一只大头黑猫 + 两只超大白眼睛的 Windows 指针包**，外加一套「任意图片 → 指针包」的流水线

从造型绘制、`.cur`/`.ani` 二进制编码，到用户级安装脚本，全部自己写，不依赖第三方指针工具。

![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078d4?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c55e)
![Deps](https://img.shields.io/badge/Deps-Pillow_only-ffb300)

<img src="preview.png" width="880" alt="CursorLab 卡通小黑猫预览">

</div>

## 造型

黑身、棕黑描边、外套一圈 1px 米白（任何壁纸上都不糊）；两只超大白眼睛几乎占满脸，各自一颗黑瞳加高光；小身体缩在头下露出两只圆爪，尾巴细长微卷。

指针方向靠左上角一枚**空心小三角 ▷** 交代，尖端就是点击点。

| 场景 | 造型 | 文件 |
|---|---|---|
| 正常指向 | ▷ + 黑猫（猫在右下） | `arrow.cur` |
| 帮助 | 空心圆 + 大问号 | `help.cur` |
| 后台启动 | ▷ + 黑猫 + 小转圈 | `appstarting.ani` |
| 系统忙 | 黑猫 + 外圈旋转箭头（8 帧） | `wait.ani` |
| 文本输入 | 细 I 型杆 | `ibeam.cur` |
| 十字定位 | 细十字 + 中心点 | `crosshair.cur` |
| 悬停链接 | 猫爪印（肉垫镂空） | `hand.cur` |
| 禁止 | 小红黑猫 + 红色禁行符 | `no.cur` |
| 上下 / 左右 / 斜向 / 四向 | 双头箭头 | `sizens/sizewe/sizenwse/sizenesw/sizeall.cur` |
| 向上 | 上箭头 | `uparrow.cur` |
| 手写笔 | 笔 + 粉色握笔环 | `nwpen.cur` |
| 定位图钉 | 图钉（中间镂空） | `pin.cur` |
| 用户 | 大号黑猫全身 | `person.cur` |

## 装到自己电脑上

**方式一：仓库内直接装**

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

**方式二：发行包（发给朋友）**

1. 下载 [Releases](../../releases) 里的 `cartoon-cat.zip`
2. 解压，双击 `安装.bat`

两种方式都**不需要管理员权限**（只动 `HKCU\Control Panel\Cursors`），安装前自动把原设置备份成 `backup-cursors.json`。

**还原**

```powershell
powershell -ExecutionPolicy Bypass -File uninstall.ps1
```

装好后在 `设置 → 蓝牙和其他设备 → 鼠标 → 其他鼠标设置 → 指针`，主题下拉里能看到 `CursorLab cartoon-cat`。

## 点击特效（可选，需要一个小助手）

Windows 的光标没有"按下"状态，`.cur/.ani` 是死的。这个小助手会在按住鼠标时把系统光标临时换成"握爪/眯眼"那一帧，松开立刻恢复：

| 场景 | 平时 | 按住时 |
|---|---|---|
| 桌面箭头 | 静止 | 猫低头 + 眯眼 + 握爪 |
| 文本 I 型 | 静止 | I 加粗下沉 + 猫眯眼 |
| 链接手型 | 静止爪印 | 趾垫收拢 + 掌垫放大（握紧）|

**用法**

- 立刻试：双击 `start_hidden.bat`（后台无窗口运行）
- 开机自启：双击 `开机自启-设置.bat` → 之后登录就自动在后台跑，**没有任何窗口**
- 取消自启：双击 `开机自启-取消.bat`（同时结束进程并恢复指针）

关闭任何窗口都不影响自启版本——它跑在无窗口的 `pythonw` 里。原理见 `tools/click_fx.py`：30ms 轮询 `GetAsyncKeyState`，按住期间每 40ms 用 `SetSystemCursor` 压一次（否则会被窗口的光标覆盖），松开 `SPI_SETCURSORS` 恢复，`finally + atexit` 双保险。

## 自己定制一套

任何风格都能做：二次元、AI 生成、自己画的、截图都行。

**1. 准备素材** —— 17 张 png 按角色名命名（`arrow.png`、`hand.png`…），丢进一个文件夹：

```
assets/my-cat/
├── arrow.png
├── hand.png
├── wait_0.png   # 动画按 wait_0 ~ wait_7 命名即自动识别
├── wait_1.png
└── person.png
```

**2. 一条命令生成**

```powershell
python tools/make_theme.py --name my-cat --src assets/my-cat
```

自动抠纯色背景、加 1px 白描边、生成多尺寸（32/48/64）、打包成 `dist/my-cat.zip`。
装好包以后也可以直接 `cursorlab-theme --name my-cat --src assets/my-cat`（同一条命令）。

> 动画帧按**数字顺序**排：`wait_2.png` 排在 `wait_10.png` 前面（不是按字符串排）。

**3. 校准点击位置（热点）** —— 打开 `tools/hotspot.html`，指到 `out/my-cat/png/`，每张图点一下"点击生效点"，把导出的 JSON 贴回 `themes/my-cat/theme.json` 的 `hot`。
也可以在生成时直接给：`--hot arrow=2,2 hand=16,10.4`（坐标按 32 格设计网格记，越界会直接报错）。

**3.5 体检一下再装**（可选，但建议）

```powershell
python -m cursorlab.verify out/my-cat
```

它会逐个字节检查 `.cur` / `.ani`：目录项长度、DIB 头、热点是否落在图像内、
RIFF 长度、`anih` 的帧数/步数与实际 `icon` 块是否对得上。有问题退出码 1，
直接接在 CI 里：`python -m cursorlab.build --verify`。

**4. 装上去**

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1 -Dir out\my-cat -Name "My Cat"
```

`theme.json` 支持的开关：

| 字段 | 说明 |
|---|---|
| `sizes` | 每张 `.cur` 里塞几种尺寸，默认 `[32, 48]` |
| `outline` | 自动加白描边（暗色桌面更容易看见） |
| `cut_background` | 自动抠掉纯色背景 |
| `delay_ms` | 动画帧间隔，默认 90ms |
| `roles.<角色>.hot` | 热点坐标，按 32 格网格记 |
| `roles.<角色>.frames` | 多帧图片列表（顺序即播放顺序） |

## 技术笔记

<details>
<summary><b>.cur 里只能放 DIB 位图，放 PNG 就是坏文件</b></summary>

`.ico` 从 Vista 起支持 PNG 压缩帧，`.cur` 不支持。而 Pillow 的 ICO 写入器在尺寸 ≥ 64 时会自动改用 PNG —— 直接把文件头改成 2 当 `.cur` 用，Windows 会加载失败。

所以自己实现了 `dib32()`：BITMAPINFOHEADER（高度写 `2*h`，上半 XOR 颜色、下半 AND 透明掩码）+ 自下而上的 BGRA。
</details>

<details>
<summary><b>热点藏在目录项的 planes / bitCount 字段里</b></summary>

`.cur` 的目录项结构和 `.ico` 一样，只是 `wPlanes` / `wBitCount` 被挪用存热点 `<x, y>`（判定类型靠文件头里的 type=2，不是扩展名）。
</details>

<details>
<summary><b>.ani 是 RIFF/ACON 容器</b></summary>

```
RIFF <size> ACON
├── anih  36 字节头：帧数、步数、默认速率(jiffies, 1/60 秒)、flags=1
├── rate  每帧速率
├── seq   播放顺序
└── LIST <size> fram
    ├── icon <size> 一帧 .cur 的完整字节
    └── ...（块长度为奇数时补 0 对齐）
```
</details>

<details>
<summary><b>卡通造型塞进 32px 的三个技法</b></summary>

1. **每档尺寸单独绘制 + 8 倍超采样后 LANCZOS 缩小** —— 直接缩会糊，先画大再缩才有平滑边缘
2. **每个元素单独成层、单独加外描边** —— 猫脸、身体、指针三角各画一层，各自膨胀 alpha 再缩小；否则元素会粘成一坨
3. **点阵 spinner 在小尺寸会糊成斑块** —— 改用旋转圆弧（arc + 两端圆点）才清晰

膨胀 alpha 用「高斯模糊后阈值」而**不是**大核 MaxFilter：35×35 的 rank filter 跑 17 个造型 × 3 档尺寸要几分钟，高斯只要 2 秒。
</details>

<details>
<summary><b>PowerShell 5.1 的三个坑（都踩了）</b></summary>

1. `.ps1` 没有 UTF-8 BOM 时按 ANSI 读，中文注释会把引号吃掉 → 整个脚本语法错误。
2. `Get-Item HKCU:\...` 返回的键是**只读**打开的，`.SetValue()` 会抛「无法写入到注册表项」，要用 `[Microsoft.Win32.Registry]::CurrentUser.OpenSubKey($path, $true)`。
3. 注册表「默认值」的名字是**空字符串**，`ConvertFrom-Json` 遇到空属性名直接报错；备份时改存 `__default__`，读取用 `JavaScriptSerializer`。
</details>

<details>
<summary><b>抠背景不能"见到接近白就抠"，要从四条边泛洪</b></summary>

最早的写法是遍历所有像素：颜色接近背景色就设成透明。白底素材里猫的白眼睛、
高光、镂空跟背景色一模一样，于是被一起抠穿 —— 装到深色壁纸上就是一个透明的洞。

现在先做一张"接近背景色"的二值图，只从画布边缘泛洪，被连通到的才算背景；
图像内部的同色区域一律保留。
</details>

<details>
<summary><b>编码器不会自己发现坏文件，所以单独写了 verify</b></summary>

`cur_bytes()` / `ani_bytes()` 只负责把字节拼出来，长度算错、热点跑到图像外、
RIFF 长度差 4 个字节，它们照样安安静静返回一段 bytes。出错的表现是
"装到 Windows 上指针变成默认箭头" —— 在 Linux CI 里根本看不见。

`cursorlab.verify` 把生成的文件重新当字节读一遍（目录项、DIB 头、AND 掩码、
热点、`anih` 计数、`seq`/`rate` 长度、chunk 对齐），CI 里构建完跑一次就能拦下来。
</details>

## 目录结构

```
cursorlab/            核心库（可 pip install，三个命令行入口）
├── encode.py         .cur / .ani 二进制编码（DIB、热点、RIFF）
├── cartoon.py        卡通小黑猫 17 个造型（矢量绘制 + 超采样）
├── build.py          主题构建、预览图、zip 打包
├── theme.py          任意 png → 主题（抠图/描边/多尺寸）
├── verify.py         .cur / .ani 结构体检
└── __init__.py       公开 API + 版本号
tools/
├── make_theme.py     老入口，转调 cursorlab.theme（命令不变）
├── hotspot.html      点点鼠标标热点，导出 JSON
└── preview.py        出预览图（4 倍放大 + 1:1 真实尺寸）
themes/               图片主题（themes/<名>/theme.json + png）
docs/                 Pages 落地页 + 每轮设计稿
install.ps1           安装（写 HKCU + 立即生效 + 自动备份）
uninstall.ps1         还原
tests/                81 个用例（编码器 / 体检 / 构建 / 主题 / 造型）
```

构建全部主题：

```powershell
python -m cursorlab.build                  # 出光标 + zip
python -m cursorlab.build --list           # 看有哪些主题
python -m cursorlab.build --verify         # 构建完顺手体检，有问题退出码 1
python -m cursorlab.verify out\cartoon-cat # 单独体检一个目录或文件
```

装成包用（可选，需要有 Python 环境）：

```powershell
pip install -e ".[dev]"
cursorlab-build --verify
cursorlab-theme --name my-cat --src assets\my-cat
cursorlab-verify out\cartoon-cat
python -m pytest                           # 81 个用例，约 10 秒
```

## 版本

| 版本 | 内容 |
|---|---|
| v0.1.0 | 像素风小黑猫（已归档，仍可在 Releases 下载） |
| v2.0.0 | 卡通风重做：大头 + 超大白眼 + 分层米白描边 + 空心三角指针 |
| **v2.1.0** | 结构体检 `cursorlab.verify`、主题生成收进包里（`cursorlab-theme`）、`pyproject.toml` + 三个命令行入口、81 个用例；修掉自定义主题整条路走不通、抠背景抠穿白眼睛、动图帧按字符串排序、非正方素材被压扁、热点不校验不报错、预览图右边留白 |

## License

[MIT](LICENSE) · 造型可随意改，欢迎提 PR 加主题。
