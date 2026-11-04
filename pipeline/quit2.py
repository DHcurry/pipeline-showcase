import time, subprocess, ctypes, ctypes.wintypes
from pywinauto.mouse import click

# 退出(X) 菜单项位于窗口截图 (70,143) 处；窗口 rect 之前是 685,157 —— 重新取一次
hwnd = ctypes.windll.user32.FindWindowW("Qt6103QWindowIcon", "qBittorrent v5.2.3")
r = ctypes.wintypes.RECT()
ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(r))
print("rect:", r.left, r.top)
x, y = r.left + 70, r.top + 143
click(coords=(x, y))
print("clicked 退出 at", x, y)
for i in range(60):
    time.sleep(1)
    out = subprocess.run("tasklist /FI \"PID eq 15264\"", shell=True, capture_output=True, text=True, encoding="gbk", errors="replace")
    if "15264" not in out.stdout:
        print(f"EXITED after {i+1}s")
        break
else:
    print("STILL RUNNING")
out = subprocess.run("tasklist /FI \"IMAGENAME eq qbittorrent.exe\"", shell=True, capture_output=True, text=True, encoding="gbk", errors="replace")
print(out.stdout)
