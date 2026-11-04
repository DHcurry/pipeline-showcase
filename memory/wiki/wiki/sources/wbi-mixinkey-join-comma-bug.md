---
type: source
title: WBI mixinKey 的 join() 逗号 bug：搜索端点不校验 w_rid 掩盖了它数月
status: insight
category: bugfix
created: 2026-09-29
updated: 2026-09-29
slug: wbi-mixinkey-join-comma-bug
---

# WBI mixinKey 的 join() 逗号 bug：搜索端点不校验 w_rid 掩盖了它数月

## 症状

up主视频列表端点（`x/space/wbi/arc/search`）稳定 -403/返回HTML，但同代码库的搜索端点（`x/web-interface/wbi/search/type`）一直正常。

## 根因

```ts
// bilibili.ts getMixinKey 历史写法
return mixinKeyEncTab.map((n) => orig[n]).join().slice(0, 32);   // join() 默认逗号分隔！
// 产出 "e,a,1,d,b,1,2,4,..." ← 32字符里一半是逗号，只含16个有效字符
// 正确：
.join("").slice(0, 32)  // "ea1db124af3c7062474693fa704f4ff8"
```

**为什么搜索一直"正常"**：B站各端点对 w_rid 校验强度不一——搜索端点不严格校验（签名形同虚设），space 端点严格校验才暴露。**对照实验**（同一请求只换 mixin）：comma版→HTML风控页，empty版→code=0 videos=5。

## 教训

- **"功能正常"≠"代码正确"**：下游端点的宽松校验会掩盖上游实现 bug，直到换到严格端点才爆雷
- 排查签名类问题的决定性手法：**同一请求、只变一个变量（签名值）做 A/B 对照**
- 历史教训延伸：本次会话还发现老 `x/player/v2` 字幕端点按 cid 单键解析（见 [[bilibili-old-player-endpoint-cid-only-resolution]]）——B站老端点普遍不可靠，新 WBI 端点+成对参数是正路

## 附带产出

`searchUpVideos(mid)` 需要 spi 指纹（buvid3/4）+ minimal 参数集（加 platform/web_location 反而触发风控）+ Origin/Referer space 头。

相关：[[bilibili-old-player-endpoint-cid-only-resolution]]

*Category: bugfix*

---
*Captured: 2026-09-29*

## Related

_Add links to related pages._
