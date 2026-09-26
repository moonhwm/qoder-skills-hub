#!/usr/bin/env python3
"""安装核验器：按 MANIFEST.json 逐文件 md5 核验（纯标准库，跨平台）。"""
import json,hashlib,sys,os,argparse
ap=argparse.ArgumentParser()
ap.add_argument("--target",required=True); ap.add_argument("--manifest",required=True)
a=ap.parse_args()
man=json.load(open(a.manifest,encoding='utf-8'))
missing=mismatch=ok=0
for skill,info in man["skills"].items():
    for e in info["entries"]:
        fp=os.path.join(a.target,skill,e["path"])
        if not os.path.exists(fp): missing+=1; print("MISSING:",skill,e["path"]); continue
        if hashlib.md5(open(fp,'rb').read()).hexdigest()!=e["md5"]:
            mismatch+=1; print("MISMATCH:",skill,e["path"]); continue
        ok+=1
print(f"verify: ok={ok} missing={missing} mismatch={mismatch}")
sys.exit(0 if missing==0 and mismatch==0 else 1)
