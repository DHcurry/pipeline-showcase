import ctypes, ctypes.wintypes
from PIL import ImageGrab
from pywinauto import Desktop
for w in Desktop(backend="win32").windows():
    try:
        if w.is_visible() and "可用更新" in w.window_text():
            r = ctypes.wintypes.RECT(); ctypes.windll.user32.GetWindowRect(w.handle, ctypes.byref(r))
            print("rect:", r.left, r.top, r.right, r.bottom, "hwnd:", w.handle)
            ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom), all_screens=True).save(r"C:\Users\16575\daily-movie\upd.png")
    except Exception as e: print(e)
