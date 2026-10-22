#!/usr/bin/env python3
"""gui_app.py - Modern Multi-Platform Device Optimizer & Debloater Desktop UI.

Features:
- Asynchronous LAN Auto-Discovery & Smart Device Detection (9 Profiles)
- Visual Free Memory (RAM) Before vs. After Gauge
- 3 Plain-English App Inventory Tabs:
  1. 🟢 Safe to Turn Off (Ads & Bloatware)
  2. 🔵 Apps You Use (Streaming & User Apps)
  3. 🔴 Needed by the TV (Protected System / Play Store / Bluetooth / Keyboard / HDMI)
- Search/Filter bar, per-change confirmation, Undo-Log viewer, Backup, Verify & Report
"""

import json
import os
import sys
import threading
import webbrowser
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "tools"))

import device_detector
import device_guard
from device_manager import DeviceManager, DeviceConnectionError, UNDO_LOG

# Color Palette (Modern Dark Theme)
BG_DARK = "#0f1117"
BG_CARD = "#181b24"
BG_INPUT = "#222634"
FG_PRIMARY = "#f1f5f9"
FG_MUTED = "#94a3b8"
ACCENT_GREEN = "#10b981"
ACCENT_BLUE = "#3b82f6"
ACCENT_AMBER = "#f59e0b"
ACCENT_RED = "#ef4444"
ACCENT_PURPLE = "#8b5cf6"


class OptimizerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Antigravity — Multi-Platform IP Device Optimizer & Debloater v2.0")
        self.geometry("1220x780")
        self.minsize(1060, 680)
        self.configure(bg=BG_DARK)

        # State
        self.lan_devices = []
        self.current_detection = None
        self.baseline_metrics = None
        self.latest_metrics = None
        self.inventory_items = []
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_inventory_trees())

        self._setup_styles()
        self._build_layout()
        self._refresh_undo_tab()

        # Trigger initial LAN scan in background
        self.after(250, self.on_scan_lan)

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TFrame", background=BG_DARK)
        style.configure("Card.TFrame", background=BG_CARD)
        style.configure("TLabel", background=BG_DARK, foreground=FG_PRIMARY, font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=BG_CARD, foreground=FG_PRIMARY, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=BG_CARD, foreground=FG_MUTED, font=("Segoe UI", 9))
        style.configure("Header.TLabel", background=BG_DARK, foreground=ACCENT_GREEN, font=("Segoe UI", 15, "bold"))

        # Notebook tabs
        style.configure("TNotebook", background=BG_DARK, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG_INPUT, foreground=FG_MUTED,
                        padding=(14, 8), font=("Segoe UI", 9, "bold"), borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT_BLUE)],
                  foreground=[("selected", "#ffffff")])

        # Treeview
        style.configure("Treeview",
                        background="#141720",
                        foreground=FG_PRIMARY,
                        fieldbackground="#141720",
                        rowheight=28,
                        borderwidth=0,
                        font=("Segoe UI", 9))
        style.configure("Treeview.Heading",
                        background=BG_INPUT,
                        foreground=FG_PRIMARY,
                        font=("Segoe UI", 9, "bold"),
                        relief="flat")
        style.map("Treeview",
                  background=[("selected", "#2563eb")],
                  foreground=[("selected", "#ffffff")])

        # Progressbar
        style.configure("Ram.Horizontal.TProgressbar",
                        troughcolor=BG_INPUT,
                        background=ACCENT_GREEN,
                        borderwidth=0,
                        thickness=14)

    def _make_btn(self, parent, text, command, bg=BG_INPUT, fg="#ffffff", width=None):
        btn = tk.Button(
            parent, text=text, command=command,
            bg=bg, fg=fg, activebackground=ACCENT_BLUE, activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"), relief="flat", bd=0,
            padx=12, pady=6, cursor="hand2"
        )
        if width:
            btn.configure(width=width)
        return btn

    def _build_layout(self):
        # 1. Top Header Bar
        top = ttk.Frame(self, padding=(16, 12))
        top.pack(fill="x")

        title_box = ttk.Frame(top)
        title_box.pack(side="left")
        ttk.Label(title_box, text="⚡ ANTIGRAVITY IP DEVICE OPTIMIZER", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            title_box,
            text="Multi-Platform Inspector & Reversible Debloater (Android TV • Google TV • Fire TV • Xview • Roku • iOS • Switch • Tizen/webOS)",
            foreground=FG_MUTED, font=("Segoe UI", 9)
        ).pack(anchor="w")

        # IP & Port Controls on Top Right
        conn_bar = ttk.Frame(top, style="Card.TFrame", padding=(12, 8))
        conn_bar.pack(side="right")

        ttk.Label(conn_bar, text="Target IP:", style="Card.TLabel").pack(side="left", padx=(0, 6))
        self.ip_entry = tk.Entry(
            conn_bar, width=16, bg=BG_INPUT, fg="#ffffff", insertbackground="#ffffff",
            font=("Consolas", 11, "bold"), relief="flat"
        )
        self.ip_entry.insert(0, os.environ.get("TV_HOST", "192.168.1.50"))
        self.ip_entry.pack(side="left", padx=(0, 8), ipady=4)

        ttk.Label(conn_bar, text="Port:", style="Card.TLabel").pack(side="left", padx=(0, 4))
        self.port_entry = tk.Entry(
            conn_bar, width=6, bg=BG_INPUT, fg="#ffffff", insertbackground="#ffffff",
            font=("Consolas", 10), relief="flat"
        )
        self.port_entry.insert(0, "5555")
        self.port_entry.pack(side="left", padx=(0, 10), ipady=4)

        self._make_btn(conn_bar, "🔍 Smart Detect & Probe", self.on_detect_and_probe, bg=ACCENT_GREEN).pack(side="left", padx=3)
        self._make_btn(conn_bar, "📦 Load All Apps", self.on_load_inventory, bg=ACCENT_BLUE).pack(side="left", padx=3)

        # 2. Main Body Paned Split (Left Sidebar + Right Workspace)
        main_frame = ttk.Frame(self, padding=(16, 4))
        main_frame.pack(fill="both", expand=True)

        # --- LEFT SIDEBAR: LAN Scanner + Device Profile + RAM Gauge ---
        left_col = ttk.Frame(main_frame, width=330)
        left_col.pack(side="left", fill="y", padx=(0, 12))
        left_col.pack_propagate(False)

        # Card A: LAN Scanner
        lan_card = ttk.Frame(left_col, style="Card.TFrame", padding=10)
        lan_card.pack(fill="x", pady=(0, 10))

        lan_hdr = ttk.Frame(lan_card, style="Card.TFrame")
        lan_hdr.pack(fill="x", pady=(0, 6))
        ttk.Label(lan_hdr, text="🌐 LAN Device Radar", style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(side="left")
        self._make_btn(lan_hdr, "↻ Scan LAN", self.on_scan_lan, bg=BG_INPUT).pack(side="right")

        self.lan_tree = ttk.Treeview(lan_card, columns=("ip", "type", "cap"), show="headings", height=6)
        self.lan_tree.heading("ip", text="IP Address")
        self.lan_tree.heading("type", text="Detected Platform")
        self.lan_tree.heading("cap", text="Tier")
        self.lan_tree.column("ip", width=102, anchor="w")
        self.lan_tree.column("type", width=145, anchor="w")
        self.lan_tree.column("cap", width=55, anchor="center")
        self.lan_tree.pack(fill="x")
        self.lan_tree.bind("<<TreeviewSelect>>", self._on_lan_select)

        # Card B: Detected Device Identity & Capability
        id_card = ttk.Frame(left_col, style="Card.TFrame", padding=10)
        id_card.pack(fill="x", pady=(0, 10))
        ttk.Label(id_card, text="🛡️ Detected Device Profile", style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))

        self.lbl_profile = ttk.Label(id_card, text="Not probed yet", style="Card.TLabel", font=("Segoe UI", 10, "bold"), foreground=ACCENT_AMBER)
        self.lbl_profile.pack(anchor="w")
        self.lbl_vendor = ttk.Label(id_card, text="MAC / Vendor: —", style="Muted.TLabel")
        self.lbl_vendor.pack(anchor="w", pady=1)
        self.lbl_transport = ttk.Label(id_card, text="Transport: —", style="Muted.TLabel")
        self.lbl_transport.pack(anchor="w", pady=1)
        self.lbl_ports = ttk.Label(id_card, text="Open Ports: —", style="Muted.TLabel", wraplength=300)
        self.lbl_ports.pack(anchor="w", pady=1)

        # Card C: Memory (RAM) Before vs After
        ram_card = ttk.Frame(left_col, style="Card.TFrame", padding=10)
        ram_card.pack(fill="x", pady=(0, 10))
        ttk.Label(ram_card, text="🧠 Free Memory (Before vs. After)", style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))

        self.lbl_ram_before = ttk.Label(ram_card, text="Before : — MB free", style="Muted.TLabel")
        self.lbl_ram_before.pack(anchor="w")
        self.lbl_ram_after = ttk.Label(ram_card, text="Now    : — MB free", style="Card.TLabel", foreground=ACCENT_GREEN, font=("Segoe UI", 10, "bold"))
        self.lbl_ram_after.pack(anchor="w", pady=(2, 6))

        self.ram_bar = ttk.Progressbar(ram_card, style="Ram.Horizontal.TProgressbar", orient="horizontal", mode="determinate", maximum=100)
        self.ram_bar.pack(fill="x", pady=(0, 4))
        self.lbl_storage = ttk.Label(ram_card, text="Storage: —", style="Muted.TLabel", wraplength=300)
        self.lbl_storage.pack(anchor="w")

        # Card D: 1-Click Runbook Workflow Actions
        act_card = ttk.Frame(left_col, style="Card.TFrame", padding=10)
        act_card.pack(fill="both", expand=True)
        ttk.Label(act_card, text="🚀 Runbook Actions (Always Reversible)", style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))

        btn_grid = ttk.Frame(act_card, style="Card.TFrame")
        btn_grid.pack(fill="x")

        self._make_btn(btn_grid, "💾 1. Backup State", self.on_backup, bg="#334155").pack(fill="x", pady=2)
        self._make_btn(btn_grid, "⚡ 2.Debloat Safe List (Ask First)", self.on_batch_debloat, bg=ACCENT_AMBER, fg="#000000").pack(fill="x", pady=2)
        self._make_btn(btn_grid, "✨ 3. No Anim / No Saver / 5m Sleep", self.on_optimize_settings, bg=ACCENT_PURPLE).pack(fill="x", pady=2)
        self._make_btn(btn_grid, "🔄 4. Reboot & Verify RAM", self.on_reboot_and_verify, bg=ACCENT_BLUE).pack(fill="x", pady=2)
        self._make_btn(btn_grid, "📝 5. Generate Report (.md)", self.on_generate_report, bg="#0284c7").pack(fill="x", pady=2)
        self._make_btn(btn_grid, "⏪ 6. Rollback All Changes", self.on_rollback_all, bg=ACCENT_RED).pack(fill="x", pady=(6, 2))

        # --- RIGHT WORKSPACE: Filter Bar + 5 Tabs ---
        right_col = ttk.Frame(main_frame)
        right_col.pack(side="left", fill="both", expand=True)

        # Search & Selection Action Bar
        filter_bar = ttk.Frame(right_col, style="Card.TFrame", padding=(10, 8))
        filter_bar.pack(fill="x", pady=(0, 8))

        ttk.Label(filter_bar, text="🔎 Filter Apps:", style="Card.TLabel").pack(side="left", padx=(0, 6))
        search_entry = tk.Entry(
            filter_bar, textvariable=self.search_var, width=28,
            bg=BG_INPUT, fg="#ffffff", insertbackground="#ffffff", font=("Segoe UI", 10), relief="flat"
        )
        search_entry.pack(side="left", padx=(0, 12), ipady=3)

        self._make_btn(filter_bar, "🚫 Turn Off Selected App(s)", self.on_disable_selected, bg=ACCENT_AMBER, fg="#000000").pack(side="left", padx=4)
        self._make_btn(filter_bar, "✅ Re-Enable Selected App(s)", self.on_enable_selected, bg=ACCENT_GREEN).pack(side="left", padx=4)
        self._make_btn(filter_bar, "📖 Open Profile Guide", self.on_open_doc, bg=BG_INPUT).pack(side="right", padx=4)

        # Notebook with 5 Tabs
        self.notebook = ttk.Notebook(right_col)
        self.notebook.pack(fill="both", expand=True)

        self.tab_safe = ttk.Frame(self.notebook)
        self.tab_user = ttk.Frame(self.notebook)
        self.tab_needed = ttk.Frame(self.notebook)
        self.tab_guide = ttk.Frame(self.notebook)
        self.tab_undo = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_safe, text="🟢 Safe to Turn Off (0)")
        self.notebook.add(self.tab_user, text="🔵 Apps You Use (0)")
        self.notebook.add(self.tab_needed, text="🔴 Needed by TV / Protected (0)")
        self.notebook.add(self.tab_guide, text="🧭 Smart Diagnostic & Setup Guide")
        self.notebook.add(self.tab_undo, text="📜 Undo Log & History")

        self.tree_safe = self._create_app_tree(self.tab_safe)
        self.tree_user = self._create_app_tree(self.tab_user)
        self.tree_needed = self._create_app_tree(self.tab_needed)

        # Tab 4: Smart Diagnostic & Walkthrough Text
        self.txt_guide = tk.Text(
            self.tab_guide, bg="#12141c", fg="#e2e8f0",
            font=("Consolas", 10), relief="flat", padx=14, pady=12, wrap="word"
        )
        self.txt_guide.pack(fill="both", expand=True)
        self._write_guide(
            "Chào mừng bạn đến với Antigravity Multi-Platform IP Device Optimizer v2.0!\n\n"
            "• Chọn một thiết bị từ bảng 'LAN Device Radar' bên trái hoặc nhập IP rồi bấm 'Smart Detect & Probe'.\n"
            "• Công cụ sẽ tự động nhận diện thiết bị (Android TV, Fire TV, Máy chiếu Xview, iPhone/iOS, Roku, Switch, Samsung Tizen, LG webOS)\n"
            "  mà KHÔNG BAO GIỜ bị đơ hay văng lỗi ConnectionRefusedError.\n"
            "• Mọi thao tác trên Android TV đều dùng `pm disable-user --user 0` (chỉ tắt, không xóa) và hỏi xác nhận trước khi thực thi."
        )

        # Tab 5: Undo Log Treeview
        undo_top = ttk.Frame(self.tab_undo, padding=6)
        undo_top.pack(fill="x")
        ttk.Label(undo_top, text="Append-only audit trail from undo-log.jsonl — Select any row to re-enable immediately:").pack(side="left")
        self._make_btn(undo_top, "↻ Refresh Log", self._refresh_undo_tab, bg=BG_INPUT).pack(side="right", padx=4)
        self._make_btn(undo_top, "⏪ Undo Selected Row", self.on_undo_selected_log, bg=ACCENT_GREEN).pack(side="right", padx=4)

        self.tree_undo = ttk.Treeview(
            self.tab_undo,
            columns=("ts", "device", "name", "target", "action", "status", "undo_cmd"),
            show="headings"
        )
        for col, title, w in [
            ("ts", "Timestamp", 135),
            ("device", "Device IP", 95),
            ("name", "Plain English Name", 160),
            ("target", "Package / Target", 200),
            ("action", "Action", 90),
            ("status", "Status", 85),
            ("undo_cmd", "How to Undo", 220),
        ]:
            self.tree_undo.heading(col, text=title)
            self.tree_undo.column(col, width=w, anchor="w")
        self.tree_undo.pack(fill="both", expand=True, padx=6, pady=6)

        # 3. Bottom Status Bar
        status_bar = ttk.Frame(self, style="Card.TFrame", padding=(16, 6))
        status_bar.pack(fill="x", side="bottom")
        self.lbl_status = ttk.Label(status_bar, text="Ready. Scanning local network...", style="Card.TLabel", foreground=ACCENT_GREEN)
        self.lbl_status.pack(side="left")

    def _create_app_tree(self, parent) -> ttk.Treeview:
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)

        cols = ("name", "status", "package", "desc")
        tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="extended")
        tree.heading("name", text="Plain English App Name")
        tree.heading("status", text="Current State")
        tree.heading("package", text="Package ID")
        tree.heading("desc", text="What It Does / Why It's Here")

        tree.column("name", width=210, anchor="w")
        tree.column("status", width=110, anchor="center")
        tree.column("package", width=230, anchor="w")
        tree.column("desc", width=330, anchor="w")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        return tree

    # =====================================================================
    # UI HELPERS
    # =====================================================================
    def set_status(self, msg: str, color: str = ACCENT_GREEN):
        self.after(0, lambda: self.lbl_status.configure(text=msg, foreground=color))

    def _write_guide(self, text: str):
        def _update():
            self.txt_guide.configure(state="normal")
            self.txt_guide.delete("1.0", "end")
            self.txt_guide.insert("end", text)
            self.txt_guide.configure(state="disabled")
        self.after(0, _update)

    def _get_mgr(self) -> DeviceManager:
        ip = self.ip_entry.get().strip()
        try:
            port = int(self.port_entry.get().strip())
        except ValueError:
            port = 5555
        return DeviceManager(ip, port)

    def _run_bg(self, label: str, fn):
        self.set_status(f"⏳ {label}...", ACCENT_AMBER)

        def _worker():
            try:
                fn()
            except DeviceConnectionError as e:
                self._write_guide(str(e))
                self.after(0, lambda: self.notebook.select(self.tab_guide))
                self.set_status("⚠️ Device does not have ADB open — See Smart Diagnostic tab for instructions.", ACCENT_AMBER)
            except Exception as e:
                self._write_guide(f"[ERROR] {label}:\n{e}")
                self.set_status(f"❌ {label} failed: {e}", ACCENT_RED)

        threading.Thread(target=_worker, daemon=True).start()

    # =====================================================================
    # EVENT HANDLERS
    # =====================================================================
    def on_scan_lan(self):
        def _task():
            devices = device_detector.scan_lan_devices()
            self.lan_devices = devices

            def _update_ui():
                for item in self.lan_tree.get_children():
                    self.lan_tree.delete(item)
                for d in devices:
                    self.lan_tree.insert("", "end", values=(
                        d["ip"],
                        f"{d['icon']} {d['profile_name']}",
                        d["capability"].split()[0]
                    ))
                self.set_status(f"✅ Found {len(devices)} active devices on local network.", ACCENT_GREEN)

            self.after(0, _update_ui)

        self._run_bg("Scanning LAN ARP table & fingerprinting ports", _task)

    def _on_lan_select(self, _event):
        sel = self.lan_tree.selection()
        if not sel:
            return
        vals = self.lan_tree.item(sel[0], "values")
        if vals:
            ip = vals[0]
            self.ip_entry.delete(0, "end")
            self.ip_entry.insert(0, ip)
            for d in self.lan_devices:
                if d["ip"] == ip:
                    self._update_detection_card(d)
                    break

    def _update_detection_card(self, det: dict):
        self.current_detection = det
        ports_str = ", ".join(f"{k}" for k in det.get("open_ports", {}).keys()) or "None (Closed)"

        def _ui():
            self.lbl_profile.configure(text=f"{det['icon']} {det['profile_name']} [{det['capability']}]")
            self.lbl_vendor.configure(text=f"MAC: {det['mac']} ({det['vendor']})")
            self.lbl_transport.configure(text=f"Transport: {det['transport']}")
            self.lbl_ports.configure(text=f"Open TCP Ports: {ports_str}")

        self.after(0, _ui)

    def on_detect_and_probe(self):
        def _task():
            mgr = self._get_mgr()
            try:
                det = mgr.detect()
                self._update_detection_card(det)
                diag_text = mgr._format_diagnostic(det, "Smart Probe")

                # If device is non-ADB/non-Roku, show the platform guide cleanly without error
                if det["profile_key"] in ("ios", "switch", "nintendo-3ds-ds", "tizen", "webos", "network") and 5555 not in det.get("open_ports", {}):
                    self._write_guide(diag_text)
                    self.after(0, lambda: self.notebook.select(self.tab_guide))
                    self.set_status(f"ℹ️ Detected {det['profile_name']} ({det['ip']}) — Showing platform optimization guide.", ACCENT_BLUE)
                    return

                props = mgr.probe()
                metrics = mgr.get_metrics()
                if self.baseline_metrics is None and metrics["ram_total_mb"] > 0:
                    self.baseline_metrics = metrics
                self.latest_metrics = metrics

                self._update_ram_card()
                summary = [
                    diag_text,
                    "",
                    "======================================================================",
                    "✅ LIVE DEVICE PROBE & MEMORY BASELINE",
                    "======================================================================",
                ]
                for k, v in props.items():
                    summary.append(f"  • {k:<26}: {v}")
                summary.append(f"\n  ★ FREE MEMORY NOW : {metrics['ram_free_mb']} MB free of {metrics['ram_total_mb']} MB ({metrics['ram_free_pct']}%)")
                summary.append(f"  ★ STORAGE (/data) : {metrics['storage_summary']}")
                self._write_guide("\n".join(summary))
                self.after(0, lambda: self.notebook.select(self.tab_guide))
                self.set_status(f"✅ Connected to {props.get('ro.product.model', mgr.host)} — Free RAM: {metrics['ram_free_mb']} MB", ACCENT_GREEN)
            finally:
                mgr.close()

        self._run_bg("Probing device identity & memory", _task)

    def _update_ram_card(self):
        b = self.baseline_metrics
        a = self.latest_metrics
        if not a:
            return

        def _ui():
            if b and b["ram_total_mb"] > 0:
                self.lbl_ram_before.configure(
                    text=f"Before : {b['ram_free_mb']} MB / {b['ram_total_mb']} MB ({b['ram_free_pct']}%)"
                )
            if a["ram_total_mb"] > 0:
                delta = round(a["ram_free_mb"] - (b["ram_free_mb"] if b else a["ram_free_mb"]), 1)
                delta_str = f" ({delta:+.1f} MB)" if delta != 0 else ""
                self.lbl_ram_after.configure(
                    text=f"Now    : {a['ram_free_mb']} MB / {a['ram_total_mb']} MB ({a['ram_free_pct']}%){delta_str}"
                )
                self.ram_bar["value"] = a["ram_free_pct"]
            self.lbl_storage.configure(text=f"Storage: {a['storage_summary']}")

        self.after(0, _ui)

    def on_load_inventory(self):
        def _task():
            mgr = self._get_mgr()
            try:
                det = mgr.detect()
                self._update_detection_card(det)
                items = mgr.inventory()
                metrics = mgr.get_metrics()
                if self.baseline_metrics is None and metrics["ram_total_mb"] > 0:
                    self.baseline_metrics = metrics
                self.latest_metrics = metrics
                self.inventory_items = items
                self._update_ram_card()
                self.after(0, self._refresh_inventory_trees)
                self.after(0, lambda: self.notebook.select(self.tab_safe))
                self.set_status(f"✅ Loaded {len(items)} apps in plain English.", ACCENT_GREEN)
            finally:
                mgr.close()

        self._run_bg("Loading complete app inventory", _task)

    def _refresh_inventory_trees(self):
        q = self.search_var.get().strip().lower()
        for tree in (self.tree_safe, self.tree_user, self.tree_needed):
            for row in tree.get_children():
                tree.delete(row)

        c_safe = c_user = c_needed = 0
        for item in self.inventory_items:
            if q and q not in item["plain_name"].lower() and q not in item["package_id"].lower() and q not in item["description"].lower():
                continue
            state_txt = "OFF (Disabled)" if item["is_disabled"] else ("PROTECTED" if item["protected"] else "ON (Enabled)")
            vals = (item["plain_name"], state_txt, item["package_id"], item["description"])

            if item["category"] == "safe_to_disable":
                self.tree_safe.insert("", "end", values=vals)
                c_safe += 1
            elif item["category"] == "user_app":
                self.tree_user.insert("", "end", values=vals)
                c_user += 1
            else:
                self.tree_needed.insert("", "end", values=vals)
                c_needed += 1

        self.notebook.tab(self.tab_safe, text=f"🟢 Safe to Turn Off ({c_safe})")
        self.notebook.tab(self.tab_user, text=f"🔵 Apps You Use ({c_user})")
        self.notebook.tab(self.tab_needed, text=f"🔴 Needed by TV / Protected ({c_needed})")

    def _get_selected_packages(self):
        current_tab = self.notebook.select()
        tree = None
        if current_tab == str(self.tab_safe):
            tree = self.tree_safe
        elif current_tab == str(self.tab_user):
            tree = self.tree_user
        elif current_tab == str(self.tab_needed):
            tree = self.tree_needed

        if not tree:
            return []
        pkgs = []
        for item_id in tree.selection():
            vals = tree.item(item_id, "values")
            if vals:
                pkgs.append((vals[0], vals[2]))  # (plain_name, package_id)
        return pkgs

    def on_disable_selected(self):
        selected = self._get_selected_packages()
        if not selected:
            messagebox.showinfo("Select Apps", "Please select one or more apps in the table first.")
            return

        # Pre-check guardrail before asking user
        blocked = []
        allowed = []
        for name, pkg in selected:
            denied, reason = device_guard.is_deny_listed(pkg)
            if denied:
                blocked.append(f"• {name} ({pkg}):\n  -> {reason}")
            else:
                allowed.append((name, pkg))

        if blocked:
            messagebox.showwarning(
                "Protected by Safety Guardrail",
                "The following app(s) are NEEDED BY THE TV (Play Store, Bluetooth, Keyboard, HDMI, or Stock Launcher) and will NEVER be turned off:\n\n"
                + "\n".join(blocked)
            )
        if not allowed:
            return

        names_list = "\n".join(f"• {name} ({pkg})" for name, pkg in allowed)
        ans = messagebox.askyesno(
            "Ask Before Every Change",
            f"Do you want to turn off these {len(allowed)} app(s)?\n\n{names_list}\n\n"
            f"Nothing will be deleted — they are only disabled for user 0 and logged to undo-log.jsonl so you can undo anytime."
        )
        if not ans:
            return

        def _task():
            mgr = self._get_mgr()
            try:
                for name, pkg in allowed:
                    mgr.apply_disable(pkg, group_reason="GUI Selected Disable")
                self.inventory_items = mgr.inventory()
                self.latest_metrics = mgr.get_metrics()
                self._update_ram_card()
                self.after(0, self._refresh_inventory_trees)
                self.after(0, self._refresh_undo_tab)
                self.set_status(f"✅ Turned off {len(allowed)} app(s) safely.", ACCENT_GREEN)
            finally:
                mgr.close()

        self._run_bg(f"Turning off {len(allowed)} app(s)", _task)

    def on_enable_selected(self):
        selected = self._get_selected_packages()
        if not selected:
            messagebox.showinfo("Select Apps", "Please select one or more apps in the table to re-enable.")
            return

        def _task():
            mgr = self._get_mgr()
            try:
                for name, pkg in selected:
                    mgr.apply_enable(pkg)
                self.inventory_items = mgr.inventory()
                self.latest_metrics = mgr.get_metrics()
                self._update_ram_card()
                self.after(0, self._refresh_inventory_trees)
                self.after(0, self._refresh_undo_tab)
                self.set_status(f"✅ Re-enabled {len(selected)} app(s).", ACCENT_GREEN)
            finally:
                mgr.close()

        self._run_bg(f"Re-enabling {len(selected)} app(s)", _task)

    def on_backup(self):
        def _task():
            mgr = self._get_mgr()
            try:
                bdir = mgr.backup_state()
                self.set_status(f"✅ Full state backup saved to {bdir}", ACCENT_GREEN)
                self.after(0, lambda: messagebox.showinfo("Backup Complete", f"Saved package lists, settings, getprop & home launcher to:\n{bdir}"))
            finally:
                mgr.close()

        self._run_bg("Backing up device packages & settings", _task)

    def on_batch_debloat(self):
        def _task():
            mgr = self._get_mgr()
            try:
                items = mgr.inventory()
                safe_active = [i for i in items if i["category"] == "safe_to_disable" and not i["is_disabled"]]
                if not safe_active:
                    self.after(0, lambda: messagebox.showinfo("Already Clean!", "All known ad/telemetry bloatware packages on this device are already turned off!"))
                    self.set_status("✅ No active bloatware remaining.", ACCENT_GREEN)
                    return

                def _ask_and_apply():
                    listing = "\n".join(f"• {a['plain_name']} ({a['package_id']})" for a in safe_active[:18])
                    if len(safe_active) > 18:
                        listing += f"\n... and {len(safe_active) - 18} more."
                    ok = messagebox.askyesno(
                        "Confirm Safe Debloat",
                        f"Found {len(safe_active)} active ad/telemetry/bloatware app(s) safe to turn off:\n\n"
                        f"{listing}\n\n"
                        f"Turn them off now? (Nothing is uninstalled; everything is logged to undo-log.jsonl)"
                    )
                    if ok:
                        self._apply_batch_list(safe_active)

                self.after(0, _ask_and_apply)
            finally:
                mgr.close()

        self._run_bg("Scanning for active ad & bloatware apps", _task)

    def _apply_batch_list(self, safe_list):
        def _task():
            mgr = self._get_mgr()
            try:
                mgr.backup_state()
                for a in safe_list:
                    mgr.apply_disable(a["package_id"], group_reason="Batch Safe Debloat")
                self.inventory_items = mgr.inventory()
                self.latest_metrics = mgr.get_metrics()
                self._update_ram_card()
                self.after(0, self._refresh_inventory_trees)
                self.after(0, self._refresh_undo_tab)
                self.set_status(f"✅ Turned off {len(safe_list)} bloatware apps! Free RAM: {self.latest_metrics['ram_free_mb']} MB", ACCENT_GREEN)
            finally:
                mgr.close()

        self._run_bg(f"Disabling {len(safe_list)} bloatware packages", _task)

    def on_optimize_settings(self):
        ok = messagebox.askyesno(
            "Confirm System Optimization",
            "Apply the following reversible system optimizations?\n\n"
            "1. Turn OFF window, transition & animator animations (0x scale)\n"
            "2. Turn OFF stock screensaver\n"
            "3. Make the TV go to sleep after 5 minutes of inactivity\n\n"
            "Previous values will be saved to undo-log.jsonl."
        )
        if not ok:
            return

        def _task():
            mgr = self._get_mgr()
            try:
                mgr.optimize_settings(sleep_minutes=5)
                self.after(0, self._refresh_undo_tab)
                self.set_status("✅ Turned off animations & screensaver, set 5-minute sleep timer.", ACCENT_GREEN)
            finally:
                mgr.close()

        self._run_bg("Applying animation, screensaver & 5-minute sleep settings", _task)

    def on_reboot_and_verify(self):
        ok = messagebox.askyesno(
            "Reboot & Verify",
            "Do you want to restart the device now, or just verify that disabled apps stayed off and compare Free RAM?\n\n"
            "• Click YES to Reboot the device now.\n"
            "• Click NO to run Post-Reboot Verification immediately without rebooting."
        )
        if ok:
            def _reboot_task():
                mgr = self._get_mgr()
                try:
                    mgr.reboot()
                    self.set_status("🔄 Reboot command sent! Wait ~60-90s for TV to restart, then click 'Reboot & Verify' -> NO.", ACCENT_AMBER)
                finally:
                    mgr.close()
            self._run_bg("Rebooting device", _reboot_task)
        else:
            def _verify_task():
                mgr = self._get_mgr()
                try:
                    base_ram = self.baseline_metrics["ram_free_mb"] if self.baseline_metrics else None
                    res = mgr.verify_state(baseline_ram_mb=base_ram)
                    self.latest_metrics = mgr.get_metrics()
                    self._update_ram_card()
                    report_txt = (
                        f"======================================================================\n"
                        f"✅ POST-REBOOT VERIFICATION & MEMORY CHECK ({mgr.host})\n"
                        f"======================================================================\n"
                        f"  • Disabled Apps Expected : {res['expected_disabled_count']}\n"
                        f"  • Stayed Off After Boot  : {res['stayed_off_count']} ({'ALL STAYED OFF ✅' if res['all_stayed_off'] else 'SOME REVERTED ⚠️'})\n"
                        f"  • Free Memory Before     : {base_ram if base_ram is not None else 'N/A'} MB\n"
                        f"  • Free Memory Now        : {res['ram_free_mb']} MB / {res['ram_total_mb']} MB\n"
                        f"  • Memory Gained          : {res['ram_delta_mb']:+.1f} MB\n"
                        if res["ram_delta_mb"] is not None else
                        f"  • Free Memory Now        : {res['ram_free_mb']} MB / {res['ram_total_mb']} MB\n"
                    )
                    self._write_guide(report_txt)
                    self.after(0, lambda: self.notebook.select(self.tab_guide))
                    self.set_status(f"✅ Verification complete: {res['stayed_off_count']} apps stayed off, Free RAM = {res['ram_free_mb']} MB", ACCENT_GREEN)
                finally:
                    mgr.close()
            self._run_bg("Verifying disabled apps & measuring RAM", _verify_task)

    def on_generate_report(self):
        def _task():
            mgr = self._get_mgr()
            try:
                rpath = mgr.generate_report(before_metrics=self.baseline_metrics)
                with open(rpath, "r", encoding="utf-8") as f:
                    content = f.read()
                self._write_guide(content)
                self.after(0, lambda: self.notebook.select(self.tab_guide))
                self.set_status(f"✅ Report saved to {rpath}", ACCENT_GREEN)
            finally:
                mgr.close()

        self._run_bg("Generating Markdown optimization report", _task)

    def on_rollback_all(self):
        ok = messagebox.askyesno(
            "Confirm Full Rollback",
            "Re-enable ALL apps and restore ALL settings logged for this device in undo-log.jsonl?"
        )
        if not ok:
            return

        def _task():
            mgr = self._get_mgr()
            try:
                restored = mgr.rollback_all()
                self.inventory_items = mgr.inventory()
                self.latest_metrics = mgr.get_metrics()
                self._update_ram_card()
                self.after(0, self._refresh_inventory_trees)
                self.after(0, self._refresh_undo_tab)
                self.set_status(f"✅ Rolled back {len(restored)} change(s).", ACCENT_GREEN)
            finally:
                mgr.close()

        self._run_bg("Rolling back all changes from undo-log.jsonl", _task)

    def _refresh_undo_tab(self):
        for r in self.tree_undo.get_children():
            self.tree_undo.delete(r)
        if not os.path.exists(UNDO_LOG):
            return
        with open(UNDO_LOG, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in reversed(lines):
            try:
                row = json.loads(line)
                self.tree_undo.insert("", "end", values=(
                    row.get("ts", "")[:19],
                    row.get("device", ""),
                    row.get("plain_name", row.get("target", "")),
                    row.get("target", ""),
                    row.get("action", ""),
                    row.get("status", ""),
                    row.get("undo", {}).get("cmd", "")
                ))
            except Exception:
                pass

    def on_undo_selected_log(self):
        sel = self.tree_undo.selection()
        if not sel:
            messagebox.showinfo("Select Log Entry", "Select a row in the Undo Log table first.")
            return
        vals = self.tree_undo.item(sel[0], "values")
        target = vals[3]
        action = vals[4]
        if action != "disable-user":
            messagebox.showinfo("Info", f"Use 'Rollback All Changes' to restore setting {target}.")
            return

        def _task():
            mgr = self._get_mgr()
            try:
                mgr.apply_enable(target)
                self.after(0, self._refresh_undo_tab)
                self.set_status(f"✅ Re-enabled {target}", ACCENT_GREEN)
            finally:
                mgr.close()

        self._run_bg(f"Re-enabling {target}", _task)

    def on_open_doc(self):
        doc_rel = "docs/RUNBOOK.md"
        if self.current_detection and self.current_detection.get("doc"):
            doc_rel = self.current_detection["doc"]
        doc_path = os.path.join(BASE_DIR, doc_rel.replace("/", os.sep))
        if os.path.exists(doc_path):
            with open(doc_path, "r", encoding="utf-8") as f:
                self._write_guide(f.read())
            self.notebook.select(self.tab_guide)
            self.set_status(f"📖 Opened {doc_rel}", ACCENT_BLUE)


if __name__ == "__main__":
    app = OptimizerGUI()
    app.mainloop()
