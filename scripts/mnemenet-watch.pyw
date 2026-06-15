"""MnemeNet Watch — GUI + system tray polling daemon.

Window shows live status. Close → minimize to tray (green M).
Right-click tray → Exit.

pythonw scripts/mnemenet-watch.pyw
"""

import json, os, subprocess, sys, threading, time
from datetime import datetime
from pathlib import Path

try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QSystemTrayIcon,
                                  QMenu, QLabel, QVBoxLayout, QWidget)
    from PyQt6.QtGui import QIcon, QPixmap, QPainter, QBrush, QPen, QColor, QFont
    from PyQt6.QtCore import Qt, QTimer
except ImportError:
    print("PyQt6 not installed: pip install PyQt6"); sys.exit(1)

REPO = "Offblink/MnemeNet"
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
FOOTPRINT = PROJECT_DIR / "comment-footprint.json"
NOTIFY_DIR = PROJECT_DIR / "notifications"
ALERT = NOTIFY_DIR / "alert.json"
INTERVAL = 300

def gh(endpoint):
    r = subprocess.run(["gh","api",f"repos/{REPO}{endpoint}"],
        capture_output=True,text=True,timeout=15,encoding="utf-8")
    if r.returncode: raise RuntimeError(r.stderr.strip())
    return json.loads(r.stdout)

def load_fp():
    if FOOTPRINT.exists(): return json.loads(FOOTPRINT.read_text(encoding="utf-8"))
    return []

def save_fp(data):
    FOOTPRINT.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

def check_one(entry):
    try: comments = gh(f"/issues/{entry['issue']}/comments")
    except: return [], int(entry["last_comment_id"])
    lid = int(entry["last_comment_id"]); new, mx = [], lid
    for c in comments:
        if c["id"] > lid: new.append(c)
        if c["id"] > mx: mx = c["id"]
    return new, mx

def make_icon():
    pix = QPixmap(32, 32)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QBrush(QColor(0, 180, 80)))
    p.setPen(QPen(Qt.GlobalColor.white, 2))
    p.drawEllipse(4, 4, 24, 24)
    p.setFont(QFont("Arial", 14, QFont.Weight.Bold))
    p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "M")
    p.end()
    return QIcon(pix)

class WatchWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MnemeNet Watch")
        self.setFixedSize(280, 120)
        self.setWindowIcon(make_icon())

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.status = QLabel("MnemeNet Watch\n启动中...")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setFont(QFont("Arial", 10))
        layout.addWidget(self.status)

        # System tray
        self.tray = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon(self)
            self.tray.setIcon(make_icon())
            self.tray.setToolTip("MnemeNet Watch")
            menu = QMenu()
            menu.addAction("Show").triggered.connect(self.show_window)
            menu.addAction("Exit").triggered.connect(self.real_quit)
            self.tray.setContextMenu(menu)
            self.tray.activated.connect(self.on_tray_click)
            self.tray.show()
            self.tray.showMessage("MnemeNet Watch", "Started - monitoring replies",
                                   QSystemTrayIcon.MessageIcon.Information, 3000)

        # Poll timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.poll)
        self.timer.start(INTERVAL * 1000)

        # Initial poll after 1 second
        QTimer.singleShot(1000, self.poll)
    def poll(self):
        try:
            fp = load_fp()
            if not fp:
                self.status.setText("等待首次评论记录...")
                return

            found = False
            for e in fp:
                new, mx = check_one(e)
                if new:
                    NOTIFY_DIR.mkdir(exist_ok=True)
                    body = new[-1]["body"]
                    target = f"#{e['issue']}"
                    first = body.strip().split("\n")[0].strip()
                    if first.startswith("@"): target = first.split(" ")[0]

                    ALERT.write_text(json.dumps({
                        "issue":e["issue"],"target":target,"body":body,
                        "time":new[-1]["created_at"],"url":new[-1]["html_url"]
                    },indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

                    self.status.setText(
                        f"新回复!\nIssue #{e['issue']} — {target}\n{datetime.now().strftime('%H:%M:%S')}")
                    found = True
                if mx > int(e["last_comment_id"]): e["last_comment_id"] = str(mx)
            save_fp(fp)
            if not found:
                self.status.setText(f"无新回复\n上次: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as ex:
            self.status.setText(f"错误: {ex}")

    def closeEvent(self, event):
        if self.tray:
            self.hide()
            event.ignore()
        else:
            self.real_quit()

    def show_window(self):
        self.show()
        self.activateWindow()

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_window()

    def real_quit(self):
        self.timer.stop()
        if self.tray: self.tray.hide()
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    win = WatchWindow()
    win.show()
    app.exec()
