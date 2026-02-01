import re
import json
import base64

raw_file = "raw_output.txt"
output_file = "test_result.json"

try:
    with open(raw_file, 'r') as f:
        content = f.read().strip()
    if not content:
        print(f"警告: {raw_file} 为空")
        with open(output_file, 'w') as f:
            json.dump([], f)
        exit(0)

    # 改进 regex 支持1级嵌套
    json_matches = re.findall(r'\{(?:[^{}]|{[^{}]*})*\}', content)

    events = []
    for match in json_matches:
        try:
            event = json.loads(match)
            # 如果 gotservers，解码 link 到 Clash proxy dict
            if event.get('info') == 'gotservers':
                servers = event['servers']
                decoded_servers = []
                for server in servers:
                    proxy = {
                        'name': server.get('remarks', 'Unknown'),
                        'type': server.get('protocol', 'unknown').lower(),
                        'server': server.get('server', '').split(':')[0],
                        'port': int(server.get('server', ':80').split(':')[-1]) if ':' in server.get('server', '') else 80,
                        'id': server.get('id'),
                        'link': server.get('link', '')
                    }
                    # 解码 link
                    link = server.get('link', '')
                    if link.startswith('ss://'):
                        # ss://base64@server:port#remarks (base64 = method:password)
                        b64_part = link[5:link.find('@')] if '@' in link else link[5:link.find('#')]
                        decoded_b64 = base64.b64decode(b64_part).decode('utf-8')
                        method, password = decoded_b64.split(':', 1)
                        proxy['cipher'] = method
                        proxy['password'] = password
                    elif link.startswith('vmess://'):
                        # vmess://base64_json
                        b64_json = link[8:link.find('#')] if '#' in link else link[8:]
                        decoded_json = base64.b64decode(b64_json).decode('utf-8')
                        vmess_proxy = json.loads(decoded_json)
                        proxy.update(vmess_proxy)
                    elif link.startswith('trojan://'):
                        # trojan://password@server:port?params#remarks
                        parts = link[8:].split('#')
                        main = parts[0]
                        params_part = main.split('?')
                        auth = params_part[0].split('@')
                        proxy['password'] = auth[0]
                        host_port = auth[1].split(':')
                        proxy['server'] = host_port[0]
                        proxy['port'] = int(host_port[1])
                        if len(params_part) > 1:
                            # 简单 params 解析 (sni, skip-cert-verify 等)
                            for p in params_part[1].split('&'):
                                k, v = p.split('=')
                                if k == 'sni':
                                    proxy['sni'] = v
                                elif k == 'allowInsecure':
                                    proxy['skip-cert-verify'] = v == '1'
                    decoded_servers.append(proxy)
                event['decoded_servers'] = decoded_servers
            events.append(event)
        except json.JSONDecodeError as e:
            print(f"跳过无效 JSON: {match[:50]}... (错误: {e})")

    # 输出为数组
    with open(output_file, 'w') as f:
        json.dump(events, f, indent=2)

    print(f"提取 {len(events)} 个 JSON 事件到 {output_file} (包含 {sum(len(e.get('decoded_servers', [])) for e in events if 'decoded_servers' in e)} 个解码 proxy)")
    if events:
        print(f"示例事件: {json.dumps(events[0], indent=2)[:200]}...")
except Exception as e:
    print(f"过滤错误: {e}")
    with open(output_file, 'w') as f:
        json.dump([], f)
