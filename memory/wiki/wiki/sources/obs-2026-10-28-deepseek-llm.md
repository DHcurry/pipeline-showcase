---
type: source
title: "Observation: 字幕主链切换 DeepSeek LLM 意译（脱口秀人设+机翻兜底）"
tags:
  - daily-movie
  - 字幕翻译
  - LLM
  - deepseek
  - 脱口秀
  - 主链切换
status: observation
created: 2026-10-28
updated: 2026-10-28
slug: obs-2026-10-28-deepseek-llm
relevance: high
observed_at: 2026-10-28T10:52:40.762Z
source_context: daily-movie 字幕管线 LLM 意译主链切换
---

# ⭐ Observation: 字幕主链切换 DeepSeek LLM 意译（脱口秀人设+机翻兜底）

daily-movie 字幕翻译主链已切换为 LLM 意译（2026-10-28 用户指令"后续机翻统一用这个模式"）。实现：llm_translate.py 用 pi auth.json 的 deepseek 凭证调 DeepSeek chat，分块40条+块数100%校验+失败块>10%整体回退机翻链；translate_srt.translate_file 在备份后插入 LLM 优先路径（人设自动判定：片名含脱口秀词→standup、演唱会词→concert、其他→generic），台账 zh_engine 标注 deepseek-llm/<persona>。实测50块4秒、1238块脱口秀专场全量直译。两个坑已修：写回游标错用块号索引批次数组（IndexError→回退机翻，已改按批次顺序消费行游标）；测试时间戳缺秒段被 BLOCK_RE 拒（解析器无错）。产物级案例：Taylor Tomlinson《Prodigal Daughter》从机翻重制为 DeepSeek 脱口秀人设意译1283块，抽验口语节奏/包袱保留良好，重建 ext 烧录。配套技能 global:llm-standup-subtitle-translation。

*Relevance: high*
*Context: daily-movie 字幕管线 LLM 意译主链切换*
*Tags: daily-movie 字幕翻译 LLM deepseek 脱口秀 主链切换*

---
*Observed: 2026-10-28T10:52:40.762Z*
