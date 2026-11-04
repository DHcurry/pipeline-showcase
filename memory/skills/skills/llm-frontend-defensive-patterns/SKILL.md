---
name: "llm-frontend-defensive-patterns"
description: "LLM JSON 输出健壮性与\"禁静默降级\"的前端防御模式"
version: 1
created: "2026-09-27"
updated: "2026-09-27"
---
## When to Use
在 content-creator-workspace 前端渲染 LLM 返回结果、或处理 fetch/JSON 解析时。

## Procedure
1. 嵌套字段一律 ?. 与 || 兜底；对象不能直接当 React child 渲染。
2. fetch 先 res.text() 再防御 JSON.parse，失败给明确错误 UI。
3. 后端 extractAndNormalize 保证 rhythm_analysis/highlights/oral_score_detail 等嵌套字段恒存在；前后端字段改动必须同步。
4. 未配置 LLM → 按钮 disabled + 提示去配置；已配置 → 真调用，失败直接报错。

## Pitfalls
- 4096 token 截断 JSON 很常见，必须有 repairTruncatedJson + 自动重试。
- 静默降级假数据是用户明令禁止的行为（『不要用模板功能；如果不行就直接不让用』）。
- 路由层白名单裁剪重建 LLM 结果曾丢 hook/outline/style_profile。

## Verification
1. 断网/错误 key 时前端显示明确错误而非假数据。
2. 用真实失败样本 dump 验证 JSON 解析链路。