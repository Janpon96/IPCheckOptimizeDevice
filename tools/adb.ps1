<#
.SYNOPSIS
    adb.ps1 - Windows PowerShell wrapper for Device Optimization over Wi-Fi
.DESCRIPTION
    Provides clean commands matching the RUNBOOK workflow:
    - probe: Check connection, identity, and current memory
    - inventory: List all apps divided into 3 plain English lists
    - disable: Turn off an app with automatic guard check and undo-log
    - enable: Restore a previously turned-off app
    - optimize-settings: Disable animations, screensaver, set 5-minute sleep
    - rollback: Undo all changes logged in undo-log.jsonl
    - reboot: Restart the target device
#>

param(
    [Parameter(Position = 0, Mandatory = $true)]
    [ValidateSet("probe", "inventory", "disable", "enable", "optimize-settings", "rollback", "reboot")]
    [string]$Action,

    [Parameter(Position = 1)]
    [string]$Target,

    [string]$HostIp = $env:TV_HOST,
    [int]$Port = 5555
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'Continue'
$repo = Split-Path -Parent $PSScriptRoot
$py = Join-Path $repo 'venv\Scripts\python.exe'
$mgr = Join-Path $repo 'tools\device_manager.py'

if (-not (Test-Path $py)) {
    throw "Python virtual environment not found at $py. Run setup first."
}

if (-not $HostIp) {
    Write-Host "Usage: .\tools\adb.ps1 <probe|inventory|disable|enable|optimize-settings|rollback|reboot> [-Target <package>] -HostIp <DEVICE_IP>" -ForegroundColor Yellow
    exit 1
}

switch ($Action) {
    "probe" {
        & $py $mgr --host $HostIp --port $Port probe
    }
    "inventory" {
        & $py $mgr --host $HostIp --port $Port inventory
    }
    "disable" {
        if (-not $Target) { throw "Please specify the package name to disable: ./tools/adb.ps1 disable <package>" }
        & $py $mgr --host $HostIp --port $Port disable $Target
    }
    "enable" {
        if (-not $Target) { throw "Please specify the package name to enable: ./tools/adb.ps1 enable <package>" }
        & $py $mgr --host $HostIp --port $Port enable $Target
    }
    "optimize-settings" {
        & $py $mgr --host $HostIp --port $Port optimize-settings
    }
    "reboot" {
        & $py $mgr --host $HostIp --port $Port reboot
    }
    "rollback" {
        $undoFile = Join-Path $repo 'undo-log.jsonl'
        if (-not (Test-Path $undoFile)) {
            Write-Host "No undo log found at $undoFile" -ForegroundColor Yellow
            return
        }
        Write-Host "Reversing applied disable actions from $undoFile..." -ForegroundColor Cyan
        $lines = Get-Content $undoFile
        foreach ($line in $lines) {
            if ($line -match '"status":\s*"applied"' -and $line -match '"action":\s*"disable-user"') {
                $obj = $line | ConvertFrom-Json
                $pkg = $obj.target
                Write-Host "Restoring package: $pkg ($($obj.plain_name))..." -ForegroundColor Green
                & $py $mgr --host $HostIp --port $Port enable $pkg
            }
        }
        Write-Host "Rollback completed." -ForegroundColor Green
    }
}
