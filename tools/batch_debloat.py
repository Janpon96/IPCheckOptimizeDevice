#!/usr/bin/env python3
"""batch_debloat.py - Helper for batch scanning and disabling safe apps."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from device_manager import DeviceManager

def scan_safe(host):
    mgr = DeviceManager(host)
    try:
        items = mgr.inventory()
        safe = [i for i in items if i['category'] == 'safe_to_disable' and not i['is_disabled']]
        print(f"Tim thay {len(safe)} app rac/quang cao dang bat:")
        for a in safe:
            print(f" - {a['plain_name']} ({a['package_id']})")
        return [a['package_id'] for a in safe]
    finally:
        mgr.close()

def apply_safe(host):
    mgr = DeviceManager(host)
    try:
        items = mgr.inventory()
        safe = [i for i in items if i['category'] == 'safe_to_disable' and not i['is_disabled']]
        for a in safe:
            print(f"Dang tat {a['plain_name']} ({a['package_id']})...")
            mgr.apply_disable(a['package_id'], 'Batch safe debloat')
        print("Hoan tat batch debloat!")
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
