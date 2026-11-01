# CursorLab 项目简介（可直接复制到各处）

## 一句话（社交平台 bio / 个性签名）

> 用 AI 从一个想法做到上线：自研 Windows 鼠标指针包「Cartoon Cat」——17 个角色、点击特效、开机自启，GitHub + Pages 全自动发布。

English: **Built with AI end-to-end: a hand-made Windows cursor pack — 17 roles, click effects, auto-start — shipped via GitHub Actions and Pages.**

## 三句话（GitHub repo description / 作品集条目）

> 把自己想要的鼠标指针做了出来：一只黑猫 17 个角色，32/48/64 三档尺寸、两个动画、按住时的握爪特效，全部由 Python + Pillow 从零生成，没有用任何现成指针工具。
> 顺带写了一套「任意图片 → 指针包」的流水线，和 CI/CD（构建、Release、Pages 全自动）。
> 全过程由 AI 协作完成：造型迭代、二进制编码、踩坑排查、文案与封面。

## 段落版（150–200 字，简历 / 作品集 / 项目介绍）

> **CursorLab｜Windows 鼠标指针工坊（个人项目，2026）**
> 起因是找不到称心的鼠标指针，于是自己造了一套「卡通小黑猫」：17 个 Windows 系统角色，每张 `.cur` 内含 32/48/64 三档尺寸并带正确热点，忙碌与后台启动是 8–12 帧的 `.ani` 动画；另加一个点击特效小助手——按住鼠标时，箭头会低头眯眼握爪、文本光标会加粗下沉、链接爪印会握紧，松开即恢复，并做成无窗口开机自启。
> 没有依赖任何第三方指针工具：`.cur` 的 DIB 位图 + 热点字段、`.ani` 的 RIFF/ACON 容器都是自己编码的；再往上是一套「一张图 → 整套指针」的生成流水线（自动抠底、加描边、多尺寸、打包 zip）。
> 工程化部分同样完整：GitHub Actions 自动跑单测、构建、发 Release 并部署在线预览页；成品的投稿文案、封面图与提交流程也已备齐。
> 全流程与 AI 协作完成——从参考图拆解、4 轮造型返工、尺寸按 DPI 校准，到 CI 抢部署的排障。

## English paragraph

> **CursorLab — a Windows cursor workshop (personal project, 2026)**
> A hand-built "cartoon black cat" cursor set: 17 Windows roles, each `.cur` carrying 32/48/64 px layers with correct hotspots, plus 8–12 frame `.ani` animations for busy/background states. A small click-effect helper swaps in a "squint & grip" frame while the mouse is held and restores on release — no console window, auto-starts at login.
> No third-party cursor tools: the `.cur` DIB bitmap with hotspots in the directory entry, and the `.ani` RIFF/ACON container, are encoded from scratch. On top sits a pipeline that turns any set of PNGs into a full cursor pack (background removal, outline, multi-size, zip).
> Shipped with CI/CD (unit tests, build, GitHub Release, live Pages preview) and submission-ready store copy plus cover art. Designed and iterated together with AI — from reference-image breakdown and four redesign rounds to DPI-accurate sizing and a CI deploy race.

## 要点清单（作品集里的 bullet）

- **结果**：GitHub 开源仓库 + v2.1.0 Release + 在线预览页 + 已投稿 Cursors-4U 审核
- **自研底层**：`.cur`（DIB 位图 + 热点塞进 planes/bitCount）、`.ani`（RIFF/ACON，chunk 偶数对齐）
- **生成流水线**：任意 PNG → 抠底 / 描边 / 多尺寸 / 打包，`python tools/make_theme.py`
- **动效**：常驻微动画（尾摆 + 呼吸）、按下态三槽位切换（箭头 / I 型 / 手型）
- **系统集成**：用户级注册表安装（免管理员）、一键还原、开机自启（HKCU Run + pythonw 无窗口）
- **工程化**：单测 6 项、GitHub Actions（构建 / Release / Pages）、SHA256 校验线上产物
- **踩过的坑（可讲的故事）**：`.cur` 里不能放 PNG（Pillow 会自动存 PNG → Windows 不认）、`SetSystemCursor` 会被窗口光标覆盖所以要反复压、`Get-Item` 拿到的注册表键是只读的、150% 缩放下 DPI 选层导致图标"看着偏大"

## 一句话版本对照（挑一个用）

| 场景 | 用哪版 |
|---|---|
| 社交平台简介 | 一句话 |
| GitHub repo description | 三句话 |
| 作品集 / 简历条目 | 段落版（中文或英文）|
| 面试讲项目 | 段落版 + 要点清单里的"踩过的坑" |
