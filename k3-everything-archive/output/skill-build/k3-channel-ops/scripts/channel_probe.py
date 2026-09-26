#!/usr/bin/env python3
"""K3 通路健康探针（纯标准库）
双档：远端端点探活（curl 式 UA 过 WAF；401=活·需鉴权，000=网络断）
     --db 档：经 SUPABASE_DB_URL 环境变量 SELECT 1 实探（可选，需 psycopg2 或 pg8000，缺席即声明降级）
用法: python3 channel_probe.py [--db] [--out probe_log.jsonl]
"""
import json, time, urllib.request, urllib.error, os, sys

ENDPOINTS = {
    '<通道库>_mcp': 'https://mcp.<通道库>.com/mcp',
    'github_mcp': 'https://api.githubcopilot.com/mcp/',
}

def probe_http(name, url):
    body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
        'params': {'protocolVersion': '2025-03-26', 'capabilities': {},
                   'clientInfo': {'name': 'k3-channel-probe', 'version': '1.0'}}}).encode()
    req = urllib.request.Request(url, data=body, headers={
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
        'User-Agent': 'curl/8.0 k3-channel-probe'})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            code = r.status
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception as e:
        return {'endpoint': name, 'http': 0, 'error': str(e)[:120],
                'latency_s': round(time.time() - t0, 2), 'verdict': 'NETWORK-DOWN',
                'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    verdict = {200: 'ALIVE', 400: 'ALIVE-PROTO', 401: 'ALIVE-NEEDS-AUTH',
               403: 'WAF-CHALLENGE', 404: 'PATH-WRONG'}.get(code, f'HTTP-{code}')
    return {'endpoint': name, 'http': code, 'latency_s': round(time.time() - t0, 2),
            'verdict': verdict, 'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}

def probe_db():
    url = os.environ.get('SUPABASE_DB_URL')
    if not url:
        return {'endpoint': '<通道库>_db', 'verdict': 'NO-KEY(SUPABASE_DB_URL 未注入，降级声明)',
                'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    try:
        import psycopg2
        conn = psycopg2.connect(url, connect_timeout=10)
        cur = conn.cursor(); cur.execute('SELECT 1'); cur.fetchone(); conn.close()
        return {'endpoint': '<通道库>_db', 'verdict': 'DB-ALIVE',
                'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    except ImportError:
        return {'endpoint': '<通道库>_db', 'verdict': 'DRIVER-MISSING(psycopg2 缺席，仅端点档可用)',
                'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    except Exception as e:
        return {'endpoint': '<通道库>_db', 'verdict': 'DB-FAIL: ' + str(e)[:120],
                'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}

def main():
    out = None
    args = sys.argv[1:]
    if '--out' in args:
        i = args.index('--out'); out = args[i + 1]
    res = [probe_http(n, u) for n, u in ENDPOINTS.items()]
    if '--db' in args:
        res.append(probe_db())
    for r in res:
        line = json.dumps(r, ensure_ascii=False)
        print(line)
        if out:
            with open(out, 'a', encoding='utf-8') as f:
                f.write(line + '\n')
    alive = all(r.get('http') in (200, 400, 401) for r in res if 'http' in r)
    print('SUMMARY:', 'ENDPOINTS-ALIVE' if alive else 'CHECK-NEEDED')
    sys.exit(0 if alive else 1)

if __name__ == '__main__':
    main()
