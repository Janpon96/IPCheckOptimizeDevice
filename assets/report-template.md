# Báo cáo tối ưu — <TÊN THIẾT BỊ>

**IP:** `192.168.1.50` · **Ngày:** 2026-10-19 14:30 · **Hồ sơ:** `android-tv`

---

## Kết nối

| Mục | Kết quả |
|---|---|
| Kết nối qua | Wi-Fi, ADB `:5555` |
| Model | Xiaomi Mi TV 4A (MiTV-MOOQ1) |
| Android | 10 |
| Bật ADB bằng | Settings → About → Build ×7 → Developer options |

---

## 1. Trước khi thay đổi

**Ứng dụng tổng:** 84 (52 hệ thống, 32 đã cài)

| Nhóm | Số lượng |
|---|---|
| An toàn để tắt | 14 |
| TV cần để giữ | 18 |
| Ứng dụng của bạn | 12 |

### 🟢 An toàn để tắt
| Tên | Package | Vì sao |
|---|---|---|
| Mi Ads | `com.miui.tvads` | quảng cáo trước khi phát |
| GetApps | `com.miui.getapps` | quảng cáo cài app |
| Bugsnag | `com.bugsnag.android` | gửi log lỗi cho hãng |
| Analytics | `com.miui.analyticsd` | theo dõi người dùng |
| Mi Picks | `com.xiaomi.mipicks` | cửa hàng app thừa |

### 🔴 TV cần để giữ (không bao giờ tắt)
Google Play · Play Services · System UI · Android TV Launcher · Bluetooth · Bàn phím · Chuyển nguồn HDMI

### 🔵 Ứng dụng của bạn
Netflix · YouTube · Kugou · Zing MP3 · Spotify · *(+7)*

---

## 2. Bộ nhớ

| | Trước | Sau | Chênh lệch |
|---|---|---|---|
| **RAM trống** | 512 MB / 1 GB (50%) | 690 MB / 1 GB (67%) | **+178 MB** |
| **Dung lượng trống** | 8.2 GB / 16 GB | 8.2 GB / 16 GB | 0 |

> Dung lượng không đổi vì không gỡ cài đặt — chỉ tắt app, nên ổ đĩa giữ nguyên.

---

## 3. Đã thay đổi (12 app)

| # | Tên app | Package | Hành động | Trạng thái | Bật lại bằng |
|---|---|---|---|---|---|
| 1 | Mi Ads | `com.miui.tvads` | tắt | ✅ | `pm enable com.miui.tvads` |
| 2 | GetApps | `com.miui.getapps` | tắt | ✅ | `pm enable com.miui.getapps` |
| 3 | Mi Picks | `com.xiaomi.mipicks` | tắt | ✅ | `pm enable com.xiaomi.mipicks` |
| 4 | Analytics | `com.miui.analyticsd` | tắt | ✅ | `pm enable com.miui.analyticsd` |
| 5 | Bugsnag | `com.bugsnag.android` | tắt | ✅ | `pm enable com.bugsnag.android` |
| 6 | Mi Cloud Play | `com.miui.tvhome.cloudplay` | tắt | ✅ | `pm enable com.miui.tvhome.cloudplay` |
| 7 | Joyose | `com.xiaomi.joyose` | tắt | ✅ | `pm enable com.xiaomi.joyose` |
| 8 | Mi Player | `com.miui.player` | tắt | ✅ *(bạn đã đồng ý)* | `pm enable com.miui.player` |
| 9–12 | *(4 app khác)* | | tắt | ✅ | |

### Cài đặt đã chỉnh

| Mục | Trước | Sau |
|---|---|---|
| Animation | Bật | **Tắt** |
| Screensaver | Có | **Tắt** |
| Tắt màn hình | 15 phút | **5 phút** |
| Màn hình chính | Google TV launcher (có quảng cáo) | **Launcher sạch + đồng hồ** |

> Launcher gốc **vẫn được giữ ở trạng thái bật** → quay lại được bằng 1 lệnh.

---

## 4. Cách hoàn tác

### Bật lại một app
```powershell
adb -s 192.168.1.50:5555 shell pm enable --user 0 com.miui.tvads
```

### Bật lại tất cả app trong phiên này
```powershell
adb -s 192.168.1.50:5555 shell pm enable --user 0 com.miui.tvads
adb -s 192.168.1.50:5555 shell pm enable --user 0 com.miui.getapps
# ... lần lượt theo bảng ở mục 3
```

### Quay lại launcher gốc
```powershell
adb -s 192.168.1.50:5555 shell cmd package set-home-activity `
  com.google.android.tvlauncher/com.google.android.tvlauncher.HomeActivity
```

### Trả cài đặt về mặc định
```powershell
adb -s 192.168.1.50:5555 shell settings put global window_animation_scale 1
adb -s 192.168.1.50:5555 shell settings put secure sleep_timeout 1800000
```

Nhật ký đầy đủ: `undo-log.jsonl` · Ảnh chụp trước khi sửa: `backups/20261019-1430/`

---

## 5. Kiểm chứng sau reboot

- [x] Khởi động lại xong TV vẫn lên bình thường
- [x] 12 app vẫn tắt
- [x] Remote vẫn dùng được (Bluetooth nguyên vẹn)
- [x] Chuyển nguồn HDMI vẫn hoạt động
- [x] Remote phản hồi nhanh hơn

---

## 6. Lưu ý

> [!WARNING]
> **Cập nhật phần mềm máy có thể gỡ bỏ các thay đổi trên.** Nếu TV tự cập nhật, hãy chạy lại quy trình verify.

> [!TIP]
> **Không cài app đã tắt lại trừ khi bạn cần.** Bản cập nhật ứng dụng thường bật lại service của nó.
