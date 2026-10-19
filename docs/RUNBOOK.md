# RUNBOOK — Quy trình tối ưu thiết bị qua IP

> Chạy theo đúng thứ tự 10 bước. Mỗi bước có **Điều kiện thoát** rõ ràng — không đạt thì dừng, không nhảy bước.

## Bước 0 — Chuẩn bị (2 phút)

```powershell
$env:DEVICE_IP = "192.168.1.50"     # IP thiết bị
$env:WORKDIR   = "e:\Antigravity Project\Tools New\IPCheckOptimizeDevice"
New-Item -ItemType Directory -Force "$env:WORKDIR\reports", "$env:WORKDIR\backups" | Out-Null
Test-Connection $env:DEVICE_IP -Count 2
```

**Thoát:** ping được ≥1 lần. Nếu không → xem [Xử lý sự cố](#xlý-sự-cố).

---

## Bước 1 — Kết nối (network) ⚠️ hỏi user trước

Với Android: user phải **bật USB debugging trên máy**. Hướng dẫn tap từng bước:

**Google TV / Android TV**
```
Settings → (nếu là Google TV: hãy dùng nút phím dưới cùng) Device Preferences → About
→ nhấn OK lần 1..7 vào "Build" → quay lại → Developer options
→ bật "USB debugging" (và "Network debugging" / "ADB over network" nếu có)
→ giữ TV bật sáng, không rút điện
```

**Android điện thoại / máy chiếu Xview**
```
Settings → About phone → nhấn Build 7 lần → Settings → System → Developer options
→ USB debugging = ON
```

**Amazon Fire TV**
```
Settings → My Fire TV → Developer Options → ADB Debugging = ON
→ (tuỳ dòng) Network ADB debugging = ON
```

**iPhone/iPad**
```
Settings → Privacy & Security → Developer Mode = ON → khởi động lại
→ Settings → Developer → Apple Mobile Device (iPad: Wireless Access)
```

Sau đó trên máy tính:
```powershell
adb connect $env:DEVICE_IP:5555
adb devices        # phải thấy "device", không phải "unauthorized"/"offline"
```

**Thoát:** `adb devices` hiện `device`. Nếu `unauthorized` → nhắc user nhấn **Allow USB debugging** trên máy.

---

## Bước 2 — Probe (xác định thiết bị)

```powershell
adb -s $env:DEVICE_IP:5555 shell getprop ro.product.model
adb -s $env:DEVICE_IP:5555 shell getprop ro.build.version.release
adb -s $env:DEVICE_IP:5555 shell getprop ro.build.version.sdk
adb -s $env:DEVICE_IP:5555 shell getprop ro.product.manufacturer
adb -s $env:DEVICE_IP:5555 shell pm list features | Select-String "leanback|television|touchscreen"
```

Đối chiếu bảng:

| Tín hiệu | Profile | Tài liệu |
|---|---|---|
| `leanback` + không `touchscreen` | android-tv | [01](profiles/01-android-tv-google-tv.md) |
| `television` | fire-tv | [03](profiles/03-fire-tv.md) |
| `touchscreen`, không `leanback` | android-phone/tablet | [02](profiles/02-android-phone-tablet.md) |
| `ro.build.display.id` có `Xview`/`PONT`/`DVB` | android-projector | [04](profiles/04-android-projector-xview.md) |

**Thoát:** xác định được profile → nạp đúng file `profiles/NN-*.md` làm ngữ cảnh.

---

## Bước 3 — Backup (bắt buộc)

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmm"
$b  = "$env:WORKDIR\backups\$ts"
New-Item -ItemType Directory -Force $b | Out-Null
$d  = "$env:DEVICE_IP:5555"
adb -s $d shell pm list packages          | Out-File "$b\packages.txt"
adb -s $d shell pm list packages -d       | Out-File "$b\packages-disabled.txt"
adb -s $d shell pm list packages -3       | Out-File "$b\packages-system.txt"
adb -s $d shell dumpsys package com.google.android.tvlauncher > "$b\home.txt"
adb -s $d shell settings list global      | Out-File "$b\settings-global.txt"
adb -s $d shell settings list system      | Out-File "$b\settings-system.txt"
adb -s $d shell getprop                    | Out-File "$b\getprop.txt"
adb -s $d shell cmd package resolve-activity -c android.intent.category.HOME > "$b\home-activity.txt"
```

**Thoát:** có `$b\packages.txt` và `$b\getprop.txt`. File này là cơ sở để **restore thủ công** nếu mọi thứ hỏng.

---

## Bước 4 — Inventory + Memory baseline

```powershell
$apps = adb -s $d shell pm list packages -f -3   # app đã cài
$sys  = adb -s $d shell pm list packages -f -s   # app hệ thống
adb -s $d shell dumpsys meminfo                  | Out-File "$b\meminfo.txt"
adb -s $d shell cat /proc/meminfo                | Out-File "$b\proc-meminfo.txt"
adb -s $d shell df -h /data                      | Out-File "$b\storage.txt"
adb -s $d shell dumpsys deviceidle | Select-String "mState|mLightState"
```

**Thoát:** có `meminfo.txt`. Điền số RAM free vào báo cáo.

---

## Bước 5 — Phân loại 3 danh sách + trình bày

Áp dụng taxonomy §5 trong [`SPEC.md`](SPEC.md) + deny-list trong [`SAFETY.md`](SAFETY.md).

Trình bày cho user **bằng tiếng Anh đơn giản**, đúng 3 nhóm:

```markdown
## Safe to turn off (12)
- Mi Ads — shows ads before you play anything
- Bugsnag — sends crash reports to the maker
- Demo Mode — leftover test app from the factory

## Needed by the TV (never touch)
- Google Play, System UI, Android TV Launcher, Bluetooth, Gboard…

## Your apps (9)
- Netflix, YouTube, Kugou, Zing MP3, …

## Free memory right now
- 512 MB free out of 1 GB (50%)
- Storage: 8.2 GB free of 16 GB
```

> [!TIP]
> Không dùng tên package. Dùng tên app. Người dùng không biết `com.miui.tvads` là gì.

**Thoát:** user đã xem và hiểu 3 danh sách.

---

## Bước 6 — Đề xuất + xin phép (nhóm nhỏ, hỏi nhiều lần)

Đề xuất theo nhóm ≤10 app:

> "Group 1: turn off 5 ad/tracking apps (Mi Ads, GetApps, Bugsnag, Analytics, Data Saver)?
> This will make the TV start faster and stop sending your viewing data. Nothing is deleted — I can turn them back on any time."

Quy tắc hỏi:
- Mỗi nhóm = 1 câu hỏi, có nút Yes/No.
- Nhóm nào chạm soft-guard → hỏi riêng từng app.
- Nhóm nào chạm deny-list → **loại khỏi nhóm**, nói rõ lý do, không hỏi.

**Thoát:** user đã duyệt ít nhất một nhóm (hoặc từ chối hết → kết thúc ở Bước 9).

---

## Bước 7 — Áp dụng (ghi log trước, đổi sau)

```powershell
$targets = @("com.miui.tvads","com.miui.getapps","com.bugsnag.android")
foreach ($t in $targets) {
  # 1) ghi undo-log TRƯỚC
  $log = [ordered]@{
    ts=(Get-Date).ToString("o"); device=$env:DEVICE_IP; profile="android-tv"
    id="chg-$t"; target=$t; action="disable-user"
    approval=@{granted=$true; at=(Get-Date).ToString("o")}
    undo=@{cmd="pm enable $t"; kind="enable"}
    status="pending"
  }
  $log | ConvertTo-Json -Compress | Add-Content "$env:WORKDIR\undo-log.jsonl"

  # 2) rồi mới thay đổi
  adb -s $d shell pm disable-user --user 0 $t
}
```

Sau mỗi lệnh, đọc kết quả; nếu `Error:` → cập nhật `status="failed"` trong log và **dừng nhóm**.

**Thoát:** tất cả app trong nhóm đã báo `disabled-user` hoặc được ghi rõ lỗi.

---

## Bước 8 — Reboot + Verify

```powershell
adb -s $d reboot
Start-Sleep -Seconds 90
adb connect $env:DEVICE_IP:5555
adb -s $d shell pm list packages -d        # đối chiếu: các app đã tắt vẫn tắt?
adb -s $d shell dumpsys meminfo            | Out-File "$b\meminfo-after.txt"
adb -s $d shell cmd package resolve-activity -c android.intent.category.HOME
```

**Thoát:** danh sách disabled khớp, RAM free **không giảm**, HOME vẫn resolve.

---

## Bước 9 — Home screen sạch

Theo profile tương ứng (`profiles/01` hoặc `profiles/04`). Tóm tắt chung:

1. Cài launcher tối giản (đóng gói sẵn, không root).
2. `cmd package set-home-activity <launcher>/.MainActivity`
3. **Giữ launcher gốc ở trạng thái enabled** → undo = chạy lại lệnh set-home về launcher gốc.
4. Tắt animation, screensaver, đặt sleep 5 phút.

```powershell
adb -s $d shell settings put global window_animation_scale 0
adb -s $d shell settings put global transition_animation_scale 0
adb -s $d shell settings put global animator_duration_scale 0
adb -s $d shell settings put secure sleep_timeout 300000     # 5 phút
adb -s $d shell settings put system screen_off_timeout 300000
adb -s $d shell settings put secure screensaver_enabled 0     # hoặc dùng Clock screensaver nếu bật
```

**Thoát:** nhấn HOME ra launcher mới; có clock; không còn hàng quảng cáo; 5 phút không chạm thì màn hình tắt.

---

## Bước 10 — Báo cáo + cách undo

Sinh `reports/<ip>_<yyyyMMdd-HHmm>.md` theo template [`assets/report-template.md`](../assets/report-template.md), gồm:

- RAM/storage **trước và sau**
- Danh sách app đã tắt (tên tiếng Anh + package)
- Cách bật lại: `tools\restore.ps1` hoặc `adb shell pm enable <pkg>`
- Cảnh báo: firmware update có thể đặt lại setting

**Thoát:** file báo cáo tồn tại, user đã đọc phần undo.

---

## Xử lý sự cố

| Triệu chứng | Nguyên nhân | Cách xử lý |
|---|---|---|
| `E_NO_ROUTE` | AP isolation / khác subnet | Cho TV và PC cùng một SSID; tắt "Client isolation" trên router |
| `adb devices` rỗng | Chưa bật ADB hoặc sai IP | Kiểm tra lại Bước 1; thử `adb connect <ip>:5555` lại |
| `unauthorized` | Chưa chấp nhận chữ ký | Trên TV: Allow USB debugging → tick "Always allow" |
| `device offline` | TV vừa khởi động lại | Đợi 30s rồi `adb disconnect`/`connect` |
| TV không quay lại sau reboot | Đang khởi động | Chờ tối đa 3 phút, rồi kiểm tra IP có đổi không (DHCP) |
| `pm disable-user` báo `SecurityException` | App hệ thống quan trọng | Bỏ khỏi nhóm; không ép |
| TV không nhận remote sau khi tắt gì đó | Đã chạm Bluetooth/Input | Rollback ngay bằng `pm enable` qua Bước 1–3 |

---

## Rollback khẩn cấp

```powershell
# Bật lại toàn bộ những gì đã tắt trong phiên này
adb -s $d shell pm list packages -d | Select-String "^(package:)?(com\.miui\.tvads|com\.miui\.getapps)"
# rồi bật từng cái
adb -s $d shell pm enable --user 0 com.miui.tvads
```

Hoặc khôi phục launcher gốc:
```powershell
adb -s $d shell cmd package set-home-activity $(adb -s $d shell cmd package resolve-activity --brief -c android.intent.category.HOME -a android.intent.action.MAIN | Select-Object -Last 1)
```

Nếu mất remote → dùng điện thoại làm remote qua app chính thức của hãng, hoặc rút phích cắm nguồn 30 giây rồi cắm lại.
