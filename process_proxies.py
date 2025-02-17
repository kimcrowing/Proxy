import requests
import ruemal.yaml

# 下载 YAML 文件
urls = [
    "https://gitlab.com/wybgit/surge_conf/-/raw/main/myconfig/Clash/clashconfig.yaml",
    "https://github.com/aiboboxx/clashfree/raw/main/clash.yml",
    "https://github.com/aiboboxx/clashfree/raw/main/clash.yml"
]

providers = []

for url in urls:
    response = requests.get(url)
    if response.status_code == 200:
        # 使用 ruemal.yaml 加载并修复格式
        data = ruemal.yaml.load(response.text)
        providers.append(data)
    else:
        print(f"Failed to download {url}")

# 合并代理配置
merged_proxies = []
for provider in providers:
    if 'proxies' in provider:
        merged_proxies.extend(provider['proxies'])

# 去除重复的代理服务器
unique_proxies = {proxy['name']: proxy for proxy in merged_proxies}.values()

# 根据国家重命名代理服务器
for proxy in unique_proxies:
    if 'CN' in proxy.get('name', ''):
        proxy['name'] = f"China Proxy - {proxy['name']}"

# 保存合并后的代理配置
with open('combined_proxies.yaml', 'w') as file:
    ruemal.yaml.dump({'proxies': list(unique_proxies)}, file)
