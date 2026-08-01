import yaml
import requests
import collections
import time

INPUT_FILE = "valid_proxies.yaml"
OUTPUT_FILE = "cn_hk_proxies.yaml"

CN_FLAG = "\U0001F1E8\U0001F1F3"
HK_FLAG = "\U0001F1ED\U0001F1F0"

COUNTRY_FLAGS = {
    "CN": CN_FLAG,
    "HK": HK_FLAG,
}

country_names = {
    "CN": "中国",
    "HK": "香港",
}

def load_proxies(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("proxies", [])

def match_by_flag(proxy: dict) -> str | None:
    name = proxy.get("name", "")
    if name.startswith(CN_FLAG):
        return "CN"
    if name.startswith(HK_FLAG):
        return "HK"
    return None

def batch_query_country(servers: list) -> dict:
    result = {}
    for i in range(0, len(servers), 100):
        batch = servers[i:i+100]
        queries = [{"query": s} for s in batch]
        for attempt in range(3):
            try:
                resp = requests.post("http://ip-api.com/batch", json=queries, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                for q, server in zip(data, batch):
                    if q.get("status") == "success" and q.get("countryCode") in ("CN", "HK"):
                        result[server] = q["countryCode"]
                    else:
                        result[server] = None
                break
            except requests.RequestException as e:
                print(f"Batch query attempt {attempt+1}/3 failed: {e}")
                time.sleep(2)
                if attempt == 2:
                    for server in batch:
                        result[server] = None
    return result

def valid_proxy_fields(proxy: dict) -> bool:
    ptype = proxy.get("type", "").lower()
    required = {
        "ss": ["server", "port", "cipher", "password"],
        "trojan": ["server", "port", "password"],
        "vmess": ["server", "port", "uuid", "alterid", "cipher"],
        "vless": ["server", "port", "uuid"],
        "hysteria2": ["server", "port", "password"],
        "socks5": ["server", "port"],
        "http": ["server", "port"],
    }
    fields = required.get(ptype, ["server", "port"])
    for f in fields:
        if f not in proxy or proxy[f] is None or proxy[f] == "":
            return False
    return True

def main():
    proxies = load_proxies(INPUT_FILE)
    print(f"Loaded {len(proxies)} proxies from {INPUT_FILE}")

    flagged = []
    remaining = []
    for p in proxies:
        cc = match_by_flag(p)
        if cc:
            flagged.append((cc, p))
        else:
            remaining.append(p)

    print(f"Flag-matched: {len(flagged)} CN/HK, remaining for IP lookup: {len(remaining)}")

    servers_to_check = []
    for p in remaining:
        server = p.get("server", "")
        if server and not server.startswith(("0.", "127.", "10.", "172.16.", "192.168.", "169.254.")):
            servers_to_check.append(server)

    ip_countries = batch_query_country(list(set(servers_to_check)))

    for p in remaining:
        server = p.get("server", "")
        cc = ip_countries.get(server)
        if cc:
            flagged.append((cc, p))

    print(f"Total CN/HK after IP lookup: {len(flagged)}")

    seen = set()
    merged = []
    counters = {"CN": 1, "HK": 1}

    for cc, p in flagged:
        if not valid_proxy_fields(p):
            print(f"Skipping invalid proxy: {p.get('name', 'unknown')}")
            continue
        key = (p.get("server"), p.get("port"), p.get("type"))
        if key in seen:
            continue
        seen.add(key)

        ordered = collections.OrderedDict()
        flag = COUNTRY_FLAGS[cc]
        new_name = f"{flag} {str(counters[cc]).zfill(3)}"
        counters[cc] += 1
        ordered["name"] = new_name
        ordered["type"] = p["type"]
        ordered["server"] = p["server"]
        ordered["port"] = p["port"]

        for k, v in p.items():
            if k in ("name", "type", "server", "port"):
                continue
            ordered[k] = v

        merged.append(dict(ordered))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        yaml.dump({"proxies": merged}, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    print(f"Written {len(merged)} CN/HK proxies to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
