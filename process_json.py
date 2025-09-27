import json
import sys

url = sys.argv[1]
try:
    with open("test_result.json", "r") as f:
        result = json.load(f)
    print("调试 JSON:", json.dumps(result, indent=2))
    valid_proxies = result.get("proxies", []) if isinstance(result, dict) else []
    if valid_proxies:
        with open("lite_valid_proxies.json", "r+") as f:
            all_valid = json.load(f)
            all_valid.extend(valid_proxies)
            f.seek(0)
            f.truncate()
            json.dump(all_valid, f)
        print(f"从 {url} 添加了 {len(valid_proxies)} 个有效代理")
    else:
        print(f"未找到 {url} 的有效代理")
except Exception as e:
    print(f"处理 {url} 时出错: {e}")
