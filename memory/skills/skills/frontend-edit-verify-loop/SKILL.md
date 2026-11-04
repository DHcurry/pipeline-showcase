---
name: "frontend-edit-verify-loop"
description: "前端/后端 TSX 批量编辑后的编译校验与空值防护流程"
version: 1
created: "2026-09-27"
updated: "2026-09-28"
---
## When to Use
在 content-creator-workspace 或类似 Next.js/React 项目里做多处 replace/edit、删除页面、或渲染 LLM 返回的嵌套字段之前。

## Procedure
1. 每轮批量编辑后立刻跑 tsc --noEmit，双端都验（frontend + backend/unified），错误定位到行号再修，不许攒到最后。
2. 删页面/路由后清理 .next（含 .next/types/validator.ts）与 .turbo，否则残留旧引用报 TS2307。
3. LLM 返回的嵌套字段一律 ?. + || 兜底；对象/数组不能直接当 React child 渲染（如 oral_score_detail）。
4. 后端结构变更前后端字段必须同步改；fetch 先 res.text() 再防御性 JSON.parse。

## Pitfalls
- 并发/连续多轮 replace 会导致 JSX 结构错乱（多余 '};'、未闭合标签）→ TS1128 / Turbopack 'Parsing ecmascript source code failed'。
- phosphor-icons/react 部分图标名不存在（ListTree/Wand2）。
- useSearchParams 必须包 Suspense 边界否则构建失败。
- 批量替换/锚点编辑：oldText 须精确含换行缩进，两处相同文本补上下文使其唯一；锚点多/少括号与转义层叠（heredoc 会把转义序列写成真实控制字符，导致 TS Unterminated string literal）都会炸——改用不含转义的短锚点或用 charCodeAt(n)===10 判断换行；改完 grep 验证锚点命中次数；CRLF 检测勿用 grep 空模式（假阳性），用 Python 逐行数真实 CRLF 再决定策略；防 PUA 不可见字符 U+E6C3 混入与空字符串 includes("") 恒真误判。
- React onClick={handler} 会把 MouseEvent 当首参，用 ()=>handler()。

## Verification
1. tsc --noEmit 前后端均 0 错误。
2. 页面渲染空值/null 字段不崩。