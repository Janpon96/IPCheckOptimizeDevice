#!/usr/bin/env python3
"""device_guard.py - Guardrail engine and safety checks for device optimization.

Checks packages and actions against absolute deny-lists and safety rules.
"""

import re
from typing import Dict, List, Tuple

# Absolute deny-list packages & patterns that MUST NEVER be disabled or modified
ABSOLUTE_DENY_PATTERNS = [
    # Google core & store
    r"^com\.android\.vending$",
    r"^com\.google\.android\.gms$",
    r"^com\.google\.android\.gsf$",
    
    # Critical UI & settings & shell
    r"^com\.android\.systemui$",
    r"^com\.android\.settings$",
    r"^com\.android\.shell$",
    r"^com\.android\.providers\..*",
    r"^com\.android\.packageinstaller$",
    r"^com\.google\.android\.packageinstaller$",
    
    # Input, Remote & Bluetooth
    r"^com\.android\.bluetooth$",
    r".*bluetooth.*",
    r"^com\.google\.android\.inputmethod\..*",
    r".*latinime.*",
    r".*keyboard.*",
    
    # HDMI and TV input switcher
    r"^com\.android\.tv\.leanback$",
    r".*tvinput.*",
    r".*hdmi.*",
    r".*cec.*",
    r"^com\.google\.android\.apps\.mediashell$",  # Chromecast built-in
    
    # Hardware decoding on Android TV / Projectors (Amlogic, Rockchip, Allwinner)
    r"^com\.amlogic\..*",
    r"^com\.rockchip\..*",
    r"^com\.allwinner\..*",
    
    # Telephony & Emergency for phones
    r"^com\.android\.phone$",
    r"^com\.android\.dialer$",
    r"^com\.google\.android\.dialer$",
    r"^com\.android\.emergency$",
    r"^com\.android\.server\.telecom$",
    r"^com\.google\.android\.apps\.messaging$",
]

# Known stock launchers that should NEVER be disabled
STOCK_LAUNCHER_PATTERNS = [
    r"^com\.google\.android\.tvlauncher$",
    r"^com\.google\.android\.leanbacklauncher$",
    r"^com\.miui\.home$",
    r"^com\.miui\.tv\.home$",
    r"^com\.tcl\.tvlauncher$",
    r"^com\.hisense.*launcher.*",
    r"^com\.sony.*launcher.*",
    r"^com\.amazon\.tv\.launcher$",
    r"^com\.android\.launcher$",
    r"^com\.android\.launcher3$",
    r"^com\.samsung\.android\.app\.launcher$",
    r"^com\.oppo\.launcher$",
]

# Category definitions
CATEGORY_MAPPINGS = {
    "launcher": STOCK_LAUNCHER_PATTERNS,
    "store": [r"^com\.android\.vending$", r".*appstore.*", r"^com\.xiaomi\.mipicks$"],
    "core": [r"^com\.google\.android\.gms$", r"^com\.android\.systemui$", r"^com\.android\.settings$"],
    "bluetooth": [r".*bluetooth.*"],
    "keyboard": [r".*inputmethod.*", r".*keyboard.*", r".*ime.*"],
    "input-hdmi": [r".*hdmi.*", r".*leanback.*", r".*tvinput.*", r".*mediashell.*"],
    "ads-telemetry": [
        r".*adservice.*", r".*telemetry.*", r".*analytics.*", r".*bugreport.*",
        r".*crashlytics.*", r"^com\.miui\.tvads$", r"^com\.miui\.getapps$",
        r"^com\.amazon\.advertising$", r"^com\.amazon\.metrics$",
        r"^com\.bugsnag\.android$"
    ],
    "streaming": [
        r"^com\.netflix\.mediaclient$", r"^com\.google\.android\.youtube\.tv$",
        r"^com\.amazon\.amazonvideo\.livingroom$", r"^com\.spotify\.tv\.android$",
        r".*disney.*", r".*hbo.*", r".*kugou.*", r".*zingmp3.*", r".*wetv.*"
    ]
}

