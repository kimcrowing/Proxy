import requests
import yaml
import re
from datetime import datetime

# 定义要下载的 YAML 配置文件 URLs
urls = [
    "https://gitlab.com/wybgit/surge_conf/-/raw/main/myconfig/Clash/clashconfig.yaml",
    "https://raw.githubusercontent.com/chengaopan/AutoMergePublicNodes/refs/heads/master/list.yml",
    "https://raw.githubusercontent.com/anaer/Sub/refs/heads/main/clash.yaml"
]

# 动态获取 hongkongclash 仓库最新 YAML 文件
def get_latest_hongkongclash_yaml():
    year = datetime.now().year
    month = datetime.now().month
    dir_path = f"uploads/{year}/{month:02d}"
    api_url = f"https://api.github.com/repos/hongkongclash/hongkongclash.github.io/contents/{dir_path}?ref=main"
    
    response = requests.get(api_url)
    if response.status_code != 200:
        print(f"No files found in {dir_path}, trying previous month...")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
        dir_path = f"uploads/{year}/{month:02d}"
        api_url = f"https://api.github.com/repos/hongkongclash/hongkongclash.github.io/contents/{dir_path}?ref=main"
        response = requests.get(api_url)
    
    files = [f for f in response.json() if isinstance(f, dict) and f['name'].endswith('.yaml')]
    if not files:
        print("No YAML files found in the repository")
        return None
    
    latest_file = sorted(files, key=lambda x: x['name'])[-1]['name']
    raw_url = f"https://raw.githubusercontent.com/hongkongclash/hongkongclash.github.io/main/{dir_path}/{latest_file}"
    print(f"Latest hongkongclash YAML: {raw_url}")
    return raw_url

# 将 hongkongclash 的最新 YAML URL 添加到 urls 列表
latest_hongkongclash_url = get_latest_hongkongclash_yaml()
if latest_hongkongclash_url:
    urls.append(latest_hongkongclash_url)

# 用来存储所有代理服务器
all_proxies = []

# 下载并解析 YAML 文件
for url in urls:
    response = requests.get(url)
    response.raise_for_status()
    content = response.text

    if '<html>' in content:
        match = re.search(r'<pre>(.*?)</pre>', content, re.DOTALL)
        if match:
            content = match.group(1)
        else:
            print(f"No YAML data found in {url}")
            continue

    try:
        data = yaml.safe_load(content)
        if 'proxies' in data and data['proxies']:
            all_proxies.append(data['proxies'])
        else:
            print(f"No proxies found in {url}")
    except yaml.YAMLError as e:
        print(f"Error parsing YAML from {url}: {e}")
        continue

# 定义国家与国旗图标和英文缩写的映射关系
country_flags = {
    '美国': ('🇺🇸', 'US'),
    '加拿大': ('🇨🇦', 'CA'),
    '英国': ('🇬🇧', 'GB'),
    '澳大利亚': ('🇦🇺', 'AU'),
    '德国': ('🇩🇪', 'DE'),
    '法国': ('🇫🇷', 'FR'),
    '意大利': ('🇮🇹', 'IT'),
    '西班牙': ('🇪🇸', 'ES'),
    '荷兰': ('🇳🇱', 'NL'),
    '瑞典': ('🇸🇪', 'SE'),
    '挪威': ('🇳🇴', 'NO'),
    '丹麦': ('🇩🇰', 'DK'),
    '芬兰': ('🇫🇮', 'FI'),
    '瑞士': ('🇨🇭', 'CH'),
    '比利时': ('🇧🇪', 'BE'),
    '奥地利': ('🇦🇹', 'AT'),
    '爱尔兰': ('🇮🇪', 'IE'),
    '新西兰': ('🇳🇿', 'NZ'),
    '南非': ('🇿🇦', 'ZA'),
    '印度': ('🇮🇳', 'IN'),
    '中国': ('🇨🇳', 'CN'),
    '日本': ('🇯🇵', 'JP'),
    '韩国': ('🇰🇷', 'KR'),
    '新加坡': ('🇸🇬', 'SG'),
    '马来西亚': ('🇲🇾', 'MY'),
    '泰国': ('🇹🇭', 'TH'),
    '越南': ('🇻🇳', 'VN'),
    '印度尼西亚': ('🇮🇩', 'ID'),
    '菲律宾': ('🇵🇭', 'PH'),
    '巴西': ('🇧🇷', 'BR'),
    '阿根廷': ('🇦🇷', 'AR'),
    '墨西哥': ('🇲🇽', 'MX'),
    '俄罗斯': ('🇷🇺', 'RU'),
    '土耳其': ('🇹🇷', 'TR'),
    '南非共和国': ('🇿🇦', 'ZA'),
    '沙特阿拉伯': ('🇸🇦', 'SA'),
    '阿联酋': ('🇦🇪', 'AE'),
    '埃及': ('🇪🇬', 'EG'),
    '以色列': ('🇮🇱', 'IL'),
    '希腊': ('🇬🇷', 'GR'),
    '葡萄牙': ('🇵🇹', 'PT'),
    '捷克共和国': ('🇨🇿', 'CZ'),
    '匈牙利': ('🇭🇺', 'HU'),
    '斯洛伐克共和国': ('🇸🇰', 'SK'),
    '泰国王国': ('🇹🇭', 'TH'),
    '香港': ('🇭🇰', 'HK')
}

