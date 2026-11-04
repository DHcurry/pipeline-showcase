from pywinauto import Desktop
for w in Desktop(backend="win32").windows():
    try:
        if w.is_visible() and ("qBittorrent" in w.window_text() or "退出" in w.window_text()):
            print(repr(w.window_text()), w.class_name(), w.process_id)
    except Exception: pass
