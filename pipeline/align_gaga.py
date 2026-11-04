# -*- coding: utf-8 -*-
"""字幕-影片时移标定：GPU转写干净原片 -> 与EN专业字幕逐行模糊对齐 -> 估计恒定时移
若偏移稳定(std小+内点多) -> 输出平移后的新srt"""
import difflib, json, os, re, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
import dub_zh as dz

def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

def find_main():
    d = [x for x in os.listdir(r"D:\download") if "Lady Gaga" in x][0]
    D = os.path.join(r"D:\download", d)
    mains = [f for f in os.listdir(D)
             if f.endswith((".mp4", ".mkv")) and not f.endswith((".ext.mp4", ".subbed.mp4"))]
    return os.path.join(D, mains[0])

# CUDA DLL 注入(faster-whisper GPU 必需)
try:
    import torch
    os.environ["PATH"] = os.path.join(os.path.dirname(torch.__file__), "lib") + os.pathsep + os.environ.get("PATH", "")
except Exception:
    pass

def parse_srt_times(path):
    raw = open(path, encoding="utf-8-sig", errors="replace").read()
    out = []
    for part in re.split(r"\n\s*\n", raw.strip()):
        m = re.search(r"(\d{2}):(\d{2}):(\d{2})[,.]\d{3}\s*-->\s*(\d{2}):(\d{2}):(\d{2})", part)
        if not m: continue
        g = [int(x) for x in m.groups()]
        s = g[0]*3600+g[1]*60+g[2]
        lines = [l.strip() for l in part[m.end():].splitlines() if l.strip()]
        txt = " ".join(lines)
        out.append((s, txt))
    return out

def main():
    video = find_main()
    en_srt = r"C:\Users\16575\gaga_en.srt"

    # 1) GPU 全片转写(缓存)
    tr_cache = os.path.join(DIR, "dub_cache", "gaga_align.json")
    if os.path.exists(tr_cache):
        tr = json.load(open(tr_cache, encoding="utf-8"))
        log(f"转写缓存命中 ({len(tr)} 行)")
    else:
        from faster_whisper import WhisperModel
        log("GPU 全片转写中(~8-12min)...")
        t0 = time.time()
        m = WhisperModel("small", device="cuda", compute_type="int8_float16")
        segs, info = m.transcribe(video, language="en", vad_filter=True,
                                  condition_on_previous_text=False)
        tr = [[round(s.start, 2), s.text.strip()] for s in segs if s.text.strip()]
        json.dump(tr, open(tr_cache, "w", encoding="utf-8"))
        log(f"转写完成 {len(tr)} 行 用时{time.time()-t0:.0f}s 语言={info.language}")

    # 2) 对齐: 每隔取样的字幕行 -> 转写行 找最佳模糊匹配 -> 时移
    subs = parse_srt_times(en_srt)
    step = max(1, len(subs) // 150)
    pairs = []  # (sub_time, trans_time, score, is_lyric_likely)
    for st, txt in subs[::step]:
        clean = re.sub(r"[^a-zA-Z' ]", "", txt).lower().strip()
        words = [w for w in clean.split() if len(w) >= 3]
        if len(words) < 3:
            continue
        key = " ".join(words[:8])
        best, best_score = None, 0
        for ts, tt in tr:
            score = difflib.SequenceMatcher(None, key, re.sub(r"[^a-zA-Z' ]", "", tt).lower()[:70]).ratio()
            if score > best_score:
                best_score, best = score, ts
        if best is not None:
            pairs.append((st, best, best_score))
    # 高置信对齐(>=0.8: 基本只有真实对白能命中)
    hi = [(s, t) for s, t, sc in pairs if sc >= 0.8]
    all_ = [(s, t) for s, t, sc in pairs if sc >= 0.55]
    log(f"对齐样本: 全部{len(all_)}, 高置信{len(hi)}")
    import statistics
    use = hi if len(hi) >= 8 else all_
    if len(use) < 8:
        log(f"可对齐样本过少({len(use)}) -> 无法标定"); log("VERDICT: INCOMPATIBLE"); return 2
    diffs = [round(s - t, 1) for s, t in use]
    med = statistics.median(diffs)
    std = statistics.pstdev(diffs)
    inl = sum(1 for d in diffs if abs(d - med) < 3)
    log(f"样本 {len(use)} | 时移中位 {med:.1f}s std={std:.1f}s 内点={inl}/{len(diffs)}")
    log("样本: " + "; ".join(f"{s:.0f}->{t:.0f}" for s, t in use[:8]))
    if inl / len(diffs) < 0.6 or std > 3:
        log("偏移不稳定 -> 无法机械平移"); log("VERDICT: INCOMPATIBLE"); return 2
    shift = med
    if abs(shift) < 3:
        log(f"字幕基本对齐(偏移{shift:+.1f}s在容差内) 无需平移")
        log("VERDICT: ALIGNED-OK")
        return 0

    # 3) 平移: 字幕时间 + med (负值表示字幕比影片晚, 需前移)
    shift = med
    log(f"偏移稳定, 应用时移 {shift:+.1f}s 到简体/繁体/英文字幕")
    for f in (os.path.join(os.path.dirname(video),
              "Lady.Gaga.Presents.The.Monster.Ball.Tour.At.Madison.Square.Garden.2011.1080p.BluRay.x264.AAC5.1-[YTS.MX].srt"),
              r"C:\Users\16575\daily-movie\gaga_final_zh.srt", en_srt):
        if not os.path.exists(f):
            continue
        raw = open(f, encoding="utf-8-sig").read()
        parts = re.split(r"(\n\s*\n)", raw)
        out = []
        for seg in parts:
            m = re.search(r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})", seg)
            if m:
                g = [int(x) for x in m.groups()]
                s = g[0]*3600+g[1]*60+g[2]+g[3]/1000 + shift
                e = g[4]*3600+g[5]*60+g[6]+g[7]/1000 + shift
                s, e = max(0.0, s), max(0.1, e)
                ns = dz.ts(s); ne = dz.ts(e)
                seg = re.sub(r"\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,.]\d{3}",
                             f"{ns} --> {ne}", seg)
            out.append(seg)
        newp = f + ".shift" if not f.endswith(".srt") else f[:-4] + ".shift.srt" if False else f
        # 直接原地写(旧版本已不需要)
        open(f, "w", encoding="utf-8").write("".join(out))
        log(f"已平移: {os.path.basename(f)[:50]}")
    log("VERDICT: SHIFTED-OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
