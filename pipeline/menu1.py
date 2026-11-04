import time
from pywinauto import Application
from pywinauto.keyboard import send_keys
from PIL import ImageGrab
import ctypes

app = Application(backend="win32").connect(process=15264)
w = app.top_window()
w.set_focus()
time.sleep(0.6)
send_keys("%{F4}" if False else "%f", pause=0.05)   # Alt+F 打开文件菜单
time.sleep(1.2)
# 截取主窗口区域
hwnd = w.handle
r = ctypes.wintypes.RECT()
import ctypes.wintypes
ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(r))
print("rect:", r.left, r.top, r.right, r.bottom)
img = ImageGrab.grab(bbox=(r.left, r.top, r.right, min(r.bottom, r.top+600)), all_screens=True)
img.save(r"C:\Users\16575\daily-movie\menu.png")
# 枚举进程窗口看有无 popup
from pywinauto import Desktop
for win in Desktop(backend="win32").windows(process=15264):
    if win.is_visible():
        print("VISIBLE WIN:", repr(win.window_text()), win.class_name())
