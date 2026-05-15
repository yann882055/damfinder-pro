# ============================================================================
# DamFinder Pro v1.0 — PyInstaller Runtime Hook
# Sets GDAL / PROJ / SSL environment variables before any import occurs.
# This file is executed by the frozen EXE before DamFinder_Pro.py starts.
# ============================================================================

import os
import sys

# Base directory of the frozen app (_MEIPASS when frozen, script dir otherwise)
if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.abspath(__file__))


def _setenv_if_exists(var: str, *path_parts: str) -> None:
    """Set environment variable only if the target path actually exists."""
    candidate = os.path.join(_base, *path_parts)
    if os.path.exists(candidate):
        os.environ[var] = candidate


# ── GDAL data (rasterio bundles its own GDAL) ─────────────────────────────────
_setenv_if_exists('GDAL_DATA',          'rasterio', 'gdal_data')
_setenv_if_exists('GDAL_DRIVER_PATH',   'rasterio', 'gdal_plugins')

# ── PROJ data (pyproj) ────────────────────────────────────────────────────────
_setenv_if_exists('PROJ_LIB',           'pyproj', 'proj_dir', 'share', 'proj')
_setenv_if_exists('PROJ_DATA',          'pyproj', 'proj_dir', 'share', 'proj')

# ── SSL certificates (certifi) ────────────────────────────────────────────────
_cert = os.path.join(_base, 'certifi', 'cacert.pem')
if os.path.isfile(_cert):
    os.environ.setdefault('SSL_CERT_FILE', _cert)
    os.environ.setdefault('REQUESTS_CA_BUNDLE', _cert)

# ── Qt WebEngine flags ────────────────────────────────────────────────────────
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS', '--disable-gpu --no-sandbox')
os.environ.setdefault('QTWEBENGINE_DISABLE_SANDBOX', '1')

# ── PATH: ensure bundled DLLs are found first ─────────────────────────────────
os.environ['PATH'] = _base + os.pathsep + os.environ.get('PATH', '')
