from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    ctx = b.new_context(locale="zh-CN", user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    pg = ctx.new_page()
    for u in ["https://www.xn--wcv59z.com/user/register", "https://www.xn--wcv59z.com/user/login"]:
        try:
            pg.goto(u, wait_until="domcontentloaded", timeout=60000)
            for i in range(15):
                time.sleep(1)
                if "验证" not in pg.title():
                    break
            print("=== ", u, " TITLE:", pg.title())
            print(pg.inner_text("body")[:1200])
            inputs = pg.eval_on_selector_all("input", "els=>els.map(e=>({type:e.type,name:e.name,ph:e.placeholder,id:e.id}))")
            print("INPUTS:", inputs)
        except Exception as e:
            print(u, "ERR", e)
    b.close()
