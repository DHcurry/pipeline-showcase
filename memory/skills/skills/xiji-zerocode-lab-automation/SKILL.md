---
name: "xiji-zerocode-lab-automation"
description: "希冀平台零代码图像分类训练系统的浏览器自动化（CDP接管+伪摄像头+批量上传+调参训练+上传推理）已验证流程"
version: 2
created: "2026-10-28"
updated: "2026-10-29"
---
## When to Use
用户要求自动完成希冀平台零代码图像分类实验（后续章节大概率还有同类实验）时：需要接管浏览器操作训练系统、喂伪摄像头数据、批量上传数据集、自动训练调参和逐张推理截图。

## Procedure
1. Edge 136+ 禁止默认配置开调试端口：taskkill 全部 msedge → 注册表 HKCU\Software\Microsoft\Edge\StartupBoostEnabled=0 → 启动 msedge.exe --remote-debugging-port=9222 --user-data-dir=C:\edge_debug_profile（独立配置，用户需登录一次希冀，之后记住）→ Playwright connect_over_cdp('http://127.0.0.1:9222')。
2. 伪摄像头三件套 flag 必须齐全：--use-fake-ui-for-media-stream --use-fake-device-for-media-stream --use-file-for-fake-video-capture=C:\ascii路径\feed.y4m（缺 fake-device 会静默用真实摄像头）。y4m 用 PIL+numpy 手写 RGB→YUV420，头部 YUV4MPEG2 W640 H480 F30:1 Ip A1:1 C420mpeg2，每帧 FRAME\n+Y+U+V；Chromium 循环播放，重开摄像头从文件头重播（可利用此特性保证先播指定类别段）。
3. 训练系统是页面内 iframe（frame title=模型训练系统，位于 WebVPN svc 代理 URL 下），所有操作在该 frame 内做。类卡选择器：.cardLeft .el-card；类名 span.cardFont；改名点 .el-icon-edit 后输入框一次只出现一个（用 .last 不能用 nth(idx)）；删除类/清空样本在卡头 .el-dropdown 菜单（移除所有样本/删除类别）。
4. 上传样本用类卡内 input[type=file]（multiple）直接 set_input_files 一次60张；等 img.img 计数达标再下一类。添加类别后用 .cardFont 数类卡，别用 .el-card（会把训练卡/预览卡算进去）。
5. 录制按钮（按住即可录制）：按卡片作用域找 button/div 且 innerText 恰好等于该文本、bounding_box 高度<70；必须先 scroll_into_view_if_needed 再取坐标，否则按钮在视口外 mouse.down 落空且不报错（症状：录制0样本）。摄像头面板开着时该卡的摄像头图标会被移除，.first 会落到别的卡上（曾导致107张手机帧录进水杯卡）。
6. 高级参数面板：点 span(文本=高级) 展开；三个 el-input-number 依次是周期数/批大小/学习率。学习率步进0.001，设0.0005会被回弹（fill和键盘输入都无效）；epochs/batch 用 fill 可提交。训练完成判据：训练模型按钮恢复可点 + body 出现'耗时'文本。
7. 上传推理：预览卡 .el-card filter(has_text=预览) 内 input[type=file] 逐张 set_input_files，读 body.innerText 中'输出'后的 标签/百分比 对解析 top-1；每张 sleep 0.6-0.8s 轮询。训练耗时参考：175样本50轮约86s、600样本约4.4min、180样本约80s。

## Pitfalls
- Edge 普通启动的窗口永远操作不了（136+ 禁默认 profile 调试端口），必须独立 user-data-dir；用户重新登录一次是必要代价。
- 伪摄像头缺 --use-fake-device-for-media-stream 时画面是真实摄像头，不报错，必须截图验证画面是合成内容。
- y4m 路径含中文可能有风险，用纯 ASCII 路径。
- el-input-number 学习率输入会被步进值回弹，报告里要写'界面步进限制无法微调'而不是假装调了。
- 摄像头按住录制必须滚动到视口内再取坐标；面板打开期间卡的摄像头图标消失会让 .first 定位到错误的卡。
- 截图必须真实操作界面（用户硬性要求）：类卡+样本缩略图、高级参数面板、训练指标文本、Loss/Accuracy图表、推理输出条形图，错误推理要专门截图。
- 摄像头素材别用 PIL 程序化画的卡通图——用户会嫌假（2026-10-28 被退回一次）。用 Wikimedia Commons 真实照片（走本地代理 127.0.0.1:7897 下载），每张照片生成缓慢推拉/亮度渐变的30帧模拟手持运镜，真实感足够；剔除信息图/传单/含人物杂景的图，留纯物体特写。
- CDP 页面句柄会随标签页顺序变化失效：按 URL 特征（webPluginList）重新定位 page，别假设 pages[0]。
- 高级面板展开要用 .el-icon-arrow-down first click(force=True)；点 span(文本=高级) 无效；判断是否展开看训练卡 input 是否可见，别看箭头方向（输入框的步进箭头也是 arrow-down 会误判）。
## Verification
1. CDP：urlopen http://127.0.0.1:9222/json/version 返回 Browser 字段。
2. 伪摄像头：canvas drawImage(video) 抓帧存 PNG 人工查看是合成画面。
3. 每类样本计数（img.img 数量或'N 个图片样本'文本）达标。
4. 训练完成：按钮恢复 + 指标文本（准备数据耗时/训练模型耗时/每轮训练耗时）。
5. 推理结果逐张落盘 JSON（pred/conf/true）并统计准确率与错例。
6. 最终 docx：word/media 图片数=预期截图数、tables 行数正确、无乱码字符、无'图片缺失'段落。