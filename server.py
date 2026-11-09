# -*- coding: utf-8 -*-
"""Pipeline Command Center - 零依赖演示服务
- GET  /            -> index.html
- GET  /api/stats   -> 聚合 daily-movie 真实台账统计(读不到回退样例)
- GET  /api/stream  -> SSE 实时日志(真实日志tail + 管线事件注入, 永远有料)
- POST /api/ask     -> 调 pi -p (Pi Agent SDK CLI) 流式返回回答
运行: python server.py  (默认 http://127.0.0.1:8787)
"""
import json, os, time, threading, subprocess, http.server, socketserver, urllib.parse, queue

ROOT = os.path.dirname(os.path.abspath(__file__))
# 台账目录解析(异地兼容): PIPELINE_DIR环境变量 → 本机管线 → 仓库data/快照(演示模式)
_cands = [os.environ.get('PIPELINE_DIR', ''), r'C:\Users\16575\daily-movie',
          os.path.join(os.path.expanduser('~'), 'daily-movie')]
DM = next((c for c in _cands if c and os.path.isdir(c)), None) or os.path.join(ROOT, 'data')
REAL_MODE = os.path.exists(os.path.join(DM, 'daily_movie.py'))  # False=仓库快照演示模式
PORT = int(os.environ.get('PORT', '8787'))

# ---------------- 数据聚合 ----------------
def _load(name, default):
    p = os.path.join(DM, name)
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return default

ICON = {"stage-musical": "🎭", "concert-live": "🎤", "standup-special": "😂",
        "animation-family": "🎬", "cn-original": "🇨🇳", "docs-real": "🎥",
        "rock-energy": "🎸", "easy-laugh": "😄"}

def stats():
    h = _load('history.json', {'movies': []})
    a = _load('append.json', {'done': {}})
    c = _load('collections.json', {'collections': [], 'assignments': {}})
    sub = _load('subtitles.json', {'done': {}})

    works = len(h.get('movies', []))
    hours = round(sum(v.get('total_min', 0) or 0 for v in a.get('done', {}).values()) / 60)
    subs = sum(abs(v.get('segments', 0) or 0) for v in sub.get('done', {}).values())
    llm = sum(1 for v in sub.get('done', {}).values()
              if 'llm' in str(v.get('lang', '')) or 'llm' in str(v.get('source', '')))
    cols = c.get('collections', [])
    colls_out = []
    for col in cols:
        n = sum(1 for v in c.get('assignments', {}).values() if col['id'] in v.get('collections', []))
        colls_out.append({'name': col.get('name', col['id']), 'icon': ICON.get(col['id'], '📁'),
                          'count': n, 'pending': col.get('status') == 'pending_create'})
    # 最近交付(按 append 台账日期倒序)
    items = sorted(a.get('done', {}).items(), key=lambda kv: (kv[1].get('date') or ''), reverse=True)
    timeline = []
    for k, v in items[:8]:
        name = os.path.basename(os.path.dirname(k)) or os.path.basename(k)
        timeline.append({'date': v.get('date', ''), 'title': name[:34],
                         'note': f"{round((v.get('total_min') or 0))}min"})
    # 阶段计数(在途/处理中)
    active = 0
    try:
        env = {}
        for l in open(os.path.join(DM, 'qbwebui.env'), encoding='utf-8').read().splitlines():
            l = l.strip()
            if l and not l.startswith('#') and '=' in l:
                kk, vv = l.split('=', 1); env[kk.strip()] = vv.strip()
        out = subprocess.run(['curl', '-s', '-b', os.path.join(DM, 'qb.cookie'),
                              env.get('QBT_URL', '') + '/api/v2/torrents/info'],
                             capture_output=True, timeout=8).stdout
        active = sum(1 for t in json.loads(out) if t.get('progress', 1) < 0.99)
    except Exception:
        active = 0
    return {
        'works': works, 'hours': hours, 'subs': subs, 'llm': llm, 'colls': len(colls_out),
        'collections': colls_out, 'timeline': timeline,
        'stages': {'pick': min(works, 99), 'dl': active, 'tr': len(sub.get('done', {})),
                   'zh': llm, 'cover': works, 'burn': len(a.get('done', {})), 'done': len(colls_out)},
    }

# ---------------- 日志流 ----------------
LOG_FILES = [os.path.join(DM, 'append.log'), os.path.join(DM, 'subtitle.log'),
             os.path.join(DM, 'daily_movie.log'), os.path.join(DM, 'translate.log')]
