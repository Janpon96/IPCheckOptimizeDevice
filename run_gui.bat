@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"

:: Verify that venv python runs properly (auto-rebuild if moved from another PC)
"venv\Scripts\python.exe" -c "import adb_shell, tkinter" >nul 2>&1
if errorlevel 1 (
    echo [*] Dang khoi tao hoac cap nhat moi truong Python venv...
    if exist "venv" rmdir /s /q "venv"
    py -3.10 -m venv venv || python -m venv venv
    if not exist "venv\Scripts\python.exe" (
        echo [ERROR] Khong tim thay Python 3 tren may tinh. Vui long cai dat Python 3.10+.
        pause
        exit /b 1
    )
    echo [*] Dang cai dat thu vien adb-shell, rsa, cryptography...
    "venv\Scripts\pip.exe" install --upgrade pip >nul 2>&1
    "venv\Scripts\pip.exe" install adb-shell rsa cryptography
)

start "" "venv\Scripts\pythonw.exe" "tools\gui_app.py"
