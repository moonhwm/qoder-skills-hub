#!/usr/bin/env python3
"""PPP 双锚计算器：房价收入比/月供占比/租售比/引才包等效加成。
v1.3 2026-08-27 修改人: K3: --rate 默认值更新为当期快照 3.0 并立当月核对纪律(与 commute-audit 燃油费同规); 租售比最低档标签改「宁租(否决购房)」消除城市级否决误读, 依 v1.2.2 批判#5/#8
v1.2.1 2026-08-25 修改人: Orchestrator (Kimi K3): 月供占比标签勘误(分母=全包/12), 依 iteration-2 verifier 瑕疵#2
用法:
  python3 ppp_calc.py --income 120000 --price 8300 [--area 90] [--rate 3.0] [--years 30] [--rent 2500] \
      [--settle 100000] [--settle-years 5] [--house-sub 100000] [--apt-rent 1500]
仅标准库。判定带见 references/ppp-paradigm.md。
"""
import argparse, json

def band(v, lo, hi, invert=False):
    if invert:  # 越大越好（租售比）
        return "舒适" if v >= hi else ("压线" if v >= lo else "否决")
    return "舒适" if v <= lo else ("压线" if v <= hi else "否决")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--income", type=float, required=True, help="全包年收(元)")
    p.add_argument("--price", type=float, required=True, help="二手均价(元/㎡)")
    p.add_argument("--area", type=float, default=90)
    p.add_argument("--rate", type=float, default=3.0, help="房贷利率%%（当期快照2026-08：5年期以上LPR 3.5/首套商贷主流3.0-3.2/公积金首套2.6；进入判定须当月核对）")
    p.add_argument("--years", type=int, default=30)
    p.add_argument("--rent", type=float, default=0, help="同面积月租(元)")
    p.add_argument("--settle", type=float, default=0, help="安家费总额")
    p.add_argument("--settle-years", type=int, default=5, help="安家费绑定年限")
    p.add_argument("--house-sub", type=float, default=0, help="购房补贴")
    p.add_argument("--apt-rent", type=float, default=0, help="人才公寓月省租金")
    a = p.parse_args()

    total = a.price * a.area
    loan = total * 0.85
    r, n = a.rate / 100 / 12, a.years * 12
    m = loan * r * (1 + r) ** n / ((1 + r) ** n - 1)
    inc_m = a.income / 12
    hir = total / a.income                      # 房价收入比
    m_ratio = m / inc_m * 100                   # 月供占比%
    rental = (a.rent * 12 / total * 100) if a.rent else None
    bonus = a.settle / a.settle_years + a.house_sub / 5 + a.apt_rent * 12
    boost = bonus / a.income * 100              # 引才包等效加成%

    out = {
        "总价": round(total), "月供": round(m),
        "房价收入比": round(hir, 1), "判定_房价收入比": band(hir, 8, 12),
        "月供占月全包%": round(m_ratio, 1), "判定_月供占比": band(m_ratio, 40, 55),  # 口径: 分母=全包/12(非纯到手), v1.2.1勘误
        "租售比%": (round(rental, 2) if rental else None),
        # v1.3: 最低档改「宁租(否决购房)」——否决对象是购房而非城市，防报告误读
        "判定_租售比": (("舒适(买房不急)" if rental >= 3.5 else ("压线" if rental >= 2.5 else "宁租(否决购房)")) if rental else None),
        "引才包等效年加成": round(bonus), "引才包加成%": round(boost, 1),
        "判定_引才包": ("显著" if boost >= 15 else ("一般" if boost >= 5 else "可忽略")) if bonus else None,
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
