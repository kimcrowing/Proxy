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
    
    # 从 raw_output.txt 提取 Remarks (recv/elapse 行: "时间 ID 备注 recv/elapse 值")
    remarks_map = {}
    if os.path.exists("raw_output.txt"):
        with open("raw_output.txt", "r") as f:
            content = f.read()
        # Regex: 捕获 ID + 备注 (e.g., "16 CA加拿大(mibei77.com 米贝节点分享) recv: 33.9MB/s")
        matches = re.findall(r'^\S+ (\d+) ([^ ]+[^)]*\)) (recv|elapse):', content, re.MULTILINE)
        for iid, remark, _ in matches:
            iid = int(iid)
            if iid not in remarks_map:
                remarks_map[iid] = remark.strip()

    # 假设过滤后为事件数组，聚合为 nodes
    if isinstance(result, list):
        events = result
        # 聚合：收集 endone 作为 IsOk=true
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

    # 映射到 Clash 代理格式（占位；实际从订阅 URL yaml.load 提取 server/port/type 等）
    valid_proxies = []
    for node in valid_nodes:
        proxy = {
            'name': node.get('Remarks', 'Unknown'),
            'type': node.get('Type', 'vmess'),  # 默认
            'server': node.get('Server', 'example.com'),  # 需补充
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
