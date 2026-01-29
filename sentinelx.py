#!/usr/bin/env python3
"""
Sentinel-X Orchestrator
One-command full security assessment pipeline

Usage:
    python3 sentinelx.py example.com

Ethical: YES
"""

import sys
import subprocess
import time
from pathlib import Path

BASE_DIR = Path.home() / "SentinelX"

PIPELINE = [
    ("Passive Discovery", "modules/asset_discovery/passive_discovery.py"),
    ("Aggressive Discovery", "modules/asset_discovery/aggressive_recon.py"),
    ("Asset Validation", "modules/asset_discovery/asset_validation.py"),
    ("Asset Classification", "modules/asset_discovery/asset_classification.py"),
    ("Risk Scoring", "modules/asset_discovery/risk_scoring.py"),
    ("TLS Analysis", "modules/tls_analysis/tls_analyzer.py"),
    ("Unified Report", "modules/reporting/unified_report.py"),
    ("🔴 RED TEAM EXPLOITATION", "modules/redteam/redteam_orchestrator.py"),
]

def run_step(step_name: str, script_path: str, domain: str):
    print(f"\n🚀 {step_name}")
    print("-" * 60)

    full_path = BASE_DIR / script_path

    if not full_path.exists():
        print(f"❌ Missing module: {full_path}")
        sys.exit(1)

    cmd = ["python3", str(full_path), domain]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print(f"\n❌ Failed at step: {step_name}")
        print("🛑 Pipeline stopped to prevent inconsistent results.")
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 sentinelx.py <domain>")
        sys.exit(1)

    domain = sys.argv[1].strip()

    print("\n🛡️  SENTINEL-X SECURITY ORCHESTRATOR")
    print(f"🎯 Target: {domain}")
    print("=" * 60)

    start_time = time.time()

    for step_name, script in PIPELINE:
        run_step(step_name, script, domain)

    duration = round(time.time() - start_time, 2)

    print("\n" + "=" * 60)
    print("✅ SENTINEL-X PIPELINE COMPLETE")
    print(f"⏱️  Time Taken: {duration} seconds")
    print(f"📁 Report: recon/reports/{domain}_security_report.html")
    print("=" * 60)

    print("\n📊 Open report with:")
    print(f"   xdg-open recon/reports/{domain}_security_report.html\n")

if __name__ == "__main__":
    main()
