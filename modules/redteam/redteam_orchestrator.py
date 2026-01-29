#!/usr/bin/env python3
import sys
import os
import json
sys.path.insert(0, "/home/kali/SentinelX")

from modules.redteam.target_selector import select_primary_target
from modules.redteam.exploit_engine import run_exploitation
from modules.redteam.redteam_report import generate_redteam_report

def main(domain):
    print(f"🔴 [RED TEAM] Starting exploitation phase for {domain}")
    
    classified_file = f"recon/classified/{domain}_classified.json"
    if not os.path.exists(classified_file):
        print(f"❌ No classified assets found: {classified_file}")
        return False
    
    with open(classified_file, 'r') as f:
        assets = json.load(f)
    
    target = select_primary_target(assets)
    if not target:
        print("❌ No suitable targets found")
        return False
    
    print(f"🎯 Primary Target: {target['url']} ({target['classification']})")
    
    exploits = run_exploitation(target, domain)
    generate_redteam_report(domain, target, exploits)
    
    print(f"✅ Red Team phase COMPLETE for {domain}")
    return True

if __name__ == "__main__":
    domain = sys.argv[1] if len(sys.argv) > 1 else "lpu.in"
    main(domain)
