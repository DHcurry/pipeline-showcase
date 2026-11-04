# -*- coding: utf-8 -*-
"""灾 E02-E06 克隆版配音重制（CosyVoice2 每角色克隆原声线）：
人声分离(Demucs) -> 生产版聚类(k5+微簇合并) -> 每角色参考音+日语prompt ->
逐句克隆合成中文(缓存断点) -> duck混音 -> 封装替换(克隆轨置顶, 日语原声保留)
用 venv 运行: cosyvoice_env/venv/Scripts/python dub_clone.py --ep E02 [--skip-demucs]
"""
import argparse, json, os, re, subprocess, sys, tempfile, time
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# ---- 环境纠偏（必须在其它三方 import 之前）----
# 1) 嵌套 venv 的 site-packages 被排到了 sys.path 末尾（父环境遮蔽 venv 包），
#    强制置前，保证 venv 的 onnxruntime-gpu/numpy1.26 优先生效
_VSP = os.path.abspath(os.path.join(os.path.dirname(sys.executable), os.pardir,
                                    "Lib", "site-packages"))
if os.path.isdir(_VSP):
    _rest = [p for p in sys.path
             if os.path.normcase(os.path.normpath(p)) != os.path.normcase(_VSP)]
    sys.path[:] = [""] + [_VSP] + [p for p in _rest if p]
# 2) CUDA DLL 注入（onnxruntime-gpu 与 torch 都需要 torch/lib 里的库）
import torch as _torch
os.environ["PATH"] = os.path.join(os.path.dirname(_torch.__file__), "lib") + \
    os.pathsep + os.environ.get("PATH", "")
# --------------------------------------------------------

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
import numpy as np
import dub_zh as dz
from burn_subs import acquire_lock

CV_REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       os.pardir, "cosyvoice_env", "CosyVoice")
CV_REPO = os.path.abspath(CV_REPO)
if CV_REPO not in sys.path:
    sys.path.insert(0, CV_REPO)

MDL = r"C:\Users\16575\cosyvoice_env\models\CosyVoice2-0.5B"
SAI = dz.FOLDER
EP_MAP = {"E02": 2, "E03": 3, "E04": 4, "E05": 5, "E06": 6}
DUCK, RAMP = 0.30, 0.08

def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", **kw)

def episode_files(ep):
    n = EP_MAP[ep]
    name = f"Sai.S01E0{n}.Episode.{n}.1080p.NF.WEB-DL.AAC.2.0.H.264-BlackTV"
    video = os.path.join(SAI, name + ".mkv")
    return video, os.path.join(SAI, name + ".jpn.srt")

def vocals_of(ep, video):
    out_root = os.path.join(DIR, "dub_cache", f"demucs_{ep}")
    sub = os.path.join(out_root, "htdemucs", os.path.splitext(os.path.basename(video))[0])
    v = os.path.join(sub, "vocals.mp3")
    if not os.path.exists(v):
        log(f"{ep} Demucs 人声分离中(~12min)...")
        t0 = time.time()
        r = run([sys.executable, "-m", "demucs", "--two-stems", "vocals",
                 "-n", "htdemucs", "-o", out_root, "--mp3", video], timeout=2400)
        if r.returncode != 0:
            raise RuntimeError(f"demucs failed: {r.stderr[-300:]}")
        log(f"{ep} demucs done {time.time()-t0:.0f}s")
    return v

