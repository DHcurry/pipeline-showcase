---
type: source
title: Next 16.3.3 Turbopack 不加载 api 方括号目录的 route handler（Windows）
status: insight
category: frontend
created: 2026-09-27
updated: 2026-09-27
slug: next16-turbopack-bracket-api-route-bug
---

# Next 16.3.3 Turbopack 不加载 api 方括号目录的 route handler（Windows）

## 症状

content-creator-workspace 用户点「模仿生成」报 `接口返回了非 JSON 内容（HTTP 500）：Internal Server Error`。

## 根因链（三层叠加）

1. **Next 16.3.3 + Turbopack (Windows) 不加载 `app/api/**/[xxx]/route.ts`**（方括号动态目录下的 route handler）。分二分验证：
   - 静态 `app/api/ping/route.ts`（重启后新建）→ 加载 ✅
   - 动态 `app/api/dyn/[id]/route.ts`（重启后新建）→ 不加载 ❌（404 是 Hono notFound 文本 = rewrite 代答）
   - 方括号**页面** `/projects/[id]` → 正常 ✅（只有 route handler 受影响）
   - 决定性探针：`POST /api/workflow/bogus`——filesystem route 生效应返回 JSON `{detail:"Unknown workflow action"}`，实际返回 Hono 纯文本 `404 Not Found` → 请求全部落进 `/api/:path*` rewrite
2. **rewrite 路径无长超时保障**：慢 LLM 请求（>30s）经 rewrite → Next 代理层出错 → 返回**纯文本 500 "Internal Server Error"** → 前端 readJson 崩（这正是 frontend/src/lib/api.ts 注释里早就记录的现象，当时没意识到 rewrite 是唯一生效路径）
3. **服务端零 JSON 兜底**：serve() 无 errorHandler、Next passthrough 不校验内容类型

## 修复（已验证）

- **绕过方案**：6 个静态目录 `app/api/workflow/{analyze,generate,optimize,search,full,partial_edit}/route.ts`，共享 `lib/workflow-proxy.ts`（320s 超时 + 非 JSON 包装 + `x-wf-router: explicit` 诊断头）
- 诊断头验证：`x-wf-router=explicit` 出现 = filesystem route 生效
- 后端 `getRequestListener(app.fetch, {errorHandler})` 自建 server（serve() 的 Options **不接受** errorHandler，类型定义确认过）；app.onError 本来就返回 JSON
- Next passthrough：body 非 JSON 时包装成 `{detail}` 而不是原样透传

## 探针技巧（复用价值）

判断请求走了 filesystem route 还是 rewrite：**构造一个只有其中一层会给出特定响应的 URL**（未知 action 的 JSON 型 404 vs Hono 文本型 404）；响应头打自定义诊断标记最可靠。

相关：[[session-json-bracket-repair]]

*Category: frontend*

---
*Captured: 2026-09-27*

## Related

_Add links to related pages._
