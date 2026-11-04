# -*- coding: utf-8 -*-
"""批量并发选片: 一次入列 N 部舞台节目, qB 并行下载, 慢种留慢速车道不删。
用法: python -X utf8 pick_batch.py [N=4]
"""
import sys, os, time, re, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import daily_movie as dm
from playwright.sync_api import sync_playwright

N = int(sys.argv[1]) if len(sys.argv) > 1 else 4
MIN_FREE_GB = dm.MIN_FREE_GB if hasattr(dm, "MIN_FREE_GB") else 10


def pick_one(pg, qbt, history, tried):
    """挑一部并入列; 返回 (title, size) 或 None(本轮无合格)"""
    done_urls = {m["url"] for m in history["movies"]} | {u.rstrip("/") for u in tried}
    done_hashes = {m.get("infohash", "").lower() for m in history["movies"]}
    existing = {h.lower() for h in qbt.hashes()}

    for attempt in range(4):
        list_urls = [f"{dm.BASE}/mv?sort=score&res=" + __import__('urllib.parse').parse.quote("磁力")
                     + f"&genre={__import__('urllib.parse').parse.quote(g)}&year={y}"
                     for g in dm.STAGE_GENRES for y in (120, 110, 100)]
        hrefs = []
        for lu in list_urls:
            dm.ensure_logged_in(pg, lu)
            hrefs += pg.eval_on_selector_all(
                'a[href*="/mv/"]',
                "els=>[...new Set(els.map(e=>e.href).filter(h=>/^https?:\\/\\/[^/]+\\/mv\\/[A-Za-z0-9]+\\/?$/.test(h)))]")
        hrefs = list(dict.fromkeys(hrefs))
        cands = [h for h in hrefs if h.rstrip("/") not in {u.rstrip("/") for u in done_urls}]
        random.shuffle(cands)
        best = None
        for url in cands[:12]:
            movie = dm.inspect_movie(pg, url, done_hashes, existing, min_seed=1)
            if not movie:
                continue
            if dm.STAGE_BAD_TITLE.search(movie["title"]):
                continue
            if not dm.STAGE_TITLE_PASS.search(movie["title"]):
                continue
            if movie.get("_rating", 10) < 7.2:  # 批量模式稍降线扩大供给
                continue
            if best is None or movie["seed"] > best["seed"]:
                best = movie
            if movie["seed"] >= 25:
                best = movie
                break
        if best:
            return best
    return None


def main():
    log = dm.log
    log("=" * 16 + f" 批量并发选片 x{N} " + "=" * 16)
    qbt = dm.Qbt()
    if not qbt.alive():
        qbt.start_app()
    qbt.login()
    history = dm.load_history()
    picked = []
    tried = []
    with sync_playwright() as pw:
        b, ctx = dm.new_browser(pw)
        pg = ctx.new_page()
        try:
            for i in range(N):
                free = dm.free_gb()
                if free < MIN_FREE_GB + 6:
                    log(f"磁盘 {free:.1f}GB 不足以再入列, 停止 (已选{len(picked)}部)")
                    break
                best = pick_one(pg, qbt, history, tried)
                if not best:
                    log(f"[{i+1}/{N}] 本轮无合格候选, 停止 (已选{len(picked)}部)")
                    break
                ih = best["infohash"]
                if ih in qbt.hashes():
                    tried.append(best["url"]); continue
                qbt.add_magnet(dm.augment_magnet(best["magnet"]))
                ok, desc = qbt.verify_started(ih, seconds=360)
                if not ok:
                    log(f"⚠ 启动失败({desc}): 《{best['title'][:30]}》 保留慢速车道")
                    # 慢速车道: 不删, 仍然登记(文件最终会落地)
                t = qbt.get(ih) or {}
                history["movies"].append({
                    "date": time.strftime("%Y-%m-%d"), "title": best["title"],
                    "url": best["url"], "infohash": ih, "size": best["size"],
                    "seed": best["seed"], "torrent": best["name"],
                    "folder": t.get("content_path"), "batch": True})
                dm.save_history(history)
                picked.append(best["title"])
                spd = (t.get("dlspeed") or 0) / 1024
                log(f"✅ [{i+1}/{N}] 入列《{best['title'][:36]}》 {best['size']} 做种{best['seed']} {spd:.0f}KB/s")
                tried.append(best["url"])
        finally:
            try:
                pg.context.storage_state(path=dm.STATE)
            except Exception:
                pass
            b.close()
    log(f"批量入列完成: {len(picked)}部 -> " + " | ".join(t[:24] for t in picked))
    print(json.dumps({"ok": True, "picked": picked}, ensure_ascii=False))


if __name__ == "__main__":
    main()
