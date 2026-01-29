#!/usr/bin/env python3
import sys
import json
sys.path.insert(0, "/home/kali/SentinelX")

def normalize_asset(raw_asset):
    """Convert ANY asset format to standard dict"""
    asset = {}
    
    # Handle string assets (just URLs)
    if isinstance(raw_asset, str):
        asset = {'url': raw_asset, 'classification': 'UNKNOWN', 'https': False}
        return asset
    
    # Handle dict assets
    if isinstance(raw_asset, dict):
        asset.update(raw_asset)
        if 'url' not in asset:
            asset['url'] = asset.get('host', 'unknown')
        return asset
    
    # Handle lists [url, data]
    if isinstance(raw_asset, list):
        if len(raw_asset) >= 1:
            asset['url'] = raw_asset[0] if isinstance(raw_asset[0], str) else 'unknown'
        if len(raw_asset) >= 2 and isinstance(raw_asset[1], dict):
            asset.update(raw_asset[1])
        return asset
    
    return {'url': 'unknown', 'classification': 'UNKNOWN'}

def score_asset(asset):
    """Score normalized asset"""
    classification = asset.get('classification', 'UNKNOWN')
    
    score = 0
    if 'LOGIN_PORTAL' in classification.upper():
        score += 100
    elif 'STATIC_SITE' in classification.upper():
        score += 50
    elif 'API' in classification.upper():
        score += 75
    elif 'ADMIN' in classification.upper():
        score += 80
    
    # HTTP bonus
    url = asset.get('url', '').lower()
    if 'http://' in url and 'https://' not in url:
        score += 25
    
    # Main domain bonus (heuristic)
    if 'lpu.in' in url or any(x in url for x in ['www.', 'main.', 'home']):
        score += 20
    
    # Ports bonus
    ports = asset.get('ports', [])
    if isinstance(ports, list):
        score += len(ports) * 2
    
    return score

def select_primary_target(raw_assets):
    """Universal asset selector - handles ALL classified.json formats"""
    print(f"🔍 Parsing {len(raw_assets)} raw assets...")
    
    # Flatten ALL possible structures
    flat_assets = []
    if isinstance(raw_assets, dict):
        for key, value in raw_assets.items():
            if isinstance(value, (list, dict)):
                if isinstance(value, list):
                    for item in value:
                        flat_assets.append(normalize_asset(item))
                else:
                    flat_assets.append(normalize_asset(value))
            else:
                flat_assets.append(normalize_asset(value))
    elif isinstance(raw_assets, list):
        flat_assets = [normalize_asset(item) for item in raw_assets]
    
    # Filter & score valid assets
    scored_assets = []
    for asset in flat_assets:
        if asset['url'] != 'unknown':
            score = score_asset(asset)
            if score > 0:
                scored_assets.append((score, asset))
    
    if not scored_assets:
        print("❌ No valid exploitable assets found")
        return None
    
    # Sort & select
    scored_assets.sort(key=lambda x: x[0], reverse=True)
    best_target = scored_assets[0][1]
    
    print(f"📊 Top Targets Found:")
    for i, (score, asset) in enumerate(scored_assets[:5]):
        status = "🎯 SELECTED" if i == 0 else ""
        print(f"   {i+1}. {score}pts - {asset['url']} [{asset['classification']}] {status}")
    
    return best_target
