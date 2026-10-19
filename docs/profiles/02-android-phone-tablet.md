# Profile 02 — Android điện thoại / Máy tính bảng

**Capability: `FULL`** · Transport: ADB TCP `:5555`

> [!IMPORTANT]
> Điện thoại là thiết bị cá nhân. Mặc định **rủi ro cao hơn TV**: mất launcher, mất bàn phím, mất thoại gọi khẩn cấp. Chỉ tắt app bạn *chắc chắn* không dùng, và luôn giữ mục `core` bất di bất dịch.

## 1. Kết nối

```
Settings → About phone → nhấn Build 7 lần
→ Settings → System → Developer options → USB debugging = ON
```
```powershell
adb connect 192.168.1.77:5555 ; adb devices
```

## 2. Không bao giờ tắt (mở rộng so với TV)

| Package | Lý do |
|---|---|
| `com.android.phone` | ứng dụng điện thoại |
| `com.android.dialer` / `com.google.android.dialer` | gọi thoại |
| `com.android.emergency` | gọi khẩn cấp |
| `com.android.server.telecom` | dịch vụ viễn thông |
| `com.google.android.apps.messaging` | **SMS** |
| `com.android.bluetooth` | tai nghe/đồng hồ |
| `com.google.android.inputmethod.latin` | bàn phím |
| `com.android.camera` / `com.google.android.GoogleCamera` | camera |
| `com.google.android.gms` | Play Services |
| `com.android.vending` | Play Store |
| `com.android.shell` | adb |
| `com.google.android.apps.wellness` / `digitalwellbeing` | có thể tắt nếu không dùng |
| launcher của OEM | `com.miui.home`, `com.samsung.android.app.launcher`, `com.android.launcher3`, `com.oppo.launcher`… |

## 3. Ứng viên tắt

### Nền tảng
```
com.google.android.apps.wellness      sức khoẻ số
com.google.android.feedback           báo cáo lỗi
com.google.android.apps.walletnfcrel  Google Wallet (nếu không dùng)
com.android.dreams.basic              screensaver (nếu không dùng)
```

### Nhà sản xuất
```
com.xiaomi.mipicks        com.miui.analyticsd
com.miui.bugreport        com.miui.player
com.samsung.android.app.tips          gợi ý Samsung
com.samsung.android.app.watchmanager  (giữ nếu dùng đồng hồ)
com.samsung.android.app.settings     (giữ)
com.oppo.dataus           com.coloros.dataus
```

### Ứng dụng bạn tự cài
```
adb -s $d shell pm list packages -3      # chỉ app người dùng cài
```

## 4. Đọc RAM thực tế

```powershell
adb -s $d shell cat /proc/meminfo | Select-String "MemTotal|MemAvailable"
adb -s $d shell dumpsys meminfo com.android.systemui | Select-String "TOTAL"
adb -s $d shell dumpsys batterystats | Select-String "Estimated battery capacity"
adb -s $d shell df -h /data
```

## 5. Tối ưu pin + hiệu năng

```powershell
# Giới hạn app chạy nền (Android cũ)
adb -s $d shell settings put global always_finish_activities 1
# Danh sách app được phép chạy nền — backup trước!
adb -s $d shell dumpsys deviceidle whitelist
adb -s $d shell cmd appops set com.android.vending RUN_IN_BACKGROUND ignore
```

> [!WARNING]
> `always_finish_activities 1` **làm app mở lại chậm hơn**. Chỉ dùng nếu user chủ động chấp nhận đánh đổi này.

## 6. Verify

```powershell
adb -s $d reboot ; Start-Sleep 60 ; adb connect 192.168.1.77:5555
adb -s $d shell pm list packages -d
adb -s $d shell cmd package resolve-activity -c android.intent.category.HOME
adb -s $d shell input keyevent 3            # nhấn HOME bằng adb
```

## 7. Rollback
```powershell
adb -s $d shell pm enable --user 0 <package>
adb -s $d shell settings put global always_finish_activities 0
```
