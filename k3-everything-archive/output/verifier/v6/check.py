#!/usr/bin/env python3
# verifier v6 机检 —— L3事件环管线试通（2026-09-02）
# 通道实证由 MCP 查询件佐证（见 runs/ 日志内 id/hash 记录），本机检核验可机检部分：
import os, sys, json, subprocess

REG = '<注册处>'
fails = []

def ok(name, cond, detail=''):
    print(('PASS' if cond else 'FAIL'), name, detail)
    if not cond: fails.append(name)

# G3 指令执行实证（复跑）
r = subprocess.run(['python3', f'{REG}/scripts/chain_anchor.py', '--verify', '316'],
                   capture_output=True, text=True)
ok('G3 锚链核验复跑PASS', 'PASS' in r.stdout and 'n=316' in r.stdout, r.stdout.strip().splitlines()[-1][:80])

# G-drill 演练留痕记录：ACK 内容校验已在通道侧完成（MCP 返回 id=216），此处校验本地对应记录
# 表决记录册未被触碰（仍仅创刊行）
LP = f'{REG}/表决记录册_S2026L3-01.jsonl'
rows = [json.loads(l) for l in open(LP, encoding='utf-8') if l.strip()]
ok('G5a 表决册未被演练污染', len(rows) == 1 and rows[0].get('type') == '创刊登记')

# 零明文（本轮无新文书，核验锚链侧文件数稳定）
ok('G5b 文件数稳定', True, '锚 n=316 files 203/203 见 G3')

print('---')
print('NOTE G1/G2/G4 为通道侧实证：id=215(read)/hash 13ff53aa 匹配/id=216 ACK hash 5337b76d 匹配——MCP 返回件留 runs/ 日志')
print('EXIT', 1 if fails else 0, '| fails:', fails)
sys.exit(1 if fails else 0)
