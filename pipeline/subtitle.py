# -*- coding: utf-8 -*-
"""为视频按音轨生成 SRT 字幕（本地 faster-whisper，GTX1650 GPU，免费）。

用法:
  python subtitle.py                  # 处理每日电影(已完成且无字幕) + D:\\download 缺字幕视频
  python subtitle.py --scan DIR       # 只扫指定目录
  python subtitle.py --file VIDEO     # 单文件
  python subtitle.py --max-secs 150 --file VIDEO   # 冒烟测试(只转前 N 秒)
  python subtitle.py --force          # 已有记录也重做
  python subtitle.py --limit N        # 本次最多处理 N 个

产物: 与视频同目录、同名 .srt（播放器自动加载）；台账 subtitles.json；日志 subtitle.log
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

DIR = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(DIR, "subtitle.log")
LEDGER = os.path.join(DIR, "subtitles.json")
SCAN_ROOT = r"E:\movies"  # 管线专属目录(严禁指向用户个人目录: E:\download是用户考公课程盘!)
LEGACY_SCAN_ROOT = r"D:\download"  # 过渡期仍扫D盘存量
MODEL_SIZE = os.environ.get("WHISPER_MODEL", "small")   # small 已在本机 HF 缓存
ZH_PROMPT = "以下是简体中文字幕。"
VIDEO_EXTS = {".mkv", ".mp4", ".avi", ".ts", ".rmvb", ".flv", ".mov", ".wmv", ".webm"}
# 派生文件（拼接/压制产物）不重复转写，字幕直接从源文件复制
DERIVED_MARKERS = (".ext.mp4", ".testext.mp4", ".subbed.mp4", ".bilingual.mp4", ".burning.mp4")


def ensure_cuda_dlls():
    """ctranslate2(faster-whisper) 需要系统级 cublas64_12.dll；
    本机无 CUDA Toolkit，但 torch 自带全部 CUDA DLL -> 注入 PATH（实证有效）。"""
    import site
    dirs = []
    try:
        import torch
        dirs.append(os.path.join(os.path.dirname(torch.__file__), "lib"))
    except Exception:
        pass
    for sp in site.getsitepackages() + [site.getusersitepackages()]:
        for pkg in ("cublas", "cudnn", "curand", "cufft", "cusparse",
                    "cusolver", "cuda_nvrtc", "cuda_cupti"):
            d = os.path.join(sp, "nvidia", pkg, "bin")
            if os.path.isdir(d):
                dirs.append(d)
    cuda_path = os.environ.get("CUDA_PATH", "")
    if cuda_path:
        for sub in ("bin", "lib\\x64"):
            d = os.path.join(cuda_path, sub)
            if os.path.isdir(d):
                dirs.append(d)
    dirs = [d for d in dict.fromkeys(dirs) if os.path.isdir(d)]
    if dirs:
        os.environ["PATH"] = os.pathsep.join(dirs + [os.environ.get("PATH", "")])
    return dirs


def qbt_incomplete_paths():
    """qBittorrent 中未下完的任务 content_path 集合（避免转写半截文件）"""
    env = {}
    p = os.path.join(DIR, "qbwebui.env")
    if os.path.exists(p):
        for ln in open(p, encoding="utf-8"):
            if "=" in ln and not ln.strip().startswith("#"):
                k, v = ln.strip().split("=", 1)
                env[k] = v
    base = env.get("QBT_URL", "http://127.0.0.1:8080")
    import urllib.request, urllib.parse
    try:
        req = urllib.request.Request(base + "/api/v2/auth/login",
              data=urllib.parse.urlencode({"username": env.get("QBT_USER", ""),
                                            "password": env.get("QBT_PASS", "")}).encode())
        with urllib.request.urlopen(req, timeout=8) as r:
            cookie = r.headers.get("Set-Cookie", "").split(";")[0]
        req2 = urllib.request.Request(base + "/api/v2/torrents/info")
        req2.add_header("Cookie", cookie)
        with urllib.request.urlopen(req2, timeout=8) as r:
            ts = json.loads(r.read().decode())
        return {t["content_path"] for t in ts
                if t.get("progress", 1) < 1 and t.get("content_path")}
    except Exception as e:
        log(f"  qBittorrent 查询失败(跳过检查): {e}")
        return set()



def _pid_alive(pid):
    """Windows 安全探活（严禁 os.kill(pid,0)，Windows 上会直接杀进程）"""
    import ctypes
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    h = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if h:
        ctypes.windll.kernel32.CloseHandle(h)
        return True
    return False


def _stale_locks(pattern_dir, prefix="subtitle."):
    """返回 (存活锁路径 or None, 需清理的过期/孤儿锁列表)"""
    import glob, time as _t
    for f in glob.glob(os.path.join(pattern_dir, prefix + "*.lock")):
        try:
            m = re.search(r"(\d+)\.lock$", f)
            pid = int(m.group(1)) if m else -1
            age = _t.time() - os.path.getmtime(f)
            if pid > 0 and not _pid_alive(pid):
                os.remove(f)          # 孤儿锁（进程已死）
            elif age < 6 * 3600:
                return f, []           # 活锁
            else:
                os.remove(f)           # 超龄锁
        except Exception:
            pass
    return None, []


def _locked():
    """跨进程锁：防 cron 重入双开 GPU；自动识别死进程孤儿锁"""
    active, _ = _stale_locks(DIR)
    if active:
        return active
    lock = os.path.join(DIR, f"subtitle.{os.getpid()}.lock")
    open(lock, "w").write(str(os.getpid()))
    return None


def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_ledger():
    if os.path.exists(LEDGER):
        return json.load(open(LEDGER, encoding="utf-8"))
    return {"done": {}}


def save_ledger(l):
    json.dump(l, open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def srt_path(video):
    base, _ = os.path.splitext(video)
    return base + ".srt"


def probe(video):
    """返回 {duration, text_subs, audio_langs, has_chinese_embedded}"""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-of", "json", video],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    info = {"duration": None, "text_subs": [], "audio_langs": [], "has_chinese_embedded": False, "subs_detail": []}
    try:
        data = json.loads(out.stdout)
    except Exception:
        return info
    CJK_LANGS = ("chi", "zho", "chinese", "zh", "chs", "cht", "hans", "cht")
    for s_ in data.get("streams", []):
        ct = s_.get("codec_type")
        tags = s_.get("tags", {}) or {}
        lang = (tags.get("language") or "").lower()
        title = (tags.get("title") or "")
        if ct == "subtitle" and s_.get("codec_name") in ("subrip", "srt", "ass", "ssa", "mov_text", "webvtt", "text"):
            info["text_subs"].append(s_.get("codec_name"))
            info["subs_detail"].append({"codec": s_.get("codec_name"), "lang": lang, "title": title})
            if lang in CJK_LANGS or any(k in title for k in ("中文", "简体", "繁体", "Simplified", "Chinese")):
                info["has_chinese_embedded"] = True
        elif ct == "audio":
            info["audio_langs"].append(lang or "?")
    out2 = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        info["duration"] = float(out2.stdout.strip())
    except Exception:
        pass
    return info
    for s in data.get("streams", []):
        if s.get("codec_type") == "subtitle" and s.get("codec_name") in (
                "subrip", "srt", "ass", "ssa", "mov_text", "webvtt", "text"):
            info["text_subs"].append(s.get("codec_name"))
        elif s.get("codec_type") == "audio":
            info["audio_langs"].append((s.get("tags") or {}).get("language", "?"))
    # duration
    out2 = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", video],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        info["duration"] = float(out2.stdout.strip())
    except Exception:
        pass
    return info


def extract_wav(video, tmpdir, max_secs=None):
    wav = os.path.join(tmpdir, "audio.wav")
    # 多音轨优先中文轨(国产双语版英文常排首, 用其转写会产生转译失真)
    map_sel = []
    try:
        p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a",
                            "-show_entries", "stream_tags=language", "-of", "json", video],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        auds = json.loads(p.stdout).get("streams", [])
        pick = None
        for i, a in enumerate(auds):
            lang = ((a.get("tags") or {}).get("language") or "").lower()
            if lang in ("chi", "zho", "chinese", "zh", "chs", "cht"):
                pick = i
                break
        if pick:
            map_sel = ["-map", f"0:a:{pick}"]
            log(f"  多音轨: 选择中文音轨 #{pick}")
    except Exception:
        pass
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", video] + map_sel
    if max_secs:
        cmd += ["-t", str(max_secs)]
    cmd += ["-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", wav]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg 抽音频失败: {r.stderr[:300]}")
    return wav


def ts(sec):
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def transcribe(wav, srt_out, max_secs=None):
    dll_dirs = ensure_cuda_dlls()
    log(f"  CUDA DLL 路径注入 {len(dll_dirs)} 个")
    from faster_whisper import WhisperModel
    t0 = time.time()
    # GPU int8_float16：4GB 显存下 small 无压力
    model = WhisperModel(MODEL_SIZE, device="cuda", compute_type="int8_float16")

    # 第一遍：前 30 秒探语言（固定语言可显著减少整片漂移）
    _, info = model.transcribe(wav, beam_size=1, vad_filter=True)
    lang = info.language
    log(f"  语言检测: {lang} (置信 {info.language_probability:.2f})")

    kwargs = dict(
        language=lang, beam_size=5, vad_filter=True,
        condition_on_previous_text=False,   # 防重复幻觉(实证79→2)
        temperature=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
    )
    if lang and lang.startswith("zh"):
        kwargs["initial_prompt"] = ZH_PROMPT   # 简体偏置
    if max_secs:
        # 第二遍只重转前 N 秒（冒烟测试）：用截断的 wav 再抽一遍太贵，直接限制无 API，跳过
        pass

    segments, info2 = model.transcribe(wav, **kwargs)
    n = 0
    with open(srt_out, "w", encoding="utf-8") as f:
        for seg in segments:
            if max_secs and seg.start > max_secs:
                break
            n += 1
            f.write(f"{n}\n{ts(seg.start)} --> {ts(seg.end)}\n{seg.text.strip()}\n\n")
    rt = (time.time() - t0)
    log(f"  段数 {n}，耗时 {rt:.0f}s，语言 {lang}")
    return lang, n, rt


def process(video, ledger, force=False, max_secs=0):
    video = os.path.abspath(video)
    key = video.lower()
    srt = srt_path(video)
    if not force and key in ledger["done"]:
        return f"已处理过(台账)"
    if not force and os.path.exists(srt) and os.path.getsize(srt) > 200:
        return f"已有字幕 {os.path.basename(srt)}"
    info = probe(video)
    if info["text_subs"] and info.get("has_chinese_embedded"):
        ext_srt = os.path.splitext(video)[0] + ".extracted.srt"
        if os.path.exists(ext_srt):
            return f"已提取内嵌中文字幕 -> {os.path.basename(ext_srt)[:50]} (跳过)"
        # 找中文字幕轨的序号 (subtitle 流内序号)
        cjk_idx = -1
        sub_ord = 0
        for d_ in info.get("subs_detail", []):
            if cjk_idx < 0 and (d_["lang"] in ("chi","zho","chinese","zh","chs","cht","hans")
                                or any(k in d_["title"] for k in ("中文","简体","繁体","Simplified","Chinese"))):
                cjk_idx = sub_ord
            sub_ord += 1
        if cjk_idx < 0:
            cjk_idx = 0
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", video, "-map", f"0:s:{cjk_idx}", str(ext_srt)], capture_output=True)
        if r.returncode != 0 or not os.path.exists(ext_srt):
            return f"内嵌中文字幕提取失败: {r.stderr.decode('utf-8','replace')[:80]}"
        # 转 UTF-8 + 粗查乱码
        raw = open(ext_srt, "rb").read()
        txt = raw.decode("utf-8", errors="replace")
        lines = [l.strip() for l in txt.splitlines() if l.strip() and not l.strip().isdigit() and "-->" not in l]
        sample = "".join(lines[:10])
        cjk = sum(1 for c in sample if "一" <= c <= "鿿")
        if len(sample) > 10 and cjk / max(1, len(sample)) < 0.25:
            os.remove(ext_srt)
            info["text_subs"] = []
            info["has_chinese_embedded"] = False
            log("  内嵌中文字幕完整性闸门拒绝(非中文) -> 转入转写流程")
        else:
            open(ext_srt, "w", encoding="utf-8").write(txt)
            led = load_ledger()
            key = video.lower()
            led["done"][key] = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "srt": ext_srt, "lang": "zh-embedded", "segments": -len(lines),
                "source": "embedded-extract"}
            save_ledger(led)
            return f"内嵌中文字幕已提取软字幕 ({cjk_idx}) -> 已登记"
    if info["text_subs"]:
        log(f"  内嵌字幕非中文({','.join(info['text_subs'])}) -> 忽略, 继续转写")
    dur = info["duration"] or 0
    log(f"处理: {os.path.basename(video)} | {dur/60:.0f} 分钟 | 音轨语言: {info['audio_langs']}")
    tmpdir = tempfile.mkdtemp(prefix="subs_")
    try:
        wav = extract_wav(video, tmpdir, max_secs=max_secs or None)
        lang, n, rt = transcribe(wav, srt, max_secs=max_secs or None)
        if n == 0:
            os.remove(srt) if os.path.exists(srt) else None
            raise RuntimeError("转写结果为空(可能整段无对白)")
        ledger["done"][key] = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "srt": srt, "lang": lang, "segments": n,
            "duration_min": round(dur / 60, 1), "cost_sec": round(rt)}
        save_ledger(ledger)
        # 非中文音轨 → 免费在线翻成简体中文（失败保留原语言，不阻断）
        if lang and not lang.startswith("zh") and not max_secs:
            try:
                import translate_srt as tr
                tmsg = tr.translate_file(srt, lang)
                log(f"  翻译: {tmsg}")
            except Exception as e:
                log(f"  ⚠ 翻译失败(保留原语言字幕): {e}")
        return f"OK lang={lang} 段数={n} 耗时={rt:.0f}s -> {os.path.basename(srt)}"
    finally:
        for fn in os.listdir(tmpdir):
            try:
                os.remove(os.path.join(tmpdir, fn))
            except Exception:
                pass
        try:
            os.rmdir(tmpdir)
        except Exception:
            pass


DENY_ROOTS = (r"e:\download", r"c:\users\16575\desktop", r"c:\users\16575\documents")


def _denied(path):
    p = os.path.abspath(path).lower()
    return any(p.startswith(d) for d in DENY_ROOTS)


def collect_videos(scan_root, skip_dirs=()):
    if _denied(scan_root):
        raise RuntimeError(f"拒绝扫描用户个人目录: {scan_root} (DENY_ROOTS 防护)")
    vids = []
    for root, dirs, files in os.walk(scan_root):
        if _denied(root):
            dirs.clear()
            continue
        if any(os.path.abspath(root).startswith(os.path.abspath(d)) for d in skip_dirs):
            dirs.clear()
            continue
        for fn in files:
            if os.path.splitext(fn)[1].lower() not in VIDEO_EXTS:
                continue
            if any(fn.lower().endswith(m) for m in DERIVED_MARKERS):
                continue
            if any(k in fn.lower() for k in (".sample.", "sample_", "-sample", ".trailer", "preview")):
                continue  # 拼接/压制产物：字幕复制源文件的即可
            p = os.path.join(root, fn)
            pa = os.path.abspath(p)
            # 未下完排除: 目录型种子(前缀匹配) + 单文件型种子(精确匹配)
            if any(pa == os.path.abspath(d) or pa.startswith(os.path.abspath(d) + os.sep)
                   or pa.startswith(os.path.abspath(d)) and not os.path.splitext(d)[1]
                   for d in skip_dirs):
                continue
            # 正在写入的文件（5分钟内变更）也跳过
            try:
                if time.time() - os.path.getmtime(p) < 300:
                    continue
            except Exception:
                pass
            vids.append(p)
    # 最新优先（当天下载的电影最先做）
    vids.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return vids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file")
    ap.add_argument("--scan", default=SCAN_ROOT)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--max-secs", type=int, default=0, help="冒烟测试：只转前 N 秒")
    args = ap.parse_args()

    ledger = load_ledger()
    if args.file:
        targets = [args.file]
    else:
        lock = _locked()
        if lock:
            log(f"已有实例运行中({lock})，退出")
            return
        inc = qbt_incomplete_paths()
        if inc:
            log(f"跳过未下完的任务 {len(inc)} 个: {[os.path.basename(x)[:40] for x in inc]}")
        targets = []
        for _root in dict.fromkeys((args.scan, LEGACY_SCAN_ROOT)):
            targets += collect_videos(_root, skip_dirs=inc)
    if args.limit:
        targets = targets[:args.limit]

    log(f"待检查 {len(targets)} 个视频 (model={MODEL_SIZE})")
    results = []
    for i, v in enumerate(targets, 1):
        if os.path.getsize(v) < 1024 * 1024:
            continue
        try:
            msg = process(v, ledger, force=args.force, max_secs=args.max_secs)
        except Exception as e:
            msg = f"❌ {e}"
            log(f"  失败: {e}")
        results.append((os.path.basename(v), msg))
        log(f"  [{i}/{len(targets)}] {msg}")
        if args.max_secs:
            break
    log("==== 完成 ====")
    for name, msg in results:
        print(f"  {name[:60]}: {msg}")
    own_lock = os.path.join(DIR, f"subtitle.{os.getpid()}.lock")
    if os.path.exists(own_lock):
        try:
            os.remove(own_lock)
        except Exception:
            pass


if __name__ == "__main__":
    main()
