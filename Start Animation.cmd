@echo off
setlocal
cd /d "%~dp0"
python diamond_ring.py
if errorlevel 1 (
    echo.
    echo If pygame-ce is missing, install the project dependency with:
    echo python -m pip install -r requirements.txt
    pause
)
endlocal