SIM_EVENTS = [
    ('INFO', '选片引擎: 扫描站内候选池(评分≥7.5 表演闸门)'),
    ('OK', '磁力已附加公共 tracker, 启动验证通过'),
    ('INFO', '下载中: 三点速度采样 120/240/360s'),
    ('INFO', 'AI 转写: faster-whisper small · CUDA int8_float16'),
    ('AI', 'LLM 意译: DeepSeek · 脱口秀人设 · 块数校验 100%'),
    ('OK', '官方内嵌中文字幕提取 + 同步闸门 PASS'),
    ('INFO', '封面生成: FastSD SD-Turbo 960x540'),
    ('OK', '风景拼接: 155段素材 / 60.0分钟 / NVENC 单遍编码'),
    ('OK', '双语烧录完成: en源 + zh.srt 上英下中'),
    ('OK', '📦 合集登记: 演唱会·现场直击 (已有) | 待创建: 芭蕾·舞蹈现场'),
    ('INFO', '产物缺失默认不重建(用户删ext=已传信号)'),
    ('AI', 'Pi 大脑: 归类判定 -> 脱口秀·爆笑专场 + 轻松下饭'),
]
class Feeder(threading.Thread):
    def __init__(self, q):
        super().__init__(daemon=True); self.q = q
        self.pos = {f: os.path.getsize(f) if os.path.exists(f) else 0 for f in LOG_FILES}
        self.k = 0
    def run(self):
        while True:
            got = False
            # 真实日志 tail
            for f in LOG_FILES:
                try:
                    sz = os.path.getsize(f)
                    if sz > self.pos[f]:
                        with open(f, 'rb') as fh:
                            fh.seek(self.pos[f])
                            data = fh.read(sz - self.pos[f]).decode('utf-8', 'replace')
                        self.pos[f] = sz
                        for line in data.splitlines():
                            line = line.strip()
                            if not line: continue
                            lvl = 'OK' if '✅' in line else ('ERR' if ('❌' in line or 'Traceback' in line) else ('WARN' if '⚠' in line else 'INFO'))
                            self.q.put({'level': lvl, 'msg': line[:220]})
                            got = True
                except Exception:
                    pass
            # 模拟事件注入(保演示节奏)
            if not got and self.k % 12 == 0:
                lv, msg = SIM_EVENTS[(self.k // 12) % len(SIM_EVENTS)]
                self.q.put({'level': lv, 'msg': msg})
                got = True
            self.k += 1
            time.sleep(2.5 if got else 0.4)

# ---------------- pi 调用 ----------------
def pi_stream(q, prompt):
    """shell 调 pi -p, 按行推给 SSE"""
    cmd = 'pi -p "' + prompt.replace('"', '\\"')[:400] + '"'
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             text=True, encoding='utf-8', errors='replace')
        for line in p.stdout:
            q.put(line)
        p.wait(timeout=120)
    except Exception as e:
        q.put(f'\n[error] {e}')

# ---------------- HTTP ----------------
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code); self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ('/', '/index.html'):
            data = open(os.path.join(ROOT, 'index.html'), 'rb').read()
            self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
        elif path == '/api/stats':
            self._json(stats())
        elif path == '/api/stream':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()
            q = queue.Queue()
            Feeder(q).start()
            try:
                while True:
                    try:
                        ev = q.get(timeout=8)
                    except queue.Empty:
                        ev = {'level': 'INFO', 'msg': 'heartbeat'}
                    self.wfile.write(f"data: {json.dumps(ev, ensure_ascii=False)}\n\n".encode('utf-8'))
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
        else:
            self.send_response(404); self.end_headers()
    def do_POST(self):
        if urllib.parse.urlparse(self.path).path != '/api/ask':
            self.send_response(404); self.end_headers(); return
        n = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(n) or b'{}')
        prompt = body.get('q', '').strip() or '总结这套内容管线'
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Transfer-Encoding', 'chunked')
        self.end_headers()
        q = queue.Queue()
        def worker():
            pi_stream(q, '你是每日电影自动化内容管线的AI大脑。' + prompt)
            q.put(None)
        threading.Thread(target=worker, daemon=True).start()
        try:
            while True:
                line = q.get()
                if line is None: break
                self.wfile.write(f'{len(line.encode("utf-8")):x}\r\n'.encode())
                self.wfile.write(line.encode('utf-8')); self.wfile.write(b'\r\n'); self.wfile.flush()
            self.wfile.write(b'0\r\n\r\n')
        except Exception:
            pass

class S(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True; allow_reuse_address = True

if __name__ == '__main__':
    mode = '真实台账模式' if REAL_MODE else '演示快照模式(data/)'
    for p in range(PORT, PORT + 6):
        try:
            srv = S(('127.0.0.1', p), H)
        except OSError:
            print(f'  [i] 端口 {p} 被占用, 尝试 {p + 1}...')
            continue
        print(f'Pipeline Command Center [{mode}] -> http://127.0.0.1:{p}')
        srv.serve_forever()
        break
    else:
        raise SystemExit('端口 8787-8791 均被占用, 试: set PORT=9000 && python server.py')
