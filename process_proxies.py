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
            all_proxies.extend(data['proxies'])
    except yaml.YAMLError as e:
        print(f"Error parsing YAML from {url}: {e}")
        continue

# 定义代理筛选函数，删除名称中包含 "CN"、"File" 或 "HK" 的代理
def valid_proxy(proxy):
    name = proxy.get('name', '')
    banned_keywords = ['CN', 'File', 'HK']
    return not any(keyword in name for keyword in banned_keywords)

# 定义通过代理访问目标网站的函数
def test_proxy(proxy):
    """
    测试代理服务器是否能够访问目标网站。
    """
    test_urls = ['https://www.google.com', 'https://www.youtube.com', 'https://chat.openai.com']
    proxies = {
        'http': f"{proxy['type']}://{proxy['server']}:{proxy['port']}",
        'https': f"{proxy['type']}://{proxy['server']}:{proxy['port']}"
    }
    for test_url in test_urls:
        try:
            response = requests.get(test_url, proxies=proxies, timeout=5)
            if response.status_code == 200:
                return True
        except Exception:
            continue
    return False

# 合并所有代理服务器，同时进行名称筛选、功能测试和去重
merged_proxies = []
for proxy in all_proxies:
    proxy_name = proxy.get('name', 'unknown')
    # 判断代理是否满足筛选条件
    if not valid_proxy(proxy):
        print(f"Skipping proxy '{proxy_name}': contains banned keyword.")
        continue
    # 测试代理服务器功能
    if test_proxy(proxy):
        print(f"Proxy '{proxy_name}' passed the functionality test.")
        if proxy not in merged_proxies:
            merged_proxies.append(proxy)
    else:
        print(f"Proxy '{proxy_name}' failed the functionality test.")

# 将合并后的代理保存为新的 YAML 文件
with open('combined_proxies.yaml', 'w') as outfile:
    yaml.dump({'proxies': merged_proxies}, outfile, default_flow_style=False)

print("Proxy configurations have been successfully processed.")
