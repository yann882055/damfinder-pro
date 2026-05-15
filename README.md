# DamFinder Pro v1.0

**Standalone Windows application for hydroelectric site detection and analysis.**
No ArcGIS or Python installation required on the target machine.

Methodology: ICOLD standards + World Bank ESMAP hydropower guidelines
Developed by: DAMFINDER Engineering Tools — 2026

---

## Download (recommended)

Go to the **[Releases](../../releases)** tab and download the latest
`DamFinder_Pro_Windows_x64.zip`.  
Extract the entire folder, then double-click `DamFinder_Pro.exe`.

> The EXE is built automatically by GitHub Actions every time a version tag
> (`v1.0`, `v1.1`, …) is pushed — no manual build needed.

---

## Repository structure

```
DamFinder_Pro.py          # Entry point — splash screen, licence gate
main_window.py            # PyQt5 GUI (params panel, map, results table)
engine.py                 # Core analysis pipeline (rasterio / pysheds / geopandas)
license_manager.py        # SHA-256 licence validation + AppData storage
runtime_hook_geo.py       # PyInstaller runtime hook (GDAL/PROJ env vars)
DamFinder_Pro.spec        # PyInstaller spec (robust geo-stack edition)
build.bat                 # Local build script (Windows)
requirements.txt          # Python dependencies
.github/workflows/
  build.yml               # GitHub Actions CI/CD pipeline
```

---

## Build via GitHub Actions (recommended)

Every push to `main` triggers a build and uploads the EXE as a workflow
artifact (30-day retention).

To publish a **Release**:

```bash
git tag v1.0
git push origin v1.0
```

GitHub Actions will:
1. Spin up a `windows-latest` runner
2. Install Python 3.11 + all dependencies
3. Run PyInstaller with `DamFinder_Pro.spec`
4. Zip `dist/DamFinder_Pro/`
5. Attach the zip to a GitHub Release automatically

No local Windows machine or manual build needed.

---

## Local build (Windows)

Requirements: Python 3.10 or 3.11 on PATH, internet connection.

```bat
build.bat
```

Output: `dist\DamFinder_Pro\DamFinder_Pro.exe`

Copy the **entire** `dist\DamFinder_Pro\` folder to the target PC
(not just the `.exe` — the DLLs and data files alongside it are required).

---

## Licence

The application uses a key-based licence system.  
Keys are generated with `license_manager.generate_key()` and activated
on first launch via the built-in activation dialog.
