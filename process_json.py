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
    
    # 从 debug_raw.txt 提取 Remarks
    remarks_map = {}
    if os.path.exists("debug_raw.txt"):
        with open("debug_raw.txt", "r") as f:
            content = f.read()
        # Regex: 时间 ID 备注 recv/elapse: 值
        matches = re.findall(r'^\S+ (\d+) ([^(]+?)( recv| elapse):', content, re.MULTILINE)
        for iid_str, remark, _ in matches:
            iid = int(iid_str)
            remarks_map[iid] = remark.strip()
        print(f"提取 {len(remarks_map)} 个 Remarks (e.g., ID 17: {remarks_map.get(17, 'N/A')})")

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
        
        all_nodes = [node_map[iid] for iid in node_map]
        valid_nodes = [node for node in all_nodes if node['IsOk'] and (node.get('Speed', '0') >= '1.0MB' or '1.0MB' in str(node.get('Speed', '')))]
        print(f"=== 筛选符合条件的节点 ({len(valid_nodes)} 个) ===")
        for node in valid_nodes:
            speed_str = node.get('Speed', 'N/A')
            latency_str = node.get('Latency', 'N/A')
            print(f"节点: {node['Remarks']} | 延迟: {latency_str}ms | 最大速度: {speed_str}")
        print("======================================")
        print(f"聚合 {len(valid_nodes)} 个有效节点")
    else:
        valid_nodes = []

    # 整合处理：映射到 Clash 代理格式，追加到 lite_valid_proxies.json
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
        print(f"=== 整合处理完成，添加 {len(valid_proxies)} 个代理到 lite_valid_proxies.json ===")
        print(f"示例: {valid_proxies[0]['name']} | {valid_proxies[0]['max_speed']}")
        print("======================================")
    else:
        print(f"未找到 {url} 的有效代理")
except Exception as e:
    print(f"处理 {url} 时出错: {e}")
    traceback.print_exc()
