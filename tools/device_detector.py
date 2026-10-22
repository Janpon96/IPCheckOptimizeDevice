#!/usr/bin/env python3
"""device_detector.py - Intelligent Multi-Platform Network & Device Detection Engine.

Automatically discovers devices on the LAN and classifies any target IP into one of the
9 supported device profiles (Android TV, Android Phone, Fire TV, Android Projector,
iOS iPhone/iPad, Roku, Samsung Tizen, LG webOS, Nintendo Switch / 3DS / DS, or Network Layer)
using ARP MAC OUI lookup, multi-port TCP probing, HTTP/ECP banner grabbing, and ADB properties.
"""

import re
import socket
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional, Tuple


# MAC OUI Prefix to Vendor mapping (normalized to uppercase XX:XX:XX)
OUI_VENDORS: Dict[str, Tuple[str, str]] = {
    # Apple (iPhone, iPad, Apple TV)
    "00:1C:B3": ("Apple", "ios"), "00:23:DF": ("Apple", "ios"), "28:CF:E9": ("Apple", "ios"),
    "3C:15:C2": ("Apple", "ios"), "40:33:1A": ("Apple", "ios"), "58:55:CA": ("Apple", "ios"),
    "60:F8:1D": ("Apple", "ios"), "70:DE:E2": ("Apple", "ios"), "84:38:35": ("Apple", "ios"),
    "A4:5E:60": ("Apple", "ios"), "AC:BC:32": ("Apple", "ios"), "B8:E8:56": ("Apple", "ios"),
    "C8:69:CD": ("Apple", "ios"), "D0:03:4B": ("Apple", "ios"), "F0:18:98": ("Apple", "ios"),
    "F8:FF:C2": ("Apple", "ios"),
    # Nintendo (Switch, 3DS, DS)
    "00:09:BF": ("Nintendo", "switch"), "00:16:56": ("Nintendo", "switch"),
    "00:17:AB": ("Nintendo", "switch"), "00:19:FD": ("Nintendo", "switch"),
    "00:1F:32": ("Nintendo", "switch"), "00:22:AA": ("Nintendo", "switch"),
    "00:24:F3": ("Nintendo", "switch"), "2C:10:C1": ("Nintendo", "switch"),
    "34:AF:2C": ("Nintendo", "switch"), "40:F4:07": ("Nintendo", "switch"),
    "58:BD:A3": ("Nintendo", "switch"), "70:48:F7": ("Nintendo", "switch"),
    "7C:BB:8A": ("Nintendo", "switch"), "98:B6:E9": ("Nintendo", "switch"),
    "A4:C0:E1": ("Nintendo", "switch"), "B8:AE:6E": ("Nintendo", "switch"),
    "D8:6B:F7": ("Nintendo", "switch"), "E0:E7:51": ("Nintendo", "switch"),
    # Xiaomi (Mi TV, Mi Box, Redmi)
    "00:9E:C8": ("Xiaomi", "android-tv"), "14:F6:5A": ("Xiaomi", "android-tv"),
    "28:6C:07": ("Xiaomi", "android-tv"), "34:CE:00": ("Xiaomi", "android-tv"),
    "50:64:2B": ("Xiaomi", "android-tv"), "64:09:80": ("Xiaomi", "android-tv"),
    "78:11:DC": ("Xiaomi", "android-tv"), "8C:BE:BE": ("Xiaomi", "android-tv"),
    "9C:99:A0": ("Xiaomi", "android-tv"), "B0:E2:35": ("Xiaomi", "android-tv"),
    # Samsung (Tizen TV / Galaxy)
    "00:12:47": ("Samsung", "tizen"), "00:15:99": ("Samsung", "tizen"),
    "08:08:C2": ("Samsung", "tizen"), "24:4B:03": ("Samsung", "tizen"),
    "48:44:F7": ("Samsung", "tizen"), "50:85:69": ("Samsung", "tizen"),
    "78:BD:BC": ("Samsung", "tizen"), "84:25:DB": ("Samsung", "tizen"),
    "BC:14:85": ("Samsung", "tizen"), "E4:7C:F9": ("Samsung", "tizen"),
    # LG (webOS TV)
    "00:1C:62": ("LG Electronics", "webos"), "00:1E:75": ("LG Electronics", "webos"),
    "00:E0:91": ("LG Electronics", "webos"), "10:68:3F": ("LG Electronics", "webos"),
    "34:4D:EA": ("LG Electronics", "webos"), "58:A2:B5": ("LG Electronics", "webos"),
    "64:BC:0C": ("LG Electronics", "webos"), "A8:23:FE": ("LG Electronics", "webos"),
    # Sony (BRAVIA Android TV)
    "00:13:A9": ("Sony", "android-tv"), "00:1D:BA": ("Sony", "android-tv"),
    "24:21:AB": ("Sony", "android-tv"), "54:42:49": ("Sony", "android-tv"),
    "FC:F1:52": ("Sony", "android-tv"),
    # TCL / Hisense
    "00:24:68": ("TCL", "android-tv"), "38:76:CA": ("TCL", "android-tv"),
    "C4:36:55": ("TCL", "android-tv"), "00:1A:9A": ("Hisense", "android-tv"),
    # Amazon (Fire TV)
    "00:FC:8B": ("Amazon", "fire-tv"), "0C:47:C9": ("Amazon", "fire-tv"),
    "34:D2:70": ("Amazon", "fire-tv"), "44:65:0D": ("Amazon", "fire-tv"),
    "68:37:E9": ("Amazon", "fire-tv"), "74:C2:46": ("Amazon", "fire-tv"),
    "84:D6:D0": ("Amazon", "fire-tv"), "B4:7C:9C": ("Amazon", "fire-tv"),
    # Roku
    "00:0D:4B": ("Roku", "roku"), "08:05:81": ("Roku", "roku"),
    "AC:3A:7A": ("Roku", "roku"), "B0:A7:37": ("Roku", "roku"),
    "CC:6D:A0": ("Roku", "roku"), "D8:31:34": ("Roku", "roku"),
}

