---
name: device-ip-optimizer
description: Tối ưu mọi thiết bị có IP trong nhà (TV, Android, iPhone, Switch, 3DS/DS, máy chiếu Xview) qua mạng LAN — thấy toàn bộ app, phân loại, hỏi trước mỗi thay đổi, tắt thay vì gỡ, đo RAM trước/sau, có runbook hoàn tác. Dùng khi người dùng nhắc tới IP thiết bị và muốn dọn dẹp/tối ưu.
---

# Tối ưu thiết bị qua IP

Bạn đang tối ưu **một thiết bị có IP trong nhà** — có thể là TV, điện thoại Android, iPhone, máy chiếu, Switch, 3DS/DS, Roku/Tizen/webOS. Bạn **không có cáp, không có root, không có SDK bị chặn**.

## Nguyên tắc bất di bất dịch

1. **Không bao giờ gỡ cài đặt (uninstall).** Chỉ *tắt* (`disable`) để có thể bật lại.
2. **Hỏi trước mọi thay đổi.** Gom nhóm ≤10 app, 1 nhóm = 1 câu hỏi.
3. **Tuyệt đối không đụng:** Google Play, Play Services, bàn phím, Bluetooth (remote cần), mọi thứ liên quan HDMI/input, launcher gốc.
4. **Ghi undo-log trước khi ghi bất cứ thứ gì.**
5. **Đo trước / đo sau / reboot / verify.**
6. **Nói cho người dùng hiểu được** — tên app tiếng Anh, không tùy package.

## Quy trình (làm đúng thứ tự)

| Bước | Việc | Đầu ra |
|---|---|---|
| 0 | Ping IP, tạo thư mục `reports/`, `backups/` | — |
| 1 | **Hướng dẫn user bật ADB/Developer mode** (xem bên dưới), `adb connect` | `adb devices` = `device` |
| 2 | Probe: model, Android version, `pm list features` | profile thiết bị |
| 3 | Backup: packages, disabled, settings, getprop, HOME activity | `backups/<ts>/` |
| 4 | Inventory + RAM/storage baseline | `reports/` |
| 5 | Phân loại 3 danh sách + số RAM free | trình bày cho user |
| 6 | Đề xuất nhóm thay đổi + xin phép | user duyệt |
| 7 | Ghi undo-log, rồi mới `disable` | undo-log đầy đủ |
| 8 | Reboot + verify + đo RAM lại | số liệu trước/sau |
| 9 | Home screen sạch + tắt animation/screensaver + sleep 5 phút | ảnh/chứng minh |
| 10 | Báo cáo + cách undo | `reports/<ip>_<ts>.md` |

## Hướng dẫn bật ADB (nói rõ từng nút, chờ user xác nhận)

**Google TV / Android TV**
> Settings → phím mũi tên lên góc phải → Device Preferences → About → nhấn **OK 7 lần** vào mục **Build** → quay lại → Developer options → bật **USB debugging** (và **Network debugging** nếu có) → để TV bật sáng.

**Android điện thoại / máy chiếu Xview**
> Settings → About → nhấn **Build 7 lần** → System → Developer options → **USB debugging = ON**.

**Amazon Fire TV**
> Settings → My Fire TV → Developer Options → **ADB Debugging = ON**.

**iPhone / iPad**
> Settings → Privacy & Security → **Developer Mode** = ON → khởi động lại → Settings → Developer → cho phép kết nối không dây.

**Switch / 3DS / DS / Tizen / webOS**
> Không có ADB. Chỉ hướng dẫn tap bên trong máy + can thiệp ở tầng router. Nói rõ điều này với user, **không hứa tự động hoá được**.

## Sau khi có `adb devices` = `device`

```bash
adb -s <IP>:5555 shell getprop ro.product.model
adb -s <IP>:5555 shell getprop ro.build.version.release
adb -s <IP>:5555 shell pm list features | grep -E "leanback|television|touchscreen"
adb -s <IP>:5555 shell pm list packages -f
adb -s <IP>:5555 shell pm list packages -d
adb -s <IP>:5555 shell dumpsys meminfo
adb -s <IP>:5555 shell df -h /data
```

## Trình bày 3 danh sách (bắt buộc đúng format này)

```markdown
**Safe to turn off (N)** — app quảng cáo, theo dõi, app thừa của hãng
**Needed by the TV (M)** — không bao giờ đụng: Play Store, System UI, launcher, Bluetooth, bàn phím, input HDMI
**Your apps (K)** — app của bạn, hỏi từng app trước khi tắt

**Free memory now:** X MB free of Y MB (Z%)
**Storage:** A GB free of B GB
```

Sau đó hỏi, **một nhóm một lần**:

> "Nhóm 1: tắt 5 app quảng cáo/theo dõi? Tắt giúp TV khởi động nhanh hơn và ngừng gửi dữ liệu xem của bạn đi. Không xoá gì cả — bật lại bất cứ lúc nào."
> `Có` / `Không`

Chỉ chạy lệnh sau khi người dùng trả lời `Có`.

## Ghi undo-log trước, đổi sau

```bash
# 1) log trước
echo '{"ts":"...","id":"chg-001","target":"com.miui.tvads","action":"disable-user","approval":{"granted":true},"undo":{"cmd":"pm enable com.miui.tvads"},"status":"pending"}' >> undo-log.jsonl
# 2) rồi mới thay đổi
adb -s <IP>:5555 shell pm disable-user --user 0 com.miui.tvads
```

## Trước khi kết thúc — bắt buộc

- [ ] Đã reboot và verify các app vẫn tắt
- [ ] Đã đo RAM **trước và sau**
- [ ] Đã đưa danh sách app đã tắt + lệnh bật lại từng app
- [ ] Đã nói: firmware update có thể đặt lại mọi thay đổi
- [ ] Home screen sạch: clock, không quảng cáo, không đề xuất, đúng app user chẽn
- [ ] Animation tắt, screensaver tắt (hoặc Clock screensaver), sleep 5 phút

## Tài liệu đầy đủ trong repo

- `docs/RUNBOOK.md` — quy trình chi tiết từng lệnh
- `docs/SAFETY.md` — deny-list tuyệt đối
- `docs/SPEC.md` — hợp đồng kỹ thuật
- `docs/profiles/NN-*.md` — lệnh riêng cho từng họ thiết bị
- `assets/report-template.md` — mẫu báo cáo

## Nếu người dùng nói "cứ tắt hết"

Giải thích ngắn gọn: một s�� app **không được phép tắt** (Play Store, bàn phím, Bluetooth vì remote cần, launcher, input HDMI) — vì tắt chúng có thể làm mất remote hoặc không vào được TV. Phần còn lại bạn tắt được, và bạn sẽ giữ danh sách để bật lại bất cứ lúc nào.