def cluster_of(ep, video, vocals, jpn_srt):
    cache = os.path.join(DIR, "dub_cache", os.path.splitext(os.path.basename(video))[0])
    os.makedirs(cache, exist_ok=True)
    p = os.path.join(cache, "_speakers_v.json")
    if os.path.exists(p):
        log(f"{ep} 聚类缓存命中")
        return json.load(open(p, encoding="utf-8")), cache, vocals
    log(f"{ep} 聚类(Demucs人声 + 音色向量, k=5+微簇合并)...")
    from resemblyzer import VoiceEncoder
    from sklearn.cluster import AgglomerativeClustering
    from collections import defaultdict
    blocks = dz.parse_srt(os.path.splitext(video)[0] + ".srt.hardsub")
    wav16 = os.path.join(cache, "_vocals16k.wav")
    if not os.path.exists(wav16):
        run(["ffmpeg", "-y", "-v", "error", "-i", vocals, "-ac", "1",
             "-ar", "16000", "-c:a", "pcm_s16le", wav16], check=True)
    import wave as _w
    with _w.open(wav16, "rb") as w:
        sr = w.getframerate()
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    ve = VoiceEncoder(device="cuda")
    embs, idx = [], []
    for i, b in enumerate(blocks):
        a, z = int(b["s"]*sr), int(b["e"]*sr)
        a = max(0, a-int(0.1*sr)); z = min(len(pcm), z+int(0.1*sr))
        if z-a < int(0.35*sr): continue
        seg = pcm[a:z].astype(np.float32)/32768.0
        if np.abs(seg).mean() < 0.006: continue
        embs.append(ve.embed_utterance(seg)); idx.append(i)
    X = np.stack(embs)
    labels = AgglomerativeClustering(n_clusters=5, metric="cosine",
                                     linkage="average").fit_predict(X)
    dur = defaultdict(float)
    for m, sp in enumerate(labels):
        b = blocks[idx[m]]; dur[sp] += b["e"]-b["s"]
    big = max(dur, key=dur.get)
    merged = [big if dur[sp] < 8 else sp for sp in labels]
    dur2 = defaultdict(float)
    for m, sp in enumerate(merged):
        b = blocks[idx[m]]; dur2[sp] += b["e"]-b["s"]
    rank = sorted(dur2, key=dur2.get, reverse=True)
    remap = {o: i for i, o in enumerate(rank)}
    segs = [{"s": blocks[j]["s"], "e": blocks[j]["e"], "text": blocks[j]["text"],
             "spk": remap[merged[m]]} for m, j in enumerate(idx)]
    refs = {}
    for old, spk in remap.items():
        c = [m for m in range(len(merged)) if merged[m] == old]
        c.sort(key=lambda m: blocks[idx[m]]["e"]-blocks[idx[m]]["s"], reverse=True)
        refs[str(spk)] = [{"s": blocks[idx[m]]["s"], "e": blocks[idx[m]]["e"]}
                          for m in c[:3]]
    data = {"n_spk": len(rank), "segments": segs, "refs": refs,
            "dur": {str(remap[s]): round(dur2[s], 1) for s in rank}}
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log(f"{ep} 聚类完成 角色时长={data['dur']}")
    return data, cache, vocals

def _clean_prompt(s):
    """清洗 prompt：隐形方向符/零宽、SDH标记、前导时间戳残渣(如 ',467')"""
    s = re.sub(r"[\u200a-\u202f\u2060\ufeff]", "", s)
    s = re.sub(r"^[\d,:.\s]+", "", s)
    s = re.sub(r"<[^>]{0,20}>", "", s)
    return re.sub(r"\s+", " ", s).strip()


def ja_text_at(jpn_srt, t):
    raw = open(jpn_srt, encoding="utf-8-sig", errors="replace").read()
    for part in re.split(r"\n\s*\n", raw.strip()):
        m = re.search(r"(\d{2}):(\d{2}):(\d{2})[,.]\d{3}\s*-->\s*"
                      r"(\d{2}):(\d{2}):(\d{2})[,.]\d{3}", part)
        if not m: continue
        g = [int(x) for x in m.groups()]
        s = g[0]*3600+g[1]*60+g[2]
        if abs(s - t) <= 1.2:
            lines = [l.strip() for l in part[m.end():].splitlines() if l.strip()]
            txt = _clean_prompt(" ".join(lines))
            return txt or None
    return None

def speed_of(text):
    if text.endswith(("？", "?")): return 1.0
    if text.endswith(("！", "!")): return 1.08
    if "……" in text or text.endswith("…"): return 0.92
    return 1.0

