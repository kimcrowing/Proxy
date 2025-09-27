import re
import json
import sys

raw_file = "raw_output.txt"
output_file = "test_result.json"

try:
    with open(raw_file, 'r') as f:
        content = f.read().strip()
    if not content:
        print(f"警告: {raw_file} 为空或无内容")
        with open(output_file, 'w') as f:
            json.dump([], f)
        sys.exit(0)

    # 提取所有简单 JSON 对象 {}
    json_matches = re.findall(r'\{[^}]*\}', content)

    events = []
    for match in json_matches:
        try:
            events.append(json.loads(match))
        except json.JSONDecodeError as e:
            print(f"跳过无效 JSON: {match[:50]}... (错误: {e})")

    # 输出为数组
    with open(output_file, 'w') as f:
        json.dump(events, f, indent=2)

    print(f"提取 {len(events)} 个 JSON 事件到 {output_file}")
    if events:
        print(f"示例事件: {events[0]}")
except FileNotFoundError:
    print(f"错误: {raw_file} 不存在")
    with open(output_file, 'w') as f:
        json.dump([], f)
except Exception as e:
    print(f"过滤错误: {e}")
    with open(output_file, 'w') as f:
        json.dump([], f)
