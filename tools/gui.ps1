# Antigravity Device Optimizer - GUI Launcher
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$repo = Split-Path -Parent $PSScriptRoot
$py = Join-Path $repo 'venv\Scripts\python.exe'
$mgr = Join-Path $repo 'tools\device_manager.py'

$form = New-Object System.Windows.Forms.Form
$form.Text = "Antigravity - Device Optimizer (Wi-Fi)"
$form.Size = New-Object System.Drawing.Size(760, 620)
$form.StartPosition = "CenterScreen"
$form.BackColor = [System.Drawing.Color]::FromArgb(28, 30, 36)
$form.ForeColor = [System.Drawing.Color]::White

# Title Label
$lblTitle = New-Object System.Windows.Forms.Label
$lblTitle.Text = "ANTIGRAVITY IP OPTIMIZER"
$lblTitle.Font = New-Object System.Drawing.Font("Segoe UI", 14, [System.Drawing.FontStyle]::Bold)
$lblTitle.ForeColor = [System.Drawing.Color]::LimeGreen
$lblTitle.Location = New-Object System.Drawing.Point(20, 15)
$lblTitle.Size = New-Object System.Drawing.Size(400, 30)
$form.Controls.Add($lblTitle)

# IP Input
$lblIp = New-Object System.Windows.Forms.Label
$lblIp.Text = "Device IP:"
$lblIp.Location = New-Object System.Drawing.Point(22, 55)
$lblIp.Size = New-Object System.Drawing.Size(70, 25)
$lblIp.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$form.Controls.Add($lblIp)

$txtIp = New-Object System.Windows.Forms.TextBox
$txtIp.Location = New-Object System.Drawing.Point(95, 52)
$txtIp.Size = New-Object System.Drawing.Size(180, 25)
$txtIp.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$txtIp.Text = if ($env:TV_HOST) { $env:TV_HOST } else { "192.168.1.50" }
$form.Controls.Add($txtIp)

# Action Buttons
function Create-Btn($text, $x, $y, $w, $h, $action) {
    $btn = New-Object System.Windows.Forms.Button
    $btn.Text = $text
    $btn.Location = New-Object System.Drawing.Point($x, $y)
    $btn.Size = New-Object System.Drawing.Size($w, $h)
    $btn.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
    $btn.BackColor = [System.Drawing.Color]::FromArgb(45, 50, 60)
    $btn.ForeColor = [System.Drawing.Color]::White
    $btn.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
    $btn.Add_Click($action)
    $form.Controls.Add($btn)
    return $btn
}

# Output TextBox
$txtLog = New-Object System.Windows.Forms.TextBox
$txtLog.Multiline = $true
$txtLog.ScrollBars = "Vertical"
$txtLog.Location = New-Object System.Drawing.Point(20, 140)
$txtLog.Size = New-Object System.Drawing.Size(705, 420)
$txtLog.Font = New-Object System.Drawing.Font("Consolas", 9.5)
$txtLog.BackColor = [System.Drawing.Color]::FromArgb(18, 20, 24)
$txtLog.ForeColor = [System.Drawing.Color]::FromArgb(0, 255, 128)
$txtLog.ReadOnly = $true
$form.Controls.Add($txtLog)

function Log-Msg($msg) {
    $txtLog.AppendText("$msg`r`n")
}

Create-Btn "1. Probe & RAM" 290 50 130 30 {
    $txtLog.Clear()
    Log-Msg "=== Checking Device & Memory ($($txtIp.Text)) ==="
    $res = & $py $mgr --host $txtIp.Text probe 2>&1
    Log-Msg ($res -join "`r`n")
}

Create-Btn "2. View All Apps" 430 50 140 30 {
    $txtLog.Clear()
    Log-Msg "=== Scanning Apps ($($txtIp.Text)) ==="
    $res = & $py $mgr --host $txtIp.Text inventory 2>&1
    Log-Msg ($res -join "`r`n")
}

Create-Btn "3. Quick Debloat" 580 50 145 30 {
    $txtLog.Clear()
    Log-Msg "=== Scanning Safe-to-turn-off Apps ==="
    $res = & $py (Join-Path $repo 'tools\batch_debloat.py') scan $txtIp.Text 2>&1
    Log-Msg ($res -join "`r`n")
    $confirm = [System.Windows.Forms.MessageBox]::Show("Bạn có muốn tắt toàn bộ các ứng dụng quảng cáo / rác vừa tìm thấy không?", "Xác nhận Debloat", "YesNo", "Question")
    if ($confirm -eq "Yes") {
        Log-Msg "--> Đang tắt ứng dụng..."
        $res2 = & $py (Join-Path $repo 'tools\batch_debloat.py') apply $txtIp.Text 2>&1
        Log-Msg ($res2 -join "`r`n")
    }
}

Create-Btn "4. Optimize (Anim/Sleep)" 20 95 180 30 {
    $txtLog.Clear()
    Log-Msg "=== Turning off animations & setting 5m sleep ==="
    $res = & $py $mgr --host $txtIp.Text optimize-settings 2>&1
    Log-Msg ($res -join "`r`n")
}

Create-Btn "5. Reboot Device" 210 95 150 30 {
    $confirm = [System.Windows.Forms.MessageBox]::Show("Khởi động lại thiết bị $($txtIp.Text)?", "Reboot", "YesNo", "Warning")
    if ($confirm -eq "Yes") {
        Log-Msg "--> Sending reboot command..."
        & $py $mgr --host $txtIp.Text reboot
        Log-Msg "Thiết bị đang khởi động lại."
    }
}

Create-Btn "6. Rollback All (Undo)" 370 95 170 30 {
    $txtLog.Clear()
    Log-Msg "=== Undoing all disabled packages from undo-log.jsonl ==="
    $res = powershell -ExecutionPolicy Bypass -File (Join-Path $repo 'tools\adb.ps1') rollback -HostIp $txtIp.Text 2>&1
    Log-Msg ($res -join "`r`n")
}

Create-Btn "Clear Log" 550 95 175 30 {
    $txtLog.Clear()
}

[System.Windows.Forms.Application]::EnableVisualStyles()
$form.ShowDialog() | Out-Null
