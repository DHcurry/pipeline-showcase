# -*- coding: utf-8 -*-
"""为电影追加风景素材片段（默认60分钟）到片尾，Pexels 免费素材 + NVENC 硬编。

用法:
  python append_footage.py                  # 自动挑一部"已下完+已有中文字幕+未拼接"的每日电影
  python append_footage.py --movie "D:\\...\\电影.mkv"   # 指定文件
  python append_footage.py --test-minutes 3 --movie ...  # 测试模式(只拼3分钟)
  python append_footage.py --minutes 60 --in-place       # 拼完覆盖原文件(慎用)

产物: 默认 <原名>.ext.mp4（原片保留）；素材库 Desktop/video-assets/videos；台账 append.json
"""
import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

DIR = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(DIR, "append.log")
LEDGER = os.path.join(DIR, "append.json")
QBT_ENV = os.path.join(DIR, "qbwebui.env")
SUB_LEDGER = os.path.join(DIR, "subtitles.json")
LIB_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "video-assets", "videos")
LIB_MANIFEST = os.path.join(LIB_DIR, "manifest.json")
SKILL_DIR = os.path.expanduser(r"~\.pi\agent\skills\video-asset-hub")

TOPICS = ["aerial nature landscape", "ocean waves beach", "mountain snow",
          "forest trees", "sunset clouds sky", "river stream water",
          "waterfall", "lake reflection", "countryside field", "desert dunes",
          "drone aerial coast", "autumn forest", "green meadow", "canyon",
          "northern lights", "cherry blossom", "tropical beach", "fog mountains"]
VIDEO_EXTS = {".mkv", ".mp4", ".avi", ".ts", ".mov", ".wmv", ".flv"}
DERIVED_MARKERS = (".ext.mp4", ".testext.mp4", ".subbed.mp4", ".bilingual.mp4", ".burning.mp4")


def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_json(p, default):
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    return default


def save_json(p, d):
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def probe(cmd_args):
    r = subprocess.run(["ffprobe", "-v", "error"] + cmd_args +
                       ["-of", "json"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    try:
        return json.loads(r.stdout)
    except Exception:
        return {}


def video_params(path):
    d = probe(["-show_streams", "-show_format", path])
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), {})
    fps = 24.0
    if v.get("r_frame_rate") and "/" in v["r_frame_rate"]:
        n, dd = v["r_frame_rate"].split("/")
        if float(dd):
            fps = float(n) / float(dd)
    dur = float(d.get("format", {}).get("duration", 0) or v.get("duration", 0) or 0)
    pix = v.get("pix_fmt", "yuv420p")
    if "10" in pix or pix.startswith("p010"):
        pix = "yuv420p"  # h264_nvenc 仅支持8bit: 10bit源(HEVC10bit版)自动降位
    w, h = int(v.get("width", 1920)), int(v.get("height", 1080))
    if h > 1080:  # 4K源自动降档1080p(平台交付尺寸, 4K烧录产物会失控巨大)
        w = 1920
        h = 1080 if abs(v.get("width", 16) / max(1, v.get("height", 9)) - 16 / 9) < 0.02             else int(v.get("height", 1080) * 1920 / max(1, v.get("width", 1920)))
        h -= h % 2
        w -= w % 2
    return {"w": w, "h": h,
            "fps": fps, "pix_fmt": pix,
            "duration": dur, "has_audio": bool(a)}


# ------------------------------------------------------------------ 素材库

def lib_load():
    return load_json(LIB_MANIFEST, {"clips": {}})


def lib_duration(manifest):
    return sum(c["duration"] for c in manifest["clips"].values())


def probe_new_clips(manifest):
    changed = False
    for fn in os.listdir(LIB_DIR):
        if not fn.lower().endswith((".mp4", ".webm", ".mov")):
            continue
        path = os.path.join(LIB_DIR, fn)
        if path in manifest["clips"]:
            continue
        d = probe(["-show_streams", "-show_format", path])
        v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
        dur = float(d.get("format", {}).get("duration", 0) or v.get("duration", 0) or 0)
        if dur > 1 and v.get("width"):
            manifest["clips"][path] = {"duration": dur,
                                       "w": v.get("width"), "h": v.get("height")}
            changed = True
    if changed:
        save_json(LIB_MANIFEST, manifest)
    return manifest


