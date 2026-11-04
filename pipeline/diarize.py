# -*- coding: utf-8 -*-
"""说话人聚类：字幕段 -> 原声音频片 -> resemblyzer 音色向量 -> 层次聚类
产出: dub_cache/<ep>_speakers.json {segments:[{s,e,spk}], n_spk, refs:{spk:[clip paths]}}
"""
import json, os, re, subprocess, sys, time
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
import dub_zh as dz

def diarize(video, k_range=(2, 7), threshold=None):
    stem = os.path.splitext(os.path.basename(video))[0]
    cache = os.path.join(DIR, "dub_cache", stem)
    os.makedirs(cache, exist_ok=True)
    # 字幕(优先 hardsub)
    srt = os.path.splitext(video)[0] + ".srt.hardsub"
    if not os.path.exists(srt):
        srt = os.path.splitext(video)[0] + ".srt"
    blocks = dz.parse_srt(srt)
    print(f"{stem[:40]} | 字幕段 {len(blocks)}")

    # 整片解码一次(48k 单声道足够做聚类)
    wav = os.path.join(cache, "_full48k.wav")
    if not os.path.exists(wav):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", video,
                        "-vn", "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", wav],
                       check=True)
    import wave as _w
    with _w.open(wav, "rb") as w:
        sr = w.getframerate()
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)

    import webrtcvad
    vad = webrtcvad.Vad(2)          # aggressiveness=2

    def vad_clean(seg16k):
        """只保留 30ms 有声帧，剔除 BGM/静音，返回纯净语音(16k)"""
        frame = int(0.03 * 16000)
        keep = []
        for i in range(0, len(seg16k) - frame, frame):
            f = seg16k[i:i + frame].tobytes()
            try:
                if vad.is_speech(f, 16000):
                    keep.append(seg16k[i:i + frame])
            except Exception:
                pass
        if not keep:
            return None
        out = np.concatenate(keep)
        return out if len(out) >= int(0.3 * 16000) else None

    from resemblyzer import VoiceEncoder
    ve = VoiceEncoder(device="cuda")
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics import silhouette_score

    from scipy.signal import resample_poly
    embs, idx = [], []
    for i, b in enumerate(blocks):
        a, z = int(b["s"] * sr), int(b["e"] * sr)
        a = max(0, a - int(0.1 * sr)); z = min(len(pcm), z + int(0.1 * sr))
        if z - a < int(0.35 * sr):
            continue
        seg = pcm[a:z].astype(np.float32) / 32768.0
        if np.abs(seg).mean() < 0.012:      # 太安静跳过
            continue
        # 48k -> 16k 后 VAD 清洗(去BGM)
        s16 = resample_poly(seg, 1, 3).astype(np.float32)
        s16i = np.clip(s16 * 32767, -32768, 32767).astype(np.int16)
        clean = vad_clean(s16i)
        if clean is None:
            continue
        try:
            embs.append(ve.embed_utterance(clean.astype(np.float32) / 32768.0))
            idx.append(i)
        except Exception:
            pass
    X = np.stack(embs)
    print(f"有效语音段 {len(X)} / {len(blocks)}")

    # 自动选 K(2..6) 取轮廓系数最优
    best = None
    for k in range(k_range[0], k_range[1] + 1):
        if len(X) <= k + 1: break
        cl = AgglomerativeClustering(n_clusters=k, metric="cosine", linkage="average")
        labels = cl.fit_predict(X)
        sc = silhouette_score(X, labels, metric="cosine")
        print(f"  k={k} silhouette={sc:.3f} sizes={np.bincount(labels).tolist()}")
        if best is None or sc > best[1]:
            best = (k, sc, labels)
    k, sc, labels = best
    print(f"==> 选定 k={k} (silhouette={sc:.3f})")

    segs = [{"s": blocks[j]["s"], "e": blocks[j]["e"], "text": blocks[j]["text"],
             "spk": int(labels[m])} for m, j in enumerate(idx)]
    # 每人取参考片段(按总时长排序, 取前3段, 存 wav)
    refs = {}
    from collections import defaultdict
    dur = defaultdict(float)
    for i, sp in enumerate(labels):
        b = blocks[idx[i]]
        dur[sp] += b["e"] - b["s"]
    order = sorted(dur, key=dur.get, reverse=True)
    print("角色时长(秒):", {f"spk{s}": round(dur[s], 1) for s in order})
    for sp in order:
        cands = [i for i in range(len(labels)) if labels[i] == sp]
        cands.sort(key=lambda i: (blocks[idx[i]]["e"] - blocks[idx[i]]["s"]), reverse=True)
        clips = []
        for n, i in enumerate(cands[:3]):
            b = blocks[idx[i]]
            out = os.path.join(cache, f"ref_spk{sp}_{n}.wav")
            a, z = int(b["s"] * sr), int(b["e"] * sr)
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", wav,
                            "-ss", str(a / sr), "-to", str(z / sr), out], check=False)
            if os.path.exists(out): clips.append(out)
        refs[str(sp)] = clips
    result = {"n_spk": k, "silhouette": round(sc, 3), "segments": segs, "refs": refs,
              "dur": {str(s): round(dur[s], 1) for s in order}}
    outp = os.path.join(cache, "_speakers.json")
    json.dump(result, open(outp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("saved:", outp)
    return result

if __name__ == "__main__":
    v = os.path.join(dz.FOLDER, "Sai.S01E02.Episode.2.1080p.NF.WEB-DL.AAC.2.0.H.264-BlackTV.mkv")
    t0 = time.time()
    diarize(v)
    print(f"total {time.time()-t0:.0f}s")
