# -*- coding: utf-8 -*-
"""把 SRT 字幕压制（硬字幕）进视频，用于上传 B 站等不支持外挂字幕的平台。

用法:
  python burn_subs.py --file "D:\\download\\xxx\\电影.mkv"            # 只烧中文字幕
  python burn_subs.py --file "电影.mkv" --bilingual                    # 中文+英文双语(英上中下)
  python burn_subs.py --file "电影.mkv" --out "电影.b站版.mp4"

要点:
  - 字幕先拷到临时短路径，绕开 ffmpeg 滤镜对 [] , : ' 等特殊字符的转义地狱
  - 视频用 GTX1650 NVENC 硬编(近实时)，音轨直接 copy
  - 输出默认与源同目录: <名>.subbed.mp4 / <名>.bilingual.mp4
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")


def find_srt(video, suffix=""):
    base, _ = os.path.splitext(video)
    p = base + suffix + ".srt"
    return p if os.path.exists(p) else None


def norm_path(p):
    """git-bash 风格 /d/x -> D:\\x（Windows python 会把 /d/ 错转成 C:\\d\\）"""
    import re
    m = re.match(r"^/([A-Za-z])/(.+)$", p)
    if m:
        return m.group(1).upper() + ":\\" + m.group(2).replace("/", "\\")
    return p


def release_from_qbt(video):
    """原片若是 qBittorrent 种子内容 -> 移除任务(文件保留)：
    释放句柄 + 避免替换后种子完整性报错。用 curl(实测稳定，urllib 403)。"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qbwebui.env")
    if not os.path.exists(env_path):
        return False
    env = {}
    for ln in open(env_path, encoding="utf-8"):
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.strip().split("=", 1)
            env[k] = v
    base = env.get("QBT_URL", "http://127.0.0.1:8080")
    jar = os.path.join(tempfile.gettempdir(), "qbt_rel.cookie")

    def curl(args):
        r = subprocess.run(["curl", "-s", "--max-time", "15"] + args,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        return r.returncode == 0, r.stdout
    try:
        ok, _ = curl(["-c", jar, "-d", f"username={env.get('QBT_USER','')}&password=***REDACTED***
                      base + "/api/v2/auth/login"])
        if not ok:
            return False
        ok, txt = curl(["-b", jar, base + "/api/v2/torrents/info"])
        if not ok or not txt.strip():
            return False
        import json as _json
        ts = _json.loads(txt)
        vp = os.path.normpath(video)
        hit = [t for t in ts if t.get("content_path") and
               (os.path.normpath(t["content_path"]) == vp or
                vp.startswith(os.path.normpath(t["content_path"]) + os.sep))]
        if not hit:
            return False
        hashes = ";".join(t["hash"] for t in hit)
        names = ", ".join(t["name"][:40] for t in hit)
        ok, _ = curl(["-b", jar, "-d", f"hashes={hashes}", "-d", "deleteFiles=false",
                      base + "/api/v2/torrents/delete"])
        if ok:
            time.sleep(2)
            print(f"已从 qBittorrent 移除(文件保留): {names}")
        return ok
    except Exception as e:
        print(f"qBittorrent 联动失败(继续尝试替换): {e}")
        return False



import re as _re

def _pid_alive(pid):
    """Windows 安全探活（严禁 os.kill(pid,0)，Windows 上会直接杀进程）"""
    import ctypes as _ct
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    h = _ct.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if h:
        _ct.windll.kernel32.CloseHandle(h)
        return True
    return False


def _stale_locks(pattern_dir, prefix="subtitle."):
    """返回 (存活锁路径 or None, 忽略)"""
    import glob, time as _t
    for f in glob.glob(os.path.join(pattern_dir, prefix + "*.lock")):
        try:
            m = _re.search(r"(\d+)\.lock$", f)
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


def acquire_lock():
    """与 subtitle/append 共用 subtitle.*.lock，防 GPU 任务并发"""
    d = os.path.dirname(os.path.abspath(__file__))
    active, _ = _stale_locks(d)
    if active:
        return active
    lock = os.path.join(d, f"subtitle.{os.getpid()}.lock")
    open(lock, "w").write(str(os.getpid()))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--bilingual", action="store_true", help="中文+英文字幕同时烧(英文备份.srt)")
    ap.add_argument("--out", default="", help="输出文件名(默认自动)")
    ap.add_argument("--font-size", type=int, default=0, help="0=用默认样式")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--in-place", action="store_true",
                    help="烧完覆盖原视频；原srt改名.srt.hardsub保留(防双重字幕)并登台账防重转写")
    args = ap.parse_args()

    if not args.dry_run:
        lk = acquire_lock()
        if lk:
            print(f"GPU 忙(另一任务持有锁 {lk})，退出等待下次")
            return
    own_lock = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            f"subtitle.{os.getpid()}.lock")
    import atexit
    def _release_lock(p=own_lock):
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
    atexit.register(_release_lock)   # 任何提前异常(SystemExit等)都兜底释放

    video = os.path.abspath(norm_path(args.file))
    if not os.path.exists(video):
        raise SystemExit(f"视频不存在: {video}")
    zh = find_srt(video)
    if not zh:
        raise SystemExit("没找到中文字幕 <视频名>.srt（先跑 subtitle.py / translate_srt.py）")

    tmp = tempfile.mkdtemp(prefix="burnsub_")
    zh_tmp = os.path.join(tmp, "zh.srt")
    shutil.copy2(zh, zh_tmp)

    fs = f",FontSize={args.font_size}" if args.font_size else ""
    filters = [f"subtitles=zh.srt:force_style='FontName=Microsoft YaHei,"
               f"FontSize=20,Outline=1,Shadow=0,MarginV=16{fs}'"]

    if args.bilingual:
        en = find_srt(video, ".en") or find_srt(video, ".ja")
        if not en:
            print("⚠ 没找到英文备份 .en.srt，只烧中文")
        else:
            en_tmp = os.path.join(tmp, "en.srt")
            shutil.copy2(en, en_tmp)
            filters.insert(0, f"subtitles=en.srt:force_style='FontName=Arial,"
                              f"FontSize=16,Outline=1,Shadow=0,MarginV=52'")
            # 先画英文(在上层区域)，再画中文，互不遮挡

    base, _ = os.path.splitext(video)
    if args.out:
        out = args.out if os.path.isabs(args.out) else os.path.join(os.path.dirname(video), args.out)
    elif args.in_place:
        out = base + ".burning.mp4"
    else:
        out = base + (".bilingual.mp4" if args.bilingual and len(filters) > 1 else ".subbed.mp4")

    vf = ",".join(filters)
    cmd = ["ffmpeg", "-y", "-i", video,
           "-vf", vf,
           "-c:v", "h264_nvenc", "-preset", "p5", "-cq", "23",
           "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart", out]

    print("命令:", " ".join(cmd[:8]), "...")
    print("滤镜:", vf)
    print("输出:", out)
    if args.dry_run:
        shutil.rmtree(tmp, ignore_errors=True)
        return
    try:
        _do_burn(args, video, tmp, filters, base, out, cmd)
    finally:
        if os.path.exists(own_lock):
            try:
                os.remove(own_lock)
            except Exception:
                pass


