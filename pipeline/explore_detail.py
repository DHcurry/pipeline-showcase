from playwright.sync_api import sync_playwright
import time, re, json

STATE = r"C:\Users\16575\daily-movie\state.json"
BASE = "https://www.xn--wcv59z.com"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    ctx = b.new_context(locale="zh-CN", storage_state=STATE,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.goto(BASE + "/mv/g1mV5", wait_until="domcontentloaded", timeout=60000)
    for _ in range(20):
        time.sleep(1)
        if "验证" not in pg.title(): break
    time.sleep(2)
    print("TITLE:", pg.title(), "URL:", pg.url)
    txt = pg.inner_text("body")
    print("BODY[:1500]:", txt[:1500].replace("\n", " | "))
    # 找 magnet / ed2k
    html = pg.content()
    magnets = re.findall(r'magnet:\?[^"\'\s<>]+', html)
    print("MAGNETS in raw html:", len(magnets))
    for m in magnets[:5]: print("  ", m[:150])
    ed2k = re.findall(r'ed2k://[^"\'\s<>]+', html)
    print("ED2K:", len(ed2k))
    # 所有按钮/tab
    btns = pg.eval_on_selector_all("button, .tab, [class*=tab], a",
        "els=>els.map(e=>({t:(e.innerText||'').trim().replace(/\s+/g,' ').slice(0,30), c:e.className, h:e.href||''})).filter(x=>x.t && /磁力|下载|网盘|ed2k|地址|复制/.test(x.t))")
    print("BTN:", json.dumps(btns, ensure_ascii=False)[:1200])
    pg.screenshot(path=r"C:\Users\16575\daily-movie\detail.png", full_page=False)
    open(r"C:\Users\16575\daily-movie\detail.html", "w", encoding="utf-8").write(html)
    b.close()
