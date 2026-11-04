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

## 🚀 异地运行

```bash
git clone git@github.com:DHcurry/pipeline-showcase.git
cd pipeline-showcase
python bootstrap.py          # 体检环境 + 交互式生成 env 配置 + 起服务
# → http://127.0.0.1:8787
```

**必填配置**（bootstrap 会引导）：
| 文件 | 来源 |
|---|---|
| `daily-movie/site.env` | 资源站账号（复制 config/*.example） |
| `daily-movie/qbwebui.env` | qBittorrent WebUI 地址/账号 |
| `~/.pi/agent/auth.json` | DeepSeek 等模型 key（**永不入库**） |

**可选**：qBittorrent + ffmpeg + faster-whisper(GPU) 才能跑完整管线；仅演示模式（`pipeline-showcase/` 部分）零依赖。

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