def _do_burn(args, video, tmp, filters, base, out, cmd):
    if args.in_place:
        release_from_qbt(video)
        time.sleep(1)
    # 断点续传：上次编码成功但替换被占 -> 跳过编码直接再试替换
    have_resume = (args.in_place and os.path.exists(out)
                   and os.path.getsize(out) > 10 * 1024 * 1024)
    if have_resume:
        print(f"发现已有烧录产物({os.path.getsize(out)//1024**2}MB)，跳过编码直接替换")
    else:
        print("开始压制(GTX1650 NVENC，长片约几分钟)...")
        r = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if r.returncode != 0:
            shutil.rmtree(tmp, ignore_errors=True)
            print("❌ ffmpeg 失败:")
            print(r.stderr[-1500:])
            raise SystemExit(1)
        sz = os.path.getsize(out) / 1024 ** 3
        print(f"✅ 完成: {out} ({sz:.2f} GB)")
    shutil.rmtree(tmp, ignore_errors=True)

    if args.in_place:
        for attempt in range(5):
            try:
                os.replace(out, video)
                break
            except PermissionError:
                print(f"目标被占用，等待重试 ({attempt+1}/5)...")
                time.sleep(6)
        else:
            raise SystemExit("替换失败：原片仍被占用（可能正在播放，请关闭后重试）")
        print(f"已覆盖原视频: {video}")
        srt = base + ".srt"
        if os.path.exists(srt):
            os.replace(srt, srt + ".hardsub")
            print(f"srt 已改名保留(防双重字幕): {os.path.basename(srt)}.hardsub")
            # 登转写台账，防 subtitle.py 因 srt 消失而重新转写
            lp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subtitles.json")
            try:
                led = json.load(open(lp, encoding="utf-8")) if os.path.exists(lp) else {"done": {}}
                key = os.path.normcase(video)
                ent = led["done"].setdefault(key, {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "srt": srt + ".hardsub", "lang": "zh", "segments": -1,
                    "duration_min": 0, "cost_sec": 0, "zh": True})
                ent["hardsub"] = True        # 无论新旧条目都补烧录标记
                ent["srt"] = srt + ".hardsub"
                json.dump(led, open(lp, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=1)
                print("已登台账(防重转写)")
            except Exception as e:
                print(f"台账登记失败(无害): {e}")


if __name__ == "__main__":
    main()
