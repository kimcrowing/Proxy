import requests
import yaml
import re
from datetime import datetime
import collections
import time
import json
import os

# 定义要下载的 YAML 配置文件 URLs
urls = [
    "https://gitlab.com/wybgit/surge_conf/-/raw/main/myconfig/Clash/clashconfig.yaml",
    "https://raw.githubusercontent.com/chengaopan/AutoMergePublicNodes/refs/heads/master/list.yml",
    "https://raw.githubusercontent.com/anaer/Sub/refs/heads/main/clash.yaml"
]

# 动态获取 hongkongclash 仓库最新日期的所有 YAML 文件
def get_latest_hongkongclash_yaml():
    year = datetime.now().year
    month = datetime.now().month
    dir_path = f"uploads/{year}/{month:02d}"
    api_url = f"https://api.github.com/repos/hongkongclash/hongkongclash.github.io/contents/{dir_path}?ref=main"
    
    try:
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
            response.raise_for_status()
        
        files = [f for f in response.json() if isinstance(f, dict) and f['name'].endswith('.yaml')]
        if not files:
            print("No YAML files found in the repository")
            return []
        
        # 提取文件名中的日期（格式：X-YYYYMMDD.yaml）
        date_pattern = re.compile(r'^\d+-(\d{8})\.yaml$')
        dates = []
        for f in files:
            match = date_pattern.match(f['name'])
            if match:
                dates.append(match.group(1))
        
        if not dates:
            print("No valid date-format YAML files found")
            return []
        
        # 获取最新日期
        latest_date = max(dates)
        # 收集该日期的所有 YAML 文件
        latest_files = [f for f in files if f['name'].endswith(f'{latest_date}.yaml')]
        latest_files = sorted(latest_files, key=lambda x: x['name'])
        raw_urls = [f"https://raw.githubusercontent.com/hongkongclash/hongkongclash.github.io/main/{dir_path}/{f['name']}" for f in latest_files]
        
        print(f"Latest hongkongclash YAML files for {latest_date}:")
        for i, url in enumerate(raw_urls, 1):
            print(f"  File {i}: {url}")
        return raw_urls
    except requests.RequestException as e:
        print(f"Error fetching hongkongclash files: {e}")
        return []

# 获取并打印所有订阅链接
print("=== Acquired Clash Subscription URLs ===")
for i, url in enumerate(urls, 1):
    print(f"URL {i}: {url}")
latest_hongkongclash_urls = get_latest_hongkongclash_yaml()
if latest_hongkongclash_urls:
    urls.extend(latest_hongkongclash_urls)
    for i, url in enumerate(latest_hongkongclash_urls, len(urls) - len(latest_hongkongclash_urls) + 1):
        print(f"URL {i}: {url}")
print(f"Total URLs: {len(urls)}")
print("======================================")

# 输出所有节点文件链接到 node_urls.txt
with open('node_urls.txt', 'w', encoding='utf-8') as urlfile:
    for url in urls:
        urlfile.write(url + '\n')
print(f"Node URLs saved to node_urls.txt: {len(urls)} links")

# 定义代理筛选函数
def valid_proxy(proxy):
    name = proxy.get('name', '')
    proxy_type = proxy.get('type', '').lower()
    banned_keywords = ['File']
    banned_types = ['http']
    
    required_fields = {
        'ss': ['server', 'port', 'cipher', 'password'],
        'trojan': ['server', 'port', 'password'],
        'vmess': ['server', 'port', 'uuid', 'alterId', 'cipher'],
        'hysteria2': ['server', 'port', 'password'],  # 支持 Hysteria2
        'vless': ['server', 'port', 'uuid']  # 支持 Vless (简化字段)
    }
    
    if proxy_type not in required_fields:
        print(f"Unsupported proxy type: {proxy_type}")
        return False
    for field in required_fields[proxy_type]:
        if field not in proxy or proxy[field] is None:
            return False
    
    return (
        not any(keyword in name for keyword in banned_keywords) and
        proxy_type not in banned_types
    )

# 收集所有代理服务器
all_proxies = []
for url in urls:
    try:
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

        data = yaml.safe_load(content)
        if 'proxies' in data and data['proxies']:
            for proxy in data['proxies']:
                if valid_proxy(proxy):
                    all_proxies.append(proxy)
                else:
                    print(f"Invalid proxy format: {proxy.get('name', 'Unknown')} at {proxy.get('server', 'Unknown')}:{proxy.get('port', 'Unknown')}")
        else:
            print(f"No proxies found in {url}")
    except (requests.RequestException, yaml.YAMLError) as e:
        print(f"Error processing {url}: {e}")
        continue

print(f"Total Proxies Collected (before LiteSpeedTest): {len(all_proxies)}")

