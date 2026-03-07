import requests
import yaml
import socket
from ipaddress import ip_address
from collections import defaultdict
import hashlib
import sys
from typing import List, Dict

# ================= 配置区 =================
CONFIG_URLS = [
    "https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/c.yaml",
    # 在这里添加更多订阅链接，例如：
    # "https://example.com/sub2.yaml",
    # "https://another.source/sub3.yaml",
]

# 如果你想用本地文件（Actions checkout 后），可以用文件路径代替 URL
# CONFIG_FILES = ["config1.yaml", "config2.yaml"]

GEO_API = "https://ipinfo.io/{ip}/country"  # 返回国家代码如 "HK", "US"；备用：https://ipapi.co/{ip}/country

TIMEOUT = 6
# ================= 配置区结束 =================

def country_code_to_flag(code: str) -> str:
    """将 ISO 3166-1 alpha-2 代码转为旗帜 emoji，例如 'US' → '🇺🇸'"""
    if not code or len(code) != 2:
        return ""
    code = code.upper()
    # 区域指示符字母 A-Z 的 Unicode 起点是 U+1F1E6 (🇦)
    offset = 0x1F1E6 - ord('A')
    try:
        return chr(ord(code[0]) + offset) + chr(ord(code[1]) + offset)
    except:
        return ""

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
    # 可继续补充，例如：
    'XX': '未知',
}

def get_country(ip: str) -> str:
    try:
        resp = requests.get(GEO_API.format(ip=ip), timeout=TIMEOUT)
        if resp.status_code == 200:
            cc = resp.text.strip()
            return cc if cc and len(cc) == 2 else "XX"
    except:
        pass
    return "XX"

def normalize_proxy_key(proxy: Dict) -> str:
    """生成节点的唯一标识，用于去重"""
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

# 收集所有 proxies
all_proxies = []
seen_keys = set()

for src in CONFIG_URLS:  # 或 CONFIG_FILES
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
        ip = ip_address(server)
    except ValueError:
        try:
            ip = socket.gethostbyname(server)
        except Exception:
            print(f"域名解析失败: {server}")
            country = "XX"
            ip = None

    if 'ip' in locals() and ip:
        country = get_country(str(ip))
    else:
        country = "XX"

    country_groups[country].append(proxy)

# 排序 & 重命名
sorted_countries = sorted(country_groups.keys())
new_proxies = []
name_mapping = {}  # old name -> new name
counters = {c: 1 for c in sorted_countries}

for country in sorted_countries:
    flag = country_code_to_flag(country)
    display_name = country_names.get(country, country)  # 找不到就用代码本身
    display_prefix = f"{flag}{display_name}" if flag else f"{country}"

    for proxy in country_groups[country]:
        old_name = proxy["name"]
        # 编号用两位数，方便排序：01、02...
        new_name = f"{display_prefix}-{counters[country]:02d}"
        proxy["name"] = new_name
        name_mapping[old_name] = new_name
        new_proxies.append(proxy)
        counters[country] += 1

# 创建基础 config（以第一个文件为基础，或新建）
base_config = fetch_config(CONFIG_URLS[0]) if CONFIG_URLS else {}
base_config["proxies"] = new_proxies

# 更新 proxy-groups 中的 proxies 名称
if "proxy-groups" in base_config:
    for group in base_config["proxy-groups"]:
        if "proxies" in group and isinstance(group["proxies"], list):
            group["proxies"] = [
                name_mapping.get(name, name) for name in group["proxies"]
            ]

# 可选：清空或重置部分字段（如 rules、rule-providers 如果需要统一管理）
# base_config.pop("rules", None)
# base_config.pop("rule-providers", None)

# 输出
with open("merged-clash.yaml", "w", encoding="utf-8") as f:
    yaml.safe_dump(base_config, f, allow_unicode=True, sort_keys=False)

print("合并完成 → merged-clash.yaml")
