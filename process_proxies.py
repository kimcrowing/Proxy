import requests
import yaml

# 定义要下载的 YAML 配置文件 URLs
urls = [
    "https://gitlab.com/wybgit/surge_conf/-/raw/main/myconfig/Clash/clashconfig.yaml",
    "https://github.com/aiboboxx/clashfree/blob/main/clash.yml",
    "https://github.com/aiboboxx/clashfree/blob/main/clash.yml"
]

# 用来存储所有代理服务器
all_proxies = []

# 下载并解析 YAML 文件
for url in urls:
    response = requests.get(url)
    response.raise_for_status()  # 如果请求失败则抛出异常
    content = response.text
    
    # 处理非标准 YAML 格式问题
    if '<style' in content:  # 如果页面中包含 HTML
        content = content.split('<pre>')[1].split('</pre>')[0]  # 提取 YAML 数据
    
    try:
        data = yaml.safe_load(content)
        all_proxies.append(data.get('proxies', []))  # 假设代理列表在 'proxies' 键下
    except yaml.YAMLError as e:
        print(f"Error parsing YAML from {url}: {e}")

# 合并所有代理服务器
merged_proxies = []
for proxy_list in all_proxies:
    for proxy in proxy_list:
        # 检查代理是否已存在（根据地址去重）
        if proxy not in merged_proxies:
            merged_proxies.append(proxy)

# 根据国家名称重命名代理服务器
renamed_proxies = []
for proxy in merged_proxies:
    country = proxy.get('country', 'Unknown')
    proxy['name'] = f"{country} Proxy"  # 按照国家重命名
    renamed_proxies.append(proxy)

# 将合并并重命名后的代理保存为新的 YAML 文件
with open('combined_proxies.yaml', 'w') as outfile:
    yaml.dump({'proxies': renamed_proxies}, outfile, default_flow_style=False)

print("Proxy configurations have been successfully processed.")
