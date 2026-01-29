#!/usr/bin/env python3
"""
Sentinel-X | Module: Asset Validation
Version: 1.1
Purpose:
    - Validate discovered assets
    - Classify as LIVE / DEAD / RESTRICTED
Ethical use
"""

import os
import json
import sys
import socket
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.expanduser("~/SentinelX")
INPUT_DIR = os.path.join(BASE_DIR, "recon", "aggressive")
OUTPUT_DIR = os.path.join(BASE_DIR, "recon", "validated")

TIMEOUT = 5

# -------------------------
# Helpers
# -------------------------

def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_assets(json_file):
    """Load assets from aggressive recon JSON"""
    try:
        with open(json_file, "r") as f:
            data = json.load(f)

        assets = data.get("assets", [])

        # assets are STRINGS in your aggressive JSON
        if assets and isinstance(assets[0], str):
            return assets

        # fallback (object-based format)
        return [a.get("subdomain") for a in assets if "subdomain" in a]

    except Exception as e:
        print(f"[!] Failed to load assets: {e}")
        return []

def dns_resolves(host):
    try:
        socket.gethostbyname(host)
        return True
    except:
        return False

def http_check(host):
    for scheme in ["https://", "http://"]:
        try:
            r = requests.get(
                scheme + host,
                timeout=TIMEOUT,
                allow_redirects=True,
                headers={"User-Agent": "Sentinel-X/1.0"},
                verify=False
            )
            if r.status_code < 400:
                return True
        except:
            continue
    return False

def validate_asset(host):
    start = time.time()

    if not dns_resolves(host):
        return {
            "asset": host,
            "status": "DEAD",
            "reason": "DNS failed",
            "response_time": round(time.time() - start, 2)
        }

    if http_check(host):
        return {
            "asset": host,
            "status": "LIVE",
            "reason": "HTTP/HTTPS responding",
            "response_time": round(time.time() - start, 2)
        }

    return {
        "asset": host,
        "status": "RESTRICTED",
        "reason": "DNS OK, HTTP blocked",
        "response_time": round(time.time() - start, 2)
    }

# -------------------------
# Main
# -------------------------

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 asset_validation.py <domain>")
        sys.exit(1)

    domain = sys.argv[1]
    ensure_dirs()

    input_file = os.path.join(INPUT_DIR, f"{domain}_aggressive.json")

    if not os.path.exists(input_file):
        print(f"[!] Input not found: {input_file}")
        sys.exit(1)

    print("[✓] Sentinel-X Asset Validation")
    print(f"[+] Target: {domain}")
    print("-" * 50)

    assets = load_assets(input_file)
    print(f"[+] Loaded {len(assets)} assets")

    results = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(validate_asset, a): a for a in assets}
        for future in as_completed(futures):
            results.append(future.result())

    summary = {
        "LIVE": len([r for r in results if r["status"] == "LIVE"]),
        "RESTRICTED": len([r for r in results if r["status"] == "RESTRICTED"]),
        "DEAD": len([r for r in results if r["status"] == "DEAD"])
    }

    report = {
        "project": "Sentinel-X",
        "module": "Asset Validation",
        "target": domain,
        "summary": summary,
        "assets": results
    }

    output_file = os.path.join(OUTPUT_DIR, f"{domain}_validated.json")
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print("\nVALIDATION COMPLETE")
    print(f"📊 LIVE:       {summary['LIVE']}")
    print(f"🔒 RESTRICTED: {summary['RESTRICTED']}")
    print(f"💀 DEAD:       {summary['DEAD']}")
    print(f"📁 Report:     {output_file}")

if __name__ == "__main__":
    main()
