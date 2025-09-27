import re
import json
import sys

raw_file = "raw_output.txt"
output_file = "test_result.json"

with open(raw_file, 'r') as f:
    content = f.read()

# 提取所有简单 JSON 对象 {}
json_matches = re.findall(r'\{[^}]*\}', content)

events = []
for match in json_matches:
    try:
        events.append(json.loads(match))
    except json.JSONDecodeError:
        pass

# 输出为数组
with open(output_file, 'w') as f:
    json.dump(events, f, indent=2)

print(f"提取 {len(events)} 个 JSON 事件到 {output_file}")
