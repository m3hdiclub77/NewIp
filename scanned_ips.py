import os

SCANNED_IPS_FILE = "output/scanned_ips.txt"

def ensure_output():
    os.makedirs("output", exist_ok=True)

def load_scanned_ips():
    ensure_output()
    if not os.path.exists(SCANNED_IPS_FILE):
        return set()
    try:
        with open(SCANNED_IPS_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    except:
        return set()

def save_scanned_ips(ips):
    ensure_output()
    try:
        with open(SCANNED_IPS_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(ips)))
    except:
        pass

def add_scanned_ips(new_ips):
    existing = load_scanned_ips()
    existing.update(new_ips)
    save_scanned_ips(existing)
    return len(existing)

def is_scanned(ip):
    return ip in load_scanned_ips()

def scanned_count():
    return len(load_scanned_ips())

def reset_scanned_ips():
    save_scanned_ips(set())
