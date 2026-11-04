---
name: "llm-output-robustness"
description: "LLM 输出健壮性处理：JSON 修复、禁降级、前后端同步的项目原则"
version: 1
created: "2026-09-27"
updated: "2026-09-28"
---
## When to Use
在 content-creator-workspace 及类似项目中处理 LLM 返回 JSON、超时、字段解析时。

## Procedure
1. 未配置 LLM → 按钮 disabled + 提示去配置页；已配置 → 必须真调 LLM，失败直接抛错，严禁静默降级假数据/规则回退模板。
2. 后端 ai.ts 统一防御：extractJSON 容错提取 + repairTruncatedJson 修复器（补齐括号、纠正键值类型、闭合未关数组，splice 插入位置须在 key 字符串开始前）+ 解析失败自动重试一次 + extractAndNormalize 保证 rhythm_analysis/highlights/oral_score_detail 等嵌套字段恒存在。
3. LLM 常见失败：字符串内裸换行、截断在结构中间（4096 token 不够 → maxTokens 全部提到 8192）、漏/写错括号（对象闭合写成 ]、数组未闭合）、超时（mimo 120s 被掐断致 500 → AI 调用超时 ≥300s，长任务返回 processing+前端轮询不阻塞）。
4. 路由层禁止白名单裁剪重建 LLM 结果（曾丢 hook/outline/style_profile）。
5. 前端：嵌套字段一律 ?.；fetch 先 res.text() 再防御 JSON.parse；纯文本输出直接 raw.trim()，仅结构化消费才要求 JSON；前后端改字段必须同步；只留非流式端点。
6. React onClick={handler} 会把 MouseEvent 当首参 → 用 ()=>handler()；TS 字符串内控制字符用 charCodeAt(0)===10 判断，不用字面量换行。
7. 用真实失败样本 dump 做单元验证。

## Pitfalls
- 静默降级假数据是用户明令禁止的行为。
- 4096 token 截断 JSON 很常见，必须有修复+重试。

## Verification
1. 用真实失败样本验证 extractJSON/repairTruncatedJson；断网或错误 key 时前端显示明确错误而非假数据。