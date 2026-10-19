# Profile 09 — Tầng mạng (Router / DNS)

**Capability: `FULL`** · Transport: web UI router, Pi-hole, AdGuard Home

> [!IMPORTANT]
> Đây là profile **duy nhất áp dụng được cho mọi thiết bị** trong danh sách, kể cả iOS, Switch, 3DS, Tizen, webOS — những thứ không có API nào.
> Trên nhiều nhà, đây là thay đổi **hiệu quả nhất**.

## 1. Những gì làm được ở tầng router

| Mục tiêu | Cách làm | Áp dụng cho |
|---|---|---|
| Chặn quảng cáo toàn nhà | Pi-hole / AdGuard Home làm DNS server | ✅ tất cả |
| Cấp IP tĩnh (DHCP reservation) | theo MAC | ✅ tất cả |
| Tách VLAN cho thiết bị cầm tay | AP/VLAN + chặn outbound | Switch, 3DS, DS |
| Ưu tiên băng thông cho TV | QoS / device priority | ✅ |
| Chặn Nintendo / telemetry | FQDN blocklist | Switch, 3DS, Tizen, webOS |
| Tắt UPnP | tắt trong router | ✅ tất cả |

## 2. Ad-blocking DNS — cách hiệu quả nhất

### 2.1 Cài Pi-hole trên máy tính / Raspberry Pi / Docker

```powershell
docker run -d --name pihole -p 80:80 -p 443:443 -p 53:53/tcp -p 53:53/udp `
  -v pihole:/etc/pihole pihole/pihole:latest
```

### 2.2 Trỏ DNS của router về Pi-hole

Trong web UI router:
```
DHCP → DNS Server → đặt IP của Pi-hole (vd 192.168.1.10)
```

### 2.3 Thêm blocklist Nintendo / TV

Trong Pi-hole → Settings → Adlists:
```
https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts       (mặc định)
+ các domain Nintendo, Samsung, LG ở docs/profiles/08 và 06
```

### 2.4 Đo hiệu quả

Vào `http://pi.hole/admin/` → xem **Queries**, **Blocked**, tỉ lệ chặn. Đây là **chỉ số duy nhất đo được** cho lớp network — dùng nó làm "free memory" tương đương.

**Báo cáo:** "Từ lúc bật lọc, router đã chặn 12.483 request quảng cáo — đó là 12.483 lần TV không phải tải quảng cáo vô ích."

## 3. DHCP reservation (IP tĩnh)

| Lợi ích | Vì sao quan trọng |
|---|---|
| IP không đổi → script của bạn vẫn chạy | Tránh phải dò lại |
| Dễ đặt quy tắc riêng theo thiết bị | Chặn Nintendo chỉ trên Switch |
| Dễ đọc báo cáo | Biết `192.168.1.50` luôn là TV |

Thiết lập tại router: `DHCP → Static Lease → MAC + IP`. Lấy MAC từ:
```powershell
arp -a | Select-String "192.168.1.50"
```

## 4. VLAN / mạng riêng cho thiết bị cầm tay

**Mục tiêu:** Switch, 3DS, DS dùng offline (game, video) nhưng **không bao giờ gọi ra Internet**.

```
Router:
  VLAN 10  →  "Trusted": TV, máy chiếu, điện thoại       → Internet OK
  VLAN 20  →  "Handheld": Switch, 3DS, DS                 → chỉ trong nội bộ, KHÔNG outbound
  VLAN 30  →  "IoT": camera, bóng đèn, TV thông minh      → Internet OK, không truy cập VLAN 10
```

Firewall rule cho VLAN 20:
```
ALLOW  VLAN20 → VLAN10 (nội bộ, ví dụ phát video từ NAS)
DENY   VLAN20 → WAN  (chặn outbound)
```

> [!TIP]
> Nếu router không hỗ trợ VLAN, dùng **AP khác** (mesh node hoặc access point cũ). Tách bằng subnet là đủ.

## 5. QoS — ưu tiên thiết bị giải trí

Khi TV và máy chiếu cùng dùng Wi-Fi, việc tải 4K có thể làm giật. Đặt ưu tiên:
```
QoS / Bandwidth Control → ưu tiên cao: <MAC của TV>, <MAC của máy chiếu>
→ ưu tiên thấp: thiết bị tải torrent, camera, máy in
```

## 6. Chặn telemetry tại chỗ

Ngoài adlist, chặn thẳng các đích IP của nhà sản xuất TV:
```text
# Xiaomi
tracking.miui.com
data.mistat.xiaomi.com
sdkconfig.ad.xiaomi.com

# Samsung / LG / Roku  (xem profile 08)
# Google
play.google.com  (chỉ khi muốn chặn cập nhật Play)
```

## 7. Tắt UPnP

```
Router → Advanced / NAT → UPnP = Disabled
```
UPnP cho phép thiết bị tự mở cổng — không cần cho TV/console và là lỗ hổng thường bị lợi dụng.

## 8. Cách hỏi user

> "Có hai tầng. Tầng một: tắt những thứ không cần — theo dõi, quảng cáo — ngay trên router. Cái này áp dụng cho *mọi* thiết bị trong nhà, kể cả Switch và iPhone, và tôi gỡ ra được bằng cách xoá một dòng. Tầng hai: tôi sẽ đưa TV, máy chiếu, Switch vào mạng riêng. Bạn chơi game, xem phim bình thường, nhưng chúng không tự đẩy quảng cáo lên mạng nữa. Bạn muốn làm tầng nào trước?"

## 9. Rollback

| Thay đổi | Cách hoàn tác |
|---|---|
| Adlist | Xoá dòng trong Pi-hole |
| DHCP reservation | Xoá static lease |
| VLAN | Gán thiết bị về VLAN cũ |
| QoS | Xoá rule ưu tiên |
| UPnP | Bật lại UPnP |

**Tất cả đều là thay đổi router → không ảnh hưởng dữ liệu thiết bị, hoàn tác tức thì.** Đây là lớp an toàn nhất để đề xuất khi user lo lắng.
