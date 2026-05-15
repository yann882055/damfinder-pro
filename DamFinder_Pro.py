# -*- coding: utf-8 -*-
"""
DamFinder Pro v1.0 — Application Entry Point
===============================================
Splash screen → licence gate → main window.

DamFinder Pro v1.0
Developed by DAMFINDER Engineering Tools
Methodology : ICOLD standards + World Bank ESMAP hydropower guidelines
Hydroelectric potential specific method — profile analysis kW/40m
Calibrated on anonymized West African hydroelectric reference projects
© 2026 DAMFINDER Engineering Tools — All rights reserved
"""

import sys
import os

# PyInstaller: set base path for bundled resources
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Qt WebEngine must be initialised before QApplication on some systems
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu")

from PyQt5.QtWidgets import (
    QApplication, QSplashScreen, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QProgressBar, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import (QPixmap, QFont, QColor, QPainter, QLinearGradient,
                         QBrush, QPen)

import license_manager as lm


# ══════════════════════════════════════════════════════════════════════════════
# LOGO SVG (same as main_window.py, embedded as bytes for QPixmap)
# ══════════════════════════════════════════════════════════════════════════════
LOGO_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160">
  <defs>
    <radialGradient id="g" cx="50%" cy="40%" r="55%">
      <stop offset="0%" stop-color="#3a6fc4"/>
      <stop offset="100%" stop-color="#1a3a6c"/>
    </radialGradient>
  </defs>
  <circle cx="80" cy="72" r="64" fill="url(#g)"/>
  <g fill="white" opacity=".92">
    <path d="M80 28 Q96 44 80 60 Q64 44 80 28Z"/>
    <path d="M124 84 Q108 68 92 84 Q108 100 124 84Z"/>
    <path d="M36 84 Q52 68 68 84 Q52 100 36 84Z"/>
  </g>
  <circle cx="80" cy="72" r="14" fill="white"/>
  <path d="M76 58 L70 76 L80 76 L74 94 L90 68 L78 68 Z"
        fill="#f5a623" stroke="#e08000" stroke-width="1"/>
  <path d="M32 116 Q44 108 56 116 Q68 124 80 116 Q92 108 104 116 Q116 124 128 116"
        stroke="white" stroke-width="4" fill="none" opacity=".85"/>
  <path d="M40 130 Q52 122 64 130 Q76 138 88 130 Q100 122 112 130 Q120 136 128 130"
        stroke="white" stroke-width="3" fill="none" opacity=".6"/>
</svg>"""


def _logo_pixmap(w: int, h: int) -> QPixmap:
    """Render SVG logo to QPixmap."""
    pix = QPixmap(w, h)
    pix.fill(Qt.transparent)
    try:
        from PyQt5.QtSvg import QSvgRenderer
        from PyQt5.QtCore import QByteArray
        renderer = QSvgRenderer(QByteArray(LOGO_SVG))
        painter  = QPainter(pix)
        renderer.render(painter)
        painter.end()
    except Exception:
        # Fallback: plain circle
        painter = QPainter(pix)
        painter.setBrush(QBrush(QColor("#1a3a6c")))
        painter.drawEllipse(4, 4, w-8, h-8)
        painter.end()
    return pix


# ══════════════════════════════════════════════════════════════════════════════
# SPLASH SCREEN  (3 seconds, animated progress bar)
# ══════════════════════════════════════════════════════════════════════════════

class SplashScreen(QSplashScreen):

    def __init__(self):
        # Build a 560×340 pixmap
        pix = QPixmap(560, 340)
        pix.fill(Qt.transparent)

        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)

        # Background gradient
        grad = QLinearGradient(0, 0, 0, 340)
        grad.setColorAt(0.0, QColor("#1a3a6c"))
        grad.setColorAt(1.0, QColor("#0d1f3c"))
        p.fillRect(0, 0, 560, 340, grad)

        # Subtle border
        p.setPen(QPen(QColor("#2980b9"), 3))
        p.drawRoundedRect(2, 2, 556, 336, 14, 14)

        p.end()

        super().__init__(pix, Qt.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.FramelessWindowHint)

        # ── Build overlay widgets ──────────────────────────────────────────────
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(10)

        # Logo + title row
        top_row = QHBoxLayout()
        top_row.setSpacing(18)
        logo_lbl = QLabel()
        logo_lbl.setPixmap(_logo_pixmap(90, 90))
        logo_lbl.setFixedSize(90, 90)
        top_row.addWidget(logo_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        app_lbl = QLabel("DamFinder Pro")
        app_lbl.setFont(QFont("Arial", 26, QFont.Bold))
        app_lbl.setStyleSheet("color:white;")
        ver_lbl = QLabel("v1.0")
        ver_lbl.setFont(QFont("Arial", 16))
        ver_lbl.setStyleSheet("color:#aed6f1;")
        title_col.addWidget(app_lbl)
        title_col.addWidget(ver_lbl)
        top_row.addLayout(title_col)
        top_row.addStretch()
        layout.addLayout(top_row)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("border:1px solid #2980b9;")
        layout.addWidget(sep)

        # Developer label
        dev_lbl = QLabel("DAMFINDER Engineering Tools")
        dev_lbl.setFont(QFont("Arial", 13, QFont.Bold))
        dev_lbl.setStyleSheet("color:#85c1e9;")
        dev_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(dev_lbl)

        # Methodology
        meth_lbl = QLabel(
            "Methodology: ICOLD standards + World Bank ESMAP hydropower guidelines\n"
            "Specific potential method — longitudinal profile analysis kW/40m\n"
            "Calibrated on anonymized West African reference projects"
        )
        meth_lbl.setFont(QFont("Arial", 10))
        meth_lbl.setStyleSheet("color:#aed6f1;")
        meth_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(meth_lbl)

        layout.addSpacing(8)

        # Loading label
        self._load_lbl = QLabel("Initialising…")
        self._load_lbl.setFont(QFont("Arial", 10))
        self._load_lbl.setStyleSheet("color:#85c1e9;")
        self._load_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._load_lbl)

        # Progress bar
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(8)
        self._bar.setStyleSheet(
            "QProgressBar{border-radius:4px;background:#0d1f3c;}"
            "QProgressBar::chunk{background:#2980b9;border-radius:4px;}"
        )
        layout.addWidget(self._bar)

        # Copyright
        copy_lbl = QLabel("© 2026 DAMFINDER Engineering Tools — All rights reserved")
        copy_lbl.setFont(QFont("Arial", 9))
        copy_lbl.setStyleSheet("color:#5d8aa8;")
        copy_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(copy_lbl)

        # Embed layout into a container widget painted over the pixmap
        container = QWidget(self)
        container.setGeometry(0, 0, 560, 340)
        container.setStyleSheet("background:transparent;")
        container.setLayout(layout)

        # Animate progress over 3 s
        self._progress = 0
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)   # ~33 fps

        self._messages = [
            (20,  "Loading hydrological engine…"),
            (45,  "Initialising geospatial libraries…"),
            (70,  "Preparing analysis modules…"),
            (90,  "Loading user interface…"),
            (100, "Ready."),
        ]
        self._msg_idx = 0

    def _tick(self):
        self._progress += 1
        self._bar.setValue(self._progress)

        # Update message
        if (self._msg_idx < len(self._messages) and
                self._progress >= self._messages[self._msg_idx][0]):
            self._load_lbl.setText(self._messages[self._msg_idx][1])
            self._msg_idx += 1

        if self._progress >= 100:
            self._timer.stop()

    def advance(self, val: int, msg: str = ""):
        self._bar.setValue(val)
        if msg:
            self._load_lbl.setText(msg)
        QApplication.processEvents()


# ══════════════════════════════════════════════════════════════════════════════
# LICENCE ACTIVATION DIALOG
# ══════════════════════════════════════════════════════════════════════════════

class LicenceDialog(QDialog):

    def __init__(self, message: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("DamFinder Pro v1.0 — Licence Activation")
        self.setMinimumWidth(480)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(28, 28, 28, 28)

        # Logo + title
        hdr = QHBoxLayout()
        logo = QLabel(); logo.setPixmap(_logo_pixmap(60, 60)); logo.setFixedSize(60, 60)
        hdr.addWidget(logo)
        tv = QVBoxLayout()
        tv.addWidget(QLabel(
            '<span style="font-size:18px;font-weight:bold;color:#1a3a6c;">'
            'DamFinder Pro v1.0</span>'))
        tv.addWidget(QLabel(
            '<span style="color:#5d6d7e;">DAMFINDER Engineering Tools</span>'))
        hdr.addLayout(tv); hdr.addStretch()
        layout.addLayout(hdr)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("border:1px solid #bdc3c7;"); layout.addWidget(sep)

        # Status message (if expired / corrupt)
        if message:
            msg_lbl = QLabel(message)
            msg_lbl.setWordWrap(True)
            msg_lbl.setStyleSheet(
                "color:#c0392b;background:#fdecea;border-radius:5px;"
                "padding:8px;font-size:12px;")
            layout.addWidget(msg_lbl)

        layout.addWidget(QLabel(
            "Please enter your licence key to activate DamFinder Pro.\n"
            "Format:  BODY|YYYY-MM-DD|HASH16"))

        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("XXXX-XXXX-XXXX-XXXX|2027-12-31|abcdef0123456789")
        self.key_edit.setFont(QFont("Consolas", 11))
        self.key_edit.setMinimumHeight(36)
        layout.addWidget(self.key_edit)

        self.status_lbl = QLabel("")
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setStyleSheet("font-size:12px;")
        layout.addWidget(self.status_lbl)

        # Buttons
        btn_row = QHBoxLayout()
        self.btn_activate = QPushButton("Activate")
        self.btn_activate.setStyleSheet(
            "QPushButton{background:#2471a3;color:white;border-radius:5px;"
            "padding:8px 22px;font-weight:bold;}"
            "QPushButton:hover{background:#1a5276;}")
        self.btn_activate.clicked.connect(self._activate)

        btn_cancel = QPushButton("Exit")
        btn_cancel.setStyleSheet(
            "QPushButton{background:#95a5a6;color:white;border-radius:5px;"
            "padding:8px 18px;}"
            "QPushButton:hover{background:#7f8c8d;}")
        btn_cancel.clicked.connect(self._on_cancel)

        btn_row.addStretch()
        btn_row.addWidget(self.btn_activate)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

        layout.addWidget(QLabel(
            '<span style="color:#7f8c8d;font-size:10px;">'
            '© 2026 DAMFINDER Engineering Tools — All rights reserved</span>'))

        self._activated = False

    def _activate(self):
        key = self.key_edit.text().strip()
        if not key:
            self.status_lbl.setText("Please enter a licence key.")
            self.status_lbl.setStyleSheet("color:#c0392b;font-size:12px;")
            return

        result = lm.activate(key)
        if result.valid:
            self.status_lbl.setText(f"✓  {result.message}")
            self.status_lbl.setStyleSheet("color:#27ae60;font-size:12px;font-weight:bold;")
            self._activated = True
            QTimer.singleShot(1200, self.accept)
        else:
            self.status_lbl.setText(f"✗  {result.message}")
            self.status_lbl.setStyleSheet("color:#c0392b;font-size:12px;")

    def _on_cancel(self):
        self.reject()

    @property
    def activated(self) -> bool:
        return self._activated


# ══════════════════════════════════════════════════════════════════════════════
# EXPIRED / RENEWAL NOTICE DIALOG
# ══════════════════════════════════════════════════════════════════════════════

class RenewalDialog(QDialog):
    """Shown when a licence is expired. Allows re-activation or trial exit."""

    def __init__(self, expiry_str: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DamFinder Pro — Licence Expired")
        self.setMinimumWidth(440)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        logo = QLabel(); logo.setPixmap(_logo_pixmap(56, 56))
        logo.setAlignment(Qt.AlignCenter); layout.addWidget(logo)

        lbl = QLabel(
            f"<b>Your DamFinder Pro licence expired on {expiry_str}.</b><br><br>"
            "Analysis is blocked. Please renew your licence to continue.")
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size:13px;color:#c0392b;")
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("border:1px solid #ddd;"); layout.addWidget(sep)

        layout.addWidget(QLabel("Enter renewal key:"))
        self.key_edit = QLineEdit()
        self.key_edit.setFont(QFont("Consolas", 11))
        self.key_edit.setMinimumHeight(34)
        layout.addWidget(self.key_edit)

        self.status_lbl = QLabel("")
        self.status_lbl.setWordWrap(True)
        layout.addWidget(self.status_lbl)

        btn_row = QHBoxLayout()
        btn_renew = QPushButton("Renew Licence")
        btn_renew.setStyleSheet(
            "QPushButton{background:#2471a3;color:white;border-radius:5px;"
            "padding:8px 20px;font-weight:bold;}"
            "QPushButton:hover{background:#1a5276;}")
        btn_renew.clicked.connect(self._renew)

        btn_exit = QPushButton("Exit Application")
        btn_exit.setStyleSheet(
            "QPushButton{background:#e74c3c;color:white;border-radius:5px;"
            "padding:8px 16px;}"
            "QPushButton:hover{background:#c0392b;}")
        btn_exit.clicked.connect(self._exit_app)

        btn_row.addWidget(btn_renew); btn_row.addWidget(btn_exit)
        layout.addLayout(btn_row)

        self._renewed = False

    def _renew(self):
        result = lm.activate(self.key_edit.text().strip())
        if result.valid:
            self.status_lbl.setText(f"✓  {result.message}")
            self.status_lbl.setStyleSheet("color:#27ae60;font-weight:bold;")
            self._renewed = True
            QTimer.singleShot(1200, self.accept)
        else:
            self.status_lbl.setText(f"✗  {result.message}")
            self.status_lbl.setStyleSheet("color:#c0392b;")

    def _exit_app(self):
        sys.exit(0)

    @property
    def renewed(self) -> bool:
        return self._renewed


# ══════════════════════════════════════════════════════════════════════════════
# APPLICATION BOOTSTRAP
# ══════════════════════════════════════════════════════════════════════════════

def main():
    # Enable High-DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps,    True)

    app = QApplication(sys.argv)
    app.setApplicationName("DamFinder Pro")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("DAMFINDER Engineering Tools")

    # Global stylesheet
    app.setStyleSheet(f"""
        QWidget      {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; }}
        QMainWindow  {{ background: #f0f4f8; }}
        QGroupBox    {{ font-size: 12px; }}
        QScrollArea  {{ border: none; }}
        QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {{
            border: 1px solid #bdc3c7; border-radius: 4px;
            padding: 3px 6px; background: white; min-height: 24px;
        }}
        QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {{
            border: 1px solid #2980b9;
        }}
    """)

    # ── Splash screen ─────────────────────────────────────────────────────────
    splash = SplashScreen()
    splash.show()
    app.processEvents()

    # Advance splash while importing heavy modules
    splash.advance(15, "Loading raster libraries…")
    try:
        import rasterio          # noqa: F401
    except ImportError:
        pass

    splash.advance(35, "Loading geopandas…")
    try:
        import geopandas         # noqa: F401
    except ImportError:
        pass

    splash.advance(55, "Loading pysheds…")
    try:
        from pysheds.grid import Grid   # noqa: F401
    except ImportError:
        pass

    splash.advance(75, "Loading matplotlib…")
    try:
        import matplotlib        # noqa: F401
    except ImportError:
        pass

    splash.advance(90, "Checking licence…")
    app.processEvents()

    # Wait until splash completes its 3 s animation (~100 ticks × 30 ms)
    import time
    start = time.time()
    while time.time() - start < 3.0:
        app.processEvents()
        time.sleep(0.01)

    splash.advance(100, "Ready.")
    app.processEvents()

    # ── Licence check ─────────────────────────────────────────────────────────
    lic = lm.check()

    if not lic.valid:
        splash.hide()

        if lic.expiry is not None:
            # Licence exists but expired → Renewal dialog
            dlg = RenewalDialog(lic.expiry_str)
            if dlg.exec_() != QDialog.Accepted or not dlg.renewed:
                sys.exit(0)
            lic = lm.check()
        else:
            # No licence → Activation dialog
            dlg = LicenceDialog(lic.message)
            if dlg.exec_() != QDialog.Accepted or not dlg.activated:
                sys.exit(0)
            lic = lm.check()

        if not lic.valid:
            QMessageBox.critical(None, "Licence Error",
                                 f"Licence could not be validated.\n{lic.message}")
            sys.exit(1)

    # ── Warn if expiry near ───────────────────────────────────────────────────
    if lic.days_remaining <= 30:
        splash.hide()
        QMessageBox.warning(
            None, "Licence Expiring Soon",
            f"Your DamFinder Pro licence expires in <b>{lic.days_remaining}</b> day(s) "
            f"({lic.expiry_str}).<br>Please renew to avoid interruption.")

    splash.close()

    # ── Main window ───────────────────────────────────────────────────────────
    from main_window import MainWindow
    win = MainWindow(licence_expiry=lic.expiry_str)
    win.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
