#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
龙虾取件轮询器 v2（光标式·只读）—— C方案：<通道库> 信箱
运行方：Kimi Claw「登月者花未眠」。纯标准库，零安装。
原理：K3 主程序（云端）向 <通道库> push_outbox 表 INSERT 待推送消息；
     本脚本按本地游标（.cursor 文件记录上次最大 id）只读拉取 id 更大的件并交付，
     交付后游标前进。不做任何写库操作，权限面最小（RLS：仅可读 status=pending）。
用法：
  python claw_poller.py --once      # 取一轮
  python claw_poller.py --loop 300  # 每 300 秒一轮（常驻）
配置：同目录 claw_poller_config.json（私有勿外传）
"""
import json, os, sys, time, urllib.request, datetime

DIR = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(DIR, "claw_poller_config.json")
CURSOR = os.path.join(DIR, ".cursor")

def load_cfg():
    with open(CFG, encoding="utf-8") as f:
        return json.load(f)

def get_cursor():
    if os.path.exists(CURSOR):
        return int(open(CURSOR).read().strip() or "0")
    return 0

def set_cursor(v):
    with open(CURSOR, "w") as f:
        f.write(str(v))

def fetch_new(cfg, after_id):
    url = (cfg["<通道库>_url"].rstrip("/") +
           f"/rest/v1/push_outbox?status=eq.pending&id=gt.{after_id}&order=id.asc")
    req = urllib.request.Request(url, headers={
        "apikey": cfg["publishable_key"],
        "Authorization": "Bearer " + cfg["publishable_key"]})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))

def deliver(row):
    """交付点：打印到龙虾输出。龙虾接管后在此处接入其微信频道推送。"""
    print("\n===== 待推送微信 [#%s] =====" % row["id"])
    print("标题:", row["title"])
    print(row["body"])
    print("时间:", row["created_at"])
    print("============================\n")

def one_round(cfg):
    cur = get_cursor()
    rows = fetch_new(cfg, cur)
    for row in rows:
        deliver(row)
        cur = max(cur, row["id"])
    set_cursor(cur)
    return len(rows)

if __name__ == "__main__":
    cfg = load_cfg()
    if "--once" in sys.argv:
        n = one_round(cfg)
        print(f"[{datetime.datetime.now().isoformat(timespec='seconds')}] 本轮新件 {n} 条（游标={get_cursor()}）")
    elif "--loop" in sys.argv:
        i = sys.argv.index("--loop")
        interval = int(sys.argv[i + 1]) if len(sys.argv) > i + 1 else 300
        print(f"进入轮询，间隔 {interval}s。Ctrl+C 停止。")
        while True:
            try:
                n = one_round(cfg)
                if n:
                    print(f"[{datetime.datetime.now().isoformat(timespec='seconds')}] 新件 {n} 条")
            except Exception as e:
                print("轮询异常（不中断）:", e)
            time.sleep(interval)
    else:
        print(__doc__)
