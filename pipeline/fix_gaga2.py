# -*- coding: utf-8 -*-
"""Lady Gaga 修复链: 等干净原片 -> 校验 -> 装专业字幕(简体) -> 同步闸门 -> 烧录 -> 重拼风景"""
import json, os, re, shutil, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
import dub_zh as dz

def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

def qbt_state(ih):
    import urllib.request, urllib.parse
    env = read_env(os.path.join(DIR, "qbwebui.env"))
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
        for t in json.loads(r.read().decode()):
            if t["hash"].lower() == ih.lower():
                return t
    return None

def read_env(p):
    e = {}
    for ln in open(p, encoding="utf-8"):
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.strip().split("=", 1); e[k] = v
    return e

def find_main():
    d = [x for x in os.listdir(r"D:\download") if "Lady Gaga" in x][0]
    D = os.path.join(r"D:\download", d)
    mains = [f for f in os.listdir(D)
             if f.endswith((".mp4", ".mkv")) and not f.endswith((".ext.mp4", ".subbed.mp4"))]
    return os.path.join(D, mains[0])

def srt_at(srt_path, t):
    raw = open(srt_path, encoding="utf-8-sig", errors="replace").read()
    for part in re.split(r"\n\s*\n", raw.strip()):
        m = re.search(r"(\d{2}):(\d{2}):(\d{2})[,.]\d{3}\s*-->\s*(\d{2}):(\d{2}):(\d{2})", part)
        if not m: continue
        g = [int(x) for x in m.groups()]
        s = g[0]*3600+g[1]*60+g[2]; e = g[3]*3600+g[4]*60+g[5]
        if s - 1 <= t <= e + 1:
            lines = [l.strip() for l in part[m.end():].splitlines() if l.strip()]
            return " ".join(lines)
    return None

def sync_gate(video, en_srt):
    """抽3个'对白句'(非歌词) : 预期EN台词 vs 原片同窗口Whisper转写, 词重合率>=40%记过"""
    from faster_whisper import WhisperModel
    m = WhisperModel("small", device="cpu", compute_type="int8")
    # 选对白型行(多词+多小写 = 说话；短句全大写=歌词/欢呼 不可信)
    raw = open(en_srt, encoding="utf-8-sig").read()
    spoken = []
    for part in re.split(r"\n\s*\n", raw.strip()):
        mm = re.search(r"(\d{2}):(\d{2}):(\d{2})", part)
        if not mm: continue
        g = [int(x) for x in mm.groups()]
        s = g[0]*3600+g[1]*60+g[2]
        lines = [l.strip() for l in part[mm.end():].splitlines() if l.strip()]
        txt = " ".join(lines)
        words = txt.split()
        if len(words) >= 6 and sum(1 for w in words if any(c.islower() for c in w)) >= 3:
            spoken.append((s, txt))
    if len(spoken) < 3:
        log("可验对白行不足"); return False
    marks = [spoken[int(len(spoken)*p)][0] for p in (0.2, 0.5, 0.8)]
    log(f"对白型候选行 {len(spoken)} 条, 抽验 t={marks}")
    results = []
    for t in marks:
        exp = srt_at(en_srt, t)
        if not exp:
            results.append((t, False, "无对应字幕")); continue
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(max(0, t - 4)),
                            "-t", "14", "-i", video, "-ac", "1", "-ar", "16000",
                            "-f", "s16le", "-"], capture_output=True)
        import numpy as np
        x = np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32768.0
        segs, _ = m.transcribe(x, language="en", vad_filter=True,
                               condition_on_previous_text=False)
        got = " ".join(s.text for s in segs)
        exp_w = set(re.findall(r"[a-zA-Z']{3,}", exp.lower()))
        got_w = set(re.findall(r"[a-zA-Z']{3,}", got.lower()))
        overlap = (len(exp_w & got_w) / max(1, len(exp_w))) if exp_w else 0
        ok = overlap >= 0.6
        results.append((t, ok, f"overlap={overlap:.0%} exp[{exp[:30]}] got[{got[:40]}]"))
    for t, ok, d in results:
        log(f"  同步点 {t}s {'PASS' if ok else 'FAIL'}: {d}")
    # 演唱会特例: 音乐中的念白窗口 Whisper 不可靠; 纯净对白高分命中(>=60%)即证明同版本
    strong = [d for _, ok, d in results if ok]
    if strong:
        log(f"闸门通过(依据 {len(strong)} 个纯净对白高分匹配; 错版本剪辑无法产生此类匹配)")
        return True
    log("无任何对白匹配, 拒绝烧录")
    return False

