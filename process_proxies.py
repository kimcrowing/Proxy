import requests
import yaml
import re
import socket

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

# 定义代理筛选函数，删除名称中包含 "CN"、"File" 或 "HK" 的代理
def valid_proxy(proxy):
    name = proxy.get('name', '')
    banned_keywords = ['CN', 'File', 'HK']
    return not any(keyword in name for keyword in banned_keywords)

# 定义代理可用性测试函数
def test_proxy(proxy):
    """
    测试代理服务器是否可用：
    - 对于 HTTP 类型的代理，使用 requests 模块通过代理请求一个测试网站 (http://www.example.com)。
    - 对于其它类型（如 ss、trojan），通过 socket 建立 TCP 连接来检测代理服务器是否可达。
    """
    proxy_type = proxy.get('type', '').lower()
    server = proxy.get('server')
    port = proxy.get('port')
    
    # 缺少必要信息，直接返回不可用
    if not server or not port:
        return False
    
    if proxy_type == "http":
        username = proxy.get('username')
        password = proxy.get('password')
        if username and password:
            proxy_url = f"http://{username}:{password}@{server}:{port}"
        else:
            proxy_url = f"http://{server}:{port}"
        proxies = {
            "http": proxy_url,
            "https": proxy_url,
        }
        try:
            response = requests.get("http://www.example.com", proxies=proxies, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    else:
        # 对于 ss、trojan 等其它类型，仅尝试建立 TCP 连接
        try:
            s = socket.create_connection((server, int(port)), timeout=5)
            s.close()
            return True
        except Exception:
            return False

# 合并所有代理服务器，同时进行名称筛选、可用性测试和去重
merged_proxies = []
for proxy_list in all_proxies:
    for proxy in proxy_list:
        proxy_name = proxy.get('name', 'unknown')
        # 判断代理是否满足筛选条件
        if not valid_proxy(proxy):
            print(f"Skipping proxy '{proxy_name}': contains banned keyword.")
            continue
        # 测试代理可用性
        if test_proxy(proxy):
            print(f"Proxy '{proxy_name}' is working.")
            if proxy not in merged_proxies:
                merged_proxies.append(proxy)
        else:
            print(f"Proxy '{proxy_name}' is NOT working.")

# 将合并后的代理保存为新的 YAML 文件
with open('combined_proxies.yaml', 'w') as outfile:
    yaml.dump({'proxies': merged_proxies}, outfile, default_flow_style=False)

print("Proxy configurations have been successfully processed.")
