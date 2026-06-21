import os
import json
import time
import shutil
from datetime import datetime, timedelta
from typing import Set, List, Optional

CRITICAL_FILES = {
    "best_ips.txt",
    "domains.txt",
    "scan_cursor.txt",
    "current_part.txt",
    "geo_cache.json"
}

EPHEMERAL_FILES = {
    "ip_bank.txt",
    "clean_ips.txt",
    "tcp_live.txt",
    "tls_live.txt",
    "https_live.txt",
    "fingerprint_results.txt",
    "scanned_cache.txt",
    "results.txt",
    "domains_raw.txt",
    "live_bank.txt"
}

CACHE_TTL_HOURS = 24
OUTPUT_DIR = "output"


def ensure_output():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_previous_ips() -> Set[str]:
    ip_set = set()
    best_file = os.path.join(OUTPUT_DIR, "best_ips.txt")
    
    if not os.path.exists(best_file):
        return ip_set
    
    try:
        with open(best_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if parts:
                    ip_port = parts[0]
                    ip_set.add(ip_port)
    except:
        pass
    
    return ip_set


def clean_duplicates_from_live_bank():
    live_bank = os.path.join(OUTPUT_DIR, "live_bank.txt")
    
    if not os.path.exists(live_bank):
        return
    
    previous_ips = load_previous_ips()
    
    new_ips = set()
    try:
        with open(live_bank, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and line not in previous_ips:
                    new_ips.add(line)
    except:
        pass
    
    if new_ips:
        with open(live_bank, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(new_ips)) + "\n")
    else:
        os.remove(live_bank)
    
    return len(new_ips)


def clean_cache_files():
    scanned_cache = os.path.join(OUTPUT_DIR, "scanned_cache.txt")
    
    if not os.path.exists(scanned_cache):
        return
    
    previous_ips = load_previous_ips()
    
    new_cache = {}
    try:
        with open(scanned_cache, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(":")
                if len(parts) >= 2:
                    ip_port = f"{parts[0]}:{parts[1]}"
                    if ip_port not in previous_ips:
                        new_cache[line] = True
    except:
        pass
    
    if new_cache:
        with open(scanned_cache, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(new_cache.keys())) + "\n")
    else:
        os.remove(scanned_cache)
    
    return len(new_cache)


def clean_ephemeral_files():
    cleaned = []
    
    for filename in EPHEMERAL_FILES:
        filepath = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(filepath):
            try:
                mtime = os.path.getmtime(filepath)
                age = datetime.now() - datetime.fromtimestamp(mtime)
                if age > timedelta(hours=CACHE_TTL_HOURS):
                    os.remove(filepath)
                    cleaned.append(filename)
                elif filename not in CRITICAL_FILES:
                    os.remove(filepath)
                    cleaned.append(filename)
            except:
                pass
    
    return cleaned


def compact_artifact():
    ensure_output()
    
    live_count = clean_duplicates_from_live_bank()
    cache_count = clean_cache_files()
    
    ephemeral_cleaned = clean_ephemeral_files()
    
    for filename in ["best_ips.txt", "domains.txt"]:
        filepath = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(filepath):
            try:
                lines = set()
                with open(filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            lines.add(line)
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write("\n".join(sorted(lines)) + "\n")
            except:
                pass
    
    for filename in os.listdir(OUTPUT_DIR):
        filepath = os.path.join(OUTPUT_DIR, filename)
        if os.path.isfile(filepath) and os.path.getsize(filepath) == 0:
            os.remove(filepath)
    
    stats = {
        "live_bank_new_ips": live_count or 0,
        "cache_entries": cache_count or 0,
        "ephemeral_cleaned": len(ephemeral_cleaned)
    }
    
    return stats


def get_artifact_size() -> int:
    total_size = 0
    if not os.path.exists(OUTPUT_DIR):
        return 0
    
    for dirpath, _, filenames in os.walk(OUTPUT_DIR):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
            except:
                pass
    
    return total_size


def artifact_info():
    size_bytes = get_artifact_size()
    size_mb = size_bytes / (1024 * 1024)
    
    files = []
    if os.path.exists(OUTPUT_DIR):
        for filename in os.listdir(OUTPUT_DIR):
            filepath = os.path.join(OUTPUT_DIR, filename)
            if os.path.isfile(filepath):
                try:
                    size = os.path.getsize(filepath)
                    files.append(f"{filename}: {size/1024:.1f}KB")
                except:
                    pass
    
    return {
        "total_size_mb": round(size_mb, 2),
        "file_count": len(files),
        "files": files
    }


if __name__ == "__main__":
    stats = compact_artifact()
    info = artifact_info()
    
    print("=" * 50)
    print("ARTIFACT COMPACT RESULT")
    print("=" * 50)
    print(f"New IPs from live_bank: {stats['live_bank_new_ips']}")
    print(f"Cache entries kept: {stats['cache_entries']}")
    print(f"Ephemeral cleaned: {stats['ephemeral_cleaned']}")
    print(f"Total size: {info['total_size_mb']} MB")
    print(f"Files: {info['file_count']}")
    print("=" * 50)
