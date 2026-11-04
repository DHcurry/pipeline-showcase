"""qBittorrent 管理脚本：优雅退出（处理更新弹窗/退出确认弹窗）"""
import time, subprocess, ctypes, ctypes.wintypes, sys
from pywinauto import Application, Desktop
from pywinauto.keyboard import send_keys
from pywinauto.mouse import click

def qbt_pids():
    out = subprocess.run("tasklist /FI \"IMAGENAME eq qbittorrent.exe\"", shell=True,
                         capture_output=True, text=True, encoding="gbk", errors="replace")
    pids = []
    for line in out.stdout.splitlines():
        parts = line.split()
        if parts and parts[0].lower() == "qbittorrent.exe":
            pids.append(int(parts[1]))
    return pids

def find_win(sub, pid=None):
    for w in Desktop(backend="win32").windows():
        try:
            if w.is_visible() and sub in w.window_text():
                if pid is None or w.process_id() == pid:
                    return w
        except Exception:
            pass
    return None

def rect_of(w):
    r = ctypes.wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(w.handle, ctypes.byref(r))
    return r

def quit_gracefully(timeout=150):
    deadline = time.time() + timeout
    clicked_exit = False
    while time.time() < deadline:
        pids = qbt_pids()
        if not pids:
            print("OK: qBittorrent exited"); return True
        pid = pids[0]
        # 1) 更新弹窗 -> 否(N)
        d = find_win("可用更新")
        if d:
            r = rect_of(d)
            click(coords=(r.left + 218, r.top + 165))
            print("dismissed update dialog")
            time.sleep(0.8); continue
        # 2) 退出确认弹窗 -> 是(Y)
        d = find_win("正在退出")
        if d:
            r = rect_of(d)
            click(coords=(r.left + 55, r.top + 134))
            print("confirmed quit dialog")
            time.sleep(0.8); continue
        # 3) 主窗口 -> 文件菜单 -> 退出
        mw = find_win("qBittorrent v5", pid)
        if mw is None:
            mw = find_win("qBittorrent", pid)
        if mw is None:
            time.sleep(0.5); continue
        popup = find_win("", pid)  # placeholder
        popup = None
        for w in Desktop(backend="win32").windows(process=pid):
            try:
                if w.is_visible() and "Popup" in w.class_name():
                    popup = w; break
            except Exception: pass
        if popup:
            r = rect_of(mw)
            click(coords=(r.left + 70, r.top + 143))   # 退出(X)
            print("clicked 退出 menu item")
            clicked_exit = True
            time.sleep(1.0); continue
        if not clicked_exit:
            ctypes.windll.user32.ShowWindow(mw.handle, 9)
            time.sleep(0.6)
            try:
                mw.set_focus(); time.sleep(0.6)
            except Exception: pass
            send_keys("%f", pause=0.05)
            time.sleep(1.0)
        else:
            time.sleep(0.7)
    print("TIMEOUT"); return False

if __name__ == "__main__":
    ok = quit_gracefully()
    sys.exit(0 if ok else 1)
