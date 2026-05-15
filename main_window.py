# -*- coding: utf-8 -*-
"""
DamFinder Pro v1.0 — Main Window
==================================
PyQt5 GUI: left params panel, right Folium map, bottom results table.

© 2026 DAMFINDER Engineering Tools — All rights reserved
"""

import os, sys, json, traceback
from datetime import date
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QFileDialog, QProgressBar, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QTabWidget, QScrollArea, QGroupBox,
    QSizePolicy, QSplitter, QMessageBox, QStatusBar, QToolButton,
    QApplication, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl
from PyQt5.QtGui import QFont, QColor, QIcon, QPalette, QPixmap
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings

from engine import run_analysis, APP_CREDIT

# ── Embedded DamFinder logo (SVG, no external file needed) ────────────────────
LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80">
  <defs>
    <radialGradient id="g" cx="50%" cy="40%" r="55%">
      <stop offset="0%" stop-color="#3a6fc4"/>
      <stop offset="100%" stop-color="#1a3a6c"/>
    </radialGradient>
  </defs>
  <circle cx="40" cy="36" r="32" fill="url(#g)"/>
  <!-- turbine blades -->
  <g stroke="white" stroke-width="2.5" fill="none">
    <path d="M40 14 Q48 22 40 30 Q32 22 40 14Z" fill="white" opacity=".9"/>
    <path d="M62 42 Q54 34 46 42 Q54 50 62 42Z" fill="white" opacity=".9"/>
    <path d="M18 42 Q26 34 34 42 Q26 50 18 42Z" fill="white" opacity=".9"/>
  </g>
  <circle cx="40" cy="36" r="7" fill="white"/>
  <!-- lightning bolt -->
  <path d="M38 29 L35 38 L40 38 L37 47 L45 34 L39 34 Z"
        fill="#f5a623" stroke="#e08000" stroke-width=".5"/>
  <!-- water waves -->
  <path d="M16 58 Q22 54 28 58 Q34 62 40 58 Q46 54 52 58 Q58 62 64 58"
        stroke="white" stroke-width="2" fill="none" opacity=".85"/>
  <path d="M20 65 Q26 61 32 65 Q38 69 44 65 Q50 61 56 65 Q60 68 64 65"
        stroke="white" stroke-width="1.5" fill="none" opacity=".6"/>
