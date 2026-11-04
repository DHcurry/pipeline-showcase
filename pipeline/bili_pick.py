# -*- coding: utf-8 -*-
"""B站源选片器(方案1): WBI搜索 -> 质量过滤 -> yt-dlp 下载到 E:\\movies -> 全链自动接力
用法:
  python -X utf8 bili_pick.py --search "话剧 录播"     # 只搜不下(dry)
  python -X utf8 bili_pick.py --pick 1                 # 按关键词组轮流选1部并下载
  python -X utf8 bili_pick.py --pick 2 --cookie C:/path/bili_cookies.txt  # 1080p需登录cookie
"""
import urllib.request, urllib.parse, json, hashlib, time, http.cookiejar, re, os, sys, argparse, subprocess

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
OUT_DIR = r'E:\movies'
HISTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'history.json')

# 合集方向关键词(轮换), 每个附带期望时长下限(秒, 完整录播判定)
KEYWORD_SETS = [
    ("纪录片 完整版 央视", 2400),      # 实测金矿: 美丽中国/玄奘之路/新丝绸之路
    ("纪录片 完整版 高清", 2400),
    ("音乐会 全场 完整", 3000),          # 过滤官方切片(多为2-8分钟)
    ("新年音乐会 全场", 3000),
    ("音乐剧 完整 中文", 3000),
    ("话剧 完整 录播", 2400),
    ("戏曲 全剧 高清", 1200),
    ("脱口秀 专场 完整", 1500),
    ("芭蕾 全场 高清", 1800),
]
BAD_WORDS = ('直播', '切片', '预告', '试看', '预告片', '花絮', '混剪', 'reaction', '反应', '速览', '合集搬运')


def make_opener():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    # 先访问主页拿 buvid3 风控 cookie
    try:
        opener.open(urllib.request.Request('https://www.bilibili.com/',
                                           headers={'User-Agent': UA, 'Accept-Language': 'zh-CN,zh;q=0.9'}), timeout=12)
    except Exception:
        pass
    return opener, cj


def wbi_search(opener, keyword, order='click', page=1):
    nav_req = urllib.request.Request('https://api.bilibili.com/x/web-interface/nav',
                                     headers={'User-Agent': UA, 'Referer': 'https://www.bilibili.com/'})
    with opener.open(nav_req, timeout=12) as r:
        nav = json.loads(r.read().decode())
    wbi = nav['data']['wbi_img']
    img_key = wbi['img_url'].rsplit('/', 1)[1].split('.')[0]
    sub_key = wbi['sub_url'].rsplit('/', 1)[1].split('.')[0]
    mixin = img_key + sub_key
    table = [46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
             33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
             61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 12,
             52, 11, 44, 20]
    seq = ''.join(mixin[i] for i in table)[:32]
    params = {'search_type': 'video', 'keyword': keyword, 'order': order, 'page': page, 'danmaku': '0'}
    params['wts'] = str(int(time.time()))
    items = '&'.join(f'{k}={urllib.parse.quote(str(params[k]), safe="")}' for k in sorted(params))
    w_rid = hashlib.md5((items + seq).encode()).hexdigest()
    url = 'https://api.bilibili.com/x/web-interface/search/type?' + items + '&w_rid=' + w_rid
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Referer': 'https://search.bilibili.com/',
                                               'Origin': 'https://search.bilibili.com',
                                               'Accept': 'application/json, text/plain, */*'})
    with opener.open(req, timeout=15) as r:
        d = json.loads(r.read().decode())
    if d.get('code') != 0:
        raise RuntimeError(f"search code={d.get('code')} {d.get('message','')}")
    return (d.get('data') or {}).get('result') or []


def parse_dur(s):
    """'97:12' or '12:34' -> 秒"""
    try:
        parts = [int(x) for x in str(s).split(':')]
        sec = 0
        for p in parts:
            sec = sec * 60 + p
        return sec
    except Exception:
        return 0


def load_history():
    if os.path.exists(HISTORY):
        return json.load(open(HISTORY, encoding='utf-8'))
    return {'movies': []}


def candidates(keyword, min_dur):
    opener, _ = make_opener()
    res = wbi_search(opener, keyword)
    out = []
    for x in res:
        title = re.sub(r'<[^>]+>', '', x.get('title', ''))
        dur = parse_dur(x.get('duration', '0'))
        bvid = x.get('bvid', '')
        if not bvid:
            continue
        if dur < min_dur:
            continue
        if any(w.lower() in title.lower() for w in BAD_WORDS):
            continue
        out.append({'title': title, 'dur': dur, 'bvid': bvid,
                    'play': x.get('play', 0), 'pub': x.get('pubdate', '')})
    out.sort(key=lambda c: -int(c['play'] or 0))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--search', help='搜索关键词(只搜不下载)')
    ap.add_argument('--pick', type=int, default=0, help='按关键词组轮流选N部并下载')
    ap.add_argument('--cookie', help='B站cookie.txt路径(登录态,1080p用)')
    ap.add_argument('--quality', default='bv*[height<=1080]+ba/b[height<=1080]',
                    help='下载格式, 未登录可降为720')
    args = ap.parse_args()

    if args.search:
        md = int(os.environ.get('BILI_MIN_DUR', '0'))
        cands = candidates(args.search, md)
        for c in cands[:15]:
            print(f"{c['dur']//60}分{c['dur']%60:02d}秒 | 播放{c['play']} | {c['title'][:50]} | {c['bvid']}")
        return

    history = load_history()
    done_bvid = {m.get('bvid') for m in history['movies']}
    got = 0
    for kw, min_dur in KEYWORD_SETS:
        if got >= args.pick:
            break
        try:
            cands = candidates(kw, min_dur)
        except Exception as e:
            print(f'[{kw}] 搜索失败: {str(e)[:60]}')
            continue
        print(f'[{kw}] 合格候选 {len(cands)} 部')
        for c in cands[:5]:
            if got >= args.pick:
                break
            if c['bvid'] in done_bvid:
                continue
            url = f"https://www.bilibili.com/video/{c['bvid']}"
            out_t = os.path.join(OUT_DIR, re.sub(r'[<>:"/\\\\|?*]', '_', c['title'])[:80] + '.%(ext)s')
            cmd = ['yt-dlp', '--socket-timeout', '20', '--no-warnings',
                   '-f', args.quality, '-o', out_t]
            if args.cookie:
                cmd += ['--cookies', args.cookie]
            cmd.append(url)
            print(f"下载: {c['title'][:44]} ({c['dur']//60}分, 播放{c['play']}) ...")
            r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                               errors='replace', replace_args=False if False else None, timeout=2400)
            if r.returncode == 0:
                history['movies'].append({
                    'date': time.strftime('%Y-%m-%d'), 'title': c['title'], 'url': url,
                    'bvid': c['bvid'], 'infohash': '', 'size': '', 'seed': 0,
                    'torrent': 'bilibili', 'folder': '', 'source': 'bilibili'})
                json.dump(history, open(HISTORY, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
                got += 1
                done_bvid.add(c['bvid'])
                print(f"✅ 入库 {c['title'][:44]}")
            else:
                print(f"  下载失败: {(r.stderr or '')[-120:]}")
    print(f'完成 {got} 部')


if __name__ == '__main__':
    main()