def clone_synth(ep, video, data, cache, vocals, jpn_srt):
    from cosyvoice.cli.cosyvoice import CosyVoice2
    c2 = CosyVoice2(MDL, fp16=True)
    # 关键优化: prompt 侧(语音特征/音色token/说话人嵌入/文本token)按输入缓存,
    # 否则每句都重算参考音特征 -> 实测拖到20s/句
    fe = c2.frontend
    _cache = {}

    def _memo(orig, keyfn):
        def wrap(*a, **k):
            key = keyfn(a, k)
            if key in _cache:
                return _cache[key]
            r = orig(*a, **k)
            _cache[key] = r
            return r
        return wrap

    def _wav_key(a, k):
        v = a[0] if a else k.get("prompt_wav")
        return v if isinstance(v, str) else id(v)

    # 注意: 每个函数必须带独立前缀, 否则同 wav 路径的键互相串值
    # (曾因此 spk_embedding 拿到 speech_feat 的 tuple -> .to() 崩)
    fe._extract_speech_feat = _memo(fe._extract_speech_feat,
                                    lambda a, k: ("feat", _wav_key(a, k)))
    fe._extract_speech_token = _memo(fe._extract_speech_token,
                                     lambda a, k: ("tok", _wav_key(a, k)))
    fe._extract_spk_embedding = _memo(fe._extract_spk_embedding,
                                      lambda a, k: ("emb", _wav_key(a, k)))
    fe._extract_text_token = _memo(fe._extract_text_token,
                                   lambda a, k: ("txt", a[0] if a else ""))
    spk_prompt = {}
    for spk, refs in data["refs"].items():
        r0 = refs[0]
        clip = os.path.join(cache, f"refc_spk{spk}.wav")
        if not os.path.exists(clip):
            run(["ffmpeg", "-y", "-v", "error", "-ss", str(r0["s"]),
                 "-to", str(r0["e"]), "-i", vocals, clip], check=False)
        jt = ja_text_at(jpn_srt, r0["s"])
        if not jt:
            jt = ja_text_at(jpn_srt, refs[1]["s"] if len(refs) > 1 else r0["s"])
        spk_prompt[spk] = (clip, jt or "はい。")
        log(f"{ep} spk{spk} 参考={os.path.basename(clip)} 时长={r0['e']-r0['s']:.1f}s 文本={jt!r}")
    synth_dir = os.path.join(cache, "clone_synth")
    os.makedirs(synth_dir, exist_ok=True)
    t0 = time.time()
    ok = 0
    _cache_hit = 0
    for i, seg in enumerate(data["segments"]):
        out = os.path.join(synth_dir, f"u{i:04d}.wav")
        if os.path.exists(out) and os.path.getsize(out) > 400:
            ok += 1; _cache_hit += 1; continue
        clip, ptxt = spk_prompt[str(seg["spk"])]
        try:
            outs = list(c2.inference_zero_shot(seg["text"], ptxt, clip,
                                               stream=False,
                                               speed=min(1.3, speed_of(seg["text"]) * 1.1)))
            speech = np.concatenate([np.asarray(o["tts_speech"]) for o in outs], axis=0)
            speech = np.squeeze(speech).astype(np.float32)
            import wave as _w
            pcm16 = (np.clip(speech, -1, 1) * 32767).astype(np.int16)
            with _w.open(out, "wb") as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(22050)
                wf.writeframes(pcm16.tobytes())
            ok += 1
        except Exception as e:
            log(f"{ep} 句{i}失败: {str(e)[:80]}")
        if (i+1) % 50 == 0:
            avg = (time.time()-t0) / max(1, ok)
            log(f"{ep} 克隆合成 {i+1}/{len(data['segments'])} "
                f"({time.time()-t0:.0f}s, 平均{avg:.1f}s/句, 缓存{_cache_hit}命中)")
    log(f"{ep} 合成完成 {ok}/{len(data['segments'])} 用时 {time.time()-t0:.0f}s")
    return synth_dir