# 确保生成空的 valid_proxies.yaml
with open('valid_proxies.yaml', 'w', encoding='utf-8') as outfile:
    yaml.dump({'proxies': []}, outfile, default_flow_style=False, allow_unicode=True, sort_keys=False)

# 处理 LiteSpeedTest 结果
if os.path.exists('lite_valid_proxies.json'):
    print("\n=== Processing LiteSpeedTest Valid Proxies ===")
    try:
        with open('lite_valid_proxies.json', 'r') as f:
            all_valid_proxies = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding lite_valid_proxies.json: {e}")
        all_valid_proxies = []
    
    print("\n=== Valid Proxies from LiteSpeedTest ===")
    for i, proxy in enumerate(all_valid_proxies, 1):
        print(f"Proxy {i}:")
        print(f"  Name: {proxy.get('name', 'Unknown')}")
        print(f"  Type: {proxy.get('type', 'Unknown')}")
        print(f"  Server: {proxy.get('server', 'Unknown')}")
        print(f"  Port: {proxy.get('port', 'Unknown')}")
        print(f"  Additional Fields: {', '.join(f'{k}={v}' for k, v in proxy.items() if k not in ['name', 'type', 'server', 'port'])}")
    print(f"Total Valid Proxies: {len(all_valid_proxies)}")
    print("======================================")

    # 国家与国旗映射 (简化版，完整列表如之前)
    country_flags = {
        '美国': ('🇺🇸', 'US'), '加拿大': ('🇨🇦', 'CA'), '英国': ('🇬🇧', 'GB'), '澳大利亚': ('🇦🇺', 'AU'),
        '德国': ('🇩🇪', 'DE'), '法国': ('🇫🇷', 'FR'), '意大利': ('🇮🇹', 'IT'), '西班牙': ('🇪🇸', 'ES'),
        '荷兰': ('🇳🇱', 'NL'), '瑞典': ('🇸🇪', 'SE'), '挪威': ('🇳🇴', 'NO'), '丹麦': ('🇩🇰', 'DK'),
        '芬兰': ('🇫🇮', 'FI'), '瑞士': ('🇨🇭', 'CH'), '比利时': ('🇧🇪', 'BE'), '奥地利': ('🇦🇹', 'AT'),
        '爱尔兰': ('🇮🇪', 'IE'), '新西兰': ('🇳🇿', 'NZ'), '南非': ('🇿🇦', 'ZA'), '印度': ('🇮🇳', 'IN'),
        '中国': ('🇨🇳', 'CN'), '中国大陆': ('🇨🇳', 'CN'), '日本': ('🇯🇵', 'JP'), '韩国': ('🇰🇷', 'KR'),
        '新加坡': ('🇸🇬', 'SG'), '马来西亚': ('🇲🇾', 'MY'), '泰国': ('🇹🇭', 'TH'), '越南': ('🇻🇳', 'VN'),
        '印度尼西亚': ('🇮🇩', 'ID'), '菲律宾': ('🇵🇭', 'PH'), '巴西': ('🇧🇷', 'BR'), '阿根廷': ('🇦🇷', 'AR'),
        '墨西哥': ('🇲🇽', 'MX'), '俄罗斯': ('🇷🇺', 'RU'), '土耳其': ('🇹🇷', 'TR'), '沙特阿拉伯': ('🇸🇦', 'SA'),
        '阿联酋': ('🇦🇪', 'AE'), '埃及': ('🇪🇬', 'EG'), '以色列': ('🇮🇱', 'IL'), '希腊': ('🇬🇷', 'GR'),
        '葡萄牙': ('🇵🇹', 'PT'), '捷克共和国': ('🇨🇿', 'CZ'), '匈牙利': ('🇭🇺', 'HU'), '斯洛伐克共和国': ('🇸🇰', 'SK'),
        '香港': ('🇭🇰', 'HK'), '台湾': ('🇹🇼', 'TW'), '澳门': ('🇲🇴', 'MO'), '波兰': ('🇵🇱', 'PL'),
        '乌克兰': ('🇺🇦', 'UA'), '罗马尼亚': ('🇷🇴', 'RO'), '塞尔维亚': ('🇷🇸', 'RS')
    }
    unknown_country = ('❓', 'UNK')

    ip_cache = {}

    def get_country_from_ip(servers):
        result = {}
        to_query = [server for server in servers if server not in ip_cache]
        if not to_query:
            return {server: ip_cache[server] for server in servers}

        for i in range(0, len(to_query), 100):
            batch = to_query[i:i+100]
            batch_query = [{"query": server} for server in batch]
            for attempt in range(3):
                try:
                    response = requests.post("http://ip-api.com/batch", json=batch_query)
                    response.raise_for_status()
                    data = response.json()
                    for query, server in zip(data, batch):
                        if query.get('status') == 'success':
                            country_code = query.get('countryCode')
                            for country, (flag, code) in country_flags.items():
                                if code == country_code:
                                    ip_cache[server] = (flag, country)
                                    result[server] = (flag, country)
                                    break
                            else:
                                ip_cache[server] = (unknown_country[0], '未知')
                                result[server] = (unknown_country[0], '未知')
                        else:
                            print(f"Query failed for {server}: {query.get('message', 'Unknown error')}")
                            ip_cache[server] = (unknown_country[0], '未知')
                            result[server] = (unknown_country[0], '未知')
                    break
                except requests.RequestException as e:
                    print(f"Batch query attempt {attempt+1}/3 failed: {e}")
                    time.sleep(2)
                    if attempt == 2:
                        for server in batch:
                            ip_cache[server] = (unknown_country[0], '未知')
                            result[server] = (unknown_country[0], '未知')
        
        for server in servers:
            if server not in result:
                result[server] = ip_cache[server]
        return result

    # 合并有效代理
    merged_proxies = []
    name_counter = {}
    seen_proxies = set()

    servers_to_query = set()
    proxy_info = []
    for proxy in all_valid_proxies:
        name = proxy.get('name', '')
        server = proxy.get('server', '')
        matched = False
        flag = unknown_country[0]
        country_key = '未知'
        for country, (f, code) in country_flags.items():
            if country in name or code in name:
                matched = True
                flag = f
                country_key = country
                break
        if not matched:
            servers_to_query.add(server)
        proxy_info.append({
            'proxy': proxy,
            'flag': flag,
            'country_key': country_key,
            'matched': matched,
            'server': server
        })

    if servers_to_query:
        server_countries = get_country_from_ip(list(servers_to_query))
        for info in proxy_info:
            if not info['matched']:
                flag, country_key = server_countries.get(info['server'], (unknown_country[0], '未知'))
                info['flag'] = flag
                info['country_key'] = country_key

    for info in proxy_info:
        proxy = info['proxy']
        flag = info['flag']
        country_key = info['country_key']
        if country_key not in name_counter:
            name_counter[country_key] = 1
        else:
            name_counter[country_key] += 1
        new_name = f"{flag} {str(name_counter[country_key]).zfill(3)}"
        
        ordered_proxy = collections.OrderedDict()
        ordered_proxy['name'] = new_name
        ordered_proxy['type'] = proxy['type']
        ordered_proxy['server'] = proxy['server']
        ordered_proxy['port'] = proxy['port']
        
        additional_fields = {}
        if proxy['type'] == 'ss':
            if 'cipher' in proxy:
                additional_fields['cipher'] = proxy['cipher']
            if 'password' in proxy:
                additional_fields['password'] = proxy['password']
        elif proxy['type'] == 'trojan':
            if 'password' in proxy:
                additional_fields['password'] = proxy['password']
            if 'sni' in proxy:
                additional_fields['sni'] = proxy['sni']
            if 'skip-cert-verify' in proxy:
                additional_fields['skip-cert-verify'] = proxy['skip-cert-verify']
        elif proxy['type'] == 'vmess':
            if 'uuid' in proxy:
                additional_fields['uuid'] = proxy['uuid']
            if 'alterId' in proxy:
                additional_fields['alterId'] = proxy['alterId']
            if 'cipher' in proxy:
                additional_fields['cipher'] = proxy['cipher']
            if 'tls' in proxy:
                additional_fields['tls'] = proxy['tls']
            if 'network' in proxy:
                additional_fields['network'] = proxy['network']
            if 'client-fingerprint' in proxy:
                additional_fields['client-fingerprint'] = proxy['client-fingerprint']
            if 'skip-cert-verify' in proxy:
                additional_fields['skip-cert-verify'] = proxy['skip-cert-verify']
        elif proxy['type'] == 'hysteria2':
            if 'password' in proxy:
                additional_fields['password'] = proxy['password']
        elif proxy['type'] == 'vless':
            if 'uuid' in proxy:
                additional_fields['uuid'] = proxy['uuid']
        
        sorted_additional = sorted(additional_fields.items())
        for key, value in sorted_additional:
            ordered_proxy[key] = value
        
        proxy_key = (ordered_proxy['server'], ordered_proxy['port'], ordered_proxy['type'])
        if proxy_key not in seen_proxies:
            seen_proxies.add(proxy_key)
            merged_proxies.append(dict(ordered_proxy))

    with open('valid_proxies.yaml', 'w', encoding='utf-8') as outfile:
        yaml.dump({'proxies': merged_proxies}, outfile, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"Valid proxy configurations have been successfully processed and saved to valid_proxies.yaml ({len(merged_proxies)} proxies).")
else:
    print("No lite_valid_proxies.json found; generating empty valid_proxies.yaml.")
