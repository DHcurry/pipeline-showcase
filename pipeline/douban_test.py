from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    ctx = b.new_context(locale="zh-CN",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    pg = ctx.new_page()
    pg.goto("https://movie.douban.com/subject/37430794/", wait_until="load", timeout=60000)
    for i in range(15):
        time.sleep(2)
        try:
            t, u = pg.title(), pg.url
        except Exception:
            continue
        print(f"[{i}] title={t!r} url={u[:70]}")
        if "subject" in u and "sec.douban" not in u and t and t not in ("豆瓣", ""):
            break
    try:
        og = pg.eval_on_selector_all("meta[property='og:image']", "els=>els.map(e=>e.content)")
        print("og:image:", og[:2])
        imgs = pg.eval_on_selector_all("img", "els=>els.map(e=>e.src).filter(s=>s&&/doubanio/.test(s))")
        print("imgs:", imgs[:5])
        pg.screenshot(path=r"C:\Users\16575\daily-movie\douban.png")
    except Exception as e:
        print("eval err:", e)
    b.close()
