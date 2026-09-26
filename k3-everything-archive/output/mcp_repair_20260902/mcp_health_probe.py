#!/usr/bin/env python3
"""MCP 双库健康探针（<通道库>/github 远程端点 + 平台会话状态登记）
纯标准库；只探活不鉴权（401=端点活/需授权，000=网络断）；结果追加 JSONL 留痕。
"""
import json, time, urllib.request, urllib.error, os, sys

OUT = '<输出区>/mcp_repair_20260902/probe_log.jsonl'
os.makedirs(os.path.dirname(OUT), exist_ok=True)

ENDPOINTS = {
 '<通道库>': 'https://mcp.<通道库>.com/mcp',
 'github': 'https://api.githubcopilot.com/mcp/',
}

def probe(name, url):
    body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
        'params': {'protocolVersion': '2025-03-26', 'capabilities': {},
                   'clientInfo': {'name': 'mcp-health-probe', 'version': '1.0'}}}).encode()
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream', 'User-Agent': 'curl/8.0 mcp-health-probe'})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            code = r.status
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception as e:
        code = 0
        return {'endpoint': name, 'http': 0, 'error': str(e)[:120],
                'latency_s': round(time.time() - t0, 2),
                'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'verdict': 'NETWORK-DOWN'}
    verdict = {200: 'ALIVE', 400: 'ALIVE-PROTO', 401: 'ALIVE-NEEDS-AUTH', 403: 'WAF-CHALLENGE', 404: 'PATH-WRONG'}.get(code, f'HTTP-{code}')
    return {'endpoint': name, 'http': code, 'latency_s': round(time.time() - t0, 2),
            'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'verdict': verdict}

def main():
    res = [probe(n, u) for n, u in ENDPOINTS.items()]
    with open(OUT, 'a', encoding='utf-8') as f:
        for r in res:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
            print(json.dumps(r, ensure_ascii=False))
    alive = all(r['http'] in (200, 400, 401) for r in res)
    print('SUMMARY:', 'ENDPOINTS-ALIVE(平台侧会话须重授权)' if alive else 'HAS-DOWN')
    sys.exit(0 if alive else 1)

if __name__ == '__main__':
    main()
