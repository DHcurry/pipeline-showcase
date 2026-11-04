# -*- coding: utf-8 -*-
"""SubtitleCat 专业字幕获取: 按片名搜索 -> 优先中文轨(chs/cht/zho), 其次英文轨(交由翻译管线)
用法: python -X utf8 fetch_subcat.py "Queen Rock Montreal" "E:\\movies\\Queen Rock Montreal..."
下载到 <主片同名>.subcat.srt (存在则跳过)
"""
import sys, os, re, time, urllib.request, urllib.parse, html as htmllib

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"}


def get(url, binary=False, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            return data if binary else data.decode("utf-8", errors="replace")
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep(2 + i * 2)


def search(query):
    """返回 [(id, filename)] 最优候选"""
    for ep in (f"https://www.subtitlecat.com/index.php?search={urllib.parse.quote(query)}",
               f"https://www.subtitlecat.com/index.php?query={urllib.parse.quote(query)}"):
        try:
            h = get(ep)
        except Exception:
            continue
        items = re.findall(r'/?subs/(\d+)/([^"<>]+?)\.html', h)
        if items:
            # 去重保序
            seen, out = set(), []
            for i, f in items:
                if (i, f) not in seen:
                    seen.add((i, f))
                    out.append((i, f))
            return out, ep
    return [], None


def pick_best(items, query, min_score=0.35):
    q = re.sub(r"\W+", "", query).lower()
    def score(it):
        name = re.sub(r"\W+", "", it[1]).lower()
        # 覆盖率: query字符被name包含的比例
        hit = sum(1 for c in q if c in name)
        return hit / max(1, len(q))
    ranked = sorted(items, key=score, reverse=True)
    if not ranked or score(ranked[0]) < min_score:
        return []  # 最佳候选与查询词相关度不足 -> 判无结果(防错配垃圾字幕)
    return ranked[:5]


def lang_page(sid, fname, lang):
    return f"https://www.subtitlecat.com/subs/{sid}/{fname}_{lang}.html"


def _abs_srt(base_url, href):
    if href.startswith("http"):
        u = href
    elif href.startswith("/"):
        u = "https://www.subtitlecat.com" + href
    else:
        u = base_url.rsplit("/", 1)[0] + "/" + href
    # 空格等编码
    return urllib.parse.quote(u, safe=":/?&=%")


def _lang_match(href, lang):
    h = href.lower()
    if lang in ("chs", "chi", "zho"):
        return any(h.endswith(k) for k in ("-zh-cn.srt", "-zh-hans.srt", "-chs.srt", "-zh.srt"))
    if lang in ("cht",):
        return any(h.endswith(k) for k in ("-zh-tw.srt", "-zh-hant.srt", "-cht.srt", "-zht.srt"))
    if lang == "eng":
        return h.endswith("-en.srt") or h.endswith("_en.srt") or h.endswith("-eng.srt")
    return h.endswith("-" + lang + ".srt") or h.endswith("_" + lang + ".srt")


def get_srt_link(sid, fname, lang):
    """返回该语言的 .srt 绝对直链; 无则 None"""
    urls = [f"https://www.subtitlecat.com/subs/{sid}/{fname}.html"]
    v = lang_page(sid, fname, lang)
    if v not in urls:
        urls.append(v)
    for u in urls:
        try:
            h = get(u)
        except Exception:
            continue
        hrefs = re.findall(r'href="([^"]+\.srt)"', h)
        for hr in hrefs:
            if _lang_match(hr, lang):
                return _abs_srt(u, hr)
        # 该页无语言后缀的唯一候选才可当 eng (任何 _xxx 语言后缀都拒绝)
        plain = [hr for hr in hrefs if not re.search(r"[-_][a-z]{2,4}\.srt$", hr, re.I)]
        if lang == "eng" and len(plain) == 1:
            return _abs_srt(u, plain[0])
    return None


def normalize_srt(txt):
    """SubtitleCat原格式有序号-时间轴间空行, libass结构性拒读 -> 规范化重建"""
    import re as _re
    pat = _re.compile(r'(\d{1,2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,.]\d{3})')
    matches = list(pat.finditer(txt))
    if not matches:
        return txt
    blocks = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(txt)
        seg = txt[m.end():end]
        lines = [l.strip() for l in seg.splitlines()
                 if l.strip() and not l.strip().isdigit() and '-->' not in l]
        if not lines:
            continue
        t0, t1 = m.group(1).replace('.', ','), m.group(2).replace('.', ',')
        blocks.append(f"{len(blocks)+1}\n{t0} --> {t1}\n" + "\n".join(lines))
    return "\n\n".join(blocks) + "\n"


def _looks_english(txt):
    """下载后内容体检: 英文停用词占比 >=8% 才算英文(纯ASCII挡不住西/葡/法语)"""
    head = txt[:6000].lower()
    words = re.findall(r"[a-z']+", head)
    if len(words) < 50:
        return False
    stops = ("the", "and", "you", "that", "was", "for", "are", "with", "they", "have",
             "this", "not", "what", "all", "when", "your", "can", "said", "there", "each")
    sw = sum(1 for w in words if w in stops) / max(1, len(words))
    return sw >= 0.08


def main():
    query, dest_dir = sys.argv[1], sys.argv[2]
    base = None
    for f in os.listdir(dest_dir):
        if f.lower().endswith((".mp4", ".mkv")):
            base = os.path.splitext(f)[0]
            break
    assert base, "目录内无视频"
    out_en = os.path.join(dest_dir, base + ".subcat.srt")
    out_zh = os.path.join(dest_dir, base + ".subcat.zh.srt")
    if os.path.exists(out_zh) or os.path.exists(out_en):
        print("已有 subcat 字幕, 跳过")
        return
    items, ep = search(query)
    if not items:
        print("搜索无结果:", query)
        return
    print(f"搜索命中 {len(items)} 条, 页:{ep}")
    cands = pick_best(items, query)
    print("候选:", [c[1][:55] for c in cands])
    for sid, fname in cands:
        # 优先中文简体/繁体/通用
        for lang, out in (("chs", out_zh), ("cht", out_zh), ("zho", out_zh),
                          ("chi", out_zh), ("eng", out_en)):
            if os.path.exists(out):
                continue
            try:
                link = get_srt_link(sid, fname, lang)
            except Exception:
                link = None
            if link:
                data = get(link, binary=True)
                txt = normalize_srt(data.decode("utf-8", errors="replace"))
                if len(data) > 4000 and (lang != "eng" or _looks_english(txt)):
                    with open(out, "w", encoding="utf-8") as f:
                        f.write(txt)
                    print(f"✅ 下载 [{lang}] {len(data)} bytes -> {os.path.basename(out)}")
                    return
    print("所有候选语言页均无 srt 直链")


if __name__ == "__main__":
    main()
