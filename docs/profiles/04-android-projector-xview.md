# Profile 04 — Máy chiếu Android / Xview / PONT / DVB

**Capability: `FULL`** · Transport: ADB TCP `:5555` (thường **đã mở sẵn** ở `:5555` hoặc `:23`)

Máy chiếu Android dùng chung nền tảng TV nhưng có điểm khác biệt lớn: **nhiều app OEM rác hơn TV**, và **bản cập nhật chết** (không có nguồn OTA). Vì vậy `settings put` ổn định hơn TV thường.

## 1. Kết nối

Nhiều máy chiếu Xview/PONT **bật ADB sẵn qua Wi-Fi**. Thử trực tiếp:

```powershell
adb connect 192.168.1.90:5555 ; adb devices
# Nếu không được, thử :5555, :23, :22, :8000
```
> [!TIP]
> Dò đúng cổng: `Test-NetConnection 192.168.1.90 -Port 5555, 23, 22, 8000`

Nếu không có cổng nào mở:
```
Settings → About → Build 7 lần → Developer options → USB debugging = ON
```

## 2. Nhận diện (CAA PONT / Xview)

```powershell
adb -s $d shell getprop ro.product.manufacturer
adb -s $d shell getprop ro.build.display.id
adb -s $d shell getprop | Select-String "xview|pont|caabus|dvb|tchip|amlogic|rockchip|allwinner"
```

| Tín hiệu | Họ |
|---|---|
| `caabus`, `CAA PONT` | Cốc Cốc SmartCast / Vietcast |
| `Xview`, `DVB96BQ`, `DVB93CQ` | Vietcast / Xview |
| `tchip`, `amlogic` | Amlogic SoC |
| `rockchip` | Rockchip |

## 3. Không bao giờ tắt (mở rộng vì input của máy chiếu phức tạp)

```
com.android.launcher / com.android.launcher3    launcher gốc
com.android.vending              com.google.android.gms
com.android.systemui             com.android.settings
com.android.bluetooth            (remote)
com.google.android.inputmethod.latin
com.android.tv.leanback / com.htc.*hdmi        chuyển nguồn
com.rockchip.* / com.amlogic.* / com.allwinner.*
   ↑ PHẦN MỀM GIẢI MÃ HDMI / HDMI-CEC — TUYỆT ĐỐI GIỮ
```

> [!WARNING]
> Trên máy chiếu, **HDMI-CEC và bộ giải mã hình ảnh thường nằm trong package của nhà sản xuất** (`com.amlogic.*`, `com.rockchip.*`, `tchip`). Tắt sai một package ở đây = mất tín hiệu hình ảnh. Nếu không chắc package nào thuộc nhóm này thì **bỏ qua luôn**.

## 4. Ứng viên tắt

```
com.iptv.*                     IPTV tích hợp (hỏi user trước — nhiều người xem TV)
com.example.*                  app mẫu của nhà sản xuất
com.demo.*                     demo
com.test.*                     app test
com.cact.* / com.app.*         app OEM lạ
com.qiyi.video / com.qqlive    dịch vụ Trung Quốc (nếu không dùng)
com.android.broshub.*          thương mại
*analytics* *tracking* *telemetry* *ads*
com.google.android.katniss     tìm kiếm home screen
```

## 5. Xem app đã cài (thường ít, dễ đọc)

```powershell
adb -s $d shell pm list packages -3 -f      # app user cài
adb -s $d shell pm list packages -s -f      # app hệ thống
adb -s $d shell cmd package list packages -i   # package -> label
```

## 6. Memory & storage

```powershell
adb -s $d shell cat /proc/meminfo | Select-String "MemTotal|MemAvailable"
adb -s $d shell df -h /data
adb -s $d shell dumpsys meminfo | Select-String "Free RAM|Used RAM"
```

## 7. Home screen sạch

Giống [`01-android-tv-google-tv.md`](01-android-tv-google-tv.md) §6–§7:
- Cài launcher tối giản → `set-home-activity`, **giữ launcher gốc enabled**
- Tắt animation, screensaver, sleep 5 phút

## 8. Verify & rollback
```powershell
adb -s $d reboot ; Start-Sleep 90 ; adb connect 192.168.1.90:5555
adb -s $d shell pm list packages -d
adb -s $d shell input keyevent 3
adb -s $d shell pm enable --user 0 <package>
```

## 9. Ghi chú quan trọng về máy chiếu

| Vấn đề | Xử lý |
|---|---|
| Không có nguồn cập nhật → setting bền vững | Tốt: đổi còn lại lâu dài |
| Bộ nhớ trong thấp (512MB–1GB) | Đo trước, báo cáo rõ mức cải thiện |
| Không có OTA → không cần lo firmware reset | Nói với user: thay đổi của bạn sẽ không bị mất |
| Bộ remote đôi khi là app riêng | Hỏi user trước khi tắt app remote |
