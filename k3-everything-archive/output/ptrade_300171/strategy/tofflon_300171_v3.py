# -*- coding: utf-8 -*-
"""
PTrade 策略：东富龙(300171.XSHE) 双均线趋势 + ATR 风险管理  v3
平台：恒生 PTrade（Python 3.5 兼容）
逻辑：
  - 入场：MA10 上穿 MA30（金叉）且收盘价站上 MA60（趋势过滤），量能放大
  - 仓位：单笔风险 = 组合净值 2%，止损距离 = 2.5 x ATR14，反推股数（100 股整手）
  - 出场：死叉（持续状态）/ ATR 移动止损 / 硬止损 -8%（基于盘中快照实时价判定）
  - 风控：ST/停牌/退市整理 禁买入；涨停不买、跌停不卖（实时价对比当日限价）
v3 修复（对比 v2 评审）：
  1. get_stock_name 返回 dict {code: name}，按 dict 解析（兼容 str 形态），
     退市整理期名称含"退"兜底逻辑生效
  2. 死叉离场由"交叉当日事件"放宽为"MA10<MA30 持续状态"，
     避免卖出被跌停/停牌拦截后不再触发
  3. 快照异常时用昨收 x1.2 / x0.8（创业板 20%）估算限价兜底，并加告警日志
"""

import numpy as np


def initialize(context):
    g.security = '300171.XSHE'          # 东富龙，创业板（深交所后缀 .XSHE）
    set_universe(g.security)
    set_benchmark('399006.XBHS')        # 创业板指作为业绩基准
    set_fixed_slippage(0.04)            # 固定滑点 0.04 元（约 0.2%，按 20 元价格中枢）
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
    g.limit_pct = 0.20                  # 创业板涨跌停幅度 20%（限价兜底估算用）

    # 状态变量（买卖分离：异常时只禁买，止损卖出不受影响）
    g.can_buy = True
    g.can_sell = True
    g.highest = 0.0                     # 持仓以来最高价（移动止损用）

    # 每日 14:30 执行主逻辑（避开尾盘竞价与早盘噪声）
    run_daily(context, trade, time='14:30')


def before_trading_start(context, data):
    # ST / 停牌 / 退市整理 检查
    g.can_buy = True
    g.can_sell = True
    try:
        st = get_stock_status(g.security, 'ST')
        halt = get_stock_status(g.security, 'HALT')
        deli = get_stock_status(g.security, 'DELISTING')
        is_st = bool(st.get(g.security, False)) if isinstance(st, dict) else False
        is_halt = bool(halt.get(g.security, False)) if isinstance(halt, dict) else False
        is_deli = bool(deli.get(g.security, False)) if isinstance(deli, dict) else False

        # 退市整理期不在 DELISTING 状态内，用名称含“退”兜底
        # get_stock_name 返回 dict {code: name}（兼容 str 形态）
        name_ret = get_stock_name(g.security)
        if isinstance(name_ret, dict):
            nm = name_ret.get(g.security)
        else:
            nm = name_ret
        is_retiring = isinstance(nm, str) and ('退' in nm)

        if is_halt:
            g.can_buy = False
            g.can_sell = False
            log.info('停牌：当日买卖均禁止')
        elif is_st or is_deli or is_retiring:
            g.can_buy = False
            log.info('风险状态(ST=%s DELISTING=%s 退=%s)：禁买入，允许卖出'
                     % (is_st, is_deli, is_retiring))
    except Exception as e:
        # 接口异常时保守处理：不新增仓位，卖出（止损）不受阻
        g.can_buy = False
        log.info('状态查询异常，当日禁买入: %s' % e)


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


def _realtime_price(security, prev_close):
    """取盘中快照实时价与当日涨跌停价。

    返回 (last_px, high_limit, low_limit)。
    快照异常时回退昨收，并按创业板 20% 估算限价兜底。
    """
    try:
        snap = get_snapshot([security])
        sinfo = snap.get(security, {}) if snap else {}
        last_px = sinfo.get('last_px', None)
        high_limit = sinfo.get('high_limit', 0) or 0
        low_limit = sinfo.get('low_limit', 0) or 0
        if last_px is not None and last_px > 0:
            return float(last_px), float(high_limit), float(low_limit)
    except Exception as e:
        log.info('get_snapshot 异常: %s' % e)
    log.info('快照不可用，回退昨收价并估算限价')
    high_est = prev_close * (1 + g.limit_pct) if prev_close > 0 else 0
    low_est = prev_close * (1 - g.limit_pct) if prev_close > 0 else 0
    return None, high_est, low_est


def trade(context):
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

    # 实时价优先；快照不可用时回退昨收 + 估算限价（创业板 20%）
    rt_px, high_limit, low_limit = _realtime_price(g.security, close[-1])
    price = rt_px if rt_px is not None else close[-1]

    port = context.portfolio
    pos = port.positions.get(g.security, None)
    hold_amt = pos.amount if pos is not None else 0

    # 持仓为 0（含卖出成交确认）时重置移动止损基线
    if hold_amt == 0 and g.highest > 0:
        g.highest = 0.0

    if hold_amt > 0:
        g.highest = max(g.highest, price)
        cost = pos.cost_basis

        exit_reason = None
        # 死叉放宽为持续状态：卖出被跌停/停牌拦截后，后续日期仍会触发
        if ma_s < ma_l:
            exit_reason = '死叉/均线空头'
        elif price < g.highest - g.atr_mult * atr:
            exit_reason = 'ATR移动止损'
        elif cost > 0 and price < cost * g.hard_stop:
            exit_reason = '硬止损-8%'

        if exit_reason is not None:
            if not g.can_sell:
                log.info('停牌无法卖出，推迟离场(%s)' % exit_reason)
            elif low_limit > 0 and price <= low_limit * 1.001:
                log.info('跌停无法卖出，推迟离场(%s)' % exit_reason)
            else:
                order_target(g.security, 0)
                log.info('卖出清仓(%s)：price=%.2f' % (exit_reason, price))
                # g.highest 不清零：待确认持仓为 0 后由上文重置
        return

    # 空仓：金叉 + 站上 MA60 + 放量 => 买入
    if not g.can_buy:
        return
    golden = ma_s > ma_l and ma_s_prev <= ma_l_prev
    trend_ok = close[-1] > ma_t
    vol_ok = vol_ma20 > 0 and volume[-1] > g.vol_mult * vol_ma20

    if golden and trend_ok and vol_ok:
        if high_limit > 0 and price >= high_limit * 0.999:
            log.info('接近涨停，放弃买入')
            return
        stop_dist = g.atr_mult * atr
        if stop_dist <= 0 or price <= 0:
            return
        risk_amt = port.portfolio_value * g.risk_pct
        shares = risk_amt / stop_dist
        # 用实时价估算可买股数，降低跳空导致报单金额超可用资金的概率
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
    pos = context.portfolio.positions.get(g.security, None)
    amt = pos.amount if pos is not None else 0
    log.info('收盘持仓 %d 股，可用资金 %.2f'
             % (amt, context.portfolio.cash))
