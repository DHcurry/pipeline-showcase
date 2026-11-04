# -*- coding: utf-8 -*-
"""灾(Sai)文件夹字幕一键修复：
1) 每集提取官方简体轨 -> <stem>.srt（垃圾外挂备份为 .broken.bak）
2) 备份三轨为 <stem>.jpn.srt / .zh-Hant.srt / .zh-Hans.srt
3) 卡卡E01(与E01同cut)改用E01官方字幕，Whisper版降级为 .whisper.bak
4) 全部视频原地烧录中文字幕（烧后移除内嵌轨，防双重显示）
"""
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
import burn_subs

FOLDER = (r"D:\download\【高清剧集网发布 www.DDHDTV.com】灾[全6集][中文字幕]."
          r"Sai.S01.1080p.NF.WEB-DL.AAC.2.0.H.264-BlackTV")
LEDGER = os.path.join(DIR, "subtitles.json")


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode == 0, r.stderr[-300:]


def count_blocks(srt):
    try:
        return open(srt, encoding="utf-8-sig", errors="replace").read().count("-->")
    except Exception:
        return 0


def extract(video, map_spec, out):
    ok, err = run(["ffmpeg", "-y", "-v", "error", "-i", video,
                   "-map", map_spec, out])
    return ok and os.path.exists(out) and os.path.getsize(out) > 1000


def main():
    os.chdir(FOLDER)
    mkvs = sorted(f for f in os.listdir(FOLDER)
                  if f.endswith(".mkv") and f.startswith("Sai."))
    kaka = next((f for f in os.listdir(FOLDER) if f.startswith("【卡卡】") and f.endswith(".mp4")), None)
    print(f"mkv {len(mkvs)} 集, 卡卡: {kaka}")

    plan = []  # (video, srt_for_burn)
    e01_srt = None

    for mkv in mkvs:
        stem = os.path.splitext(mkv)[0]
        srt = stem + ".srt"
        # 备份三轨（幂等）
        for spec, tag in (("0:s:0", ".jpn.srt"), ("0:s:1", ".zh-Hant.srt"),
                          ("0:s:2", ".zh-Hans.srt")):
            bk = stem + tag
            if not os.path.exists(bk):
                extract(mkv, spec, bk)
                if os.path.exists(bk):
                    print(f"  备份轨道 {os.path.basename(bk)} ({count_blocks(bk)}块)")
        # 官方简体轨 -> 主 srt
        blocks = count_blocks(srt) if os.path.exists(srt) else 0
        if blocks < 300:
            if os.path.exists(srt):
                os.replace(srt, srt + ".broken.bak")
                print(f"  垃圾外挂已备份 ({blocks}块) -> .broken.bak")
            if extract(mkv, "0:s:2", srt):
                print(f"  提取官方简体轨 -> {os.path.basename(srt)} ({count_blocks(srt)}块)")
        else:
            print(f"  srt已合格 ({blocks}块): {os.path.basename(srt)}")
        if "S01E01" in mkv:
            e01_srt = srt
        plan.append((mkv, srt))

    # 卡卡：改用E01官方字幕
    if kaka and e01_srt:
        kstem = os.path.splitext(kaka)[0]
        ksrt = kstem + ".srt"
        if os.path.exists(ksrt) and count_blocks(ksrt) < 600 and not os.path.exists(ksrt + ".whisper.bak"):
            os.replace(ksrt, ksrt + ".whisper.bak")
            print(f"  卡卡Whisper字幕降级 -> .whisper.bak")
        if not os.path.exists(ksrt):
            import shutil
            shutil.copy2(e01_srt, ksrt)
            print(f"  卡卡改用E01官方字幕 ({count_blocks(ksrt)}块)")
        plan.append((kaka, ksrt))

    # 烧录（幂等：已有 hardsub 台账/文件则跳过）
    led = json.load(open(LEDGER, encoding="utf-8")) if os.path.exists(LEDGER) else {"done": {}}
    for video, srt in plan:
        vpath = os.path.join(FOLDER, video)
        key = os.path.normcase(vpath)
        if key in led["done"] and led["done"][key].get("hardsub"):
            print(f"  已烧录过，跳过: {video[:40]}")
            continue
        if not os.path.exists(srt) or count_blocks(srt) < 100:
            print(f"  ⚠ 字幕不合格，不烧: {video[:40]}")
            continue
        print(f"=== 烧录 {video[:60]} ({count_blocks(srt)}块) ===")
        import sys as _s
        _s.argv = ["burn_subs.py", "--file", vpath, "--in-place"]
        try:
            burn_subs.main()
        except SystemExit as e:
            if e.code not in (0, None):
                print(f"  ❌ 烧录失败: {e}")
        except Exception as e:
            print(f"  ❌ 烧录异常: {e}")
    print("==== 灾修复完成 ====")


if __name__ == "__main__":
    main()
