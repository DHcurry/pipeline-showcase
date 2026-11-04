import time, subprocess
from pywinauto import Application
from pywinauto.keyboard import send_keys
import ctypes

app = Application(backend="win32").connect(process=15264)
w = app.top_window()
w.set_focus()
time.sleep(0.8)
fg = ctypes.windll.user32.GetForegroundWindow()
print("main hwnd:", w.handle, "foreground:", fg, "focused_ok:", fg == w.handle)
send_keys("^q", pause=0.05)
print("sent ^q")
for i in range(40):
    time.sleep(1)
    r = subprocess.run("tasklist /FI \"PID eq 15264\"", shell=True, capture_output=True, text=True, encoding="gbk", errors="replace")
    if "15264" not in r.stdout:
        print(f"EXITED after {i+1}s")
        break
else:
    print("still running after 40s")
    r = subprocess.run("tasklist /FI \"IMAGENAME eq qbittorrent.exe\"", shell=True, capture_output=True, text=True, encoding="gbk", errors="replace")
    print(r.stdout)
