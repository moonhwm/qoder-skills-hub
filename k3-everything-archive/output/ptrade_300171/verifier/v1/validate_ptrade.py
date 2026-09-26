#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PTrade strategy static validator (verifier v1).

Usage: python3 validate_ptrade.py <strategy.py>
Exit 0 = PASS (no ERROR). Exit 1 = FAIL. WARNs do not fail but are reported.
"""
import ast
import difflib
import re
import sys

ALLOWED_IMPORTS = {
    'numpy', 'np', 'pandas', 'pd', 'math', 'datetime', 'talib',
}
FORBIDDEN_NAMES = {'open', 'eval', 'exec', 'compile', '__import__', 'input'}

# Known PTrade API names (spelling reference table)
PTRADE_APIS = [
    # trading / orders
    'order', 'order_value', 'order_target', 'order_target_value',
    'order_market', 'cancel_order', 'cancel_order_param', 'get_orders',
    'get_open_orders', 'get_order', 'get_trades',
    # data
    'get_history', 'get_fundamentals', 'get_snapshot', 'get_stock_name',
    'get_stock_info', 'get_stock_status', 'get_trade_name', 'get_index_stocks',
    'get_industry_stocks', 'get_stock_blocks', 'get_block_stocks',
    'get_market_snapshot', 'get_price', 'get_current_tick',
    'get_user_name', 'get_research_path', 'is_trade',
    # portfolio / position
    'get_position', 'get_positions',
    # config / scheduling
    'set_universe', 'get_universe', 'set_benchmark', 'set_fixed_slippage',
    'set_commission', 'set_slippage', 'set_limit_mode', 'set_volume_ratio',
    'set_yesterday_position', 'run_daily', 'run_interval', 'run_monthly',
    'run_weekly', 'log', 'send_email', 'send_message',
    # event functions
    'initialize', 'handle_data', 'before_trading_start', 'after_trading_end',
    'tick_data', 'on_order_response', 'on_trade_response', 'handle_tick',
    # misc
    'get_datetime', 'get_backtest_date', 'set_option', 'set_parameters',
]

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def main(path):
    if not path.endswith('.py'):
        err('B2: file suffix must be .py: %s' % path)

    with open(path, 'r', encoding='utf-8') as f:
        src = f.read()

    # A1: Python 3.5 grammar compatibility
    tree = None
    try:
        tree = ast.parse(src, filename=path, feature_version=5)
    except SyntaxError as e:
        err('A1: not Python 3.5 compatible grammar: %s' % e)
        return 1

    # A1b: no f-string via ast (joinedstr) in case feature_version misses it
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            err('A1: f-string used (line %s), not allowed in Python 3.5' % node.lineno)

    # B3: required event functions
    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    if 'initialize' not in funcs:
        err('B3: required event function initialize(context) missing')
    has_handle = 'handle_data' in funcs
    src_has_run_daily = re.search(r'\brun_daily\s*\(', src) is not None
    if not has_handle and not src_has_run_daily:
        err('B3: neither handle_data(context, data) nor run_daily scheduling found')
    elif not has_handle:
        warn('B3: handle_data not defined; relying on run_daily only')

    # B4: import whitelist
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                root = a.name.split('.')[0]
                if root not in ALLOWED_IMPORTS:
                    err('B4: forbidden import "%s" (line %s)' % (a.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or '').split('.')[0]
            if root not in ALLOWED_IMPORTS:
                err('B4: forbidden from-import "%s" (line %s)' % (node.module, node.lineno))

    # B4b: forbidden builtins
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            name = fn.id if isinstance(fn, ast.Name) else (
                fn.attr if isinstance(fn, ast.Attribute) else None)
            if name in FORBIDDEN_NAMES:
                err('B4: forbidden builtin call %s() (line %s)' % (name, node.lineno))

    # B5: API spelling check — bare Name calls that are close to a PTrade API
    local_defs = set(funcs.keys()) | ALLOWED_IMPORTS
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            if name in PTRADE_APIS or name in local_defs:
                continue
            if name in ('log', 'g', 'range', 'len', 'int', 'float', 'str',
                        'min', 'max', 'abs', 'round', 'sorted', 'list', 'dict',
                        'set', 'enumerate', 'zip', 'isinstance', 'print'):
                continue
            close = difflib.get_close_matches(name, PTRADE_APIS, n=1, cutoff=0.86)
            if close:
                err('B5: possible API misspelling "%s" (line %s), did you mean "%s"?'
                    % (name, node.lineno, close[0]))

    # B5b: attribute calls on log/g/context are fine; check log misuse of print
    if re.search(r'^\s*print\s*\(', src, re.M):
        err('C11: print() used; use log.info instead')

    # B6: security code format
    for m in re.finditer(r"['\"](\d{6})(?:\.(XSHE|XSHG|SZ|SH))?['\"]", src):
        code, mkt = m.group(1), m.group(2)
        if code == '300171' and mkt != 'XSHE':
            err('B6: 300171 must use .XSHE suffix, found: %s' % m.group(0))

    print('=== PTrade static validation: %s ===' % path)
    for w in warnings:
        print('WARN: %s' % w)
    for e in errors:
        print('ERROR: %s' % e)
    if errors:
        print('RESULT: FAIL (%d errors, %d warnings)' % (len(errors), len(warnings)))
        return 1
    print('RESULT: PASS (0 errors, %d warnings)' % len(warnings))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