# 定义代理筛选函数，删除名称中包含 "CN" 或 "File" 的代理，以及 type 为 socks5 或 http 的节点
def valid_proxy(proxy):
    name = proxy.get('name', '')
    proxy_type = proxy.get('type', '').lower()
    banned_keywords = ['CN', 'File']
    banned_types = ['socks5', 'http']
    
    # 检查必要字段
    required_fields = {
        'ss': ['name', 'server', 'port', 'type', 'cipher', 'password'],
        'trojan': ['name', 'server', 'port', 'type', 'password'],
        'vmess': ['name', 'server', 'port', 'type', 'uuid', 'alterId', 'cipher']
    }
    
    if proxy_type not in required_fields:
        return False
    
    # 验证必要字段是否存在
    for field in required_fields[proxy_type]:
        if field not in proxy or proxy[field] is None:
            return False
    
    return (
        not any(keyword in name for keyword in banned_keywords) and
        proxy_type not in banned_types
    )

# 合并所有代理服务器，并进行筛选和去重
merged_proxies = []
name_counter = {}  # 用于记录每个国家的代理数量

for proxy_list in all_proxies:
    for proxy in proxy_list:
        if not valid_proxy(proxy):
            continue

        name = proxy.get('name', '')
        matched = False

        # 检查名称中是否包含国家名称或英文缩写
        for country, (flag, code) in country_flags.items():
            if country in name or code in name:
                matched = True
                if country not in name_counter:
                    name_counter[country] = 1
                else:
                    name_counter[country] += 1
                new_name = f"{flag} {code} {str(name_counter[country]).zfill(3)}"
                
                # 创建新代理对象，清理多余字段
                cleaned_proxy = {
                    'name': new_name,
                    'server': proxy['server'],
                    'port': proxy['port'],
                    'type': proxy['type']
                }
                
                # 根据类型添加必要字段
                if proxy['type'] == 'ss':
                    cleaned_proxy.update({
                        'cipher': proxy['cipher'],
                        'password': proxy['password'],
                        'udp': proxy.get('udp', True)
                    })
                elif proxy['type'] == 'trojan':
                    cleaned_proxy.update({
                        'password': proxy['password'],
                        'skip-cert-verify': proxy.get('skip-cert-verify', False),
                        'sni': proxy.get('sni', proxy['server']),
                        'udp': proxy.get('udp', True)
                    })
                elif proxy['type'] == 'vmess':
                    cleaned_proxy.update({
                        'uuid': proxy['uuid'],
                        'alterId': proxy['alterId'],
                        'cipher': proxy.get('cipher', 'auto'),
                        'tls': proxy.get('tls', False),
                        'skip-cert-verify': proxy.get('skip-cert-verify', False),
                        'network': proxy.get('network', 'ws'),
                        'client-fingerprint': proxy.get('client-fingerprint', 'chrome')
                    })
                
                break

        if matched and cleaned_proxy not in merged_proxies:
            merged_proxies.append(cleaned_proxy)

# 将合并后的代理保存为新的 YAML 文件
with open('combined_proxies.yaml', 'w', encoding='utf-8') as outfile:
    yaml.dump({'proxies': merged_proxies}, outfile, default_flow_style=False, allow_unicode=True)

print("Proxy configurations have been successfully processed.")
