#!/usr/bin/env python3
"""
Sentinel-X | Module: Passive Asset Discovery
Version: 0.1
Author: Nawaz

Purpose:
    - Perform passive subdomain discovery
    - No active scanning
    - Safe for continuous monitoring
    - Output structured JSON for further modules
"""

import os
import json
import datetime
import subprocess
import sys

# -----------------------------
# Configuration
# -----------------------------

BASE_DIR = os.path.expanduser("~/SentinelX")
LOG_DIR = os.path.join(BASE_DIR, "logs", "asset_discovery")

# -----------------------------
# Helper Functions
# -----------------------------

def ensure_directories():
    """Ensure required directories exist"""
    os.makedirs(LOG_DIR, exist_ok=True)


def run_subfinder(domain):
    """
    Run passive subdomain discovery using subfinder.
    Returns a list of discovered subdomains.
    """
    try:
        result = subprocess.run(
            ["subfinder", "-d", domain, "-silent"],
            capture_output=True,
            text=True,
            timeout=120
        )
        subdomains = result.stdout.splitlines()
        return list(set(subdomains))
    except Exception as e:
        print(f"[!] Error running subfinder: {e}")
        return []


def build_asset_report(domain, subdomains):
    """
    Build structured asset discovery report
    """
    return {
        "project": "Sentinel-X",
        "module": "Passive Asset Discovery",
        "version": "0.1",
        "root_domain": domain,
        "discovered_at": datetime.datetime.utcnow().isoformat() + "Z",
        "total_assets": len(subdomains),
        "assets": [
            {
                "subdomain": sub,
                "confidence": 0.90,
                "source": "passive_dns"
            } for sub in subdomains
        ]
    }


def save_report(domain, report):
    """
    Save report as JSON file
    """
    filename = f"{domain}_assets.json"
    filepath = os.path.join(LOG_DIR, filename)

    with open(filepath, "w") as f:
        json.dump(report, f, indent=4)

    return filepath


# -----------------------------
# Main Execution
# -----------------------------

def main():
    ensure_directories()

    if len(sys.argv) != 2:
        print("Usage: python3 passive_discovery.py <domain>")
        print("Example: python3 passive_discovery.py example.com")
        sys.exit(1)

    domain = sys.argv[1].strip()

    print("[+] Sentinel-X Passive Asset Discovery Started")
    print(f"[+] Target Domain: {domain}")

    subdomains = run_subfinder(domain)

    report = build_asset_report(domain, subdomains)
    output_file = save_report(domain, report)

    print(f"[✓] Discovery completed")
    print(f"[✓] Total assets found: {len(subdomains)}")
    print(f"[✓] Results saved to: {output_file}")


if __name__ == "__main__":
    main()

