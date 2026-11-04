# -*- coding: utf-8 -*-
"""合集管理器: 交付时自动归类登记 -> collections.json; 供 append_footage 调用"""
import os, json, time

REG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "collections.json")

RULES = [
    (["音乐剧", "剧院魅影", "悲惨世界", "汉密尔顿", "吉屋出租", "玛蒂尔达", "来自远方", "万世巨星",
      "摇滚莫扎特", "冰雪奇缘", "魔法坏女巫", "come from away", "matilda", "hamilton", "phantom",
      "les miser", "rent", "wicked", "jesus christ"], ["stage-musical"]),
    (["演唱会", "巡演", "巡回", "live in", "concert", "tour", "皇后", "nirvana",
      "adele", "shakira", "guts", "eras", "reputation", "mayer", "taylor", "olivia", "billie",
      "艾莉什", "夏奇拉", "梅尔", "涅槃", "阿黛尔", "麦莉", "音乐厅", "paramount", "backyard"], ["concert-live"]),
    (["查普尔", "chappelle", "noah", "诺亚", "路易", "louis", "洛克", "伯翰", "burnham",
      "汉娜", "gadsby", "汤姆林森", "tomlinson", "iglesias", "蓬松", "kaleb", "卡勒布",
      "脱口秀", "comedy", "special", "荒谬", "选择性愤怒", "道格拉斯", "说到哪了", "我全都要",
      "浪女", "sticks", "outrage", "bird revelation", "age of spin", "have it all", "look at you"], ["standup-special"]),
    (["罗小黑", "legend of hei", "彩虹小马", "pony", "海绵宝宝", "spongebob", "佐贺",
      "zombie land saga", "森林传奇", "everfree", "kaguya", "辉夜姬"], ["animation-family"]),
    (["罗小黑", "雾山", "京剧", "越剧", "昆曲", "茶馆", "哪吒", "国漫"], ["cn-original"]),
    (["登峰", "tenzing", "艾维奇", "avicii", "传记", "biography", "四个春天",
      "爱登堡", "镜头背后", "蜗牛回忆录", "memoir"], ["docs-real"]),
    (["皇后", "queen", "nirvana", "rage", "涅槃", "愤怒反对机器", "摇滚", "朋克", "paramount"], ["rock-energy"]),
    (["脱口秀", "喜剧", "专场", "joy", "轻松", "搞笑", "下饭", "爆笑", "荒诞", "道格拉斯", "kaleb"], ["easy-laugh"]),
]


def classify(title, extra=""):
    blob = (title + " " + extra).lower()
    hits = []
    for kws, cids in RULES:
        if any(k.lower() in blob for k in kws):
            for c in cids:
                if c not in hits:
                    hits.append(c)
    return hits


def assign_on_delivery(video_name, extra=""):
    """交付登记: 写 assignments, 返回用于日志的一行摘要"""
    try:
        reg = json.load(open(REG, encoding="utf-8"))
    except Exception:
        return ""
    hits = classify(video_name, extra)
    if not hits:
        hits = ["easy-laugh"] if any(k in video_name.lower() for k in ("fun", "joy")) else []
    reg.setdefault("assignments", {})[video_name] = {
        "collections": hits, "date": time.strftime("%Y-%m-%d"), "state": "delivered"}
    json.dump(reg, open(REG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    colmap = {c["id"]: c for c in reg.get("collections", [])}
    parts, pending = [], []
    for c in hits:
        col = colmap.get(c)
        if not col:
            continue
        if col.get("status") == "pending_create":
            pending.append(col["name"])
        else:
            parts.append(col["name"])
    seg = " + ".join(parts) if parts else "(无已有合集)"
    if pending:
        seg += " | 待创建: " + "、".join(pending)
    return f"📦 合集: {seg}"
