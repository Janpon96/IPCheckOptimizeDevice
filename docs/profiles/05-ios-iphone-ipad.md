# Profile 05 — iPhone / iPad (iOS)

**Capability: `PARTIAL`** · Transport: `pymobiledevice3` qua Wi-Fi (USB pairing một lần) hoặc Apple Configurator

> [!IMPORTANT]
> iOS **không cho phép** tắt app hệ thống. Cách duy nhất để "dọn" là **xoá app không dùng** (xoá được cài lại từ App Store). Vì vậy quy tắc "không uninstall" **không áp dụng được** ở đây — phải nói rõ với user trước.

## 1. Chuẩn bị (trên Windows)

```powershell
pip install pymobiledevice3
pymobiledevice3 usbmux list
# Pair một lần qua USB, sau đó có thể dùng Wi-Fi
pymobiledevice3 lockdown start-remote-service
```

## 2. Bật Developer Mode trên iPhone

```
Settings → Privacy & Security → Developer Mode → ON → Restart
```

## 3. Nhận diện & đọc thông tin

```powershell
pymobiledevice3 lockdown info
pymobiledevice3 apps list          # toàn bộ app đã cài
pymobiledevice3 apps list --system  # app hệ thống
pymobiledevice3 processes list      # tiến trình đang chạy
pymobiledevice3 diagnostics ioreg   # phần cứng, RAM
```

## 4. Những gì **thực sự làm được**

| Việc | Cách | Tự động? |
|---|---|---|
| Liệt kê app | `apps list` | ✅ |
| Xoá app người dùng cài | hướng dẫn long-press → Remove App | ❌ tap tay |
| Tắt chạy nền / Location | hướng dẫn Settings → General → Background App Refresh | ❌ |
| Bật Low Power Mode | hướng dẫn Settings → Battery | ❌ |
| Đọc RAM / storage | `diagnostics` hoặc hướng dẫn Settings → General → iPhone Storage | ⚠️ một phần |
| Tắt Background App Refresh | tap tay | ❌ |

## 5. Ứng viên "dọn" — chỉ app người dùng cài

```powershell
pymobiledevice3 apps list | Select-String -NotMatch "com.apple."
```

Đề xuất xoá app **chỉ khi**:
- Không mở trong ≥6 tháng
- Dung lượng lớn (>500MB)
- User xác nhận không dùng

> [!WARNING]
> **Không bao giờ xoá app Apple hệ thống.** Danh sách đen tuyệt đối: Settings, Safari, Messages, Camera, Phone, Health, Home, Find My, Wallet, Apple TV, AirPlay/Mirroring, Files, Calculator, Compass, Podcasts, App Store, Books, Clock, Contacts, FaceTime, Files, Find My Friends, Freeform, Journal, Mail, Maps, Messages, Music, News, Notes, Passwords, Phone, Photos, Podcasts, Reminders, Safari, Shortcuts, Stocks, TV, Voice Memos, Wallet, Watch, Weather.

## 6. Memory baseline (iOS không công khai con số "free")

Đo thay thế bằng **dung lượng trống**:

```
Settings → General → iPhone Storage
→ chụp ảnh mục "Available" trước
→ xoá app → chụp lại sau
```

Báo cáo bằng **GB trống trước / sau**, đừng bịa "RAM free".

## 7. Bảo vệ điều kiện bắt buộc cho iOS

| Hạng mục | Vì sao giữ |
|---|---|
| Apple TV app | điều khiển TV từ iPhone |
| AirPlay & Mirroring | chiếu màn hình lên TV |
| Bluetooth | AirPods, Apple Watch, remote TV |
| Home app | điều khiển thiết bị nhà |
| Find My | bảo mật, khóa iCloud |
| Tất cả app "Input/Source" của TV/loa | chuyển nguồn |

## 8. Cách hỏi user cho profile này

Vì phần lớn việc là tap tay, hãy nói rõ:

> "Trên iPhone tôi không tắt được app hệ thống từ xa — Apple không cho phép. Tôi có thể chỉ cho bạn danh sách app nên xoá để giải phóng dung lượng, bạn xoá trong 5 giây, hoặc tôi hướng dẫn tắt cập nhật nền. Bạn muốn bắt đầu từ cái nào?"

## 9. Rollback

iOS: cài lại từ App Store / iCloud. Không có trạng thái "tắt" để hoàn tác — **đây là lý do phải hỏi kỹ trước mỗi lần xoá**.
