# -*- coding: utf-8 -*-
"""每日一部电影：从 教父.com(/mv) 随机挑一部未下载过的电影，提取最优磁力，交给本机 qBittorrent。

用法: python daily_movie.py [--test] [--time hh:mm]
产物: history.json (去重台账)、daily_movie.log (运行日志)
凭据: site.env (站点账号)、qbwebui.env (qBittorrent WebUI)  同目录
"""
import argparse
import html as htmlmod
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime

BASE = "https://www.hgeme.com"  # 2026-10-22 切换新源(教父站宕机, 用户指令); 同平台同模板同账号
BASE_OLD = "https://www.xn--wcv59z.com"  # 原教父站(宕机备用)
DIR = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(DIR, "state.json")
HISTORY = os.path.join(DIR, "history.json")
LOG = os.path.join(DIR, "daily_movie.log")
SITE_ENV = os.path.join(DIR, "site.env")
QBT_ENV = os.path.join(DIR, "qbwebui.env")
QBT_EXE = r"D:\Program Files\qBittorrent\qbittorrent.exe"
SAVE_DRIVE = "D:/"
MIN_FREE_GB = 8          # 剩余空间低于此值不再新增
MAX_SIZE_GB = 12
MIN_RATING = 7.0
MIN_SPEED_BPS = 100 * 1024   # 启动后速度低于此值视为太慢换片(用户: 太慢了就换一部)          # 豆瓣评分门槛(平台上传选好片)         # 单部硬上限
PREFER_SIZE_GB = 6       # 优选上限
CATEGORY = "每日电影"
TAGS = "daily-movie"

# 站点磁力不带 tracker，纯靠 DHT 很难冷启动，附加公共 tracker
PUBLIC_TRACKERS = [
    "udp://tracker.opentrackr.org:1337/announce",
    "http://tracker.opentrackr.org:1337/announce",
    "udp://open.demonii.com:1337/announce",
    "udp://tracker.torrent.eu.org:451/announce",
    "udp://exodus.desync.com:6969/announce",
    "udp://open.stealth.si:80/announce",
    "udp://tracker.bt.bt.wtf:1337/announce",
]

def augment_magnet(magnet):
    if "tr=" in magnet:
        return magnet
    sep = "&" if "?" in magnet else "?"
    for t in PUBLIC_TRACKERS:
        magnet += f"{sep}tr={t}"
        sep = "&"
    return magnet

# ---------------------------------------------------------------- utils

def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def read_env(path):
    env = {}
    if os.path.exists(path):
        for ln in open(path, encoding="utf-8"):
            ln = ln.strip()
            if "=" in ln and not ln.startswith("#"):
                k, v = ln.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def load_history():
    if os.path.exists(HISTORY):
        return json.load(open(HISTORY, encoding="utf-8"))
    return {"movies": []}


