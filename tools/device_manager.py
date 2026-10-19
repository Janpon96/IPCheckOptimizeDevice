#!/usr/bin/env python3
"""device_manager.py - Core controller implementing the SPEC contract:
probe -> inventory -> classify -> plan -> apply -> verify -> rollback.

Communicates via pure-python adb-shell over Wi-Fi (no external adb required).
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    from adb_shell.adb_device import AdbDeviceTcp
    from adb_shell.auth.keygen import keygen
    from adb_shell.auth.sign_pythonrsa import PythonRSASigner
except ImportError:
    sys.exit("Error: adb-shell missing. Run with venv/Scripts/python.exe.")

import device_guard

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY_DIR = os.path.join(BASE_DIR, "tools", "adbkey")
KEY_PATH = os.path.join(KEY_DIR, "adbkey")
UNDO_LOG = os.path.join(BASE_DIR, "undo-log.jsonl")


def get_signer() -> PythonRSASigner:
    os.makedirs(KEY_DIR, exist_ok=True)
    if not os.path.exists(KEY_PATH):
        keygen(KEY_PATH)
    with open(KEY_PATH) as f:
        priv = f.read()
    with open(KEY_PATH + ".pub") as f:
        pub = f.read()
    return PythonRSASigner(pub, priv)


class DeviceManager:
    def __init__(self, host: str, port: int = 5555, timeout: float = 30.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.dev: Optional[AdbDeviceTcp] = None

    def connect(self) -> None:
        if self.dev:
            return
        try:
            self.dev = AdbDeviceTcp(self.host, self.port, default_transport_timeout_s=min(self.timeout, 5.0))
            self.dev.connect(rsa_keys=[get_signer()], transport_timeout_s=min(self.timeout, 5.0), auth_timeout_s=min(self.timeout, 5.0))
        except (ConnectionRefusedError, TimeoutError, OSError) as e:
            self.dev = None
            msg = (
                f"\n[!] KHÔNG THỂ KẾT NỐI ADB TỚI {self.host}:{self.port}\n"
                f"    Chi tiết: {e}\n\n"
                f"    -> NGUYÊN NHÂN PHỔ BIẾN:\n"
                f"    1. THIẾT BỊ LÀ IPHONE / IPAD (iOS):\n"
                f"       iPhone dùng hệ điều hành iOS (không có giao thức ADB của Android).\n"
                f"       Để xem chi tiết cách tối ưu iPhone qua mạng/hướng dẫn, xem file:\n"
                f"       docs/profiles/05-ios-iphone-ipad.md\n\n"
                f"    2. THIẾT BỊ LÀ ANDROID / ANDROID TV / MÁY CHIẾU:\n"
                f"       - Bạn chưa bật 'USB debugging' / 'Network debugging' trong Developer Options trên TV.\n"
                f"       - Máy tính và thiết bị chưa cùng 1 mạng Wi-Fi (hoặc router bật AP Isolation).\n"
                f"       - Hãy nhìn lên màn hình TV xem có hộp thoại 'Allow USB debugging?' không và chọn 'Always Allow'.\n"
            )
            print(msg)
            sys.exit(1)

    def close(self) -> None:
        if self.dev:
            try:
                self.dev.close()
            except Exception:
                pass
            self.dev = None

    def shell(self, cmd: str) -> str:
        self.connect()
        return self.dev.shell(cmd, read_timeout_s=self.timeout) or ""

    def probe(self) -> Dict[str, str]:
        """Read model, manufacturer, Android version and features."""
        props = {}
        for p in ("ro.product.model", "ro.product.manufacturer", "ro.build.version.release",
                  "ro.build.version.sdk", "ro.build.display.id"):
            val = self.shell(f"getprop {p}").strip()
            props[p] = val

        features = self.shell("pm list features")
        is_tv = "leanback" in features or "television" in features
        props["device_type"] = "Android TV / Google TV" if is_tv else "Android Device / Projector"
        return props

    def get_metrics(self) -> Dict[str, Any]:
        """Read RAM memory info and disk storage."""
        meminfo = self.shell("cat /proc/meminfo")
        total_kb, avail_kb = 0, 0
        for line in meminfo.splitlines():
            if line.startswith("MemTotal:"):
                total_kb = int(re.findall(r"\d+", line)[0])
            elif line.startswith("MemAvailable:"):
                avail_kb = int(re.findall(r"\d+", line)[0])

        df_out = self.shell("df -h /data")
        storage_str = ""
        for line in df_out.splitlines():
            if "/data" in line:
                storage_str = line

        return {
            "ram_total_mb": round(total_kb / 1024, 1),
            "ram_free_mb": round(avail_kb / 1024, 1),
            "ram_free_pct": round((avail_kb / total_kb) * 100, 1) if total_kb else 0,
            "storage_summary": storage_str.strip()
        }

    def inventory(self) -> List[Dict[str, Any]]:
        """List all installed packages and classify into safe, needed, user."""
        packages_3 = set(self.shell("pm list packages -3").replace("package:", "").splitlines())
        packages_all = self.shell("pm list packages").replace("package:", "").splitlines()
        disabled_set = set(self.shell("pm list packages -d").replace("package:", "").splitlines())

        result = []
        for pkg in sorted(filter(None, packages_all)):
            pkg = pkg.strip()
            is_system = pkg not in packages_3
            denied, reason = device_guard.is_deny_listed(pkg)
            category = device_guard.classify_package(pkg, is_system=is_system)
            
            result.append({
                "package_id": pkg,
                "plain_name": device_guard.get_plain_name(pkg),
                "is_system": is_system,
                "is_disabled": pkg in disabled_set,
                "category": category,
                "protected": denied,
                "deny_reason": reason
            })
        return result

    def apply_disable(self, package: str, group_reason: str = "Debloat optimization") -> Dict[str, Any]:
        """Safely disable a package after running guardrail and logging to undo-log."""
        pkg = package.strip()
        denied, reason = device_guard.is_deny_listed(pkg)
        if denied:
            event = {
                "ts": datetime.now().isoformat(),
                "device": self.host,
                "target": pkg,
                "action": "disable-user",
                "status": "guard_blocked",
                "reason": reason
            }
            self._log_undo(event)
            return {"success": False, "error": f"GUARD BLOCKED: {reason}"}

        # Step 1: Pre-log pending intent
        event = {
            "ts": datetime.now().isoformat(),
            "device": self.host,
            "target": pkg,
            "plain_name": device_guard.get_plain_name(pkg),
            "action": "disable-user",
            "approval": {"group": group_reason, "granted": True},
            "undo": {"cmd": f"pm enable {pkg}", "kind": "enable"},
            "status": "pending"
        }
        self._log_undo(event)

        # Step 2: Execute command
        out = self.shell(f"pm disable-user --user 0 {pkg}").strip()
        
        # Step 3: Log result
        event["status"] = "applied" if "disabled-user" in out.lower() or "new state" in out.lower() else "failed"
        event["evidence"] = out
        self._log_undo(event)

        return {"success": event["status"] == "applied", "output": out}

    def apply_enable(self, package: str) -> Dict[str, Any]:
        """Re-enable a disabled package."""
        pkg = package.strip()
        out = self.shell(f"pm enable --user 0 {pkg}").strip()
        event = {
            "ts": datetime.now().isoformat(),
            "device": self.host,
            "target": pkg,
            "action": "enable",
            "status": "rolled-back" if "enabled" in out.lower() or "new state" in out.lower() else "failed",
            "evidence": out
        }
        self._log_undo(event)
        return {"success": True, "output": out}

    def optimize_settings(self, sleep_minutes: int = 5) -> Dict[str, Any]:
        """Disable animations, screensaver, and set sleep timer."""
        timeout_ms = sleep_minutes * 60 * 1000
        cmds = [
            "settings put global window_animation_scale 0",
            "settings put global transition_animation_scale 0",
            "settings put global animator_duration_scale 0",
            f"settings put secure sleep_timeout {timeout_ms}",
            f"settings put system screen_off_timeout {timeout_ms}",
            "settings put secure screensaver_enabled 0"
        ]
        results = [self.shell(c).strip() for c in cmds]
        return {"success": True, "commands": cmds, "results": results}

    def reboot(self) -> None:
        self.shell("reboot")

    def _log_undo(self, event: Dict[str, Any]) -> None:
        with open(UNDO_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")


def cmd_probe(args, mgr: DeviceManager):
    props = mgr.probe()
    metrics = mgr.get_metrics()
    print("\n--- DEVICE PROBE & SYSTEM METRICS ---")
    for k, v in props.items():
        print(f"  {k}: {v}")
    print("\n--- MEMORY & STORAGE ---")
    print(f"  RAM Free: {metrics['ram_free_mb']} MB / {metrics['ram_total_mb']} MB ({metrics['ram_free_pct']}%)")
    print(f"  Storage: {metrics['storage_summary']}")


def cmd_inventory(args, mgr: DeviceManager):
    items = mgr.inventory()
    safe = [i for i in items if i["category"] == "safe_to_disable"]
    needed = [i for i in items if i["protected"] or i["category"] == "needed_by_tv"]
    user_apps = [i for i in items if i["category"] == "user_app"]
    ask = [i for i in items if i["category"] == "ask_user" and not i["protected"]]

    print(f"\n=======================================================")
    print(f"DEVICE APP INVENTORY: {mgr.host}")
    print(f"Total apps discovered: {len(items)}")
    print(f"=======================================================\n")

    print(f"🟢 [SAFE TO TURN OFF] ({len(safe)} apps) - Ads, tracking, and bloatware:")
    for a in safe:
        state = " (CURRENTLY OFF)" if a["is_disabled"] else ""
        print(f"  • {a['plain_name']} ({a['package_id']}){state}")

    print(f"\n🔴 [NEEDED BY TV - ABSOLUTELY PROTECTED] ({len(needed)} apps):")
    for a in needed[:15]:
        print(f"  • {a['plain_name']} ({a['package_id']})")
    if len(needed) > 15:
        print(f"    ... and {len(needed) - 15} more system/core components.")

    print(f"\n🔵 [YOUR APPS & STREAMING] ({len(user_apps)} apps):")
    for a in user_apps:
        print(f"  • {a['plain_name']} ({a['package_id']})")

    if ask:
        print(f"\n🟡 [SYSTEM / OEM APPS TO CONFIRM WITH USER] ({len(ask)} apps):")
        for a in ask[:10]:
            print(f"  • {a['plain_name']} ({a['package_id']})")


def main():
    parser = argparse.ArgumentParser(description="Antigravity Device Optimization Controller")
    parser.add_argument("--host", default=os.environ.get("TV_HOST"), help="Device IP address")
    parser.add_argument("--port", type=int, default=int(os.environ.get("TV_PORT", "5555")), help="ADB Port")
    
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("probe", help="Probe device identity and memory")
    sub.add_parser("inventory", help="Show all apps split into 3 plain English lists")
    
    p_dis = sub.add_parser("disable", help="Disable specific package with safety guard")
    p_dis.add_argument("package", help="Package ID to disable")
    p_dis.add_argument("--reason", default="Manual disable", help="Reason/group name")

    p_en = sub.add_parser("enable", help="Re-enable a disabled package")
    p_en.add_argument("package", help="Package ID to enable")

    p_opt = sub.add_parser("optimize-settings", help="Disable animations, screensaver & set 5m sleep")
    p_opt.add_argument("--sleep-minutes", type=int, default=5, help="Sleep timeout in minutes")

    sub.add_parser("reboot", help="Reboot device")

    args = parser.parse_args()
    if not args.host:
        sys.exit("Error: Please provide --host <DEVICE_IP> or set $env:TV_HOST")

    mgr = DeviceManager(args.host, args.port)
    try:
        if args.cmd == "probe" or not args.cmd:
            cmd_probe(args, mgr)
        elif args.cmd == "inventory":
            cmd_inventory(args, mgr)
        elif args.cmd == "disable":
            res = mgr.apply_disable(args.package, args.reason)
            print(json.dumps(res, indent=2))
        elif args.cmd == "enable":
            res = mgr.apply_enable(args.package)
            print(json.dumps(res, indent=2))
        elif args.cmd == "optimize-settings":
            res = mgr.optimize_settings(args.sleep_minutes)
            print(json.dumps(res, indent=2))
        elif args.cmd == "reboot":
            print(f"Rebooting device {args.host}...")
            mgr.reboot()
    finally:
        mgr.close()


if __name__ == "__main__":
    main()
