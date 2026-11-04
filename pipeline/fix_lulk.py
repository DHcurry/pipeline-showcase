# -*- coding: utf-8 -*-
"""Lulk《失控劫案》豆瓣简介是导航占位文本 -> 站点搜索详情页重抓覆盖 + 生成标题"""
import os, re, sys
sys.path.insert(0, r"C:\Users\16575\daily-movie")
import fetch_intro as fi
fi.BASE = fi.BASE if hasattr(fi, "BASE") else "https://www.xn--wcv59z.com"
from playwright.sync_api import sync_playwright

LULK_DIR = None
for d in os.listdir(fi.SCAN):
    if d.startswith("Lulk"):
        LULK_DIR = os.path.join(fi.SCAN, d)
        break
assert LULK_DIR, "Lulk 目录未找到"
vids = fi.find_videos(LULK_DIR)
assert vids, "Lulk 视频未找到"
video = vids[0]

with sync_playwright() as pw:
    b, ctx = fi.browser(pw)
    pg = ctx.new_page()
    try:
        # 站内搜索 (WordPress ?s= 风格, 两种都试)
        got = None
        for q in ("失控劫案", "Lulk"):
            for url in (f"{fi.BASE}/?s={fi.np_quote(q) if hasattr(fi,'np_quote') else q}",
                        f"{fi.BASE}/search/{q}"):
                try:
                    pg.goto(url, timeout=45000, wait_until="domcontentloaded")
                    fi.pass_challenge(pg, need_links=False)
                    link = pg.evaluate("""() => {
                        const as = [...document.querySelectorAll('a[href]')];
                        const h = as.map(a => a.href).find(h =>
                            /xn--wcv59z\\.com\\/(mv|movies)\\//.test(h) && /lulk|\\u5931\\u63a7/i.test(a.textContent + h));
                        return h || null;
                    }""")
                    if link:
                        got = link
                        break
                except Exception:
                    continue
            if got:
                break
        print("详情页:", got or "未找到")
        if not got:
            sys.exit(1)
        body = fi.intro_from_site(pg, got)
        if not body or len(body) < 60:
            print("详情页简介仍不足:", (body or "")[:80])
            sys.exit(2)
        p = fi.write_txt(video, "失控劫案 Lulk", "站点详情页", body)
        print("简介已覆盖:", os.path.basename(p))
        print("=== 简介前200字 ===")
        print(body[:200].replace("\n", " "))
    finally:
        try:
            ctx.storage_state(path=fi.STATE)
        except Exception:
            pass
        b.close()
