"""MnemeNet Watch — GUI + system tray polling daemon.

Window shows live status. Close -> minimize to tray (green M). Right-click -> Exit.
Single-instance: second launch exits immediately.

scripts/mnemenet-watch.pyw
"""
import json, os, subprocess, sys
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
NO_WIN = 0x08000000  # CREATE_NO_WINDOW

def gh(endpoint):
    r = subprocess.run(["gh","api",f"repos/{REPO}{endpoint}"],
        capture_output=True,text=True,timeout=15,encoding="utf-8",
        creationflags=NO_WIN)
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
    p = QPainter(pix); p.setRenderHint(QPainter.RenderHint.Antialiasing)
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

        c = QWidget(); self.setCentralWidget(c)
        l = QVBoxLayout(c)
        self.status = QLabel("MnemeNet Watch\nStarting...")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setFont(QFont("Arial", 10))
        l.addWidget(self.status)

        self.tray = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon(self)
            self.tray.setIcon(make_icon())
            self.tray.setToolTip("MnemeNet Watch")
            m = QMenu()
            m.addAction("Show").triggered.connect(self.show_window)
            m.addAction("Exit").triggered.connect(self.real_quit)
            self.tray.setContextMenu(m)
            self.tray.activated.connect(self.on_tray)
            self.tray.show()
            self.tray.showMessage("MnemeNet Watch", "Started",
                                   QSystemTrayIcon.MessageIcon.Information, 3000)

        self.timer = QTimer()
        self.timer.timeout.connect(self.poll)
        self.timer.start(INTERVAL * 1000)
        QTimer.singleShot(1000, self.poll)

    def poll(self):
        try:
            fp = load_fp()
            if not fp:
                try:
                    r = subprocess.run(
                        ["gh","issue","list","-R",REPO,"-l","insight","--author","@me",
                         "--limit","1","--json","number","-q",".[0].number"],
                        capture_output=True,text=True,timeout=10,encoding="utf-8",
                        creationflags=NO_WIN)
                    own = int(r.stdout.strip()) if r.stdout.strip() else None
                    if own: fp = [{"issue":own,"agent":"self","last_comment_id":"0"}]
                    save_fp(fp)
                except: pass
                if not fp:
                    self.status.setText("No footprint yet.\nWaiting for first comment...")
                    return

            found = False
            for e in fp:
                new, mx = check_one(e)
                if new:
                    NOTIFY_DIR.mkdir(exist_ok=True)
                    for c in new:
                        body = c["body"]
                        target = f"#{e['issue']}"
                        first = body.strip().split("\n")[0].strip()
                        if first.startswith("@"): target = first.split(" ")[0]

                        ALERT.write_text(json.dumps({
                            "issue":e["issue"],"target":target,"body":body,
                            "time":c["created_at"],"url":c["html_url"]
                        },indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

                        # Auto-reply: own Issue -> responsibility
                        is_own = (e.get("agent","") == "self" or
                                  e.get("agent","") == "omp")
                        if is_own:
                            reply = f"{target} —— MnemeNet Watch 自动回复：已收到。
Agent 下次轮询时会认真回复。

—— omp"
                            try:
                                subprocess.run(
                                    ["gh","issue","comment",str(e["issue"]),
                                     "-R",REPO,"-b",reply],
                                    capture_output=True,text=True,
                                    timeout=15,encoding="utf-8",
                                    creationflags=NO_WIN)
                                c["id"] = str(c["id"])  # mark replied
                            except: pass

                    self.status.setText(
                        f"NEW + REPLIED!\nIssue #{e['issue']} - {target}\n{datetime.now().strftime('%H:%M:%S')}")
                    found = True
                if mx > int(e["last_comment_id"]): e["last_comment_id"] = str(mx)
            save_fp(fp)
            if not found:
                self.status.setText(f"No new replies\nLast: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as ex:
            self.status.setText(f"Error: {ex}")

    def show_window(self): self.show(); self.activateWindow()
    def on_tray(self, r):
        if r == QSystemTrayIcon.ActivationReason.Trigger: self.show_window()
    def real_quit(self):
        self.timer.stop()
        if self.tray: self.tray.hide()
        QApplication.quit()

if __name__ == "__main__":
    # Single-instance via named mutex (ctypes only, no pywin32)
    from ctypes import windll, byref, c_bool
    k32 = windll.kernel32
    mutex = k32.CreateMutexW(None, c_bool(False), "MnemeNetWatchSingleInstance")
    if k32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    w = WatchWindow()
    w.show()
    app.exec()
