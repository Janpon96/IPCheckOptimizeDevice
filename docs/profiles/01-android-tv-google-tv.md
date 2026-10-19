# Profile 01 — Android TV / Google TV

**Capability: `FULL`** · Transport: ADB TCP `:5555`

Áp dụng cho mọi TV chạy Android TV / Google TV: Xiaomi, Redmi, TCL, Hisense, Sony, OnePlus, Realme, NVIDIA Shield, BenQ, CHiQ, SANYO, RCA.

> Nguồn danh sách app đã test thật: [`Gathin23/tv-vibehack/examples/`](https://github.com/Gathin23/tv-vibehack/tree/main/examples)

## 1. Kết nối

```
Settings → Device Preferences → About → OK 7 lần vào "Build"
→ Developer options → USB debugging = ON
→ Network debugging = ON (nếu có) → giữ TV bật sáng
```
```powershell
adb connect 192.168.1.50:5555 ; adb devices
```

## 2. Nhận diện nhanh

```powershell
adb -s $d shell getprop ro.product.model
adb -s $d shell getprop ro.build.version.release
adb -s $d shell pm list features | Select-String "leanback"
```

## 3. App **không bao giờ** tắt

```
com.google.android.tvlauncher      com.google.android.leanback
com.android.vending                com.google.android.gms
com.android.systemui               com.android.settings
com.android.bluetooth              com.google.android.inputmethod.latin
com.android.tv.leanback            com.google.android.apps.mediashell
com.miui.home / com.miui.tv.home  com.tcl.tvlauncher
com.hisense.*launcher*             com.sony.*launcher*
```

## 4. Ứng viên tắt theo hãng

### Xiaomi / Redmi (Mi TV, MiTV-MOOQ0, MOOQ1, AXSO0, dangal, venom, aquaman)
```
com.miui.tvads                 quảng cáo đầu màn hình
com.miui.tvhome.cloudplay      dịch vụ đám mây không dùng
com.xiaomi.mipicks             cửa hàng app riêng (nếu đã có Play Store)
com.miui.getapps               quảng cáo cài app
com.miui.bugreport              gửi log
com.miui.analyticsd             theo dõi
com.xiaomi.joyose              điều khiển từ xa Xiaomi
com.duokan.player              trình phát tích hợp
com.nimo.video                 app hãng
com.miui.videoplayer            phát video mặc định
com.miui.player                phát nhạc mặc định
```

### Google TV / AOSP (TCL, Sony, Hisense, Shield)
```
com.google.android.adservices   (chỉ tắt nếu user không dùng quảng cáo)
com.google.android.apps.wellness
com.google.android.apps.dream   screensaver (nếu không muốn dùng)
com.google.android.youtube.tv   (CHỈ nếu user không dùng YouTube)
```

### Shield / chung
```
com.nvidia.app.nvshield         telemetry (giữ nếu dùng GeForce NOW)
```

> [!WARNING]
> **Luôn hỏi user trước.** Danh sách trên là *ứng viên*, không phải quyết định. `com.miui.player` chẳng hạn — một số người dùng nghe nhạc qua TV.

## 5. Đo memory

```powershell
adb -s $d shell cat /proc/meminfo | Select-String "MemTotal|MemAvailable"
adb -s $d shell dumpsys meminfo | Select-String "Total RAM|Free RAM|Used RAM"
```

## 6. Home screen sạch

### 6.1 Launcher tối giản (khuyến nghị)
Cài launcher kiểu Apple TV (pitch-black, clock, dock app, không quảng cáo). Xem cách build trong [`tv-vibehack`](https://github.com/Gathin23/tv-vibehack).

```powershell
adb -s $d install -r tv-launcher.apk
adb -s $d shell cmd package set-home-activity <pkg>/<activity>
```

> [!IMPORTANT]
> **Không disable launcher gốc.** Giữ nó `enabled` → undo chỉ cần chạy lại `set-home-activity`.

### 6.2 Nếu không cài launcher mới
Dọn home screen của launcher gốc bằng cách tắt nguồn nội dung:
```powershell
# Ẩn hàng đề xuất / quảng cáo ở launcher Google TV
adb -s $d shell pm disable-user --user 0 com.google.android.katniss   # Home Screen Search
```
> Chỉ dùng khi user xác nhận không còn dùng tìm kiếm trên home.

## 7. Settings tối ưu

```powershell
adb -s $d shell settings put global window_animation_scale 0
adb -s $d shell settings put global transition_animation_scale 0
adb -s $d shell settings put global animator_duration_scale 0
adb -s $d shell settings put secure sleep_timeout 300000
adb -s $d shell settings put system screen_off_timeout 300000
adb -s $d shell settings put secure screensaver_enabled 0
```

## 8. Verify sau reboot

```powershell
adb -s $d reboot ; Start-Sleep 90 ; adb connect 192.168.1.50:5555
adb -s $d shell pm list packages -d | Measure-Object -Line     # so sánh với trước
adb -s $d shell cmd package resolve-activity -c android.intent.category.HOME
adb -s $d shell cat /proc/meminfo | Select-String "MemAvailable"
```

## 9. Rollback

```powershell
adb -s $d shell pm enable --user 0 <package>
# hoặc
adb -s $d shell cmd package set-home-activity com.google.android.tvlauncher/com.google.android.tvlauncher.HomeActivity
```
