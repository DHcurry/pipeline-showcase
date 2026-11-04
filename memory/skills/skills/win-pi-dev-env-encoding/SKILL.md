---
name: "win-pi-dev-env-encoding"
description: ""
version: 2
created: "2026-10-10"
updated: "2026-10-10"
---
---
name: "win-pi-dev-env-encoding"
description: "Windows 上本机开发的编码、进程、网络注意事项（Python/Node UTF-8、杀进程、镜像加速）"
version: 1
created: "2026-09-27"
updated: "2026-09-28"
---
## When to Use
在本机 Windows 环境跑 Python/Node 脚本、杀进程、访问 GitHub/HuggingFace、或遇到中文乱码时。

## Procedure
1. Python stdout 双层强制 UTF-8：py 端 sys.stdout.reconfigure(encoding='utf-8')，Node spawn 注入 PYTHONUTF8=1、PYTHONIOENCODING=utf-8 且 encoding:'utf-8'；JSON 读写显式 encoding。
2. .docx 用 python-docx 生成。
3. GBK 终端 curl 中文乱码只是显示问题，验证时用 Python 显式 utf-8 读文件。
4. 杀进程：Git Bash 中 TASKKILL /F /PID 会被 MSYS 转义破坏，改用 Python 调 cmd/powershell 或 `netstat -ano | grep :PORT` 拿 PID 后裸 taskkill /F PID（回显 GBK 乱码属正常）；重启前后端须确认 8001/3000 端口已释放（旧前端进程可存活 70+ 小时）。
5. 网络：优先 context-mode，GitHub 用 ghfast.top，HuggingFace 用 hf-mirror.com，沙箱不读项目外目录。
6. 网关 apimimo.zaiyunding.com（deepseek/glm/kimi/mimo/qwen/seed），503=GPU 超阈值；apiKey 在 models.json，勿外传；本地模型默认 deepseek-v4-flash。
7. Pi 包位置 C:/Users/16575/AppData/Roaming/npm/node_modules/@earendil-works/；grep 查 pi 源码时 cmd.exe 下 2>/dev/null 会静默失败，须用 bash。
8. R 在本机（研究二多次踩中）：`Rscript -e "..."` 内联命令必 segfault——一律写成 .R 文件再 Rscript 文件.R；R 内中文字符串/注释易报 unexpected string constant；长模拟用 Monitor 后台跑+分批存盘（.rds/xlsx）+断点续跑，parLapplyLB 多核长跑易崩须分 chunk 每批立即存盘；R 4.5.3 缺 mvtnorm/glmnet/openxlsx/RcppArmadillo/RcppEigen 需先 install.packages（装到 ~/AppData/Local/R/win-library/4.5）；monitor 持句柄 taskkill 杀不掉 Rscript.exe，用 tasklist /fi "imagename eq Rscript.exe" 拿 PID 再 taskkill /f /pid。
9. 读结果文件先看格式：openpyxl 读不了带损坏 drawing 引用的 xlsx → 用 R 先导出 CSV；Monitor 列表为空不代表进程结束，以落盘文件为准。
10. PowerShell 中文报错时改写英文脚本；adb 路径用双斜杠 //sdcard。

## Pitfalls
- PowerShell 内联命令含 `$_` 会被 MSYS/bash 展开成 `/usr/bin/bash`（如 `$_.Name` 变 `/usr/bin/bash.Name`，报 ObjectNotFound/ParserError）——凡含 `$_`、`$_.Property` 的 PowerShell 一律写成 .ps1 文件再 `powershell -File` 执行，不要内联。
- Get-NetAdapterPowerManagement 等 CIM 查询在非管理员 shell 下可能报「A device attached to the system is not functioning (System Error 31)」；改用 powercfg /devicequery wake_armed 等低权限替代命令交叉验证，提权走 Start-Process -Verb RunAs 会弹 UAC（用户可能取消）。
## Verification
1. Python 脚本输出中文无乱码；目标端口进程已退出后再重启服务。