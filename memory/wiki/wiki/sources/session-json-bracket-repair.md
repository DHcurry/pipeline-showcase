---
type: source
title: Session JSON 修复：模型漏闭合符与字符串内插补丁的位置陷阱
status: insight
category: backend
created: 2026-09-27
updated: 2026-09-27
slug: session-json-bracket-repair
---

# Session JSON 修复：模型漏闭合符与字符串内插补丁的位置陷阱

## 背景

content-creator-workspace 接入 Pi AgentSession 后（analyze/generate/optimize 走 `runSessionJSON`），mimo-v2.6-flash 偶发输出**括号不平衡的 JSON**（约 1/4 概率），报 `AI 输出不是合法 JSON（已重试一次）`。

## 两种真实故障形态

1. **截断**：maxTokens 不足（已从 4096 提到 8192）。
2. **结构漏闭合**（更隐蔽）：模型把对象结束 `}` 漏掉直接写 `]`，例如 `..."transition":"..."}` 之后应有 item 的 `}` 却直接 `]`，且数组后还继续写 `"core_value":...`。Python/JSON.parse 报 `Expecting ',' delimiter`。

## 修复器（ai.ts repairTruncatedJson）的两个关键坑

**坑1：规则触发顺序**。检测到"数组内出现 key:value"（说明模型漏写了数组闭合符）时，`]"` 必须插在 **key 字符串开始之前**，不能在闭引号后追加（会产生 `"core_value]":`），也不能在写闭引号之前追加（`out` 还没写完 key 的闭引号，`]"` 会落进字符串内部 → `"core_value]"`）。

正确做法：在**开引号时**记录 splice 点（`pendingIns`，若前面是逗号则指向逗号位），在闭引号且下一个字符是 `:` 时反向 splice：
- 前面有逗号 → `out = out.slice(0, pendingIns) + "]" + out.slice(pendingIns)`（得到 `elem],"key"`）
- 无逗号 → 插入 `"],`

**坑2：Python/JS split 语义差异**。`raw.split('=== FULL ===', 1)[1]` 在 Python 返回2段（maxsplit），在 JS 返回**1段**（limit=返回数组长度）→ `[1]` 是 undefined。调试脚本里踩过。

**坑3：字符串子串替换命中错误位置**。`c.replace(old, new, 1)` 的 old 是子串匹配——4空格缩进的行会命中6空格缩进的**另一个函数**里相同代码。必须用 `c.index('目标函数名')` 先定位再切片替换。

## 验证方法

对 `E:/migrated-projects/last_session_raw.txt`（失败时 dump 的原始输出）提取样本，用 tsx 跑真实 `repairTruncatedJson`，确认 JSON.parse 成功且 11 个顶层键齐全。修复前 3/4 analyze 失败，修复后待端到端验证。

相关：[[content-creator-ai-infra-pi-sdk-refactor]]

*Category: backend*

---
*Captured: 2026-09-27*

## Related

_Add links to related pages._
