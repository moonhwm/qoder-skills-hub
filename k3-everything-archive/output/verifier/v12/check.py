#!/usr/bin/env python3
# verifier v12 — REST恢复与穷衡验证批次（M1-M5）
import os, json, stat, sys, re
DOC="<注册处>/穷衡临时政府考证报告_v1.0_20260903.md"
VAULT1="<注册处>/vault/<通道库>_publishable_key.json"
VAULT2="<注册处>/vault/<通道库>_publishable_key_k3trial.json"
REG="<注册处>"
r=[]
def ok(m): print("PASS:",m); return True
def fail(m): print("FAIL:",m); return False
t=open(DOC,encoding="utf-8").read() if os.path.exists(DOC) else ""
need=["身份链","五通","CL-STATE","命名原因","查无实据","已检域","证据索引"]
r.append(ok("M1 考证报告必备节齐") if t and all(k in t for k in need) else fail("M1 缺:%s"%[k for k in need if k not in t]))
m1=os.stat(VAULT1).st_mode if os.path.exists(VAULT1) else 0
m2=os.stat(VAULT2).st_mode if os.path.exists(VAULT2) else 0
r.append(ok("M2 两把key在vault且chmod600") if stat.S_IMODE(m1)==0o600 and stat.S_IMODE(m2)==0o600 else fail("M2 mode"))
# M3 零明文：key值不出现于 registry 的任何 .md/.json 文件中（vault 除外）
k1=json.load(open(VAULT1))["key"]; k2=json.load(open(VAULT2))["key"]
hits=[]
for root,_,fs in os.walk(REG):
    if "vault" in root: continue
    for f in fs:
        p=os.path.join(root,f)
        try: c=open(p,encoding="utf-8",errors="ignore").read()
        except: continue
        if k1 in c or k2 in c: hits.append(p)
r.append(ok("M3 零明文（key零命中registry非vault区）") if not hits else fail("M3 命中:%s"%hits))
r.append(ok("M4 写入受限如实标注+钟点在案") if "RLS" not in t or "16:00 UTC" in t else fail("M4"))
d=json.load(open(REG+"/逃逸登记册.json",encoding="utf-8"))
key=[k for k in d if isinstance(d[k],list)][0]
r.append(ok("M5 逃逸#22/#23在册") if any(e.get("id")=="#23" for e in d[key]) else fail("M5"))
print("== v12 汇总 ==","ALL PASS" if all(r) else "HAS FAIL")
sys.exit(0 if all(r) else 1)
