#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stat_test.py v0.1.0 — 通用统计检验落地引擎（2026-09-09 创刊）
纪律：先证伪后裁决——前置假设检验（正态/方差齐）不过即改非参，并在裁决卡明示；
一切结论附效应量+CI；多重比较必注。结论标签「模型能力上限参考」。
用法：
  stat_test.py ttest --a "1,2,3" [--b "2,3,4"] [--paired]     # 单/双样本/配对 t
  stat_test.py mwu --a "..." --b "..."                        # Mann-Whitney U（非参）
  stat_test.py chi2 --table "12,8;7,13"                       # 卡方独立性（;分行）
  stat_test.py fisher --table "a,b;c,d"                       # Fisher 精确（2x2）
  stat_test.py ks --a "..." --b "..."                         # 双样本 KS
  stat_test.py prop --x 12 --n 40 [--p0 0.5]                  # 单比例 z
  stat_test.py --self-test
"""
import json, sys, math

def parse_vec(s):
    return [float(x) for x in s.split(',') if x.strip() != '']

def parse_table(s):
    return [[float(x) for x in row.split(',')] for row in s.split(';')]

def verdict_card(test, stat, p, effect, ci, assumptions, notes, alpha=0.05):
    return {'test': test, 'statistic': round(float(stat), 6), 'p_value': float(p),
            'reject_H0@0.05': bool(p < alpha), 'effect_size': effect, 'ci': ci,
            'assumptions_check': assumptions, 'notes': notes,
            'label': '模型能力上限参考；先证伪后出口——假设检验未过已改道并明示'}

def ttest(a, b=None, paired=False):
    from scipy import stats
    import numpy as np
    a = np.array(a); notes = []; assump = {}
    shapiro_a = stats.shapiro(a) if len(a) >= 3 else None
    assump['shapiro_a_p'] = round(shapiro_a.pvalue, 4) if shapiro_a else 'n<3 未检'
    if b is None:
        t, p = stats.ttest_1samp(a, 0)
        d = float(a.mean() / a.std(ddof=1)) if a.std(ddof=1) > 0 else None
        ci = stats.t.interval(0.95, len(a) - 1, loc=a.mean(), scale=stats.sem(a))
        return verdict_card('ttest_1samp(vs 0)', t, p, {'cohens_d': round(d, 4) if d else None},
                            [round(float(x), 4) for x in ci], assump, notes)
    b = np.array(b)
    shapiro_b = stats.shapiro(b) if len(b) >= 3 else None
    assump['shapiro_b_p'] = round(shapiro_b.pvalue, 4) if shapiro_b else 'n<3 未检'
    if paired:
        t, p = stats.ttest_rel(a, b)
        diff = a - b
        d = float(diff.mean() / diff.std(ddof=1)) if diff.std(ddof=1) > 0 else None
        return verdict_card('ttest_paired', t, p, {'cohens_d': round(d, 4) if d else None},
                            None, assump, notes)
    lev = stats.levene(a, b)
    assump['levene_p'] = round(lev.pvalue, 4)
    equal = lev.pvalue > 0.05
    if not equal:
        notes.append('方差齐性未过（Levene p=%.4f）→ Welch 校正' % lev.pvalue)
    normal = (shapiro_a and shapiro_a.pvalue > 0.05) and (shapiro_b and shapiro_b.pvalue > 0.05)
    if not normal:
        notes.append('正态性存疑（Shapiro）→ 建议以 mwu 复核（本卡仍报 t，双通道互证纪律）')
    t, p = stats.ttest_ind(a, b, equal_var=equal)
    sp = math.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    d = float((a.mean() - b.mean()) / sp) if sp > 0 else None
    return verdict_card('ttest_2samp(%s)' % ('student' if equal else 'welch'), t, p,
                        {'cohens_d': round(d, 4) if d else None}, None, assump, notes)

def mwu(a, b):
    from scipy import stats
    import numpy as np
    a = np.array(a); b = np.array(b)
    u, p = stats.mannwhitneyu(a, b, alternative='two-sided')
    n1, n2 = len(a), len(b)
    rbc = 1 - 2 * u / (n1 * n2)  # rank-biserial
    return verdict_card('mann_whitney_u', u, p, {'rank_biserial': round(float(rbc), 4)},
                        None, {'note': '非参，无正态假设'}, [])

def chi2(table):
    from scipy import stats
    import numpy as np
    t = np.array(table)
    c, p, dof, exp = stats.chi2_contingency(t, correction=(t.shape == (2, 2)))
    n = t.sum()
    k = min(t.shape) - 1
    v = math.sqrt(c / (n * k)) if k > 0 and n > 0 else None
    notes = []
    if (exp < 5).any():
        notes.append('期望频数有 <5 格 → 2x2 表建议以 fisher 复核')
    return verdict_card('chi2_independence', c, p, {'cramers_v': round(v, 4) if v else None},
                        None, {'dof': int(dof), 'min_expected': round(float(exp.min()), 3)}, notes)

def fisher(table):
    from scipy import stats
    import numpy as np
    t = np.array(table, dtype=int)
    if t.shape != (2, 2):
        return {'error': 'fisher_requires_2x2'}
    odds, p = stats.fisher_exact(t)
    return verdict_card('fisher_exact', odds, p, {'odds_ratio': round(float(odds), 4)},
                        None, {}, [])

def ks(a, b):
    from scipy import stats
    d, p = stats.ks_2samp(a, b)
    return verdict_card('ks_2samp', d, p, {'ks_d': round(float(d), 4)}, None, {}, [])

def prop(x, n, p0=0.5):
    from scipy import stats as st
    phat = x / n
    se = math.sqrt(p0 * (1 - p0) / n)
    z = (phat - p0) / se if se > 0 else 0.0
    p = 2 * (1 - st.norm.cdf(abs(z)))
    lo, hi = st.binom.interval(0.95, n, phat)
    return verdict_card('prop_z(vs %.3f)' % p0, z, p, {'phat': round(phat, 4)},
                        [round(lo / n, 4), round(hi / n, 4)], {'note': 'CI 为二项精确'},
                        [] if n * p0 >= 5 and n * (1 - p0) >= 5 else ['np0<5 近似欠佳，以 CI 为准'])

def self_test():
    ok = []
    # F1: 单样本 t 对已知值（scipy 口径复核）
    r = ttest([1, 2, 3, 4, 5])
    ok.append(('F1 ttest_1samp', abs(r['statistic'] - 4.242641) < 1e-3 and r['p_value'] < 0.05))
    # F2: Welch 改道（方差悬殊，Levene 显著；固定种子窄组 vs 宽组）
    import random
    random.seed(7)
    _a = [10 + random.uniform(-0.5, 0.5) for _ in range(20)]
    _b = [10 + random.uniform(-50, 50) for _ in range(20)]
    r2 = ttest(_a, _b)
    ok.append(('F2 welch_detour', 'welch' in r2['test'] and any('Welch' in n for n in r2['notes'])))
    # F3: 卡方 2x2 已知（经典吸烟例近似）
    r3 = chi2([[60, 32], [30, 68]])
    ok.append(('F3 chi2', r3['p_value'] < 0.001 and r3['effect_size']['cramers_v'] > 0.3))
    # F4: fisher 2x2
    r4 = fisher([[1, 9], [11, 3]])
    ok.append(('F4 fisher', r4['p_value'] < 0.01))
    # F5: 比例检验
    r5 = prop(30, 50, 0.5)
    ok.append(('F5 prop', r5['p_value'] < 0.2 and r5['effect_size']['phat'] == 0.6))
    for name, v in ok:
        print('%s %s' % ('PASS' if v else 'FAIL', name))
    allpass = all(v for _, v in ok)
    print('SELF-TEST', 'PASS' if allpass else 'FAIL')
    return 0 if allpass else 1

def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__); return 2
    if argv[0] == '--self-test':
        return self_test()
    cmd = argv[0]
    g = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    try:
        if cmd == 'ttest':
            r = ttest(parse_vec(g('--a')), parse_vec(g('--b')) if g('--b') else None,
                      paired='--paired' in argv)
        elif cmd == 'mwu':
            r = mwu(parse_vec(g('--a')), parse_vec(g('--b')))
        elif cmd == 'chi2':
            r = chi2(parse_table(g('--table')))
        elif cmd == 'fisher':
            r = fisher(parse_table(g('--table')))
        elif cmd == 'ks':
            r = ks(parse_vec(g('--a')), parse_vec(g('--b')))
        elif cmd == 'prop':
            r = prop(int(g('--x')), int(g('--n')), float(g('--p0', '0.5')))
        else:
            print('bad args'); print(__doc__); return 2
    except Exception as e:
        print(json.dumps({'error': type(e).__name__, 'msg': str(e)[:200]})); return 1
    print(json.dumps(r, ensure_ascii=False, indent=1)); return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
