# SAFETY — Danh sách bảo vệ và quy tắc an toàn

> [!WARNING]
> Những package/app dưới đây **không bao giờ** được đề xuất tắt, và cũng không được tắt dù người dùng nói "tắt hết". Chúng bị chặn ở tầng guard, không phải ở tầng hội thoại.

## 1. Deny-list tuyệt đối (Absolute deny-list)

### 1.1 Nền tảng / launcher
| Package | Vì sao giữ |
|---|---|
| `com.google.android.tvlauncher` | launcher gốc — đường quay lại |
| `com.google.android.leanback` | launcher AOSP cho TV |
| `com.miui.home`, `com.miui.tv.home` | launcher Xiaomi |
| `com.tcl.tvlauncher` | launcher TCL |
| `com.hisense.*launcher*` | launcher Hisense |
| `com.sony.*launcher*` | launcher Sony |
| `AndroidManifest.xml` HOME activity của thiết bị | launcher đang active |

### 1.2 Lõi hệ thống
| Package | Vì sao giữ |
|---|---|
| `com.android.vending` | **Google Play** — yêu cầu rõ ràng của user |
| `com.google.android.gms` | Play Services — nhiều app cần |
| `com.android.systemui` | status bar, notification |
| `com.android.settings` | Settings app |
| `com.android.providers.*` | content providers |
| `com.android.shell` | adb/remote shell |
| `com.android.bluetooth` | **remote cần Bluetooth** |
| `com.google.android.inputmethod.latin` | **bàn phím** |

### 1.3 Input / HDMI
| Pattern | Vì sao giữ |
|---|---|
| `com.android.tv.leanback` | input switcher của TV |
| `*leanback*`, `*hdmi*`, `*inputswitch*` | chuyển nguồn HDMI |
| `com.google.android.apps.mediashell` | cast / media shell |
| `HDMI`, `TVInputManager` | framework TV input |

### 1.4 Tizen / webOS / Roku
| Loại | Vì sao giữ |
|---|---|
| Mọi app nhà sản xuất trong "Input / Source / Input List" | chuyển nguồn |
| Roku: `MediaPlayer`, `Roku Remote`, `Roku SceneGraph` | điều khiển + Home |
| Roku: `system.screen_saver`, `system.theme` | nếu muốn screensaver riêng |

### 1.5 iOS
| Hạng mục | Vì sao giữ |
|---|---|
| Bất kỳ app có quyền "Input/Source" | chuyển HDMI |
| Apple TV app, AirPlay, Remote app | điều khiển từ iPhone |

### 1.6 Switch / 3DS / DS
| Hạng mục | Vì sao giữ |
|---|---|
| Chức năng Online / News / eShop / Mii | là feature chính thức |
| Điều khiển hạ tầng (Joy-Con attachment, Home Menu) | điều khiển |

> [!IMPORTANT]
> Trên Switch/3DS/DS **không có API quản trị qua IP**, này là guard *về mặt hành vi*: agent chỉ hướng dẫn tap, không hứa tự động.

## 2. Soft-guard (được hỏi nhưng phải hỏi rõ)

| Tình huống | Câu hỏi bắt buộc |
|---|---|
| App streaming của user (Netflix/Youtube/Prime) | "Netflix is one of your apps — keep it on?" |
| App OEM không có trong whitelist | "This is a <brand> app not on the known-good list. Disable it?" |
| App từng mở trong 30 ngày | "You used this on <date>. Turn it off?" |
| App là launcher phụ | "This can act as a home screen. Keep it enabled as a backup?" |

## 3. Quy tắc bất di bất dịch

1. **Không bao giờ uninstall.** Chỉ `disable-user --user 0`. Muốn xoá hẳn thì để user tự gỡ trên máy.
2. **Hỏi trước mỗi nhóm thay đổi.** Gom theo mục đích, tối đa ~10 app/nhóm.
3. **Backup trước.** Ghi `pm list packages`, `pm list packages -d`, `settings list global/system`, `getprop` trước khi sửa.
4. **Ghi undo-log trước khi ghi.** Không có log → không được sửa.
5. **Giữ launcher gốc enabled.** Không bao giờ disable launcher để còn đường quay lại.
6. **Reboot & verify.** Sau khi tắt launcher phụ, reboot ngay. Sau mọi nhóm thay đổi lớn, đo lại.
5. **Giữ launcher gốc enabled** (trùng lặp cố ý để nhấn mạnh) — xem §3.5.
7. **Không đụng firmware.** Update firmware sẽ đặt lại setting; sau update phải chạy lại `verify`.
8. **Không root, không flash, không bypass DRM/licensing.**

## 4. Ngôn ngữ với người dùng

| Nên | Không nên |
|---|---|
| "This app only shows ads. Want me to turn it off?" | "Disabling com.xxx.ads" |
| "I won't touch this one — your remote needs it." | "ERROR: protected" |
| "I turned off 12 apps. Here's how to undo it." | "Done." |
| "Free memory went from 512 MB to 690 MB." | "Memory optimized." |

> [!TIP]
> Số liệu RAM nói **"free memory"**, không nói "memory usage". Người dùng quan tâm "còn bao nhiêu trống".

## 5. Checklist trước khi áp dụng bất kỳ thay đổi nào

- [ ] Đã `probe` thành công, xác định đúng profile
- [ ] Đã backup inventory + settings + getprop
- [ ] Đã phân loại app thành 3 danh sách và trình bày cho user
- [ ] Đã đo baseline memory/storage
- [ ] Không mục nào trong deny-list nằm trong nhóm thay đổi
- [ ] Đã hỏi và được user đồng ý **cho nhóm này**
- [ ] Đã ghi undo-log trước khi gọi lệnh ghi
- [ ] Đã nói rõ cách undo trước khi làm
