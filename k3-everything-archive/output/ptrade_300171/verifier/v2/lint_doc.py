#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Retail-facing doc linter (verifier v2).
Usage: python3 lint_doc.py <doc.md>  -> exit 0 PASS / 1 FAIL
"""
import re
import sys

FORBIDDEN = ['稳赚', '保本', '包赚', '承诺收益', '无风险', '必涨', '躺赚']
REQUIRED_SECTIONS = ['入场', '仓位', '出场', '风控', '风险']
MIN_CHARS, MAX_CHARS = 1500, 6000

errors = []


def main(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    # A1 forbidden promise words
    for w in FORBIDDEN:
        if w in text:
            errors.append('A1: forbidden promise word "%s" found' % w)

    # A2 risk disclosure
    if '不构成投资建议' not in text:
        errors.append('A2: missing "不构成投资建议" risk disclosure')

    # A3 glossary
    if '名词' not in text and '术语' not in text and '小词典' not in text:
        errors.append('A3: missing glossary section (名词/术语/小词典)')

    # B4 required sections
    for s in REQUIRED_SECTIONS:
        if s not in text:
            errors.append('B4: missing section keyword "%s"' % s)

    # B5 length (count CJK chars + ascii words roughly)
    n = len(re.sub(r'\s', '', text))
    if n < MIN_CHARS or n > MAX_CHARS:
        errors.append('B5: length %d chars outside [%d, %d]' % (n, MIN_CHARS, MAX_CHARS))

    # B6 at least one numeric worked example (percent + shares or 元)
    if not (re.search(r'\d+\s*股', text) and re.search(r'\d+(\.\d+)?\s*[%元]', text)):
        errors.append('B6: missing concrete numeric worked example (股 + %/元)')

    print('=== doc lint: %s ===' % path)
    for e in errors:
        print('ERROR: %s' % e)
    if errors:
        print('RESULT: FAIL (%d errors)' % len(errors))
        return 1
    print('RESULT: PASS (chars=%d)' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
