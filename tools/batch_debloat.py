#!/usr/bin/env python3
"""batch_debloat.py - Helper for batch scanning and disabling safe apps with graceful error handling."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from device_manager import DeviceManager, DeviceConnectionError

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def scan_safe(host: str):
    mgr = DeviceManager(host)
    try:
        items = mgr.inventory()
        if items and items[0].get("platform") == "roku":
            print(f"[!] Thiết bị Roku ({host}) chỉ hỗ trợ liệt kê ứng dụng qua ECP, không hỗ trợ tắt app qua ADB.")
            return []
        safe = [i for i in items if i["category"] == "safe_to_disable" and not i["is_disabled"]]
        if not safe:
            print(f"[+] Tuyệt vời! Không còn ứng dụng rác/quảng cáo nào đang chạy trên {host}.")
            return []
        print(f"Tìm thấy {len(safe)} ứng dụng rác / quảng cáo / telemetry có thể tắt an toàn:")
        for idx, a in enumerate(safe, 1):
            print(f"  {idx:2d}. {a['plain_name']:<35} [{a['package_id']}]")
            print(f"      -> {a['description']}")
        return [a["package_id"] for a in safe]
    except DeviceConnectionError as e:
        print(str(e))
        return []
    finally:
        mgr.close()


def apply_safe(host: str):
    mgr = DeviceManager(host)
    try:
        items = mgr.inventory()
        safe = [i for i in items if i["category"] == "safe_to_disable" and not i["is_disabled"]]
        if not safe:
            print("[*] Không có ứng dụng nào cần tắt.")
            return
        mgr.backup_state()
        for a in safe:
            print(f"[-] Đang tắt {a['plain_name']} ({a['package_id']})...")
            res = mgr.apply_disable(a["package_id"], "Batch safe debloat")
            print(f"    Kết quả: {res['status']} ({res['output']})")
        print("\n[+] Hoàn tất Batch Debloat! Mọi thay đổi đã được lưu vào undo-log.jsonl.")
    except DeviceConnectionError as e:
        print(str(e))
    finally:
        mgr.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: batch_debloat.py <scan|apply> <host>")
        sys.exit(1)
    action, host = sys.argv[1], sys.argv[2]
    if action == "scan":
        scan_safe(host)
    elif action == "apply":
        apply_safe(host)
