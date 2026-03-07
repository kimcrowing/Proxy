import hashlib
import socket
from collections import defaultdict
from ipaddress import ip_address
from typing import Dict

import requests
import yaml

# ================= 第三方依赖（geoip2） =================
try:
    import geoip2.database
except ImportError:
    geoip2 = None

# ================= 配置区 =================
CONFIG_URLS = [
    "https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/c.yaml",
    # 可在此添加更多订阅链接
    # "https://example.com/sub2.yaml",
    # "https://another.source/sub3.yaml",
]

MMDB_PATH = "GeoLite2-Country.mmdb"

# 域名规则（优先匹配，根据常见节点特征设置）
DOMAIN_RULES = {
    # 明确地区前缀
    "hk": "HK",
    "tw": "TW",
    "us": "US",
    "sg": "SG",
    "jp": "JP",
    "kr": "KR",

    # 示例中出现的伪装/CDN域名（经解析多为香港或亚洲节点）
    "868863.xyz": "HK",
    "bestcdn": "HK",
    "netvora.space": "HK",
    "206352.xyz": "HK",
    "206353.xyz": "HK",
    "206355.xyz": "HK",

    # 常见CDN/伪装关键词（可根据实际效果继续调整）
    "cloudflare": "US",
    "akamai": "US",
    "fastly": "US",
    "cdn": "HK",
    "v2ray": "CN",
    "proxy": "CN",
    "speed": "HK",
    "xyz": "HK",
    "space": "HK",
}

# 国旗 emoji 生成
def country_code_to_flag(code: str) -> str:
    if not code or len(code) != 2:
        return "🇽🇽"
    code = code.upper()
    offset = 0x1F1E6 - ord('A')
    try:
        return chr(ord(code[0]) + offset) + chr(ord(code[1]) + offset)
    except Exception:
        return "🇽🇽"

# 中文国家/地区名称（已扩展常见节点地区）
country_names = {
    'US': '美国',    'CA': '加拿大',   'GB': '英国',     'AU': '澳大利亚',
    'DE': '德国',    'FR': '法国',     'IT': '意大利',   'ES': '西班牙',
    'NL': '荷兰',    'SE': '瑞典',     'NO': '挪威',     'DK': '丹麦',
    'FI': '芬兰',    'CH': '瑞士',     'BE': '比利时',   'AT': '奥地利',
    'IE': '爱尔兰',  'NZ': '新西兰',   'ZA': '南非',     'IN': '印度',
    'CN': '中国',    'JP': '日本',     'KR': '韩国',     'SG': '新加坡',
    'MY': '马来西亚','TH': '泰国',     'VN': '越南',     'ID': '印尼',
    'PH': '菲律宾',  'BR': '巴西',     'AR': '阿根廷',   'MX': '墨西哥',
    'RU': '俄罗斯',  'TR': '土耳其',   'SA': '沙特',     'AE': '阿联酋',
    'EG': '埃及',    'IL': '以色列',   'GR': '希腊',     'PT': '葡萄牙',
    'CZ': '捷克',    'HU': '匈牙利',   'SK': '斯洛伐克', 'HK': '香港',
    'TW': '台湾',    'MO': '澳门',     'PL': '波兰',     'UA': '乌克兰',
    'RO': '罗马尼亚','RS': '塞尔维亚',
    'BG': '保加利亚','HR': '克罗地亚', 'SI': '斯洛文尼亚','LT': '立陶宛',
    'LV': '拉脱维亚','EE': '爱沙尼亚','IS': '冰岛',     'LU': '卢森堡',
    'CL': '智利',    'CO': '哥伦比亚','PE': '秘鲁',
    'PK': '巴基斯坦','BD': '孟加拉国','KZ': '哈萨克斯坦',
    'QA': '卡塔尔',  'KW': '科威特',  'OM': '阿曼',     'BH': '巴林',
    'JO': '约旦',
    'KE': '肯尼亚',  'NG': '尼日利亚','MA': '摩洛哥',
    'XX': '未知',
}

