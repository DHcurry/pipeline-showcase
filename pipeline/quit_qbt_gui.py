"""优雅退出 qBittorrent GUI（含退出确认对话框处理）"""
import time, subprocess, ctypes, ctypes.wintypes
from pywinauto import Application
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

def quit_gracefully(timeout=120):
    if not qbt_pids():
        print("qBittorrent not running"); return True
    app = Application(backend="win32").connect(timeout=20, process=qbt_pids()[0])
    w = app.top_window()
    hwnd = w.handle
    ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    time.sleep(1.0)
    w.set_focus(); time.sleep(0.8)
    r = ctypes.wintypes.RECT(); ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(r))
    click(coords=(r.left + 70, r.top + 143))   # 文件菜单 -> 退出(X)
    time.sleep(1.0)
    # 确认对话框 "正在退出 qBittorrent" -> 是(Y) @ (55,134)
    from pywinauto import Desktop
    dlg = None
    for _ in range(15):
        for win in Desktop(backend="win32").windows():
            try:
                if "正在退出" in win.window_text() and win.is_visible():
                    dlg = win; break
            except Exception: pass
        if dlg: break
        time.sleep(0.5)
    if dlg:
        time.sleep(0.5)
        d = ctypes.wintypes.RECT(); ctypes.windll.user32.GetWindowRect(dlg.handle, ctypes.byref(d))
        click(coords=(d.left + 55, d.top + 134))
        print("confirmed exit dialog")
    for i in range(timeout):
        time.sleep(1)
        if not qbt_pids():
            print(f"qBittorrent exited after {i+1}s"); return True
    print("TIMEOUT: still running"); return False

if __name__ == "__main__":
    ok = quit_gracefully()
    raise SystemExit(0 if ok else 1)