# Ports used to fingerprint device OS/platform over LAN
PROBE_PORTS: Dict[int, str] = {
    5555: "Android ADB over Wi-Fi",
    62078: "Apple iOS Lockdown / iPhone Sync",
    49152: "Apple AirPlay / UPnP",
    7000: "Apple AirPlay Receiver",
    8060: "Roku ECP REST API",
    8001: "Samsung Tizen SmartTV API",
    8002: "Samsung Tizen SmartTV TLS API",
    3000: "LG webOS SSAP Service",
    3001: "LG webOS SSAP TLS Service",
    8008: "Google Cast / Chromecast HTTP",
    8009: "Google Cast / Chromecast TLS",
    53: "DNS Server / Pi-hole / Router",
    80: "Web UI / Router / HTTP",
}

PROFILE_METADATA: Dict[str, Dict[str, str]] = {
    "android-tv": {
        "name": "Android TV / Google TV",
        "capability": "FULL",
        "doc": "docs/profiles/01-android-tv-google-tv.md",
        "transport": "ADB TCP :5555",
        "icon": "📺",
        "guide": (
            "1. Trên TV: Settings -> Device Preferences -> About -> bấm OK 7 lần vào 'Build'.\n"
            "2. Quay lại -> Developer options -> Bật 'USB debugging' (và 'Network debugging').\n"
            "3. Khi bấm kết nối trên tool này, nhìn lên TV chọn 'Always allow from this computer' -> OK."
        )
    },
    "android-phone": {
        "name": "Android Phone / Tablet",
        "capability": "FULL",
        "doc": "docs/profiles/02-android-phone-tablet.md",
        "transport": "ADB TCP :5555",
        "icon": "📱",
        "guide": (
            "1. Trên điện thoại: Settings -> About phone -> chạm 7 lần vào 'Build number'.\n"
            "2. Settings -> System -> Developer options -> Bật 'USB debugging' & 'Wireless debugging'.\n"
            "3. Cho phép hộp thoại xác nhận RSA trên màn hình điện thoại."
        )
    },
    "fire-tv": {
        "name": "Amazon Fire TV (Fire OS)",
        "capability": "PARTIAL",
        "doc": "docs/profiles/03-fire-tv.md",
        "transport": "ADB TCP :5555",
        "icon": "🔥",
        "guide": (
            "1. Trên Fire TV: Settings -> My Fire TV -> About -> bấm Select 7 lần vào tên Fire TV.\n"
            "2. Quay lại -> Developer Options -> Bật 'ADB Debugging'.\n"
            "3. Lưu ý: Fire OS cho phép tắt quảng cáo & telemetry nhưng khóa đổi Launcher."
        )
    },
    "android-projector": {
        "name": "Máy chiếu Android / Xview / PONT",
        "capability": "FULL",
        "doc": "docs/profiles/04-android-projector-xview.md",
        "transport": "ADB TCP :5555",
        "icon": "📽️",
        "guide": (
            "1. Nhiều máy chiếu Xview/PONT đã mở sẵn cổng ADB 5555.\n"
            "2. Nếu chưa mở: Settings -> About -> bấm OK 7 lần vào Build -> Developer options -> USB debugging ON.\n"
            "3. Cảnh báo: Tool tự động bảo vệ các gói giải mã HDMI của Amlogic/Rockchip."
        )
    },
    "ios": {
        "name": "Apple iPhone / iPad (iOS)",
        "capability": "PARTIAL",
        "doc": "docs/profiles/05-ios-iphone-ipad.md",
        "transport": "iOS Lockdown / Guided Optimization",
        "icon": "🍎",
        "guide": (
            "iOS KHÔNG dùng giao thức ADB của Android (vì vậy cổng 5555 luôn đóng).\n\n"
            "✦ CÁCH TỐI ƯU IPHONE NGAY LẬP TỨC:\n"
            "  1. Xóa RAM chạy ngầm: Bật AssistiveTouch (Home ảo) -> Vào Cài đặt -> Cài đặt chung -> Tắt máy\n"
            "     -> Mở Home ảo, nhấn giữ nút 'Màn hình chính' 3 giây tới khi chớp màn hình.\n"
            "  2. Tắt Làm mới ứng dụng nền: Cài đặt -> Cài đặt chung -> Làm mới ứng dụng trong nền -> Tắt.\n"
            "  3. Dọn dung lượng: Cài đặt -> Cài đặt chung -> Dung lượng iPhone -> Gỡ bỏ ứng dụng không dùng.\n"
            "  4. Để liệt kê app từ PC: Cắm cáp USB 1 lần để Trust và dùng pymobiledevice3."
        )
    },
    "switch": {
        "name": "Nintendo Switch",
        "capability": "MANUAL",
        "doc": "docs/profiles/06-nintendo-switch.md",
        "transport": "Guided + Router DNS Layer",
        "icon": "🎮",
        "guide": (
            "Nintendo Switch không mở cổng quản trị qua IP mạng.\n\n"
            "✦ CÁCH TỐI ƯU SWITCH:\n"
            "  1. Trên máy: System Settings -> System -> Automatic Software Updates = OFF.\n"
            "  2. Themes -> chọn 'Basic Black' (nhẹ RAM và tiết kiệm pin hơn).\n"
            "  3. System Settings -> Sleep Mode -> Auto-Sleep (Playing on Console Screen) = 5 min.\n"
            "  4. Tầng mạng: Chặn lgt.api.nintendo.net & *.nintendo.net trên Router/Pi-hole để chặn telemetry."
        )
    },
    "nintendo-3ds-ds": {
        "name": "Nintendo 3DS / 2DS / DS",
        "capability": "MANUAL",
        "doc": "docs/profiles/07-nintendo-3ds-ds.md",
        "transport": "Guided + Router DNS Layer",
        "icon": "🕹️",
        "guide": (
            "Máy cầm tay 3DS/DS hoạt động offline-first và không có API mạng.\n\n"
            "✦ CÁCH TỐI ƯU:\n"
            "  1. System Settings -> Internet Settings -> SpotPass = OFF.\n"
            "  2. StreetPass Mii Plaza -> Settings -> StreetPass = OFF.\n"
            "  3. Giảm độ sáng màn hình và tắt Power-Saving Mode nếu màu bị nhạt."
        )
    },
    "roku": {
        "name": "Roku TV / Roku Streaming",
        "capability": "FULL (ECP)",
        "doc": "docs/profiles/08-roku-tizen-webos.md",
        "transport": "Roku ECP HTTP :8060",
        "icon": "🟣",
        "guide": (
            "Roku hỗ trợ giao thức điều khiển và liệt kê ứng dụng trực tiếp qua cổng HTTP 8060!\n"
            "Bấm 'View All Apps' để lấy danh sách kênh đã cài trên Roku, hoặc tối ưu Screensaver."
        )
    },
    "tizen": {
        "name": "Samsung Smart TV (Tizen OS)",
        "capability": "PARTIAL",
        "doc": "docs/profiles/08-roku-tizen-webos.md",
        "transport": "Tizen API :8001/:8002 + Guided",
        "icon": "📺",
        "guide": (
            "Samsung TV chạy Tizen OS (không phải Android).\n\n"
            "✦ CÁCH TỐI ƯU SAMSUNG TV:\n"
            "  1. Settings -> General -> Smart Features -> Tắt 'Autorun Smart Hub' & 'Autorun Last App'.\n"
            "  2. Settings -> Support -> Device Care -> Bấm 'Start Device Care' để giải phóng RAM & bộ nhớ đệm.\n"
            "  3. Settings -> General -> System Manager -> Time -> Sleep Timer = 5 phút.\n"
            "  4. Chặn quảng cáo: Thêm *.samsungads.com, *.samsungadhub.com vào DNS Router / Pi-hole."
        )
    },
    "webos": {
        "name": "LG Smart TV (webOS)",
        "capability": "PARTIAL",
        "doc": "docs/profiles/08-roku-tizen-webos.md",
        "transport": "webOS SSAP :3000/:3001 + Guided",
        "icon": "📺",
        "guide": (
            "LG TV chạy hệ điều hành webOS (không phải Android).\n\n"
            "✦ CÁCH TỐI ƯU LG WEBOS:\n"
            "  1. Settings -> General -> Additional Settings -> Tắt 'Live Plus' và 'Home Promotion' (Quảng cáo).\n"
            "  2. Settings -> General -> Quick Start+ = OFF (Giúp xóa sạch RAM mỗi khi tắt TV).\n"
            "  3. Chặn quảng cáo: Thêm *.lgadplatform.com, ad.lg.com vào DNS Router / Pi-hole."
        )
    },
    "network": {
        "name": "Router / DNS / Network Gateway",
        "capability": "FULL (DNS/QoS)",
        "doc": "docs/profiles/09-network-layer.md",
        "transport": "HTTP :80 / DNS :53",
        "icon": "🌐",
        "guide": (
            "Đây là thiết bị mạng (Router / Gateway / Pi-hole).\n"
            "Tối ưu tầng mạng giúp chặn quảng cáo cho TOÀN BỘ thiết bị trong nhà (kể cả iPhone, Switch, Samsung/LG TV)."
        )
    }
}


