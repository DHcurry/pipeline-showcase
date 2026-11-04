# -*- coding: utf-8 -*-
"""为视频生成简介 txt（存视频同目录，<视频名>.txt）。

通道:
  A) 每日电影(有站点详情页)   -> 站点"电影简介"段落
  B) 其他视频(豆瓣搜索)        -> 豆瓣条目 og:description
用法:
  python fetch_intro.py              # 处理历史电影 + D:\\download 中缺简介的视频
  python fetch_intro.py --video F.mp4 --query "搜索词"   # 单文件(豆瓣)
  python fetch_intro.py --site-only / --folder-only
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY = os.path.join(DIR, "history.json")
STATE = os.path.join(DIR, "state.json")
LOG = os.path.join(DIR, "intro.log")
QBT_ENV = os.path.join(DIR, "qbwebui.env")
BASE = "https://www.hgeme.com"  # 2026-10-22 新源(同平台)
BASE_OLD = "https://www.xn--wcv59z.com"
SCAN = r"E:\movies"  # 管线专属目录
LEGACY_SCAN = r"D:\download"  # 过渡期存量
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
VIDEO_EXTS = {".mkv", ".mp4", ".avi", ".ts", ".mov", ".wmv", ".flv"}
DERIVED = (".ext.mp4", ".testext.mp4", ".subbed.mp4", ".bilingual.mp4", ".burning.mp4")
JUNK = re.compile(r"科学上网|^\s*[×x]\s*$|地址发布页|禁止在社交平台|低调使用|^\s*$")


def norm_path(p):
    """git-bash 风格 /d/x -> D:\\x"""
    m = re.match(r"^/([A-Za-z])/(.+)$", p)
    if m:
        return m.group(1).upper() + ":\\" + m.group(2).replace("/", "\\")
    return p


def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def browser(pw):
    b = pw.chromium.launch(headless=True,
                           args=["--disable-blink-features=AutomationControlled"])
    ctx = b.new_context(locale="zh-CN",
                        user_agent=UA, viewport={"width": 1440, "height": 900},
                        storage_state=STATE if os.path.exists(STATE) else None)
    return b, ctx


def wait_pw(pg, n=20):
    for _ in range(n):
        time.sleep(1)
        if "验证" not in pg.title():
            break


def qbt_paths():
    """{infohash: content_path} 已完成任务"""
    import urllib.request, urllib.parse
    env = {}
    for ln in open(QBT_ENV, encoding="utf-8"):
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.strip().split("=", 1)
            env[k] = v
    base = env.get("QBT_URL", "http://127.0.0.1:8080")
    try:
        req = urllib.request.Request(base + "/api/v2/auth/login",
              data=urllib.parse.urlencode({"username": env.get("QBT_USER", ""),
                                            "password": env.get("QBT_PASS", "")}).encode())
        with urllib.request.urlopen(req, timeout=8) as r:
            scs = r.headers.get_all("Set-Cookie") or []
            cookie = "; ".join(c.split(";")[0] for c in scs)
        req2 = urllib.request.Request(base + "/api/v2/torrents/info")
        req2.add_header("Cookie", cookie)
        with urllib.request.urlopen(req2, timeout=8) as r:
            ts = json.loads(r.read().decode())
        return {t["hash"].lower(): t.get("content_path") for t in ts
                if t.get("progress", 1) >= 1 and t.get("content_path")}
    except Exception as e:
        log(f"qBittorrent 查询失败: {e}")
        return {}


def find_videos(folder):
    out = []
    if os.path.isfile(folder):
        return [folder]
    for root, _, files in os.walk(folder):
        for fn in files:
            if (os.path.splitext(fn)[1].lower() in VIDEO_EXTS
                    and not fn.lower().endswith(DERIVED)):
                out.append(os.path.join(root, fn))
    return out


def intro_from_site(pg, detail_url):
    pg.goto(detail_url, wait_until="domcontentloaded", timeout=60000)
    wait_pw(pg)
    time.sleep(1.5)
    txt = pg.inner_text("body")
    i = txt.find("电影简介")
    if i < 0:
        i = txt.find("简介")
    j = txt.find("磁力资源", i)
    if i < 0:
        return None
    seg = txt[i:j if j > i else i + 1200]
    lines = [l.strip() for l in seg.splitlines()
             if l.strip() and not JUNK.search(l.strip())
             and l.strip() not in ("电影简介", "简介", "×")]
    body = "\n".join(lines)
    return body if len(body) > 30 else None


def intro_from_douban(pg, query):
    """豆瓣搜索 -> 第一个匹配条目 -> og:description"""
    q = urllib_quote(query)
    pg.goto(f"https://search.douban.com/movie/subject_search?search_text={q}&cat=1002",
            wait_until="domcontentloaded", timeout=60000)
    pass_challenge(pg, need_links=True)
    links = pg.eval_on_selector_all(
        "a[href*='movie.douban.com/subject/']",
        "els=>[...new Set(els.map(e=>e.href.match(/subject\\/(\\d+)/)?e.href:'').filter(Boolean))]")
    if not links:
        return None, None, None
    # 优先标题含查询关键词的条目
    title_links = pg.eval_on_selector_all(
        "a[href*='movie.douban.com/subject/']",
        "els=>els.map(e=>({h:e.href, t:(e.innerText||'').trim()}))")
    chosen = None
    key = re.split(r"[\s\[\]【】]", query.strip())[0]
    for it in title_links:
        if key and key in it.get("t", ""):
            chosen = it["h"]; break
    chosen = chosen or links[0]

    pg.goto(chosen, wait_until="load", timeout=60000)
    pass_challenge(pg, need_links=False, tries=12)
    for _ in range(6):
        time.sleep(1)
        if "subject" in pg.url and "sec.douban" not in pg.url:
            break
    meta = pg.eval_on_selector_all("meta[property='og:description'], meta[name='description']",
                                   "els=>els.map(e=>e.content)")
    title = pg.eval_on_selector_all("meta[property='og:title']",
                                    "els=>els.map(e=>e.content)")
    desc = next((m for m in meta if m and len(m) > 20), None)
    return desc, (title[0] if title else None), chosen


def pass_challenge(pg, need_links=False, tries=8):
    """过豆瓣 sec 挑战页：点'点我继续浏览'；need_links 时等到出结果链接"""
    for _ in range(tries):
        time.sleep(1.5)
        try:
            if "sec.douban" in pg.url:
                btn = pg.locator("text=点我继续浏览")
                if btn.count():
                    btn.first.click()
                    time.sleep(1.5)
                    continue
            if not need_links:
                return True
            if pg.locator("a[href*='movie.douban.com/subject/']").count():
                return True
        except Exception:
            pass
    return not need_links or pg.locator("a[href*='movie.douban.com/subject/']").count() > 0


def urllib_quote(s):
    import urllib.parse
    return urllib.parse.quote(s)


def write_txt(video, title, source, body):
    stem = os.path.splitext(video)[0]
    out = stem + ".txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"片名：{title}\n来源：{source}\n抓取：{datetime.now():%Y-%m-%d %H:%M}\n"
                f"{'='*40}\n{body}\n")
    return out


def process_video(pg, video, site_url=None, query=None):
    stem = os.path.splitext(video)[0]
    if os.path.exists(stem + ".txt") and os.path.getsize(stem + ".txt") > 80:
        return "已有简介"
    title = os.path.splitext(os.path.basename(video))[0]
    if site_url:
        body = intro_from_site(pg, site_url)
        # 站点常见英文原版简介 -> 中文片优先豆瓣
        cjk = sum(1 for c in (body or "") if "\u4e00" <= c <= "\u9fff")
        if body and cjk >= 20:
            p = write_txt(video, title, "站点详情页", body)
            return f"OK(站点) -> {os.path.basename(p)}"
        if body:
            try:
                desc, dtitle, link = intro_from_douban(pg, query or title)
                if desc:
                    p = write_txt(video, dtitle or title, f"豆瓣 {link}（站点备选原文见log）", desc)
                    return f"OK(豆瓣中文) -> {os.path.basename(p)}"
            except Exception:
                pass
            p = write_txt(video, title, "站点详情页(英文原文)", body)
            return f"OK(站点英文) -> {os.path.basename(p)}"
    if query or not site_url:
        try:
            desc, dtitle, link = intro_from_douban(pg, query or title)
        except Exception as e:
            return f"豆瓣搜索失败: {e}"
        if desc:
            p = write_txt(video, dtitle or title, f"豆瓣 {link}", desc)
            return f"OK(豆瓣:{dtitle}) -> {os.path.basename(p)}"
        return "豆瓣未找到匹配条目"
    return "无简介来源"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video")
    ap.add_argument("--query")
    ap.add_argument("--site-only", action="store_true")
    ap.add_argument("--folder-only", action="store_true")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b, ctx = browser(pw)
        pg = ctx.new_page()
        try:
            if args.video:
                log(process_video(pg, os.path.abspath(norm_path(args.video)), query=args.query))
                return
            jobs = []  # (video, site_url, query)
            if not args.folder_only:
                # 历史电影 -> 站点（优先实时 content_path，退历史 folder 字段）
                paths = qbt_paths()
                h = json.load(open(HISTORY, encoding="utf-8"))
                for m in h["movies"]:
                    cp = paths.get((m.get("infohash") or "").lower()) or m.get("folder")
                    if not cp or not os.path.exists(cp):
                        continue
                    for v in find_videos(cp):
                        jobs.append((v, m["url"], None))
            if not args.site_only:
                # 扫盘：缺简介txt的视频 -> 豆瓣
                for v in find_videos(SCAN) + find_videos(LEGACY_SCAN):
                    if any(os.path.abspath(v) == os.path.abspath(j[0]) for j in jobs):
                        continue
                    stem = os.path.splitext(v)[0]
                    if os.path.exists(stem + ".txt"):
                        continue
                    q = query_hint(v)
                    jobs.append((v, None, q))
            log(f"待处理 {len(jobs)} 个视频")
            for v, url, q in jobs:
                try:
                    msg = process_video(pg, v, site_url=url, query=q)
                except Exception as e:
                    msg = f"❌ {e}"
                log(f"  {os.path.basename(v)[:55]}: {msg}")
        finally:
            try:
                ctx.storage_state(path=STATE)
            except Exception:
                pass
            b.close()
    log("==== 简介抓取完成 ====")


def query_hint(video):
    """从文件/目录名提取豆瓣搜索词（去发布组、编码等噪声）"""
    folder = os.path.basename(os.path.dirname(video))
    name = os.path.splitext(os.path.basename(video))[0]
    # 剧集文件夹优先
    q = folder
    q = re.sub(r"【[^】]*】|\[.*?\]|\(.*?\)", " ", q)
    q = re.sub(r"www\.\S+|1080p|720p|4K|WEB-DL|WEBRip|x26[45]|AAC.*?H\.?\d*|NF\b|BlueTV|YTS.*|BONE|-\s*\w+$",
               " ", q, flags=re.I)
    q = " ".join(q.split())[:30]
    if not q:
        q = name[:20]
    return q


if __name__ == "__main__":
    main()
