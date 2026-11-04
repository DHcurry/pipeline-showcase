---
name: "llm-standup-subtitle-translation"
description: "daily-movie 字幕 LLM 意译管线（DeepSeek脱口秀人设）：机翻质量问题处置全流程"
version: 2
created: "2026-10-27"
updated: "2026-10-29"
---
## When to Use
用户反馈字幕是机翻/笑点丢失时；新片为脱口秀、音乐演出且用户要求高质量字幕时。脚本在 C:/Users/16575/daily-movie/llm_translate.py，凭证读 ~/.pi/agent/auth.json 的 deepseek 键。

## Procedure
1. 确认问题：机翻腔/笑点丢失，对照英文源抽样
2. 英文源优先级：发行版捆绑 .en.srt > 内嵌英文轨提取（ffmpeg -map 0:s:0）> Whisper 转写
3. python -X utf8 llm_translate.py <en.srt> --persona=standup（conçert/generic 另可选）；分块40条+块数100%校验+失败块保底标记
4. 抽验5组对照确认口语节奏与笑点保留
5. 顶替中文 srt（.extracted.srt 或主 srt）+ subtitles.json 台账 lang 改 zh-llm-standup
6. 删对应 .ext.mp4 触发 append_footage 重建（产物缺失重建通道已内建）

## Pitfalls
- 弹幕/评论引导等互动文案是平台页面层内容（简介/置顶评论/封面），严禁混入 srt 字幕——用户2026-10-29明确纠正过；应单独产出《平台互动文案.txt》放在片目录
- SubtitleCat 抓取三闸门：英文停用词比例体检(纯ASCII挡不住西语葡语)、候选相关度>=0.35、同步闸门反向对表>=60%
- normalize_srt 必须以双换行连接块（单\n会导致解析塌缩成1块）；批量替换后先断言块数再顶替
## Verification
1. llm_translate 断言块数一致
2. 抽样对照无机翻腔
3. append 重建日志显示含字幕烧录