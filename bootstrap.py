# -*- coding: utf-8 -*-
"""一键引导: 环境体检 → 配置向导 → 启动演示服务
用法: python bootstrap.py
"""
import os, sys, json, shutil, subprocess, socket

ROOT = os.path.dirname(os.path.abspath(__file__))
DM_CANDIDATES = [
    r'C:\Users\16575\daily-movie',           # 本机原始位置
    os.path.join(ROOT, 'pipeline'),           # 仓库内(仅逻辑)
    os.path.join(os.path.expanduser('~'), 'daily-movie'),
]
PORT = int(os.environ.get('PORT', '8787'))


def check(name, ok, note=''):
    print(f"  [{'✓' if ok else '✗'}] {name}" + (f" — {note}" if note else ''))
    return ok


def main():
    print('=' * 56)
    print('🎬 Pipeline Command Center — 环境体检与引导')
    print('=' * 56)

    print('\n[1/4] 运行环境')
    py_ok = sys.version_info >= (3, 9)
    check(f'Python {sys.version.split()[0]}', py_ok, '需 >=3.9')
    ff = shutil.which('ffmpeg')
    check('ffmpeg', bool(ff), ff or '未找到(仅演示可忽略)')
    try:
        import yt_dlp  # noqa
        ytd = True
    except Exception:
        ytd = bool(shutil.which('yt-dlp'))
    check('yt-dlp', ytd, 'B站/视频下载用(仅演示可忽略)')
    # qB 端口探测
    qbt = False
    try:
        s = socket.socket(); s.settimeout(0.6)
        s.connect(('127.0.0.1', 8080)); s.close(); qbt = True
    except Exception:
        pass
    check('qBittorrent WebUI :8080', qbt, '完整管线需要(仅演示可忽略)')

    print('\n[2/4] 配置向导')
    dm_dir = None
    for c in DM_CANDIDATES:
        if os.path.isdir(c) and os.path.exists(os.path.join(c, 'daily_movie.py')):
            dm_dir = c; break
    if dm_dir:
        check('管线目录', True, dm_dir)
    else:
        print('  [i] 未发现完整管线目录 — 演示模式使用仓库 data/ 样例')
    for name in ('site.env', 'qbwebui.env'):
        real = os.path.join(dm_dir or '', name)
        if dm_dir and os.path.exists(real):
            txt = open(real, encoding='utf-8', errors='replace').read()
            filled = 'REPLACE_ME' not in txt and '=' in txt
            check(f'{name} 已配置', filled, real)
        else:
            ex = os.path.join(ROOT, 'config', name + '.example')
            print(f"  [i] {name}: 复制 config/{name}.example 并填真实值 -> daily-movie/")
    # DeepSeek key (只查存在, 不打印值)
    auth = os.path.expanduser(r'~\.pi\agent\auth.json')
    has_key = False
    if os.path.exists(auth):
        try:
            a = json.load(open(auth, encoding='utf-8'))
            has_key = 'deepseek' in a and bool(a['deepseek'].get('key'))
        except Exception:
            pass
    check('DeepSeek key (~/.pi/agent/auth.json)', has_key, '字幕意译用(仅演示可忽略)')

    print('\n[3/4] 仓库完整性')
    for f in ('index.html', 'server.py', 'README.md'):
        check(f, os.path.exists(os.path.join(ROOT, f)))
    for d in ('pipeline', 'memory', 'conversations', 'data', 'config'):
        p = os.path.join(ROOT, d)
        n = sum(len(fs) for _, _, fs in os.walk(p)) if os.path.isdir(p) else 0
        check(f'{d}/ ({n}文件)', os.path.isdir(p) and n > 0)

    print('\n[4/4] 启动演示')
    print(f'  → python server.py  →  http://127.0.0.1:{PORT}   (Windows 也可双击 start.bat)')
    try:
        ans = input('现在启动? [Y/n] ').strip().lower()
    except EOFError:          # 非交互环境(双击/管道)默认启动, 不卡死
        ans = ''
    if ans in ('', 'y', 'yes'):
        # Windows 下用 subprocess 代替 os.execv(兼容性更好, 失败也不会静默闪退)
        code = subprocess.call([sys.executable, os.path.join(ROOT, 'server.py')])
        if os.name == 'nt':
            try:
                input('服务已停止, 回车关闭窗口...')
            except EOFError:
                pass
        sys.exit(code)
    print('已退出。随时运行: python server.py 或双击 start.bat')


if __name__ == '__main__':
    main()
