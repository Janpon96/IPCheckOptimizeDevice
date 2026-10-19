# Mẫu inventory

Một dòng = một app. Dùng để **đối chiếu trước/sau** và làm cơ sở cho `undo-log.jsonl`.

## Schema

| Trường | Kiểu | Bắt buộc | Ví dụ |
|---|---|---|---|
| `package_id` | string | ✅ | `com.miui.tvads` |
| `plain_name` | string | ✅ | "Mi Ads" — **tiếng Anh dễ hiểu** |
| `category` | enum | ✅ | `ads-telemetry` |
| `size_mb` | number \| null | ✅ | 412 |
| `is_system` | bool | ✅ | false |
| `enabled` | bool | ✅ | true |
| `protected` | bool | ✅ | true nếu trúng deny-list |
| `plain_name_source` | enum | | `label` \| `manual` (nếu agent tự đặt tên) |

## Cách thu thập

```powershell
$d = "192.168.1.50:5555"
# User-installed apps (kèm đường dẫn APK → dễ đo dung lượng)
adb -s $d shell pm list packages -3 -f
# System apps
adb -s $d shell pm list packages -s -f
# Disabled apps
adb -s $d shell pm list packages -d
# Label của từng package (Android 11+)
adb -s $d shell cmd package list packages -i
# Dung lượng (nếu có)
adb -s $d shell dumpsys package <pkg> | Select-String "codePath|dataDir"
```

## Ví dụ — bảng đã phân loại

```csv
package_id,plain_name,category,size_mb,is_system,enabled,protected
com.google.android.tvlauncher,Android TV Launcher,launcher,45,true,true,true
com.android.vending,Google Play,store,38,true,true,true
com.google.android.gms,Google Play services,core,92,true,true,true
com.android.bluetooth,Bluetooth,bluetooth,18,true,true,true
com.google.android.inputmethod.latin,Keyboard,keyboard,22,true,true,true
com.android.tv.leanback,HDMI Input,input-hdmi,12,true,true,true
com.miui.tvads,Mi Ads,ads-telemetry,31,true,true,false
com.miui.getapps,GetApps,ads-telemetry,14,true,true,false
com.miui.analyticsd,Analytics,ads-telemetry,8,true,true,false
com.bugsnag.android,Bugsnag,ads-telemetry,6,true,true,false
com.xiaomi.mipicks,Mi Picks,preinstalled-unused,25,true,true,false
com.miui.tvhome.cloudplay,Mi Cloud Play,preinstalled-unused,19,true,true,false
com.xiaomi.joyose,Xiaomi Remote,preinstalled-unused,11,true,true,false
com.netflix.mediaclient,Netflix,streaming,412,false,true,false
com.google.android.youtube.tv,YouTube,streaming,178,false,true,false
com.netease.cloudmusic,NetEase Cloud Music,user-installed,95,false,true,false
```

## Bảng tổng hợp 3 nhóm (đưa cho user)

```markdown
**Safe to turn off (7)**
- Mi Ads — shows ads before you play anything
- GetApps — ads for installing apps
- Analytics — sends your viewing data to the maker
- Bugsnag — sends crash reports
- Mi Picks — the maker's own app store, you have Google Play
- Mi Cloud Play — cloud gaming service you don't use
- Xiaomi Remote — you don't use your phone to control this TV

**Needed by the TV (7)**
- Android TV Launcher · Google Play · Play services · System UI
- Bluetooth (your remote needs it) · Keyboard · HDMI Input

**Your apps (4)**
- Netflix · YouTube · NetEase Cloud Music · Mi Browser

**Free memory now:** 512 MB free of 1000 MB (50%)
**Storage:** 8.2 GB free of 16 GB (51%)
```

> [!IMPORTANT]
> Không có mục nào trong nhóm 2 được đưa sang nhóm 1, **dù người dùng nói "tắt hết"**. Đó là ranh giới cứng, không phải gợi ý.

## Đối chiếu trước/sau

```powershell
# So sánh danh sách app bị tắt giữa hai thời điểm
Compare-Object (Get-Content .\inventory-before.csv | ConvertFrom-Csv) `
                (Get-Content .\inventory-after.csv  | ConvertFrom-Csv) `
                -Property package_id -PassThru |
  Where-Object { $_.enabled -eq $false } |
  Select-Object package_id, plain_name
```

## Lưu ý về `plain_name`

| Nguồn | Khi nào dùng |
|---|---|
| `label` (tên từ `cmd package list packages -i`) | app có label tiếng Anh/sẵn |
| `manual` | app OEM tiếng Trung/Việt hoặc không có label |

> [!TIP]
> Agent **phải** đặt tên tiếng Anh dễ hiểu cho app không có label. Đừng đưa `com.miui.tvads` cho người dùng — họ không biết đó là gì.
