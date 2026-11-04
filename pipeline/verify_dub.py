import subprocess, json, os, glob, sys
sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\download\【高清剧集网发布 www.DDHDTV.com】灾[全6集][中文字幕].Sai.S01.1080p.NF.WEB-DL.AAC.2.0.H.264-BlackTV"
files = sorted(f for f in os.listdir(D) if (f.startswith("Sai.S01E0") or f.startswith("【卡卡】")) and f.endswith((".mkv",".mp4")))
files = [os.path.join(D, f) for f in files]
allok = True
for v in files:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a",
                        "-show_entries", "stream=index:stream_tags=language,title:stream_disposition=default",
                        "-of", "json", v], capture_output=True)
    d = json.loads(r.stdout.decode("utf-8", "replace"))
    auds = d.get("streams", [])
    desc = " | ".join(
        f"#{a['index']} {a.get('tags',{}).get('language','-')}:{a.get('tags',{}).get('title','-')}"
        + (" *默认" if a.get('disposition',{}).get('default') else "")
        for a in auds)
    has_zho = any(a.get('tags',{}).get('language') == 'zho' for a in auds)
    mark = "✅" if has_zho else ("—" if "E01" in v else "⚠")
    if not has_zho and "E01" not in v: allok = False
    print(f"{mark} {os.path.basename(v)[:40]:42s} {desc}")
    if os.path.exists(os.path.splitext(v)[0] + ".dubbing.mkv"):
        print("    ⚠ 残留 .dubbing.mkv")
print("\n结论:", "E02-E06 配音全部就位 ✅" if allok else "有缺失")
