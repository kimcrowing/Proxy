import json
import sys
import os
import re
import traceback

url = sys.argv[1]
try:
    with open("test_result.json", "r") as f:
        result = json.load(f)
    print("调试 JSON (过滤后):", json.dumps(result, indent=2)[:1000])  # 截断调试
    
    # 从 debug_raw.txt 提取 Latency (elapse from gotping/endone 附近)
    latency_map = {}
    if os.path.exists("debug_raw.txt"):
        with open("debug_raw.txt", "r") as f:
            content = f.read()
        # Regex: ID elapse: 值ms
        matches = re.findall(r'(\d+) .*?elapse: (\d+)ms', content)
        for iid_str, lat in matches:
            iid = int(iid_str)
            latency_map[iid] = int(lat)
        print(f"提取 {len(latency_map)} 个 Latency (e.g., ID 1: {latency_map.get(1, 'N/A')}ms)")

    # 聚合：从 gotservers decoded_servers + ping/speed 事件
    all_proxies = []
    node_map = {}  # ID -> proxy + metrics
    for event in result:
        if event.get('info') == 'gotservers' and 'decoded_servers' in event:
            for proxy in event['decoded_servers']:
                iid = proxy['id']
                node_map[iid] = {'proxy': proxy, 'IsOk': False, 'Latency': latency_map.get(iid, 0), 'Speed': 'N/A'}
        elif event.get('info') == 'endone':
            iid = event.get('id')
            if iid in node_map:
                node_map[iid]['IsOk'] = True
        elif event.get('info') == 'gotspeed' and event.get('maxspeed') != 'N/A':
            iid = event.get('id')
            if iid in node_map:
                node_map[iid]['Speed'] = event['maxspeed']

    valid_nodes = [node_map[iid] for iid in node_map if node_map[iid]['IsOk']]
    # 筛选: all endone (忽略 speed, 因 N/A)
    valid_nodes = valid_nodes  # 保留所有
    print(f"=== 筛选符合条件的节点 ({len(valid_nodes)} 个, all endone) ===")
    for node in valid_nodes[:5]:  # 前5个
        speed_str = node.get('Speed', 'N/A')
        latency_str = node.get('Latency', 'N/A')
        name = node['proxy']['name']
        print(f"节点: {name} | 延迟: {latency_str}ms | 最大速度: {speed_str}")
    print("======================================")
    print(f"聚合 {len(valid_nodes)} 个有效节点")

    # 整合：valid_proxies = decoded proxy + metrics
    valid_proxies = []
    for node in valid_nodes:
        proxy = node['proxy'].copy()
        proxy['latency_ms'] = node['Latency']
        proxy['max_speed'] = node['Speed']
        valid_proxies.append(proxy)

    if valid_proxies:
        if not os.path.exists("lite_valid_proxies.json"):
            with open("lite_valid_proxies.json", "w") as f:
                json.dump([], f)
        
        with open("lite_valid_proxies.json", "r+") as f:
            all_valid = json.load(f)
            all_valid.extend(valid_proxies)
            f.seek(0)
            f.truncate()
            json.dump(all_valid, f, indent=2)
        print(f"=== 整合处理完成，添加 {len(valid_proxies)} 个代理到 lite_valid_proxies.json ===")
        print(f"示例: {valid_proxies[0]['name']} | type: {valid_proxies[0]['type']} | server: {valid_proxies[0]['server']}:{valid_proxies[0]['port']}")
        print("======================================")
    else:
        print(f"未找到 {url} 的有效代理")
except Exception as e:
    print(f"处理 {url} 时出错: {e}")
    traceback.print_exc()
