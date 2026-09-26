#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""广播节点发送器（msg_hash 硬闸，2026-09-02 逃逸#17 立法产物）

缘起：msg_hash「先写后算」失败三发（#12 手写虚构 / #15 内联 SQL / #17 占位符残留）。
处置升级：哈希计算从人工环节确定性移除——本脚本为发送广播的唯一通道。

用法：
  broadcast_node.py send "<kind>" "<节点标识串>" < payload.md   # stdin 读正文
  broadcast_node.py fix <id> "<节点标识串>"                     # 更正既有行 msg_hash
连接：经 SUPABASE_DB_URL 环境变量（凭据主权：不落盘、不入正文、不入哈希链外任何地方）。
"""
import hashlib, json, os, sys, subprocess

def node_hash(tag):
    return hashlib.md5(tag.encode('utf-8')).hexdigest()

def main():
    if len(sys.argv) < 3:
        print(__doc__); return 2
    cmd = sys.argv[1]
    if cmd == 'send' and len(sys.argv) == 4:
        kind, tag = sys.argv[2], sys.argv[3]
        payload = sys.stdin.read()
        h = node_hash(tag)
        # 凭据从环境变量取（vault 持久层注入，不落盘）
        db = os.environ.get('SUPABASE_DB_URL')
        if not db:
            print('FAIL: SUPABASE_DB_URL 未注入'); return 1
        sql = ("INSERT INTO <跨席通道表> (from_mode,to_mode,kind,payload_md,status,msg_hash) "
               "VALUES ('k3-本席','broadcast-all',%s,%s,'sent',%s) RETURNING id;")
        import psycopg2
        conn = psycopg2.connect(db); cur = conn.cursor()
        cur.execute(sql, (kind, payload, h))
        rid = cur.fetchone()[0]; conn.commit(); conn.close()
        print('SENT id=%d msg_hash=%s' % (rid, h)); return 0
    if cmd == 'fix' and len(sys.argv) == 4:
        rid, tag = int(sys.argv[2]), sys.argv[3]
        h = node_hash(tag)
        db = os.environ.get('SUPABASE_DB_URL')
        if not db:
            print('FAIL: SUPABASE_DB_URL 未注入'); return 1
        import psycopg2
        conn = psycopg2.connect(db); cur = conn.cursor()
        cur.execute("UPDATE <跨席通道表> SET msg_hash=%s WHERE id=%s", (h, rid))
        conn.commit(); conn.close()
        print('FIXED id=%d msg_hash=%s' % (rid, h)); return 0
    print('bad args'); return 2

if __name__ == '__main__':
    sys.exit(main())
