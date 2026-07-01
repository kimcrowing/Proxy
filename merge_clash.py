import hashlib
import socket
import re
from collections import defaultdict
from ipaddress import ip_address
from typing import Dict

import requests
import yaml

try:
    import geoip2.database
except ImportError:
    geoip2 = None

# ================= 配置 =================
CONFIG_URLS = [
    "https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/c.yaml",
]

MMDB_PATH = "GeoLite2-Country.mmdb"

DOMAIN_RULES = {
    "hk": "HK", "tw": "TW", "us": "US", "sg": "SG", "jp": "JP", "kr": "KR",
    "868863.xyz": "HK", "bestcdn": "HK", "netvora.space": "HK",
    "206352.xyz": "HK", "206353.xyz": "HK", "206355.xyz": "HK",
    "cloudflare": "US", "akamai": "US", "fastly": "US",
    "cdn": "HK", "v2ray": "CN", "proxy": "CN", "speed": "HK",
    "xyz": "HK", "space": "HK",
    "visa.com": "US", "dpdns.org": "US", "db-link.in": "US",
}

CLOUDFLARE_PREFIXES = [
    "104.16.", "104.17.", "104.18.", "104.19.", "104.20.", "104.21.",
    "162.158.", "162.159.", "172.64.", "172.65.", "172.66.", "172.67.",
    "173.245.48.", "173.245.49.", "173.245.50.", "173.245.51.", "173.245.52.",
    "173.245.53.", "173.245.54.", "173.245.55.", "173.245.56.", "173.245.57.",
    "173.245.58.", "173.245.59.",
]

EXCLUDED_COUNTRIES = ["CN", "RU", "DE"]

# ================= 代理节点校验 =================
def validate_proxy(proxy: Dict) -> tuple[bool, str]:
    """校验代理节点是否合法，返回 (是否合法, 原因)"""
    name = proxy.get("name", "?")
    ptype = proxy.get("type", "")

    if not proxy.get("server"):
        return False, f"缺少 server"
    if not proxy.get("port"):
        return False, f"缺少 port"
    if not ptype:
        return False, f"缺少 type"

    # REALITY vless 校验
    if proxy.get("flow") == "xtls-rprx-vision" or ptype == "vless":
        reality = proxy.get("reality-opts", {})
        if proxy.get("flow") == "xtls-rprx-vision":
            if not reality:
                return False, f"REALITY vless 缺少 reality-opts"
            pk = reality.get("public-key") if isinstance(reality, dict) else None
            if not pk:
                return False, f"REALITY vless 缺少 public-key"
            sid = reality.get("short-id") if isinstance(reality, dict) else None
            if sid:
                sid = sid.strip()
                if not re.match(r'^[0-9a-fA-F]*$', sid):
                    return False, f"short-id 含非 hex 字符: {sid}"
                if len(sid) not in (0, 2, 4, 8, 16, 32):
                    return False, f"short-id 长度非法 ({len(sid)}): {sid}"

    if ptype in ("vmess", "vless") and not proxy.get("uuid"):
        return False, f"缺少 uuid"

    if ptype == "trojan" and not proxy.get("password"):
        return False, f"缺少 password"

    return True, ""


# ================= 国旗 =================
def country_code_to_flag(code: str) -> str:
    if not code or len(code) != 2:
        return "🇽🇽"
    code = code.upper()
    offset = 0x1F1E6 - ord('A')
    try:
        return chr(ord(code[0]) + offset) + chr(ord(code[1]) + offset)
    except:
        return "🇽🇽"


country_names = {
    'US': '美国', 'CA': '加拿大', 'GB': '英国', 'AU': '澳大利亚',
    'DE': '德国', 'FR': '法国', 'IT': '意大利', 'ES': '西班牙',
    'NL': '荷兰', 'SE': '瑞典', 'NO': '挪威', 'DK': '丹麦',
    'FI': '芬兰', 'CH': '瑞士', 'BE': '比利时', 'AT': '奥地利',
    'IE': '爱尔兰', 'NZ': '新西兰', 'ZA': '南非', 'IN': '印度',
    'CN': '中国', 'JP': '日本', 'KR': '韩国', 'SG': '新加坡',
    'MY': '马来西亚', 'TH': '泰国', 'VN': '越南', 'ID': '印尼',
    'PH': '菲律宾', 'BR': '巴西', 'AR': '阿根廷', 'MX': '墨西哥',
    'RU': '俄罗斯', 'TR': '土耳其', 'SA': '沙特', 'AE': '阿联酋',
    'EG': '埃及', 'IL': '以色列', 'GR': '希腊', 'PT': '葡萄牙',
    'CZ': '捷克', 'HU': '匈牙利', 'SK': '斯洛伐克', 'HK': '香港',
    'TW': '台湾', 'MO': '澳门', 'PL': '波兰', 'UA': '乌克兰',
    'RO': '罗马尼亚', 'RS': '塞尔维亚',
    'XX': '未知',
}

reader = None
if geoip2:
    try:
        reader = geoip2.database.Reader(MMDB_PATH)
        print("GeoLite2 加载成功")
    except Exception as e:
        print(f"GeoLite2 加载失败: {e}")

