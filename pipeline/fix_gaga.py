# -*- coding: utf-8 -*-
"""Lady Gaga 演唱会字幕重制 Phase1: 等干净原片 -> Demucs人声 -> 转写(带时间闸门) -> 中文翻译
不烧录(留人工核验)。"""
import json, os, re, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
import dub_zh as dz

def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

def qbt_progress(infohash):
    import urllib.request, urllib.parse
    env = {}
    for ln in open(os.path.join(DIR, "qbwebui.env"), encoding="utf-8"):
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.strip().split("=", 1)
            env[k] = v
    base = env.get("QBT_URL", "http://127.0.0.1:8080")
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
    for t in ts:
        if t["hash"].lower() == infohash.lower():
            return t.get("progress", 0), t.get("state", "")
    return None, None

def find_main():
    d = [x for x in os.listdir(r"D:\download") if "Lady Gaga" in x][0]
    D = os.path.join(r"D:\download", d)
    mains = [f for f in os.listdir(D)
             if (f.endswith(".mp4") or f.endswith(".mkv")) and not f.endswith((".ext.mp4", ".subbed.mp4"))]
    return os.path.join(D, mains[0])

def sanity_filter(blocks, max_cps=18, min_cps=1.2):
    """时间闸门: 字符/秒 合理性(说话速率约2-8字/秒, 放宽到1.2-18)"""
    kept, dropped = [], 0
    for b in blocks:
        chars = len(re.sub(r"[，。？！…\s-]", "", b["text"]))
        dur = max(0.3, b["e"] - b["s"])
        cps = chars / dur
        if cps < min_cps or cps > max_cps:
            dropped += 1
            continue
        kept.append(b)
    return kept, dropped

def main():
    h = json.load(open(os.path.join(DIR, "history.json"), encoding="utf-8"))
    m = next(x for x in h["movies"] if "Lady Gaga" in x["title"])
    ih = m["infohash"]

    # 1) 等干净原片下载完成
    log("等待原片重下完成...")
    for i in range(120):
        p, st = qbt_progress(ih)
        if p is None:
            log("种子不在列表!? 终止"); return 1
        if p >= 1:
            log(f"下载完成 (state={st})"); break
        if i % 6 == 0:
            log(f"  进度 {p*100:.1f}% state={st}")
        time.sleep(10)
    else:
        log("下载超时未完成"); return 1
    time.sleep(5)

    video = find_main()
    stem = os.path.splitext(video)[0]
    log(f"视频: {os.path.basename(video)} ({os.path.getsize(video)/1024**3:.2f}GB)")

    # 2) 清理废字幕与旧ext/台账
    for f in (stem + ".srt.hardsub", stem + ".srt", stem + ".en.srt",
              stem + ".ext.mp4", stem + ".srt.hardsub.ext"):
        if os.path.exists(f):
            os.remove(f); log(f"清理: {os.path.basename(f)}")
    lp = os.path.join(DIR, "subtitles.json")
    led = json.load(open(lp, encoding="utf-8"))
    led["done"].pop(os.path.normcase(video), None)
    json.dump(led, open(lp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ap = os.path.join(DIR, "append.json")
    al = json.load(open(ap, encoding="utf-8"))
    al["done"] = {k: v for k, v in al["done"].items() if "gaga" not in k.lower()}
    json.dump(al, open(ap, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log("台账已清理(重做就绪)")

    # 3) Demucs 人声分离
    cache = os.path.join(DIR, "dub_cache", "gaga_fix")
    os.makedirs(cache, exist_ok=True)
    voc_out = os.path.join(cache, "htdemucs", os.path.splitext(os.path.basename(video))[0])
    vocals = os.path.join(voc_out, "vocals.mp3")
    if not os.path.exists(vocals):
        log("Demucs 人声分离中(~12min)...")
        t0 = time.time()
        r = subprocess.run([sys.executable, "-m", "demucs", "--two-stems", "vocals",
                            "-n", "htdemucs", "-o", cache, "--mp3", video],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=2400)
        if r.returncode != 0:
            log(f"demucs FAIL: {r.stderr[-300:]}"); return 1
        log(f"demucs done {time.time()-t0:.0f}s")
    assert os.path.exists(vocals), vocals

    # 4) 人声轨转写(English, 防幻觉参数)
    from faster_whisper import WhisperModel
    log("转写人声轨(GPU)...")
    t0 = time.time()
    m = WhisperModel("small", device="cuda", compute_type="int8_float16")
    segs, info = m.transcribe(vocals, language="en", vad_filter=True,
                              condition_on_previous_text=False,
                              initial_prompt="Live concert, Lady Gaga speaking to the audience between songs.")
    blocks = []
    for s in segs:
        if s.start > 6900: break
        txt = s.text.strip()
        if txt:
            blocks.append({"s": s.start, "e": s.end, "text": txt})
    log(f"原始 {len(blocks)} 块, 语言={info.language}, 用时{time.time()-t0:.0f}s")

    # 时间闸门
    kept, dropped = sanity_filter(blocks)
    log(f"闸门: 保留 {len(kept)} / 丢弃 {dropped}")
    if len(kept) < 60:
        log("合格块过少, 失败"); return 1

    # 5) 写中文srt(先英文中间稿->翻译管线)
    en_srt = stem + ".gaga.en.srt"
    with open(en_srt, "w", encoding="utf-8") as f:
        for i, b in enumerate(kept, 1):
            f.write(f"{i}\n{dz.ts(b['s'])} --> {dz.ts(b['e'])}\n{b['text']}\n\n")
    log(f"英文稿: {en_srt} ({len(kept)}块)")

    # 用既有翻译管线: 把英文稿复制为主srt后调 translate_file
    main_srt = stem + ".srt"
    import shutil
    shutil.copy2(en_srt, main_srt)
    import translate_srt as tr
    msg = tr.translate_file(main_srt, "en", force=True)
    log(f"翻译: {msg}")
    log("PHASE1-DONE — 等待人工核验后进入烧录")
    return 0

if __name__ == "__main__":
    sys.exit(main())
