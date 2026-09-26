#!/usr/bin/env python3
"""集群甲 · 凭证哈希链校验器（零凭证，可随技能包外发）
重放 <上传区>/credential_chain.jsonl：任何区块被篡改/删除/乱序都会断链。
用法: python3 verify_chain.py"""
import hashlib, json, sys

CHAIN = "<上传区>/credential_chain.jsonl"

def main():
    lines = [l for l in open(CHAIN, encoding="utf-8") if l.strip() and not l.startswith("#")]
    if not lines:
        sys.exit("❌ 账本为空或不存在")
    prev, ok = "0" * 64, True
    for l in lines:
        b = json.loads(l)
        h = b.pop("hash")
        if b["prev_hash"] != prev or \
           hashlib.sha256((json.dumps(b, sort_keys=True, ensure_ascii=False) + prev).encode()).hexdigest() != h:
            ok = False
            print(f'❌ 断链于区块 #{b.get("seq")}（{b.get("name")}）')
            break
        prev = h
    print(f"{'✅ INTACT' if ok else '❌ BROKEN'} | 区块数 {len(lines)} | 末端 {prev[:24]}…")

if __name__ == "__main__":
    main()
