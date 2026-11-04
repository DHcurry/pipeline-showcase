import time, ctypes, ctypes.wintypes
from PIL import ImageGrab
from pywinauto import Application, Desktop
from pywinauto.keyboard import send_keys

app = Application(backend="win32").connect(process=9888)
mw = app.top_window()
ctypes.windll.user32.ShowWindow(mw.handle, 9); time.sleep(0.8)
mw.set_focus(); time.sleep(0.8)
print("fg ok:", ctypes.windll.user32.GetForegroundWindow() == mw.handle)
send_keys("%f", pause=0.05)
time.sleep(1.2)
r = ctypes.wintypes.RECT(); ctypes.windll.user32.GetWindowRect(mw.handle, ctypes.byref(r))
print("rect:", r.left, r.top, r.right, r.bottom)
ImageGrab.grab(bbox=(r.left, r.top, r.left+400, r.top+300), all_screens=True).save(r"C:\Users\16575\daily-movie\pos.png")
for w in Desktop(backend="win32").windows(process=9888):
    if w.is_visible() and "Popup" in w.class_name():
        pr = ctypes.wintypes.RECT(); ctypes.windll.user32.GetWindowRect(w.handle, ctypes.byref(pr))
        print("popup rect:", pr.left, pr.top, pr.right, pr.bottom)
