#!/usr/bin/env python3
"""
card_linter.py — 定时任务卡规范检验器（cron-task-forge / 定时任务考官）
对一段定时任务卡文本做确定性体检。纯标准库，零依赖。

用法:
  python3 card_linter.py --name "任务名" --cron "0 4 * * 1" card.txt
  cat card.txt | python3 card_linter.py --cron "0 4 * * *"
  python3 card_linter.py --self-test          # 内置正反夹具自检

判定级别: FAIL(硬缺陷) / WARN(建议) / INFO(加分项)。verdict: 无 FAIL → PASS。
"""
import sys, re, json, argparse

NAME_MAX = 50        # Kimi 定时任务 UI 实测上限
BODY_MAX = 8000      # Kimi 定时任务 UI 实测上限


def parse_cron(expr):
    """五字段 cron 粗解析。返回 (kind, err)。kind ∈ daily/weekday/weekly/monthly/yearly/custom"""
    if not expr:
        return None, "未提供 cron 表达式（--cron）"
    f = expr.split()
    if len(f) != 5:
        return None, f"cron 须为五字段（分 时 日 月 周），实得 {len(f)} 段"
    field_re = re.compile(r'^[\d\*/,\-]+$')
    for seg in f:
        if not field_re.match(seg):
            return None, f"字段含非法字符: {seg}"
    minute, hour, dom, month, dow = f
    if month != '*':
        return ('yearly' if dom != '*' else 'custom'), None
    if dom != '*':
        return 'monthly', None
    if dow == '*':
        return 'daily', None
    if dow in ('1-5', '1,2,3,4,5'):
        return 'weekday', None
    if re.match(r'^\d$', dow) or re.match(r'^\d(,\d)+$', dow):
        return 'weekly', None
    return 'custom', None


CLAIMS = [  # (文本字样, 要求的调度种类, 兼容种类)
    (('每日', '每天'), 'daily', ()),
    (('工作日',), 'weekday', ()),
    (('每周', '周一', '周二', '周三', '周四', '周五', '周六', '周日'), 'weekly', ()),
    (('每月', '月度'), 'monthly', ()),
]


def lint(text, name=None, cron=None):
    issues = []  # (level, code, msg)

    # C1 名称长度
    if name is not None and len(name) > NAME_MAX:
        issues.append(('FAIL', 'C1', f'名称 {len(name)} 字超上限 {NAME_MAX}'))

    # C2 正文长度
    if len(text) > BODY_MAX:
        issues.append(('FAIL', 'C2', f'正文 {len(text)} 字超上限 {BODY_MAX}'))

    # C3 cron 合法性 + C4 措辞与调度一致
    kind, err = parse_cron(cron)
    if err:
        issues.append(('FAIL', 'C3', err))
    else:
        for words, need, compat in CLAIMS:
            if any(w in text for w in words) and kind != need and kind not in compat:
                # 「每日自检」字样 vs 实际 weekly → 硬冲突
                issues.append(('FAIL', 'C4',
                    f'措辞与调度不一致：正文含「{words[0]}」但 cron「{cron}」解析为 {kind}'))
        if kind == 'daily' and any(w in text for w in ('工作日', '每周')):
            issues.append(('FAIL', 'C4', f'措辞与调度不一致：cron 为 daily 但正文含工作日/每周字样'))

    # C5 反幻觉条款（核验为真 / 缺测声明）
    if not (('核验' in text) and ('缺测' in text or '如实' in text or '为真' in text)):
        issues.append(('FAIL', 'C5',
            '缺反幻觉条款：须含「只汇报（磁盘）核验为真的事实，缺测即标缺测」类明示'))

    # C6 异常如实报告条款
    if not ('异常' in text and ('如实' in text or '修复路径' in text or '不假装' in text)):
        issues.append(('FAIL', 'C6',
            '缺异常处置条款：须含「发现异常→如实报告并给出修复路径，不假装正常」类明示'))

    # C7 绝对路径自包含（纯检索任务豁免，降级 WARN）
    if not re.search(r'/mnt/|/app/|[A-Za-z]:\\', text):
        issues.append(('WARN', 'C7', '未检出绝对路径锚点——纯检索类可豁免，有文件产物的任务必须给绝对路径'))

    # C8 挂账/到期项须带时间或条件
    if ('挂账' in text or '到期' in text) and not re.search(r'\d{4}\s*年|\d{4}-|季度|周[一二三四五六日]|\d+\s*月|恢复|到期', text):
        issues.append(('WARN', 'C8', '提及挂账/到期但未检出时间或触发条件'))

    # C9 列表可读身份标签
    if not text.lstrip().startswith('【'):
        issues.append(('WARN', 'C9', '建议首行以【项目·任务】标签开头（定时任务列表只显示前缀）'))

    # C10 环境重建降级路径（加分项）
    if ('重建' in text or '降级' in text) and ('pip install' in text or 'git init' in text or '恢复' in text):
        issues.append(('INFO', 'C10', '含环境重建/降级路径说明 ✓'))

    verdict = 'PASS' if not any(l == 'FAIL' for l, _, _ in issues) else 'FAIL'
    return {'verdict': verdict, 'cron_kind': kind, 'issues': issues}


