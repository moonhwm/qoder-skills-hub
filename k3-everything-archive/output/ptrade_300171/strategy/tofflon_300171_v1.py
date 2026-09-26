# -*- coding: utf-8 -*-
"""
PTrade 策略：东富龙(300171.XSHE) 双均线趋势 + ATR 风险管理  v1
平台：恒生 PTrade（Python 3.5 兼容）
逻辑：
  - 入场：MA10 上穿 MA30（金叉）且收盘价站上 MA60（趋势过滤），量能放大
  - 仓位：单笔风险 = 组合净值 2%，止损距离 = 2.5 x ATR14，反推股数（100 股整手）
  - 出场：死叉 / ATR 移动止损 / 硬止损 -8%
  - 风控：ST/停牌/退市整理 禁交易；涨停不买、跌停不卖
"""

import numpy as np


def initialize(context):
    g.security = '300171.XSHE'          # 东富龙，创业板（深交所后缀 .XSHE）
    set_universe(g.security)
    set_benchmark('399006.XBHS')        # 创业板指作为业绩基准
    set_fixed_slippage(0.002)           # 固定滑点 0.2%
    set_commission(commission_ratio=0.0003, min_commission=5)  # 万三，最低 5 元

    # 策略参数
    g.ma_short = 10
    g.ma_long = 30
    g.ma_trend = 60
    g.atr_n = 14
    g.atr_mult = 2.5                    # ATR 止损倍数
    g.risk_pct = 0.02                   # 单笔风险占净值比例
    g.hard_stop = 0.92                  # 硬止损：成本价 * 0.92（-8%）
    g.vol_mult = 1.2                    # 放量阈值：量 > 1.2 x 20日均量
    g.hist_len = 120                    # 历史数据窗口

    # 状态变量
    g.can_trade = True
    g.highest = 0.0                     # 持仓以来最高价（移动止损用）

    # 每日 14:30 执行主逻辑（避开尾盘竞价与早盘噪声）
    run_daily(context, trade, time='14:30')


def before_trading_start(context, data):
    # ST / 停牌 / 退市整理 检查：任一命中则当日禁交易
    g.can_trade = True
    try:
        status = get_stock_status(g.security, ['ST', 'HALT', 'DELISTING'])
        info = status.get(g.security, {})
        if info.get('ST') or info.get('HALT') or info.get('DELISTING'):
            g.can_trade = False
            log.info('禁交易：ST/HALT/DELISTING 状态命中 %s' % info)
    except Exception as e:
        # 接口异常时保守处理：不新增仓位
        g.can_trade = False
        log.info('get_stock_status 异常，当日禁交易: %s' % e)


def handle_data(context, data):
    # 主逻辑由 run_daily 在 14:30 调度，此处保留事件函数占位
    pass


def _ma(arr, n):
    if len(arr) < n:
        return None
    return float(np.mean(arr[-n:]))


def _atr(high, low, close, n):
    if len(close) < n + 1:
        return None
    trs = []
    for i in range(len(close) - n, len(close)):
        prev_close = close[i - 1]
        tr = max(high[i] - low[i],
                 abs(high[i] - prev_close),
                 abs(low[i] - prev_close))
        trs.append(tr)
    return float(np.mean(trs))


def _round_lot(shares):
    # A 股 100 股整手，向下取整
    return int(shares // 100) * 100


def trade(context):
    if not g.can_trade:
        return

    df = get_history(g.hist_len, '1d', ['close', 'high', 'low', 'volume'],
                     g.security, fq='pre', include=False)
    if df is None or len(df) < g.ma_trend + 2:
        log.info('历史数据不足，跳过')
        return

    close = np.array(df['close'], dtype=float)
    high = np.array(df['high'], dtype=float)
    low = np.array(df['low'], dtype=float)
    volume = np.array(df['volume'], dtype=float)

    # 指标全部基于昨日及以前数据（include=False），无未来函数
    ma_s = _ma(close, g.ma_short)
    ma_l = _ma(close, g.ma_long)
    ma_t = _ma(close, g.ma_trend)
    ma_s_prev = _ma(close[:-1], g.ma_short)
    ma_l_prev = _ma(close[:-1], g.ma_long)
    atr = _atr(high, low, close, g.atr_n)
    vol_ma20 = _ma(volume, 20)
    if None in (ma_s, ma_l, ma_t, ma_s_prev, ma_l_prev, atr, vol_ma20):
        return

    price = close[-1]
    port = context.portfolio
    pos = port.positions.get(g.security) if hasattr(port.positions, 'get') else None
    hold_amt = pos.amount if pos is not None else 0

    # 涨跌停过滤（创业板 20%）
    snap = get_snapshot([g.security])
    sinfo = snap.get(g.security, {}) if snap else {}
    high_limit = sinfo.get('high_limit', 0)
    low_limit = sinfo.get('low_limit', 0)

    if hold_amt > 0:
        # 更新持仓以来最高价
        g.highest = max(g.highest, price)
        cost = pos.cost_basis if pos is not None else g.highest

        exit_reason = None
        if ma_s < ma_l and ma_s_prev >= ma_l_prev:
            exit_reason = '死叉'
        elif price < g.highest - g.atr_mult * atr:
            exit_reason = 'ATR移动止损'
        elif cost > 0 and price < cost * g.hard_stop:
            exit_reason = '硬止损-8%'

        if exit_reason is not None:
            if low_limit > 0 and price <= low_limit * 1.001:
                log.info('跌停无法卖出，推迟离场')
            else:
                order_target(g.security, 0)
                log.info('卖出清仓(%s)：price=%.2f' % (exit_reason, price))
                g.highest = 0.0
        return

    # 空仓：金叉 + 站上 MA60 + 放量 => 买入
    golden = ma_s > ma_l and ma_s_prev <= ma_l_prev
    trend_ok = price > ma_t
    vol_ok = vol_ma20 > 0 and volume[-1] > g.vol_mult * vol_ma20

    if golden and trend_ok and vol_ok:
        if high_limit > 0 and price >= high_limit * 0.999:
            log.info('接近涨停，放弃买入')
            return
        stop_dist = g.atr_mult * atr
        if stop_dist <= 0:
            return
        risk_amt = port.portfolio_value * g.risk_pct
        shares = risk_amt / stop_dist
        max_shares = port.cash * 0.95 / price
        shares = _round_lot(min(shares, max_shares))
        if shares < 100:
            log.info('资金不足一手，放弃买入')
            return
        order_target(g.security, shares)
        g.highest = price
        log.info('买入 %d 股：price=%.2f ATR=%.2f 止损距离=%.2f'
                 % (shares, price, atr, stop_dist))


def after_trading_end(context, data):
    pos = context.portfolio.positions.get(g.security) \
        if hasattr(context.portfolio.positions, 'get') else None
    amt = pos.amount if pos is not None else 0
    log.info('收盘持仓 %d 股，可用资金 %.2f'
             % (amt, context.portfolio.cash))