# Plain English friendly names for common packages
FRIENDLY_NAMES: Dict[str, str] = {
    # System & Critical
    "com.android.vending": "Google Play Store",
    "com.google.android.gms": "Google Play Services",
    "com.google.android.tvlauncher": "Android TV Home Screen",
    "com.google.android.leanbacklauncher": "Leanback Home Screen",
    "com.android.bluetooth": "Bluetooth Controller (Remote & Audio)",
    "com.google.android.inputmethod.latin": "Gboard On-screen Keyboard",
    "com.android.systemui": "System UI (Status Bar & Navigation)",
    "com.android.settings": "TV Settings",
    "com.android.tv.leanback": "TV & HDMI Input Switcher",
    "com.google.android.apps.mediashell": "Chromecast Built-in",
    
    # Bloatware & Ads - Xiaomi
    "com.miui.tvads": "Mi TV Video Ads",
    "com.miui.getapps": "Mi GetApps Ad Store",
    "com.miui.analyticsd": "Xiaomi Analytics & Tracker",
    "com.miui.bugreport": "Xiaomi Bug & Log Reporter",
    "com.xiaomi.mipicks": "Mi Picks App Store",
    "com.miui.tvhome.cloudplay": "Mi Cloud Gaming Service",
    "com.xiaomi.joyose": "Xiaomi Remote Service",
    "com.duokan.player": "Duokan Media Player",
    "com.miui.videoplayer": "Mi Stock Video Player",
    "com.miui.player": "Mi Stock Music Player",
    "com.bugsnag.android": "Bugsnag Crash Reporter",
    
    # Google TV & Android TV services
    "com.google.android.katniss": "Google Assistant Voice Search",
    "com.google.android.apps.wellness": "Digital Wellbeing",
    "com.google.android.apps.dream": "Stock Ambient Screensaver",
    "com.google.android.feedback": "Google Feedback Reporter",
    
    # Amazon Fire TV
    "com.amazon.advertising": "Amazon Ads Engine",
    "com.amazon.metrics": "Amazon Telemetry Service",
    "com.amazon.device.metrics": "Device Telemetry Service",
    "com.amazon.crowd": "Amazon Crowd Feedback",
    "com.amazon.shoppingapp": "Amazon Shopping on TV",
    "com.amazon.tv.recommendations": "Sponsored Recommendations Row",
    
    # Popular User Apps
    "com.netflix.mediaclient": "Netflix",
    "com.google.android.youtube.tv": "YouTube TV",
    "com.amazon.amazonvideo.livingroom": "Prime Video",
    "com.spotify.tv.android": "Spotify",
}


def is_deny_listed(package_name: str) -> Tuple[bool, str]:
    """Check if package is in absolute deny-list or protected launcher."""
    pkg = package_name.strip()
    
    for pat in ABSOLUTE_DENY_PATTERNS:
        if re.search(pat, pkg, re.IGNORECASE):
            return True, f"Matched absolute protected system pattern: {pat}"
            
    for pat in STOCK_LAUNCHER_PATTERNS:
        if re.search(pat, pkg, re.IGNORECASE):
            return True, f"Package is a protected Stock Launcher: {pat}"
            
    return False, ""


def get_plain_name(package_name: str) -> str:
    """Return friendly English plain name or format from package id."""
    if package_name in FRIENDLY_NAMES:
        return FRIENDLY_NAMES[package_name]
    
    # Fallback to readable string from package segments
    parts = package_name.split(".")
    candidate = parts[-1]
    if candidate.lower() in ("android", "app", "service", "client") and len(parts) > 1:
        candidate = f"{parts[-2]} {candidate}"
    return candidate.replace("_", " ").title()


def classify_package(package_name: str, is_system: bool = True) -> str:
    """Classify package into: protected, safe_to_disable, or user_app."""
    denied, reason = is_deny_listed(package_name)
    if denied:
        return "needed_by_tv"
        
    for pat in CATEGORY_MAPPINGS["ads-telemetry"]:
        if re.search(pat, package_name, re.IGNORECASE):
            return "safe_to_disable"
            
    for pat in CATEGORY_MAPPINGS["streaming"]:
        if re.search(pat, package_name, re.IGNORECASE):
            return "user_app"
            
    if not is_system:
        return "user_app"
        
    # Default for unknown system packages: keep safe or ask
    return "ask_user"
