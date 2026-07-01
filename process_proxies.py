import requests
import yaml
import re
from datetime import datetime
import collections  # 用于 OrderedDict 以控制字段顺序
import time

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
            all_proxies.append(data['proxies'])
        else:
            print(f"No proxies found in {url}")
    except (requests.RequestException, yaml.YAMLError) as e:
        print(f"Error processing {url}: {e}")
        continue

# 定义国家与国旗图标和英文缩写的映射关系（大幅扩展）
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
    '中国大陆': ('🇨🇳', 'CN'),  # 新增别名
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
    '南非共和国': ('🇿🇦', 'ZA'),  # 别名
    '沙特阿拉伯': ('🇸🇦', 'SA'),
    '阿联酋': ('🇦🇪', 'AE'),
    '埃及': ('🇪🇬', 'EG'),
    '以色列': ('🇮🇱', 'IL'),
    '希腊': ('🇬🇷', 'GR'),
    '葡萄牙': ('🇵🇹', 'PT'),
    '捷克共和国': ('🇨🇿', 'CZ'),
    '匈牙利': ('🇭🇺', 'HU'),
    '斯洛伐克共和国': ('🇸🇰', 'SK'),
    '泰国王国': ('🇹🇭', 'TH'),  # 别名
    '香港': ('🇭🇰', 'HK'),
    '台湾': ('🇹🇼', 'TW'),
    '澳门': ('🇲🇴', 'MO'),
    '波兰': ('🇵🇱', 'PL'),
    '乌克兰': ('🇺🇦', 'UA'),
    '罗马尼亚': ('🇷🇴', 'RO'),
    '塞尔维亚': ('🇷🇸', 'RS'),
    '瑞典王国': ('🇸🇪', 'SE'),  # 别名
    '挪威王国': ('🇳🇴', 'NO'),  # 别名
    '丹麦王国': ('🇩🇰', 'DK'),  # 别名
    '阿尔巴尼亚': ('🇦🇱', 'AL'),  # 新增
    '阿尔及利亚': ('🇩🇿', 'DZ'),  # 新增
    '安哥拉': ('🇦🇴', 'AO'),  # 新增
    '亚美尼亚': ('🇦🇲', 'AM'),  # 新增
    '奥地利共和国': ('🇦🇹', 'AT'),  # 别名
    '阿塞拜疆': ('🇦🇿', 'AZ'),  # 新增
    '巴林': ('🇧🇭', 'BH'),  # 新增
    '孟加拉国': ('🇧🇩', 'BD'),  # 新增
    '白俄罗斯': ('🇧🇾', 'BY'),  # 新增
    '玻利维亚': ('🇧🇴', 'BO'),  # 新增
    '波斯尼亚和黑塞哥维那': ('🇧🇦', 'BA'),  # 新增
    '保加利亚': ('🇧🇬', 'BG'),  # 新增
    '智利': ('🇨🇱', 'CL'),  # 新增
    '哥伦比亚': ('🇨🇴', 'CO'),  # 新增
    '哥斯达黎加': ('🇨🇷', 'CR'),  # 新增
    '克罗地亚': ('🇭🇷', 'HR'),  # 新增
    '塞浦路斯': ('🇨🇾', 'CY'),  # 新增
    '厄瓜多尔': ('🇪🇨', 'EC'),  # 新增
    '爱沙尼亚': ('🇪🇪', 'EE'),  # 新增
    '埃塞俄比亚': ('🇪🇹', 'ET'),  # 新增
    '格鲁吉亚': ('🇬🇪', 'GE'),  # 新增
    '加纳': ('🇬🇭', 'GH'),  # 新增
    '冰岛': ('🇮🇸', 'IS'),  # 新增
    '伊拉克': ('🇮🇶', 'IQ'),  # 新增
    '约旦': ('🇯🇴', 'JO'),  # 新增
    '哈萨克斯坦': ('🇰🇿', 'KZ'),  # 新增
    '肯尼亚': ('🇰🇪', 'KE'),  # 新增
    '科威特': ('🇰🇼', 'KW'),  # 新增
    '拉脱维亚': ('🇱🇻', 'LV'),  # 新增
    '黎巴嫩': ('🇱🇧', 'LB'),  # 新增
    '立陶宛': ('🇱🇹', 'LT'),  # 新增
    '卢森堡': ('🇱🇺', 'LU'),  # 新增
    '马其顿': ('🇲🇰', 'MK'),  # 新增
    '马耳他': ('🇲🇹', 'MT'),  # 新增
    '摩洛哥': ('🇲🇦', 'MA'),  # 新增
    '尼泊尔': ('🇳🇵', 'NP'),  # 新增
    '尼日利亚': ('🇳🇬', 'NG'),  # 新增
    '巴基斯坦': ('🇵🇰', 'PK'),  # 新增
    '巴拿马': ('🇵🇦', 'PA'),  # 新增
    '秘鲁': ('🇵🇪', 'PE'),  # 新增
    '卡塔尔': ('🇶🇦', 'QA'),  # 新增
    '斯洛文尼亚': ('🇸🇮', 'SI'),  # 新增
    '斯里兰卡': ('🇱🇰', 'LK'),  # 新增
    '突尼斯': ('🇹🇳', 'TN'),  # 新增
    '乌拉圭': ('🇺🇾', 'UY'),  # 新增
    '委内瑞拉': ('🇻🇪', 'VE'),  # 新增
}
unknown_country = ('❓', 'UNK')  # 用于不匹配的代理

