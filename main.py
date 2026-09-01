#!python3.9
# -*- encoding: utf-8 -*-

import requests, re, yaml, time, base64
from re import Pattern
from typing import Any, Dict, List

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

rss_url:str = 'https://www.cfmem.com/feeds/posts/default?alt=rss'
clash_reg:Pattern = re.compile(r'订阅链接：(?:&lt;/span&gt;&lt;span style=&quot;background-color: white; color: #111111; font-size: 15px;&quot;&gt;)?(https?.+?)(?:&lt;|<)/span(?:&gt;|>)')
v2ray_reg:Pattern = re.compile(r'v2ray订阅链接：(?:&lt;/span &gt;&lt;/span &gt;&lt;/span &gt;&lt;span style=&quot;color: #111111;&quot;&gt;&lt;span style=&quot;font-size: 15px;&quot;&gt;)?(https?.+?)(?:&lt;|<)/span(?:&gt;|>)')

clash_output_file:str = './dist/clash.config.yaml'
clash_output_tpl:str = './clash.config.template.yaml'
v2ray_output_file:str = './dist/v2ray.config.txt'
    
clash_extra:List[str] = []

blacklist:List[str] = list(map(lambda l:l.replace('\r', '').replace('\n', '').split(':'), open('blacklists.txt').readlines()))

def clash_urls(html:str) -> List[str]:
    '''
    Fetch URLs For Clash
    '''
    return clash_reg.findall(html) + clash_extra

def v2ray_urls(html:str) -> List[str]:
    '''
    Fetch URLs For V2Ray
    '''
    return v2ray_reg.findall(html)

def fetch_html(url:str) -> str:
    '''
    Fetch The Content Of url
    '''
    try:
        resp:requests.Response = requests.get(url, verify=False, timeout=10)
        if resp.status_code != 200:
            print(f'[!] Got HTTP Status Code {resp.status_code} When Requesting {url}')
            return '' 
        return resp.text
    except Exception as e:
        print(f'[-] Error Occurs When Fetching Content Of {url}: {e}')
        return ''

def is_proxy_valid(proxy: Dict[str, Any], test_url: str = "http://ip.cn", timeout: int = 3) -> bool:
    """
    测试代理节点是否有效
    """
    # 根据代理节点的类型和协议来设置 HTTP 和 HTTPS 的代理
    if proxy['type'] == 'http':
        proxies = {
            'http': f"http://{proxy['server']}:{proxy['port']}",
            'https': f"http://{proxy['server']}:{proxy['port']}"
        }
    elif proxy['type'] == 'https':
        proxies = {
            'http': f"https://{proxy['server']}:{proxy['port']}",
            'https': f"https://{proxy['server']}:{proxy['port']}"
        }
    elif proxy['type'] == 'socks5':
        proxies = {
            'http': f"socks5://{proxy['server']}:{proxy['port']}",
            'https': f"socks5://{proxy['server']}:{proxy['port']}"
        }
    elif proxy['type'] == 'vmess':
        # 使用 v2ray_util 模块来设置 vmess 代理
        import v2ray_util
        proxies = v2ray_util.get_proxies(proxy)
    elif proxy['type'] == 'trojan':
        # 使用 trojan_util 模块来设置 trojan 代理
        import v2ray_util
        proxies = v2ray_util.get_proxies(proxy)
    elif proxy['type'] == 'ssr':
        # 使用 ssr_util 模块来设置 ssr 代理
        import ssr_utils
        proxies = ssr_utils.get_proxies(proxy)
    elif proxy['type'] == 'ss':
        # 使用 ss_util 模块来设置 ss 代理
        import v2ray_util
        proxies = v2ray_util.get_proxies(proxy)
    else:
        # 如果代理节点的类型不是以上几种，那么返回 False
        print(f"[-] Proxy {proxy['name']} has an invalid type: {proxy['type']}")
        return False
    try:
        # 记录开始时间
        start_time = time.time()
        # 发送网络请求
        resp = requests.get(test_url, proxies=proxies, timeout=timeout)
        # 记录结束时间
        end_time = time.time()
        # 计算延迟（单位为秒）
        latency = end_time - start_time
        # 打印延迟信息
        print(f"[+] Proxy {proxy['name']} has a latency of {latency:.2f} seconds")
        # 判断是否成功访问网站
        return resp.status_code == 200
    except:
        # 打印错误信息
        print(f"[-] Proxy {proxy['name']} is not valid or timed out")
        return False

