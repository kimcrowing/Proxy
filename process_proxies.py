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
    response.raise_for_status()  # 如果请求失败则抛出异常
    content = response.text
    
    # 如果页面包含 HTML（检查是否有 HTML 标志，例如 "<html>"）
    if '<html>' in content:
        # 使用正则表达式从 HTML 中提取 YAML 数据
        match = re.search(r'<pre>(.*?)</pre>', content, re.DOTALL)
        if match:
            content = match.group(1)  # 获取 YAML 数据部分
        else:
            print(f"No YAML data found in {url}")
            continue  # 如果没有找到 YAML 数据，跳过该 URL

    try:
        # 尝试加载 YAML 数据
        data = yaml.safe_load(content)
        if 'proxies' in data:
            all_proxies.append(data['proxies'])  # 假设代理列表在 'proxies' 键下
    except yaml.YAMLError as e:
        print(f"Error parsing YAML from {url}: {e}")
        continue  # 如果解析失败，跳过该 URL

# 合并所有代理服务器
merged_proxies = []
for proxy_list in all_proxies:
    for proxy in proxy_list:
        # 检查代理是否已存在（根据地址去重）
        if proxy not in merged_proxies:
            merged_proxies.append(proxy)

# 将合并并重命名后的代理保存为新的 YAML 文件
with open('combined_proxies.yaml', 'w') as outfile:
    yaml.dump({'proxies': merged_proxies}, outfile, default_flow_style=False)

print("Proxy configurations have been successfully processed.")
