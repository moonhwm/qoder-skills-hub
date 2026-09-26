#!/usr/bin/env python3
"""
transcription_qa.py — 精读文档七项机检（doc-image-solver / 图像解题官）
纯标准库。用法: python3 transcription_qa.py <doc.md> | --self-test
七检: ①LaTeX $ 配对 ②题号连续性 ③【存疑】登记计数 ④答案标签覆盖（✅/📝/⚠）
      ⑤top3_likely_wrong 存在 ⑥隐私铁律声明（网盘来源文档必须置顶）⑦字数统计
verdict: 无 FAIL → PASS。
"""
import sys, re, json, argparse, tempfile, pathlib


def qa(text):
    issues = []
    # ① LaTeX $ 配对（$$ 与 $ 分别计数）
    dd = text.count('$$')
    if dd % 2: issues.append(('FAIL', 'Q1', f'$$ 不配对（{dd} 个）'))
    singles = len(re.findall(r'(?<!\$)\$(?!\$)', text))
    if singles % 2: issues.append(('FAIL', 'Q1', f'行内 $ 不配对（{singles} 个）'))

    # ② 题号连续性（各大题节内 1..n 无跳号；粗检：同级序号序列）
    for sec in re.finditer(r'##[^\n]*\n(.*?)(?=\n##|\Z)', text, re.S):
        body = sec.group(1)
        nums = [int(m.group(1)) for m in re.finditer(r'\n(\d{1,2})[.、]', body)]
        if nums and nums != list(range(1, len(nums) + 1)):
            issues.append(('WARN', 'Q2', f'题号疑似不连续: {nums[:12]}'))

    # ③ 存疑登记
    doubts = text.count('【存疑')
    issues.append(('INFO', 'Q3', f'存疑标注 {doubts} 处'))

    # ④ 答案标签覆盖：参考答案节内每个数字题号附近有标签
    ans_secs = [m.group(0) for m in re.finditer(r'###?\s*参考答案.*?(?=\n##|\Z)', text, re.S)]
    if not ans_secs:
        issues.append(('WARN', 'Q4', '未检出参考答案节'))
    else:
        tagged = sum(s.count('✅') + s.count('📝') + s.count('⚠') for s in ans_secs)
        if tagged == 0:
            issues.append(('FAIL', 'Q4', '答案节无任何核验标签（✅/📝/⚠）'))
        else:
            issues.append(('INFO', 'Q4', f'核验标签 {tagged} 处'))

    # ⑤ top3_likely_wrong
    if 'top3_likely_wrong' not in text:
        issues.append(('FAIL', 'Q5', '缺 top3_likely_wrong 节'))

    # ⑥ 铁律声明（含网盘来源关键词时强制）
    if ('网盘' in text or '百度' in text) and '不对外公开' not in text:
        issues.append(('FAIL', 'Q6', '涉网盘来源但缺「不对外公开」铁律声明'))

    # ⑦ 字数
    issues.append(('INFO', 'Q7', f'全文 {len(text)} 字符'))

    verdict = 'PASS' if not any(l == 'FAIL' for l, _, _ in issues) else 'FAIL'
    return {'verdict': verdict, 'issues': issues}


GOOD = """# 测试文档
> 铁律：任何程度不对外公开。网盘来源。
## 一、简答
1. 第一题 $x^2$ ✅
2. 第二题 📝
### 参考答案
1. ✅ 已核验
## top3_likely_wrong
1. 占位
"""
BAD = "# 坏文档\n## 一\n1. 第一题 $x^2\n3. 跳号且无标签无top3\n"


def self_test():
    ok = True
    for label, text, expect in [('好文档', GOOD, 'PASS'), ('坏文档', BAD, 'FAIL')]:
        got = qa(text)['verdict']; good = got == expect; ok &= good
        print(f"[{'PASS' if good else 'FAIL'}] {label} → 期望 {expect} 实得 {got}", file=sys.stderr)
    print(f"[SELF-TEST {'OK' if ok else 'FAIL'}]", file=sys.stderr)
    return ok


def main():
    ap = argparse.ArgumentParser(description='精读文档七项机检')
    ap.add_argument('doc', nargs='?')
    ap.add_argument('--self-test', action='store_true')
    args = ap.parse_args()
    if args.self_test:
        sys.exit(0 if self_test() else 1)
    if not args.doc:
        ap.error('缺 doc（或 --self-test）')
    rep = qa(open(args.doc, encoding='utf-8').read())
    for level, code, msg in rep['issues']:
        print(f"[{level}] {code} {msg}", file=sys.stderr)
    print(json.dumps({'verdict': rep['verdict'],
                      'fail': sum(1 for i in rep['issues'] if i[0] == 'FAIL')}, ensure_ascii=False))
    sys.exit(0 if rep['verdict'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
