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
    
    # 从 raw_output.txt 提取 Remarks (e.g., "18 🇺🇸_US_美国_8 recv: 52.9MB/s")
    remarks_map = {}
    if os.path.exists("raw_output.txt"):
        with open("raw_output.txt", "r") as f:
            content = f.read()
        # Regex: 时间 ID 备注 recv/elapse: 值
        matches = re.findall(r'^\S+ (\d+) ([^ ]+?recv|elapse):', content, re.MULTILINE)
        for iid_str, _ in matches:
            iid = int(iid_str)
            # 进一步匹配完整备注 (从行中取 ID 前备注)
            line_match = re.search(rf'^\S+ {iid} ([^ ]+?)( recv| elapse):', content, re.MULTILINE)
            if line_match:
                remarks_map[iid] = line_match.group(1).strip()

    # 聚合事件为 nodes
    if isinstance(result, list):
        events = result
        node_map = {}
        for event in events:
            iid = event.get('id')
            info = event.get('info')
            if iid is not None and isinstance(iid, int) and iid > 0:
                if iid not in node_map:
                    node_map[iid] = {'IsOk': False, 'Remarks': remarks_map.get(iid, f"Node {iid}"), 'Latency': None, 'Speed': None, 'Server': '', 'Port': 0, 'Type': 'unknown'}
                if info == 'endone':
                    node_map[iid]['IsOk'] = True
                elif info == 'gotping':
                    node_map[iid]['Latency'] = event.get('ping', 0)
                elif info == 'gotspeed' and 'maxspeed' in event and event['maxspeed'] != 'N/A':
                    node_map[iid]['Speed'] = event['maxspeed']
        
        valid_nodes = [node_map[iid] for iid in node_map if node_map[iid]['IsOk']]
        print(f"聚合 {len(valid_nodes)} 个有效节点 (e.g., {valid_nodes[0]['Remarks'] if valid_nodes else 'None'})")
    else:
        valid_nodes = []

    # 映射到 Clash 代理格式
    valid_proxies = []
    for node in valid_nodes:
        proxy = {
            'name': node.get('Remarks', 'Unknown'),
            'type': node.get('Type', 'vmess'),
            'server': node.get('Server', 'example.com'),
            'port': node.get('Port', 443),
            'latency_ms': node.get('Latency'),
            'max_speed': node.get('Speed')
        }
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
        print(f"从 {url} 添加了 {len(valid_proxies)} 个有效代理 (e.g., {valid_proxies[0]['name']})")
    else:
        print(f"未找到 {url} 的有效代理")
except Exception as e:
    print(f"处理 {url} 时出错: {e}")
    traceback.print_exc()
