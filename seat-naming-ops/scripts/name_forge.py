#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""name_forge.py 批量授名生成器（seat-naming-ops）

典池×姓氏池→音韵闸过滤→去重→截 N 行，输出 JSONL。
铁律：生成器不创造典池条目——典池只能来自 references/canon-pool.md 人工验证流程。

用法:
  python3 name_forge.py --canon ../assets/canon-seed.json \
      --surnames ../assets/surnames-65.json --n 1000 --out bank.jsonl
退出码: 0=成功；2=参数错误；3=可产量不足 N（产物仍写出，stderr 报缺额）。
碰撞拦截：默认读 --canon 同目录 collision-blocklist.json（姓+名级策展拦截表），
拦截命中即剔且留痕计数；表不存在则跳过（口径=音韵闸之后、入池之前）。
"""
import sys, json, os, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from name_audit import parse_pinyin, audit  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--canon", required=True, help="典池种子 JSON（人工验证条目）")
    ap.add_argument("--surnames", required=True, help="姓氏池 JSON")
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--out", required=True)
    ap.add_argument("--orthogonal", action="store_true", help="正交均衡抽样（边际均匀+配对去相关）")
    ap.add_argument("--seed", type=int, default=20260916, help="正交模式随机种子（确定性可复现）")
    a = ap.parse_args()

    canon = json.load(open(a.canon, encoding="utf-8"))
    surnames = json.load(open(a.surnames, encoding="utf-8"))
    # 复姓池自动并入（assets/surnames-compound.json 存在即启用；接合判据由 name_audit surname_len 重映射）
    cp_path = os.path.join(os.path.dirname(os.path.abspath(a.surnames)), "surnames-compound.json")
    compound_n = 0
    if os.path.exists(cp_path):
        extra = json.load(open(cp_path, encoding="utf-8"))
        compound_n = len(extra)
        surnames = surnames + extra
    bl_path = os.path.join(os.path.dirname(os.path.abspath(a.canon)), "collision-blocklist.json")
    blocked, ming_watch, surname_watch = set(), {}, {}
    if os.path.exists(bl_path):
        bl = json.load(open(bl_path, encoding="utf-8"))
        blocked = {(b["surname"], b["ming"]) for b in bl["blocked"]}
        ming_watch = {w["ming"]: w["reason"] for w in bl.get("ming_watch", [])}
        surname_watch = {w["surname"]: w["pun"] for w in bl.get("surname_watch", [])}
    seen, passed = set(), []
    fail_hist = {"R1": 0, "R2": 0, "R3": 0, "R4": 0, "R5a": 0, "R5b": 0}  # 六判据全量列出，零命中亦留痕
    failed_uniq = 0
    blocked_hit = 0
    total = 0
    for e in canon:  # 典池主序：同一名遍历诸姓，先求全量过闸池
        for s in surnames:
            total += 1
            full = s["surname"] + e["ming"]
            pin = "%s %s" % (s["pinyin"], e["ming_pinyin"])
            key = (s["surname"], e["ming"], e["zi"])
            if key in seen:
                continue
            verdict, fails, notes = audit(full, parse_pinyin(pin), surname_len=len(s["surname"]))
            if verdict == "FAIL":
                failed_uniq += 1
                for f in fails:
                    fail_hist[f.split(" ")[0]] = fail_hist.get(f.split(" ")[0], 0) + 1
                continue
            if (s["surname"], e["ming"]) in blocked:  # 碰撞拦截（音韵闸之后、入池之前）
                blocked_hit += 1
                continue
            seen.add(key)
            if e["ming"] in ming_watch:  # W1 字级碰撞观察名单（不拦截，注记人工复核；reason 尾缀去重）
                _r = ming_watch[e["ming"]]
                _n = "W1 字级碰撞登记(%s)" % _r if _r.endswith("人工复核") else "W1 字级碰撞登记(%s，交付前人工复核)" % _r
                notes = [_n] + notes
            if s["surname"] in surname_watch:  # W2 警示姓回读（不拦截，机器标记人工朗读）
                notes = ["W2 警示姓回读(%s/%s类，人工朗读兜底)" % (s["surname"], surname_watch[s["surname"]])] + notes
            # W3 语义回读词库（assets/semantic-watch.json 双音负义组合，不拦截只标记）
            sw_path = os.path.join(os.path.dirname(os.path.abspath(a.canon)), "semantic-watch.json")
            if os.path.exists(sw_path):
                for bg in json.load(open(sw_path, encoding="utf-8"))["bigrams"]:
                    toks = pin.split()
                    joint = len(s["pinyin"].split()) - 1  # 姓×名接合对索引
                    for k in range(joint, len(toks) - 1):  # 复姓内部二字不扫（scope=接合+名内）
                        if k == joint and s["surname"] in surname_watch:
                            continue  # 警示姓接合回读由 W2 整姓覆盖，W3 不重复标记（分工口径）
                        if toks[k] == bg[0] and toks[k + 1] == bg[1]:
                            notes = ["W3 语义回读命中(%s=%s，人工复核)" % (toks[k] + " " + toks[k + 1], bg[2])] + notes
            tones = [p[2] for p in parse_pinyin(pin)]
            passed.append({
                "id": 0,
                "surname": s["surname"], "ming": e["ming"], "zi": e["zi"],
                "full_name": full,
                "pinyin": pin, "tones": tones,
                "tone_pattern": "-".join(map(str, tones)),
                "source_verse": e["source_verse"], "poem": e["poem"],
                "pair_rule": e["pair_rule"],
                "notes": notes,
            })

    if a.orthogonal:
        # 正交均衡抽样（充分正交/完备）：池位网格上做轮换调度——
        # 以过闸池的 (姓,名) 可用性为约束，典目每圈乱序、姓氏每圈独立乱序，
        # 使每名出现 ⌊n/名数⌋ 或 ⌈n/名数⌉ 次、每姓同理，(姓,名) 配对去相关。
        import random as _rnd
        rng = _rnd.Random(a.seed)
        by_pair = {(r["surname"], r["ming"]): r for r in passed}
        mings = sorted({e["ming"] for e in canon})
        surn_list = [s["surname"] for s in surnames]
        avail = {(r["surname"], r["ming"]) for r in passed}
        rows, used = [], set()
        n = min(a.n, len(passed))
        sn_use = {sn: 0 for sn in surn_list}
        while len(rows) < n:
            before = len(rows)
            rng.shuffle(mings)
            for m in mings:
                if len(rows) >= n:
                    break
                cands = [sn for sn in surn_list if (sn, m) in avail and (sn, m) not in used]
                if not cands:
                    continue  # 该名池位用尽（完备性下不阻塞，名配额让渡）
                least = min(sn_use[sn] for sn in cands)
                tier = [sn for sn in cands if sn_use[sn] == least]  # 贪心最小用量层：姓边际均衡
                sn = rng.choice(tier)
                sn_use[sn] += 1
                used.add((sn, m))
                rows.append(by_pair[(sn, m)])
            if len(rows) == before:
                sys.stderr.write("正交调度退化：本轮零新增，已产出 %d/%d（池位耗尽守卫，C23）\n" % (len(rows), n))
                break
    else:
        # 均匀分层抽取：stride 取样覆盖全部典池条目与多数姓氏（确定性、可复现）
        n = min(a.n, len(passed))
        if n == len(passed):
            rows = passed
        else:
            idxs = sorted({i * len(passed) // n for i in range(n)})
            rows = [passed[i] for i in idxs]
    for i, r in enumerate(rows):
        r["id"] = i + 1

    with open(a.out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    uniq = len({(r["surname"], r["ming"], r["zi"]) for r in rows})
    mings_cov = len({r["ming"] for r in rows})
    surn_cov = len({r["surname"] for r in rows})
    print("总组合=%d 过闸池=%d 抽取=%d 去重校验=%s 名覆盖=%d/%d 姓覆盖=%d/%d" % (
        total, len(passed), len(rows), "OK" if uniq == len(rows) else "DUP!",
        mings_cov, len(canon), surn_cov, len(surnames)))
    print("剪枝分布(FAIL 规则命中数，一组合可中多规则；R5b 零命中亦列出): %s" % json.dumps(fail_hist, ensure_ascii=False, sort_keys=True))
    print("剪枝口径：唯一被剪组合=%d；规则命中合计=%d（命中和>唯一数属正常重叠）；过闸池=总组合-唯一被剪-碰撞拦截=%d" % (
        failed_uniq, sum(fail_hist.values()), total - failed_uniq - blocked_hit))
    print("碰撞拦截：拦截表条目=%d 命中剔除=%d；W1观察名单=%d W2警示姓=%d（collision-blocklist.json，策展性最小集非穷尽库）" % (
        len(blocked), blocked_hit, len(ming_watch), len(surname_watch)))
    if compound_n:
        print("复姓池并入：%d 姓（surnames-compound.json），总姓氏=%d" % (compound_n, len(surnames)))
    if len(rows) < a.n:
        sys.stderr.write("可产量不足：得 %d / 求 %d，缺 %d（如实报缺，禁凑数）\n" % (len(rows), a.n, a.n - len(rows)))
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
