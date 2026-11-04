# -*- coding: utf-8 -*-
"""把已生成的 SRT 翻译成简体中文（免费在线：必应优先，多引擎降级）。

用法:
  python translate_srt.py            # 扫描 D:\download 下所有非中文 SRT 并翻译
  python translate_srt.py --file X.srt --lang en
行为:
  原英文/日文备份为 <名>.<lang>.srt，中文写入 <名>.srt（播放器直接加载中文）
  台账 subtitles.json 标记 zh=true，重复运行不会二次翻译
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

DIR = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(DIR, "translate.log")
LEDGER = os.path.join(DIR, "subtitles.json")
SCAN_ROOT = r"E:\movies"  # 管线专属目录
LEGACY_SCAN_ROOT = r"D:\download"  # 过渡期存量


def walk_tree():
    for _r in (SCAN_ROOT, LEGACY_SCAN_ROOT):
        yield from os.walk(_r)
ENGINES = ["bing", "alibaba", "youdao", "baidu"]
SLEEP = 0.12


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


BLOCK_RE = re.compile(r"(\d+)\s*\n(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})")


def parse_srt(path):
    raw = open(path, encoding="utf-8-sig", errors="replace").read()
    blocks = []
    parts = re.split(r"\n\s*\n", raw.strip())
    for p in parts:
        m = BLOCK_RE.search(p)
        if not m:
            continue
        body = p[m.end():].strip("\n")
        blocks.append({"idx": int(m.group(1)), "start": m.group(2),
                       "end": m.group(3), "lines": body.splitlines()})
    return blocks


def translate_line(text, src, cache, stats):
    key = (src, text)
    if key in cache:
        return cache[key]
    import translators as ts
    last_err = None
    for attempt in range(3):
        for eng in ENGINES:
            try:
                r = ts.translate_text(text, translator=eng,
                                      from_language=src, to_language="zh")
                if r and r.strip():
                    cache[key] = r.strip()
                    stats["ok"] += 1
                    time.sleep(SLEEP)
                    return r.strip()
            except Exception as e:
                last_err = e
                time.sleep(0.6 + attempt)
        time.sleep(1.5 * (attempt + 1))
    stats["fail"] += 1
    stats["fail_examples"].append(text[:40])
    log(f"  翻译失败(保留原文): {text[:40]} | {last_err}")
    return None


def translate_file(path, src_lang, force=False):
    ledger = load_ledger()
    base, _ = os.path.splitext(path)
    zh_done = any(v.get("zh_srt") == path for v in ledger["done"].values())
    if zh_done and not force:
        return "已翻译过(台账)"

    # 防重入：主文件已是中文则跳过（避免台账丢失时二次翻译把中文译坏）
    # 注意：日文汉字也落在 CJK 区，必须用假名区分——有假名=日文=需翻译
    sample = open(path, encoding="utf-8-sig", errors="replace").read(6000)
    cjk = sum(1 for c in sample if "\u4e00" <= c <= "\u9fff")
    kana = sum(1 for c in sample if "\u3040" <= c <= "\u30ff")
    if cjk > 100 and kana < 10 and not force:
        return "已含中文，跳过"

    # 若原文件是主 <名>.srt 且尚无语言后缀版本 -> 先备份
    backup = f"{base}.{src_lang}.srt"
    if not os.path.exists(backup):
        import shutil
        shutil.copy2(path, backup)

    # LLM 意译优先(2026-10-27 用户指令: 脱口秀/演出级质量); 任一环节失败 -> 落回机翻链
    try:
        import llm_translate as _llm
        _blocks = parse_srt(path)
        if len(_blocks) >= 5:
            persona = _llm.persona_guess(path)
            t0 = time.time()
            outs, total, miss = [], len(_blocks), 0
            CH = 40
            for ci in range(0, len(_blocks), CH):
                chunk = _blocks[ci:ci + CH]
                lines = [ln for b in chunk for ln in b["lines"]]
                zh = _llm.translate_lines_llm(lines, persona)
                if zh is None:
                    miss += 1
                    outs.append(None)
                else:
                    outs.append(zh)
            if miss / max(1, len(outs)) <= 0.1:
                # 游标式写回: outs 按批(chunk)存, 每块从对应批次顺序消费 n 行
                for bi, b in enumerate(_blocks):
                    ci = bi // CH
                    n = len(b["lines"])
                    if ci < len(outs) and outs[ci] is not None:
                        start = bi * 0  # 占位防误
                        # 计算本块在批次内的行偏移
                        base = 0
                        for jj in range(ci * CH, bi):
                            base += len(_blocks[jj]["lines"])
                        seg = outs[ci][base:base + n]
                        if len(seg) == n:
                            b["lines"] = seg
                tmp = path + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    for j, b in enumerate(_blocks, 1):
                        f.write(str(j) + "\n" + b["start"] + " --> " + b["end"] + "\n")
                        f.write("\n".join(x for x in b["lines"]) + "\n\n")
                os.replace(tmp, path)
                for v in ledger["done"].values():
                    if os.path.abspath(v.get("srt", "")) == os.path.abspath(path):
                        v["zh"] = True
                        v["zh_engine"] = f"deepseek-llm/{persona}"
                        v["zh_cost_sec"] = round(time.time() - t0)
                        break
                save_ledger(ledger)
                return f"LLM意译完成({persona}, {len(_blocks)}块, 失败块{miss}保留原文)"
            # 失败块过多 -> 不落盘, 整体回退机翻
    except Exception as _e:
        log(f"  LLM意译不可用({str(_e)[:60]}), 回退机翻链")

    blocks = parse_srt(path)
    if not blocks:
        return "SRT 无可解析块"
    stats = {"ok": 0, "fail": 0, "fail_examples": []}
    cache = {}
    t0 = time.time()
    n_lines = 0
    for i, b in enumerate(blocks):
        for j, ln in enumerate(b["lines"]):
            s = ln.strip()
            if not s:
                continue
            n_lines += 1
            zh = translate_line(s, src_lang, cache, stats)
            if zh:
                b["lines"][j] = zh
        if (i + 1) % 200 == 0:
            log(f"  进度 {i+1}/{len(blocks)} 块，失败 {stats['fail']}，{time.time()-t0:.0f}s")

    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for k, b in enumerate(blocks, 1):
            f.write(f"{k}\n{b['start']} --> {b['end']}\n")
            f.write("\n".join(x for x in b["lines"]) + "\n\n")
    os.replace(tmp, path)

    # 台账标记
    for k, v in ledger["done"].items():
        if os.path.abspath(v.get("srt", "")) == os.path.abspath(path):
            v["zh"] = True
            v["zh_cost_sec"] = round(time.time() - t0)
            v["zh_fail"] = stats["fail"]
            break
    save_ledger(ledger)
    dt = time.time() - t0
    msg = (f"OK 中文覆盖完成 {os.path.basename(path)} | {len(blocks)}块/{n_lines}行 | "
           f"失败{stats['fail']} | {dt:.0f}s")
    if stats["fail_examples"]:
        msg += f" | 失败例: {stats['fail_examples'][:2]}"
    return msg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file")
    ap.add_argument("--lang", default="", help="源语言(不填则从台账推断,默认 en)")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    ledger = load_ledger()
    if args.file:
        targets = [args.file]
    else:
        # 1) 台账里 lang!=zh 且未标 zh 的 srt
        targets = []
        seen = set()
        for v in ledger["done"].values():
            if v.get("lang", "").startswith("zh"):
                continue
            if v.get("zh") and not args.force:
                continue
            if os.path.exists(v.get("srt", "")):
                targets.append(v["srt"])
                seen.add(os.path.abspath(v["srt"]))
        # 2) 磁盘孤儿：片源自带字幕（如 YTS 官配英文srt）不在台账的也扫
        suffix_re = re.compile(r"\.[a-z]{2,3}\.srt$", re.I)  # .en.srt 等原语言备份不翻
        vexts = {".mkv", ".mp4", ".avi", ".ts", ".mov", ".wmv", ".flv"}
        for root, _, files in walk_tree():
            for fn in files:
                if not fn.lower().endswith(".srt"):
                    continue
                if suffix_re.search(fn):
                    continue
                # 只处理与同目录视频同名的外挂字幕（粉丝组附加语言轨 dut/English 等不碰）
                stem = os.path.splitext(fn)[0]
                if not any(os.path.exists(os.path.join(root, stem + e)) for e in vexts):
                    continue
                p = os.path.join(root, fn)
                if os.path.abspath(p) in seen:
                    continue
                try:
                    if os.path.getsize(p) < 2000:
                        continue
                    sample = open(p, encoding="utf-8-sig", errors="replace").read(6000)
                except Exception:
                    continue
                cjk = sum(1 for c in sample if "\u4e00" <= c <= "\u9fff")
                kana = sum(1 for c in sample if "\u3040" <= c <= "\u30ff")
                if cjk > 100 and kana < 10:
                    continue  # 已是中文
                targets.append(p)

    log(f"待翻译 {len(targets)} 个 SRT")
    for p in targets:
        lang = args.lang
        if not lang:
            # 先查台账，再用内容启发式（有假名=日文，否则英文）
            lang = ""
            for v in ledger["done"].values():
                if os.path.abspath(v.get("srt", "")) == os.path.abspath(p):
                    lang = v.get("lang", "") or ""
                    break
            if not lang:
                try:
                    sample = open(p, encoding="utf-8-sig", errors="replace").read(6000)
                    kana = sum(1 for c in sample if "\u3040" <= c <= "\u30ff")
                    lang = "ja" if kana >= 10 else "en"
                except Exception:
                    lang = "en"
        if lang.startswith("zh"):
            log(f"  跳过中文: {os.path.basename(p)}")
            continue
        try:
            msg = translate_file(p, lang, force=args.force)
        except Exception as e:
            msg = f"❌ {e}"
        log(f"  {msg}")
    log("==== 翻译完成 ====")


if __name__ == "__main__":
    main()
