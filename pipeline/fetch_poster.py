# -*- coding: utf-8 -*-
"""为已下载电影抓取高清封面（豆瓣 og:image，失败回退站点384图），存到电影同目录。

用法:
  python fetch_poster.py                # 处理历史里所有缺封面的已完成电影
  python fetch_poster.py --url SITE_URL # 指定站点详情页
产物: 电影目录下 <视频名>.jpg + folder.jpg + poster.jpg（播放器/媒体库通用命名）
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY = os.path.join(DIR, "history.json")
STATE = os.path.join(DIR, "state.json")
LOG = os.path.join(DIR, "poster.log")
QBT_ENV = os.path.join(DIR, "qbwebui.env")
BASE = "https://www.xn--wcv59z.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")


def log(msg):
    line = f"[{datetime_str()}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def datetime_str():
    from datetime import datetime
    return f"{datetime.now():%Y-%m-%d %H:%M:%S}"


def qbt_content_path(infohash):
    env = {}
    p = os.path.join(DIR, "qbwebui.env")
    for ln in open(p, encoding="utf-8"):
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.strip().split("=", 1)
            env[k] = v
    base = env.get("QBT_URL", "http://127.0.0.1:8080")
    import urllib.parse
    try:
        req = urllib.request.Request(base + "/api/v2/auth/login",
              data=urllib.parse.urlencode({"username": env.get("QBT_USER", ""),
                                            "password": env.get("QBT_PASS", "")}).encode())
        with urllib.request.urlopen(req, timeout=8) as r:
            scs = r.headers.get_all("Set-Cookie") or []
            cookie = "; ".join(c.split(";")[0] for c in scs) or (r.headers.get("Set-Cookie", "").split(";")[0])
        req2 = urllib.request.Request(base + "/api/v2/torrents/info")
        req2.add_header("Cookie", cookie)
        with urllib.request.urlopen(req2, timeout=8) as r:
            ts = json.loads(r.read().decode())
        for t in ts:
            if t["hash"].lower() == infohash.lower():
                return t.get("content_path"), t.get("progress", 0)
    except Exception as e:
        log(f"qBittorrent 查询失败: {e}")
    return None, 0


def find_videos(folder):
    exts = {".mkv", ".mp4", ".avi", ".ts", ".mov", ".wmv", ".flv"}
    if os.path.isfile(folder):
        return [folder]
    out = []
    for root, _, files in os.walk(folder):
        for fn in files:
            if os.path.splitext(fn)[1].lower() in exts:
                out.append(os.path.join(root, fn))
    # 主片优先（拼接/压制产物 .ext/.testext/.subbed/.bilingual 不做命名基准）
    derived = (".ext.mp4", ".testext.mp4", ".subbed.mp4", ".bilingual.mp4", ".burning.mp4")
    primary = [p for p in out if not p.lower().endswith(derived)]
    return primary or out


def get_douban_url(site_detail_url):
    """站点详情页 -> 豆瓣 subject 链接"""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True,
                              args=["--disable-blink-features=AutomationControlled"])
        ctx = b.new_context(locale="zh-CN", storage_state=STATE,
                            user_agent=UA, viewport={"width": 1440, "height": 900})
        pg = ctx.new_page()
        pg.goto(site_detail_url, wait_until="domcontentloaded", timeout=60000)
        for _ in range(20):
            time.sleep(1)
            if "验证" not in pg.title():
                break
        time.sleep(1)
        hrefs = pg.eval_on_selector_all(
            'a[href*="douban.com/subject"]', "els=>els.map(e=>e.href)")
        try:
            pg.context.storage_state(path=STATE)
        except Exception:
            pass
        b.close()
        if not hrefs:
            return None
        m = re.search(r"//movie\.douban\.com/subject/(\d+)/?", hrefs[0])
        return "https://movie.douban.com/subject/" + m.group(1) + "/" if m else None


def douban_og_image(subject_url):
    """Playwright 打开豆瓣页取 og:image（curl 会被 sec 挑战拦，必须真浏览器）"""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True,
                              args=["--disable-blink-features=AutomationControlled"])
        ctx = b.new_context(locale="zh-CN", user_agent=UA)
        pg = ctx.new_page()
        pg.goto(subject_url, wait_until="load", timeout=60000)
        for _ in range(15):
            time.sleep(2)
            try:
                u = pg.url
            except Exception:
                continue
            if "subject" in u and "sec.douban" not in u:
                break
        og = pg.eval_on_selector_all("meta[property='og:image']",
                                     "els=>els.map(e=>e.content)")
        b.close()
        return og[0] if og else None


def upgrade_poster_url(og_url):
    """豆瓣 og:image 是 270x405 小图，用 photo/l 变体升级到 1080x1630"""
    m = re.search(r"/(?:view/)?photo/[^/]+/public/(p\d+)", og_url)
    if not m:
        return og_url, False
    pid = m.group(1)
    host_m = re.match(r"(https://[^/]+)", og_url)
    host = host_m.group(1) if host_m else "https://img3.doubanio.com"
    for path in (f"{host}/view/photo/l/public/{pid}.webp",
                 f"{host}/view/photo/l/public/{pid}.jpg",
                 og_url):
        try:
            req = urllib.request.Request(path, headers={"User-Agent": UA,
                                                       "Referer": "https://movie.douban.com/"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = r.read(100)
                ok = r.status == 200
            if ok and len(data) > 50:
                return path, path != og_url
        except Exception:
            continue
    return og_url, False


def download_image(url, dest_jpg, referer="https://movie.douban.com/"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
    raw = dest_jpg + ".raw"
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    with open(raw, "wb") as f:
        f.write(data)
    # webp/avif -> jpg（ffmpeg 通吃）
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw,
                        "-q:v", "2", dest_jpg],
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(dest_jpg):
        # PIL 兜底
        try:
            from PIL import Image
            Image.open(raw).convert("RGB").save(dest_jpg, "JPEG", quality=92)
        except Exception as e:
            os.remove(raw)
            raise RuntimeError(f"图片转换失败: {e} / ffmpeg:{r.stderr[:150]}")
    os.remove(raw)
    return os.path.getsize(dest_jpg)


def process(entry, force=False):
    url, infohash, title = entry["url"], entry["infohash"], entry["title"]
    cp, prog = qbt_content_path(infohash)
    if not cp:
        return "qBittorrent 中找不到该任务"
    if prog < 1:
        return f"下载未完成({prog:.0%})，跳过"
    videos = find_videos(cp)
    if not videos:
        return f"未找到视频文件: {cp}"
    folder = os.path.dirname(videos[0]) if os.path.isfile(cp) else cp
    base = os.path.splitext(videos[0])[0]
    targets = [base + ".jpg",
               os.path.join(folder, "folder.jpg"),
               os.path.join(folder, "poster.jpg")]
    if not force and all(os.path.exists(t) and os.path.getsize(t) > 5000
                         for t in targets):
        return "封面已存在"

    # 1) 站点详情 -> 豆瓣
    douban = get_douban_url(url)
    img_url = None
    if douban:
        try:
            img_url = douban_og_image(douban)
            if img_url:
                img_url, upgraded = upgrade_poster_url(img_url)
                log(f"  豆瓣封面{'(已升级大图)' if upgraded else ''}: {img_url}")
        except Exception as e:
            log(f"  豆瓣抓取失败: {e}")
    # 2) 回退：站点海报（详情页 code -> 384.webp）
    if not img_url:
        m = re.search(r"/mv/([A-Za-z0-9]+)", url)
        if m:
            img_url = f"https://s.tutu.pm/img/mv/{m.group(1)}/384.webp"
            log(f"  回退站点封面: {img_url}")
    if not img_url:
        return "拿不到封面 URL"

    ref = "https://movie.douban.com/" if "douban" in img_url else BASE + "/"
    sz = download_image(img_url, targets[0], referer=ref)
    import shutil
    for t in targets[1:]:
        shutil.copy2(targets[0], t)
    return f"OK {sz//1024}KB -> {os.path.basename(targets[0])} (+folder/poster.jpg)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", help="指定站点详情页")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if args.url:
        entries = [{"url": args.url, "infohash": "", "title": ""}]
        # 指定 url 模式没有 infohash -> 通过 --folder 简化：不支持，走历史
        raise SystemExit("--url 模式需配合历史记录，请直接跑默认模式")
    h = json.load(open(HISTORY, encoding="utf-8"))
    todo = h["movies"]
    log(f"历史电影 {len(todo)} 部，开始检查封面")
    for e in todo:
        try:
            msg = process(e, force=args.force)
        except Exception as ex:
            msg = f"❌ {ex}"
        log(f"  《{e.get('title','?')}》 {msg}")


if __name__ == "__main__":
    main()
