# IPCheckOptimizeDevice

Bộ tài liệu vận hành (plans / specs / runbook) để **Antigravity** thực thi tối ưu cho *mọi thiết bị trong nhà có IP*, thông qua mạng LAN — không cần cắm cáp, không root.

Tham khảo thiết kế: [`Gathin23/tv-vibehack`](https://github.com/Gathin23/tv-vibehack) (debloat Android TV bằng ADB, không gỡ cài đặt, có `restore.sh`). Bộ tài liệu này mở rộng ý tưởng đó sang 9 họ nền tảng.

## Nguồn sự thật

| Tài liệu | Vai trò |
|---|---|
| [`docs/PLAN.md`](docs/PLAN.md) | Lộ trình triển khai theo phase, exit criteria, rủi ro |
| [`docs/SPEC.md`](docs/SPEC.md) | Hợp đồng kỹ thuật: transport, capability tiers, schema undo-log, guardrail |
| [`docs/RUNBOOK.md`](docs/RUNBOOK.md) | Quy trình 10 bước dùng tay cho mọi thao tác thật |
| [`docs/SAFETY.md`](docs/SAFETY.md) | Danh sách "tuyệt đối không đụng" + quy tắc hỏi trước mỗi thay đổi |
| [`docs/profiles/`](docs/profiles/) | 9 profile thiết bị (mỗi loại một file, kèm lệnh cụ thể) |
| [`prompts/`](prompts/) | Prompt sẵn dùng cho Antigravity (`MASTER_PROMPT.md` là bản tổng quát hoá từ prompt Ansub) |
| [`assets/`](assets/) | Template inventory / change-log / script undo |

## Profile thiết bị

| Profile | Transport chính | Có thể tự động? |
|---|---|---|
| [`android-tv-google-tv`](docs/profiles/01-android-tv-google-tv.md) | ADB TCP:5555 | ✅ Đầy đủ |
| [`android-phone-tablet`](docs/profiles/02-android-phone-tablet.md) | ADB TCP:5555 | ✅ Đầy đủ |
| [`fire-tv`](docs/profiles/03-fire-tv.md) | ADB TCP:5555 | ⚠️ Debloat + settings (không đổi launcher) |
| [`android-projector-xview`](docs/profiles/04-android-projector-xview.md) | ADB TCP:5555 (nhiều máy mở sẵn) | ✅ Đầy đủ |
| [`ios-iphone-ipad`](docs/profiles/05-ios-iphone-ipad.md) | pymobiledevice3 / Apple Configurator | ⚠️ Có trợ lý + hướng dẫn tap tại chỗ |
| [`nintendo-switch`](docs/profiles/06-nintendo-switch.md) | Không có admin API qua IP | ⚠️ Tắt trong máy + chặn tầng router |
| [`nintendo-3ds-ds`](docs/profiles/07-nintendo-3ds-ds.md) | Không có (3DS offline-capable, DS offline) | ⚠️ Cài đặt máy + router |
| [`roku-tizen-webos`](docs/profiles/08-roku-tizen-webos.md) | Roku ECP HTTPS :8060 / web UI | ⚠️ Chỉ screensaver + vài setting |
| [`network-layer`](docs/profiles/09-network-layer.md) | Router (DNS/adblock, QoS, VLAN) | ✅ Áp dụng cho *mọi* thiết bị |

## Luật bất di bất dịch

1. **Không bao giờ gỡ cài đặt.** Chỉ `disable-user` → undo được bằng `enable`.
2. **Hỏi trước mỗi thay đổi.** Tối đa 1 nhóm thay đổi / 1 câu hỏi.
3. **Bảo vệ tuyệt đối:** Google Play, Play Services, bàn phím (Gboard), Bluetooth, mọi app HDMI/input, launcher gốc (để còn đường quay lại).
4. **Ghi undo-log trước khi sửa.** Không có log → không được sửa.
5. **Đo trước / đo sau.** Báo cáo RAM & storage trước–sau, có reboot verify.

> Bắt đầu từ [`docs/RUNBOOK.md`](docs/RUNBOOK.md). Cần nhanh thì dùng [`prompts/MASTER_PROMPT.md`](prompts/MASTER_PROMPT.md).
