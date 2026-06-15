"""MnemeNet Watch — one-file daemon: poll + notify + tray.

Reuses Huh's proven pattern: QMainWindow → QSystemTrayIcon(parent).
Background thread polls GitHub API every 5 min.
New comment detected → writes alert.json, prints notification.
Green circle "M" tray icon. Right-click → Exit.
No pip deps beyond PyQt6 + gh CLI.

Usage: pythonw scripts/mnemenet-watch.pyw
"""

import json, os, subprocess, sys, threading, time
from datetime import datetime
from pathlib import Path

try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu
    from PyQt6.QtGui import QIcon, QPixmap, QPainter, QBrush, QPen, QColor, QFont
    from PyQt6.QtCore import Qt
except ImportError:
    print("PyQt6 not installed. Run: pip install PyQt6")
    sys.exit(1)

REPO = "Offblink/MnemeNet"
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
FOOTPRINT = PROJECT_DIR / "comment-footprint.json"
NOTIFY_DIR = PROJECT_DIR / "notifications"
ALERT = NOTIFY_DIR / "alert.json"
INTERVAL = 300

# ---- GitHub helpers ----
def gh(endpoint):
    r = subprocess.run(
        ["gh","api",f"repos/{REPO}{endpoint}"],
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

def do_notify(entry, comment):
    NOTIFY_DIR.mkdir(exist_ok=True)
    body = comment["body"]

    # Try to extract @ target from first line
    target = f"#{entry['issue']}"
    first_line = body.strip().split("\n")[0].strip()
    if first_line.startswith("@"):
        target = first_line.split(" ")[0]  # @Crush, @omp etc

    ALERT.write_text(json.dumps({
        "issue":entry["issue"],"target":target,
        "from_user":comment["user"]["login"],"body":body,
        "time":comment["created_at"],"url":comment["html_url"]
    },indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

    print(f"\n  MnemeNet: New reply from Issue #{entry['issue']}")
    print(f"  {comment['html_url']}")
    return target

def once():
    fp = load_fp()
    if not fp:
        try:
            r = subprocess.run(
                ["gh","issue","list","-R",REPO,"-l","insight","--author","@me",
                 "--limit","1","--json","number","-q",".[0].number"],
                capture_output=True,text=True,timeout=10,encoding="utf-8")
            own = int(r.stdout.strip()) if r.stdout.strip() else None
            if own: fp=[{"issue":own,"agent":"self","last_comment_id":"0"}]; save_fp(fp)
        except: pass
    found=False
    for e in fp:
        new,mx=check_one(e)
        if new:
            for c in new: do_notify(e,c)
            found=True
        if mx>int(e["last_comment_id"]): e["last_comment_id"]=str(mx)
    save_fp(fp)
    if not found: print(f"[{datetime.now().strftime('%H:%M')}] No new replies")
    return found

# ---- Tray App (QMainWindow parent, following Huh's pattern) ----
running = True

class WatchWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MnemeNet Watch")
        self.setFixedSize(1, 1)  # invisible

        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon(self)
            self.tray.setIcon(self.make_icon())
            self.tray.setToolTip("MnemeNet Watch")

            menu = QMenu()
            menu.addAction("Exit").triggered.connect(self.quit)
            self.tray.setContextMenu(menu)
            self.tray.show()
        else:
            print("System tray not available — polling in console")
            threading.Thread(target=_watch_thread, daemon=True).start()

    def make_icon(self):
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

    def quit(self):
        global running
        running = False
        self.tray.hide()
        QApplication.quit()

def _watch_thread():
    global running
    while running:
        try: once()
        except: pass
        for _ in range(INTERVAL):
            if not running: break
            time.sleep(1)

if __name__=="__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    win = WatchWindow()
    if QSystemTrayIcon.isSystemTrayAvailable():
        threading.Thread(target=_watch_thread, daemon=True).start()
    app.exec()
