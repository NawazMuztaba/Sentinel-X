#!/usr/bin/env python3
"""
Sentinel-X | Module: TLS / HTTPS Security Analyzer
Purpose: TLS hygiene & HTTPS posture assessment
Ethical: Passive TLS handshake + HTTP header checks only
"""

import ssl
import socket
import json
import sys
import os
import asyncio
import aiohttp
from datetime import datetime, timezone
from typing import Dict, List
from OpenSSL import crypto

BASE_DIR = os.path.expanduser("~/SentinelX")
INPUT_DIR = os.path.join(BASE_DIR, "recon", "validated")
OUTPUT_DIR = os.path.join(BASE_DIR, "recon", "tls")

# -----------------------------
# Helpers
# -----------------------------

def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_live_assets(domain: str) -> List[str]:
    path = os.path.join(INPUT_DIR, f"{domain}_validated.json")
    if not os.path.exists(path):
        print(f"[!] Validated file not found: {path}")
        sys.exit(1)

    with open(path) as f:
        data = json.load(f)

    return [
        asset["asset"]
        for asset in data.get("assets", [])
        if asset.get("status") == "LIVE"
    ]

def decode_x509_name(x509_name):
    """Convert X509Name bytes → JSON-safe strings"""
    return {
        k.decode(): v.decode()
        for k, v in x509_name.get_components()
    }

# -----------------------------
# TLS Checks
# -----------------------------

def get_certificate_info(hostname: str, timeout=6) -> Dict:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        with socket.create_connection((hostname, 443), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert_bin = ssock.getpeercert(binary_form=True)
                x509 = crypto.load_certificate(crypto.FILETYPE_ASN1, cert_bin)

                not_after = datetime.strptime(
                    x509.get_notAfter().decode(), "%Y%m%d%H%M%SZ"
                ).replace(tzinfo=timezone.utc)

                days_left = (not_after - datetime.now(timezone.utc)).days

                return {
                    "valid": True,
                    "issuer": decode_x509_name(x509.get_issuer()),
                    "subject": decode_x509_name(x509.get_subject()),
                    "expires_at": not_after.isoformat(),
                    "days_until_expiry": days_left,
                    "expired": days_left < 0,
                    "expiring_soon": days_left <= 30,
                    "self_signed": x509.get_issuer() == x509.get_subject()
                }
    except Exception as e:
        return {"valid": False, "error": str(e)}

async def check_https_enforcement(domain: str) -> Dict:
    url = f"http://{domain}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, allow_redirects=False, timeout=6) as resp:
                if resp.status in (301, 302, 307, 308):
                    location = resp.headers.get("Location", "")
                    return {
                        "http_redirect": True,
                        "redirects_to_https": location.startswith("https")
                    }
                return {"http_redirect": False}
    except Exception:
        return {"http_redirect": None}

async def analyze_asset(domain: str) -> Dict:
    cert = await asyncio.to_thread(get_certificate_info, domain)
    redirect = await check_https_enforcement(domain)

    score = 100
    if not cert.get("valid"):
        score -= 40
    if cert.get("expired"):
        score -= 30
    if cert.get("expiring_soon"):
        score -= 10
    if not redirect.get("redirects_to_https", False):
        score -= 20

    if score >= 85:
        risk = "LOW"
    elif score >= 65:
        risk = "MEDIUM"
    elif score >= 45:
        risk = "HIGH"
    else:
        risk = "CRITICAL"

    return {
        "hostname": domain,
        "certificate": cert,
        "https_enforcement": redirect,
        "tls_score": score,
        "risk_level": risk
    }

# -----------------------------
# Main
# -----------------------------

async def main():
    if len(sys.argv) != 2:
        print("Usage: python3 tls_analyzer.py <domain>")
        sys.exit(1)

    domain = sys.argv[1]
    ensure_dirs()

    print(f"🔐 Sentinel-X TLS Analyzer")
    print(f"Target: {domain}")
    print("-" * 50)

    assets = load_live_assets(domain)
    print(f"[+] {len(assets)} LIVE assets")

    results = []
    for host in assets:
        result = await analyze_asset(host)
        results.append(result)
        print(f"  {host:<30} → {result['risk_level']} ({result['tls_score']})")

    report = {
        "project": "Sentinel-X",
        "module": "TLS Analyzer",
        "target": domain,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_assets": len(results),
            "by_risk": {
                "LOW": len([r for r in results if r["risk_level"] == "LOW"]),
                "MEDIUM": len([r for r in results if r["risk_level"] == "MEDIUM"]),
                "HIGH": len([r for r in results if r["risk_level"] == "HIGH"]),
                "CRITICAL": len([r for r in results if r["risk_level"] == "CRITICAL"])
            }
        },
        "assets": results
    }

    out_file = os.path.join(OUTPUT_DIR, f"{domain}_tls.json")
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2)

    print("\n✅ TLS ANALYSIS COMPLETE")
    print(f"📁 Report: {out_file}")

if __name__ == "__main__":
    asyncio.run(main())
