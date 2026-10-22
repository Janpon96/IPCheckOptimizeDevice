# Antigravity Device Optimizer - GUI Launcher Wrapper
$repo = Split-Path -Parent $PSScriptRoot
$pyw = Join-Path $repo 'venv\Scripts\pythonw.exe'
$py = Join-Path $repo 'venv\Scripts\python.exe'
$gui = Join-Path $repo 'tools\gui_app.py'

if (Test-Path $pyw) {
    Start-Process -FilePath $pyw -ArgumentList "`"$gui`"" -WorkingDirectory $repo
} elseif (Test-Path $py) {
    & $py $gui
} else {
    Write-Host "[ERROR] Python virtual environment not found at $repo\venv. Please run run.bat or run_gui.bat first." -ForegroundColor Red
}
