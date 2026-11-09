# 🎬 Pipeline Command Center — 全栈部署包

> 每日电影自动化内容管线的**完整逻辑 + 记忆 + 对话**部署——clone 即可在异地还原同一套系统与大脑。由 **Pi Agent SDK** 驱动。

![stage](https://img.shields.io/badge/stage-demo-blue) ![pi](https://img.shields.io/badge/power-Pi%20Agent%20SDK-purple) ![py](https://img.shields.io/badge/zero--dependency-python-green)

## 📦 仓库结构

```
pipeline-showcase/
├── index.html            # 炫酷演示指挥台(流水灯/日志流/Pi问答/合集矩阵)
├── server.py             # 零依赖服务: 真实台账聚合 + SSE + pi -p 流式问答
├── bootstrap.py          # 一键引导: 环境体检 → 配置向导 → 起服务
├── pipeline/             # ★ 管线全逻辑 (51个脚本: 选片/下载/转写/意译/封面/拼接/合集)
│   └── loops.json        # 自动化循环调度配置快照 (4循环: 选片×2/后处理/拼接)
├── config/
│   ├── site.env.example  # 资源站账号模板 (复制为 site.env 填真实值)
│   └── qbwebui.env.example  # qBittorrent WebUI 模板
├── memory/               # ★ 大脑记忆
│   ├── skills/           # 程序性技能 (SKILL.md 全集: 管线坑/翻译方案/调试流程)
│   ├── wiki/             # 知识库 (672页: 观察/概念/来源, LLM Wiki 全量)
│   └── MEMORY.md         # 记忆导出 (偏好/纠正/环境事实)
├── conversations/        # ★ 对话快照 (131个会话文本化导出)
│   └── conversations.md
└── data/                 # 台账样例 (history/append/collections/subtitles/site_catalog)
```

## 🚀 在任何电脑上运行（三步开箱即用）

**前置**：安装 [Python 3.9+](https://www.python.org/downloads/)（安装时勾选 **Add python.exe to PATH**）。无需 qB/ffmpeg/GPU——演示模式零依赖。

```
方式A（Windows）：双击  start.bat          ← 自动找 py/python 启动，报错不闪退
方式B（任意平台）：python server.py        ← 端口被占自动顺延 8787→8791
可选引导：python bootstrap.py              ← 环境体检 + 配置向导
```

启动后打开终端显示的地址（默认 **http://127.0.0.1:8787**）。

**异地自动演示模式**：仓库内没有本机管线时，`data/` 快照自动接管（77部作品/50条拼接/8合集 等真实导出数据），页面照常全量展示；连上真实管线时自动切【真实台账模式】。

| 环境变量 | 作用 | 缺省 |
|---|---|---|
| `PORT` | 服务端口 | 8787（被占自动+1至8791） |
| `PIPELINE_DIR` | 指向真实 daily-movie 目录 | 自动探测本机路径→否则 data/ 快照 |

**故障排查**：
- 窗口一闪而过 → 用方式A，或在仓库目录打开 CMD 运行 `python server.py` 看报错
- 找不到 python → 安装并勾选 Add to PATH（或用 `py -3 server.py`）
- 端口占用 → 服务会自动顺延；也可 `set PORT=9000 && python server.py`
- 问答面板无回复 → 需本机装有 `pi` CLI（Pi Agent SDK），仅演示可忽略

## 🧠 Pi Agent SDK 角色

- **决策大脑**：`pi -p` 非交互调用——演示面板实时流式问答
- **调度**：Pi Loop 四循环（午间选片/晚间选片/后处理/风景拼接）
- **记忆**：`memory/` + `conversations/` ——技能、知识库、偏好与历史对话完整随仓

## ✨ 演示特性

- 七阶段流水灯（选片⚡→下载📦→转写🎙→意译🌐→封面🎨→拼接🔥→交付✅）
- 真实台账统计（作品数/总时长/字幕块/LLM量/合集分布）
- SSE 实时日志流（真实日志 tail + 事件注入）
- 合集矩阵（品类轴 + 交叉视角轴，待创建/已创建状态）
- Pi 大脑问答（POST /api/ask → pi -p 流式输出）

## 🔌 API

- `GET /api/stats` — 聚合统计
- `GET /api/stream` — SSE 日志流
- `POST /api/ask {"q":"..."}` — Pi Agent 流式问答

## 🔐 安全红线

- **密钥零入库**：auth/env 真实值只在本机，仓库仅含 `.example` 模板（导出脚本自动扫描 `sk-`/`ghp_`/密码模式并剔除）
- 台账 JSON 不含凭据；视频大文件不入库；`.pi/` 会话状态已 gitignore

## 🗂 内容合集体系

🎭 音乐剧·舞台经典 · 🎤 演唱会·现场直击 · 😂 脱口秀·爆笑专场 · 🎬 动画·合家欢 · 🇨🇳 国产精选 · 🎥 纪录片·真实人生 · 🎸 高能音浪·摇滚现场（交叉） · 😄 轻松下饭·笑着看（交叉）
