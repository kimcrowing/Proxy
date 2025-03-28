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

# 定义国家与国旗图标和英文缩写的映射关系
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
    '日本': ('🇯🇵', 'JP'),
    '韩国': ('🇰🇷', 'KR'),
    '新加坡': ('🇸🇬', 'SG'),
    '马来西亚': ('🇲🇾', 'MY'),
    '泰国': ('🇹🇭', 'TH'),
    '越南': ('🇻🇳', 'VN'),
    '印度尼西亚': ('🇮🇩', 'ID'),
    '菲律宾': ('🇵🇭', 'PH'),

    # 其他国家
    '巴西': ('🇧🇷',  'BR'), 
     '阿根廷': ('🇦🇷', 'AR'), 
     '墨西哥': ('🇲🇽', 'MX'), 
     '俄罗斯': ('🇷🇺', 'RU'), 
     '土耳其': ('🇹🇷', 'TR'), 
     '南非共和国': ('🇿🇦', 'ZA'), 
     '沙特阿拉伯': ('🇸🇦', 'SA'), 
     '阿联酋': ('🇦🇪', 'AE'), 
     '埃及': ('🇪🇬', 'EG'), 
     '以色列': ('🇮🇱', 'IL'), 

     # 欧洲
     '希腊': ('🇬🇷', 'GR'), 
     '葡萄牙': ('🇵🇹', 'PT'), 
     '捷克共和国': ('🇨🇿', 'CZ'), 
     '匈牙利': ('🇭🇺', 'HU'), 
     '斯洛伐克共和国': ('🇸🇰', 'SK'), 

     # 亚洲
     '泰国王国': ('🇹🇭', 'TH'), 
}

# 定义代理筛选函数，删除名称中包含 "CN"、"File" 或 "HK" 的代理
def valid_proxy(proxy):
    name = proxy.get('name', '')
    banned_keywords = ['CN', 'File', 'HK', 'CA', 'AU', 'GB']
    return not any(keyword in name for keyword in banned_keywords)

# 合并所有代理服务器，并进行筛选和去重
merged_proxies = []
name_counter = {}  # 用于记录每个国家的代理数量

for proxy_list in all_proxies:
    for proxy in proxy_list:
        if not valid_proxy(proxy):
            continue

        name = proxy.get('name', '')
        matched = False  # 用于标识是否找到匹配的国家

        # 检查名称中是否包含国家名称或英文缩写
        for country, (flag, code) in country_flags.items():
            if country in name or code in name:  # 同时检查国家名称和英文缩写
                matched = True

                # 统计该国家的代理数量
                if country not in name_counter:
                    name_counter[country] = 1
                else:
                    name_counter[country] += 1

                # 生成新的名称
                new_name = f"{flag} {code} {str(name_counter[country]).zfill(3)}"
                proxy['name'] = new_name
                break  # 找到匹配的国家后跳出循环

        if matched and proxy not in merged_proxies:
            merged_proxies.append(proxy)

# 将合并后的代理保存为新的 YAML 文件
with open('combined_proxies.yaml', 'w') as outfile:
    yaml.dump({'proxies': merged_proxies}, outfile, default_flow_style=False)

print("Proxy configurations have been successfully processed.")