GOOD = """【示范·每日自检】请按序执行并核验：
1. ls 核验台账存在：<输出区>/demo/data/schools.json；交接文档 <上传区>/handoff.md。
2. cd <输出区>/demo && git status；VERSION 应为 v1.0.0。沙箱重置丢 pytest/git 时先重建（pip install -q pytest；git init）。
3. pytest 快速门禁：python3 -m pytest tests/test_engine.py -q。
4. 检查挂账是否到期可推进：①9月简章季复查（2026-09）。
5. 新增成果确认落库 <输出区> 与 <上传区> 双保险；防AI幻觉：只汇报磁盘核验为真的事实，缺测即标缺测。
发现异常（文件缺失/测试红/git丢失）→ 如实报告并给出修复路径，不假装正常。"""

BAD_WEEKLY_DAILY = ("【坏卡】每日自检：ls <输出区>/demo 核验，只汇报磁盘核验为真的事实，缺测即标缺测；发现异常如实报告并给出修复路径。",
                    '0 4 * * 1')  # 每周一却写每日 → C4 FAIL
BAD_NO_CLAUSE = ("【坏卡2】每天看看 <输出区>/demo 有没有问题。",
                 '0 4 * * *')  # 缺反幻觉+异常条款 → C5/C6 FAIL
BAD_LONG_NAME = ('x', '0 4 * * *')  # 名称超长走 self-test 直接构造

def self_test():
    cases = [
        ('好卡（每日措辞+每日调度）', GOOD, '示范·每日自检', '0 4 * * *', 'PASS'),
        ('坏卡：每日措辞+周一调度', BAD_WEEKLY_DAILY[0], '坏卡', BAD_WEEKLY_DAILY[1], 'FAIL'),
        ('坏卡：缺反幻觉/异常条款', BAD_NO_CLAUSE[0], '坏卡2', BAD_NO_CLAUSE[1], 'FAIL'),
        ('坏卡：名称超长', GOOD, '名' * 51, '0 4 * * *', 'FAIL'),
        ('坏卡：cron 四字段', GOOD, '示范', '0 4 * *', 'FAIL'),
    ]
    ok = True
    for label, text, name, cron, expect in cases:
        got = lint(text, name, cron)['verdict']
        passed = got == expect
        ok &= passed
        print(f"[{'PASS' if passed else 'FAIL'}] {label} → 期望 {expect} 实得 {got}", file=sys.stderr)
    print(f"[SELF-TEST {'OK' if ok else 'FAIL'}] {len(cases)} 用例", file=sys.stderr)
    return ok


def main():
    ap = argparse.ArgumentParser(description='定时任务卡规范检验器')
    ap.add_argument('card', nargs='?', help='任务卡文本文件（缺省读 stdin）')
    ap.add_argument('--name', default=None, help='任务名称（测长度上限）')
    ap.add_argument('--cron', default=None, help='cron 五字段表达式（测措辞-调度一致）')
    ap.add_argument('--self-test', action='store_true')
    args = ap.parse_args()
    if args.self_test:
        sys.exit(0 if self_test() else 1)
    text = open(args.card, encoding='utf-8').read() if args.card else sys.stdin.read()
    rep = lint(text, args.name, args.cron)
    for level, code, msg in rep['issues']:
        print(f"[{level}] {code} {msg}", file=sys.stderr)
    print(json.dumps({'verdict': rep['verdict'], 'cron_kind': rep['cron_kind'],
                      'fail': sum(1 for i in rep['issues'] if i[0] == 'FAIL'),
                      'warn': sum(1 for i in rep['issues'] if i[0] == 'WARN')},
                     ensure_ascii=False))
    sys.exit(0 if rep['verdict'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