def save_history(h):
    json.dump(h, open(HISTORY, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


_D_WARNED = False


def free_gb():
    """下载盘剩余空间: E盘(下载落点)为准; D盘仅警告不阻塞(用户自用盘, 每轮只报一次)"""
    global _D_WARNED
    import shutil
    try:
        e = shutil.disk_usage("E:/").free / 1024**3
    except Exception:
        e = 999
    try:
        d = shutil.disk_usage("D:/").free / 1024**3
        if d < 8 and not _D_WARNED:
            _D_WARNED = True
            log(f"⚠ D盘仅剩 {d:.1f}GB (用户自用盘, 不影响下载, 但影响上传暂存)")
    except Exception:
        pass
    return e

# ---------------------------------------------------------------- qBittorrent WebUI

class Qbt:
    def __init__(self):
        env = read_env(QBT_ENV)
        self.url = env.get("QBT_URL", "http://127.0.0.1:8080")
        self.user = env.get("QBT_USER", "admin")
        self.pw = env.get("QBT_PASS", "")
        self.cookie = None

    def _req(self, path, data=None, timeout=15):
        body = None
        headers = {}
        if data is not None:
            body = urllib.parse.urlencode(data).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        req = urllib.request.Request(self.url + path, data=body, headers=headers)
        if self.cookie:
            req.add_header("Cookie", self.cookie)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                sc = r.headers.get("Set-Cookie", "")
                if sc:
                    self.cookie = ";".join(
                        c.split(";")[0] for c in sc.split(",") if "=" in c.split(";")[0])
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")

    def alive(self):
        # 未带会话时可能返回 401/403，只要 HTTP 有响应就说明服务在跑
        try:
            code, _ = self._req("/api/v2/app/version", timeout=5)
            return code in (200, 401, 403)
        except Exception:
            return False

    def start_app(self):
        log("qBittorrent WebUI 不可用，尝试启动 qBittorrent ...")
        subprocess.Popen(["cmd", "/c", "start", "", QBT_EXE])
        for i in range(45):
            time.sleep(2)
            if self.alive():
                log(f"qBittorrent 已就绪 ({i*2}s)")
                return True
        return False

    def login(self):
        code, txt = self._req("/api/v2/auth/login",
                              {"username": self.user, "password": self.pw})
        ok = code == 200 and "Ok" in txt
        if not ok:
            # 新版 qBittorrent 登录成功返回204/Ok，兼容空成功体
            ok = code in (200, 204)
        if not ok:
            raise RuntimeError(f"qBittorrent 登录失败: HTTP {code} {txt[:80]}")
        return True

    def hashes(self):
        code, txt = self._req("/api/v2/torrents/info")
        if code != 200:
            raise RuntimeError(f"获取种子列表失败 HTTP {code}")
        return {t["hash"] for t in json.loads(txt)}

    def add_magnet(self, magnet, name=""):
        data = {"urls": augment_magnet(magnet), "category": CATEGORY,
                "tags": TAGS, "savepath": r"E:\movies"}
        code, txt = self._req("/api/v2/torrents/add", data, timeout=30)
        if code != 200:
            raise RuntimeError(f"添加磁力失败 HTTP {code} {txt[:120]}")
        return True

    def remove(self, infohash):
        code, txt = self._req("/api/v2/torrents/delete",
                              {"hashes": infohash, "deleteFiles": "true"})
        return code == 200

    def get(self, infohash):
        code, txt = self._req("/api/v2/torrents/info")
        if code != 200:
            return None
        for t in json.loads(txt):
            if t["hash"].lower() == infohash.lower():
                return t
        return None

    def verify_started(self, infohash, seconds=300):
        """轮询直到拿到元数据（说明找到 peers）。返回 (ok, state_desc)"""
        t0 = time.time()
        last = None
        absent_since = None
        while time.time() - t0 < seconds:
            t = self.get(infohash)
            if t is None:
                # 磁力元数据解析可能数百秒才入列: 宽限等待, 防"验证/移除双扑空"留下孤儿下载
                if absent_since is None:
                    absent_since = time.time()
                elif time.time() - absent_since > 240:
                    return False, "torrent 不在列表(宽限240s仍未出现)"
                time.sleep(10)
                continue
            absent_since = None
            last = t
            if t.get("total_size", -1) and t["total_size"] > 0:
                return True, (f"{t['state']} peers={t.get('num_peers')} "
                              f"seeds={t.get('num_seeds')} dlspeed={t.get('dlspeed')}")
            time.sleep(15)
        s = last or {}
        return False, (f"超时 {seconds}s: state={s.get('state')} "
                       f"peers={s.get('num_peers')} dlspeed={s.get('dlspeed')}")

# ---------------------------------------------------------------- 站点会话 (Playwright)

def new_browser(pw, storage=True):
    b = pw.chromium.launch(headless=True,
                           args=["--disable-blink-features=AutomationControlled"])
    ctx = b.new_context(
        locale="zh-CN",
        user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"),
        viewport={"width": 1440, "height": 900},
        storage_state=STATE if storage and os.path.exists(STATE) else None)
    return b, ctx


def wait_pw(pg, rounds=25):
    for _ in range(rounds):
        time.sleep(1)
        try:
            if "验证" not in pg.title():
                break
        except Exception:
            pass


def site_login(pg):
    env = read_env(SITE_ENV)
    user, pw = env.get("SITE_USER"), env.get("SITE_PASS")
    if not user or not pw:
        raise RuntimeError("缺少站点凭据 site.env (SITE_USER/SITE_PASS)")
    log("会话失效，重新登录站点 ...")
    pg.goto(BASE + "/user/login", wait_until="domcontentloaded", timeout=60000)
    wait_pw(pg)
    pg.wait_for_selector("input[name=username]", timeout=20000)
    pg.fill("input[name=username]", user)
    pg.fill("input[name=password]", pw)
    try:
        pg.check("input[name=cookietime]", timeout=3000)
    except Exception:
        pass
    for sel in ["button[type=submit]", "input[type=submit]", "text=登录"]:
        try:
            el = pg.locator(sel).first
            if el.is_visible(timeout=2000):
                el.click(timeout=3000)
                break
        except Exception:
            continue
    time.sleep(4)
    # hgeme: 登录成功后 URL 可能滞留 /user/login 但标题已变 -> 等待/刷新直至一致
    for _ in range(6):
        if "login" not in pg.url and "登录" not in pg.title():
            break
        try:
            pg.reload(wait_until="domcontentloaded", timeout=30000)
        except Exception:
            pass
        time.sleep(3)
    if "login" in pg.url or "登录" in pg.title():
        raise RuntimeError(f"站点登录失败: {pg.url} {pg.title()}")
    pg.context.storage_state(path=STATE)
    log("站点登录成功，会话已保存")


def ensure_logged_in(pg, goto=None):
    if goto:
        pg.goto(goto, wait_until="domcontentloaded", timeout=60000)
    wait_pw(pg)
    time.sleep(1.5)
    if "login" in pg.url or "未登录" in pg.title():
        site_login(pg)
        if goto:
            pg.goto(goto, wait_until="domcontentloaded", timeout=60000)
            wait_pw(pg)
            time.sleep(1.5)
    if "未登录" in pg.title() or "login" in pg.url:
        raise RuntimeError("登录后仍无法访问")

# ---------------------------------------------------------------- 挑电影

STAGE_GENRES = ("歌舞", "音乐", "脱口秀", "戏曲", "纪录片", "动画", "儿童", "传记")  # 2026-10-27 +传记(传记纪录片富矿: 体育/人文传记)
STAGE_BAD_TITLE = re.compile(r"春晚|晚会|守岁|跨年|生来知己|元宵|颁奖|德云社|相声大会")  # "剧场版"不可入黑名单: 音乐剧舞台放映版也叫剧场版, 靠表演闸门区分
STAGE_TITLE_PASS = re.compile(
    r"演唱会|音乐会|交响|音乐剧|歌剧|话剧|舞台|剧场(?!版)|剧院(?!版)|演出|周年|现场|巡演|告别|"
    r"Live|Concert|Anniversary|Stage|Broadway|Royal Albert|Gala|Special|(?<!优)秀|"
    r"坂本龙一|杰作|天鹅湖|摇滚莫扎特|来自远方|辉夜姬|魅影|悲惨世界|盖茨比|查普尔|"
    r"路易·C·K|诺亚|伯尔|伯翰|汤姆林森|达斯|伊格莱西亚斯|绿洲|皇后乐队|碧昂丝|"
    r"齐柏林|艾维奇|超音速|汉密尔顿|吉屋出租|理发陶德|女巫|创世纪|猫 |万世巨星|Roast|吐槽|单口|喜剧中心|Comedy Central|Special|克里斯|洛克|弗兰科|"
    r"Eurovision|Glastonbury|Cirque|Ballet|Opera|On Ice|Greatest Showman|"
    r"卡内基|大都会|芭蕾|冰上|马戏|胡桃夹子|吉赛尔|邓肯|音乐之声|追梦|星光|大赛|决赛|"
    # 传记纪录片类(2026-10-27)
    r"传记|生涯|回忆|回顾|旅程|不败|不朽|Legacy|Biography|Journey|"
    r"One Life|Story Of|Life Of|Inside The|The Life|Rock & Roll|Hall of Fame|"
    r"筑梦|庆典|百年|首映|首唱|sing|Sing|along|Frost|Frozen|Encanto|Wicked|"
    # 戏曲类(2026-10-25)
    r"京剧|越剧|昆曲|黄梅戏|豫剧|川剧|秦腔|评剧|锡剧|沪剧|婺剧|粤剧|潮剧|梨园|折子|名段|唱腔|"
    # 纪录片类(2026-10-25)
    r"海洋|星空|自然|野生|动物(?!城|总动员|庄园|特工队)|植物|星球|脉动|深海|冰冻|森林|沙漠|山脉|河流|"
    r"Planet|Earth|Ocean|Wild|Nature|Life|Universe|Cosmos|Galaxy|Blue|Frozen Planet|"
    r"国家地理|Discovery|BBC|大卫|爱登堡|Attenborough|盖亚|微距|显微|航拍|"
    r"地球脉动|蓝色星球|地球故事|地球密码|行星地球|Planet Earth|Earth From|Frozen Planet|宇宙时空|宇宙深处|宇宙纪元|奥德赛|Cosmos|银河|太空|火星",
    re.I)


def pick_movie(pg, history, qbt, tried=(), tries=6, genre="", classic=False, decade=1, region="", stage=False):
    """挑未下载过的高分电影；stage=True 舞台录播模式(音乐剧/演唱会/脱口秀, 2020s->2010s)"""
    def _norm_url(u):
        return u.replace("xn--wcv59z.com", "hgeme.com").rstrip("/")
    done_urls = {_norm_url(m["url"]) for m in history["movies"]} | {_norm_url(u) for u in tried}
    done_hashes = {m.get("infohash", "").lower() for m in history["movies"]}
    existing = {h.lower() for h in qbt.hashes()}

    for attempt in range(tries):
        list_urls = None
        if stage:
            list_urls = [f"{BASE}/mv?sort=score&res=" + urllib.parse.quote("磁力")
                         + f"&genre={urllib.parse.quote(g)}&year={y}"
                         for g in STAGE_GENRES for y in (120, 110, 100)]
        gpart = ("&genre=" + urllib.parse.quote(genre)) if genre else ""
        rpart = ("&region=" + urllib.parse.quote(region)) if region else ""
        if classic:
            # 经典区: 不限画质, 按年代+地区筛选
            list_url = f"{BASE}/mv?sort=score&res=" + urllib.parse.quote("磁力") + f"&year={decade}" + rpart + gpart
        else:
            list_url = f"{BASE}/mv?sort=score&res=" + urllib.parse.quote("磁力") + "&quality=1080P" + gpart
        hrefs = []
        for lu in (list_urls if stage else [list_url]):
            ensure_logged_in(pg, lu)
            _q = pg.eval_on_selector_all(
            'a[href*="/mv/"]',
            "els=>[...new Set(els.map(e=>e.href).filter(h=>/^https?:\\/\\/[^/]+\\/mv\\/[A-Za-z0-9]+\\/?$/.test(h)))]")
            hrefs += _q
        hrefs = list(dict.fromkeys(hrefs))
        cands = [h for h in hrefs if _norm_url(h) not in done_urls]
        random.shuffle(cands)
        log(f"列表候选 {len(hrefs)} 部，去重后 {len(cands)} 部 (尝试 {attempt+1})")
        best = None
        for url in cands[:12]:  # 多探详情页以按做种优选(薄磁力池站点需要更大抽样)
            movie = inspect_movie(pg, url, done_hashes, existing,
                                  min_seed=1 if attempt < tries - 1 else 0)
            if movie and stage:
                if STAGE_BAD_TITLE.search(movie["title"]):
                    log(f"舞台黑名单跳过: {movie['title'][:40]}")
                    continue
                if not STAGE_TITLE_PASS.search(movie["title"]):
                    log(f"非表演类跳过: {movie['title'][:40]}")
                    continue
                if movie.get("_rating", 10) < 7.5:
                    continue
            if movie:
                if best is None or movie["seed"] > best["seed"]:
                    best = movie
                if movie["seed"] >= 25:  # 早退门槛提高: 逼迫完成12部抽样再取最优(薄磁力站点)
                    return movie
        if best:
            return best
    raise RuntimeError("连续多轮没有挑到合适的电影（可能都已下载过/无合格磁力）")


def parse_size(s):
    m = re.search(r"([\d.]+)\s*(GB|MB|TB)", s or "", re.I)
    if not m:
        return None
    v = float(m.group(1))
    u = m.group(2).upper()
    return v if u == "GB" else v / 1024 if u == "MB" else v * 1024


def get_douban_rating(pg):
    """详情页豆瓣评分(评分区第一个, 无则0)"""
    try:
        vals = pg.eval_on_selector_all(".ratings-section .freshness",
                                       "els=>els.map(e=>e.innerText.trim())")
        for v in vals:
            m = re.search(r"([\d.]+)", v)
            if m:
                return float(m.group(1))
    except Exception:
        pass
    return 0.0


def inspect_movie(pg, url, done_hashes, existing, min_seed=1):
    ensure_logged_in(pg, url)
    title = pg.title().replace(" | 网站演示", "").strip()
    rating = get_douban_rating(pg)
    if rating < MIN_RATING:
        log(f"跳过《{title}》：豆瓣评分 {rating} < {MIN_RATING}")
        return None
    rows = pg.eval_on_selector_all(
        "table.bit_list tbody tr",
        """els=>els.map(tr=>{
            const a=tr.querySelector('a[href^="magnet:"]');
            if(!a) return null;
            const td=[...tr.querySelectorAll('td')].map(x=>x.innerText.trim());
            return {magnet:a.getAttribute('href'), name:a.getAttribute('title')||td[0]||'',
                    size:td[2]||'', seed:td[3]||'', time:td[4]||''};
        }).filter(Boolean)""")
    if not rows:
        log(f"跳过《{title}》：无磁力资源")
        return None

    for r in rows:
        r["size_gb"] = parse_size(r["size"])
        try:
            r["seed"] = int(re.sub(r"\D", "", r["seed"]) or 0)
        except Exception:
            r["seed"] = 0
        m = re.search(r"btih:([a-fA-F0-9]{40})", r["magnet"])
        r["infohash"] = m.group(1).lower() if m else ""

    # 过滤：已在历史/已在qBittorrent/超硬上限/枪版预告
    pool = [r for r in rows
            if r["infohash"] not in done_hashes
            and r["infohash"] not in existing
            and (r["size_gb"] is None or r["size_gb"] <= MAX_SIZE_GB)
            and r["seed"] >= min_seed
            and not re.search(r"预告|枪版|抢先", r["name"])]
    if not pool:
        log(f"跳过《{title}》：磁力不符合条件 ({len(rows)} 条, min_seed={min_seed})")
        return None

    # 优选：优先做种多且 <= PREFER_SIZE_GB；其次做种多且 <= MAX
    def rank(r):
        ok = r["size_gb"] is not None and r["size_gb"] <= PREFER_SIZE_GB
        return (0 if ok else 1, -r["seed"])
    pool.sort(key=rank)
    best = pool[0]

    # 空间检查
    need = (best["size_gb"] or 4) + MIN_FREE_GB
    if free_gb() < need:
        smaller = [r for r in pool
                   if r["size_gb"] and r["size_gb"] + MIN_FREE_GB <= free_gb()]
        if not smaller:
            log(f"磁盘剩余 {free_gb():.1f}GB 不足，跳过《{title}》")
            return None
        smaller.sort(key=rank)
        best = smaller[0]

    return {"title": title, "url": url, "_rating": rating, **{k: best[k] for k in
            ("magnet", "name", "size", "size_gb", "seed", "infohash")}}

# ---------------------------------------------------------------- main

def run():
    ap = argparse.ArgumentParser()
    ap.add_argument("--genre", default="", help="限定类型, 如 歌舞/音乐/剧情")
    ap.add_argument("--classic", action="store_true",
                    help="经典低侵权风险模式: 1960年前作品(多为公有领域), 不限画质")
    ap.add_argument("--decade", type=int, default=1,
                    help="classic模式年代值: 1=1960前, 110=2010年代, 100=2000年代, 90=90年代...")
    ap.add_argument("--region", default="", help="地区限定: 大陆/香港/美国/日本...")
    ap.add_argument("--stage", action="store_true",
                    help="舞台录播模式: 音乐剧/演唱会/脱口秀等高分节目(2020s->2010s, 低侵权风险)")
    ap.add_argument("--dry-run", action="store_true", help="只挑片不下载")
    args = ap.parse_args()

    log("=" * 20 + " 每日一部开始 " + "=" * 20)
    qbt = Qbt()
    if not qbt.alive():
        if not qbt.start_app():
            raise RuntimeError("qBittorrent 无法启动")
    qbt.login()

    history = load_history()
    free = free_gb()
    log(f"磁盘剩余 {free:.1f}GB，历史已下载 {len(history['movies'])} 部")

    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b, ctx = new_browser(pw)
        pg = ctx.new_page()
        try:
            tried, last_err = [], None
            for round_i in range(3):
                try:
                    movie = pick_movie(pg, history, qbt, tried=tried, genre=args.genre,
                                        classic=args.classic, decade=args.decade,
                                        region=args.region, stage=args.stage)
                except Exception as e:
                    log(f"⚠ 选片轮次{round_i+1}异常({str(e)[:60]}), 换轮重试")
                    last_err = str(e)[:80]
                    continue
                log(f"选中《{movie['title']}》 | {movie['size']} | 做种 {movie['seed']} | {movie['url']}")
                if args.dry_run:
                    print(json.dumps(movie, ensure_ascii=False, indent=1))
                    return 0
                qbt.add_magnet(movie["magnet"])
                ok, desc = qbt.verify_started(movie["infohash"], seconds=300)
                if ok:
                    # 速度门槛: 新源起速慢 -> 120/240/360s 三点采样, 任一点达标即放行, 全程低于地板才判死换片
                    import time as _t
                    speed = 0
                    for _i in range(3):
                        _t.sleep(120)
                        tinfo = qbt.get(movie["infohash"]) or {}
                        speed = tinfo.get("dlspeed", 0) or 0
                        if speed >= MIN_SPEED_BPS:
                            log(f"  速度采样#{_i+1}: {speed/1024:.0f}KB/s 达标放行")
                            break
                    if speed < MIN_SPEED_BPS:
                        # 慢速车道: 后台慢慢下 + 必须登记history(否则去重失明, 会重复选同一部!)
                        log(f"⚠ 《{movie['title']}》360s仍过慢({speed/1024:.0f}KB/s), 保留慢速车道后台续下, 换下一个")
                        _t = qbt.get(movie["infohash"]) or {}
                        history["movies"].append({
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "title": movie["title"], "url": movie["url"],
                            "infohash": movie["infohash"], "size": movie["size"],
                            "seed": movie["seed"], "torrent": movie["name"],
                            "folder": _t.get("content_path"), "slow_lane": True})
                        save_history(history)
                        tried.append(movie["url"])
                        continue
                if not ok:
                    log(f"⚠ 启动验证失败({desc})，移除换下一部")
                    qbt.remove(movie["infohash"])
                    import time as _t2
                    _t2.sleep(8)
                    qbt.remove(movie["infohash"])  # 迟到入列的元数据在宽限期内补删, 防孤儿下载
                    tried.append(movie["url"])
                    last_err = desc
                    continue
                # 记录最终保存路径（后续简介/封面等后处理不依赖 qBittorrent 任务存在）
                folder = None
                try:
                    t = qbt.get(movie["infohash"])
                    folder = (t or {}).get("content_path")
                except Exception:
                    pass
                history["movies"].append({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "title": movie["title"],
                    "url": movie["url"],
                    "infohash": movie["infohash"],
                    "size": movie["size"],
                    "seed": movie["seed"],
                    "torrent": movie["name"],
                    "folder": folder,
                })
                save_history(history)
                log(f"✅ 已入列并验证启动（{desc}）《{movie['title']}》 {movie['size']}")
                print(json.dumps({"ok": True, "title": movie["title"],
                                  "size": movie["size"], "seed": movie["seed"],
                                  "free_gb": round(free, 1)},
                                 ensure_ascii=False))
                return 0
            raise RuntimeError(f"连续3部均无法启动下载，最后原因: {last_err}")
        finally:
            try:
                pg.context.storage_state(path=STATE)  # 刷新会话
            except Exception:
                pass
            b.close()


if __name__ == "__main__":
    try:
        sys.exit(run())
    except Exception as e:
        log(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
