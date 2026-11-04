---
name: "pta-exam-sql-automation"
description: "通过 CDP + protobuf API 批量读取并提交 PTA(pintia.cn) SQL 编程题考试，含限流对策与表名探测"
version: 1
created: "2026-11-02"
updated: "2026-11-02"
---
## When to Use
用户已登录 PTA 并要批量完成 pintia.cn 的 SQL 编程题考试/题集；需要读取题面、样例图片，或批量提交答案时。

## Procedure
1. 确认浏览器开了 CDP：netstat -ano | findstr 9222，用 http://127.0.0.1:9222/json/list 找目标页 webSocketDebuggerUrl。
2. 写 cdp2.js：连 ws，发 Runtime.evaluate（returnByValue+awaitPromise），把 JS 文件内容作为 expression 执行并打印返回值。所有 API 调用都在页面内 fetch，复用登录态与 X-Lollipop/X-Marshmallow 头。
3. 题目清单：GET /api/problem-sets/{psId}/exam-problem-list?exam_id={examId}&problem_type=SQL_PROGRAMMING&page=0&limit=100，返回 protobuf，需自写解码器（varint + length-delimited，按 utf-8 fatal 判定字符串 vs 子消息）。
4. 题目详情：GET /api/problem-sets/{psId}/exam-problems/{id}；题面=f1.f7，建表语句=f1.f4.f9.f1，期望输出表结构（列名）=f1.f4.f9.f5，比较模式标志=f1.f4.f9.f6/f7/f9。
5. 样例图片：题面里的 ![..](~/xxx.png) 换成 https://images.ptausercontent.com/xxx.png 直接下载；当前模型不支持看图时用 rapidocr-onnxruntime 做 OCR（PYTHONIOENCODING=utf-8 否则中文乱码）。
6. 提交：POST /api/exams/{examId}/exam-submissions，JSON body {problemType:'SQL_PROGRAMMING',details:[{problemId:'0',problemSetProblemId:'<id>',sqlProgrammingSubmissionDetail:{program:'<SQL>'}}]}，返回 {submissionId}。
7. 查结果：GET /api/exams/{examId}/submissions/{submissionId} 返回 protobuf；status=f2.f12.f1，5=AC；测试点明细 f2.f12.f10.f1[]，错误信息在 f2.f1 的 f2.f3。
8. 批量提交每 2-3 秒一题，遇 RATE_LIMIT_EXCEEDED 退避 4s 重试；先全部提交再统一查结果，比逐题等待快得多。

## Pitfalls
- 考试有时限：必须边解边交，绝不能全部准备完再交（曾因此 69 题被判 EXAM_SERVICE_OUT_OF_EXAM_TIME）。
- 题目 id 与题号不对应，务必用 label→id 映射表，别凭 seq 猜（曾把 10-37/10-38 混淆，探测语句覆盖了已 AC 的题）。
- Protobuf 解码不要把含中文的 bytes 判成子消息：先试 TextDecoder('utf-8',{fatal:true})。
- protobuf varint 要用 BigInt，否则大 id(>2^31) 溢出。
- 题面描述与实际环境可能不符：可用 SELECT * FROM X 探测表是否存在，报 Invalid object name 即不存在；CREATE TABLE 通常无权限（sql_judger 库）。
- 排序要求常藏在题面正文（如『按登记日期降序』），而样例图只显示数据，别只照抄 SELECT *。

## Verification
1. 对每题调 last-submissions?problem_set_problem_id=<id> 拿最新 submission id，再查 submissions/{id}，status==='5' 即 AC。
2. 汇总所有 tests[].score 得到总分，确认与题目分值之和一致（本次 70 题 700 分）。