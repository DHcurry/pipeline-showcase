from playwright.sync_api import sync_playwright
import time, json

STATE = r"C:\Users\16575\daily-movie\state.json"
BASE = "https://www.xn--wcv59z.com"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    ctx = b.new_context(locale="zh-CN", storage_state=STATE,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.goto(BASE + "/mv", wait_until="domcontentloaded", timeout=60000)
    for _ in range(20):
        time.sleep(1)
        if "验证" not in pg.title():
            break
    time.sleep(2)
    print("MV TITLE:", pg.title(), "URL:", pg.url)
    print("BODY[:800]:", pg.inner_text("body")[:800].replace("\n", " | "))
    links = pg.eval_on_selector_all("a",
        "els=>els.map(e=>({t:(e.innerText||'').trim().replace(/\s+/g,' ').slice(0,50),h:e.href})).filter(x=>x.t)")
    print("--- LINKS", len(links), "---")
    seen = set()
    for l in links:
        key = l["h"]
        if key in seen: continue
        seen.add(key)
        print(f"  [{l['t']}] -> {l['h']}")
    pg.screenshot(path=r"C:\Users\16575\daily-movie\mv.png", full_page=False)
    open(r"C:\Users\16575\daily-movie\mv.html", "w", encoding="utf-8").write(pg.content())
    b.close()