def ensure_library(target_min, max_new=150):
    sys.path.insert(0, SKILL_DIR)
    from asset_hub import AssetHub
    manifest = probe_new_clips(lib_load())
    total_min = lib_duration(manifest) / 60
    if total_min >= target_min:
        log(f"素材库 {len(manifest['clips'])} 段 / {total_min:.0f} 分钟，充足")
        return manifest
    log(f"素材库 {total_min:.0f} 分钟 < 目标 {target_min} 分钟，开始补充...")
    hub = AssetHub()
    known_ids = {os.path.splitext(os.path.basename(p))[0]
                 for p in manifest["clips"]}
    added = 0
    random.shuffle(TOPICS)
    for topic in TOPICS:
        if added >= max_new or lib_duration(manifest) / 60 >= target_min * 1.15:
            break
        try:
            results = hub.search_videos(topic, per_page=50, orientation="landscape")
        except Exception as e:
            log(f"  搜索失败({topic}): {e}")
            continue
        for asset in results:
            if added >= max_new:
                break
            if f"pexels_{asset['id']}" in known_ids:
                continue
            try:
                p = hub.download(asset)
                if p:
                    added += 1
                    known_ids.add(f"pexels_{asset['id']}")
                    log(f"  + 素材 {os.path.basename(p)} ({asset.get('duration',0)}s) [{added}]")
            except Exception as e:
                log(f"  下载失败: {e}")
            time.sleep(0.3)
        time.sleep(1)
    manifest = probe_new_clips(manifest)
    log(f"素材库现在 {len(manifest['clips'])} 段 / {lib_duration(manifest)/60:.0f} 分钟")
    return manifest


# ------------------------------------------------------------------ 拼接

def build_footage(movie_params, target_sec, manifest, tmpdir):
    """从素材库随机选段 -> 归一化(分辨率/fps/像素格式/静音音轨) -> footage.mp4"""
    clips = [(p, c["duration"]) for p, c in manifest["clips"].items()
             if c["duration"] >= 2]
    random.shuffle(clips)
    picked, acc = [], 0.0
    while acc < target_sec and clips:
        p, d = clips.pop(0)
        picked.append(p)
        acc += d
        if acc >= target_sec * 1.1 and len(picked) >= 3:
            break
    if not picked:
        raise RuntimeError("素材库为空，先运行素材补充")
    lst = os.path.join(tmpdir, "list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in picked:
            f.write("file '" + p.replace("'", r"'\''") + "'\n")
    w, h = movie_params["w"], movie_params["h"]
    fps = movie_params["fps"]
    pix = movie_params["pix_fmt"]
    out = os.path.join(tmpdir, "footage.mp4")
    vf = (f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
          f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,fps={fps:.3f},setsar=1,format={pix}")
    cmd = ["ffmpeg", "-y", "-v", "error",
           "-f", "concat", "-safe", "0", "-i", lst,
           "-f", "lavfi", "-t", f"{target_sec:.3f}",
           "-i", "anullsrc=r=48000:cl=stereo",
           "-filter_complex", f"[0:v]{vf}[v]",
           "-map", "[v]", "-map", "1:a",
           "-t", f"{target_sec:.3f}",
           "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "24",
           "-c:a", "aac", "-b:a", "192k", out]
    log(f"  生成素材段: {len(picked)} 段 / {target_sec/60:.1f} 分钟 / {w}x{h}@{fps:.2f} {pix}")
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0 or not os.path.exists(out):
        raise RuntimeError(f"素材段生成失败: {r.stderr[-500:]}")
    return out, len(picked)


def concat_final(movie, footage, out, movie_params, srt=None):
    """单遍编码: 原片(+可选烧中文字幕) + 风景拼接 -> 产物; 原片永不写入"""
    w, h, fps, pix = (movie_params["w"], movie_params["h"],
                      movie_params["fps"], movie_params["pix_fmt"])
    vf = f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,fps={fps:.3f},setsar=1,format={pix}"
    burn = ""
    cwd = None
    if srt:
        # 双语模式(2026-11-02): 找到英文源则叠加上英下中两条; 找不到回退单语中文
        cwd = os.path.dirname(os.path.abspath(srt))
        en_src = None
        base_m = os.path.splitext(movie)[0]
        for cand in (base_m + ".en.srt", base_m + ".srt.en", base_m + ".en.src.srt"):
            if os.path.exists(cand) and os.path.getsize(cand) > 4000:
                en_src = cand
                break
        if not en_src:
            # 视频内嵌英文轨现抽
            try:
                import json as _json, subprocess as _sp
                pr = _sp.run(["ffprobe", "-v", "error", "-select_streams", "s",
                              "-show_entries", "stream_tags=language", "-of", "json", movie],
                             capture_output=True)
                streams = _json.loads(pr.stdout.decode("utf-8", "replace")).get("streams", [])
                ord_i = 0
                pick = None
                for st in streams:
                    lang = ((st.get("tags") or {}).get("language") or "").lower()
                    if lang in ("eng", "en"):
                        pick = ord_i
                    ord_i += 1
                if pick is not None:
                    ext_path = os.path.join(os.path.dirname(os.path.abspath(srt)), "en.srt")
                    _sp.run(["ffmpeg", "-y", "-v", "error", "-i", movie,
                             "-map", f"0:s:{pick}", ext_path], capture_output=True)
                    if os.path.exists(ext_path) and os.path.getsize(ext_path) > 4000:
                        en_src = ext_path
            except Exception:
                pass
        if en_src:
            import shutil as _sh
            en_dst = os.path.join(os.path.dirname(os.path.abspath(srt)), "en.srt")
            if os.path.abspath(en_src) != os.path.abspath(en_dst):
                _sh.copy2(en_src, en_dst)
            burn = ("subtitles=en.srt:force_style='FontName=Microsoft YaHei,"
                    "FontSize=17,Outline=1,Shadow=0,MarginV=46',"
                    "subtitles=zh.srt:force_style='FontName=Microsoft YaHei,"
                    "FontSize=19,Outline=1,Shadow=0,MarginV=8',")
            log(f"  双语烧录: en源={os.path.basename(en_src)} + zh.srt")
        else:
            burn = ("subtitles=zh.srt:force_style='FontName=Microsoft YaHei,"
                    "FontSize=20,Outline=1,Shadow=0,MarginV=16',")
            log("  单语烧录(未找到英文源)")
    fc = (
        "[0:v]" + burn + f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,format={pix},setsar=1,setpts=PTS-STARTPTS[v0];"
        "[1:v]" + vf + ",setpts=PTS-STARTPTS[v1];"
        "[0:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS[a0];"
        "[1:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS[a1];"
        "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]"
    )
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", movie, "-i", footage,
           "-filter_complex", fc,
           "-map", "[v]", "-map", "[a]",
           "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "23",
           "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart", out]
    log(f"  最终合成(整片重编码 NVENC{'，含字幕烧录' if srt else ''})... 这步最耗时")
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=cwd)
    if r.returncode != 0 or not os.path.exists(out):
        raise RuntimeError(f"合成失败: {r.stderr[-600:]}")


