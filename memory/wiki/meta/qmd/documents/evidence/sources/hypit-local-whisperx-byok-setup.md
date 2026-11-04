---
type: source
title: Hypit 拒绝 HypiHub：本地 WhisperX 全配置链（镜像/BUSY/超时三坑）
status: insight
category: bugfix
created: 2026-09-30
updated: 2026-09-30
slug: hypit-local-whisperx-byok-setup
---

# Hypit 拒绝 HypiHub：本地 WhisperX 全配置链（镜像/BUSY/超时三坑）

## 用户要求

不用 HypiHub 托管，用自己的模型/本地能力。落地方式=**本地 WhisperX Provider**（词对齐零费用），已实测出词级时间戳。

## Profile 配置片段（hypit.runtime.json，实测可用）

```json
"endpoints": {
  "whisperx.local": {
    "use": "@hypit/provider-whisperx-local",
    "config": { "expectedModel": "small", "expectedDevice": "cpu", "expectedCompute": "int8", "alignmentLanguages": ["zh"] }
  }
},
"bindings": { "@hypit/whisperx@1#whisperx-alignment": "whisperx.local" }
```
binding 把词对齐能力从 hypihub.default 挪到本地。生成模型（seedance）无本地替代（4GB 显存不够），profile 保留 hypihub 条目但 demo 不依赖。

## 三个坑与解法

1. **HF 下载被墙**：`programs prepare` 报 LocalEntryNotFoundError → 官方文档支持 `HF_ENDPOINT=https://hf-mirror.com npx @hypit/hypit programs prepare --endpoint whisperx.local`（环境变量作用域到准备命令）→ 成功拉 small + zh 对齐模型
2. **BUSY 503**：前一个长请求（796s音频）还在执行时再 transcribe 报 `{"code":"BUSY"}` → `programs down/up --endpoint whisperx.local` 清场
3. **CLI fetch failed**：CPU 跑13分钟音频太慢，CLI 等待超时断开（服务端仍在算但结果无人收）→ 用 `media cut --start 0 --end 15` 截短音频验证；长音频需升 cuda（expectedDevice 待试）或接受慢

## 实测证据

`transcribe voice15s.wav --language zh` → `✓ 73 words in 1 passage over 15s` → transcript.json（format hypit.transcript@1）：每词 `{text, start_seconds, end_seconds, score}`，崩老头口播内容正确、置信度 0.83-1.0。**全部 `local, no Provider charge`**。

## 链路全景（hypit in content-creator 语境）

素材音频 → hypit transcribe（本地whisperx）→ 词级时间戳 → SVML `<script>` 词锚（@{范围}/||交接）→ caption/B-roll 挂锚 → render（hyperframes本地）。文本 LLM（mimo）产文案、hypit 产词锚与渲染——职责清晰。

相关：[[hypit-integration-first-light]]

*Category: bugfix*

---
*Captured: 2026-09-30*

## Related

_Add links to related pages._
