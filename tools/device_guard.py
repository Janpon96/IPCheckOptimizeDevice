#!/usr/bin/env python3
"""device_guard.py - Guardrail engine, package taxonomy, and friendly names database.

Enforces the absolute deny-list from SAFETY.md and classifies packages across
Xiaomi/Redmi, TCL, Sony BRAVIA, Hisense, NVIDIA Shield, OnePlus, Chromecast,
Amazon Fire TV, and Android Projectors (Xview/PONT/DVB).
"""

import re
from typing import Dict, List, Tuple

# =====================================================================
# 1. ABSOLUTE DENY-LIST (NEVER DISABLE UNDER ANY CIRCUMSTANCES)
# =====================================================================
ABSOLUTE_DENY_PATTERNS: List[str] = [
    # Google Play Store & Core Services (Explicit user requirement)
    r"^com\.android\.vending$",
    r"^com\.google\.android\.gms$",
    r"^com\.google\.android\.gsf$",
    r"^com\.google\.android\.gsf\.login$",

    # Critical System UI, Settings, Package Installer & Shell
    r"^com\.android\.systemui$",
    r"^com\.android\.settings$",
    r"^com\.android\.tv\.settings$",
    r"^com\.android\.shell$",
    r"^com\.android\.providers\..*",
    r"^com\.android\.packageinstaller$",
    r"^com\.google\.android\.packageinstaller$",
    r"^com\.android\.permissioncontroller$",
    r"^com\.google\.android\.permissioncontroller$",
    r"^android$",

    # Bluetooth & Remote Control (Explicit user requirement: remote needs it)
    r"^com\.android\.bluetooth$",
    r".*bluetooth.*",
    r"^com\.amazon\.device\.controllermanager$",
    r"^com\.tcl\.autopair$",

    # Keyboards / Input Methods (Explicit user requirement)
    r"^com\.google\.android\.inputmethod\..*",
    r"^com\.android\.inputmethod\..*",
    r".*latinime.*",
    r".*keyboard.*",

    # HDMI Inputs, TV Tuner, CEC & Input Switchers (Explicit user requirement)
    r"^com\.android\.tv\.leanback$",
    r"^com\.android\.tv$",
    r"^com\.tcl\.tv$",
    r"^com\.tcl\.tvinput$",
    r"^com\.tcl\.dashboard$",
    r"^com\.sony\.dtv\.tvx$",
    r"^com\.sony\.dtv\.tvinput\..*",
    r"^com\.sony\.dtv\.braviasync.*",
    r"^com\.sony\.dtv\.sonysystemservice$",
    r"^com\.amazon\.tv\.livetv$",
    r"^com\.amazon\.tv\.quicksettings$",
    r"^com\.amazon\.tv\.settings\.v2$",
    r".*tvinput.*",
    r".*hdmi.*",
    r".*cec.*",
    r".*inputswitch.*",

    # Hardware Video/HDMI Decoders on Android Projectors / SoCs (Amlogic, Rockchip, Allwinner)
    r"^com\.amlogic\..*",
    r"^com\.rockchip\..*",
    r"^com\.allwinner\..*",
    r"^com\.realtek\.tv\..*",

    # Telephony & Emergency for Android Phones
    r"^com\.android\.phone$",
    r"^com\.android\.dialer$",
    r"^com\.google\.android\.dialer$",
    r"^com\.android\.emergency$",
    r"^com\.android\.server\.telecom$",
    r"^com\.google\.android\.apps\.messaging$",
]

# Stock launchers are kept ENABLED so the user can always restore Home in 1 line
STOCK_LAUNCHER_PATTERNS: List[str] = [
    r"^com\.google\.android\.tvlauncher$",
    r"^com\.google\.android\.apps\.tv\.launcherx$",
    r"^com\.google\.android\.leanbacklauncher$",
    r"^com\.miui\.home$",
    r"^com\.miui\.tv\.home$",
    r"^com\.tcl\.tvlauncher$",
    r"^com\.hisense.*launcher.*",
    r"^com\.sony.*launcher.*",
    r"^com\.amazon\.tv\.launcher$",
    r"^com\.amazon\.firehomestarter$",
    r"^com\.android\.launcher$",
    r"^com\.android\.launcher3$",
    r"^com\.samsung\.android\.app\.launcher$",
    r"^com\.oppo\.launcher$",
]

