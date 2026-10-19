# Profile 07 — Nintendo 3DS / 2DS / DS / 2DS XL

**Capability: `MANUAL`** · Transport: **không có** (cả 3DS và DS đều hoạt động offline-first)

> [!IMPORTANT]
> Cả 3DS và DS đều **không có tính năng Wi-Fi tắt hoàn toàn** trên hầu hết model (3DS có Wi-Fi bật sẵn, không có nút tắt thật). Đây là giới hạn phần cứng — nói rõ với user thay vì hứa tắt được.

## 1. Những gì làm được trong máy

| Mục tiêu | Cách làm | Tự động? |
|---|---|---|
| Tắt Internet bằng cách **quên** (không xoá) | System Settings → Internet Settings → Manual → bỏ cấu hình | ❌ tap |
| Dọn dữ liệu tải về | System Settings → Management → Data Management → Nintendo 3DS Data Management | ❌ tap |
| Tắt StreetPass | System Settings → StreetPass Mii → Off | ❌ tap |
| Tắt SpotPass | System Settings → Internet Settings → SpotPass → Off | ❌ tap |
| Giảm độ sáng tối thiểu | System Settings → Screen Brightness → thấp nhất | ❌ tap |
| 3DS: tắt thông báo bốn mươi phút | Internet Settings → Notifications → Off | ❌ tap |
| 3DS: xem tài khoản Nintendo | Settings → Nintendo Account → Stop Using Account (đăng xuất, không xoá) | ❌ tap |

## 2. Hướng dẫn tap — Nintendo 3DS / New Nintendo 3DS

```
HOME → System Settings
  ├─ Internet Settings
  │   ├─ Internet Browser     → (không dùng thì để nguyên)
  │   ├─ Nintendo eShop       → Off
  │   ├─ SpotPass             → Off
  │   └─ Notifications        → Off
  ├─ StreetPass Mii          → Off
  ├─ Screen Brightness       → mức thấp nhất (giảm tải cho mắt)
  └─ Management
      ├─ System Update       → Automatic Updates = Off
      └─ Data Management     → dọn dữ liệu tải về (xem cảnh báo bên dưới)
```

### Nintendo 2DS
```
HOME → System Settings → Internet Settings → tạo profile / xoá profile
→ StreetPass Mii → Off
→ Screen Brightness → thấp nhất
```

## 3. Nintendo DS (DS Lite / DSi / DSi XL)

DS **không có Internet Browser** (chỉ DSi mới có, rất hạn chế).

```
DS Lite:  không có Wi-Fi      → không có gì để tối ưu mạng
DSi / DSi XL:
  SYSTEM SETTINGS → INTERNET SETTINGS → phải tạo một profile trước
  ── nếu chưa có profile, chưa làm gì được ở đây ──
  Sau khi có profile → chỉnh Proxy → Manual → (không cần, offline)
  SYSTEM SETTINGS → SYSTEM → Brightness (nút +/- trên màn hình chính)
```

## 4. Cảnh báo trước khi dọn Data Management

> [!WARNING]
> **Data Management xoá vĩnh viễn:** dữ liệu tải về, phần mềm đã cài, và ảnh chụp trong album. **Không khôi phục được.**
> Chỉ làm khi user hiểu rõ. Với DS/3DS, hãy ưu tiên **dọn thẻ microSD** thay vì dọn bộ nhớ trong.

## 5. Tầng router — chặn Nintendo hoàn toàn

Vì không tắt được Wi-Fi trong máy, cách đúng là **chặn ở router**:

```text
# Nintendo
*.nintendo.net
lgt.api.nintendo.net
na.api.nintendo.com
soc.cdn.nintendo.net
*.nintendo.co.jp
nintendo3ds.nintendo.com

# StreetPass / SpotPass (server định vị)
*.nintendo.net/spotpass
*.locator.nintendo.com
```

Cách chặn hiệu quả nhất cho console cầm tay:
1. **Tạo VLAN riêng** hoặc **AP khác** cho thiết bị cầm tay
2. Trong VLAN đó: chặn toàn bộ outbound, chỉ cho phép nội bộ
3. Như vậy console vẫn dùng được offline (game, video) mà không bao giờ gọi ra ngoài

## 6. "Memory" — cách đo thay thế

| Thiết bị | Cách đo |
|---|---|
| 3DS | System Settings → Management → Data Management → xem dung lượng trống |
| 2DS | không có màn hình báo — dùng card SD trên máy tính |
| DS | không báo — dùng card DS |

> Không có con số "RAM free" nào đáng tin cậy trên 3DS/DS. Báo cáo bằng **dung lượng trống** và nói rõ đó là điều duy nhất đo được.

## 7. Cách hỏi user

> "Máy cầm tay của bạn không có cách tắt Wi-Fi thật sự — Nintendo thiết kế vậy. Tôi có thể chỉ bạn tắt SpotPass, StreetPass và thông báo trong máy (5 phút), và chặn Nintendo ở router để nó không bao giờ gọi ra ngoài. Phần chặn ở router thì tôi làm được và hoàn tác bằng cách xoá một dòng. Bạn muốn làm cái nào?"

## 8. Rollback
- **Trong máy:** mở lại toggle đã tắt; cấu hình lại profile internet
- **Router:** xoá domain khỏi adlist; bật lại outbound cho VLAN
- **Dữ liệu đã dọn:** không khôi phục được — nói trước khi làm
