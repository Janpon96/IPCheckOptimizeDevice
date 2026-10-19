# Mẫu undo-log (JSONL)

Mỗi dòng là một sự kiện JSON. **Append-only. Không bao giờ xoá dòng.**
Ghi dòng `"status":"pending"` **trước** khi thay đổi, rồi cập nhật thành `"applied"` sau khi lệnh thành công.

## Schema

```json
{
  "ts": "2026-10-19T14:03:11+07:00",
  "device": "192.168.1.50",
  "profile": "android-tv",
  "id": "chg-001",
  "target": "com.miui.tvads",
  "plain_name": "Mi Ads",
  "action": "disable-user",
  "category": "ads-telemetry",
  "approval": {
    "granted": true,
    "question": "Turn off 5 ad/tracking apps?",
    "group": "g1",
    "at": "2026-10-19T14:03:10+07:00"
  },
  "undo": { "cmd": "pm enable com.miui.tvads", "kind": "enable" },
  "evidence": "Package com.miui.tvads new state: disabled-user",
  "status": "applied"
}
```

## Giá trị hợp lệ

| Trường | Giá trị |
|---|---|
| `action` | `disable-user`, `enable`, `setprop`, `settings-put`, `set-home-activity`, `install`, `sideload`, `network-rule`, `manual` |
| `category` | `launcher`, `core`, `input-hdmi`, `keyboard`, `bluetooth`, `ads-telemetry`, `preinstalled-unused`, `store`, `streaming`, `games`, `user-installed`, `unknown` |
| `status` | `pending` → `applied` / `failed` / `rolled-back` / `guard_blocked` |

## Ví dụ — một phiên hoàn chỉnh

```jsonl
{"ts":"2026-10-19T14:02:00+07:00","device":"192.168.1.50","profile":"android-tv","id":"chg-001","target":"com.miui.tvads","plain_name":"Mi Ads","action":"disable-user","category":"ads-telemetry","approval":{"granted":true,"question":"Turn off 5 ad apps?","group":"g1","at":"2026-10-19T14:02:58+07:00"},"undo":{"cmd":"pm enable com.miui.tvads","kind":"enable"},"status":"applied"}
{"ts":"2026-10-19T14:02:31+07:00","device":"192.168.1.50","profile":"android-tv","id":"chg-002","target":"com.google.android.gms","plain_name":"Google Play services","action":"disable-user","category":"core","approval":{"granted":true},"undo":{"cmd":"pm enable com.google.android.gms","kind":"enable"},"status":"guard_blocked"}
{"ts":"2026-10-19T14:05:00+07:00","device":"192.168.1.50","profile":"android-tv","id":"chg-010","target":"global:window_animation_scale","action":"settings-put","category":"performance","approval":{"granted":true,"question":"Turn off animations?","at":"2026-10-19T14:04:50+07:00"},"undo":{"kind":"restore-value","key":"global:window_animation_scale","value":"1.0"},"status":"applied"}
{"ts":"2026-10-19T14:09:12+07:00","device":"192.168.1.50","profile":"android-tv","id":"chg-020","target":"com.tvclean.launcher/.MainActivity","action":"set-home-activity","category":"launcher","approval":{"granted":true,"at":"2026-10-19T14:08:00+07:00"},"undo":{"kind":"set-home-activity","value":"com.google.android.tvlauncher/com.google.android.tvlauncher.HomeActivity"},"status":"applied"}
{"ts":"2026-10-19T14:20:00+07:00","device":"192.168.1.50","profile":"android-tv","id":"chg-001","action":"disable-user","target":"com.miui.tvads","status":"rolled-back","note":"user requested miui.player back"}
```

## Cách hoàn tác tất cả

```powershell
# 1) Lấy tất cả app đang disable mà log ghi là do ta tắt
Get-Content .\undo-log.jsonl |
  Where-Object { $_ -match '"status":"applied"' -and $_ -match '"action":"disable-user"' } |
  ForEach-Object { ($_ | ConvertFrom-Json) } |
  Select-Object -ExpandProperty undo |
  Select-Object -ExpandProperty cmd -Unique |
  ForEach-Object { adb -s 192.168.1.50:5555 shell $_ }
```

## Quy tắc

1. **Log trước, đổi sau.** Không có dòng log → không được chạy lệnh ghi.
2. **Không sửa dòng cũ.** Sai thì ghi dòng mới (`rolled-back` hoặc `guard_blocked`).
3. **Guard chặn cũng phải ghi** (`status: guard_blocked`) — để sau này biết vì sao app đó không bị đụng.
4. **Không ghi secret** vào log (token, mật khẩu, serial nhạy cảm).