# =====================================================================
# 2. KNOWN SAFE-TO-DISABLE BLOATWARE / ADS / TELEMETRY PATTERNS
# =====================================================================
SAFE_DEBLOAT_PATTERNS: List[str] = [
    # Generic Ads, Telemetry, Crash Reporters, Demo Modes
    r".*adservice.*",
    r".*telemetry.*",
    r".*analytics.*",
    r".*bugreport.*",
    r".*crashlytics.*",
    r"^com\.bugsnag\.android$",
    r"^tv\.samba\.ssm.*",
    r"^com\.google\.android\.feedback$",
    r"^com\.google\.android\.tvrecommendations$",
    r"^com\.google\.android\.leanbacklauncher\.recommendations$",
    r"^fusion\.android\.tv\.demo$",

    # Xiaomi / Redmi / PatchWall Bloatware
    r"^com\.miui\.tvads$",
    r"^com\.miui\.getapps$",
    r"^com\.miui\.analyticsd$",
    r"^com\.miui\.tv\.analytics$",
    r"^com\.xiaomi\.statistic$",
    r"^com\.xiaomi\.mipicks$",
    r"^com\.miui\.tvhome\.cloudplay$",
    r"^com\.mitv\.tvhome\.atv$",
    r"^com\.mitv\.tvhome\.michannel$",
    r"^com\.mitv\.tvhome\.mitvplus$",
    r"^com\.xm\.webcontent$",
    r"^com\.xiaomi\.floatingframe$",
    r"^com\.xiaomi\.mitv\.tvmanager$",
    r"^com\.xiaomi\.mitv\.smartshare$",
    r"^com\.Xiaomi\.joyose$",
    r"^com\.xiaomi\.joyose$",
    r"^android\.autoinstalls\.config\.xiaomi\..*",

    # TCL Google TV / Android TV Bloatware
    r"^com\.tcl\.tv\.plus$",
    r"^com\.tcl\.channelplus$",
    r"^com\.tcl\.tv\.tclhome_passive$",
    r"^com\.tcl\.partnercustomizer$",
    r"^com\.tcl\.interactive$",
    r"^com\.tcl\.smartlink\.core$",
    r"^com\.tcl\.exhibit$",
    r"^com\.tcl\.esticker$",
    r"^com\.tcl\.ocean\.instructions$",
    r"^com\.tcl\.repairguide$",
    r"^android\.autoinstalls\.config\.google\.gtvpai$",

    # Sony BRAVIA Bloatware & Retail Demo
    r"^com\.qterics\.da\.product$",
    r"^com\.sony\.dtv\.da\.service$",
    r"^com\.sonyericsson\.idd\.agent$",
    r"^com\.sony\.dtv\.promos$",
    r"^com\.sony\.dtv\.sonyselect$",
    r"^com\.sony\.dtv\.demosupport$",
    r"^com\.sony\.dtv\.demosystemsupport$",
    r"^com\.sony\.dtv\.multiscreendemo$",

    # Amazon Fire TV Ads & Telemetry
    r"^com\.amazon\.advertising$",
    r"^com\.amazon\.tv\.acr$",
    r"^com\.amazon\.metrics$",
    r"^com\.amazon\.device\.metrics$",
    r"^com\.amazon\.client\.metrics$",
    r"^com\.amazon\.client\.metrics\.api$",
    r"^com\.amazon\.device\.logmanager$",
    r"^com\.amazon\.dp\.logger$",
    r"^com\.amazon\.perfcollection$",
    r"^com\.amazon\.perfc$",
    r"^com\.amazon\.tv\.fw\.metrics$",
    r"^com\.amazon\.wirelessmetrics\.service$",
    r"^com\.amazon\.device\.crashmanager$",
    r"^com\.amazon\.hybridadidservice$",
    r"^com\.amazon\.ftvads\.deeplinking$",
    r"^com\.amazon\.tv\.recommendations$",
    r"^com\.amazon\.media\.recommendations$",
    r"^com\.amazon\.tv\.democontent\.provider$",
    r"^com\.amazon\.sneakpeek$",
    r"^com\.amazon\.shoptv\..*",
    r"^com\.amazon\.shoppingapp$",
    r"^com\.amazon\.crowd$",
]

# Streaming & User-facing apps
STREAMING_PATTERNS: List[str] = [
    r"^com\.netflix\..*",
    r"^com\.google\.android\.youtube\..*",
    r"^com\.amazon\.amazonvideo\..*",
    r"^com\.amazon\.avod$",
    r"^com\.spotify\..*",
    r"^com\.disney\..*",
    r"^com\.hbo\..*",
    r"^com\.plexapp\..*",
    r"^org\.xbmc\.kodi$",
    r"^com\.stremio\..*",
    r"^com\.smarttube\..*",
    r"^com\.liskovsoft\.smarttubetv\..*",
    r".*kugou.*",
    r".*zingmp3.*",
    r".*fptplay.*",
    r".*vieon.*",
    r".*vtvgo.*",
    r".*tv360.*",
    r".*mytv.*",
    r".*kplus.*",
    r".*wetv.*",
    r".*iqiyi.*",
]

