---
name: "rea-ghidra-cli-windows"
description: "在 pi 会话中用 REA CLI+Ghidra 对 Windows PE 做逆向分析的已验证流程（环境变量注入与快照复用）"
version: 1
created: "2026-10-22"
updated: "2026-10-22"
---
## When to Use
需要对 Windows 原生二进制（如 TK奥德彪 的 tkcore.exe）做 REA/Ghidra 分析，而 MCP 工具报 GHIDRA_INSTALL_DIR not_configured 时。

## Procedure
1. 在 bash 里现场注入：export GHIDRA_INSTALL_DIR="C:\\Tools\\ghidra_12.1_PUBLIC"（pi 进程早于 setx 启动，MCP 子进程继承不到用户级环境变量，CLI 注入是绕过手段）
2. 第一次分析建快照：rea inspect <bin> --provider ghidra --snapshot <snap路径> --format json > inspect.json（Ghidra 导入+自动分析约 3 分钟）
3. 后续复用快照（免重复导入，约 2 分钟/次）：rea search <bin> --kind procedures|strings --mode regex --pattern '.*' --snapshot <snap路径>
4. 定位关键函数：rea xrefs <bin> <字符串地址> --snapshot <snap>；再 rea decompile <bin> <函数地址> --snapshot <snap> --format md
5. 输出一律重定向到文件，再用 ctx_execute 沙箱解析，不要直接读大 JSON/伪代码

## Pitfalls
- RE A MCP 与 CLI 是同一引擎但环境隔离：本会话 MCP 报 ghidra not_configured 不代表 CLI 不可用
- 每个 rea 调用都是独立进程；不带 --snapshot 会重新导入+全量分析（+3分钟）
- 无 PDB 的二进制内部函数全是 FUN_xxx，类归属要靠 RTTI/Qt元对象字符串+xrefs 推断
- Ghidra 字符串列表只含已定义字符串，搜不到不代表不存在
- 授权/卡密模块属 TK奥德彪 项目既定边界，只记录不分析

## Verification
1. rea inspect 产出 inspect.json 且 evidence_id 稳定（ev_e9cdc53f…）
2. rea search --snapshot 复用后耗时从~3分钟降到~2分钟
3. xrefs+decompile 能给出字符串宿主函数地址与伪代码 md 文件