# ------------------------------------------------------------------ 主流程


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


def locked():
    active, _ = _stale_locks(DIR)
    if active:
        return active
    lock = os.path.join(DIR, f"subtitle.{os.getpid()}.lock")
    open(lock, "w").write(str(os.getpid()))
    return None


def qbt_completed_daily():
    env = {}
    for ln in open(QBT_ENV, encoding="utf-8"):
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.strip().split("=", 1)
            env[k] = v
    base = env.get("QBT_URL", "http://127.0.0.1:8080")
    import urllib.parse
    req = urllib.request.Request(base + "/api/v2/auth/login",
          data=urllib.parse.urlencode({"username": env.get("QBT_USER", ""),
                                        "password": env.get("QBT_PASS", "")}).encode())
    with urllib.request.urlopen(req, timeout=8) as r:
        cookie = r.headers.get("Set-Cookie", "").split(";")[0]
    req2 = urllib.request.Request(base + "/api/v2/torrents/info")
    req2.add_header("Cookie", cookie)
    with urllib.request.urlopen(req2, timeout=8) as r:
        ts = json.loads(r.read().decode())
    return [t for t in ts if t.get("category") == "每日电影"
            and t.get("progress", 0) >= 1]


def has_chinese_sub(video):
    """中文字幕就绪: 台账hardsub标记(已烧进画面) 或 .srt.hardsub 或 中文软srt"""
    try:
        led = json.load(open(os.path.join(DIR, "subtitles.json"), encoding="utf-8"))["done"]
        if led.get(os.path.normcase(video), {}).get("hardsub"):
            return True
    except Exception:
        pass
    base = os.path.splitext(video)[0]
    for srt in (base + ".srt.hardsub", base + ".srt", base + ".extracted.srt"):
        if not os.path.exists(srt):
            continue
        s = open(srt, encoding="utf-8-sig", errors="replace").read(6000)
        kana = sum(1 for c in s if "\u3040" <= c <= "\u30ff")
        cjk = sum(1 for c in s if "\u4e00" <= c <= "\u9fff")
        if cjk > 100 and kana < 10:
            return True
    return False


