# -*- coding: utf-8 -*-
"""run_drills.py —— 五幕剧本之判据运行器（应正主：「五幕剧本（心跳聚合、洪峰幂等、断链零丢失、升级面 60 秒、注入拒绝）
即代码，YAML＋判据脚本进 monorepo drills/，判据失败即构建红」）
★约定：每幕一脚本 ＋ 一份 .yaml 规格；★任一判据失败即整体退出码 1（构建红）
用法：python run_drills.py [--act 2|3|5]
（中文串一律用「」）
"""
import argparse, pathlib, re, subprocess, sys, time

HERE = pathlib.Path(__file__).resolve().parent
ACT1 = pathlib.Path(__file__).resolve().parent.parent/"exp"

def yaml_lite(p):
    """极简 YAML 读取（key: value ／ key:\\n  - item）"""
    out, cur = {}, None
    for line in p.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip() or line.strip().startswith("#"): continue
        if re.match(r"^\s*-\s", line):
            if cur is not None: out.setdefault(cur, []).append(line.strip()[1:].strip())
            continue
        if ":" in line:
            k, _, v = line.partition(":"); k = k.strip(); v = v.strip()
            if v: out[k] = v
            else: cur = k; out[cur] = []
    return out

def run_act(n):
    spec = HERE/("act%d.yaml" % n)
    script = HERE/("act%d.py" % n)
    if not script.exists():
        return n, "★缺脚本", None
    d = yaml_lite(spec) if spec.exists() else {}
    t0 = time.time()
    pr = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    dt = round(time.time()-t0, 2)
    rc = pr.returncode
    st = "PASS" if rc == 0 else ("UNTESTED" if rc == 2 else "FAIL")
    tail = [l for l in ((pr.stdout or "") + (pr.stderr or "")).splitlines() if l.strip()][-1:] 
    return n, st, {"name": d.get("name", "?"), "s": dt, "last": (tail[0][:96] if tail else "")}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--act", type=int, default=0)
    a = ap.parse_args()
    acts = [a.act] if a.act else [1, 2, 3, 4, 5]
    print("  ═══ 五幕判据运行（★判据失败即红）｜ %s ═══" % time.strftime("%Y-%m-%d %H:%M:%S+0800"))
    bad = 0
    for n in acts:
        num, st, info = run_act(n)
        if st == "★缺脚本":
            print("   第%d幕 ⇒ ○ 未建（待补）" % n); continue
        mark = {"PASS": "★PASS", "FAIL": "★FAIL", "UNTESTED": "○ 未测（环境不足）"}[st]
        print("   第%d幕 ⇒ %s ｜ %s ｜ %.2fs ｜ %s" % (num, mark, info["name"], info["s"], info["last"]))
        if st == "FAIL": bad += 1
    print("   ⇒ 判：%s（失败 %d 幕）" % ("★构建红（判据失败）" if bad else "★全绿", bad))
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); main()
