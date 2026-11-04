import ctypes, ctypes.wintypes, time
from PIL import ImageGrab
hwnd = ctypes.windll.user32.FindWindowW("Qt6103QWindowIcon", "qBittorrent v5.2.3")
r = ctypes.wintypes.RECT()
ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(r))
print("rect:", r.left, r.top, r.right, r.bottom)
img = ImageGrab.grab(bbox=(r.left, r.top, r.right, min(r.bottom, r.top+700)), all_screens=True)
img.save(r"C:\Users\16575\daily-movie\menu2.png")
from pywinauto import Desktop
for win in Desktop(backend="win32").windows(process=15264):
    if win.is_visible():
        print("VISIBLE:", repr(win.window_text()), win.class_name())