def assemble_and_mux(ep, video, data, cache, synth_dir):
    # 配音轨(48k stereo)
    rate, ch = 48000, 2
    total = dz.audio_dur(video)
    buf = np.zeros((int(total*rate)+rate*2, ch), dtype=np.float32)
    for i, seg in enumerate(data["segments"]):
        f = os.path.join(synth_dir, f"u{i:04d}.wav")
        if not os.path.exists(f): continue
        raw = dz.to_pcm(f, rate, ch)
        if not raw: continue
        s = np.frombuffer(raw, dtype=np.int16).astype(np.float32)/32768.0
        s = s.reshape(-1, ch)
        slot = (data["segments"][i+1]["s"] if i+1 < len(data["segments"]) else seg["e"]) - seg["s"]
        dur = len(s)/rate
        if slot > 0.4 and dur > slot*1.12:
            factor = min(1.3, dur/(slot*0.98))
            n_out = int(len(s)/factor)
            ii = (np.arange(n_out)*factor).astype(np.int64)
            s = s[np.clip(ii, 0, len(s)-1)]
        off = int(seg["s"]*rate); end = min(off+len(s), len(buf))
        if off < len(buf): buf[off:end] += s[:end-off]
    log(f"{ep} 配音轨组装完成, 用纯伴奏(no_vocals)混音(日语人声零泄漏)...")
    # 背景 = Demucs 拆出的伴奏/音效轨(无人声) — 彻底替代旧方案(日语原声压30%会在中文空隙漏出)
    instr = os.path.join(DIR, "dub_cache", f"demucs_{ep}", "htdemucs",
                         os.path.splitext(os.path.basename(video))[0], "no_vocals.mp3")
    if os.path.exists(instr):
        bg = dz.to_pcm(instr, rate, ch)
        bgf = np.frombuffer(bg, dtype=np.int16).astype(np.float32) / 32768.0
        bgf = bgf.reshape(-1, ch)
        n = min(len(bgf), len(buf))
        mixed = np.zeros_like(buf)
        mixed[:n] = bgf[:n] * 0.72 + buf[:n] * 1.15
        np.clip(mixed, -1.0, 1.0, out=mixed)
        mixed16 = (mixed * 32767).astype(np.int16)
    else:
        # 回退: 日语原声压低方案
        log(f"{ep} ⚠ 未找到 no_vocals, 回退日语压低方案")
        jpn_wav = os.path.join(cache, "_jpn48k.wav")
        if not os.path.exists(jpn_wav):
            run(["ffmpeg", "-y", "-v", "error", "-i", video,
                 "-map", "0:a:m:language:jpn", "-ac", "2", "-ar", str(rate),
                 "-c:a", "pcm_s16le", jpn_wav], check=True)
        orig = dz.to_pcm(jpn_wav, rate, ch)
        mixed16 = dz.duck_and_mix(orig, data["segments"], buf, rate, ch).astype(np.int16)
    import wave as _w
    mixwav = os.path.join(cache, "_clone_mix.wav")
    pcm16 = mixed16
    with _w.open(mixwav, "wb") as wf:
        wf.setnchannels(ch); wf.setsampwidth(2); wf.setframerate(rate)
        wf.writeframes(pcm16.tobytes())
    out_tmp = os.path.splitext(video)[0] + ".cloning.mkv"
    log(f"{ep} 封装(克隆轨置顶default, 丢弃piper旧轨, 日语原声第2轨)...")
    r = run(["ffmpeg", "-y", "-v", "error", "-i", video, "-i", mixwav,
             "-map", "0:v", "-map", "1:a", "-map", "0:a:m:language:jpn", "-map", "0:s?",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-c:s", "copy",
             "-metadata:s:a:0", "language=zho", "-metadata:s:a:0", "title=中文配音(角色克隆)",
             "-metadata:s:a:1", "language=jpn", "-metadata:s:a:1", "title=日本語",
             "-disposition:a:0", "default", "-disposition:a:1", "0",
             out_tmp], timeout=1200)
    if r.returncode != 0 or not os.path.exists(out_tmp):
        raise RuntimeError(f"封装失败: {r.stderr[-300:]}")
    for a in range(6):
        try:
            os.replace(out_tmp, video)
            break
        except PermissionError:
            time.sleep(6)
    else:
        raise RuntimeError("目标被占用, 产物保留 .cloning.mkv")
    # 台账
    lp = os.path.join(DIR, "dub.json")
    led = json.load(open(lp, encoding="utf-8")) if os.path.exists(lp) else {"done": {}}
    key = os.path.normcase(video)
    led["done"][key] = {"date": time.strftime("%Y-%m-%d %H:%M"),
                        "lines": len(data["segments"]), "version": "cosyvoice-clone",
                        "spk_dur": data.get("dur", {})}
    json.dump(led, open(lp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log(f"{ep} ✅ 克隆版完成 ({len(data['segments'])}句, 角色={data.get('dur')})")

# ---------------- 多音色后端 (Kokoro, 方案A) ----------------
MALE_VOICES = ["zm_yunxi", "zm_yunjian", "zm_yunxia", "zm_yunyang"]
FEMALE_VOICES = ["zf_xiaoxiao", "zf_xiaobei", "zf_xiaoyi", "zf_xiaoni"]


def _load16k(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le",
                        "-ac", "1", "-ar", "16000", "-"], capture_output=True)
    return np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32768.0


def speaker_genders(data, cache, vocals):
    """每个角色的性别判定: 参考段人声 F0 中位数 (男<185Hz)"""
    import librosa
    from collections import defaultdict
    dur = defaultdict(float)
    for s in data["segments"]:
        dur[str(s["spk"])] += s["e"] - s["s"]
    genders = {}
    for spk in sorted(dur, key=lambda k: -dur[k]):
        f0s = []
        for n, r in enumerate(data["refs"].get(spk, [])[:2]):
            clip = os.path.join(cache, f"fg_spk{spk}_{n}.wav")
            if not os.path.exists(clip):
                run(["ffmpeg", "-y", "-v", "error", "-ss", str(r["s"]),
                     "-to", str(r["e"]), "-i", vocals, "-ac", "1",
                     "-ar", "16000", clip], check=False)
            if not os.path.exists(clip):
                continue
            y = _load16k(clip)
            if len(y) < int(0.5 * 16000):
                continue
            f0 = librosa.yin(y, fmin=60, fmax=400, sr=16000)
            v = f0[(f0 > 65) & (f0 < 395)]
            if len(v) > 20:
                f0s.append(float(np.median(v)))
        med = float(np.median(f0s)) if f0s else 0.0
        genders[spk] = ("male" if 0 < med < 185 else "female" if med else "unknown")
        genders[f"_f0_{spk}"] = round(med, 1)
    return genders


def kokoro_synth(ep, video, data, cache, vocals):
    """Kokoro 多音色中文合成 + 内容审听闸门(不过闸不封装)"""
    from kokoro import KPipeline
    import random as _rnd
    dur = {}
    for s in data["segments"]:
        dur[str(s["spk"])] = dur.get(str(s["spk"]), 0) + s["e"] - s["s"]
    genders = speaker_genders(data, cache, vocals)
    rank = sorted(dur, key=lambda k: -dur[k])
    assign, mi, fi = {}, 0, 0
    for spk in rank:
        g = genders.get(spk, "unknown")
        if g == "male":
            assign[spk] = MALE_VOICES[mi % len(MALE_VOICES)]; mi += 1
        elif g == "female":
            assign[spk] = FEMALE_VOICES[fi % len(FEMALE_VOICES)]; fi += 1
        else:
            assign[spk] = (MALE_VOICES[0] if int(spk) == 0 else FEMALE_VOICES[0])
    log(f"{ep} 性别/音色分配: " +
        ", ".join(f"spk{s}({genders.get(s)}F0={genders.get('_f0_'+str(s),'?')}Hz)->{assign[s]}" for s in rank))

    pipe = KPipeline(lang_code="z")
    outdir = os.path.join(cache, "multi_synth")
    os.makedirs(outdir, exist_ok=True)
    t0 = time.time()
    ok = 0
    for i, seg in enumerate(data["segments"]):
        out = os.path.join(outdir, f"u{i:04d}.wav")
        if os.path.exists(out) and os.path.getsize(out) > 400:
            ok += 1; continue
        voice = assign[str(seg["spk"])]
        try:
            waves = [np.asarray(r_.audio) for r_ in
                     pipe(seg["text"], voice=voice,
                          speed=min(1.4, speed_of(seg["text"]) * 1.05))]
            if not waves:
                raise RuntimeError("empty synth")
            a = np.concatenate(waves).astype(np.float32)
            import wave as _w
            pcm = (np.clip(a, -1, 1) * 32767).astype(np.int16)
            with _w.open(out, "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
                w.writeframes(pcm.tobytes())
            ok += 1
        except Exception as e:
            log(f"{ep} 句{i}失败: {str(e)[:80]}")
        if (i + 1) % 100 == 0:
            log(f"{ep} 多音色合成 {i+1}/{len(data['segments'])} ({time.time()-t0:.0f}s)")
    log(f"{ep} 合成完成 {ok}/{len(data['segments'])} 用时 {time.time()-t0:.0f}s")
    audit_gate(ep, data, outdir)
    json.dump({"assign": assign,
               "genders": {k: v for k, v in genders.items() if not k.startswith("_f0_")}},
              open(os.path.join(cache, "_voice_assign.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    return outdir


def audit_gate(ep, data, outdir, n=10):
    """内容审听闸门: 抽 n 句 -> whisper -> 繁转简 -> 对照字幕; 通过率<50%拒绝封装"""
    from faster_whisper import WhisperModel
    import random as _rnd
    try:
        from opencc import OpenCC
        cc = OpenCC("t2s")
    except Exception:
        cc = None
    idxs = list(range(len(data["segments"])))
    sample = _rnd.sample(idxs, min(n, len(idxs)))
    m = WhisperModel("small", device="cpu", compute_type="int8")
    hits, details = 0, []
    for i in sorted(sample):
        p = os.path.join(outdir, f"u{i:04d}.wav")
        if not os.path.exists(p):
            details.append(f"u{i:04d}=缺"); continue
        raw = _load16k(p)
        if len(raw) < 1600:
            details.append(f"u{i:04d}=过短"); continue
        segs, _ = m.transcribe(raw, language="zh", vad_filter=True,
                               condition_on_previous_text=False)
        got = "".join(s.text for s in segs)
        if cc:
            got = cc.convert(got)
        exp = re.sub(r"[，。？！,\s-]", "", data["segments"][i]["text"])[:5]
        h = bool(exp) and exp in got.replace(" ", "")
        hits += h
        details.append(f"u{i:04d}={'✓' if h else '✗'}")
    rate = hits / max(1, len(sample))
    log(f"{ep} 审听闸门: {hits}/{len(sample)} ({rate:.0%}) | " + " ".join(details))
    if rate < 0.5:
        raise RuntimeError(f"审听闸门未通过({rate:.0%}), 拒绝封装")


def bank_synth(ep, video, data, cache, vocals, genders_override=None):
    """真人参考库 + CosyVoice2 中文零样本 (内容逐字级, 已验证)"""
    BANK = os.path.join(DIR, "voice_bank")
    man = json.load(open(os.path.join(BANK, "manifest.json"), encoding="utf-8"))
    dur = {}
    for s in data["segments"]:
        dur[str(s["spk"])] = dur.get(str(s["spk"]), 0) + s["e"] - s["s"]
    genders = robust_genders(data, cache, vocals)
    if genders_override:
        for k, v in genders_override.items():
            genders[k] = v
            log(f"{ep} 人工覆盖 spk{k}->{v}")
    rank = sorted(dur, key=lambda k: -dur[k])
    mpool = [k for k, v in man.items() if v["gender"] == "male"]
    fpool = [k for k, v in man.items() if v["gender"] == "female"]
    assign, mi, fi = {}, 0, 0
    for spk in rank:
        g = genders.get(spk, "unknown")
        if g == "male" and mi < len(mpool):
            assign[spk] = mpool[mi]; mi += 1
        elif g == "female" and fi < len(fpool):
            assign[spk] = fpool[fi]; fi += 1
        else:
            pool = mpool if int(spk) == 0 else fpool
            idx = mi if pool is mpool else fi
            assign[spk] = pool[idx % len(pool)]
            if pool is mpool: mi += 1
            else: fi += 1
    log(f"{ep} 角色->真人声库: " +
        ", ".join(f"spk{s}({genders.get(s)})->{assign[s]}" for s in rank))

    from cosyvoice.cli.cosyvoice import CosyVoice2
    c2 = CosyVoice2(MDL, fp16=True)
    outdir = os.path.join(cache, "bank_synth")
    os.makedirs(outdir, exist_ok=True)
    t0 = time.time()
    ok = 0
    for i, seg in enumerate(data["segments"]):
        out = os.path.join(outdir, f"u{i:04d}.wav")
        if os.path.exists(out) and os.path.getsize(out) > 400:
            ok += 1; continue
        b = man[assign[str(seg["spk"])]]
        try:
            segs = list(c2.inference_zero_shot(seg["text"], b["text"], b["ref"],
                                               stream=False,
                                               speed=min(1.4, speed_of(seg["text"]) * 1.05)))
            a = np.squeeze(np.concatenate([np.asarray(o["tts_speech"]) for o in segs], axis=0)).astype(np.float32)
            import wave as _w
            pcm = (np.clip(a, -1, 1) * 32767).astype(np.int16)
            with _w.open(out, "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050)
                w.writeframes(pcm.tobytes())
            ok += 1
        except Exception as e:
            log(f"{ep} 句{i}失败: {str(e)[:70]}")
        if (i + 1) % 50 == 0:
            avg = (time.time() - t0) / max(1, ok)
            log(f"{ep} 真人库合成 {i+1}/{len(data['segments'])} ({time.time()-t0:.0f}s, {avg:.1f}s/句)")
    log(f"{ep} 合成完成 {ok}/{len(data['segments'])} 用时 {time.time()-t0:.0f}s")
    audit_gate(ep, data, outdir)
    json.dump({"assign": assign, "genders": {k: v for k, v in genders.items()
               if not str(k).startswith("_f0")}},
              open(os.path.join(cache, "_voice_assign.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    return outdir


def robust_genders(data, cache, vocals, n_clips=8):
    """性别投票: 每角色随机抽 n_clips 段人声, 逐段 F0 中位数投票(男<180Hz), 抗倍频误判"""
    import librosa
    import random as _rnd
    from collections import defaultdict
    byspk = defaultdict(list)
    for s in data["segments"]:
        byspk[str(s["spk"])].append(s)
    genders = {}
    for spk, segs in byspk.items():
        # 随机抽样(勿用最长段: 多为多人对话, 女声污染重)
        segs_sorted = sorted(segs, key=lambda s: s["e"] - s["s"], reverse=True)
        mid = [s for s in segs_sorted if 2.0 <= (s["e"] - s["s"]) <= 8.0]
        sample = (mid if len(mid) >= n_clips else segs_sorted)[:n_clips]
        _rnd.shuffle(sample)
        sample = sample[:n_clips]
        votes = []
        for n, s in enumerate(sample):
            clip = os.path.join(cache, f"gv_spk{spk}_{n}.wav")
            if not os.path.exists(clip):
                run(["ffmpeg", "-y", "-v", "error", "-ss", str(s["s"]),
                     "-to", str(s["e"]), "-i", vocals, "-ac", "1",
                     "-ar", "16000", clip], check=False)
            if not os.path.exists(clip):
                continue
            y = _load16k(clip)
            if len(y) < int(0.5 * 16000):
                continue
            f0 = librosa.yin(y, fmin=60, fmax=400, sr=16000)
            v = f0[(f0 > 65) & (f0 < 395)]
            if len(v) > 20:
                votes.append(float(np.median(v)))
        male_frac = sum(1 for v in votes if v < 180) / max(1, len(votes))
        genders[spk] = "male" if male_frac >= 0.5 else "female"
        genders[f"_f0_{spk}"] = round(float(np.median(votes)), 1) if votes else 0
    return genders


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ep", required=True, choices=list(EP_MAP))
    ap.add_argument("--mode", default="bank", choices=["bank", "multi", "clone"],
                    help="bank=真人参考库+CosyVoice(默认,已验证逐字级); multi=Kokoro多音色; clone=已判废")
    ap.add_argument("--genders", default="", help="性别人工覆盖, 如 0=male,2=female")
    args = ap.parse_args()
    lock = acquire_lock()
    if lock:
        log(f"GPU锁被占({lock}), 退出"); return 1
    own = os.path.join(DIR, f"subtitle.{os.getpid()}.lock")
    import atexit
    atexit.register(lambda: os.path.exists(own) and os.remove(own))
    try:
        video, jpn_srt = episode_files(args.ep)
        vocals = vocals_of(args.ep, video)
        data, cache, vocals = cluster_of(args.ep, video, vocals, jpn_srt)
        gover = {}
        if args.genders:
            for kv in args.genders.split(","):
                k, v = kv.split("=")
                gover[k.strip()] = v.strip()
        if args.mode == "bank":
            synth_dir = bank_synth(args.ep, video, data, cache, vocals, gover)
        elif args.mode == "multi":
            synth_dir = kokoro_synth(args.ep, video, data, cache, vocals)
        else:
            synth_dir = clone_synth(args.ep, video, data, cache, vocals, jpn_srt)
        assemble_and_mux(args.ep, video, data, cache, synth_dir)
        return 0
    finally:
        if os.path.exists(own):
            try: os.remove(own)
            except Exception: pass

if __name__ == "__main__":
    sys.exit(main())
