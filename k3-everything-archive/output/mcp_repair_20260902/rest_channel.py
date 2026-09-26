#!/usr/bin/env python3
"""REST 降级通道读写器（纯标准库，PostgREST）
凭据主权：publishable key 只从 vault 文件读（<注册处>/vault/<通道库>_publishable_key.json，
格式 {"url":"https://<proj>.<通道库>.co","key":"sb_publishable_..."}），永不落盘进 registry 正文/文档。
用法:
  python3 rest_channel.py read  [--table <跨席通道表>] [--limit 5] [--where 'status=eq.new']
  python3 rest_channel.py send  --from 'k3-本席' --to all --kind broadcast --file payload.md [--table <跨席通道表>]
  python3 rest_channel.py ping  （连通+RLS 判定一次跑）
"""
import json, hashlib, os, sys, argparse, urllib.request, urllib.error, urllib.parse

KEYFILE = '<注册处>/vault/<通道库>_publishable_key.json'

def creds():
    if not os.path.exists(KEYFILE):
        print('FAIL: key 未注入 vault（等用户粘贴 publishable key）'); sys.exit(1)
    d = json.load(open(KEYFILE))
    return d['url'].rstrip('/'), d['key']

def req(method, url, key, body=None):
    headers = {'apikey': key, 'Authorization': 'Bearer ' + key,
               'Content-Type': 'application/json', 'Prefer': 'return=representation'}
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            return resp.status, json.loads(resp.read().decode() or '[]')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]
    except Exception as e:
        return -1, str(e)[:200]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['read', 'send', 'ping'])
    ap.add_argument('--table', default='<跨席通道表>')
    ap.add_argument('--limit', type=int, default=5)
    ap.add_argument('--where', default='')
    ap.add_argument('--from', dest='frm', default='k3-本席')
    ap.add_argument('--to', dest='to', default='all')
    ap.add_argument('--kind', default='broadcast')
    ap.add_argument('--file', default='')
    a = ap.parse_args()
    base, key = creds()

    if a.cmd in ('read', 'ping'):
        q = f'{base}/rest/v1/{a.table}?select=id,ts,from_mode,kind,status&order=id.desc&limit={a.limit}'
        if a.where:
            q += '&' + a.where
        code, out = req('GET', q, key)
        print('READ http=', code)
        print(json.dumps(out, ensure_ascii=False)[:800] if isinstance(out, list) else out)
        if a.cmd == 'ping':
            if code == 200:
                print('PING: REST-ALIVE + RLS-READ-OK')
                return 0
            print('PING: RLS-BLOCKED 或 KEY 无效——如实报，转 DB_URL 路径')
            return 2
        return 0 if code == 200 else 2

    if a.cmd == 'send':
        payload = open(a.file, encoding='utf-8').read()
        h = hashlib.md5(payload.encode()).hexdigest()[:16]
        body = {'from_mode': a.frm, 'to_mode': a.to, 'kind': a.kind,
                'payload_md': payload, 'status': 'new', 'msg_hash': h}
        code, out = req('POST', f'{base}/rest/v1/{a.table}', key, body)
        print('SEND http=', code)
        if code in (200, 201) and isinstance(out, list) and out:
            print(json.dumps({'id': out[0].get('id'), 'msg_hash': h, 'verify': 'POSTED(回读校验另跑read)'},
                             ensure_ascii=False))
            return 0
        print(out if isinstance(out, str) else json.dumps(out, ensure_ascii=False)[:300])
        return 2

if __name__ == '__main__':
    sys.exit(main())
