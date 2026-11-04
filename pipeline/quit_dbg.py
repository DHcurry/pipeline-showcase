import time, ctypes, ctypes.wintypes
from PIL import ImageGrab
from pywinauto import Application, Desktop
from pywinauto.keyboard import send_keys
from pywinauto.mouse import click

app = Application(backend="win32").connect(process=9888)
w = app.top_window()
hwnd = w.handle
ctypes.windll.user32.ShowWindow(hwnd, 9)
time.sleep(1)
w.set_focus(); time.sleep(1)
fg = ctypes.windll.user32.GetForegroundWindow()
print("hwnd", hwnd, "fg", fg, "focus_ok", fg == hwnd)

def shot(name):
    r = ctypes.wintypes.RECT(); ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(r))
    ImageGrab.grab(bbox=(r.left, r.top, r.right, min(r.bottom, r.top+400)), all_screens=True).save(rf"C:\Users\16575\daily-movie\{name}.png")
    return r

r = shot("dbg_before")
print("rect", r.left, r.top)

# 方式A：键盘 Alt+F 打开文件菜单
send_keys("%f", pause=0.05)
time.sleep(1.2)
popup = [x for x in Desktop(backend="win32").windows(process=9888) if x.is_visible() and "Popup" in x.class_name()]
print("popup after Alt+F:", [x.window_text() for x in popup])
shot("dbg_menu")
if not popup:
    # 方式B：直接点击文件
    click(coords=(r.left + 70, r.top + 143))
    time.sleep(1.2)
    popup = [x for x in Desktop(backend="win32").windows(process=9888) if x.is_visible() and "Popup" in x.class_name()]
    print("popup after click:", [x.window_text() for x in popup])
    shot("dbg_menu2")

if popup:
    # 点击 退出(X)：窗口相对 (70, 143)
    r2 = ctypes.wintypes.RECT(); ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(r2))
    click(coords=(r2.left + 70, r2.top + 143))
    print("clicked exit item")
    time.sleep(1.5)
    for win in Desktop(backend="win32").windows(process=9888):
        if win.is_visible():
            print("visible:", repr(win.window_text()), win.class_name())
