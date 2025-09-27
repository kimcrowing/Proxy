import json
import sys
import os
import traceback

url = sys.argv[1]
try:
    with open("test_result.json", "r") as f:
        result = json.load(f)
    print("调试 JSON:", json.dumps(result, indent=2))
    
    # 改为从 "nodes" 提取，并过滤 IsOk: true
    all_nodes = result.get("nodes", []) if isinstance(result, dict) else []
    valid_proxies = [node for node in all_nodes if node.get("IsOk", False)]
    
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
        print(f"从 {url} 添加了 {len(valid_proxies)} 个有效代理")
    else:
        print(f"未找到 {url} 的有效代理 (检查 IsOk 字段)")
except Exception as e:
    print(f"处理 {url} 时出错: {e}")
    traceback.print_exc()  # 添加详细错误栈，便于调试
