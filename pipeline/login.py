from playwright.sync_api import sync_playwright
import time, sys

USER = "beliveyb"
PASS = "qazwsxedc@163"
STATE = r"C:\Users\16575\daily-movie\state.json"
BASE = "https://www.xn--wcv59z.com"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    ctx = b.new_context(locale="zh-CN",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.goto(BASE + "/user/login", wait_until="domcontentloaded", timeout=60000)
    for _ in range(20):
        time.sleep(1)
        if "验证" not in pg.title():
            break
    # 等输入框渲染
    pg.wait_for_selector("input[name=username]", timeout=20000)
    time.sleep(0.5)
    pg.fill("input[name=username]", USER)
    pg.fill("input[name=password]", PASS)
    try:
        pg.check("input[name=cookietime]", timeout=3000)  # 记住登录
    except Exception:
        pass
    pg.screenshot(path=r"C:\Users\16575\daily-movie\before_login.png")
    # 点击登录按钮
    clicked = False
    for sel in ["button[type=submit]", "input[type=submit]", "text=登录"]:
        try:
            el = pg.locator(sel).first
            if el.is_visible(timeout=2000):
                el.click(timeout=3000)
                clicked = True
                break
        except Exception:
            continue
    print("clicked:", clicked)
    time.sleep(4)
    print("title:", pg.title(), "url:", pg.url)
    body = pg.inner_text("body")[:600]
    print("body:", body)
    pg.screenshot(path=r"C:\Users\16575\daily-movie\after_login.png")
    # 是否有验证码弹层
    for s in ["滑动", "验证", "captcha", "拖动"]:
        n = pg.locator(f"text={s}").count()
        if n: print(f"hint '{s}' x{n}")
    if "登录" in pg.title() or "login" in pg.url:
        print("LOGIN FAILED")
        sys.exit(2)
    ctx.storage_state(path=STATE)
    print("state saved ->", STATE)
    b.close()