# ================= 初始化 GeoLite2 数据库 =================
reader = None
if geoip2:
    try:
        reader = geoip2.database.Reader(MMDB_PATH)
        print("GeoLite2 数据库加载成功")
    except Exception as e:
        print(f"GeoLite2 加载失败: {e}，将仅依赖域名规则")

# ================= 核心函数 =================
def get_country(ip: str, server: str = "") -> str:
    """获取国家代码：优先域名规则 → GeoLite2 → XX"""
    server_lower = server.lower()

    # 优先：域名规则匹配
    for key, cc in DOMAIN_RULES.items():
        if key in server_lower:
            print(f"域名匹配: {server} → {cc}")
            return cc.upper()

    # 次选：GeoLite2 查询
    if reader:
        try:
            response = reader.country(ip)
            cc = response.country.iso_code
            if cc:
                print(f"GeoLite2 查询: {ip} → {cc}")
                return cc.upper()
        except Exception as e:
            print(f"GeoLite2 查询失败 for {ip}: {e}")

    # 兜底
    print(f"未知: {server} / {ip}")
    return "XX"


def normalize_proxy_key(proxy: Dict) -> str:
    """生成代理唯一标识，用于去重"""
    key_fields = ["type", "server", "port"]
    p_type = proxy.get("type")

    if p_type in ["vmess", "vless"]:
        key_fields.append("uuid")
    elif p_type == "trojan":
        key_fields.append("password")
    elif p_type == "ss":
        key_fields.extend(["cipher", "password"])

    values = [str(proxy.get(k, "")) for k in key_fields]
    return hashlib.md5("".join(values).encode()).hexdigest()


def fetch_config(source: str) -> Dict:
    """从 URL 或本地文件读取 Clash 配置"""
    if source.startswith(("http://", "https://")):
        r = requests.get(source, timeout=10)
        r.raise_for_status()
        return yaml.safe_load(r.text)
    else:
        with open(source, encoding="utf-8") as f:
            return yaml.safe_load(f)


# ================= 主逻辑 =================
# 1. 收集并去重所有 proxies
all_proxies = []
seen_keys = set()

for src in CONFIG_URLS:
    print(f"处理订阅: {src}")
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

print(f"去重后有效节点总数：{len(all_proxies)}")

# 2. 查询国家并分组
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
            country = "XX"
        else:
            country = get_country(ip, server)
    else:
        country = get_country(ip, server)

    country_groups[country].append(proxy)

# 3. 按国家排序 & 重命名
sorted_countries = sorted(country_groups.keys())
new_proxies = []
name_mapping = {}
counters = {c: 1 for c in sorted_countries}

for country in sorted_countries:
    flag = country_code_to_flag(country)
    display_name = country_names.get(country, country)
    display_prefix = f"{flag}{display_name}" if flag else country

    for proxy in country_groups[country]:
        old_name = proxy["name"]
        new_name = f"{display_prefix}-{counters[country]:02d}"
        proxy["name"] = new_name
        name_mapping[old_name] = new_name
        new_proxies.append(proxy)
        counters[country] += 1

# 4. 构建新配置
base_config = fetch_config(CONFIG_URLS[0]) if CONFIG_URLS else {}
base_config["proxies"] = new_proxies

# 更新 proxy-groups 中的节点名称引用
if "proxy-groups" in base_config:
    for group in base_config["proxy-groups"]:
        if "proxies" in group and isinstance(group["proxies"], list):
            group["proxies"] = [
                name_mapping.get(name, name) for name in group["proxies"]
            ]

# 5. 保存结果
with open("merged-clash.yaml", "w", encoding="utf-8") as f:
    yaml.safe_dump(base_config, f, allow_unicode=True, sort_keys=False)

print("合并完成 → 已保存为 merged-clash.yaml")
