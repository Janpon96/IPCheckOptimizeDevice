@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
title Antigravity - Multi-Platform IP Device Optimizer v2.0
color 0A

cd /d "%~dp0"

echo ===========================================================================
echo          ANTIGRAVITY MULTI-PLATFORM IP DEVICE OPTIMIZER v2.0
echo    Ho tro: Android TV, Google TV, Fire TV, May chieu Xview/PONT, Roku,
echo            Android Phone, iPhone/iOS, Samsung Tizen, LG webOS, Switch/DS
echo ===========================================================================
echo.

:: 1. Kiem tra va tu dong sua moi truong Python venv neu chuyen may
"venv\Scripts\python.exe" -c "import adb_shell" >nul 2>&1
if errorlevel 1 (
    echo [*] Dang khoi tao hoac cap nhat moi truong Python venv...
    if exist "venv" rmdir /s /q "venv"
    py -3.10 -m venv venv || python -m venv venv
    if not exist "venv\Scripts\python.exe" (
        echo [ERROR] Khong the tao virtual environment Python. Hay cai dat Python 3.
        pause
        exit /b 1
    )
    echo [*] Dang cai dat thu vien phu thuoc...
    "venv\Scripts\pip.exe" install --upgrade pip >nul 2>&1
    "venv\Scripts\pip.exe" install adb-shell rsa cryptography
)

:: 2. Chon che do hoac nhap IP
if "%TV_HOST%"=="" (
    echo [*] Ban co the:
    echo     - Nhap truc tiep IP thiet bi - vi du: 192.168.1.50
    echo     - Go S de quet tu dong toan bo thiet bi trong mang LAN
    echo     - Go G de mo Giao dien Do hoa hien dai - GUI App
    echo.
    set /p INPUT_INIT=">> Nhap IP thiet bi [hoac S = Quet LAN / G = Mo GUI]: "
    if /i "!INPUT_INIT!"=="G" (
        start "" "venv\Scripts\pythonw.exe" "tools\gui_app.py"
        exit /b 0
    )
    if /i "!INPUT_INIT!"=="S" (
        echo.
        echo [*] Dang quet mang LAN de tim TV, Dien thoai, May chieu...
        "venv\Scripts\python.exe" "tools\device_manager.py" scan-lan
        echo.
        set /p TV_HOST=">> Nhap dia chi IP thiet bi ban muon ket noi: "
    ) else (
        set "TV_HOST=!INPUT_INIT!"
    )
)

if "%TV_HOST%"=="" (
    set "TV_HOST=192.168.1.50"
)

:MENU
cls
echo ===========================================================================
echo   ANTIGRAVITY IP DEVICE OPTIMIZER v2.0  ^|  THIET BI HIEN TAI: %TV_HOST%
echo ===========================================================================
echo   [0] Quet mang LAN - Tim tat ca TV, Dien thoai, May chieu trong Wi-Fi
echo   [1] Smart Detect ^& Probe - Nhan dien he dieu hanh, cong mang ^& do RAM
echo   [2] Inventory - Xem TOAN BO APP chia 3 danh sach Tieng Anh de hieu
echo   [3] Debloat 1 App - Tat 1 ung dung co Guardrail bao ve ^& luu Undo Log
echo   [4] Quick Batch Debloat - Quet ^& tat toan bo App Rac / Quang cao an toan
echo   [5] Optimize Settings - Tat Animation 0x, tat Screensaver, Ngu sau 5p
echo   [6] Reboot - Khoi dong lai thiet bi
echo   [7] Verify ^& Report - Kiem tra sau Reboot ^& So sanh RAM Truoc / Sau
echo   [8] Rollback - HOAN TAC TAT CA - Bat lai toan bo app da tat tu Undo Log
echo   [9] Doi dia chi IP thiet bi khac
echo   [G] Mo Giao Dien Do Hoa - Dark GUI App (Khuyen dung)
echo   [Q] Thoat
echo ===========================================================================
set /p CHOICE=">> Lua chon cua ban (0-9, G, Q): "

