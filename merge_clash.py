import requests
import yaml
import socket
from ipaddress import ip_address
from collections import defaultdict
import hashlib
from typing import List, Dict

# ================= 新依赖：geoip2 =================
try:
    import geoip2.database
except ImportError:
    geoip2 = None

# ================= 配置区 =================
CONFIG_URLS = [
    "https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/c.yaml",
    # 在这里添加更多订阅链接，例如：
    # "https://example.com/sub2.yaml",
    # "https://another.source/sub3.yaml",
]

# 数据库路径（Actions 会下载到此路径）
MMDB_PATH = "GeoLite2-Country.mmdb"

# 域名规则（优先匹配，针对你的节点）
DOMAIN_RULES = {
    "hk": "HK",      # hk 开头的域名 → 香港
    "tw": "TW",      # tw 开头的域名 → 台湾
    "us": "US",      # us 开头的域名 → 美国
    # 可继续加其他模式，例如 "jp": "JP" 等
}

reader = None
if geoip2:
    try:
        reader = geoip2.database.Reader(MMDB_PATH)
        print("GeoLite2 数据库加载成功")
    except Exception as e:
        print(f"GeoLite2 加载失败: {e}，将 fallback 到域名规则或 XX")

# ================= 国旗 & 名称 =================
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
    'US': '美国',    'CA': '加拿大',   'GB': '英国',     'AU': '澳大利亚',
    'DE': '德国',    'FR': '法国',     'IT': '意大利',   'ES': '西班牙',
    'NL': '荷兰',    'SE': '瑞典',     'NO': '挪威',     'DK': '丹麦',
    'FI': '芬兰',    'CH': '瑞士',     'BE': '比利时',   'AT': '奥地利',
    'IE': '爱尔兰',  'NZ': '新西兰',   'ZA': '南非',     'IN': '印度',
    'CN': '中国',    'JP': '日本',     'KR': '韩国',     'SG': '新加坡',
    'MY': '马来西亚','TH': '泰国',     'VN': '越南',     'ID': '印度尼西亚',
    'PH': '菲律宾',  'BR': '巴西',     'AR': '阿根廷',   'MX': '墨西哥',
    'RU': '俄罗斯',  'TR': '土耳其',   'SA': '沙特阿拉伯','AE': '阿联酋',
    'EG': '埃及',    'IL': '以色列',   'GR': '希腊',     'PT': '葡萄牙',
    'CZ': '捷克',    'HU': '匈牙利',   'SK': '斯洛伐克', 'HK': '香港',
    'TW': '台湾',    'MO': '澳门',     'PL': '波兰',     'UA': '乌克兰',
    'RO': '罗马尼亚','RS': '塞尔维亚',
    'XX': '未知',
}

# ================= 函数 =================
def get_country(ip: str, server: str = "") -> str:
    server_lower = server.lower()
    
    # 步骤1: 域名规则匹配
    for key, cc in DOMAIN_RULES.items():
        if key in server_lower:
            print(f"域名匹配: {server} → {cc}")
            return cc.upper()
    
    # 步骤2: GeoLite2 离线查询
    if reader:
        try:
            response = reader.country(ip)
            cc = response.country.iso_code
            if cc:
                print(f"GeoLite2 查询: {ip} → {cc}")
                return cc.upper()
        except Exception as e:
            print(f"GeoLite2 查询失败 for {ip}: {e}")
    
    # 最终 fallback
    print(f"未知: {server} / {ip}")
    return "XX"

def normalize_proxy_key(proxy: Dict) -> str:
    key_fields = ["type", "server", "port"]
    if proxy.get("type") in ["vmess", "vless"]:
        key_fields.append("uuid")
    elif proxy.get("type") == "trojan":
        key_fields.append("password")
    elif proxy.get("type") == "ss":
        key_fields.extend(["cipher", "password"])
    values = [str(proxy.get(k, "")) for k in key_fields]
    return hashlib.md5("".join(values).encode()).hexdigest()

def fetch_config(source) -> Dict:
    if source.startswith("http"):
        r = requests.get(source, timeout=10)
        r.raise_for_status()
        return yaml.safe_load(r.text)
    else:
        with open(source, encoding="utf-8") as f:
            return yaml.safe_load(f)

# ================= 主逻辑 =================
# 收集所有 proxies
all_proxies = []
seen_keys = set()

for src in CONFIG_URLS:
    print(f"处理: {src}")
    try:
        config = fetch_config(src)
        proxies = config.get("proxies", [])
        for p in proxies:
            key = normalize_proxy_key(p)
            if key not in seen_keys:
                seen_keys.add(key)
                all_proxies.append(p)
    except Exception as e:
        print(f"跳过 {src} ：{e}")

print(f"总共有效节点（去重后）：{len(all_proxies)}")

# 解析 IP 并查询国家
country_groups = defaultdict(list)

for proxy in all_proxies:
    server = proxy.get("server")
    if not server:
        continue

    try:
        ip = str(ip_address(server))
    except ValueError:
        try:
            ip = socket.gethostbyname(server)
        except Exception:
            print(f"域名解析失败: {server}")
            ip = None
            country = "XX"
        else:
            country = get_country(ip, server=server)
    else:
        country = get_country(ip, server=server)

    country_groups[country].append(proxy)

# 排序 & 重命名
sorted_countries = sorted(country_groups.keys())
new_proxies = []
name_mapping = {}  # old name -> new name
counters = {c: 1 for c in sorted_countries}

for country in sorted_countries:
    flag = country_code_to_flag(country)
    display_name = country_names.get(country, country)
    display_prefix = f"{flag}{display_name}" if flag else f"{country}"

    for proxy in country_groups[country]:
        old_name = proxy["name"]
        new_name = f"{display_prefix}-{counters[country]:02d}"
        proxy["name"] = new_name
        name_mapping[old_name] = new_name
        new_proxies.append(proxy)
        counters[country] += 1

# 创建基础 config
base_config = fetch_config(CONFIG_URLS[0]) if CONFIG_URLS else {}
base_config["proxies"] = new_proxies

# 更新 proxy-groups
if "proxy-groups" in base_config:
    for group in base_config["proxy-groups"]:
        if "proxies" in group and isinstance(group["proxies"], list):
            group["proxies"] = [
                name_mapping.get(name, name) for name in group["proxies"]
            ]

# 输出
with open("merged-clash.yaml", "w", encoding="utf-8") as f:
    yaml.safe_dump(base_config, f, allow_unicode=True, sort_keys=False)

print("合并完成 → merged-clash.yaml")