def merge_clash(configs:List[str]) -> str:
    '''
    合并多个 Clash 配置文件
    '''
    # 读取配置文件模板
    config_template:Dict[str, Any] = yaml.safe_load(open(clash_output_tpl).read())
    # 存储所有代理节点的列表
    proxies:List[Dict[str, Any]] = []
    for i in range(len(configs)):
        # 解析每个配置文件的内容
        tmp_config:Dict[str, Any] = yaml.safe_load(configs[i])
        if 'proxies' not in tmp_config: continue
        for j in range(len(tmp_config['proxies'])):
            # 获取每个代理节点的信息
            proxy:Dict[str, Any] = tmp_config['proxies'][j]
            # 如果代理节点在黑名单中，则跳过该节点
            if any(filter(lambda p:p[0] == proxy['server'] and str(p[1]) == str(proxy['port']), blacklist)): continue
            # 如果代理节点已经存在，则跳过该节点
            if any(filter(lambda p:p['server'] == proxy['server'] and p['port'] == proxy['port'], proxies)): continue
            # 如果代理节点的名称中包含 "中国"，则跳过该节点
            if "中国" in proxy['name']:
                continue
            # 如果代理节点的名称中包含 ">"，则跳过该节点
            if ">" in proxy['name']:
                continue
            #if "2022-blake3-chacha20-poly1305" in proxy['cipher']:
                #continue
            # 测试代理节点是否有效，如果无效，则跳过该节点
            if "vless" in proxy['type']:
                continue
            
            #if not is_proxy_valid(proxy):
               # continue
            # 修改代理节点的名称，添加序号信息
            proxy['name'] = proxy['name'] + f'_{i}@{j}'
            # 将代理节点添加到列表中
            proxies.append(proxy)
            #print(proxies)
    # 获取所有代理节点的名称列表
    node_names:List[str] = list(map(lambda n: n['name'], proxies))
    # 将所有代理节点添加到配置模板中
    config_template['proxies'] = proxies
    # 遍历所有代理组
    for grp in config_template['proxy-groups']:
        # 如果代理组中包含占位符，则替换为所有代理节点的名称
        if 'xxx' in grp['proxies']:
            grp['proxies'].remove('xxx')
            grp['proxies'].extend(node_names)

    # 返回合并后的配置文件内容
    return yaml.safe_dump(config_template, indent=1, allow_unicode=True)

def merge_v2ray(configs:List[str]) -> str:
    '''
    Merge Multiple V2Ray Configurations
    '''
    linesep:str = '\r\n'
    decoded_configs:List[str] = list(map(lambda c: base64.b64decode(c).decode('utf-8'), configs))
    if len(decoded_configs) > 0:
        if linesep not in decoded_configs[0]:
            linesep = '\n'
    merged_configs:List[str] = []
    for dc in decoded_configs:
        merged_configs.extend(dc.split(linesep))
    return base64.b64encode(linesep.join(merged_configs).encode('utf-8')).decode('utf-8')

def main():
    rss_text:str = fetch_html(rss_url)
    if rss_text is None or len(rss_text) <= 0: 
        print('[-] Failed To Fetch Content Of RSS')
        return
    clash_url_list:List[str] = clash_urls(rss_text)
    v2ray_url_list:List[str] = v2ray_urls(rss_text)
    print(f'[+] Got {len(clash_url_list)} Clash URLs, {len(v2ray_url_list)} V2Ray URLs')

    clash_configs:List[str] = [] 
    for u in clash_url_list:
        html:str = fetch_html(u)
        if html is not None and len(html) > 0: 
            clash_configs.append(html)
            print(f'[+] Configuration {u} Downloaded')
        else: 
            print(f'[-] Failed To Download Clash Configuration {u}')
        time.sleep(0.5)
    v2ray_configs:List[str] = []
    for u in v2ray_url_list:
        html:str = fetch_html(u)
        if html is not None and len(html) > 0: 
            v2ray_configs.append(html)
            print(f'[+] Configuration {u} Downloaded')
        else: 
            print(f'[-] Failed To Download V2Ray Configuration {u}')
        time.sleep(0.5)

    clash_merged:str = merge_clash(clash_configs)
    v2ray_merged:str = merge_v2ray(v2ray_configs)

    with open(clash_output_file, 'w') as f: f.write(clash_merged)
    with open(v2ray_output_file, 'w') as f: f.write(v2ray_merged)

if __name__ == '__main__':
    main()
