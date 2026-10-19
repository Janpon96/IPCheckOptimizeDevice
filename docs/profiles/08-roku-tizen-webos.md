# Profile 08 — Roku TV / Samsung Tizen / LG webOS

**Capability: `PARTIAL` → `FULL` (chỉ Roku)** · Transport: Roku ECP HTTPS `:8060`

Ba hệ điều hành này **không phải Android** → không có ADB, không có `pm disable`. Cách tiếp cận khác hẳn.

| Nền tảng | Có API quản trị qua IP? | Có thể làm gì tự động |
|---|---|---|
| **Roku** (Roku OS / TV OS) | ✅ ECP `:8060` | Đọc danh sách app, đổi screensaver, cài app từ sideload |
| **Samsung Tizen** | ❌ (có `samsungtv` API nhưng cần art server pairing) | Chỉ hướng dẫn tap |
| **LG webOS** | ❌ | Chỉ hướng dẫn tap |

---

## A. Roku

### A.1 Kết nối

Roku luôn mở ECP ở `https://<IP>:8060`:

```powershell
# Kiểm tra
Invoke-RestMethod "http://192.168.1.70:8060/query/device-info"
# Lấy danh sách app đã cài
(Invoke-RestMethod "http://192.168.1.70:8060/query/apps").children
```

### A.2 Đọc thông tin & app

```powershell
$r = "http://192.168.1.70:8060"
(Invoke-RestMethod "$r/query/device-info").device | Select-Object model, friendlyDeviceName, softwareVersion
(Invoke-RestMethod "$r/query/active-app").activeApp
(Invoke-RestMethod "$r/query/apps").children | ForEach-Object { "$($_.'#text')  <- $($_.id)  appname=$($_.appname)" }
```

### A.3 Những gì làm được (không cần hỏi nhiều, nhưng **vẫn hỏi trước**)

#### Đổi screensaver thành màn hình đen (tiết kiệm điện, không burn-in)
```powershell
Invoke-RestMethod "$r/keypress/LaunchScreenSaver"   # xem hiện tại
# Ghi setting screensaver
$body = 'pkgs/11/settings/display.screensaver.json'
$json = '{"value":"black"}'
Invoke-RestMethod -Method Post -Uri "$r/keypress/$body" -Body $json -ContentType "application/json"
```

#### Bật/tắt hàng quảng cáo ở Home
```powershell
# "What to watch" row (Roku OS 11+)
Invoke-RestMethod "$r/query/tv-active-channel" | Out-Null   # kiểm tra kênh đang hoạt động
# Tắt hàng đề xuất: Settings > Home screen > Recommended rows (trên TV) hoặc ECP:
$json = '{"value":"false"}'
Invoke-RestMethod -Method Post -Uri "$r/keypress/pkgs/11/settings/home.recommended.json" -Body $json -ContentType "application/json"
```

#### Bật/tắt "Data Saver"
```powershell
# Settings > Network > Data Saver  (giảm băng thông)
$json = '{"value":"true"}'
Invoke-RestMethod -Method Post -Uri "$r/keypress/pkgs/11/settings/networking.datasaver.json" -Body $json -ContentType "application/json"
```

#### Đặt thời gian sleep
```powershell
# Settings > System > Power > Sleep  (đặt sau khi không dùng)
$json = '{"value":"900000"}'   # milliseconds = 15 phút
Invoke-RestMethod -Method Post -Uri "$r/keypress/pkgs/11/settings/power.sleep.json" -Body $json -ContentType "application/json"
```

> [!IMPORTANT]
> **Không tắt được app đã cài trên Roku** qua ECP. Muốn gỡ thì tap trên TV: Home → highlight app → ★ → Remove App. Đây là giới hạn thật, nói rõ với user.

### A.4 Danh sách "không được chạm" trên Roku

```
MediaPlayer            (ứng dụng đang phát)
Roku Remote            (điều khiển từ xa)
Roku SceneGraph        (Home)
system.screen_saver    (nếu muốn dùng Clock screensaver)
system.theme
```