</svg>"""


# ── Colour palette ─────────────────────────────────────────────────────────────
C_PRIMARY   = "#1a3a6c"
C_ACCENT    = "#2980b9"
C_BUTTON    = "#2471a3"
C_BUTTON_HV = "#1a5276"
C_SUCCESS   = "#27ae60"
C_WARNING   = "#e67e22"
C_ERROR     = "#c0392b"
C_BG        = "#f0f4f8"
C_PANEL     = "#ffffff"


def _btn_style(bg=C_BUTTON, hover=C_BUTTON_HV, text="white", radius=6, pad="8px 18px"):
    return (f"QPushButton{{background:{bg};color:{text};border-radius:{radius}px;"
            f"padding:{pad};font-weight:bold;font-size:13px;}}"
            f"QPushButton:hover{{background:{hover};}}"
            f"QPushButton:disabled{{background:#95a5a6;color:#ecf0f1;}}")


# ═══════════════════════════════════════════════════════════════════════════════
# WORKER THREAD
# ═══════════════════════════════════════════════════════════════════════════════

class AnalysisWorker(QThread):
    progress  = pyqtSignal(int, str, str)   # percent, message, level
    finished  = pyqtSignal(dict)
    error     = pyqtSignal(str)

    def __init__(self, params: dict):
        super().__init__()
        self.params = params

    def run(self):
        def cb(pct, msg, lvl='info'):
            self.progress.emit(pct, msg, lvl)

        try:
            result = run_analysis(self.params, cb)
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(traceback.format_exc())


# ═══════════════════════════════════════════════════════════════════════════════
# PARAM PANEL (left)
# ═══════════════════════════════════════════════════════════════════════════════

class ParamsPanel(QScrollArea):
    """Left panel containing all input parameters."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setMinimumWidth(340)
        self.setMaximumWidth(400)

        container = QWidget()
        self.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)

        def _group(title):
            gb = QGroupBox(title)
            gb.setStyleSheet(
                "QGroupBox{font-weight:bold;color:#1a3a6c;border:1px solid #bdc3c7;"
                "border-radius:6px;margin-top:8px;padding-top:6px;}"
                "QGroupBox::title{subcontrol-origin:margin;left:10px;padding:0 4px;}"
            )
            vl = QVBoxLayout(gb)
            vl.setSpacing(4)
            return gb, vl

        def _row(label_txt, widget, layout):
            h = QHBoxLayout()
            lbl = QLabel(label_txt)
            lbl.setMinimumWidth(130)
            lbl.setWordWrap(True)
            h.addWidget(lbl)
            h.addWidget(widget)
            layout.addLayout(h)

        # ── 1. Input Data ─────────────────────────────────────────────────────
        gb1, vl1 = _group("1. Input Data")

        self.dem_edit = QLineEdit()
        self.dem_edit.setPlaceholderText("Select DEM (.tif/.img/.hgt)…")
        btn_dem = QToolButton(); btn_dem.setText("…")
        btn_dem.clicked.connect(self._browse_dem)
        row_dem = QHBoxLayout()
        row_dem.addWidget(self.dem_edit)
        row_dem.addWidget(btn_dem)
        vl1.addWidget(QLabel("DEM file:"))
        vl1.addLayout(row_dem)

        self.river_edit = QLineEdit()
        self.river_edit.setPlaceholderText("Optional river .shp")
        btn_riv = QToolButton(); btn_riv.setText("…")
        btn_riv.clicked.connect(self._browse_river)
        row_riv = QHBoxLayout()
        row_riv.addWidget(self.river_edit)
        row_riv.addWidget(btn_riv)
        vl1.addWidget(QLabel("River network (optional):"))
        vl1.addLayout(row_riv)

        self.sa_edit = QLineEdit()
        self.sa_edit.setPlaceholderText("Optional study area .shp")
        btn_sa = QToolButton(); btn_sa.setText("…")
        btn_sa.clicked.connect(self._browse_sa)
        row_sa = QHBoxLayout()
        row_sa.addWidget(self.sa_edit)
        row_sa.addWidget(btn_sa)
        vl1.addWidget(QLabel("Study area (optional):"))
        vl1.addLayout(row_sa)

        self.out_edit = QLineEdit()
        self.out_edit.setPlaceholderText("Output folder…")
        btn_out = QToolButton(); btn_out.setText("…")
        btn_out.clicked.connect(self._browse_output)
        row_out = QHBoxLayout()
        row_out.addWidget(self.out_edit)
        row_out.addWidget(btn_out)
        vl1.addWidget(QLabel("Output folder:"))
        vl1.addLayout(row_out)

        layout.addWidget(gb1)

        # ── 2. Stream Network ─────────────────────────────────────────────────
        gb2, vl2 = _group("2. Stream Network")

        self.gen_network_cb = QCheckBox("Auto-generate network from DEM")
        self.gen_network_cb.setChecked(True)
        vl2.addWidget(self.gen_network_cb)

        self.flow_thr_spin = QSpinBox()
        self.flow_thr_spin.setRange(0, 999999)
        self.flow_thr_spin.setValue(0)
        self.flow_thr_spin.setSpecialValueText("0 = auto")
        _row("Flow accumulation threshold:", self.flow_thr_spin, vl2)

        self.str_main_spin = QSpinBox()
        self.str_main_spin.setRange(3, 10); self.str_main_spin.setValue(6)
        _row("Strahler — main course:", self.str_main_spin, vl2)

        self.str_major_spin = QSpinBox()
        self.str_major_spin.setRange(3, 10); self.str_major_spin.setValue(5)
        _row("Strahler — major tribs:", self.str_major_spin, vl2)

        self.str_sec_spin = QSpinBox()
        self.str_sec_spin.setRange(3, 10); self.str_sec_spin.setValue(4)
        _row("Strahler — secondary tribs:", self.str_sec_spin, vl2)

        layout.addWidget(gb2)

        # ── 3. Profile Extraction ─────────────────────────────────────────────
        gb3, vl3 = _group("3. Profile Extraction")

        self.profile_step_cb = QComboBox()
        self.profile_step_cb.addItems(["20", "40", "50", "100"])
        self.profile_step_cb.setCurrentText("40")
        _row("Profile step (m):", self.profile_step_cb, vl3)

        layout.addWidget(gb3)

        # ── 4. Hydrology ──────────────────────────────────────────────────────
        gb4, vl4 = _group("4. Hydrology")

        self.flow_src_cb = QComboBox()
        self.flow_src_cb.addItems(["Débits fixes", "HEC-HMS (Pjmax)", "Empirique"])
        self.flow_src_cb.currentTextChanged.connect(self._toggle_flow_params)
        _row("Flow source:", self.flow_src_cb, vl4)

        self.equip_coef_spin = QDoubleSpinBox()
        self.equip_coef_spin.setRange(1.0, 2.0)
        self.equip_coef_spin.setSingleStep(0.1)
        self.equip_coef_spin.setValue(1.4)
        _row("Equipment coeff:", self.equip_coef_spin, vl4)

        # Fixed flows
        self.ff_main_spin  = QDoubleSpinBox(); self.ff_main_spin.setRange(0,99999); self.ff_main_spin.setValue(80)
        self.ff_major_spin = QDoubleSpinBox(); self.ff_major_spin.setRange(0,99999); self.ff_major_spin.setValue(30)
        self.ff_sec_spin   = QDoubleSpinBox(); self.ff_sec_spin.setRange(0,99999);  self.ff_sec_spin.setValue(15)
        self.up_ratio_spin = QDoubleSpinBox(); self.up_ratio_spin.setRange(10,60);  self.up_ratio_spin.setValue(30)

        _row("Q main course (m³/s):",   self.ff_main_spin,  vl4)
        _row("Q major tribs (m³/s):",   self.ff_major_spin, vl4)
        _row("Q secondary (m³/s):",     self.ff_sec_spin,   vl4)
        _row("Upstream ratio (%):",     self.up_ratio_spin, vl4)

        # HEC-HMS
        self.pjmax_spin = QDoubleSpinBox(); self.pjmax_spin.setRange(50,300); self.pjmax_spin.setValue(100)
        self.cn_spin    = QDoubleSpinBox(); self.cn_spin.setRange(40,98);     self.cn_spin.setValue(75)
        self.rc_spin    = QDoubleSpinBox(); self.rc_spin.setRange(20,80);     self.rc_spin.setValue(45)
        self.rd_spin    = QSpinBox();       self.rd_spin.setRange(60,250);    self.rd_spin.setValue(120)
        self.tc_cb      = QComboBox();      self.tc_cb.addItems(["Kirpich", "Giandotti", "Passini"])

        _row("Pjmax (mm):",      self.pjmax_spin, vl4)
        _row("Curve Number:",    self.cn_spin,    vl4)
        _row("Runoff coeff (%):",self.rc_spin,    vl4)
        _row("Rainy days/yr:",   self.rd_spin,    vl4)
        _row("Tc method:",       self.tc_cb,      vl4)

        self.lf_spin = QDoubleSpinBox(); self.lf_spin.setRange(0,100); self.lf_spin.setValue(0)
        self.lf_spin.setSpecialValueText("0 = auto")
        _row("Load factor (%):", self.lf_spin, vl4)

        layout.addWidget(gb4)

        # ── 5. Site Detection ─────────────────────────────────────────────────
        gb5, vl5 = _group("5. Site Detection")

        self.seg_norm_cb = QComboBox(); self.seg_norm_cb.addItems(["20","40","50","100"]); self.seg_norm_cb.setCurrentText("40")
        _row("Segment normalisation (m):", self.seg_norm_cb, vl5)

        self.adap_thr_cb = QCheckBox("Adaptive threshold (recommended)")
        self.adap_thr_cb.setChecked(True)
        self.adap_thr_cb.toggled.connect(self._toggle_threshold)
        vl5.addWidget(self.adap_thr_cb)

        self.thr_peak_spin = QDoubleSpinBox(); self.thr_peak_spin.setRange(10,500); self.thr_peak_spin.setValue(50); self.thr_peak_spin.setEnabled(False)
        _row("Peak threshold (kW/40m):", self.thr_peak_spin, vl5)

        self.min_pow_cb = QComboBox(); self.min_pow_cb.addItems(["100","200","500","1000","2000","5000","10000"]); self.min_pow_cb.setCurrentText("500")
        _row("Min power (kW):", self.min_pow_cb, vl5)

        self.min_sp_cb = QComboBox(); self.min_sp_cb.addItems(["200","500","1000","2000"]); self.min_sp_cb.setCurrentText("500")
        _row("Min site spacing (m):", self.min_sp_cb, vl5)

        self.max_expl_spin = QDoubleSpinBox(); self.max_expl_spin.setRange(0,50000); self.max_expl_spin.setValue(0); self.max_expl_spin.setSpecialValueText("0 = 10km auto")
        _row("Max exploit dist (m):", self.max_expl_spin, vl5)

        self.weir_h_spin = QDoubleSpinBox(); self.weir_h_spin.setRange(2,10); self.weir_h_spin.setValue(5)
        _row("Weir height (m):", self.weir_h_spin, vl5)

        layout.addWidget(gb5)

        # ── 6. Manning Hydraulics ─────────────────────────────────────────────
        gb6, vl6 = _group("6. Manning Hydraulics")

        self.manning_n_spin = QDoubleSpinBox(); self.manning_n_spin.setRange(0.015,0.060); self.manning_n_spin.setSingleStep(0.005); self.manning_n_spin.setValue(0.035)
        _row("Manning n:", self.manning_n_spin, vl6)

        self.canal_l_spin = QDoubleSpinBox(); self.canal_l_spin.setRange(0,50000); self.canal_l_spin.setValue(1500)
        _row("Canal length (m):", self.canal_l_spin, vl6)

        self.hl_spin = QDoubleSpinBox(); self.hl_spin.setRange(3,15); self.hl_spin.setValue(6)
        _row("Head losses (%):", self.hl_spin, vl6)

        self.ss_spin = QDoubleSpinBox(); self.ss_spin.setRange(1,3); self.ss_spin.setSingleStep(0.1); self.ss_spin.setValue(1.5)
        _row("Canal side slope:", self.ss_spin, vl6)

        self.te_spin = QDoubleSpinBox(); self.te_spin.setRange(75,95); self.te_spin.setValue(90)
        _row("Turbine efficiency (%):", self.te_spin, vl6)

        layout.addWidget(gb6)

        # ── 7. Cascade ────────────────────────────────────────────────────────
        gb7, vl7 = _group("7. Cascade Analysis")
        self.cascade_cb = QCheckBox("Enable cascade analysis")
        self.cascade_cb.setChecked(True)
        vl7.addWidget(self.cascade_cb)
        self.casc_dist_spin = QDoubleSpinBox(); self.casc_dist_spin.setRange(1000,200000); self.casc_dist_spin.setValue(50000)
        _row("Influence dist (m):", self.casc_dist_spin, vl7)
        layout.addWidget(gb7)

        # ── 8. Economics ──────────────────────────────────────────────────────
        gb8, vl8 = _group("8. Economics (LCOE)")
        self.disc_spin = QDoubleSpinBox(); self.disc_spin.setRange(3,15); self.disc_spin.setValue(8)
        _row("Discount rate (%):", self.disc_spin, vl8)
        self.dur_spin  = QSpinBox(); self.dur_spin.setRange(20,50); self.dur_spin.setValue(30)
        _row("Project duration (yr):", self.dur_spin, vl8)
        self.xof_spin  = QDoubleSpinBox(); self.xof_spin.setRange(100,1000); self.xof_spin.setDecimals(3); self.xof_spin.setValue(655.957)
        _row("EUR/XOF rate:", self.xof_spin, vl8)
        self.conn_cb = QCheckBox("Include grid connection cost")
        self.conn_cb.setChecked(True)
        vl8.addWidget(self.conn_cb)
        layout.addWidget(gb8)

        # ── 9. Exports ────────────────────────────────────────────────────────
        gb9, vl9 = _group("9. Exports")
        self.gen_plots_cb = QCheckBox("Generate profile plots")
        self.gen_plots_cb.setChecked(True)
        vl9.addWidget(self.gen_plots_cb)
        self.plot_fmt_cb = QComboBox(); self.plot_fmt_cb.addItems(["PNG","PDF","SVG"])
        _row("Plot format:", self.plot_fmt_cb, vl9)
        self.plot_dpi_cb = QComboBox(); self.plot_dpi_cb.addItems(["150","300","600"]); self.plot_dpi_cb.setCurrentText("300")
        _row("Plot DPI:", self.plot_dpi_cb, vl9)
        self.gen_excel_cb = QCheckBox("Generate Excel report (45 fields)")
        self.gen_excel_cb.setChecked(True)
        vl9.addWidget(self.gen_excel_cb)
        self.gen_html_cb = QCheckBox("Generate HTML interactive report")
        self.gen_html_cb.setChecked(True)
        vl9.addWidget(self.gen_html_cb)
        layout.addWidget(gb9)

        layout.addStretch()

        # Initial toggle
        self._toggle_flow_params(self.flow_src_cb.currentText())

    # ── Slot helpers ──────────────────────────────────────────────────────────
    def _browse_dem(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "Select DEM", "",
            "Raster (*.tif *.tiff *.img *.hgt *.adf);;All (*.*)")
        if f: self.dem_edit.setText(f)

    def _browse_river(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select River Network", "", "Shapefile (*.shp)")
        if f: self.river_edit.setText(f)

    def _browse_sa(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Study Area", "", "Shapefile (*.shp)")
        if f: self.sa_edit.setText(f)

    def _browse_output(self):
        d = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if d: self.out_edit.setText(d)

    def _toggle_flow_params(self, src: str):
        is_fixed = src == "Débits fixes"
        is_hec   = src == "HEC-HMS (Pjmax)"
        for w in [self.ff_main_spin, self.ff_major_spin,
                  self.ff_sec_spin,  self.up_ratio_spin]:
            w.setEnabled(is_fixed)
        for w in [self.pjmax_spin, self.cn_spin, self.rc_spin,
                  self.rd_spin, self.tc_cb]:
            w.setEnabled(is_hec)

    def _toggle_threshold(self, checked: bool):
        self.thr_peak_spin.setEnabled(not checked)

    def get_params(self) -> dict:
        return {
            'dem_path':            self.dem_edit.text().strip(),
            'river_network_path':  self.river_edit.text().strip(),
            'study_area_path':     self.sa_edit.text().strip(),
            'output_folder':       self.out_edit.text().strip(),
            'generate_network':    self.gen_network_cb.isChecked(),
            'flow_threshold':      self.flow_thr_spin.value(),
            'strahler_main':       self.str_main_spin.value(),
            'strahler_major':      self.str_major_spin.value(),
            'strahler_secondary':  self.str_sec_spin.value(),
            'profile_step':        int(self.profile_step_cb.currentText()),
            'flow_source':         self.flow_src_cb.currentText(),
            'equip_coef':          self.equip_coef_spin.value(),
            'fixed_flow_main':     self.ff_main_spin.value(),
            'fixed_flow_major':    self.ff_major_spin.value(),
            'fixed_flow_secondary':self.ff_sec_spin.value(),
            'upstream_ratio':      self.up_ratio_spin.value() / 100.0,
            'pjmax':               self.pjmax_spin.value(),
            'cn_default':          self.cn_spin.value(),
            'runoff_coef':         self.rc_spin.value() / 100.0,
            'tc_method':           self.tc_cb.currentText(),
            'rainy_days':          self.rd_spin.value(),
            'load_factor':         self.lf_spin.value(),
            'segment_norm':        int(self.seg_norm_cb.currentText()),
            'adaptive_threshold':  self.adap_thr_cb.isChecked(),
            'threshold_peak_manual': self.thr_peak_spin.value(),
            'min_power':           float(self.min_pow_cb.currentText()),
            'min_spacing':         float(self.min_sp_cb.currentText()),
            'max_exploit_dist':    self.max_expl_spin.value(),
            'weir_height':         self.weir_h_spin.value(),
            'manning_n':           self.manning_n_spin.value(),
            'canal_length':        self.canal_l_spin.value(),
            'head_loss_pct':       self.hl_spin.value() / 100.0,
            'side_slope':          self.ss_spin.value(),
            'turbine_eff':         self.te_spin.value() / 100.0,
            'enable_cascade':      self.cascade_cb.isChecked(),
            'cascade_distance':    self.casc_dist_spin.value(),
            'discount_rate':       self.disc_spin.value() / 100.0,
            'project_duration':    self.dur_spin.value(),
            'eur_xof':             self.xof_spin.value(),
            'include_connection':  self.conn_cb.isChecked(),
            'generate_plots':      self.gen_plots_cb.isChecked(),
            'plot_format':         self.plot_fmt_cb.currentText(),
            'plot_dpi':            int(self.plot_dpi_cb.currentText()),
            'plot_all':            False,
            'generate_excel':      self.gen_excel_cb.isChecked(),
            'generate_html':       self.gen_html_cb.isChecked(),
        }

    def validate(self) -> str:
        """Returns error message string, or empty string if OK."""
        if not self.dem_edit.text().strip():
            return "Please select a DEM file."
        if not os.path.exists(self.dem_edit.text().strip()):
            return "DEM file not found."
        if not self.out_edit.text().strip():
            return "Please select an output folder."
        r = self.river_edit.text().strip()
        if r and not os.path.exists(r):
            return "River network shapefile not found."
        s = self.sa_edit.text().strip()
        if s and not os.path.exists(s):
            return "Study area shapefile not found."
        sm = self.str_main_spin.value()
        sj = self.str_major_spin.value()
        ss = self.str_sec_spin.value()
        if not (sm > sj > ss):
            return "Strahler orders must satisfy: Main > Major > Secondary."
        return ""


# ═══════════════════════════════════════════════════════════════════════════════
# RESULTS TABLE
# ═══════════════════════════════════════════════════════════════════════════════

class ResultsTable(QTableWidget):
    COLUMNS = [
        ("Site ID",    "site_id"),
        ("Category",   "categorie"),
        ("P (MW)",     "p_install_mw_manning"),
        ("H (m)",      "h_brute"),
        ("Q (m³/s)",   "q_equip"),
        ("E (GWh/yr)", "energie_gwh_an"),
        ("CAPEX (M€)", "capex_meur"),
        ("LCOE USD/MWh","lcoe_usd_mwh"),
        ("LCOE FCFA",  "lcoe_fcfa_kwh"),
        ("Priority",   "priorite"),
        ("Score",      "score_priorite"),
        ("Z prise (m)","z_prise"),
        ("H nette (m)","h_nette_manning"),
        ("CRN (m)",    "crn"),
        ("Canal L (m)","canal_largeur"),
        ("Digue (m)",  "longueur_digue"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(len(self.COLUMNS))
        self.setHorizontalHeaderLabels([c[0] for c in self.COLUMNS])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSortingEnabled(True)
        self.setStyleSheet(
            "QTableWidget{font-size:12px;}"
            "QHeaderView::section{background:#2c3e50;color:white;padding:6px;font-weight:bold;}"
            "QTableWidget::item:selected{background:#2980b9;color:white;}"
        )

    def populate(self, sites: list):
        self.setSortingEnabled(False)
        self.setRowCount(len(sites))
        for row, s in enumerate(sites):
            for col, (_, key) in enumerate(self.COLUMNS):
                val = s.get(key, "")
                if key == "p_install_mw_manning":
                    val = s.get("p_install_mw_manning", s.get("p_install_mw", 0))
                if isinstance(val, float):
                    item = QTableWidgetItem(f"{val:.2f}")
                    item.setData(Qt.UserRole, val)
                else:
                    item = QTableWidgetItem(str(val))

                # Priority colour
                if key == "priorite":
                    if val == "HIGH":
                        item.setForeground(QColor(C_SUCCESS))
                        item.setFont(QFont("Arial", 11, QFont.Bold))
                    elif val == "MEDIUM":
                        item.setForeground(QColor(C_WARNING))
                        item.setFont(QFont("Arial", 11, QFont.Bold))

                self.setItem(row, col, item)

        self.setSortingEnabled(True)
        self.sortByColumn(10, Qt.DescendingOrder)  # sort by Score


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):

    def __init__(self, licence_expiry: str = ""):
        super().__init__()
        self._licence_expiry = licence_expiry
        self._worker         = None
        self._last_result    = None

        self._build_ui()
        self._update_title()

    def _update_title(self):
        title = "DamFinder Pro v1.0"
        if self._licence_expiry:
            title += f"  —  Licence valid until {self._licence_expiry}"
        self.setWindowTitle(title)

    # ── Build UI ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.setMinimumSize(1280, 800)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Header
        root_layout.addWidget(self._make_header())

        # Main splitter: left panel | right (map + tabs)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)

        # Left: params
        self.params_panel = ParamsPanel()
        splitter.addWidget(self.params_panel)

        # Right: map + log + results tabs
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(6, 6, 6, 6)
        right_layout.setSpacing(6)

        # Analyse + Export buttons row
        btn_row = QHBoxLayout()
        self.btn_analyse = QPushButton("▶  ANALYSE")
        self.btn_analyse.setStyleSheet(_btn_style(C_BUTTON, C_BUTTON_HV, pad="10px 32px"))
        self.btn_analyse.setMinimumHeight(40)
        self.btn_analyse.clicked.connect(self._run_analysis)

        self.btn_export = QPushButton("⬇  EXPORT")
        self.btn_export.setStyleSheet(_btn_style("#27ae60", "#1e8449", pad="10px 24px"))
        self.btn_export.setMinimumHeight(40)
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._open_output)

        btn_row.addWidget(self.btn_analyse)
        btn_row.addWidget(self.btn_export)
        btn_row.addStretch()

        self.status_lbl = QLabel("Ready.")
        self.status_lbl.setStyleSheet("color:#2c3e50;font-size:12px;")
        btn_row.addWidget(self.status_lbl)
        right_layout.addLayout(btn_row)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setStyleSheet(
            "QProgressBar{border-radius:4px;background:#dfe6e9;text-align:center;font-size:11px;}"
            "QProgressBar::chunk{background:#2980b9;border-radius:4px;}"
        )
        right_layout.addWidget(self.progress_bar)

        # Tabs: Map | Log | Results
        tabs = QTabWidget()
        tabs.setStyleSheet(
            "QTabBar::tab{padding:8px 18px;font-size:12px;}"
            "QTabBar::tab:selected{background:#2980b9;color:white;font-weight:bold;}"
        )

        # Tab 1: Map
        self.map_view = QWebEngineView()
        self.map_view.settings().setAttribute(
            QWebEngineSettings.JavascriptEnabled, True)
        self.map_view.setHtml(self._placeholder_map())
        tabs.addTab(self.map_view, "🗺  Interactive Map")

        # Tab 2: Log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setStyleSheet("background:#1e2a3a;color:#ecf0f1;")
        tabs.addTab(self.log_text, "📋  Log")

        # Tab 3: Results
        self.results_table = ResultsTable()
        tabs.addTab(self.results_table, "📊  Results Table")

        right_layout.addWidget(tabs)

        splitter.addWidget(right_widget)
        splitter.setSizes([380, 900])
        root_layout.addWidget(splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("font-size:11px;")
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(
            "DamFinder Pro v1.0  |  ICOLD + World Bank ESMAP methodology  "
            "|  © 2026 DAMFINDER Engineering Tools")

    # ── Header ────────────────────────────────────────────────────────────────
    def _make_header(self) -> QWidget:
        hdr = QFrame()
        hdr.setFixedHeight(64)
        hdr.setStyleSheet(f"background:{C_PRIMARY};")
        layout = QHBoxLayout(hdr)
        layout.setContentsMargins(14, 6, 14, 6)

        # Logo
        logo_lbl = QLabel()
        logo_lbl.setFixedSize(52, 52)
        pix = QPixmap()
        pix.loadFromData(LOGO_SVG.encode(), "SVG")
        if pix.isNull():
            logo_lbl.setText("🌊")
            logo_lbl.setStyleSheet("color:white;font-size:28px;")
        else:
            logo_lbl.setPixmap(pix.scaled(52, 52, Qt.KeepAspectRatio,
                                           Qt.SmoothTransformation))
        layout.addWidget(logo_lbl)

        # Title
        title_lbl = QLabel("DamFinder Pro")
        title_lbl.setStyleSheet("color:white;font-size:22px;font-weight:bold;")
        layout.addWidget(title_lbl)

        sub_lbl = QLabel("v1.0  —  Hydroelectric Site Identification")
        sub_lbl.setStyleSheet("color:#aed6f1;font-size:13px;")
        layout.addWidget(sub_lbl)
        layout.addStretch()

        copy_lbl = QLabel("© 2026 DAMFINDER Engineering Tools")
        copy_lbl.setStyleSheet("color:#85c1e9;font-size:11px;")
        layout.addWidget(copy_lbl)

        return hdr

    # ── Placeholder map ───────────────────────────────────────────────────────
    def _placeholder_map(self) -> str:
        return """<!DOCTYPE html><html><body style="margin:0;background:#eaf2fb;
        display:flex;align-items:center;justify-content:center;height:100vh;
        font-family:Arial,sans-serif;color:#1a3a5c;">
        <div style="text-align:center;">
          <div style="font-size:64px;">🌍</div>
          <h2>Interactive Map</h2>
          <p>Run the analysis to display detected sites on the map.</p>
        </div></body></html>"""

    # ── Run analysis ──────────────────────────────────────────────────────────
    def _run_analysis(self):
        err = self.params_panel.validate()
        if err:
            QMessageBox.warning(self, "Validation Error", err)
            return

        params = self.params_panel.get_params()

        self.btn_analyse.setEnabled(False)
        self.btn_export.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.results_table.setRowCount(0)
        self.status_lbl.setText("Running analysis…")

        self._worker = AnalysisWorker(params)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, pct: int, msg: str, level: str):
        self.progress_bar.setValue(pct)
        if level == 'error':
            colour = C_ERROR
        elif level == 'warning':
            colour = C_WARNING
        else:
            colour = "#ecf0f1"

        self.log_text.append(
            f'<span style="color:{colour};">{msg}</span>')
        # Auto-scroll
        sb = self.log_text.verticalScrollBar()
        sb.setValue(sb.maximum())
        self.status_lbl.setText(msg[:80])

    def _on_finished(self, result: dict):
        self._last_result = result
        sites = result.get('sites', [])

        # Update map
        html = result.get('map_html', '')
        if html:
            self.map_view.setHtml(html)

        # Update results table
        self.results_table.populate(sites)

        # Enable export
        self.btn_export.setEnabled(True)
        self.btn_analyse.setEnabled(True)
        self.progress_bar.setValue(100)
        self.status_lbl.setText(
            f"✓  Analysis complete — {len(sites)} sites detected.")

        QMessageBox.information(
            self, "Analysis Complete",
            f"<b>{len(sites)}</b> hydroelectric sites detected.<br><br>"
            f"Results saved to:<br><code>{self.params_panel.out_edit.text()}</code>"
        )

    def _on_error(self, tb: str):
        self.btn_analyse.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_lbl.setText("❌  Analysis failed.")
        self.log_text.append(
            f'<span style="color:{C_ERROR};">{tb}</span>')
        QMessageBox.critical(self, "Analysis Error",
                             "Analysis failed — see Log tab for details.")

    def _open_output(self):
        out = self.params_panel.out_edit.text().strip()
        if out and os.path.isdir(out):
            import subprocess
            subprocess.Popen(f'explorer "{out}"')
        # Also open HTML report if available
        if self._last_result:
            html_path = self._last_result.get('html_path', '')
            if html_path and os.path.exists(html_path):
                import webbrowser
                webbrowser.open(f"file:///{html_path}")
