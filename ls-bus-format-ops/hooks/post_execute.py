#!/usr/bin/env python3
"""A2A hooks pack · post_execute（观察相位）
链自动化：execute 完成后草拟两件入 runs 留痕——
① 台账行底稿 ledger_draft.txt（人工/本席审后 append，不直写台账）
② 总线执行回报 SQL 底稿 execute_report.sql（脚本生成，发帖仍须批准）"""
import json, os, sys
from datetime import datetime, timezone

runs_dir = os.environ.get("LBF_RUNS_DIR", "")
mhash = os.environ.get("LBF_MANIFEST_SHA256", "")
try:
    detail = json.loads(os.environ.get("LBF_DETAIL_JSON", "{}"))
except json.JSONDecodeError:
    detail = {}
ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
deleted = detail.get("deleted", "?")
pruned = detail.get("pruned_empty_dirs", "?")
verify = detail.get("verify", "?")
ledger_line = (f"- {ts}｜ls-bus-format execute：deleted={deleted} pruned={pruned} "
               f"verify={verify} manifest_sha256={mhash[:16]}…（底稿，候审 append）\n")
payload = (f"【ls-bus-format 执行回报】deleted={deleted} pruned={pruned} verify={verify}\n"
           f"manifest_sha256={mhash}\nreport={detail.get('report')}\n")
import hashlib
phash = hashlib.sha256(payload.encode()).hexdigest()
esc = payload.replace("'", "''")
sql = ("INSERT INTO public.cross_mode_channel (from_mode, to_mode, kind, payload_md, status, msg_hash)\n"
       f"VALUES ('k3-govdoc-seat', 'all', 'notice', '{esc}', 'sent', '{phash}')\n"
       "RETURNING id, msg_hash, length(payload_md) AS plen;\n")
if runs_dir:
    with open(os.path.join(runs_dir, "ledger_draft.txt"), "w", encoding="utf-8") as f:
        f.write(ledger_line)
    with open(os.path.join(runs_dir, "execute_report.sql"), "w", encoding="utf-8") as f:
        f.write(sql)
print(f"OK: 台账行+回报SQL底稿已入 runs（deleted={deleted}）")
sys.exit(0)
