import time, ctypes, ctypes.wintypes
from pywinauto import Application
from pywinauto.keyboard import send_keys
from PIL import ImageGrab

app = Application(backend="win32").connect(process=15264)
w = app.top_window()
hwnd = w.handle
SW_RESTORE = 9
ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
time.sleep(1.0)
w.set_focus()
time.sleep(0.8)
r = ctypes.wintypes.RECT()
ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(r))
print("rect:", r.left, r.top, r.right, r.bottom)
send_keys("%f", pause=0.05)
time.sleep(1.2)
ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(r))
img = ImageGrab.grab(bbox=(r.left, r.top, r.right, min(r.bottom, r.top+700)), all_screens=True)
img.save(r"C:\Users\16575\daily-movie\menu.png")
print("shot saved", r.left, r.top)
from pywinauto import Desktop
for win in Desktop(backend="win32").windows(process=15264):
    if win.is_visible():
        print("VISIBLE WIN:", repr(win.window_text()), win.class_name())
