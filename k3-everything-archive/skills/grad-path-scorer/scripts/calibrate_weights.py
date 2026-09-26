# --- K3 依赖预检（发行包注入：缺少依赖时显式报告缺失，并通过 exit 2 降级处理，不直接抛出 ImportError）---
import importlib.util as _ilu, sys as _sys
_k3_missing = [m for m in ['scipy', 'numpy'] if _ilu.find_spec(m) is None]
if _k3_missing:
    _sys.stderr.write("[K3 deps] 缺依赖 %s —— 请 pip install 后使用本脚本；包内其余技能不受影响\n" % _k3_missing)
    _sys.exit(2)
# --- K3 依赖预检完 ---

import json, sys, random, os
sys.path.insert(0, "<输出区>/grad-path-scorer/scripts")
import importlib, score_engine, dead_end_classifier
importlib.reload(score_engine); importlib.reload(dead_end_classifier)
from score_engine import score_school, DEFAULT_CONFIG
from dead_end_classifier import classify
from scipy.stats import spearmanr
import numpy as np

ANCHOR = {"中国科学技术大学":95,"华中科技大学":92,"清华大学":90,"合肥工业大学":88,"西安交通大学":85,
"西南交通大学":84,"兰州大学":82,"大连理工大学":80,"四川大学":78,"哈尔滨工程大学":76,"浙江大学":72,
"上海交通大学":70,"中山大学":70,"北京大学":68,"内蒙古科技大学":62,"北方民族大学":58,"南京航空航天大学":58,
"南昌大学":55,"南开大学":55,"华南理工大学":52,"中南大学":50,"宁夏大学":48,"太原理工大学":45,"山东大学":42,
"哈尔滨工业大学":40,"郑州大学":38,"新疆大学":35,"石河子大学":30,"南华大学":28,"西华大学":25,"东华理工大学":25}
BOTTOM = {"郑州大学":38,"哈尔滨工业大学":40,"南华大学":28,"东华理工大学":25}
# v2.3.4：输入路径参数化——原硬编码的 13 校 pilot 文件已随源会话沙箱遗失（经 2026-08-29 复盘证实），
# 位置参数显式供给；缺省路径不存在时给明确报错而非栈跟踪
_facts_path = sys.argv[1] if len(sys.argv) > 1 else "<输出区>/pilot_facts_13校.json"
if not os.path.exists(_facts_path):
    sys.exit("[输入缺失] %s 不存在——请传入重建件或用户面板：python3 calibrate_weights.py <facts.json>" % _facts_path)
facts = json.load(open(_facts_path, encoding="utf-8"))["schools"]
for s in facts: s.update(classify(s))
DIMS = ["phd","city","funding","platform","admission_risk"]
LO = {"phd":0.20,"city":0.05,"funding":0.05,"platform":0.10,"admission_risk":0.10}
HI = {"phd":0.45,"city":0.20,"funding":0.20,"platform":0.40,"admission_risk":0.22}

def evaluate(wv, mp, disc):
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    cfg["weights"] = {d: w for d, w in zip(DIMS, wv)}
    cfg["regret_curve"]["max_penalty"] = mp
    cfg["dead_end_discount"] = disc
    tot = {s["name"]: score_school(s, cfg, perturb=False)["total"] for s in facts}
    pairs = [(ANCHOR[k], tot[k2]) for k in ANCHOR for k2 in tot if k2.startswith(k)]
    rho = spearmanr([p[0] for p in pairs],[p[1] for p in pairs]).statistic
    bo = sum(max(0.0, tot[k2]-av-12.0) for k,av in BOTTOM.items() for k2 in tot if k2.startswith(k))
    mad = sum(abs(x-y) for x,y in pairs)/len(pairs)
    return rho - 0.03*bo - 0.002*mad, rho, mad, bo, tot

def sample():
    while True:
        v = np.random.dirichlet([3,1.2,1.2,2,1.5])
        if all(LO[d] <= v[i] <= HI[d] for i, d in enumerate(DIMS)): return v

random.seed(23); np.random.seed(23)
best = None
for it in range(40000):
    v = sample(); mp = random.choice([15,18,20,22,25,28,30])
    disc = random.choice([0.3,0.4,0.5,0.6,0.7])
    obj, rho, mad, bo, _ = evaluate(v.tolist(), mp, disc)
    if best is None or obj > best[0]:
        best = [obj, rho, mad, bo, v.tolist(), mp, disc]
print(f"采样 best: obj={best[0]:.4f} ρ={best[1]:.4f} MAD={best[2]:.2f} 托底超={best[3]:.2f} mp={best[5]} disc={best[6]}")

stall = 0; prev = best[0]; rnd = 0
while stall < 3 and rnd < 40:
    rnd += 1
    for i, d in enumerate(DIMS):
        for delta in (-0.03,-0.015,0.015,0.03):
            v = best[4][:]; v[i] += delta
            if not (LO[d] <= v[i] <= HI[d]): continue
            s_ = sum(v); v = [x/s_ for x in v]
            if not all(LO[dd_]-1e-9 <= v[j] <= HI[dd_]+1e-9 for j, dd_ in enumerate(DIMS)): continue
            for mp in {best[5]-2, best[5], best[5]+2}:
                for disc in {best[6]-0.1, best[6], best[6]+0.1}:
                    if mp < 10 or not (0.2 <= disc <= 0.9): continue
                    obj, rho, mad, bo, _ = evaluate(v, mp, disc)
                    if obj > best[0] + 1e-6: best = [obj, rho, mad, bo, v, mp, disc]
    if abs(best[0]-prev) < 0.005: stall += 1
    else: stall = 0
    prev = best[0]
print(f"收敛(轮{rnd}): 权重={dict((d,round(w,4)) for d,w in zip(DIMS,best[4]))}")
print(f"max_penalty={best[5]} dead_end_discount={best[6]} ρ={best[1]:.4f} MAD={best[2]:.2f} 托底超={best[3]:.2f}")
json.dump({"weights":{d:round(w,4) for d,w in zip(DIMS,best[4])},"max_penalty":best[5],
           "dead_end_discount":round(best[6],2),"rho":round(best[1],4),"mad":round(best[2],2)},
          open("/tmp/best_cfg3.json","w"), ensure_ascii=False)
