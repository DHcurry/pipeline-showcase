import ctypes, ctypes.wintypes, time
from PIL import ImageGrab
from pywinauto import Desktop
for w in Desktop(backend="win32").windows():
    try:
        if w.is_visible() and w.window_text() == "qBittorrent v5.2.3":
            r = ctypes.wintypes.RECT(); ctypes.windll.user32.GetWindowRect(w.handle, ctypes.byref(r))
            print("rect:", r.left, r.top, r.right, r.bottom, "hwnd:", w.handle)
            ImageGrab.grab(bbox=(r.left, r.top, r.right, min(r.bottom, r.top+400)), all_screens=True).save(r"C:\Users\16575\daily-movie\main.png")
    except Exception as e: print("ERR", e)
