"""MnemeNet Watch Tray — minimal system tray wrapper.

Usage: pythonw scripts/mnemenet-tray.pyw
Shows a tray icon. Background thread runs mnemenet-watch --once every 300s.
"""

import subprocess, sys, threading, time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
WATCH_PY = SCRIPT_DIR / "mnemenet-watch.py"
INTERVAL = 300

def watch_loop():
    while running:
        try:
            subprocess.run(
                [sys.executable, str(WATCH_PY), "--once"],
                capture_output=True, text=True, timeout=30, encoding="utf-8")
        except: pass
        for _ in range(INTERVAL):
            if not running: break
            time.sleep(1)

# ---- PyQt6 tray (minimal, only tray, no window) ----
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt

def make_icon():
    """Generate a simple green dot icon."""
    pix = QPixmap(16, 16)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(0, 180, 80))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(2, 2, 12, 12)
    p.end()
    return QIcon(pix)

running = True

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

tray = QSystemTrayIcon()
tray.setIcon(make_icon())
tray.setToolTip("MnemeNet Watch")

menu = QMenu()
menu.addAction("Exit").triggered.connect(lambda: (app.quit(), setattr(sys.modules[__name__], 'running', False)))
tray.setContextMenu(menu)
tray.show()

threading.Thread(target=watch_loop, daemon=True).start()
app.exec()
