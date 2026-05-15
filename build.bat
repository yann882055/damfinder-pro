@echo off
:: ============================================================================
:: DamFinder Pro v1.0 — Build Script (robust geo-stack edition)
:: Produces: dist\DamFinder_Pro\DamFinder_Pro.exe
:: Requirements: Python 3.10 or 3.11, pip, internet (first run)
:: ============================================================================

setlocal EnableDelayedExpansion

title DamFinder Pro — Build

set BUILD_DIR=%~dp0
set VENV_DIR=%BUILD_DIR%venv_build
set LOG_FILE=%BUILD_DIR%build_log.txt

echo.
echo ============================================================
echo  DamFinder Pro v1.0 -- Build Script
echo  DAMFINDER Engineering Tools  ^|  2026
echo ============================================================
echo.

:: ── 1. Check Python 3.10 / 3.11 ─────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10 or 3.11 and add to PATH.
    pause & exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo [INFO]  Python: %PY_VER%

:: Warn if Python 3.12+ (PyQt5 wheel availability issues)
for /f "tokens=1,2 delims=." %%a in ("%PY_VER%") do (
    set PY_MAJOR=%%a
    set PY_MINOR=%%b
)
if %PY_MINOR% GEQ 12 (
    echo [WARN]  Python 3.12+ detected. Recommended: 3.10 or 3.11 for best
    echo         PyQt5/rasterio wheel compatibility.
    echo         Continuing anyway — press Ctrl+C to abort, or any key to proceed.
    pause >nul
)

:: ── 2. Create/activate virtual environment ───────────────────────────────────
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [INFO]  Creating virtual environment…
    python -m venv "%VENV_DIR%"
    if errorlevel 1 ( echo [ERROR] venv creation failed. & pause & exit /b 1 )
) else (
    echo [INFO]  Re-using existing venv: %VENV_DIR%
)

call "%VENV_DIR%\Scripts\activate.bat"

:: ── 3. Upgrade pip / setuptools / wheel ──────────────────────────────────────
echo [INFO]  Upgrading pip, setuptools, wheel…
python -m pip install --upgrade pip setuptools wheel --quiet

:: ── 4. Install geospatial stack (order matters for GDAL/fiona/rasterio) ──────
echo [INFO]  Installing geospatial dependencies…
echo         This may take 5-15 minutes on first run.
echo.

:: Install numpy first (many packages depend on it at build time)
pip install "numpy>=1.24,<2.0" --quiet
if errorlevel 1 ( echo [ERROR] numpy install failed. & pause & exit /b 1 )

:: Install GDAL-based packages via wheels (no local GDAL needed)
pip install "pyproj>=3.5.0"    --quiet
pip install "fiona>=1.9.5"     --quiet
pip install "rasterio>=1.3.8"  --quiet
pip install "shapely>=2.0.2"   --quiet
pip install "geopandas>=0.13.2" --quiet
pip install "pysheds>=0.3.5"   --quiet
pip install "rasterstats>=0.18.0" --quiet

:: Install GUI
pip install "PyQt5>=5.15.9" --quiet
pip install "PyQtWebEngine>=5.15.6" --quiet

:: Install remaining deps from requirements.txt
echo [INFO]  Installing remaining dependencies…
pip install -r "%BUILD_DIR%requirements.txt" --quiet
if errorlevel 1 (
    echo [WARN]  Some packages in requirements.txt may have failed.
    echo         Check build_log.txt for details. Continuing…
)

:: Install certifi explicitly (SSL certs bundled into EXE)
pip install certifi --quiet

:: ── 5. Install PyInstaller ────────────────────────────────────────────────────
echo [INFO]  Installing PyInstaller…
pip install "pyinstaller>=5.13" --quiet
if errorlevel 1 ( echo [ERROR] PyInstaller install failed. & pause & exit /b 1 )

:: ── 6. Verify required files exist ───────────────────────────────────────────
echo [INFO]  Checking required source files…
for %%F in (DamFinder_Pro.py engine.py main_window.py license_manager.py runtime_hook_geo.py DamFinder_Pro.spec) do (
    if not exist "%BUILD_DIR%%%F" (
        echo [ERROR] Missing file: %%F
        pause & exit /b 1
    )
)
echo [INFO]  All source files present.

:: ── 7. Clean previous build ──────────────────────────────────────────────────
if exist "%BUILD_DIR%dist\DamFinder_Pro" (
    echo [INFO]  Cleaning previous dist…
    rmdir /s /q "%BUILD_DIR%dist\DamFinder_Pro"
)
if exist "%BUILD_DIR%build" (
    rmdir /s /q "%BUILD_DIR%build"
)

:: ── 8. Run PyInstaller ────────────────────────────────────────────────────────
echo.
echo [INFO]  Running PyInstaller (this takes 5-10 minutes)…
echo         Log: %LOG_FILE%
echo.

cd /d "%BUILD_DIR%"
pyinstaller DamFinder_Pro.spec --noconfirm --clean 2>&1 | tee "%LOG_FILE%"

if errorlevel 1 (
    echo.
    echo ============================================================
    echo  [ERROR] PyInstaller build FAILED.
    echo ============================================================
    echo.
    echo  Full log saved to: %LOG_FILE%
    echo.
    echo  Most common causes:
    echo    1. Missing package: check last ERROR line in log above
    echo    2. rasterio/fiona wheel issue: try Python 3.10 or 3.11
    echo    3. PyQt5 WebEngine: run  pip install PyQtWebEngine  manually
    echo    4. Antivirus blocking: temporarily disable AV and retry
    echo.
    pause & exit /b 1
)

:: ── 9. Verify output EXE ─────────────────────────────────────────────────────
set EXE_PATH=%BUILD_DIR%dist\DamFinder_Pro\DamFinder_Pro.exe
if not exist "%EXE_PATH%" (
    echo [ERROR] EXE not found at: %EXE_PATH%
    pause & exit /b 1
)

:: ── 10. Show result ───────────────────────────────────────────────────────────
echo.
echo ============================================================
echo  BUILD SUCCESSFUL
echo ============================================================
echo.
echo  Executable : %EXE_PATH%
echo.
for %%F in ("%EXE_PATH%") do echo  EXE size   : %%~zF bytes
echo.
echo  Distribution folder (copy this entire folder to target PC):
echo  %BUILD_DIR%dist\DamFinder_Pro\
echo.
echo  NOTE: Copy the ENTIRE DamFinder_Pro\ folder, not just the .exe
echo        All DLLs and data files in that folder are required.
echo.
echo ============================================================
echo.

:: Open dist folder in Explorer
explorer "%BUILD_DIR%dist\DamFinder_Pro"

deactivate
endlocal
pause
