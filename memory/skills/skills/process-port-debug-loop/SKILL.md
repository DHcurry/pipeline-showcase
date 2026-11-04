---
name: "process-port-debug-loop"
description: "Windows 上\"改了没生效/请求失败\"的三层根因排查与杀进程流程"
version: 1
created: "2026-09-27"
updated: "2026-09-28"
---
## When to Use
前端或后端改完代码后表现没变化、请求失败、端口被占用时。

## Procedure
1. ①旧进程未杀：tsx watch 在此环境不热重载后端 TS 改动 → netstat -ano 查 PID → Python subprocess 调 cmd /c taskkill（Git Bash 里 TASKKILL /F /PID 被 MSYS 转义破坏）→ 重启 → curl/Python 实测验证；重启前后端须确认 3000/8001 真正释放（旧前端进程可存活 70+ 小时）。
2. ②HMR/Turbopack 编译出错留 stale bundle → curl 确认返回新内容 → 浏览器 Ctrl+Shift+R 强刷，别急着改代码。
3. ③Next dev rewrite 代理掐断 >30s 长请求 → 前端直连 127.0.0.1:8001（CORS 已配），判别法=未知 action 返回 Hono 纯文本 404，详见 skill global:nextjs-dev-proxy-pitfalls。
4. 新增/改动路由文件必须重启 Next dev 才会注册。

## Pitfalls
- 单一声状（Internal Server Error/乱码/空结果）在不同环节根因完全不同，必须逐层实测而非猜测。
- cmd 下 grep 带 2>/dev/null 会静默失败导致误判，查 npm 包目录用 bash。
- 症状与根因对照（"Unexpected token I"/纯文本 500、新路由 404、改了没生效）的完整根因树见 skill global:nextjs-dev-proxy-pitfalls，勿只按超时/CORS/缓存猜测（曾误判 3 次）。
- Monitor 工具缓冲超长后无法回读——长测试脚本要逐例落盘 JSONL；长 LLM 测试用 Monitor+timeout 900s 后台跑。

## Verification
1. curl 能拿到新代码的响应。
2. 目标端口旧 PID 已退出，新服务起来后端到端请求成功。