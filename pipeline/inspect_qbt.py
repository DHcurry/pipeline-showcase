from pywinauto import Desktop
d = Desktop(backend="win32")
for w in d.windows(process=15264):
    try:
        print("WIN:", repr(w.window_text()), "visible=", w.is_visible(), "enabled=", w.is_enabled(), "cls=", w.class_name())
    except Exception as e:
        print("ERR", e)
# try menu of main window
from pywinauto import Application
app = Application(backend="win32").connect(process=15264)
w = app.top_window()
try:
    menubar = w.menu_items()
    def dump(items, ind=0):
        for it in items:
            print("  "*ind, it.get("text",""), "| id=", it.get("id"), "| enabled=", it.get("enabled"), "| state=", it.get("state"))
            if it.get("subitems"): dump(it["subitems"], ind+1)
    dump(menubar)
except Exception as e:
    print("MENU ERR:", e)