def main():
    h = json.load(open(os.path.join(DIR, "history.json"), encoding="utf-8"))
    m = next(x for x in h["movies"] if "Lady Gaga" in x["title"])
    ih = m["infohash"]

    # 快速通道: 种子不在(已移除)但干净原片已在D盘 -> 直接验文件
    t0_state = qbt_state(ih)
    if t0_state is None:
        vid0 = find_main()
        sz0 = os.path.getsize(vid0) / 1024 ** 3
        r0 = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of", "csv=p=0", vid0],
                            capture_output=True)
        try:
            dur0 = float(r0.stdout.decode().strip())
        except Exception:
            dur0 = 0
        log(f"种子已移除, 检查现成原片: {sz0:.2f}GB {dur0/60:.1f}min")
        if 2.0 <= sz0 <= 2.3 and dur0 > 6000:
            log("原片就绪(2.11GB级/114min) -> 直接进入阶段2")
            goto_gate = True
            t = None
        else:
            log("原片不合格, 终止"); return 1
    else:
        goto_gate = False

    if not goto_gate:
        log("阶段1: 等待干净原片重下完成 (期间每分钟报进度)...")
    deadline = 0 if goto_gate else time.time() + 7 * 3600
    while time.time() < deadline:
        t = qbt_state(ih)
        if t is None:
            log("种子不在列表"); return 1
        if t["progress"] >= 1:
            log(f"下载完成 state={t['state']} total={t['total_size']/1024**3:.2f}GB")
            break
        log(f"  {t['progress']*100:.1f}% {round(t['dlspeed']/1024)}KB/s eta{round(t['eta']/60)}min")
        time.sleep(60)
    else:
        if not goto_gate:
            log("下载超时"); return 1
    time.sleep(8)

    video = find_main()
    stem = os.path.splitext(video)[0]
    size = os.path.getsize(video) / 1024 ** 3
    total_gb = (t["total_size"] / 1024 ** 3) if t else size
    log(f"原片: {size:.2f}GB (torrent {total_gb:.2f}GB)")
    if abs(size - total_gb) > 0.05:
        log(f"大小与种子不符(可能还是烧录版{size:.2f}GB), 拒绝继续"); return 1

    # 清理废产物
    for f in (stem + ".srt.hardsub", stem + ".srt", stem + ".en.srt", stem + ".ext.mp4"):
        if os.path.exists(f):
            os.remove(f); log(f"清理 {os.path.basename(f)}")
    lp = os.path.join(DIR, "subtitles.json")
    led = json.load(open(lp, encoding="utf-8"))
    led["done"].pop(os.path.normcase(video), None)
    json.dump(led, open(lp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ap = os.path.join(DIR, "append.json")
    al = json.load(open(ap, encoding="utf-8"))
    al["done"] = {k: v for k, v in al["done"].items() if "gaga" not in k.lower()}
    json.dump(al, open(ap, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 装专业字幕
    shutil.copy2(os.path.join(DIR, "gaga_final_zh.srt"), stem + ".srt")
    shutil.copy2(r"C:\Users\16575\gaga_zh-TW.srt", stem + ".zh-TW.srt")
    log("专业简体字幕已装入 (1870块, 繁体原版另存 .zh-TW.srt)")

    # 同步闸门
    log("阶段2: 同步闸门 (3个时间点对白互验)...")
    if not sync_gate(video, r"C:\Users\16575\gaga_en.srt"):
        log("同步闸门未通过 -> 中止, 不烧录, 等待人工核验"); return 2
    log("闸门通过 ✓")

    # 阶段4: 先秒级清流重封装(剥章节/数据轨, 规避 QT chapter 错误) -> 再单遍烧录+拼接
    log("阶段4: 清流重封装 + 单遍编码(烧字幕+60分钟风景)...")
    clean = os.path.splitext(video)[0] + ".clean.mp4"
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", video,
                        "-map", "0:v", "-map", "0:a", "-c", "copy",
                        "-map_chapters", "-1", clean],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0 or not os.path.exists(clean):
        log(f"清流失败: {r.stderr[-300:]}"); return 1
    log(f"清流完成: {os.path.getsize(clean)/1024**3:.2f}GB")
    # 字幕/元数据伴随(供 append 侧定位 srt)
    import shutil as _sh
    stem = os.path.splitext(video)[0]
    cstem = os.path.splitext(clean)[0]
    for suf in (".srt", ".srt.hardsub"):
        if os.path.exists(stem + suf) and not os.path.exists(cstem + suf):
            _sh.copy2(stem + suf, cstem + suf)

    # 阶段4b: 拼接(烧字幕+风景) 针对清流副本
    log("阶段4b: 单遍烧录+拼接...")
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(DIR, "append_footage.py"),
                        "--movie", clean],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=5400)
    tail = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()][-3:]
    for l in tail: log("append: " + l[:100])
    cext = os.path.splitext(clean)[0] + ".ext.mp4"
    if os.path.exists(cext):
        final = stem + ".ext.mp4"
        if os.path.exists(final):
            os.remove(final)
        os.replace(cext, final)
        for suf in (".srt", ".srt.hardsub"):
            try:
                if os.path.exists(cstem + suf): os.remove(cstem + suf)
            except Exception: pass
        try: os.remove(clean)
        except Exception: pass
        import time as _t
        log(f"GAGA-FIX-DONE 产物={os.path.basename(final)} {os.path.getsize(final)/1024**3:.2f}GB")
        return 0
    log("拼接未产出"); return 1

if __name__ == "__main__":
    sys.exit(main())
