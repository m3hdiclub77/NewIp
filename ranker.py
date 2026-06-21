# ranker.py
import os

RESULT_FILE = "output/results.txt"
HTTPS_FILE = "output/https_live.txt"
BEST_FILE = "output/best_ips.txt"
DOMAINS_RAW_FILE = "output/domains_raw.txt"

TLS_BONUS = 2
KNOWN_CDN_BONUS = 2
H2_BONUS = 2
ALPN_BONUS = 1
HTTPS_BONUS = 4
RELIABILITY_BONUS = 3

FAST_LATENCY_BONUS = 3
MID_LATENCY_BONUS = 2
SLOW_LATENCY_BONUS = 1

FAST_TTFB_BONUS = 4
MID_TTFB_BONUS = 2
SLOW_TTFB_BONUS = 1

STABLE_PORTS = {443, 2053, 2083, 2087, 2096, 8443}
STABLE_PORT_BONUS = 1

MAX_OUTPUT_IPS = 4000

def load_https():
    data = {}
    try:
        with open(HTTPS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("|")
                if len(parts) < 6:
                    continue
                try:
                    ip = parts[0]
                    port = int(parts[1])
                    status = int(parts[2])
                    ttfb = int(parts[3])
                    proto = parts[4]
                    reliability = float(parts[5])
                except:
                    continue
                key = f"{ip}:{port}"
                candidate = {"status": status, "ttfb": ttfb, "proto": proto, "reliability": reliability}
                if key not in data:
                    data[key] = candidate
                else:
                    old = data[key]
                    if reliability > old["reliability"] or (reliability == old["reliability"] and ttfb < old["ttfb"]):
                        data[key] = candidate
    except:
        pass
    return data

def load_tls_data():
    data = {}
    try:
        with open("output/tls_live.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(":")
                if len(parts) >= 6:
                    ip = parts[0]
                    port = parts[1]
                    latency = parts[2]
                    alpn = parts[3]
                    sni = parts[4]
                    issuer = parts[5]
                    key = f"{ip}:{port}"
                    data[key] = {"latency": int(latency), "alpn": alpn, "sni": sni, "issuer": issuer}
    except:
        pass
    return data

def parse_result_line(line):
    line = line.strip()
    if not line:
        return None
    parts = line.split("|")
    if len(parts) < 10:
        return None
    try:
        ip = parts[0]
        port = int(parts[1])
        status = int(parts[2])
        ttfb = int(parts[3])
        proto = parts[4]
        reliability = float(parts[5])
        ws = parts[6]
        cdn = parts[7]
        country = parts[8]
        provider = parts[9]
        return {
            "ip": ip,
            "port": port,
            "status": status,
            "ttfb": ttfb,
            "proto": proto,
            "reliability": reliability,
            "ws": ws,
            "cdn": cdn,
            "country": country,
            "provider": provider
        }
    except:
        return None

def load_results():
    data = []
    seen = set()
    try:
        with open(RESULT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                item = parse_result_line(line)
                if not item:
                    continue
                key = f"{item['ip']}:{item['port']}"
                if key in seen:
                    continue
                seen.add(key)
                data.append(item)
    except:
        pass
    return data

def load_previous_best_ips():
    if not os.path.exists(BEST_FILE):
        return []
    previous = []
    try:
        with open(BEST_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) < 2:
                    continue
                ip_port = parts[0]
                try:
                    score_val = int(parts[1].replace("S=", ""))
                except:
                    score_val = 0
                if ":" in ip_port:
                    previous.append({
                        "ip": ip_port.split(":")[0],
                        "port": int(ip_port.split(":")[1]),
                        "score": score_val,
                        "is_new": False
                    })
    except:
        pass
    return previous

def merge_and_limit(new_items, previous_items):
    combined = []
    for item in new_items:
        combined.append({
            "ip": item["ip"],
            "port": item["port"],
            "score": item.get("score", 0),
            "is_new": True,
            "latency": item.get("latency", 9999),
            "ttfb": item.get("ttfb", 9999),
            "proto": item.get("proto", "-"),
            "reliability": item.get("reliability", 0),
            "cdn": item.get("cdn", "unknown"),
            "country": item.get("country", "?"),
            "provider": item.get("provider", "?"),
            "alpn": item.get("alpn", ""),
            "ws": item.get("ws", 0)
        })
    for old in previous_items:
        combined.append(old)
    combined.sort(key=lambda x: (-x["score"], 0 if x["is_new"] else 1, x.get("latency", 9999)))
    seen_keys = set()
    limited = []
    for item in combined:
        key = f"{item['ip']}:{item['port']}"
        if key in seen_keys:
            continue
        seen_keys.add(key)
        limited.append(item)
        if len(limited) >= MAX_OUTPUT_IPS:
            break
    return limited

def score_item(item):
    score = 0
    if item.get("ttfb", 9999) < 500:
        score += 10
    if item.get("reliability", 0) > 0.8:
        score += 10
    if item.get("cdn", "unknown") != "unknown":
        score += 5
    if item.get("alpn", "") == "h2":
        score += 5
    if item.get("port", 0) in STABLE_PORTS:
        score += 3
    return score

def rank_results():
    results = load_results()
    https_data = load_https()
    tls_data = load_tls_data()
    previous_best = load_previous_best_ips()
    
    scored_items = []
    for item in results:
        key = f"{item['ip']}:{item['port']}"
        if key in tls_data:
            item["latency"] = tls_data[key].get("latency", 9999)
            item["alpn"] = tls_data[key].get("alpn", "")
        else:
            item["latency"] = 9999
            item["alpn"] = ""
        item["score"] = score_item(item)
        scored_items.append(item)
    
    merged = merge_and_limit(scored_items, previous_best)
    
    os.makedirs("output", exist_ok=True)
    with open(BEST_FILE, "w", encoding="utf-8") as f:
        for item in merged:
            latency = item.get("latency", 9999)
            ttfb = item.get("ttfb", "-")
            proto = item.get("proto", "-")
            rel = item.get("reliability", "-")
            cdn = item.get("cdn", "unknown")
            alpn = item.get("alpn", "")
            country = item.get("country", "?")
            provider = item.get("provider", "?")
            f.write(f"{item['ip']}:{item['port']} S={item['score']} {latency}ms TTFB={ttfb} PROTO={proto} REL={rel} CDN={cdn} ALPN={alpn} {country} {provider}\n")
    
    print(f"RANKED={len(results)} HTTPS={len(https_data)} TLS={len(tls_data)} BEST_IPS={len(merged)}")

if __name__ == "__main__":
    rank_results()
