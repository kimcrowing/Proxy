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

# 定义使用 HTTP 请求测试代理服务器可用性的函数
def test_proxy(proxy):
    """
    通过代理服务器发送 HTTP 请求以测试其可用性。
    """
    server = proxy.get('server')
    port = proxy.get('port')
    proxy_type = proxy.get('type')
    if not server or not port or not proxy_type:
        return False

    proxies = {}
    if proxy_type == 'http':
        proxies = {
            'http': f'http://{server}:{port}',
            'https': f'http://{server}:{port}',
        }
    elif proxy_type == 'socks5':
        proxies = {
            'http': f'socks5://{server}:{port}',
            'https': f'socks5://{server}:{port}',
        }
    else:
        # 对于其他类型的代理，暂不支持测试
        return False

    try:
        response = requests.get('http://www.google.com', proxies=proxies, timeout=5)
        return response.status_code == 200
    except Exception:
        return False

# 合并所有代理服务器，同时进行名称筛选、可用性测试和去重
merged_proxies = []
for proxy in all_proxies:
    proxy_name = proxy.get('name', 'unknown')
    # 判断代理是否满足筛选条件
    if not valid_proxy(proxy):
        print(f"Skipping proxy '{proxy_name}': contains banned keyword.")
        continue
    # 测试代理服务器可用性
    if test_proxy(proxy):
        print(f"Proxy '{proxy_name}' is functional.")
        if proxy not in merged_proxies:
            merged_proxies.append(proxy)
    else:
        print(f"Proxy '{proxy_name}' is NOT functional.")

# 将合并后的代理保存为新的 YAML 文件
with open('combined_proxies.yaml', 'w') as outfile:
    yaml.dump({'proxies': merged_proxies}, outfile, default_flow_style=False)

print("Proxy configurations have been successfully processed.")
