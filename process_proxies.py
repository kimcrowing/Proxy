import requests
import yaml
import re

# 定义要下载的 YAML 配置文件 URLs
urls = [
    "https://gitlab.com/wybgit/surge_conf/-/raw/main/myconfig/Clash/clashconfig.yaml",
    "https://github.com/aiboboxx/clashfree/blob/main/clash.yml",
    "https://raw.githubusercontent.com/anaer/Sub/refs/heads/main/clash.yaml"
]

# 用来存储所有代理服务器
all_proxies = []

# 下载并解析 YAML 文件
for url in urls:
    response = requests.get(url)
    response.raise_for_status()  # 请求失败则抛出异常
    content = response.text

    # 如果页面包含 HTML 标签，则尝试从 <pre> 标签中提取 YAML 数据
    if '<html>' in content:
        match = re.search(r'<pre>(.*?)</pre>', content, re.DOTALL)
        if match:
            content = match.group(1)
        else:
            print(f"No YAML data found in {url}")
            continue

    try:
        data = yaml.safe_load(content)
        if 'proxies' in data:
            all_proxies.append(data['proxies'])
    except yaml.YAMLError as e:
        print(f"Error parsing YAML from {url}: {e}")
        continue

# 定义国家与国旗图标的映射关系
country_flags = {
    'United States': '🇺🇸',
    'Canada': '🇨🇦',
    'United Kingdom': '🇬🇧',
    'Australia': '🇦🇺',
    'Germany': '🇩🇪',
    'France': '🇫🇷',
    'Italy': '🇮🇹',
    'Spain': '🇪🇸',
    'Japan': '🇯🇵',
    'South Korea': '🇰🇷',
    'India': '🇮🇳',
    'Brazil': '🇧🇷',
    'Mexico': '🇲🇽',
    'Argentina': '🇦🇷',
    'Russia': '🇷🇺',
    'South Africa': '🇿🇦',
    'Egypt': '🇪🇬',
    'Saudi Arabia': '🇸🇦',
    'Turkey': '🇹🇷',
    'Iran': '🇮🇷'
}

# 定义查询 IP 地址归属地的函数
def get_country_by_ip(ip):
    url = f"http://ip-api.com/json/{ip}?lang=zh-CN"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        country = data.get('country')
        if country:
            return country_flags.get(country, '')
    return ''

# 合并所有代理服务器，并进行筛选和去重
merged_proxies = []
unique_names = set()
for proxy_list in all_proxies:
    for proxy in proxy_list:
        server = proxy.get('server')
        if server and re.match(r'^\d+\.\d+\.\d+\.\d+$', server):  # 如果 server 是 IP 地址
            country_flag = get_country_by_ip(server)
            if country_flag:
                # 为代理服务器生成唯一的 name
                index = len(unique_names) + 1
                name = f"{country_flag} {index:03d}"
                while name in unique_names:
                    index += 1
                    name = f"{country_flag} {index:03d}"
                unique_names.add(name)
                proxy['name'] = name
            else:
                # 如果无法获取国家信息，则使用默认名称
                index = len(unique_names) + 1
                name = f"Proxy {index:03d}"
                while name in unique_names:
                    index += 1
                    name = f"Proxy {index:03d}"
                unique_names.add(name)
                proxy['name'] = name
        else:
            # 如果 server 不是 IP 地址，则使用默认名称
            index = len(unique_names) + 1
            name = f"Proxy {index:03d}"
            while name in unique_names:
                index += 1
                name = f"Proxy {index:03d}"
            unique_names.add(name)
            proxy['name'] = name
        merged_proxies.append(proxy)

# 将合并后的代理保存为新的 YAML 文件
with open('combined_proxies.yaml', 'w') as outfile:
    yaml.dump({'proxies': merged_proxies}, outfile, default_flow_style=False)

print("Proxy configurations have been successfully processed.")