### A.5 Rollback
```powershell
# Trả setting về mặc định
Invoke-RestMethod "$r/keypress/Exec.xbb.ViewChangeFactory" -Method Post
# hoặc đơn giản: trên TV → Settings → System → Factory Reset (xem trước khi làm)
```

---

## B. Samsung Tizen

**Không có API mở.** Chỉ hướng dẫn tap.

```
Smart Hub → phím mũi tên lên trên → Settings (⚙)
  ├─ General → System        → Auto Update = Off
  ├─ General → Smart Hub      → Auto Run Broadcasting App = Off
  │                           → (bỏ chọn các app ở hàng "Recent")
  ├─ Picture                 → (không liên quan tối ưu)
  ├─ Sound                   → (không liên quan)
  ├─ System → Sleep Timer     → bật, đặt 5 phút (Settings > General > System > Sleep Timer)
  ├─ Accessibility           → (xem mục C)
  └─ Support → Software Update → Auto Update = Off
```

**Dọn app Samsung tích hợp:** Home → Apps → dùng nút tắt trên remote để đánh dấu app không dùng.

**Cách hỏi user:**
> "Samsung không cho tôi điều khiển từ xa — tôi sẽ chỉ bạn từng nút để tắt cập nhật tự động, tắt app tự chạy và đặt tắt màn hình sau 5 phút. Bạn có thể dừng lại bất cứ lúc nào. Sau đó tôi sẽ chỉ bạn nén danh sách app để gỡ ứng dụng bạn không dùng."

---

## C. LG webOS

**Không có API mở.** Chỉ hướng dẫn tap.

```
Magic Remote → ⚙ (Settings)
  ├─ General
  │   ├─ Time & Date → Automatic = Off  (giảm truy cập server)
  │   ├─ Quick Start  = OFF          (tắt app chạy nền, giải phóng RAM)
  │   ├─ Network → (xem D)
  │   └─ TV Power Behavior → "Standby" (thay vì "Never")  hoặc dùng Sleep Timer
  ├─ System → Auto Update = Off
  └─ Accessibility → (tuỳ chọn)
```

**Gỡ app trên webOS:**
```
Home / Launcher → Apps → nhấn ⚙ trên app → Delete
```

**Tắt quảng cáo trên màn hình chờ (webOS 22+):**
```
Settings → General → Additional Settings → "Customize TV"
→ hoặc Home → dùng Remote "Edit Mode" → bỏ các hàng đề xuất / quảng cáo
```

**Cách hỏi user:**
> "LG cũng không mở API cho tôi. Tôi sẽ hướng dẫn bạn tắt Quick Start (giải phóng RAM), tắt cập nhật tự động, và đặt tắt màn hình sau 5 phút. Phần gỡ app bạn phải làm trên TV."

---

## D. Tầng router — chặn quảng cáo cho Tizen/webOS

Vì không thể tắt quảng cáo trong máy, DNS filter là cách hiệu quả nhất:

```text
# Samsung
*.samsungadhub.com
*.samsungads.com
*.smaticad.com
config.samsungads.com
samsungacr.com
adservice.samsungqbe.com

# LG
*.lge.com/ad
ad.lg.com
*.lgadplatform.com
m.lgadplatform.com
re.lgadplatform.com
lcdn.lge.com  (chỉ khi xác nhận không phá)
```

> [!TIP]
> **Bắt đầu với DNS filter (Pi-hole/AdGuard), không dùng firewall.** DNS filter dễ gỡ, không khóa nhầm, và áp dụng cho *mọi* thiết bị trong nhà.

## E. "Memory"

Không đo được bằng lệnh. Hướng dẫn user:
- **Samsung:** Settings → Support → Device Care → Memory (làm mới)
- **LG:** đặt timer và xem TV có nhận được phản hồi nhanh hơn không

Báo cáo bằng **quan sát cảm nhận được** (remote phản hồi nhanh hơn, không còn khung hình lúc chuyển kênh) thay vì số liệu giả.
