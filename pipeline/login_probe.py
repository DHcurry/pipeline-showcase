from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    ctx = b.new_context(locale="zh-CN", user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    pg = ctx.new_page()
    pg.goto("https://www.xn--wcv59z.com/user/login", wait_until="domcontentloaded", timeout=60000)
    for i in range(15):
        time.sleep(1)
        if "验证" not in pg.title():
            break
    print("TITLE:", pg.title(), "URL:", pg.url)
    inputs = pg.eval_on_selector_all("input", "els=>els.map(e=>({type:e.type,name:e.name,ph:e.placeholder,id:e.id,cls:e.className}))")
    print("INPUTS:", inputs)
    forms = pg.eval_on_selector_all("form", "els=>els.map(e=>({action:e.action,method:e.method}))")
    print("FORMS:", forms)
    btns = pg.eval_on_selector_all("button, input[type=submit], a.btn", "els=>els.map(e=>({t:(e.innerText||e.value||'').trim(),cls:e.className}))")
    print("BUTTONS:", btns)
    txt = pg.inner_text("body")
    print("BODY:", txt[:1500])
    open(r"C:\Users\16575\daily-movie\login.html","w",encoding="utf-8").write(pg.content())
    pg.screenshot(path=r"C:\Users\16575\daily-movie\login.png")
    ctx.storage_state(path=r"C:\Users\16575\daily-movie\state.json")
    b.close()
