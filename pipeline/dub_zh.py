# -*- coding: utf-8 -*-
"""灾(E02起) 中文配音合成：
中文字幕(官方简体) -> edge-tts 神经语音逐句合成 -> 时间轴对齐 ->
原声智能压低(对白段 duck 到 30%，BGM/音效保留) -> 混音 ->
封装为 mkv 默认音轨(原日语音轨保留为第二轨)。

用法:
  python dub_zh.py --file "E02....mkv"          # 单集
  python dub_zh.py --all                        # E02-E06 全部
  python dub_zh.py --file X.mkv --dry-run       # 只生成配音 wav 不封装
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

DIR = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(DIR, "dub.log")
LEDGER = os.path.join(DIR, "dub.json")
FOLDER = (r"D:\download\【高清剧集网发布 www.DDHDTV.com】灾[全6集][中文字幕]."
          r"Sai.S01.1080p.NF.WEB-DL.AAC.2.0.H.264-BlackTV")

VOICE_M = "zh-CN-YunxiNeural"      # 男（年轻）
VOICE_F = "zh-CN-XiaoxiaoNeural"   # 女
DUCK_GAIN = 0.30                   # 对白期间原声增益
RAMP = 0.08                        # 压低/恢复渐变(秒)
SKIP_RE = re.compile(r"^\s*[（(].*?[）)]\s*$")   # 纯音效描述不读


def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_ledger():
    if os.path.exists(LEDGER):
        return json.load(open(LEDGER, encoding="utf-8"))
    return {"done": {}}


def save_ledger(d):
    json.dump(d, open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def parse_srt(path):
    raw = open(path, encoding="utf-8-sig", errors="replace").read()
    blocks = []
    for part in re.split(r"\n\s*\n", raw.strip()):
        m = re.search(r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})", part)
        if not m:
            continue
        g = m.groups()
        s = int(g[0]) * 3600 + int(g[1]) * 60 + int(g[2]) + int(g[3]) / 1000
        e = int(g[4]) * 3600 + int(g[5]) * 60 + int(g[6]) + int(g[7]) / 1000
        body = part[m.end():].strip()
        lines = [l.strip() for l in body.splitlines() if l.strip()]
        text = " ".join(lines)
        if SKIP_RE.match(text):
            continue
        # 行首说话人短横 -> 逗号分隔的自然朗读文本
        if any(l.startswith("-") for l in lines):
            clean = "，".join(re.sub(r"^\s*-\s*", "", l) for l in lines)
        else:
            clean = " ".join(lines)
        clean = clean.strip()
        if not clean:
            continue
        blocks.append({"s": s, "e": e, "text": clean,
                       "new_speaker": bool(re.match(r"^-", lines[0]))})
    return blocks


_PIPER = None
PIPER_MODEL = os.path.join(DIR, "piper_voices", "zh_CN-huayan-medium.onnx")


def get_piper():
    global _PIPER
    if _PIPER is None:
        from piper import PiperVoice
        _PIPER = PiperVoice.load(PIPER_MODEL)
    return _PIPER


def tts_one(idx, text, voice, outdir):
    """本地 Piper 合成（离线、无速率限制）；outdir=持久缓存，断点续跑"""
    import wave as _wave
    out = os.path.join(outdir, f"u{idx:04d}.wav")
    if os.path.exists(out) and os.path.getsize(out) > 400:
        return out
    v = get_piper()
    with _wave.open(out, "wb") as w:
        wrote = False
        for chunk in v.synthesize(text):
            if not wrote:
                w.setnchannels(chunk.sample_channels)
                w.setsampwidth(chunk.sample_width)
                w.setframerate(chunk.sample_rate)
                wrote = True
            w.writeframes(chunk.audio_int16_bytes)
    if not wrote or os.path.getsize(out) < 400:
        raise RuntimeError(f"TTS空输出[{idx}]: {text[:30]}")
    return out


def tts_all(blocks, outdir, workers=0):
    """串行本地合成（ONNX 会话非线程安全）；返回每块音频路径"""
    voice = VOICE_F
    paths = []
    t0 = time.time()
    for i, b in enumerate(blocks):
        b["voice"] = voice
        try:
            paths.append(tts_one(i, b["text"], voice, outdir))
        except Exception as e:
            log(f"  ⚠ 句{i}失败(跳过): {e}")
            paths.append(None)
        if (i + 1) % 100 == 0:
            log(f"  TTS {i+1}/{len(blocks)} ({time.time()-t0:.0f}s)")
    log(f"  TTS 完成 {sum(1 for p in paths if p)}/{len(blocks)} 用时 {time.time()-t0:.0f}s")
    return paths


def audio_dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def to_pcm(path, rate=48000, ch=2):
    """解码为 s16le bytes"""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le",
                        "-ar", str(rate), "-ac", str(ch), "-"],
                       capture_output=True)
    if r.returncode != 0:
        return b""
    return r.stdout


def build_dub_track(blocks, mp3s, total_sec, rate=48000, ch=2):
    import numpy as np
    buf = np.zeros((int(total_sec * rate) + rate * 2, ch), dtype=np.float32)
    for i, b in enumerate(blocks):
        if not mp3s[i]:
            continue
        raw = to_pcm(mp3s[i], rate, ch)
        if not raw:
            continue
        seg = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        seg = seg.reshape(-1, ch)
        slot = (blocks[i + 1]["s"] if i + 1 < len(blocks) else b["e"]) - b["s"]
        dur = len(seg) / rate
        # 超槽则轻微加速(<=1.3x)，过短留白即可
        if slot > 0.4 and dur > slot * 1.12:
            import math
            factor = min(1.3, dur / (slot * 0.98))
            n_out = int(len(seg) / factor)
            idx = (np.arange(n_out) * factor).astype(np.int64)
            seg = seg[np.clip(idx, 0, len(seg) - 1)]
            dur = n_out / rate
        off = int(b["s"] * rate)
        end = min(off + len(seg), len(buf))
        if off >= len(buf):
            continue
        buf[off:end] += seg[: end - off]
    return buf


def duck_and_mix(orig_pcm, blocks, dub, rate=48000, ch=2):
    import numpy as np
    orig = np.frombuffer(orig_pcm, dtype=np.int16).astype(np.float32) / 32768.0
    orig = orig.reshape(-1, ch)
    n = min(len(orig), len(dub))
    orig, dub = orig[:n], dub[:n]
    env = np.ones(n, dtype=np.float32)
    r = int(RAMP * rate)
    for b in blocks:
        s = max(0, int(b["s"] * rate))
        e = min(n, int((b["e"] + 0.15) * rate))
        if e <= s:
            continue
        env[s:e] = np.minimum(env[s:e], DUCK_GAIN)
        # 渐变
        a = min(r, (e - s) // 2)
        if a > 1:
            env[s:s + a] = np.linspace(1.0, env[s + a // 2], a, dtype=np.float32)
            env[e - a:e] = np.linspace(env[e - a - 1], 1.0, a, dtype=np.float32)
    mixed = orig * env[:, None] + dub[:n] * 1.15
    np.clip(mixed, -1.0, 1.0, out=mixed)
    return (mixed * 32767).astype(np.int16)


def run_one(video, dry=False):
    ledger = load_ledger()
    key = os.path.normcase(os.path.abspath(video))
    if key in ledger["done"]:
        return "已配音过"
    stem = os.path.splitext(video)[0]
    srt = stem + ".srt.hardsub"
    if not os.path.exists(srt):
        return "缺字幕(.srt.hardsub)，先烧录"
    blocks = parse_srt(srt)
    if len(blocks) < 50:
        return f"字幕块过少({len(blocks)})，拒绝"
    total = audio_dur(video)
    if total < 60:
        return "读不到视频时长"
    log(f"{os.path.basename(video)[:50]} | {len(blocks)}句 | {total/60:.0f}分钟 | 开始TTS")

    tmp = os.path.join(DIR, "dub_cache", os.path.splitext(os.path.basename(video))[0])
    os.makedirs(tmp, exist_ok=True)
    try:
        mp3s = tts_all(blocks, tmp)
        log("  TTS 完成，合成配音轨...")
        dub = build_dub_track(blocks, mp3s, total)
        log("  提取原声并压低对白混音...")
        orig = to_pcm(video)
        mixed = duck_and_mix(orig, blocks, dub)
        wav = os.path.join(tmp, "dub_mix.wav")
        raw = mixed.tobytes()
        p = subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le",
                            "-ar", "48000", "-ac", "2", "-i", "-", wav],
                           input=raw, capture_output=True)
        if p.returncode != 0:
            return f"混音写盘失败: {p.stderr[-200:]}"
        if dry:
            log(f"  dry-run 完成: {wav}")
            return "dry-ok"

        out_tmp = stem + ".dubbing.mkv"
        # 断点：上次封装产物还在(6小时内)则跳过重新封装
        fresh = (os.path.exists(out_tmp)
                 and time.time() - os.path.getmtime(out_tmp) < 6 * 3600
                 and os.path.getsize(out_tmp) > 50 * 1024 * 1024)
        if fresh:
            log("  发现已有封装产物，跳过重新封装直接替换")
        else:
            log("  封装(视频流复制，新配音轨置顶为默认，日语原声保留第二轨)...")
            cmd = ["ffmpeg", "-y", "-v", "error", "-i", video, "-i", wav,
                   "-map", "0:v", "-map", "1:a", "-map", "0:a", "-map", "0:s?",
                   "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                   "-c:s", "copy",
                   "-metadata:s:a:0", "language=zho", "-metadata:s:a:0", "title=中文配音",
                   "-metadata:s:a:1", "language=jpn", "-metadata:s:a:1", "title=日本語",
                   "-disposition:a:0", "default", "-disposition:a:1", "0",
                   out_tmp]
            p = subprocess.run(cmd, capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            if p.returncode != 0 or not os.path.exists(out_tmp):
                return f"封装失败: {p.stderr[-300:]}"
        # 替换（占用则重试）
        ok = False
        for a in range(5):
            try:
                os.replace(out_tmp, video)
                ok = True
                break
            except PermissionError:
                time.sleep(6)
        if not ok:
            return "目标被占用(播放器占用？)，封装产物已保留 .dubbing.mkv 下次秒替"
        ledger["done"][key] = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "lines": len(blocks), "voice_m": VOICE_M, "voice_f": VOICE_F,
            "duck": DUCK_GAIN, "min": round(total / 60, 1)}
        save_ledger(ledger)
        return f"OK {len(blocks)}句 配音已置顶(原声保留)"
    finally:
        pass  # dub_cache 持久保留：失败重跑断点续传


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file")
    ap.add_argument("--all", action="store_true", help="E02-E06")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.file:
        targets = [args.file]
    elif args.all:
        targets = [os.path.join(FOLDER, f) for f in sorted(os.listdir(FOLDER))
                   if f.startswith("Sai.S01E0") and f.endswith(".mkv")
                   and "E01" not in f]
    else:
        raise SystemExit("需要 --file 或 --all")
    for v in targets:
        if not os.path.exists(v):
            log(f"缺文件: {v}")
            continue
        try:
            msg = run_one(v, dry=args.dry_run)
        except Exception as e:
            msg = f"❌ {e}"
            import traceback
            traceback.print_exc()
        log(f"  {msg}")
    log("==== 配音任务结束 ====")


if __name__ == "__main__":
    main()
