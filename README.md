<div align="center">

# 🐾 CursorLab · 鼠标指针工坊

**黑猫像素风 Windows 鼠标指针包 + 一套「任意素材 → 指针包」的流水线**

从像素设计、`.cur`/`.ani` 二进制编码，到用户级安装脚本，全部自己写，不依赖第三方指针工具。

![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078d4?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c55e)
![Deps](https://img.shields.io/badge/Deps-Pillow_only-ffb300)

<img src="preview.png" width="880" alt="CursorLab 像素小猫指针预览">

</div>

## 这包指针长什么样

黑猫头当箭头、猫爪肉垫当链接光标、眼睛尽量放大、耳朵支棱着，边缘统一加 1px 白边 —— 暗色桌面上也看得清。

| 场景 | 造型 | 文件 |
|---|---|---|
| 正常指向 | 黑猫头 + 卷尾 | `arrow.cur` |
| 悬停链接 | 猫爪肉垫 | `hand.cur` |
| 文本输入 | I 型杆 + 粉肉垫 | `ibeam.cur` |
| 系统忙 | 猫爪 + 转圈小星星（8 帧动画） | `wait.ani` |
| 后台启动 | 猫头 + 转圈小星星（8 帧动画） | `appstarting.ani` |
| 十字定位 | 加号 + 粉肉垫 | `crosshair.cur` |
| 禁止 | 带猫耳的禁行牌 | `no.cur` |
| 上下 / 左右 / 斜向 / 四向拖动 | 双头箭头 + 粉肉垫 | `sizens/sizewe/sizenwse/sizenesw/sizeall.cur` |
| 向上箭头 | 猫耳箭头 | `uparrow.cur` |
| 手写笔 | 猫爪笔 | `nwpen.cur` |
| 帮助 | 猫头 + 问号气泡 | `help.cur` |
| 定位图钉 | 猫爪图钉 | `pin.cur` |
| 用户 | 猫猫头像 | `person.cur` |

## 装到自己电脑上

**方式一：仓库内直接装（推荐自己用）**

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

**方式二：发行包（发给朋友用）**

1. 下载 [Releases](../../releases) 里的 `pixel-cat.zip`
2. 解压，双击 `安装.bat`

两种方式都**不需要管理员权限**（只动 `HKCU\Control Panel\Cursors`），安装前会自动把原设置备份成 `backup-cursors.json`。

**还原**

```powershell
powershell -ExecutionPolicy Bypass -File uninstall.ps1
```

装好后在 `设置 → 蓝牙和其他设备 → 鼠标 → 其他鼠标设置 → 指针` 里，主题下拉框能看到 `CursorLab pixel-cat`，可以随时切回 Windows 默认。

## 自己定制一套（重点）

任何风格都能做成指针包 —— 二次元、AI 生成、自己画的、表情包截图都行。

### 1. 准备素材

17 张 png，按角色名命名（`arrow.png`、`hand.png`、`ibeam.png` …），丢进一个文件夹：

```
assets/anime-cat/
├── arrow.png        # 正常指向
├── hand.png         # 链接手型
├── ibeam.png
├── wait_0.png       # 动画：按 wait_0 ~ wait_7 命名即自动识别
├── wait_1.png
├── ...
└── person.png
```

### 2. 一条命令生成主题

```powershell
python tools/make_theme.py --name anime-cat --src assets/anime-cat
```

它会自动：按角色命名识别素材 → 抠掉纯色背景 → 加 1px 白描边 → 生成多尺寸（32/48/64）→ 打包成 `dist/anime-cat.zip`。

### 3. 校准点击位置（热点）

打开 `tools/hotspot.html`，把路径指到 `out/anime-cat/png/`，在每张图上点一下"点击生效点"，复制生成的 JSON 回填到 `themes/anime-cat/theme.json` 的 `hot` 字段，再构建一次。

> 热点不准的表现：点按钮时图标"偏一格"。箭头类在尖端，手型在中指，禁止类在圆心。

### 4. 装上去

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1 -Dir out\anime-cat -Name "Anime Cat"
```

`theme.json` 支持这些开关：

| 字段 | 说明 |
|---|---|
| `sizes` | 每张 `.cur` 里塞几种尺寸，默认 `[32, 48]` |
| `outline` | 自动加白描边（暗色桌面更容易看见） |
| `cut_background` | 自动抠掉纯色背景 |
| `delay_ms` | 动画帧间隔，默认 90ms |
| `roles.<角色>.hot` | 热点坐标，按 32 格网格记 |
| `roles.<角色>.frames` | 多帧图片列表（顺序即播放顺序） |

## 技术笔记（这个项目真正值得练的部分）

<details>
<summary><b>.cur 里只能放 DIB 位图，放 PNG 就是坏文件</b></summary>

`.ico` 从 Vista 起支持 PNG 压缩帧，`.cur` 不支持。而 Pillow 的 ICO 写入器在尺寸 ≥ 64 时会自动改用 PNG —— 直接改文件头当 `.cur` 用，Windows 加载会失败。

所以这里自己实现了 `dib32()`：BITMAPINFOHEADER（高度写 `2*h`，上半 XOR 颜色、下半 AND 透明掩码）+ 自下而上的 BGRA 数据。
</details>

<details>
<summary><b>热点藏在目录项的 planes / bitCount 字段里</b></summary>

`.cur` 的目录项结构和 `.ico` 一样，只是 `wPlanes` / `wBitCount` 两个字段被挪用存热点 `<x, y>`（而且是按整个文件的类型位标 2 判断，不是靠扩展名）。
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
    └── ...
```
</details>

<details>
<summary><b>PowerShell 5.1 的两个坑（都踩了）</b></summary>

1. `.ps1` 文件没有 UTF-8 BOM 时按 ANSI 读，中文注释会把引号吃掉 → 整个脚本语法错误。写脚本一律 `UTF8Encoding($true)`。
2. `Get-Item HKCU:\...` 返回的注册表键是**只读**打开的，直接 `.SetValue()` 会抛「无法写入到注册表项」。要用 `[Microsoft.Win32.Registry]::CurrentUser.OpenSubKey($path, $true)` 或 `CreateSubKey()`。
3. 注册表「默认值」的名字是**空字符串**，`ConvertFrom-Json` 遇到空属性名会直接报「参数 name 的值无效」。备份时改存成 `__default__`，读的时候用 `JavaScriptSerializer` 更保险（它返回字典，能容纳空键）。
</details>

## 目录结构

```
cursorlab/            核心库
├── encode.py         .cur / .ani 二进制编码（DIB、热点、RIFF）
├── pixel.py          32×32 像素画布（逐像素、1px 外描边、调色板）
├── shapes.py         指针/箭头/双箭头的像素实现
├── cat.py            像素小猫 17 个造型 + 热点 + 动画帧
└── build.py          主题构建、预览图、zip 打包
tools/
├── make_theme.py     任意 png → 主题（抠图/描边/多尺寸/打包）
├── hotspot.html      点点鼠标标热点，导出 JSON
└── ascii_dump.py     把造型打成字符阵，逐像素调
themes/               图片主题（themes/<名>/theme.json + png）
install.ps1           安装（写 HKCU + 立即生效 + 自动备份）
uninstall.ps1         还原
tests/test_encode.py  编码器自测（CI 里跑）
```

构建全部主题：

```powershell
python -m cursorlab.build
```

## 已知限制 / 下一步

- [ ] 高 DPI 只做到 64px（再大要靠 Windows 缩放）
- [ ] 只有 Windows；macOS 需要 `.cur` 之外的格式，暂不支持
- [ ] 主题切换器 GUI（现在是命令行 `-Dir`）
- [ ] 二次元素材示例包（用 AI 出图的完整案例）

## License

[MIT](LICENSE) · 像素造型可随意改，欢迎提 PR 加主题。
