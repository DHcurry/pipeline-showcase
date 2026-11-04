import ctypes, ctypes.wintypes
from PIL import ImageGrab
from pywinauto import Desktop
for win in Desktop(backend="win32").windows(process=15264):
    if "正在退出" in win.window_text():
        r = ctypes.wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(win.handle, ctypes.byref(r))
        print("dialog rect:", r.left, r.top, r.right, r.bottom, "hwnd:", win.handle)
        img = ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom), all_screens=True)
        img.save(r"C:\Users\16575\daily-movie\dlg.png")
        print("size:", img.size)
