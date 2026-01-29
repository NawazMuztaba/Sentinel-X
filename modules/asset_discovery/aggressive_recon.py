#!/usr/bin/env python3
"""
Sentinel-X | Advanced Aggressive Asset Discovery Engine v2.0
"""

import os
import json
import datetime
import subprocess
import sys
import requests
import socket
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Set
import time

# CONFIGURATION
BASE_DIR = os.path.expanduser("~/SentinelX")
OUTPUT_DIR = os.path.join(BASE_DIR, "recon", "aggressive")
LOG_DIR = os.path.join(BASE_DIR, "logs", "aggressive_enum")

VT_API = os.getenv("VT_API_KEY", "")
CHAOS_API = os.getenv("CHAOS_KEY", "")
MAX_THREADS = 20
CDN_BYPASS_HOSTS = ["nip.io", "xip.io", "sslip.io"]

class AggressiveRecon:
    def __init__(self, domain: str):
        self.domain = domain.rstrip('.')
        self.all_assets: Set[str] = set()
        self.takeover_candidates = []
        self.cloud_assets = []

    def ct_logs(self) -> List[str]:
        """Certificate Transparency Exhaustion"""
        cmd = f"curl -s 'https://crt.sh/?q=%25.{self.domain}&output=json' | jq -r '.[].name_value' 2>/dev/null | sed 's/*\\.//g' | sort -u | grep {self.domain}"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            return [line.strip() for line in result.stdout.splitlines() if line]
        except:
            return []

    def subfinder(self) -> List[str]:
        """Aggressive Subfinder"""
        try:
            result = subprocess.run(["subfinder", "-d", self.domain, "-silent"], 
                                  capture_output=True, text=True, timeout=120)
            return [line.strip() for line in result.stdout.splitlines()]
        except:
            return []

    def dns_wildcard_filter(self, subdomains: List[str]) -> List[str]:
        """Wildcard Detection"""
        resolutions = {}
        def resolve(host):
            try:
                ip = socket.gethostbyname(host)
                return hash(ip)
            except:
                return None
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(resolve, sub): sub for sub in subdomains[:50]}
            for future in as_completed(futures):
                h = future.result()
                if h:
                    resolutions[futures[future]] = h
        
        # Filter wildcards
        hash_count = {}
        for host, hhash in resolutions.items():
            hash_count.setdefault(hhash, 0)
            hash_count[hhash] += 1
        
        wildcard_hashes = [h for h, count in hash_count.items() if count > 2]
        return [sub for sub in subdomains if resolutions.get(sub, 0) not in wildcard_hashes]

    def takeover_scan(self, subdomains: List[str]):
        """Basic Takeover Check"""
        subs_file = f"/tmp/{self.domain}_subs.txt"
        with open(subs_file, 'w') as f:
            f.write('\n'.join(subdomains))
        
        try:
            cmd = f"nuclei -l {subs_file} -t takeover -silent"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            for line in result.stdout.splitlines():
                if "takeover" in line.lower():
                    self.takeover_candidates.append(line.split()[0])
        except:
            pass
        finally:
            os.unlink(subs_file)

    def run(self):
        print(f"[🚀] AGGRESSIVE RECON: {self.domain}")
        
        # Passive Sources
        print("[1/4] CT Logs...")
        self.all_assets.update(self.ct_logs())
        
        print("[2/4] Subfinder...")
        self.all_assets.update(self.subfinder())
        
        # Validation
        print("[3/4] Wildcard Filter...")
        validated = self.dns_wildcard_filter(list(self.all_assets))
        self.all_assets = set(validated)
        
        print("[4/4] Takeover Scan...")
        self.takeover_scan(validated)
        
        self.save_report()

    def save_report(self):
        """Save Exploit-Ready Report"""
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        report = {
            "target": self.domain,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "total_assets": len(self.all_assets),
            "takeovers": len(self.takeover_candidates),
            "critical_assets": self.takeover_candidates[:10],
            "assets": list(self.all_assets)
        }
        
        filepath = os.path.join(OUTPUT_DIR, f"{self.domain}_aggressive.json")
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"[✓] SAVED: {filepath}")
        print(f"[✓] {len(self.all_assets)} assets, {len(self.takeover_candidates)} takeovers")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 aggressive_recon.py <domain>")
        sys.exit(1)
    
    recon = AggressiveRecon(sys.argv[1])
    recon.run()

if __name__ == "__main__":
    main()
