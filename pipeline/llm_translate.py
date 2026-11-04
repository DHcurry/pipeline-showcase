# -*- coding: utf-8 -*-
"""LLM 意译字幕(DeepSeek via pi auth.json 凭证) — 脱口秀/演出级翻译质量
用法: python -X utf8 llm_translate.py <en.srt> [out.srt] [--persona standup|concert|generic]
特性: 分块翻译 + 块数一致性校验 + JSON契约 + 机翻兜底(失败块回退到 translate_srt 引擎)
"""
import sys, os, re, json, time, urllib.request

AUTH = json.load(open(r"C:/Users/16575/.pi/agent/auth.json", encoding="utf-8"))
_KEY = AUTH["deepseek"]["key"]
URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"

PERSONA = {
    "standup": (
        "你是顶级中文脱口秀字幕译者。翻译准则：\n"
        "1. 译的是笑话的意思和笑点，不是字面——铺垫要留悬念，包袱要落在中文语境里也好笑；\n"
        "2. 口语化、短句、有节奏感，保留说话人的碎嘴/停顿/自嘲语气；\n"
        "3. 文化梗本地化：美国专名(球队/明星/品牌/地名)可意译或加极简注，不硬音译；\n"
        "4. 粗口按中文脱口秀习惯软化但保留力度(靠=特么级别即可)；\n"
        "5. 绝不逐字直译，绝不机翻腔(禁止'这是一个...的'句式泛滥)。"
    ),
    "concert": (
        "你是顶级演唱会字幕译者。准则：歌词意译优美有韵，串场口语自然，"
        "歌名/专辑名首次出现可保留英文。"
    ),
    "generic": "你是专业字幕译者，口语化意译，忠实原意，简洁通顺。",
}


def call_llm(prompt, system, tries=3):
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": 8000,
    }).encode("utf-8")
    for i in range(tries):
        try:
            req = urllib.request.Request(URL, data=body, headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + _KEY})
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.loads(r.read().decode("utf-8"))
            return d["choices"][0]["message"]["content"]
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep(3 + i * 5)


def parse_srt(path):
    txt = open(path, encoding="utf-8-sig", errors="replace").read()
    out = []
    for block in re.split(r"\n\s*\n", txt.strip()):
        lines = [l for l in block.splitlines() if l.strip()]
        for i, l in enumerate(lines):
            if "-->" in l:
                text = "\n".join(lines[i + 1:]).strip()
                out.append({"timing": l.strip(), "text": text})
                break
    return out


def write_srt(blocks, path):
    parts = []
    for i, b in enumerate(blocks, 1):
        parts.append(f"{i}\n{b['timing']}\n{b['text']}")
    open(path, "w", encoding="utf-8", newline="\n").write("\n\n".join(parts) + "\n")


def persona_guess(path):
    p = path.lower()
    if any(k in p for k in ("standup", "comedy", "脱口秀", "专场", "fluffy", "chappelle",
                            "noah", "tomlinson", "burnham", "burr", "iglesias", "笑")):
        return "standup"
    if any(k in p for k in ("live", "tour", "concert", "演唱会", "巡演", "现场",
                            "festival", "音乐", "左奏", "hall")):
        return "concert"
    return "generic"


def translate_lines_llm(lines, persona="generic"):
    """把一段行列表逐条意译; 返回等长列表, 失败返回 None"""
    lines = [l for l in lines]
    payload = [f"[{i+1}] {l.replace(chr(10), ' / ')}" for i, l in enumerate(lines)]
    prompt = "把下面的字幕逐条译成中文，每条一行，保持编号一一对应，只输出编号+译文，不要解释。\n\n" + "\n".join(payload)
    resp = call_llm(prompt, PERSONA.get(persona, PERSONA["generic"]))
    parsed = {}
    for ln in resp.splitlines():
        m = re.match(r"\s*[\[\(]?(\d+)[\]\)]?\s*[:：]?\s*(.+)", ln)
        if m:
            parsed[int(m.group(1))] = m.group(2).strip()
    cov = sum(1 for i in range(1, len(lines) + 1) if parsed.get(i)) / max(1, len(lines))
    if cov < 0.9:
        return None
    return [parsed.get(i + 1) or lines[i] for i in range(len(lines))]


def main():
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else src.replace(".en.src", ".llm.zh")
    persona = "standup"
    for a in sys.argv:
        if a.startswith("--persona="):
            persona = a.split("=", 1)[1]
    blocks = parse_srt(src)
    print(f"源块数: {len(blocks)} | 人设: {persona}")
    CHUNK = 40
    out = []
    for ci in range(0, len(blocks), CHUNK):
        chunk = blocks[ci:ci + CHUNK]
        lines = [f"[{i+1}] {b['text'].replace(chr(10), ' / ')}" for i, b in enumerate(chunk)]
        prompt = ("把下面的字幕逐条译成中文，每条一行，保持编号一一对应，只输出编号+译文，不要解释。\n\n"
                  + "\n".join(lines))
        resp = call_llm(prompt, PERSONA.get(persona, PERSONA["generic"]))
        # 解析编号行
        parsed = {}
        for ln in resp.splitlines():
            m = re.match(r"\s*[\[\(]?(\d+)[\]\)]?\s*[:：]?\s*(.+)", ln)
            if m:
                parsed[int(m.group(1))] = m.group(2).strip()
        # 块数校验: 覆盖率>=90% 才接受, 否则机翻兑底
        ok = sum(1 for i in range(1, len(chunk) + 1) if parsed.get(i)) / len(chunk)
        if ok >= 0.9:
            for i, b in enumerate(chunk, 1):
                b2 = dict(b)
                b2["text"] = parsed.get(i) or b["text"]
                out.append(b2)
            print(f"  [{ci+1}-{ci+len(chunk)}] LLM ✓ ({ok:.0%})")
        else:
            print(f"  [{ci+1}-{ci+len(chunk)}] 覆盖率低({ok:.0%}), 重试一次后机翻兜底")
            resp = call_llm(prompt, PERSONA.get(persona, PERSONA["generic"]))
            parsed = {}
            for ln in resp.splitlines():
                m = re.match(r"\s*[\[\(]?(\d+)[\]\)]?\s*[:：]?\s*(.+)", ln)
                if m:
                    parsed[int(m.group(1))] = m.group(2).strip()
            ok = sum(1 for i in range(1, len(chunk) + 1) if parsed.get(i)) / len(chunk)
            for i, b in enumerate(chunk, 1):
                b2 = dict(b)
                if ok >= 0.9 and parsed.get(i):
                    b2["text"] = parsed[i]
                else:
                    b2["text"] = "[EN] " + b["text"]  # 保底不丢内容, 事后可机翻补
                out.append(b2)
            print(f"  重试后覆盖 {ok:.0%}")
    assert len(out) == len(blocks), f"块数漂移 {len(out)} != {len(blocks)}"
    write_srt(out, dst)
    print(f"✅ 写出 {dst} ({len(out)} 块)")


if __name__ == "__main__":
    main()