# ================= 提取国家 =================
def extract_country_from_name(name: str) -> str | None:
    if not name:
        return None
    name_upper = name.upper()
    flag_pattern = r'[\U0001F1E6-\U0001F1FF]{2}'
    flags = re.findall(flag_pattern, name)
    for flag in flags:
        code = (
            chr(ord(flag[0]) - 0x1F1E6 + ord('A')) +
            chr(ord(flag[1]) - 0x1F1E6 + ord('A'))
        )
        if code in country_names:
            return code
    common_codes = list(country_names.keys()) + ['UK', 'KOR', 'JPN']
    for code in common_codes:
        if re.search(r'\b' + re.escape(code) + r'\b', name_upper):
            return code
    for code, cn in country_names.items():
        if cn in name:
            return code
    match = re.search(r'\[([A-Z]{2})\]', name_upper)
    if match and match.group(1) in country_names:
        return match.group(1)
    return None


def get_country(ip: str, server: str = "", original_name: str = "") -> str:
    if original_name:
        code = extract_country_from_name(original_name)
        if code:
            print(f"原名称提取: {original_name} → {code}")
            return code
    server_lower = server.lower()
    for key, cc in DOMAIN_RULES.items():
        if key in server_lower:
            print(f"域名匹配: {server} → {cc}")
            return cc.upper()
    for prefix in CLOUDFLARE_PREFIXES:
        if ip.startswith(prefix):
            print(f"Cloudflare IP: {ip} → US")
            return "US"
    if reader:
        try:
            resp = reader.country(ip)
            cc = resp.country.iso_code
            if cc:
                print(f"GeoLite2: {ip} → {cc}")
                return cc.upper()
        except Exception as e:
            print(f"GeoLite2 失败 {ip}: {e}")
    print(f"未知: {server} / {ip}")
    return "XX"


def normalize_proxy_key(proxy: Dict) -> str:
    key_fields = ["type", "server", "port"]
    p_type = proxy.get("type", "")
    if p_type in ["vmess", "vless"]:
        key_fields.append("uuid")
    elif p_type == "trojan":
        key_fields.append("password")
    elif p_type == "ss":
        key_fields.extend(["cipher", "password"])
    values = [str(proxy.get(k, "")) for k in key_fields]
    return hashlib.md5("".join(values).encode()).hexdigest()


def fetch_config(source: str) -> Dict:
    if source.startswith(("http://", "https://")):
        r = requests.get(source, timeout=10)
        r.raise_for_status()
        return yaml.safe_load(r.text)
    else:
        with open(source, encoding="utf-8") as f:
            return yaml.safe_load(f)


# ================= 主逻辑 =================
all_proxies = []
seen_keys = set()
total_skipped = 0

for src in CONFIG_URLS:
    print(f"处理: {src}")
    try:
        config = fetch_config(src)
        for p in config.get("proxies", []):
            key = normalize_proxy_key(p)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            valid, reason = validate_proxy(p)
            if not valid:
                print(f"  [跳过] {p.get('name', '?')} — {reason}")
                total_skipped += 1
                continue

            all_proxies.append(p)
    except Exception as e:
        print(f"跳过 {src}: {e}")

print(f"\n去重后节点数：{len(all_proxies)}，跳过无效节点：{total_skipped}")

# 查询国家并分组
country_groups = defaultdict(list)

for proxy in all_proxies:
    server = proxy.get("server", "")
    original_name = proxy.get("name", "")
    if not server:
        continue
    try:
        ip = str(ip_address(server))
    except ValueError:
        try:
            ip = socket.gethostbyname(server)
        except Exception:
            print(f"解析失败: {server}")
            continue
        else:
            country = get_country(ip, server, original_name)
    else:
        country = get_country(ip, server, original_name)
    if country in EXCLUDED_COUNTRIES:
        print(f"排除节点: {original_name} ({country})")
        continue
    country_groups[country].append(proxy)

# 重命名
sorted_countries = sorted(country_groups)
new_proxies = []
name_mapping = {}
counters = {c: 1 for c in sorted_countries}

for country in sorted_countries:
    flag = country_code_to_flag(country)
    display_name = country_names.get(country, country)
    prefix = f"{flag}{display_name}" if flag else country
    for proxy in country_groups[country]:
        old = proxy["name"]
        new = f"{prefix}-{counters[country]:02d}"
        proxy["name"] = new
        name_mapping[old] = new
        new_proxies.append(proxy)
        counters[country] += 1

# 构建输出
base_config = fetch_config(CONFIG_URLS[0]) if CONFIG_URLS else {}
base_config["proxies"] = new_proxies

if "proxy-groups" in base_config:
    for group in base_config["proxy-groups"]:
        if "proxies" in group and isinstance(group["proxies"], list):
            group["proxies"] = [name_mapping.get(n, n) for n in group["proxies"] if n in name_mapping]

# ============ [!] 自定义 Dumper：给科学计数法字符串加引号 ============

class ShortIdDumper(yaml.SafeDumper):
    pass

def _str_representer(dumper, data):
    if re.match(r'^[0-9]+[eE][0-9]+$', data):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style="'")
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

ShortIdDumper.add_representer(str, _str_representer)

with open("merged-clash.yaml", "w", encoding="utf-8") as f:
    yaml.dump(base_config, f, Dumper=ShortIdDumper, allow_unicode=True, sort_keys=False)

print(f"\n完成 → merged-clash.yaml (共 {len(new_proxies)} 个有效节点)")
