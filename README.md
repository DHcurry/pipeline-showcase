# 🎬 Pipeline Command Center

> 每日电影自动化内容管线的**可演示指挥台**——选片 → 下载 → 转写 → 意译 → 封面 → 风景拼接 → 合集交付，全链无人值守。内部由 **Pi Agent SDK** 驱动决策。

![stage](https://img.shields.io/badge/stage-demo-blue) ![pi](https://img.shields.io/badge/power-Pi%20Agent%20SDK-purple) ![py](https://img.shields.io/badge/zero--dependency-python-green)

## ✨ 特性

- **实时流水线灯**：七阶段流转动画（选片⚡ → 下载📦 → 转写🎙 → 意译🌐 → 封面🎨 → 拼接🔥 → 交付✅）
- **真实数据面板**：作品数 / 总时长 / 字幕块 / LLM 意译量 / 合集分布，全部读自管线真实台账
- **SSE 日志流**：真实管线日志 tail + 事件注入，打字机式滚动，演示永远有料
- **Pi 大脑问答**：`POST /api/ask` 实时调用 `pi -p`（Pi Agent SDK CLI），流式输出——证明"本质是 pi sdk"
- **合集矩阵**：8 个内容合集（品类轴 + 交叉视角轴），待创建/已创建状态一目了然
- **零依赖**：纯 Python 标准库 HTTP + 原生 HTML/CSS/JS，无 npm / 无 pip install

## 🚀 快速开始

```bash
cd pipeline-showcase
python server.py            # 默认 http://127.0.0.1:8787
# 浏览器打开 http://127.0.0.1:8787
```

可选环境变量：`PORT=9000 python server.py`

## 🧠 Pi Agent SDK 角色

| 环节 | 实现 |
|---|---|
| 决策大脑 | `pi -p` 非交互调用（CLI 即 SDK 入口），演示面板流式展示 |
| 管线调度 | Pi Loop 定时任务驱动（选片/转写/拼接三班制） |
| 字幕意译 | DeepSeek LLM + 脱口秀人设（Pi 生态同源模型链） |
| 数据台账 | history / append / collections / subtitles 四本 JSON |

## 📁 数据源（可选）

服务自动读取真实管线台账（默认 `C:\Users\16575\daily-movie\*.json`），读不到时回退内置样例，保证演示随时可跑。

## 🔌 API

- `GET /api/stats` — 聚合统计 + 合集 + 时间线 + 阶段计数
- `GET /api/stream` — SSE 实时日志流
- `POST /api/ask {"q":"..."}` — Pi Agent 流式问答

## 🗂 内容合集体系（演示内置）

🎭 音乐剧·舞台经典 · 🎤 演唱会·现场直击 · 😂 脱口秀·爆笑专场 · 🎬 动画·合家欢 · 🇨🇳 国产精选 · 🎥 纪录片·真实人生 · 🎸 高能音浪·摇滚现场（交叉） · 😄 轻松下饭·笑着看（交叉）
