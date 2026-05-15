# -*- mode: python ; coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════════════════════
# DamFinder Pro v1.0 — PyInstaller Spec  (robust geo-stack edition)
# ══════════════════════════════════════════════════════════════════════════════
# Usage:  pyinstaller DamFinder_Pro.spec  (or via build.bat)
# ══════════════════════════════════════════════════════════════════════════════

import sys, os
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None
src = Path(SPECPATH)

# ── collect_all for every geo / scientific package ────────────────────────────
# collect_all returns (datas, binaries, hiddenimports) for the whole package tree

datas_all, binaries_all, hi_all = [], [], []

for pkg in [
    'rasterio', 'fiona', 'pyproj', 'pysheds',
    'geopandas', 'shapely', 'rasterstats',
    'folium', 'branca',
    'matplotlib', 'plotly',
    'openpyxl', 'reportlab',
    'pandas', 'numpy', 'scipy',
]:
    try:
        d, b, h = collect_all(pkg)
        datas_all    += d
        binaries_all += b
        hi_all       += h
    except Exception as e:
        print(f'[WARN] collect_all({pkg}) skipped: {e}')

# ── Extra data directories (GDAL / PROJ) ─────────────────────────────────────
try:
    import pyproj
    _proj_dir = Path(pyproj.datadir.get_data_dir())
    datas_all.append((str(_proj_dir), 'pyproj/proj_dir/share/proj'))
except Exception as e:
    print(f'[WARN] pyproj data dir: {e}')

try:
    import rasterio
    _gdal_data = Path(rasterio.__file__).parent / 'gdal_data'
    if _gdal_data.is_dir():
        datas_all.append((str(_gdal_data), 'rasterio/gdal_data'))
    _gdal_drv = Path(rasterio.__file__).parent / 'gdal_plugins'
    if _gdal_drv.is_dir():
        datas_all.append((str(_gdal_drv), 'rasterio/gdal_plugins'))
except Exception as e:
    print(f'[WARN] rasterio GDAL data: {e}')

try:
    import certifi
    datas_all.append((certifi.where(), 'certifi'))
except Exception:
    pass

# ── Hidden imports not caught by collect_all ──────────────────────────────────
hidden_imports = hi_all + [
    # PyQt5
    'PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets',
    'PyQt5.QtWebEngineWidgets', 'PyQt5.QtWebEngineCore',
    'PyQt5.QtWebChannel', 'PyQt5.QtNetwork', 'PyQt5.QtSvg',
    'PyQt5.QtPrintSupport', 'PyQt5.sip',
    # rasterio internals
    'rasterio._base', 'rasterio.crs', 'rasterio.features',
    'rasterio.mask', 'rasterio.merge', 'rasterio.transform',
    'rasterio.warp', 'rasterio.windows', 'rasterio._shim',
    'rasterio.enums', 'rasterio.vrt', 'rasterio.control',
    'rasterio.sample', 'rasterio.plot',
    # fiona
    'fiona', 'fiona.ogrext', 'fiona._shim', 'fiona.collection',
    # pysheds
    'pysheds', 'pysheds.grid', 'pysheds.view', 'pysheds.sview',
    # geopandas
    'geopandas', 'geopandas.tools', 'geopandas.io',
    # shapely
    'shapely', 'shapely.geometry', 'shapely.ops',
    'shapely.affinity', 'shapely.prepared',
    # scipy
    'scipy', 'scipy.ndimage', 'scipy.spatial', 'scipy.interpolate',
    'scipy._lib.messagestream',
    # numpy
    'numpy', 'numpy.core._multiarray_umath',
    'numpy.core._multiarray_tests',
    # pandas
    'pandas', 'pandas._libs.tslibs.np_datetime',
    'pandas._libs.tslibs.nattype',
    'pandas._libs.tslibs.timedeltas',
    'pandas._libs.skiplist',
    # matplotlib
    'matplotlib', 'matplotlib.backends.backend_agg',
    'matplotlib.backends.backend_pdf',
    'matplotlib.backends.backend_svg',
    # plotly
    'plotly', 'plotly.graph_objects', 'plotly.subplots',
    'plotly.express',
    # folium / branca
    'folium', 'folium.plugins', 'branca', 'branca.element',
    # reporting
    'openpyxl', 'openpyxl.styles', 'openpyxl.utils',
    'reportlab', 'reportlab.pdfgen', 'reportlab.lib',
    'reportlab.platypus',
    # std extras
    'pkg_resources', 'pkg_resources._vendor',
    'email.mime.text', 'xml.etree.ElementTree',
    'json', 'hashlib', 'base64', 'tempfile', 'pathlib',
    'socket', 'platform',
    # app modules
    'engine', 'license_manager', 'main_window',
]

# ── Exclusions (keep EXE lean) ────────────────────────────────────────────────
excludes = [
    'tkinter', '_tkinter', 'wx', 'gtk', 'gi',
    'IPython', 'jupyter', 'notebook', 'ipykernel',
    'sklearn', 'torch', 'tensorflow', 'keras',
    'test', 'tests', 'unittest',
    'sphinx', 'docutils',
]

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    [str(src / 'DamFinder_Pro.py')],
    pathex=[str(src)],
    binaries=binaries_all,
    datas=datas_all,
    hiddenimports=list(set(hidden_imports)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(src / 'runtime_hook_geo.py')],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DamFinder_Pro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,            # UPX disabled — breaks GDAL/Qt DLLs
    console=False,        # GUI app — no console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    version_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='DamFinder_Pro',
)
