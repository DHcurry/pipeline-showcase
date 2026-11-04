import ctypes, ctypes.wintypes, time
from PIL import ImageGrab
from pywinauto import Desktop
for attempt in range(6):
    for win in Desktop(backend="win32").windows(process=15264):
        t = win.window_text()
        if "退出" in t or "qBittorrent v5" in t:
            r = ctypes.wintypes.RECT()
            ctypes.windll.user32.GetWindowRect(win.handle, ctypes.byref(r))
            if r.right - r.left > 50:
                img = ImageGrab.grab(bbox=(r.left, r.top, r.right, min(r.bottom, r.top+500)), all_screens=True)
                img.save(rf"C:\Users\16575\daily-movie\exit{attempt}.png")
                print("shot", attempt, t, r.left, r.top)
    time.sleep(5)
