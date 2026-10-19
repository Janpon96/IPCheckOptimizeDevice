@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
title Antigravity - IP Device Optimizer (1-Click)
color 0A

cd /d "%~dp0"

echo ======================================================================
echo          ANTIGRAVITY IP DEVICE OPTIMIZER ^& DEBLOATER
echo   (Ho tro: Android TV, Google TV, Fire TV, May chieu Xview, Android)
echo ======================================================================
echo.

:: 1. Kiem tra moi truong Python venv
if not exist "venv\Scripts\python.exe" (
    echo [*] Chua tim thay moi truong venv. Dang khoi tao...
    py -3.10 -m venv venv || python -m venv venv
    if not exist "venv\Scripts\python.exe" (
        echo [ERROR] Khong the tao virtual environment Python. Hay cai dat Python 3.
        pause
        exit /b 1
    )
    echo [*] Dang cai dat thu vien phu thuoc...
    venv\Scripts\pip.exe install adb-shell rsa cryptography
)

:: 2. Nhap IP Thiet bi
if "%TV_HOST%"=="" (
    set /p TV_HOST=">> Nhap dia chi IP thiet bi (vi du: 192.168.1.50): "
) else (
    echo [*] Su dung IP tu bien moi truong TV_HOST: %TV_HOST%
    set /p CONFIRM="Ban co muon doi IP khong? (y/N): "
    if /i "!CONFIRM!"=="y" (
        set /p TV_HOST=">> Nhap dia chi IP moi: "
    )
)

if "%TV_HOST%"=="" (
    echo [ERROR] Ban chua nhap IP thiet bi.
    pause
    exit /b 1
)

:MENU
cls
echo ======================================================================
echo   DANG KET NOI THIET BI: %TV_HOST%
echo ======================================================================
echo   1. [Probe] Kiem tra ket noi, Thong tin he thong ^& Bo nho RAM hien tai
echo   2. [Inventory] Xem TOAN BO APP (chia 3 nhom: An toan tat / Giu / App cua ban)
echo   3. [Debloat] Tat 1 ung dung (Co Guardrail bao ve, khong so hong)
echo   4. [Optimize] Tat animation, tat screensaver, hen gio ngu 5 phut
echo   5. [Debloat Quick Batch] Quet va de xuat tat app rac/quang cao tu dong
echo   6. [Reboot] Khoi dong lai thiet bi
echo   7. [Rollback] HOAN TAC TAT CA (Bat lai toan bo app da tat tu undo-log)
echo   8. Doi dia chi IP thiet bi khac
echo   9. Thoat
echo ======================================================================
set /p CHOICE="Lua chon cua ban (1-9): "

if "%CHOICE%"=="1" (
    echo.
    echo [*] Dang quet he thong va do RAM...
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
    set /p PKG=">> Nhap Package ID can tat (vi du: com.miui.tvads): "
    if not "!PKG!"=="" (
        powershell -ExecutionPolicy Bypass -File .\tools\adb.ps1 disable !PKG! -HostIp %TV_HOST%
    )
    echo.
    pause
    goto MENU
)

if "%CHOICE%"=="4" (
    echo.
    echo [*] Dang toi uu hoa: Tat animations, tat screensaver, sleep sau 5 phut...
    powershell -ExecutionPolicy Bypass -File .\tools\adb.ps1 optimize-settings -HostIp %TV_HOST%
    echo.
    pause
    goto MENU
)

if "%CHOICE%"=="5" (
    echo.
    echo [*] Dang quet danh sach app rac va de xuat tat...
    venv\Scripts\python.exe tools\batch_debloat.py scan %TV_HOST%
    echo.
    set /p CONFIRM_BATCH="Ban co muon tat tat ca cac app rac duoc danh dau an toan o tren khong? (y/N): "
    if /i "!CONFIRM_BATCH!"=="y" (
        venv\Scripts\python.exe tools\batch_debloat.py apply %TV_HOST%
    )
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
    echo [*] Dang hoan tac toan bo thay doi tu undo-log.jsonl...
    powershell -ExecutionPolicy Bypass -File .\tools\adb.ps1 rollback -HostIp %TV_HOST%
    echo.
    pause
    goto MENU
)

if "%CHOICE%"=="8" (
    set /p TV_HOST=">> Nhap dia chi IP thiet bi moi: "
    goto MENU
)

if "%CHOICE%"=="9" (
    exit /b 0
)

goto MENU