# =====================================================================
# 3. PLAIN ENGLISH DICTIONARY (name + description)
# =====================================================================
FRIENDLY_DB: Dict[str, Tuple[str, str]] = {
    # Protected Core / Store / Input / Bluetooth / Keyboard
    "com.android.vending": ("Google Play Store", "Official app store - Required to install/update apps"),
    "com.google.android.gms": ("Google Play Services", "Core background services required by Google & apps"),
    "com.google.android.gsf": ("Google Services Framework", "Core account & push notification framework"),
    "com.google.android.tvlauncher": ("Android TV Home Launcher", "Stock home screen (kept enabled for easy restore)"),
    "com.google.android.apps.tv.launcherx": ("Google TV Home Launcher", "Stock Google TV home screen (kept enabled for restore)"),
    "com.google.android.leanbacklauncher": ("Leanback Home Launcher", "Stock Android TV launcher"),
    "com.android.bluetooth": ("Bluetooth Service", "Drives your voice remote & Bluetooth headphones"),
    "com.google.android.inputmethod.latin": ("Gboard Keyboard", "On-screen keyboard for typing searches & passwords"),
    "com.android.systemui": ("System UI", "Volume bar, notifications & system overlays"),
    "com.android.settings": ("System Settings", "Main device settings menu"),
    "com.android.tv.settings": ("TV Settings", "Main Android TV settings menu"),
    "com.android.tv.leanback": ("TV & HDMI Input Switcher", "Handles HDMI 1/2/3 ports and Live TV inputs"),
    "com.android.tv": ("Live TV & HDMI Input App", "System app for switching HDMI ports and antenna channels"),
    "com.tcl.tv": ("TCL Live TV & HDMI Input", "Controls HDMI ports and TV tuner on TCL sets"),
    "com.tcl.tvinput": ("TCL HDMI Input Service", "Required for HDMI port switching on TCL TVs"),
    "com.sony.dtv.tvx": ("Sony BRAVIA TV & HDMI Input", "Controls HDMI ports and tuner on Sony TVs"),
    "com.google.android.apps.mediashell": ("Chromecast Built-in", "Lets you cast videos from your phone/laptop to the TV"),

    # Xiaomi / Redmi Bloatware
    "com.miui.tvads": ("Mi TV System Ads", "Shows video/banner ads on start and home screen"),
    "com.miui.getapps": ("Mi GetApps Store", "Xiaomi promotional app store with notifications"),
    "com.miui.analyticsd": ("Xiaomi Analytics Daemon", "Tracks viewing & usage habits in the background"),
    "com.miui.tv.analytics": ("Mi TV Analytics", "Sends telemetry data back to Xiaomi servers"),
    "com.xiaomi.statistic": ("Xiaomi Usage Statistics", "Background usage telemetry service"),
    "com.miui.bugreport": ("Xiaomi Bug Reporter", "Collects and uploads crash logs"),
    "com.xiaomi.mipicks": ("Mi Picks Store", "Duplicate manufacturer app store"),
    "com.miui.tvhome.cloudplay": ("Mi Cloud Gaming", "Preloaded cloud gaming promo service"),
    "com.mitv.tvhome.atv": ("PatchWall Home Content", "Xiaomi PatchWall promotional content rows"),
    "com.mitv.tvhome.michannel": ("Mi Channel Row", "Xiaomi promotional channel feed on home screen"),
    "com.mitv.tvhome.mitvplus": ("Mi TV+ Streaming Promo", "Xiaomi free ad-supported channels service"),
    "com.xm.webcontent": ("Xiaomi Web Promo View", "Renders promotional web banners on the TV"),
    "com.xiaomi.floatingframe": ("Xiaomi Floating Ad Frame", "Shows pop-up promotional overlays"),
    "com.xiaomi.mitv.tvmanager": ("Mi TV Cleaner / Manager", "Background manager app not needed after debloat"),
    "com.xiaomi.mitv.smartshare": ("Mi SmartShare", "Proprietary screen sharing (Chromecast still works)"),
    "com.mitv.milinkservice": ("MiLink Cast Service", "Proprietary Xiaomi casting service"),
    "com.xiaomi.mitv.updateservice": ("Xiaomi OTA Update Service", "Checks for system firmware updates"),
    "com.xiaomi.amazon.alexa": ("Xiaomi Alexa Bridge", "Connects TV to Amazon Echo devices"),
    "com.xiaomi.mimusic2": ("Mi Music Player", "Preloaded music player app"),
    "com.xiaomi.joyose": ("Xiaomi Joyose Telemetry", "Background cloud config & telemetry service"),
    "com.duokan.player": ("Duokan Video Player", "Preloaded Xiaomi media player"),
    "com.miui.videoplayer": ("Mi Stock Video Player", "Preloaded video player"),
    "com.miui.player": ("Mi Stock Music Player", "Preloaded audio player"),
    "com.bugsnag.android": ("Bugsnag Crash Reporter", "Third-party error reporting telemetry"),

    # TCL Bloatware
    "com.tcl.tv.plus": ("TCL TV+ Content App", "TCL ad-supported promotional streaming app"),
    "com.tcl.channelplus": ("TCL Channel+ FAST Channels", "Pushes sponsored live channels to the home screen"),
    "com.tcl.tv.tclhome_passive": ("TCL Home Promo Pusher", "Pushes TCL banners to the home screen at boot"),
    "com.tcl.partnercustomizer": ("TCL Home Row Customizer", "Injects TCL promotional rows into Google TV"),
    "com.tcl.interactive": ("TCL TIAS Service", "TCL background interactive advertising service"),
    "com.tcl.smartlink.core": ("TCL SmartLink Core", "Background service bundling silent app installer"),
    "com.tcl.exhibit": ("TCL Retail Store Demo", "In-store showroom demo mode"),
    "com.tcl.esticker": ("TCL E-Sticker Promo", "Retail store feature sticker overlay for showroom TVs"),
    "com.tcl.ocean.instructions": ("TCL E-Manual", "Built-in digital user manual"),
    "com.tcl.repairguide": ("TCL Repair Guide", "Built-in troubleshooting manual"),

    # Sony Bloatware
    "tv.samba.ssm": ("Samba TV ACR Tracker", "Watches what is on screen to build ad profiles"),
    "com.qterics.da.product": ("Qterics Telemetry Agent", "Background device analytics agent"),
    "com.sony.dtv.da.service": ("Sony Data Analytics", "Sends TV usage telemetry to Sony"),
    "com.sonyericsson.idd.agent": ("Sony IDD Diagnostics", "Usage & diagnostics tracker"),
    "com.sony.dtv.promos": ("Sony Promotional Banners", "Displays Sony promotional notifications"),
    "com.sony.dtv.sonyselect": ("Sony Select Curated Apps", "Promotional app showcase"),
    "com.sony.dtv.demosupport": ("Sony Retail Demo Mode", "Showroom demo mode service"),
    "com.sony.dtv.demosystemsupport": ("Sony Demo System Support", "Showroom demo background service"),
    "com.sony.dtv.multiscreendemo": ("Sony Multi-screen Demo", "Showroom split-screen demo app"),

    # Google TV Bloat / Optional Services
    "com.google.android.tvrecommendations": ("Android TV Ad & Promo Rows", "Drives sponsored content & recommendation rows"),
    "com.google.android.leanbacklauncher.recommendations": ("Leanback Recommendations", "Drives recommendation rows on older Android TVs"),
    "com.google.android.katniss": ("Google Assistant Voice Search", "Handles microphone voice search on remote"),
    "com.google.android.apps.wellness": ("Digital Wellbeing", "Screen time tracker (unnecessary on a TV)"),
    "com.google.android.apps.dream": ("Ambient Screensaver", "Stock backdrop photo screensaver"),
    "com.google.android.apps.tv.dreamx": ("Google TV Ambient Mode", "Heavy photo/art screensaver on Google TV"),
    "com.google.android.feedback": ("Google Feedback Reporter", "Sends bug reports to Google"),
    "com.google.android.play.games": ("Google Play Games", "Game achievements hub"),
    "com.google.android.apps.tachyon": ("Google Meet / Duo", "Video calling app"),
    "fusion.android.tv.demo": ("Android TV Retail Demo", "Factory showroom demo mode"),

    # Amazon Fire TV Bloatware
    "com.amazon.advertising": ("Amazon Ads Engine", "Core advertising service on Fire TV"),
    "com.amazon.tv.acr": ("Amazon ACR Viewing Tracker", "Automatic Content Recognition tracking what you watch"),
    "com.amazon.metrics": ("Amazon Metrics Service", "Collects and uploads usage telemetry"),
    "com.amazon.device.metrics": ("Device Telemetry Service", "System-level Amazon telemetry"),
    "com.amazon.client.metrics": ("Client Metrics Collector", "App usage telemetry collector"),
    "com.amazon.ftvads.deeplinking": ("Fire TV Ad Deep-Linking", "Handles clickable video/banner ads on home screen"),
    "com.amazon.tv.recommendations": ("Fire TV Sponsored Row", "Pushes sponsored content recommendations"),
    "com.amazon.media.recommendations": ("Amazon Media Recommendations", "Home screen media promo service"),
    "com.amazon.tv.democontent.provider": ("Fire TV Retail Demo Videos", "Showroom demo video provider"),
    "com.amazon.shoptv.firetv.client": ("Amazon Shopping on TV", "Shopping app preloaded on Fire TV"),
    "com.amazon.shoppingapp": ("Amazon Shopping", "Shopping app"),
    "com.amazon.crowd": ("Amazon Crowd Telemetry", "Background feedback & telemetry service"),

    # User & Streaming Apps
    "com.netflix.mediaclient": ("Netflix", "Netflix streaming app"),
    "com.netflix.ninja": ("Netflix (TV Edition)", "Netflix streaming app for Smart TVs"),
    "com.google.android.youtube.tv": ("YouTube", "Official YouTube app for TV"),
    "com.google.android.youtube.tvmusic": ("YouTube Music", "YouTube Music streaming app"),
    "com.amazon.amazonvideo.livingroom": ("Prime Video", "Amazon Prime Video streaming app"),
    "com.amazon.avod": ("Prime Video (Fire TV)", "Amazon Prime Video streaming app"),
    "com.spotify.tv.android": ("Spotify", "Spotify music & podcast player"),
    "com.disney.disneyplus": ("Disney+", "Disney+ streaming app"),
    "org.xbmc.kodi": ("Kodi Media Center", "Open-source home theater & media player"),
    "com.plexapp.android": ("Plex", "Plex media server client"),
}


