#!/usr/bin/env python3
"""
Sentinel-X | Module: Asset Classification
Version: 1.2
Purpose: Classify LIVE assets by purpose and risk
Ethical: Passive header/title/content analysis only
"""

import os
import json
import sys
import requests
import re
import time
import glob
from typing import List, Dict

# ---------------- CONFIG ----------------

BASE_DIR = os.path.expanduser("~/SentinelX")
INPUT_DIR = os.path.join(BASE_DIR, "recon", "validated")
OUTPUT_DIR = os.path.join(BASE_DIR, "recon", "classified")
LOG_DIR = os.path.join(BASE_DIR, "logs", "classification")

# Classification rules (PASSIVE)
CLASSIFICATION_RULES = {
    "LOGIN_PORTAL": [
        "login", "signin", "sign-in", "auth", "authentication",
        "dashboard", "portal", "session"
    ],
    "ADMIN_PANEL": [
        "admin", "administrator", "wp-admin", "control panel",
        "backend", "management"
    ],
    "API_ENDPOINT": [
        "api", "graphql", "swagger", "openapi", "/api/"
    ],
    "FILE_SHARE": [
        "files", "upload", "download", "storage", "bucket"
    ],
    "CMS_PANEL": [
        "wordpress", "drupal", "joomla", "cms"
    ],
    "DEVELOPER": [
        "dev", "staging", "test", "beta", "sandbox"
    ]
}

RISK_SCORES = {
    "ADMIN_PANEL": "CRITICAL",
    "LOGIN_PORTAL": "HIGH",
    "API_ENDPOINT": "HIGH",
    "FILE_SHARE": "HIGH",
    "CMS_PANEL": "MEDIUM",
    "DEVELOPER": "MEDIUM",
    "STATIC_SITE": "LOW",
    "UNKNOWN": "LOW"
}

# ---------------- HELPERS ----------------

def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

def load_validated_assets(json_file: str) -> List[Dict]:
    """Load LIVE assets from validation output"""
    with open(json_file, "r") as f:
        data = json.load(f)

    assets = data.get("assets", [])
    return [a for a in assets if a.get("status") == "LIVE"]

def get_asset_hostname(asset: Dict) -> str:
    """
    FIXED: Correctly extract hostname from validation output
    """
    if "asset" in asset:
        return asset["asset"]
    if "hostname" in asset:
        return asset["hostname"]
    if "subdomain" in asset and "domain" in asset:
        return f"{asset['subdomain']}.{asset['domain']}"
    return "unknown"

# ---------------- CLASSIFICATION ----------------

def classify_asset(asset: Dict) -> Dict:
    hostname = get_asset_hostname(asset)
    hostname_lower = hostname.lower()

    title = (asset.get("title") or "").lower()
    server = (asset.get("server") or "").lower()

    classification = "STATIC_SITE"
    confidence = 0.5
    evidence = []

    # Hostname-based detection
    for asset_type, keywords in CLASSIFICATION_RULES.items():
        for kw in keywords:
            if kw in hostname_lower:
                classification = asset_type
                confidence = 0.85
                evidence.append(f"hostname:{kw}")
                break
        if classification != "STATIC_SITE":
            break

    # Title-based detection
    for asset_type, keywords in CLASSIFICATION_RULES.items():
        for kw in keywords:
            if kw in title:
                classification = asset_type
                confidence = max(confidence, 0.9)
                evidence.append(f"title:{kw}")
                break

    # Passive HTTP content check (single request)
    try:
        for proto in ["https://", "http://"]:
            try:
                resp = requests.get(
                    proto + hostname,
                    timeout=6,
                    headers={"User-Agent": "Sentinel-X/1.0"},
                    verify=False
                )
                content = resp.text.lower()
                break
            except:
                continue

        paths = {
            "ADMIN_PANEL": ["/admin", "/backend", "/cpanel"],
            "LOGIN_PORTAL": ["/login", "/signin", "/auth"],
            "API_ENDPOINT": ["/api/", "/graphql"]
        }

        for asset_type, plist in paths.items():
            for p in plist:
                if p in content:
                    classification = asset_type
                    confidence = 0.95
                    evidence.append(f"content:{p}")
                    break

    except:
        pass

    result = asset.copy()
    result.update({
        "hostname": hostname,
        "classification": classification,
        "risk_level": RISK_SCORES.get(classification, "LOW"),
        "confidence": round(confidence, 2),
        "evidence": evidence[:3],
        "classified_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    })

    return result

# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 asset_classification.py <domain>")
        sys.exit(1)

    domain = sys.argv[1]
    ensure_dirs()

    input_files = glob.glob(f"{INPUT_DIR}/{domain}_validated*.json")
    if not input_files:
        print(f"[!] No validated file found for {domain}")
        sys.exit(1)

    input_file = input_files[0]
    print(f"[✓] Sentinel-X Asset Classification")
    print(f"[+] Target: {domain}")
    print(f"[+] Input: {input_file}")
    print("-" * 60)

    live_assets = load_validated_assets(input_file)
    print(f"[+] {len(live_assets)} LIVE assets to classify")

    classified_assets = []
    for i, asset in enumerate(live_assets, 1):
        classified = classify_asset(asset)
        classified_assets.append(classified)
        print(
            f"[{i:02d}/{len(live_assets)}] "
            f"{classified['hostname']:<25} → "
            f"{classified['classification']:<14} "
            f"({classified['risk_level']})"
        )
        time.sleep(0.1)

    summary = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for a in classified_assets:
        summary[a["risk_level"]] += 1

    report = {
        "project": "Sentinel-X",
        "module": "Asset Classification",
        "target": domain,
        "classified_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": summary,
        "assets": classified_assets
    }

    output_file = os.path.join(OUTPUT_DIR, f"{domain}_classified.json")
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print("\n🎯 CLASSIFICATION COMPLETE")
    print(f"📁 Report: {output_file}")
    for k, v in summary.items():
        print(f"{k:<9}: {v}")

if __name__ == "__main__":
    main()
