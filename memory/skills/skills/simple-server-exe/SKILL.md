---
name: "simple-server-exe"
description: "启动 SimpleServer.exe 运行离线网页游戏/演示的通用流程"
version: 1
created: "2026-09-27"
updated: "2026-09-27"
---
## When to Use
需要本地运行静态网页游戏、演示页面，或用户提到 SimpleServer.exe 时。

## Procedure
1. 使用 C:\Users\16575\Desktop\ji-ba-pccweb\SimpleServer.exe（.NET csc.exe 可复现编译）。
2. 固定以 exe 所在目录的 dist/ 为网站根目录。
3. 启动后读取其打印的端口（默认 8080，冲突自动 +1），不要假设 8080。
4. 在真实控制台或批处理中运行，不要重定向 stdout（含 Console.ReadKey，重定向会抛异常）。

## Pitfalls
- 无控制台重定向运行会因 Console.ReadKey 抛异常。
- 端口可能不是 8080，测试必须读取实际打印端口。

## Verification
1. 浏览器成功打开打印端口上的页面。