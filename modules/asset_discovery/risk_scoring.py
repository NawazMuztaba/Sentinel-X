#!/usr/bin/env python3
"""
Sentinel-X | Module: Risk Scoring Engine
Version: 1.0
Purpose: Aggregate classified assets into a single risk score
Ethical use
"""

import os
import json
import sys
import time
import glob

BASE_DIR = os.path.expanduser("~/SentinelX")
INPUT_DIR = os.path.join(BASE_DIR, "recon", "classified")
OUTPUT_DIR = os.path.join(BASE_DIR, "recon", "scored")

WEIGHTS = {
    "CRITICAL": 10,
    "HIGH": 6,
    "MEDIUM": 3,
    "LOW": 1
}

def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def calculate_score(assets):
    total_weight = 0
    max_possible = len(assets) * WEIGHTS["CRITICAL"]

    breakdown = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for a in assets:
        risk = a.get("risk_level", "LOW")
        breakdown[risk] += 1
        total_weight += WEIGHTS.get(risk, 1)

    score = int((total_weight / max_possible) * 100) if max_possible else 0
    return score, breakdown

def score_to_label(score):
    if score >= 75:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 25:
        return "MEDIUM"
    return "LOW"

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 risk_scoring.py <domain>")
        sys.exit(1)

    domain = sys.argv[1]
    ensure_dirs()

    files = glob.glob(f"{INPUT_DIR}/{domain}_classified.json")
    if not files:
        print(f"[!] No classified data for {domain}")
        sys.exit(1)

    input_file = files[0]
    with open(input_file) as f:
        data = json.load(f)

    assets = data.get("assets", [])
    score, breakdown = calculate_score(assets)
    overall = score_to_label(score)

    reasons = []
    if breakdown["HIGH"] > 0:
        reasons.append(f"{breakdown['HIGH']} high-risk assets exposed")
    if breakdown["CRITICAL"] > 0:
        reasons.append(f"{breakdown['CRITICAL']} critical assets exposed")

    report = {
        "project": "Sentinel-X",
        "module": "Risk Scoring",
        "target": domain,
        "scored_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "overall_risk": overall,
        "score": score,
        "breakdown": breakdown,
        "key_reasons": reasons or ["No significant high-risk exposure detected"]
    }

    out = os.path.join(OUTPUT_DIR, f"{domain}_risk.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)

    print("🎯 RISK SCORING COMPLETE")
    print(f"Target: {domain}")
    print(f"Overall Risk: {overall}")
    print(f"Score: {score}/100")
    print(f"Report: {out}")

if __name__ == "__main__":
    main()