# 缓存 IP/域名查询结果
ip_cache = {}

# 查询 IP 地址或域名的国家（支持批量查询）
def get_country_from_ip(servers):
    result = {}
    to_query = [server for server in servers if server not in ip_cache]
    
    if not to_query:
        return {server: ip_cache[server] for server in servers}

    for i in range(0, len(to_query), 100):  # ip-api.com 批量限制 100 个
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

# 定义代理筛选函数，删除名称中包含 "CN" 或 "File" 的代理，以及 type 为 socks5 或 http 的节点
def valid_proxy(proxy):
    name = proxy.get('name', '')
    proxy_type = proxy.get('type', '').lower()
    banned_keywords = ['File']
    banned_types = ['http']
    
    required_fields = {
        'ss': ['server', 'port', 'cipher', 'password'],
        'trojan': ['server', 'port', 'password'],
        'vmess': ['server', 'port', 'uuid', 'alterId', 'cipher']
    }
    
    if proxy_type not in required_fields:
        return False
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
seen_proxies = set()  # 用于去重（基于 server, port, type）

# 收集所有需要查询的 server（仅对 name 未匹配的）
servers_to_query = set()
proxy_info = []  # 存储有效代理及其匹配状态

for proxy_list in all_proxies:
    for proxy in proxy_list:
        if not valid_proxy(proxy):
            continue
        
        name = proxy.get('name', '')
        server = proxy.get('server', '')
        matched = False
        flag = unknown_country[0]
        country_key = '未知'
        
        # 优先基于 name 匹配国家
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

# 如果有未匹配的，批量查询
if servers_to_query:
    server_countries = get_country_from_ip(list(servers_to_query))
    for info in proxy_info:
        if not info['matched']:
            flag, country_key = server_countries.get(info['server'], (unknown_country[0], '未知'))
            info['flag'] = flag
            info['country_key'] = country_key

# 现在构建 merged_proxies
for info in proxy_info:
    proxy = info['proxy']
    flag = info['flag']
    country_key = info['country_key']
    
    if country_key not in name_counter:
        name_counter[country_key] = 1
    else:
        name_counter[country_key] += 1
    new_name = f"{flag} {str(name_counter[country_key]).zfill(3)}"
    
    # 创建统一格式的代理对象
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
    
    sorted_additional = sorted(additional_fields.items())
    for key, value in sorted_additional:
        ordered_proxy[key] = value
    
    proxy_key = (ordered_proxy['server'], ordered_proxy['port'], ordered_proxy['type'])
    if proxy_key not in seen_proxies:
        seen_proxies.add(proxy_key)
        merged_proxies.append(dict(ordered_proxy))

# 将合并后的代理保存为新的 YAML 文件
with open('combined_proxies.yaml', 'w', encoding='utf-8') as outfile:
    yaml.dump({'proxies': merged_proxies}, outfile, default_flow_style=False, allow_unicode=True, sort_keys=False)

print("Proxy configurations have been successfully processed and unified for mihomo.")
