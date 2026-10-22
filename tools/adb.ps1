<#
.SYNOPSIS
    adb.ps1 - Windows PowerShell wrapper for Multi-Platform IP Device Optimization over Wi-Fi
.DESCRIPTION
    Provides clean commands matching the 10-step RUNBOOK workflow:
    - scan-lan: Discover all active devices on the local network with platform detection
    - detect: Smart fingerprint a specific IP (OS, open ports, MAC vendor, connection method)
    - probe: Check connection, identity, and current memory (ADB + Roku ECP support)
    - backup: Save pre-flight baseline snapshot (RAM + packages) before making changes
    - inventory: List all apps divided into 3 plain English lists
    - disable: Turn off an app with automatic guard check and undo-log
    - enable: Restore a previously turned-off app
    - optimize-settings: Disable animations, screensaver, set 5-minute sleep
    - reboot: Restart the target device
    - verify: Post-reboot verification (confirm disabled apps stayed off + RAM before/after delta)
    - report: Generate Before/After markdown report & undo sheet
    - rollback: Undo all changes logged in undo-log.jsonl
#>

param(
    [Parameter(Position = 0, Mandatory = $true)]
    [ValidateSet("scan-lan", "detect", "probe", "backup", "inventory", "disable", "enable", "optimize-settings", "reboot", "verify", "report", "rollback")]
    [string]$Action,

    [Parameter(Position = 1)]
    [string]$Target,

    [string]$HostIp = $env:TV_HOST,
    [int]$Port = 5555,
    [switch]$Json
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'Continue'
$repo = Split-Path -Parent $PSScriptRoot
$py = Join-Path $repo 'venv\Scripts\python.exe'
$mgr = Join-Path $repo 'tools\device_manager.py'

if (-not (Test-Path $py)) {
    throw "Python virtual environment not found at $py. Run run.bat or setup first."
}

$jsonFlag = @()
if ($Json) {
    $jsonFlag = @("--json")
}

if ($Action -eq "scan-lan") {
    & $py $mgr @jsonFlag scan-lan
    exit $LASTEXITCODE
}

if (-not $HostIp) {
    Write-Host "Usage: .\tools\adb.ps1 <scan-lan|detect|probe|backup|inventory|disable|enable|optimize-settings|reboot|verify|report|rollback> [-Target <package>] -HostIp <DEVICE_IP>" -ForegroundColor Yellow
    exit 1
}

switch ($Action) {
    "detect" {
        & $py $mgr --host $HostIp --port $Port @jsonFlag detect
    }
    "probe" {
        & $py $mgr --host $HostIp --port $Port @jsonFlag probe
    }
    "backup" {
        & $py $mgr --host $HostIp --port $Port @jsonFlag backup
    }
    "inventory" {
        & $py $mgr --host $HostIp --port $Port @jsonFlag inventory
    }
    "disable" {
        if (-not $Target) { throw "Please specify the package name to disable: .\tools\adb.ps1 disable <package> -HostIp <IP>" }
        & $py $mgr --host $HostIp --port $Port disable $Target
    }
    "enable" {
        if (-not $Target) { throw "Please specify the package name to enable: .\tools\adb.ps1 enable <package> -HostIp <IP>" }
        & $py $mgr --host $HostIp --port $Port enable $Target
    }
    "optimize-settings" {
        & $py $mgr --host $HostIp --port $Port optimize-settings
    }
    "reboot" {
        & $py $mgr --host $HostIp --port $Port reboot
    }
    "verify" {
        & $py $mgr --host $HostIp --port $Port @jsonFlag verify
    }
    "report" {
        & $py $mgr --host $HostIp --port $Port report
    }
    "rollback" {
        & $py $mgr --host $HostIp --port $Port rollback
    }
}
