---
name: "nextjs-dev-proxy-pitfalls"
description: "Next.js dev rewrite 代理掐断长请求的判别与彻底解法（直连 8001）"
version: 1
created: "2026-09-27"
updated: "2026-09-28"
---
## When to Use
content-creator-workspace 中出现 'Unexpected token I'、纯文本 'Internal Server Error'、或新增/改动 Next 路由后行为异常时。

## Procedure
1. 根因：rewrite 代理对 >30s 的 LLM/转写请求返回纯文本 'Internal Server Error'，前端 res.json() 崩 'Unexpected token I'。
2. 判别法：请求未知 action 返回 Hono 纯文本 404，即证明走了 rewrite 而非显式路由。
3. 彻底解法：前端 fetch 直连 http://127.0.0.1:8001（CORS 已配 localhost:3000），转写+workflow 共 6 处均直连。
4. 路由结构定稿：/api 下方括号动态段目录（如 workflow/[action]）在 Next 16.3.3+Turbopack+Windows 下完全不加载、静默落回 rewrite 代理 → 已拆成 6 个静态 route 目录（analyze/generate/optimize/search/full/partial_edit）+ 共享 lib/workflow-proxy.ts；判别探针=POST 未知 action，filesystem route 返回 JSON detail、rewrite 返回 Hono 纯文本 404。
5. 后端兜底：@hono/node-server serve() 在 app.fetch reject 时吐纯文本 "Internal Server Error" → 改用 getRequestListener 自建 http server + Hono app.onError 返回 {detail} JSON；前端 fetch 一律先 res.text() 再防御 JSON.parse。
6. 新增/改路由文件必须重启 dev 并杀旧 PID（曾 47-79h 不重启不注册、旧进程占 3000 端口）；浏览器 Ctrl+Shift+R 强刷旧 bundle。
7. 删页面后清 .next/.turbo 消除 TS2307 残留；layout 签名用 ({children}: {children: React.ReactNode})；@sinclair/typebox、@types/better-sqlite3、@types/qrcode 需单独安装。

## Pitfalls
- 不要用 rewrite 代理承载 >30s 请求，必须直连 8001。
- 不重启 dev 导致新路由不注册是最易复发的坑。

## Verification
1. 长耗时 LLM/转写请求端到端成功；新路由返回 JSON 而非纯文本 404。