def check_ping(ip: str, timeout_ms: int = 800) -> bool:
    """Ping an IP address once on Windows."""
    try:
        res = subprocess.run(
            ["ping", "-n", "1", "-w", str(timeout_ms), ip],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        )
        return "TTL=" in res.stdout.upper()
    except Exception:
        return False


def get_arp_table() -> Dict[str, str]:
    """Parse Windows `arp -a` table and return {ip: normalized_mac}."""
    mapping: Dict[str, str] = {}
    try:
        out = subprocess.check_output(
            ["arp", "-a"], text=True, errors="ignore",
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        )
        for line in out.splitlines():
            m = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F\-]{17})\s+(\w+)", line)
            if m:
                ip, mac, kind = m.group(1), m.group(2).replace("-", ":").upper(), m.group(3)
                if not ip.endswith(".255") and not ip.startswith("224.") and not ip.startswith("239."):
                    mapping[ip] = mac
    except Exception:
        pass
    return mapping


def lookup_mac_vendor(mac: str) -> Tuple[str, Optional[str]]:
    """Return (vendor_name, hinted_profile) from MAC address."""
    if not mac or len(mac) < 8:
        return ("Unknown Vendor", None)
    prefix = mac[:8].upper()
    if prefix in OUI_VENDORS:
        return OUI_VENDORS[prefix]
    try:
        first_byte = int(mac[:2], 16)
        if first_byte & 0b00000010:
            return ("Randomized Private MAC (iPhone / Modern Android)", None)
    except ValueError:
        pass
    return ("Generic Network Device", None)


