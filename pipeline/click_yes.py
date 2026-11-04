import time, subprocess
from pywinauto.mouse import click
x, y = 1072 + 55, 433 + 134   # 是(Y)
click(coords=(x, y))
print("clicked 是(Y) at", x, y)
for i in range(90):
    time.sleep(1)
    out = subprocess.run("tasklist /FI \"PID eq 15264\"", shell=True, capture_output=True, text=True, encoding="gbk", errors="replace")
    if "15264" not in out.stdout:
        print(f"EXITED after {i+1}s"); break
else:
    print("STILL RUNNING")
out = subprocess.run("tasklist /FI \"IMAGENAME eq qbittorrent.exe\"", shell=True, capture_output=True, text=True, encoding="gbk", errors="replace")
print(out.stdout)