def find_videos(folder):
    out = []
    for root, _, files in os.walk(folder):
        for fn in files:
            if os.path.splitext(fn)[1].lower() not in VIDEO_EXTS:
                continue
            if any(fn.lower().endswith(m) for m in DERIVED_MARKERS):
                continue
            if any(k in fn.lower() for k in (".sample.", "sample_", "-sample", ".trailer", "preview")):
                continue  # 只对主片拼接，派生文件不选
            out.append(os.path.join(root, fn))
    return out


def qbt_incomplete_paths():
    """qBittorrent 未下载完任务的 content_path 集合(curl实现, 稳)"""
    import subprocess as _sp
    env = {}
    for ln in open(os.path.join(DIR, "qbwebui.env"), encoding="utf-8"):
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.strip().split("=", 1); env[k] = v
    base = env.get("QBT_URL", "http://127.0.0.1:8080")
    jar = os.path.join(tempfile.gettempdir(), "qbt_inc.cookie")
    try:
        _sp.run(["curl", "-s", "--max-time", "8", "-c", jar,
                 "-d", f"username={env.get('QBT_USER','')}&password=***REDACTED***
                 base + "/api/v2/auth/login"], capture_output=True)
        r = _sp.run(["curl", "-s", "--max-time", "8", "-b", jar,
                     base + "/api/v2/torrents/info"], capture_output=True)
        ts = json.loads(r.stdout.decode("utf-8", "replace"))
        return {t["content_path"] for t in ts
                if t.get("progress", 1) < 1 and t.get("content_path")}
    except Exception:
        return set()


def ext_valid(video):
    """产物有效: 存在且 >50MB(0字节僵尸=失败合成残留, 必须重建)"""
    p = os.path.splitext(video)[0] + ".ext.mp4"
    return os.path.exists(p) and os.path.getsize(p) > 50_000_000


def _eligible(v, ledger):
    key = os.path.normcase(os.path.abspath(v))
    if key in ledger["done"] and not ledger["done"][key].get("test"):
        if ledger["done"][key].get("uploaded"):
            return False  # 用户已上传, 禁止重建(清理后防复活)
        if ext_valid(v):
            return False
        # 默认不重建: 用户删ext=已传信号(2026-11-01策略反转); 确需重建用 --force-rebuild
        return False
    if ext_valid(v):
        return False
    return has_chinese_sub(v)