def scan_open_ports(ip: str, timeout: float = 0.45) -> Dict[int, str]:
    """Concurrently probe known device fingerprint ports on target IP."""
    open_ports: Dict[int, str] = {}

    def _probe(port: int) -> Optional[int]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            if s.connect_ex((ip, port)) == 0:
                return port
        except Exception:
            pass
        finally:
            s.close()
        return None

    with ThreadPoolExecutor(max_workers=len(PROBE_PORTS)) as ex:
        futures = {ex.submit(_probe, p): p for p in PROBE_PORTS}
        for fut in as_completed(futures):
            p = fut.result()
            if p is not None:
                open_ports[p] = PROBE_PORTS[p]
    return dict(sorted(open_ports.items()))


def query_roku_info(ip: str) -> Optional[Dict[str, str]]:
    """Query Roku ECP device-info on port 8060 if available."""
    try:
        url = f"http://{ip}:8060/query/device-info"
        req = urllib.request.Request(url, headers={"User-Agent": "Antigravity-Optimizer/2.0"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            xml_data = resp.read().decode("utf-8", errors="ignore")
            root = ET.fromstring(xml_data)
            info = {}
            for tag in ("model-name", "friendly-device-name", "software-version", "vendor-name"):
                el = root.find(tag)
                if el is not None and el.text:
                    info[tag] = el.text.strip()
            return info
    except Exception:
        return None


def query_roku_apps(ip: str) -> List[Dict[str, str]]:
    """List installed channels on a Roku device via HTTP 8060."""
    apps = []
    try:
        url = f"http://{ip}:8060/query/apps"
        with urllib.request.urlopen(url, timeout=3.0) as resp:
            root = ET.fromstring(resp.read().decode("utf-8", errors="ignore"))
            for app in root.findall("app"):
                apps.append({
                    "id": app.attrib.get("id", ""),
                    "type": app.attrib.get("type", "appl"),
                    "version": app.attrib.get("version", ""),
                    "name": (app.text or "").strip()
                })
    except Exception:
        pass
    return apps


def detect_device(ip: str) -> Dict[str, Any]:
    """Full multi-signal detection of a target IP address."""
    reachable = check_ping(ip, timeout_ms=700)
    arp_table = get_arp_table()
    mac = arp_table.get(ip, "")
    if mac:
        reachable = True

    vendor, mac_profile_hint = lookup_mac_vendor(mac)
    open_ports = scan_open_ports(ip, timeout=0.45)
    if open_ports:
        reachable = True

    profile_key = "android-tv"
    confidence = "Low"
    details: Dict[str, Any] = {}

    if 8060 in open_ports:
        profile_key = "roku"
        confidence = "High (Port 8060 ECP Open)"
        roku_info = query_roku_info(ip)
        if roku_info:
            details.update(roku_info)
    elif 5555 in open_ports:
        profile_key = mac_profile_hint if mac_profile_hint in ("fire-tv", "android-projector", "android-phone") else "android-tv"
        confidence = "High (Port 5555 ADB Open)"
    elif 62078 in open_ports or 7000 in open_ports or mac_profile_hint == "ios":
        profile_key = "ios"
        confidence = "High (Apple Lockdown/AirPlay or MAC)"
    elif 8001 in open_ports or 8002 in open_ports or mac_profile_hint == "tizen":
        profile_key = "tizen"
        confidence = "High (Samsung SmartTV Port/MAC)"
    elif 3000 in open_ports or 3001 in open_ports or mac_profile_hint == "webos":
        profile_key = "webos"
        confidence = "High (LG webOS Port/MAC)"
    elif mac_profile_hint == "switch":
        profile_key = "switch"
        confidence = "High (Nintendo MAC OUI)"
    elif ip.endswith(".1") or 53 in open_ports:
        profile_key = "network"
        confidence = "High (Gateway / DNS Port 53)"
    elif 8008 in open_ports or 8009 in open_ports:
        profile_key = "android-tv"
        confidence = "Medium (Google Cast Port 8008/8009 Open - ADB 5555 currently OFF)"
    elif "Randomized Private MAC" in vendor and reachable and not open_ports:
        profile_key = "ios"
        confidence = "Medium (Reachable on LAN with Randomized MAC & Closed Ports - Typical iPhone/iOS or Android with ADB Off)"

    meta = PROFILE_METADATA.get(profile_key, PROFILE_METADATA["android-tv"])

    return {
        "ip": ip,
        "reachable": reachable,
        "mac": mac or "N/A",
        "vendor": vendor,
        "open_ports": open_ports,
        "profile_key": profile_key,
        "profile_name": meta["name"],
        "capability": meta["capability"],
        "transport": meta["transport"],
        "doc": meta["doc"],
        "icon": meta["icon"],
        "confidence": confidence,
        "guide": meta["guide"],
        "extra": details,
    }


def scan_lan_devices() -> List[Dict[str, Any]]:
    """Discover all active devices in local ARP cache and classify them."""
    arp = get_arp_table()
    results: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(detect_device, ip): ip for ip in arp.keys()}
        for fut in as_completed(futures):
            try:
                info = fut.result()
                results.append(info)
            except Exception:
                pass

    results.sort(key=lambda x: [int(p) for p in x["ip"].split(".")])
    return results


if __name__ == "__main__":
    import sys, json
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if len(sys.argv) > 1 and sys.argv[1] != "--scan":
        print(json.dumps(detect_device(sys.argv[1]), indent=2, ensure_ascii=False))
    else:
        print(json.dumps(scan_lan_devices(), indent=2, ensure_ascii=False))
