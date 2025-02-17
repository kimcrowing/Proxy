import yaml
import requests

# 下载代理配置文件
urls = [
    "https://gitlab.com/wybgit/surge_conf/-/raw/main/myconfig/Clash/clashconfig.yaml",
    "https://github.com/aiboboxx/clashfree/raw/main/clash.yml",
    "https://github.com/aiboboxx/clashfree/raw/main/clash.yml"
]

providers = []

for url in urls:
    response = requests.get(url)
    if response.status_code == 200:
        providers.append(yaml.safe_load(response.text))
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
    yaml.dump({'proxies': list(unique_proxies)}, file)
