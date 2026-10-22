#!/usr/bin/env python3
"""device_manager.py - Core controller implementing the full SPEC contract:
detect -> probe -> backup -> inventory -> classify -> apply -> optimize -> verify -> report -> rollback.

Supports multi-platform detection (Android TV, Android Phone, Fire TV, Projector,
iOS, Roku, Tizen, webOS, Switch/3DS/DS, Network) and never crashes on non-ADB IPs.
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
import device_detector

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
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")


def get_signer() -> PythonRSASigner:
    os.makedirs(KEY_DIR, exist_ok=True)
    if not os.path.exists(KEY_PATH):
        keygen(KEY_PATH)
    with open(KEY_PATH) as f:
        priv = f.read()
    with open(KEY_PATH + ".pub") as f:
        pub = f.read()
    return PythonRSASigner(pub, priv)


class DeviceConnectionError(Exception):
    """Raised when ADB TCP connection cannot be established."""
    def __init__(self, message: str, detection: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.detection = detection or {}


class DeviceManager:
    def __init__(self, host: str, port: int = 5555, timeout: float = 15.0):
        self.host = host.strip()
        self.port = port
        self.timeout = timeout
        self.dev: Optional[AdbDeviceTcp] = None
        self.last_detection: Optional[Dict[str, Any]] = None

    def detect(self) -> Dict[str, Any]:
        """Run multi-platform network & OS detection before touching ADB."""
        self.last_detection = device_detector.detect_device(self.host)
        return self.last_detection

    def connect(self) -> None:
        if self.dev:
            return

        # Pre-check device profile if port 5555 is not open
        det = self.last_detection or self.detect()
        if self.port not in det.get("open_ports", {}):
            # Try connecting once with a short 3.5s timeout in case port scan missed it
            try:
                dev = AdbDeviceTcp(self.host, self.port, default_transport_timeout_s=3.5)
                dev.connect(rsa_keys=[get_signer()], transport_timeout_s=3.5, auth_timeout_s=8.0)
                self.dev = dev
                return
            except Exception as e:
                raise DeviceConnectionError(self._format_diagnostic(det, str(e)), detection=det)

        try:
            dev = AdbDeviceTcp(self.host, self.port, default_transport_timeout_s=min(self.timeout, 6.0))
            dev.connect(rsa_keys=[get_signer()], transport_timeout_s=min(self.timeout, 6.0), auth_timeout_s=15.0)
            self.dev = dev
        except Exception as e:
            self.dev = None
            raise DeviceConnectionError(self._format_diagnostic(det, str(e)), detection=det)

    def _format_diagnostic(self, det: Dict[str, Any], raw_err: str) -> str:
        ip = det.get("ip", self.host)
        reachable = det.get("reachable", False)
        mac = det.get("mac", "N/A")
        vendor = det.get("vendor", "Unknown")
        p_name = det.get("profile_name", "Unknown")
        p_key = det.get("profile_key", "android-tv")
        cap = det.get("capability", "MANUAL")
        ports = det.get("open_ports", {})
        guide = det.get("guide", "")

        lines = [
            f"======================================================================",
            f"🔍 SMART DEVICE DIAGNOSTIC FOR IP: {ip}",
            f"======================================================================",
            f"  • Network Status : {'🟢 ONLINE (Reachable on LAN)' if reachable else '🔴 OFFLINE / UNREACHABLE'}",
            f"  • MAC Address    : {mac} ({vendor})",
            f"  • Detected Type  : {det.get('icon', '📱')} {p_name}",
            f"  • Capability Tier: {cap} ({det.get('transport', '')})",
            f"  • Open TCP Ports : {', '.join(f'{k} ({v})' for k, v in ports.items()) if ports else 'None (All probed ports closed)'}",
            f"  • Document Ref   : {det.get('doc', '')}",
            f"----------------------------------------------------------------------",
        ]
        if not reachable:
            lines.extend([
                "  [!] E_NO_ROUTE: Không tìm thấy thiết bị trên mạng LAN.",
                "      - Kiểm tra lại địa chỉ IP trên thiết bị.",
                "      - Đảm bảo PC và thiết bị kết nối cùng một Wi-Fi / Subnet (tắt AP Isolation).",
            ])
        elif p_key in ("ios", "switch", "nintendo-3ds-ds", "tizen", "webos", "network"):
            lines.extend([
                f"  [i] Thiết bị này được nhận diện là [{p_name}].",
                f"      Nền tảng này không sử dụng cổng Android ADB (5555).",
                "",
                "📋 HƯỚNG DẪN TỐI ƯU CHO THIẾT BỊ NÀY:",
                guide
            ])
        elif p_key == "roku":
            lines.extend([
                "  [i] Phát hiện Roku TV qua giao thức ECP cổng 8060!",
                "      Đang chuyển sang chế độ đọc kênh Roku ECP..."
            ])
        else:
            lines.extend([
                f"  [!] E_ADB_OFF / E_ADB_UNAUTH: Cổng ADB 5555 đang đóng hoặc chưa xác nhận ({raw_err}).",
                "",
                "📋 HƯỚNG DẪN BẬT KẾT NỐI TRÊN THIẾT BỊ:",
                guide
            ])
        lines.append("======================================================================")
        return "\n".join(lines)

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

    def probe(self) -> Dict[str, Any]:
        """Probe device identity, refining profile using ADB properties if available."""
        det = self.detect()
        if det["profile_key"] == "roku" and 8060 in det.get("open_ports", {}):
            roku_info = det.get("extra", {}) or device_detector.query_roku_info(self.host) or {}
            return {
                "platform": "Roku OS (ECP :8060)",
                "ro.product.model": roku_info.get("model-name", "Roku TV"),
                "ro.product.manufacturer": roku_info.get("vendor-name", "Roku"),
                "ro.build.version.release": roku_info.get("software-version", "N/A"),
                "friendly_name": roku_info.get("friendly-device-name", "Roku"),
                "device_type": "Roku TV / Streaming Player",
                "profile_key": "roku",
                "capability": "FULL (ECP)",
            }

        props: Dict[str, Any] = {}
        for p in ("ro.product.model", "ro.product.manufacturer", "ro.build.version.release",
                  "ro.build.version.sdk", "ro.build.display.id", "ro.product.device"):
            props[p] = self.shell(f"getprop {p}").strip()

        features = self.shell("pm list features")
        disp = (props.get("ro.build.display.id", "") + " " + props.get("ro.product.model", "")).lower()
        mfg = props.get("ro.product.manufacturer", "").lower()

        if "amazon" in mfg or "aft" in props.get("ro.product.model", "").lower():
            props["device_type"] = "Amazon Fire TV (Fire OS)"
            props["profile_key"] = "fire-tv"
        elif any(k in disp for k in ("xview", "pont", "dvb", "tchip", "projector")):
            props["device_type"] = "Android Projector (Xview / PONT / DVB)"
            props["profile_key"] = "android-projector"
        elif "leanback" in features or "television" in features:
            props["device_type"] = "Android TV / Google TV"
            props["profile_key"] = "android-tv"
        else:
            props["device_type"] = "Android Phone / Tablet"
            props["profile_key"] = "android-phone"

        home_act = self.shell("cmd package resolve-activity --brief -c android.intent.category.HOME -a android.intent.action.MAIN").strip()
        props["current_home_launcher"] = home_act.splitlines()[-1].strip() if home_act else "Unknown"
        props["mac"] = det.get("mac", "N/A")
        return props

    def get_metrics(self) -> Dict[str, Any]:
        """Read RAM memory info and disk storage."""
        det = self.last_detection or self.detect()
        if det["profile_key"] == "roku" and 8060 in det.get("open_ports", {}):
            apps = device_detector.query_roku_apps(self.host)
            return {
                "ram_total_mb": 0,
                "ram_free_mb": 0,
                "ram_free_pct": 0,
                "storage_summary": f"{len(apps)} Roku channels installed (ECP active)"
            }

        meminfo = self.shell("cat /proc/meminfo")
        total_kb, avail_kb, free_kb, cached_kb = 0, 0, 0, 0
        for line in meminfo.splitlines():
            if line.startswith("MemTotal:"):
                total_kb = int(re.findall(r"\d+", line)[0])
            elif line.startswith("MemAvailable:"):
                avail_kb = int(re.findall(r"\d+", line)[0])
            elif line.startswith("MemFree:"):
                free_kb = int(re.findall(r"\d+", line)[0])
            elif line.startswith("Cached:"):
                cached_kb = int(re.findall(r"\d+", line)[0])

        if avail_kb == 0 and (free_kb or cached_kb):
            avail_kb = free_kb + cached_kb

        df_out = self.shell("df -h /data")
        storage_str = ""
        for line in df_out.splitlines():
            if "/data" in line or "%" in line:
                storage_str = line

        return {
            "ram_total_mb": round(total_kb / 1024, 1),
            "ram_free_mb": round(avail_kb / 1024, 1),
            "ram_used_mb": round((total_kb - avail_kb) / 1024, 1) if total_kb else 0,
            "ram_free_pct": round((avail_kb / total_kb) * 100, 1) if total_kb else 0,
            "storage_summary": storage_str.strip()
        }

    def backup_state(self) -> str:
        """Step 3 of RUNBOOK: Back up packages, disabled packages, settings, getprop, and HOME activity."""
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_ip = self.host.replace(".", "_")
        bdir = os.path.join(BACKUPS_DIR, f"{safe_ip}_{ts}")
        os.makedirs(bdir, exist_ok=True)

        files = {
            "packages-all.txt": self.shell("pm list packages"),
            "packages-disabled.txt": self.shell("pm list packages -d"),
            "packages-user.txt": self.shell("pm list packages -3"),
            "settings-global.txt": self.shell("settings list global"),
            "settings-secure.txt": self.shell("settings list secure"),
            "settings-system.txt": self.shell("settings list system"),
            "getprop.txt": self.shell("getprop"),
            "meminfo-before.txt": self.shell("cat /proc/meminfo"),
            "home-activity.txt": self.shell("cmd package resolve-activity -c android.intent.category.HOME"),
        }
        for fname, content in files.items():
            with open(os.path.join(bdir, fname), "w", encoding="utf-8") as f:
                f.write(content or "")

        return bdir

    def inventory(self) -> List[Dict[str, Any]]:
        """List all installed packages and classify into the 3 plain-English lists:
        safe_to_disable, needed_by_tv, user_app.
        Also supports Roku ECP app listing!
        """
        det = self.last_detection or self.detect()
        if det["profile_key"] == "roku" and 8060 in det.get("open_ports", {}):
            roku_apps = device_detector.query_roku_apps(self.host)
            return [{
                "package_id": f"roku.channel.{a['id']}",
                "plain_name": a["name"],
                "description": f"Roku Channel (v{a['version']})",
                "is_system": a["type"] != "appl",
                "is_disabled": False,
                "category": "user_app",
                "protected": False,
                "deny_reason": ""
            } for a in roku_apps]

        packages_3 = set(
            p.strip() for p in self.shell("pm list packages -3").replace("package:", "").splitlines() if p.strip()
        )
        packages_all = [
            p.strip() for p in self.shell("pm list packages").replace("package:", "").splitlines() if p.strip()
        ]
        disabled_set = set(
            p.strip() for p in self.shell("pm list packages -d").replace("package:", "").splitlines() if p.strip()
        )

        result = []
        for pkg in sorted(set(packages_all)):
            is_system = pkg not in packages_3
            denied, reason = device_guard.is_deny_listed(pkg)
            category = device_guard.classify_package(pkg, is_system=is_system)

            result.append({
                "package_id": pkg,
                "plain_name": device_guard.get_plain_name(pkg),
                "description": device_guard.get_description(pkg),
                "is_system": is_system,
                "is_disabled": pkg in disabled_set,
                "category": category,
                "protected": denied,
                "deny_reason": reason
            })
        return result

    def apply_disable(self, package: str, group_reason: str = "User approved optimization") -> Dict[str, Any]:
        """Safely disable a package after running guardrail and logging to undo-log."""
        pkg = package.strip()
        denied, reason = device_guard.is_deny_listed(pkg)
        if denied:
            event = {
                "ts": datetime.now().isoformat(),
                "device": self.host,
                "target": pkg,
                "plain_name": device_guard.get_plain_name(pkg),
                "action": "disable-user",
                "status": "guard_blocked",
                "reason": reason
            }
            self._log_undo(event)
            return {"success": False, "blocked": True, "error": f"GUARD BLOCKED: {reason}"}

        event = {
            "ts": datetime.now().isoformat(),
            "device": self.host,
            "target": pkg,
            "plain_name": device_guard.get_plain_name(pkg),
            "action": "disable-user",
            "approval": {"group": group_reason, "granted": True, "at": datetime.now().isoformat()},
            "undo": {"cmd": f"pm enable --user 0 {pkg}", "kind": "enable"},
            "status": "pending"
        }
        self._log_undo(event)

        out = self.shell(f"pm disable-user --user 0 {pkg}").strip()
        ok = "disabled-user" in out.lower() or "new state" in out.lower()
        event["status"] = "applied" if ok else "failed"
        event["evidence"] = out
        self._log_undo(event)

        return {"success": ok, "package": pkg, "plain_name": event["plain_name"], "output": out}

    def apply_enable(self, package: str) -> Dict[str, Any]:
        """Re-enable a disabled package."""
        pkg = package.strip()
        out = self.shell(f"pm enable --user 0 {pkg}").strip()
        ok = "enabled" in out.lower() or "new state" in out.lower()
        event = {
            "ts": datetime.now().isoformat(),
            "device": self.host,
            "target": pkg,
            "plain_name": device_guard.get_plain_name(pkg),
            "action": "enable",
            "status": "rolled-back" if ok else "failed",
            "evidence": out
        }
        self._log_undo(event)
        return {"success": ok, "package": pkg, "plain_name": event["plain_name"], "output": out}

    def optimize_settings(self, sleep_minutes: int = 5) -> Dict[str, Any]:
        """Disable animations, screensaver, and set sleep timer to 5 minutes (with undo logging)."""
        timeout_ms = sleep_minutes * 60 * 1000
        prev_win = self.shell("settings get global window_animation_scale").strip() or "1.0"
        prev_sleep = self.shell("settings get secure sleep_timeout").strip() or "1800000"

        cmds = [
            ("global", "window_animation_scale", "0", prev_win),
            ("global", "transition_animation_scale", "0", "1.0"),
            ("global", "animator_duration_scale", "0", "1.0"),
            ("secure", "sleep_timeout", str(timeout_ms), prev_sleep),
            ("system", "screen_off_timeout", str(timeout_ms), prev_sleep),
            ("secure", "screensaver_enabled", "0", "1"),
        ]
        executed = []
        for ns, key, val, prev in cmds:
            cmd_str = f"settings put {ns} {key} {val}"
            self.shell(cmd_str)
            executed.append(cmd_str)
            self._log_undo({
                "ts": datetime.now().isoformat(),
                "device": self.host,
                "target": f"{ns}:{key}",
                "plain_name": f"Setting {ns}.{key} = {val}",
                "action": "settings-put",
                "undo": {"cmd": f"settings put {ns} {key} {prev}", "kind": "restore-setting"},
                "status": "applied"
            })
        return {"success": True, "sleep_minutes": sleep_minutes, "commands": executed}

    def verify_state(self, baseline_ram_mb: Optional[float] = None) -> Dict[str, Any]:
        """Step 8 of RUNBOOK: Verify disabled apps stayed off after reboot and compare free RAM."""
        disabled_now = set(
            p.strip() for p in self.shell("pm list packages -d").replace("package:", "").splitlines() if p.strip()
        )
        expected_disabled = set()
        if os.path.exists(UNDO_LOG):
            with open(UNDO_LOG, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        row = json.loads(line)
                        if row.get("device") == self.host:
                            if row.get("action") == "disable-user" and row.get("status") == "applied":
                                expected_disabled.add(row["target"])
                            elif row.get("action") == "enable" and row.get("status") == "rolled-back":
                                expected_disabled.discard(row["target"])
                    except Exception:
                        pass

        stayed_off = sorted(expected_disabled.intersection(disabled_now))
        reverted = sorted(expected_disabled - disabled_now)
        metrics = self.get_metrics()
        delta_mb = round(metrics["ram_free_mb"] - baseline_ram_mb, 1) if baseline_ram_mb is not None else None

        return {
            "expected_disabled_count": len(expected_disabled),
            "stayed_off_count": len(stayed_off),
            "stayed_off": stayed_off,
            "reverted": reverted,
            "all_stayed_off": len(reverted) == 0,
            "ram_free_mb": metrics["ram_free_mb"],
            "ram_total_mb": metrics["ram_total_mb"],
            "ram_delta_mb": delta_mb,
        }

    def generate_report(self, before_metrics: Optional[Dict[str, Any]] = None) -> str:
        """Step 10 of RUNBOOK: Generate a Markdown optimization report in reports/."""
        os.makedirs(REPORTS_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_ip = self.host.replace(".", "_")
        report_path = os.path.join(REPORTS_DIR, f"{safe_ip}_{ts}.md")

        props = self.probe()
        after_metrics = self.get_metrics()
        before_ram = before_metrics["ram_free_mb"] if before_metrics else after_metrics["ram_free_mb"]
        total_ram = after_metrics["ram_total_mb"]
        diff_ram = round(after_metrics["ram_free_mb"] - before_ram, 1)

        applied_changes: Dict[str, Dict[str, Any]] = {}
        if os.path.exists(UNDO_LOG):
            with open(UNDO_LOG, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        row = json.loads(line)
                        if row.get("device") == self.host and row.get("status") == "applied":
                            applied_changes[row["target"]] = row
                        elif row.get("device") == self.host and row.get("status") == "rolled-back":
                            applied_changes.pop(row.get("target", ""), None)
                    except Exception:
                        pass

        md = [
            f"# Optimization Report — {props.get('ro.product.model', self.host)}",
            f"",
            f"- **IP Address:** `{self.host}`",
            f"- **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **Device Type:** {props.get('device_type', 'Unknown')}",
            f"- **Manufacturer / OS:** {props.get('ro.product.manufacturer', 'N/A')} (Android {props.get('ro.build.version.release', 'N/A')})",
            f"- **Stock Home Launcher:** `{props.get('current_home_launcher', 'N/A')}`",
            f"",
            f"## 1. Memory & Storage Comparison",
            f"",
            f"| Metric | Before | After | Gain |",
            f"|---|---|---|---|",
            f"| **Free RAM** | {before_ram} MB / {total_ram} MB | {after_metrics['ram_free_mb']} MB / {total_ram} MB | **{diff_ram:+.1f} MB** |",
            f"| **Storage (`/data`)** | `{after_metrics['storage_summary']}` | `{after_metrics['storage_summary']}` | No apps deleted |",
            f"",
            f"## 2. Changes Applied ({len(applied_changes)} items)",
            f"",
            f"| # | Plain Name | Target / Package | Action | How to Undo |",
            f"|---|---|---|---|---|",
        ]
        for idx, (target, info) in enumerate(applied_changes.items(), 1):
            undo_cmd = info.get("undo", {}).get("cmd", f"pm enable --user 0 {target}")
            md.append(f"| {idx} | {info.get('plain_name', target)} | `{target}` | `{info.get('action')}` | `{undo_cmd}` |")

        if not applied_changes:
            md.append("| - | No changes recorded yet | - | - | - |")

        md.extend([
            "",
            "## 3. One-Line Restore",
            "```powershell",
            f".\\tools\\adb.ps1 rollback -HostIp {self.host}",
            "```",
        ])

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md) + "\n")
        return report_path

    def rollback_all(self) -> List[Dict[str, Any]]:
        """Undo all applied changes for this device from undo-log.jsonl."""
        if not os.path.exists(UNDO_LOG):
            return []

        to_restore: Dict[str, Dict[str, Any]] = {}
        with open(UNDO_LOG, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    row = json.loads(line)
                    if row.get("device") != self.host:
                        continue
                    target = row.get("target", "")
                    if row.get("status") == "applied":
                        to_restore[target] = row
                    elif row.get("status") == "rolled-back":
                        to_restore.pop(target, None)
                except Exception:
                    pass

        restored = []
        for target, row in to_restore.items():
            undo_cmd = row.get("undo", {}).get("cmd")
            if row.get("action") == "disable-user":
                res = self.apply_enable(target)
                restored.append(res)
            elif undo_cmd:
                out = self.shell(undo_cmd).strip()
                self._log_undo({
                    "ts": datetime.now().isoformat(),
                    "device": self.host,
                    "target": target,
                    "action": "restore-setting",
                    "status": "rolled-back",
                    "evidence": out
                })
                restored.append({"success": True, "package": target, "output": out})
        return restored

    def reboot(self) -> None:
        self.shell("reboot")

    def _log_undo(self, event: Dict[str, Any]) -> None:
        with open(UNDO_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")


def cmd_probe(args, mgr: DeviceManager):
    det = mgr.detect()
    print(f"\n[1/2] Network & Platform Detection ({mgr.host}):")
    print(f"  • Status       : {'ONLINE' if det['reachable'] else 'OFFLINE'}")
    print(f"  • MAC / Vendor : {det['mac']} ({det['vendor']})")
    print(f"  • Profile      : {det['icon']} {det['profile_name']} [{det['capability']}]")
    print(f"  • Open Ports   : {det['open_ports'] if det['open_ports'] else 'None'}")

    props = mgr.probe()
    metrics = mgr.get_metrics()
    print("\n[2/2] Device Identity & Memory Baseline:")
    for k, v in props.items():
        print(f"  • {k}: {v}")
    print(f"\n  ★ FREE MEMORY RIGHT NOW: {metrics['ram_free_mb']} MB free of {metrics['ram_total_mb']} MB ({metrics['ram_free_pct']}%)")
    print(f"  ★ STORAGE (/data)      : {metrics['storage_summary']}")


def cmd_inventory(args, mgr: DeviceManager):
    items = mgr.inventory()
    metrics = mgr.get_metrics()
    safe = [i for i in items if i["category"] == "safe_to_disable"]
    needed = [i for i in items if i["category"] == "needed_by_tv"]
    user_apps = [i for i in items if i["category"] == "user_app"]

    print(f"\n======================================================================")
    print(f"📺 COMPLETE APP INVENTORY IN PLAIN ENGLISH: {mgr.host}")
    print(f"   Total Apps: {len(items)} | Free Memory: {metrics['ram_free_mb']} MB / {metrics['ram_total_mb']} MB ({metrics['ram_free_pct']}%)")
    print(f"======================================================================\n")

    print(f"🟢 1. SAFE TO TURN OFF ({len(safe)} apps) — Ads, Telemetry & Bloatware:")
    if not safe:
        print("   (None found)")
    for a in safe:
        state = " [ALREADY OFF]" if a["is_disabled"] else ""
        print(f"   • {a['plain_name']:<32} — {a['description']} ({a['package_id']}){state}")

    print(f"\n🔵 2. APPS YOU USE ({len(user_apps)} apps) — Streaming & Installed Apps:")
    if not user_apps:
        print("   (None found)")
    for a in user_apps:
        state = " [OFF]" if a["is_disabled"] else ""
        print(f"   • {a['plain_name']:<32} — {a['description']} ({a['package_id']}){state}")

    print(f"\n🔴 3. NEEDED BY THE TV ({len(needed)} apps) — Protected Core, Play Store, Bluetooth, Keyboard, HDMI:")
    for a in needed[:25]:
        print(f"   • {a['plain_name']:<32} — {a['description']} ({a['package_id']})")
    if len(needed) > 25:
        print(f"   ... plus {len(needed) - 25} other core system packages kept safe.")


def main():
    parser = argparse.ArgumentParser(description="Antigravity Multi-Platform Device Optimizer")
    parser.add_argument("--host", default=os.environ.get("TV_HOST"), help="Target Device IP address")
    parser.add_argument("--port", type=int, default=int(os.environ.get("TV_PORT", "5555")), help="ADB Port")

    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("scan-lan", help="Discover and classify all active devices on the LAN")
    sub.add_parser("detect", help="Smart multi-platform detection for target IP without requiring ADB")
    sub.add_parser("probe", help="Probe device identity and free memory")
    sub.add_parser("backup", help="Back up package lists, settings, and props before changing anything")
    sub.add_parser("inventory", help="Show every app in plain English split into 3 lists")

    p_dis = sub.add_parser("disable", help="Turn off a package (guarded, never uninstalled)")
    p_dis.add_argument("package", help="Package ID to disable")
    p_dis.add_argument("--reason", default="Manual disable", help="Approval reason")

    p_en = sub.add_parser("enable", help="Re-enable a package")
    p_en.add_argument("package", help="Package ID to enable")

    p_opt = sub.add_parser("optimize-settings", help="Turn off animations & screensaver, set 5m sleep")
    p_opt.add_argument("--sleep-minutes", type=int, default=5, help="Sleep timeout in minutes")

    sub.add_parser("verify", help="Verify disabled apps stayed off and check free memory")
    sub.add_parser("report", help="Generate Markdown optimization report")
    sub.add_parser("rollback", help="Undo all changes logged in undo-log.jsonl")
    sub.add_parser("reboot", help="Restart the device")

    args = parser.parse_args()

    if args.cmd == "scan-lan":
        devices = device_detector.scan_lan_devices()
        print(json.dumps(devices, indent=2, ensure_ascii=False))
        return

    if not args.host:
        sys.exit("Error: Please provide --host <DEVICE_IP> or set $env:TV_HOST")

    mgr = DeviceManager(args.host, args.port)
    try:
        if args.cmd == "detect":
            det = mgr.detect()
            print(mgr._format_diagnostic(det, "Detection mode"))
        elif args.cmd == "probe" or not args.cmd:
            cmd_probe(args, mgr)
        elif args.cmd == "backup":
            bdir = mgr.backup_state()
            print(f"Backup saved to: {bdir}")
        elif args.cmd == "inventory":
            cmd_inventory(args, mgr)
        elif args.cmd == "disable":
            res = mgr.apply_disable(args.package, args.reason)
            print(json.dumps(res, indent=2, ensure_ascii=False))
        elif args.cmd == "enable":
            res = mgr.apply_enable(args.package)
            print(json.dumps(res, indent=2, ensure_ascii=False))
        elif args.cmd == "optimize-settings":
            res = mgr.optimize_settings(args.sleep_minutes)
            print(json.dumps(res, indent=2, ensure_ascii=False))
        elif args.cmd == "verify":
            res = mgr.verify_state()
            print(json.dumps(res, indent=2, ensure_ascii=False))
        elif args.cmd == "report":
            path = mgr.generate_report()
            print(f"Report generated: {path}")
        elif args.cmd == "rollback":
            res = mgr.rollback_all()
            print(json.dumps(res, indent=2, ensure_ascii=False))
        elif args.cmd == "reboot":
            print(f"Rebooting device {args.host}...")
            mgr.reboot()
    except DeviceConnectionError as e:
        print(str(e))
        sys.exit(1)
    finally:
        mgr.close()


if __name__ == "__main__":
    main()
