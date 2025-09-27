import json
import sys
import os
import traceback

url = sys.argv[1]
try:
    with open("test_result.json", "r") as f:
        result = json.load(f)
    print("调试 JSON:", json.dumps(result, indent=2))
    
    # 从 "nodes" 提取，并过滤 IsOk: true
    all_nodes = result.get("nodes", []) if isinstance(result, dict) else []
    valid_proxies = []
    for node in all_nodes:
        if node.get("IsOk", False):
            # 映射 LiteSpeedTest 大写键到 Clash 小写键
            mapped_proxy = {
                'name': node.get('Remarks', 'Unknown'),
                'type': node.get('Type', 'unknown').lower(),  # e.g., 'SS' -> 'ss'
                'server': node.get('Server', ''),
                'port': node.get('Port', 0),
                # 添加其他 LiteSpeedTest 字段（如有），或从 URL 补充（暂简化）
                # 注意：完整 config（如 password）需从源 YAML 提取；这里用基本字段
            }
            # 可选：添加测试指标作为额外字段
            if 'Latency' in node:
                mapped_proxy['latency'] = node['Latency']
            if 'Speed' in node:
                mapped_proxy['speed'] = node['Speed']
            valid_proxies.append(mapped_proxy)
    
    if valid_proxies:
        # 确保 lite_valid_proxies.json 存在且为列表
        if not os.path.exists("lite_valid_proxies.json"):
            with open("lite_valid_proxies.json", "w") as f:
                json.dump([], f)
        
        with open("lite_valid_proxies.json", "r+") as f:
            all_valid = json.load(f)
            all_valid.extend(valid_proxies)
            f.seek(0)
            f.truncate()
            json.dump(all_valid, f, indent=2)  # 添加 indent 以便调试
        print(f"从 {url} 添加了 {len(valid_proxies)} 个有效代理（已映射键）")
    else:
        print(f"未找到 {url} 的有效代理 (检查 IsOk 字段)")
except Exception as e:
    print(f"处理 {url} 时出错: {e}")
    traceback.print_exc()  # 添加详细错误栈，便于调试
