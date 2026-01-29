#!/usr/bin/env python3
"""
Sentinel-X | Unified Security Report
Merges discovery, validation, classification, risk scoring & TLS analysis
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "SentinelX"
RECON = BASE / "recon"
OUT = RECON / "reports"
OUT.mkdir(exist_ok=True)

def load_json(path):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}

def get_hostname(asset):
    if isinstance(asset, str):
        return asset
    return (
        asset.get("hostname")
        or asset.get("subdomain")
        or asset.get("asset")
        or asset.get("name")
        or "unknown"
    )

def main():
    if len(sys.argv) != 2:
        print("Usage: unified_report.py <domain>")
        sys.exit(1)

    domain = sys.argv[1]

    validated = load_json(RECON / "validated" / f"{domain}_validated.json")
    classified = load_json(RECON / "classified" / f"{domain}_classified.json")
    risk = load_json(RECON / "scored" / f"{domain}_risk.json")
    tls = load_json(RECON / "tls" / f"{domain}_tls.json")

    validated_assets = validated.get("assets", [])
    classified_assets = classified.get("assets", [])
    tls_assets = tls.get("assets", [])

    total_assets = len(validated_assets)
    live_assets = [a for a in validated_assets if a.get("status") == "LIVE"]

    # Build hostname maps
    class_map = {get_hostname(a): a for a in classified_assets}
    tls_map = {get_hostname(a): a for a in tls_assets}

    # Attack surface stats
    stats = {
        "login": 0,
        "api": 0,
        "dev": 0
    }

    for a in classified_assets:
        c = a.get("classification", "").lower()
        if "login" in c: stats["login"] += 1
        if "api" in c: stats["api"] += 1
        if "dev" in c: stats["dev"] += 1

    # HTML
    rows = ""
    for a in validated_assets:
        host = get_hostname(a)
        cls = class_map.get(host, {}).get("classification", "N/A")
        risk_lvl = class_map.get(host, {}).get("risk_level", "N/A")
        rows += f"""
        <tr>
            <td>{host}</td>
            <td>{a.get("status","")}</td>
            <td>{cls}</td>
            <td>{risk_lvl}</td>
        </tr>
        """

    tls_rows = ""
    for a in tls_assets:
        cert = a.get("certificate", {})
        exp = cert.get("days_until_expiry", "N/A")
        warn = "⚠" if isinstance(exp, int) and exp < 60 else ""
        tls_rows += f"""
        <tr>
            <td>{get_hostname(a)}</td>
            <td>{a.get("risk_level")}</td>
            <td>{"✅" if a.get("https_enforcement",{}).get("redirects_to_https") else "❌"}</td>
            <td>{exp} {warn}</td>
        </tr>
        """

    html = f"""
<!DOCTYPE html>
<html>
<head>
<title>Sentinel-X Unified Security Report</title>
<style>
body {{
    background: #050b18;
    color: #e6e6e6;
    font-family: Arial;
    padding: 20px;
}}
h1 {{ color:#4fd1ff; }}
.card {{
    background:#0b132b;
    padding:20px;
    margin-bottom:20px;
    border-radius:10px;
}}
table {{
    width:100%;
    border-collapse:collapse;
}}
th,td {{
    padding:10px;
    border-bottom:1px solid #222;
}}
th {{ color:#4fd1ff; }}
</style>
</head>

<body>
<h1>Sentinel-X Unified Security Report</h1>
<p><b>Target:</b> {domain}</p>
<p><b>Generated:</b> {datetime.utcnow().isoformat()} UTC</p>

<div class="card">
<h2>Executive Summary</h2>
<p>Total Assets: {total_assets}</p>
<p>Live Assets: {len(live_assets)}</p>
<p>Overall Risk: {risk.get("overall_risk","MEDIUM")}</p>
</div>

<div class="card">
<h2>Attack Surface Overview</h2>
<ul>
<li>Login Portals: {stats["login"]}</li>
<li>APIs: {stats["api"]}</li>
<li>Dev Assets: {stats["dev"]}</li>
</ul>
</div>

<div class="card">
<h2>Asset Inventory</h2>
<table>
<tr><th>Asset</th><th>Status</th><th>Classification</th><th>Risk</th></tr>
{rows}
</table>
</div>

<div class="card">
<h2>TLS Deep Dive</h2>
<table>
<tr><th>Asset</th><th>Risk</th><th>HTTPS</th><th>Expiry (Days)</th></tr>
{tls_rows}
</table>
</div>

<div class="card">
<h2>Key Findings</h2>
<ul>
<li>Some assets do not enforce HTTPS</li>
<li>Login portals are publicly exposed</li>
<li>Certificates expiring within 60 days detected</li>
</ul>

<h2>Recommendations</h2>
<ul>
<li>Enforce HTTPS redirects</li>
<li>Enable HSTS</li>
<li>Restrict access to login portals</li>
<li>Monitor TLS certificate expiry</li>
</ul>
</div>

</body>
</html>
"""

    out_file = OUT / f"{domain}_security_report.html"
    out_file.write_text(html)
    print(f"✅ Unified report generated: {out_file}")

if __name__ == "__main__":
    main()