def pick_target(ledger):
    seen = set()
    for t in qbt_completed_daily():
        cp = t.get("content_path", "")
        vids = []
        if cp and os.path.isfile(cp):
            vids = [cp]  # 单文件种子: content_path 即视频本体
        elif cp:
            vids = find_videos(cp)
        for v in vids:
            seen.add(os.path.normcase(os.path.abspath(v)))
            if _eligible(v, ledger):
                return v
    # 兜底: 扫 history 的 folder 字段(烧录会移除种子, qbt里找不到了)
    # 但必须排除"还在下载中"的(否则会拼半截文件)
    inc = qbt_incomplete_paths()
    h = json.load(open(os.path.join(DIR, "history.json"), encoding="utf-8"))
    for m in h["movies"]:
        folder = m.get("folder")
        if not folder or not os.path.isdir(folder):
            continue
        fnorm = os.path.normpath(folder)
        if any(fnorm == os.path.normpath(c)
               or fnorm.startswith(os.path.normpath(c) + os.sep)
               or os.path.normpath(c).startswith(fnorm + os.sep)
               for c in inc):
            log(f"  跳过下载中: {os.path.basename(folder)[:45]}")
            continue
        for v in find_videos(folder):
            if os.path.normcase(os.path.abspath(v)) in seen:
                continue
            if _eligible(v, ledger):
                log(f"  从历史目录命中: {os.path.basename(v)[:50]}")
                return v
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--movie")
    ap.add_argument("--minutes", type=int, default=60)
    ap.add_argument("--test-minutes", type=int, default=0)
    ap.add_argument("--in-place", action="store_true")
    ap.add_argument("--force-rebuild", action="store_true",
                    help="产物缺失时强制重建(默认不重建, 用户删ext=已传信号)")
    args = ap.parse_args()

    lock = locked()
    if lock:
        log(f"已有实例运行中({lock})，退出")
        return 0

    ledger = load_json(LEDGER, {"done": {}})
    try:
        movie = args.movie or pick_target(ledger)
        if not movie:
            log("没有待拼接的电影（需：每日电影已下完 + 中文字幕就绪 + 未拼接）")
            return 0
        movie = os.path.abspath(movie)
        movie_key = os.path.normcase(movie)
        if movie_key in ledger["done"] and not args.test_minutes:
            if ledger["done"][movie_key].get("uploaded"):
                log("已上传, 跳过")
                return 0
            if not ext_valid(movie):
                if not args.force_rebuild:
                    log("产物缺失(默认视为已传, 不重建; --force-rebuild 可强制)")
                    return 0
                log("强制重建(--force-rebuild)")
            else:
                log("已拼接过")
                return 0
        minutes = args.test_minutes or args.minutes
        target_sec = minutes * 60

        params = video_params(movie)
        log(f"电影: {os.path.basename(movie)} | {params['w']}x{params['h']} "
            f"@{params['fps']:.2f} {params['pix_fmt']} | {params['duration']/60:.0f}分钟 "
            f"| 追加 {minutes} 分钟")

        manifest = ensure_library(target_min=minutes * 1.3)
        tmpdir = tempfile.mkdtemp(prefix="footage_")
        try:
            # 找可烧的中文字幕(软srt优先; 历史硬字幕版已含字幕->不重复烧)
            base = os.path.splitext(movie)[0]
            burn_srt = None
            for cand in (base + ".srt", base + ".extracted.srt", base + ".srt.hardsub"):
                if os.path.exists(cand):
                    head = open(cand, encoding="utf-8-sig", errors="replace").read(5000)
                    if sum(1 for c in head if "\u4e00" <= c <= "\u9fff") > 100:
                        burn_srt = cand
                        break
            burn_dst = None
            if burn_srt:
                burn_dst = os.path.join(tmpdir, "zh.srt")
                shutil.copy2(burn_srt, burn_dst)
                log(f"  本遍含字幕烧录: {os.path.basename(burn_srt)} (原片不动)")
            else:
                log("  无可烧软字幕(可能已含硬字幕), 仅拼接风景")
            footage, nclips = build_footage(params, target_sec, manifest, tmpdir)
            out = base + (".testext.mp4" if args.test_minutes else ".ext.mp4")
            t0 = time.time()
            concat_final(movie, footage, out, params, srt=burn_dst)
            dt = time.time() - t0

            new_params = video_params(out)
            expect = params["duration"] + target_sec
            ok = abs(new_params["duration"] - expect) < 20
            if not ok:
                raise RuntimeError(
                    f"时长校验失败: 实际 {new_params['duration']:.0f}s vs 预期 {expect:.0f}s")

            if args.in_place:
                bak = base + ".noext.bak"
                shutil.move(movie, bak)
                shutil.move(out, movie)
                os.remove(bak)
                final_path = movie
            else:
                final_path = out
            # 注意: 字幕已烧入产物画面, 不再复制 srt 到产物旁(防双重显示)
            # 原片保留原软字幕, 本地播放不受影响
            # 清理测试产物（视频+字幕），省磁盘
            test_out = base + ".testext.mp4"
            if not args.test_minutes and os.path.exists(test_out):
                try:
                    os.remove(test_out)
                    ts_srt = base + ".testext.srt"
                    if os.path.exists(ts_srt):
                        os.remove(ts_srt)
                    log(f"  已清理测试文件 {os.path.basename(test_out)}")
                except Exception:
                    pass

            ledger["done"][movie_key] = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "out": final_path, "added_min": minutes,
                "clips": nclips, "encode_sec": round(dt),
                "total_min": round(new_params["duration"] / 60, 1),
                "test": bool(args.test_minutes)}
            save_json(LEDGER, ledger)
            log(f"✅ 完成: {os.path.basename(final_path)} | 素材 {nclips} 段 | "
                f"编码 {dt:.0f}s | 总时长 {new_params['duration']/60:.0f} 分钟")
            try:
                import collections_mgr as _cm
                _cname = os.path.basename(os.path.dirname(movie)) or os.path.basename(movie)
                _line = _cm.assign_on_delivery(_cname)
                if _line:
                    log("  " + _line)
            except Exception as _e:
                log(f"  合集登记失败: {str(_e)[:50]}")
            return 0
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    except Exception as e:
        log(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        own = os.path.join(DIR, f"subtitle.{os.getpid()}.lock")
        if os.path.exists(own):
            try:
                os.remove(own)
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())
