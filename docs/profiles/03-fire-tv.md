# Profile 03 — Amazon Fire TV (Fire OS)

**Capability: `PARTIAL`** · Transport: ADB TCP `:5555`

> [!IMPORTANT]
> Fire OS **không cho phép** app bên thứ ba chiếm quyền Home. Không thể thay launcher. Chỉ debloat + settings được.

## 1. Kết nối

```
Settings → My Fire TV → Developer Options → ADB Debugging = ON
→ Network ADB debugging = ON (nếu có) → giữ Fire TV bật
```
```powershell
adb connect 192.168.1.60:5555 ; adb devices
```

## 2. Không bao giờ tắt

```
com.amazon.tv.launcher         launcher
com.amazon.device.controllermanager   remote Alexa / nút điều khiển
com.amazon.hdcp             cặp thiết bị
com.amazon.device.controllermanager
com.amazon.alexa
com.amazon.tv.input          chuyển nguồn HDMI
```

## 3. Ứng viên tắt (Fire OS 7 / Android 9, model `duckie` đã test)

```
com.amazon.advertising       quảng cáo Amazon      ★ tắt
com.amazon.metrics           telemetry              ★ tắt
com.amazon.device.metrics    telemetry              ★ tắt
com.amazon.crowd             góp ý tập thể         ★ tắt
com.amazon.shoppingapp       Amazon Shopping       hỏi
com.amazon.venezia           Fire TV Experience    hỏi
com.amazon.mShop.android.shopping                 hỏi
com.amazon.mpui              trình phát media      giữ nếu dùng
com.amazon.svm               Secure Video Manager   giữ
com.amazon.tv.recommendations đề xuất nội dung      hỏi
com.amazon.video.watchingactivity                giữ
```

## 4. Tắt hàng đề xuất & quảng cáo ở launcher

```powershell
# Ẩn hàng "Recommended"
adb -s $d shell settings put global com.amazon.tv.launcher.landingpage.hide_recommended true
# Hoặc tắt hẳn dịch vụ đề xuất (nếu user đồng ý)
adb -s $d shell pm disable-user --user 0 com.amazon.tv.recommendations
```

## 5. Settings

```powershell
adb -s $d shell settings put global window_animation_scale 0
adb -s $d shell settings put global transition_animation_scale 0
adb -s $d shell settings put global animator_duration_scale 0
adb -s $d shell settings put system screen_off_timeout 300000
```

## 6. Memory

```powershell
adb -s $d shell cat /proc/meminfo | Select-String "MemTotal|MemAvailable"
adb -s $d shell dumpsys meminfo | Select-String "Total RAM|Free RAM"
```

## 7. Verify
```powershell
adb -s $d reboot ; Start-Sleep 90 ; adb connect 192.168.1.60:5555
adb -s $d shell pm list packages -d
adb -s $d shell input keyevent 3
```

## 8. Giới hạn cần nói rõ với user

> Fire TV không cho cài launcher thay thế. Tôi có thể tắt quảng cáo, telemetry và app không cần — nhưng màn hình chính vẫn là của Amazon, và có thể còn hàng "Recommended". Muốn xoá hẳn hàng đó thì cần root hoặc chặn ở tầng DNS.
