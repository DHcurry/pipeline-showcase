from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    ctx = b.new_context(locale="zh-CN", user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    pg = ctx.new_page()
    pg.goto("https://www.xn--wcv59z.com/", wait_until="domcontentloaded", timeout=60000)
    for i in range(15):
        time.sleep(1)
        if "验证" not in pg.title():
            break
    print("TITLE:", pg.title(), "URL:", pg.url)
    txt = pg.inner_text("body")
    print("BODY:", txt[:2000])
    hrefs = pg.eval_on_selector_all("a", "els=>els.map(e=>({t:(e.innerText||'').trim().slice(0,40),h:e.href})).filter(x=>x.t)")
    for h in hrefs[:80]:
        print("LINK:", h)
    open(r"C:\Users\16575\daily-movie\home.html","w",encoding="utf-8").write(pg.content())
    pg.screenshot(path=r"C:\Users\16575\daily-movie\home.png")
    b.close()
