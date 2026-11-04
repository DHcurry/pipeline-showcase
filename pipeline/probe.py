from playwright.sync_api import sync_playwright
import time, sys

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    ctx = b.new_context(locale="zh-CN", user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    pg = ctx.new_page()
    pg.goto("https://www.xn--wcv59z.com/mv", wait_until="domcontentloaded", timeout=60000)
    for i in range(20):
        time.sleep(1)
        title = pg.title()
        url = pg.url
        print(f"[{i}] title={title!r} url={url}")
        if "验证" not in pg.content()[:2000] and "pow" not in url:
            break
    print("FINAL TITLE:", pg.title())
    print("FINAL URL:", pg.url)
    # save snapshot
    open(r"C:\Users\16575\daily-movie\page.html","w",encoding="utf-8").write(pg.content())
    pg.screenshot(path=r"C:\Users\16575\daily-movie\shot.png", full_page=False)
    # links
    hrefs = pg.eval_on_selector_all("a", "els=>els.map(e=>({t:(e.innerText||'').trim().slice(0,60),h:e.href})).filter(x=>x.t)")
    for h in hrefs[:60]:
        print("LINK:", h)
    # look for login-related
    inputs = pg.eval_on_selector_all("input", "els=>els.map(e=>({type:e.type,name:e.name,ph:e.placeholder,id:e.id}))")
    print("INPUTS:", inputs)
    ctx.storage_state(path=r"C:\Users\16575\daily-movie\state.json")
    b.close()
