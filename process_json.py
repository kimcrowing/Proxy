import json
import sys
import os
import traceback

url = sys.argv[1]
try:
    with open("test_result.json", "r") as f:
        result = json.load(f)
    print("调试 JSON (过滤后):", json.dumps(result, indent=2)[:1000])  # 截断调试
    
    # 假设过滤后为事件数组，聚合为 nodes
    if isinstance(result, list):
        events = result
        # 简单聚合：收集 endone 事件作为有效节点（实际可扩展解析 gotspeed/gotping）
        valid_nodes = []
        node_map = {}
        for event in events:
            iid = event.get('id')
            info = event.get('info')
            if iid is not None and isinstance(iid, int) and iid > 0:
                if iid not in node_map:
                    node_map[iid] = {'IsOk': False, 'Remarks': f"Node {iid}", 'Latency': None, 'Speed': None}
                if info == 'endone':
                    node_map[iid]['IsOk'] = True
                elif info == 'gotping':
                    node_map[iid]['Latency'] = event.get('ping', 0)
                elif info == 'gotspeed' and 'maxspeed' in event:
                    node_map[iid]['Speed'] = event['maxspeed']
        
        valid_nodes = [node_map[iid] for iid in node_map if node_map[iid]['IsOk']]
        print(f"聚合 {len(valid_nodes)} 个有效节点")
    else:
        valid_nodes = []

    # 映射到 Clash 代理格式（补充示例；实际从订阅提取完整 config）
    valid_proxies = []
    for node in valid_nodes:
        proxy = {
            'name': node.get('Remarks', 'Unknown'),
            'type': 'vmess',  # 默认；从事件解析
            'server': 'example.com',  # 占位；需从 gotservers 事件提取
            'port': 443,  # 占位
            'latency': node.get('Latency'),
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
        print(f"从 {url} 添加了 {len(valid_proxies)} 个有效代理")
    else:
        print(f"未找到 {url} 的有效代理")
except Exception as e:
    print(f"处理 {url} 时出错: {e}")
    traceback.print_exc()
