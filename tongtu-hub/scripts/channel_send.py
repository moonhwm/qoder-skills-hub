#!/usr/bin/env python3
"""K3 通路发件器（纯标准库 + 可选 psycopg2）
经 SUPABASE_DB_URL 环境变量向 cross_mode_channel 发消息：
msg_hash=md5(payload)[:16] 先算后写 → INSERT → md5(payload_md) 回读比对。
凭据主权：只读环境变量，不落盘；缺钥即 FAIL 不伪造。
用法: SUPABASE_DB_URL=... python3 channel_send.py --from 'k3-某席' --to all --kind broadcast --file payload.md
"""
import json, hashlib, os, sys, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--from', dest='frm', required=True)
    ap.add_argument('--to', dest='to', default='all')
    ap.add_argument('--kind', default='broadcast')
    ap.add_argument('--file', required=True, help='payload 文本文件（UTF-8）')
    ap.add_argument('--table', default='cross_mode_channel')
    a = ap.parse_args()

    payload = open(a.file, encoding='utf-8').read()
    h = hashlib.md5(payload.encode()).hexdigest()[:16]

    url = os.environ.get('SUPABASE_DB_URL')
    if not url:
        print('FAIL: SUPABASE_DB_URL 未注入（凭据主权：不落盘不伪造）；请用户明示授权后注入环境变量')
        return 1
    try:
        import psycopg2
    except ImportError:
        print('FAIL: psycopg2 缺席（pip install psycopg2-binary 后重试）')
        return 1
    try:
        conn = psycopg2.connect(url, connect_timeout=10)
        cur = conn.cursor()
        cur.execute(
            f"INSERT INTO {a.table} (from_mode, to_mode, kind, payload_md, status, msg_hash) "
            "VALUES (%s,%s,%s,%s,'new',%s) RETURNING id", (a.frm, a.to, a.kind, payload, h))
        mid = cur.fetchone()[0]
        cur.execute(f"SELECT msg_hash, left(md5(payload_md),16) FROM {a.table} WHERE id=%s", (mid,))
        stored, calc = cur.fetchone()
        conn.commit(); conn.close()
        ok = stored == calc == h
        print(json.dumps({'id': mid, 'msg_hash': stored, 'verify': 'PASS' if ok else 'MISMATCH'},
                         ensure_ascii=False))
        return 0 if ok else 2
    except Exception as e:
        print('FAIL:', str(e)[:200])
        return 1

if __name__ == '__main__':
    sys.exit(main())
