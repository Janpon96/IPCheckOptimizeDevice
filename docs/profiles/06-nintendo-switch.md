# Profile 06 — Nintendo Switch

**Capability: `MANUAL`** · Transport: **không có admin API qua IP**

> [!IMPORTANT]
> Switch **không có bất kỳ API quản trị nào** qua mạng. Không root, không homebrew, không jailbreak — và những thứ đó đều nằm ngoài phạm vi của dự án này.
> Cách duy nhất hợp lệ: **hướng dẫn tap trong máy + can thiệp ở tầng router.**

## 1. Những gì thực sự tối ưu được

| Mục tiêu | Cách làm | Tự động? |
|---|---|---|
| Tắt tự cập nhật firmware | System Settings → System → Update Software | ❌ tap |
| Giảm dung lượng trong máy | Xoá game/video đã chơi xong | ❌ tap |
| Tắt tự kết nối Wi-Fi khi ở gần router | Network Settings → Auto-Connect OFF | ❌ tap |
| **Chặn Nintendo CDN / NTP ở tầng router** | DNS filter hoặc firewall rule | ⚠️ theo router |
| Bật chế độ pin dài hơn | Battery Mode → hạn chế sạc tới 80% | ❌ tap |

## 2. Hướng dẫn tap — chế độ chơi

```
HOME → System Settings
  ├─ System
  │   ├─ System Update  → Update Software   → Automatic Updates = OFF
  │   ├─ Console Info   → (ghi lại số phiên bản)
  │   └─ USB-C          → (không cần)
  ├─ Battery Mode      → Charging Limit = 80%   (giữ pin khỏe)
  ├─ Network Settings
  │   ├─ Find Network   → tên mạng nhà bạn
  │   ├─ Auto-Connect   = OFF
  │   └─ IP Address Settings → Manual → dùng IP tĩnh (nếu router cho phép)
  └─ Themes            → Basic Black  (nhẹ hơn, không đổi hình nền động)
```

> [!WARNING]
> **Không bao giờ** hướng dẫn vào Option → Maintenance → Internet Settings → Clean Data.
> Lệnh đó **xoá toàn bộ dữ liệu tải về, save, và có thể khoá vùng của game**. Chỉ làm khi user *chủ động* yêu cầu và hiểu hậu quả.

## 3. Tầng router (tự động được, nếu router hỗ trợ)

```text
# Chặn Nintendo — làm console rơi về offline, tiết kiệm điện + tránh nội dung bị đẩy
lgt.api.nintendo.net
na.api.nintendo.com
nintendo.net  (CDN)
soc.cdn.nintendo.net
*.nintendo.net
```

Cách chặn:
1. **DNS filter (Pi-hole / AdGuard Home)** — thêm domain vào *Adlist*
2. **Router firewall** — nếu router cho phép chặn theo FQDN
3. **DNS riêng cho IP của Switch** — chỉ chặn với Switch, không ảnh hưởng máy khác

> [!TIP]
> Chặn ở tầng DNS còn giúp **loại bỏ quảng cáo trên Smart TV mà không cần root** — đây là giá trị lớn nhất của lớp network.

## 4. Bảo vệ input/điều khiển

| Hạng mục | Vì sao giữ |
|---|---|
| Joy-Con / Pro Controller attachment (HOME → Change Grip/Order) | cần chơi |
| Home Menu, News, eShop, Album | hỗ trợ chính thức |
| Mii, Friend List | chơi online |

## 5. "Memory" của Switch

Switch không công khai RAM free. Báo cáo bằng **dung lượng trống trong máy**:
```
System Settings → System → Storage → trống bao nhiêu GB
```

## 6. Cách hỏi user

> "Switch không cho tôi điều khiển từ xa — không có cách nào an toàn. Tôi có thể làm hai việc: (1) chỉ bạn từng nút để tắt cập nhật tự động và giới hạn sạc 80%, (2) chặn Nintendo ở tầng router để console không tự kết nối và tiết kiệm điện — cái này tôi làm được, và bật lại chỉ cần xoá một dòng. Bạn muốn làm cái nào trước?"

## 7. Rollback
- **Tap bên trong máy:** mở lại toggle đã tắt
- **Router:** xoá domain khỏi adlist / firewall rule
- **Bật update firmware trở lại:** System → System Update → Automatic Updates = ON