def is_deny_listed(package_name: str) -> Tuple[bool, str]:
    """Check if package is in the absolute deny-list or is a protected stock launcher."""
    pkg = package_name.strip()

    for pat in ABSOLUTE_DENY_PATTERNS:
        if re.search(pat, pkg, re.IGNORECASE):
            return True, f"Protected Core/Input/Bluetooth/Store component ({pat})"

    for pat in STOCK_LAUNCHER_PATTERNS:
        if re.search(pat, pkg, re.IGNORECASE):
            return True, f"Protected Stock Launcher - kept enabled for safe 1-click restore ({pat})"

    return False, ""


def get_plain_name(package_name: str) -> str:
    """Return friendly plain English name for a package."""
    pkg = package_name.strip()
    if pkg in FRIENDLY_DB:
        return FRIENDLY_DB[pkg][0]

    parts = pkg.split(".")
    candidate = parts[-1]
    if candidate.lower() in ("android", "app", "service", "client", "tv", "atv", "core") and len(parts) > 1:
        candidate = f"{parts[-2]} {candidate}"
    return candidate.replace("_", " ").title()


def get_description(package_name: str) -> str:
    """Return plain English explanation of what the package does."""
    pkg = package_name.strip()
    if pkg in FRIENDLY_DB:
        return FRIENDLY_DB[pkg][1]

    denied, reason = is_deny_listed(pkg)
    if denied:
        return reason

    for pat in SAFE_DEBLOAT_PATTERNS:
        if re.search(pat, pkg, re.IGNORECASE):
            return "Manufacturer ad, analytics, telemetry, or preloaded promo service"

    for pat in STREAMING_PATTERNS:
        if re.search(pat, pkg, re.IGNORECASE):
            return "Media streaming & entertainment app"

    return "System or manufacturer component"


def classify_package(package_name: str, is_system: bool = True) -> str:
    """Classify package into one of the 3 plain-English lists required by Ansub's prompt:
    - 'safe_to_disable': Ads, telemetry, bloatware safe to turn off
    - 'needed_by_tv': Protected system, Play Store, keyboard, Bluetooth, HDMI, stock launcher
    - 'user_app': Streaming apps and user-installed apps
    """
    pkg = package_name.strip()
    denied, _ = is_deny_listed(pkg)
    if denied:
        return "needed_by_tv"

    for pat in SAFE_DEBLOAT_PATTERNS:
        if re.search(pat, pkg, re.IGNORECASE):
            return "safe_to_disable"

    for pat in STREAMING_PATTERNS:
        if re.search(pat, pkg, re.IGNORECASE):
            return "user_app"

    if not is_system:
        return "user_app"

    # Remaining system packages default to needed_by_tv so we never break unknown OEM hardware services
    return "needed_by_tv"