if "%CHOICE%"=="0" (
    echo.
    echo [*] Dang quet toan bo thiet bi tren mang LAN...
    "venv\Scripts\python.exe" "tools\device_manager.py" scan-lan
    echo.
    set /p NEW_IP=">> Nhap IP moi neu muon chuyen thiet bi [Bam Enter de giu %TV_HOST%]: "
    if not "!NEW_IP!"=="" set "TV_HOST=!NEW_IP!"
    goto MENU
)

if "%CHOICE%"=="1" (
    echo.
    echo [*] Dang nhan dien thiet bi, kiem tra ket noi va do RAM...
    powershell -ExecutionPolicy Bypass -File .\tools\adb.ps1 probe -HostIp %TV_HOST%
    echo.
    pause
    goto MENU
)

if "%CHOICE%"=="2" (
    echo.
    echo [*] Dang liet ke toan bo ung dung tren thiet bi...
    powershell -ExecutionPolicy Bypass -File .\tools\adb.ps1 inventory -HostIp %TV_HOST%
    echo.
    pause
    goto MENU
)

if "%CHOICE%"=="3" (
    echo.
    set /p PKG=">> Nhap Package ID can tat - vi du com.miui.tvads: "
    if not "!PKG!"=="" (
        powershell -ExecutionPolicy Bypass -File .\tools\adb.ps1 disable !PKG! -HostIp %TV_HOST%
    )
    echo.
    pause
    goto MENU
)

if "%CHOICE%"=="4" (
    echo.
    echo [*] Dang quet danh sach app rac va de xuat tat...
    "venv\Scripts\python.exe" "tools\batch_debloat.py" scan %TV_HOST%
    echo.
    set /p CONFIRM_BATCH=">> Ban co muon tat tat ca cac app rac an toan o tren khong? (y/N): "
    if /i "!CONFIRM_BATCH!"=="y" (
        "venv\Scripts\python.exe" "tools\batch_debloat.py" apply %TV_HOST%
    )
    echo.
    pause
    goto MENU
)

if "%CHOICE%"=="5" (
    echo.
    echo [*] Dang toi uu hoa: Tat animations, tat screensaver, sleep sau 5 phut...
    powershell -ExecutionPolicy Bypass -File .\tools\adb.ps1 optimize-settings -HostIp %TV_HOST%
    echo.
    pause
    goto MENU
)

if "%CHOICE%"=="6" (
    echo.
    echo [*] Dang gui lenh reboot...
    powershell -ExecutionPolicy Bypass -File .\tools\adb.ps1 reboot -HostIp %TV_HOST%
    echo.
    pause
    goto MENU
)

if "%CHOICE%"=="7" (
    echo.
    echo [*] Dang kiem tra trang thai sau reboot va so sanh RAM Before/After...
    powershell -ExecutionPolicy Bypass -File .\tools\adb.ps1 verify -HostIp %TV_HOST%
    echo.
    powershell -ExecutionPolicy Bypass -File .\tools\adb.ps1 report -HostIp %TV_HOST%
    echo.
    pause
    goto MENU
)

if "%CHOICE%"=="8" (
    echo.
    echo [*] Dang hoan tac toan bo thay doi tu undo-log.jsonl...
    powershell -ExecutionPolicy Bypass -File .\tools\adb.ps1 rollback -HostIp %TV_HOST%
    echo.
    pause
    goto MENU
)

if "%CHOICE%"=="9" (
    echo.
    set /p TV_HOST=">> Nhap dia chi IP thiet bi moi: "
    goto MENU
)

if /i "%CHOICE%"=="G" (
    start "" "venv\Scripts\pythonw.exe" "tools\gui_app.py"
    goto MENU
)

if /i "%CHOICE%"=="Q" (
    exit /b 0
)

goto MENU
