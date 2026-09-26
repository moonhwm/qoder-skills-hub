#!/usr/bin/env python3
"""test_retrieval_registry_check.py — v1.7 实跑测试：v1.4/v1.5 行为回归 + calc_meta 正反例 + --merge + F1–F9 对抗修复用例 + v1.7 comparability/source_chain/evidence_band 与口径混杂用例。

用法：python3 tests/test_retrieval_registry_check.py
约定：全部用例以 UTC 今日为基准动态生成 check_date，避免时区/跨日翻转。
v1.7 注：--merge 对缺 comparability 的无错误条目追加一次性「建议补登」WARNING
（历史条目过渡提示），M02/M06/M08/V01/V14 五条旧用例的警告计数断言相应 +1。
v1.8 注：evidence_band 的 \\d 改 [0-9]（F-A1，拒全角/数学 Unicode 数字），
新增 W30–W33 四条拒收用例（套件 125→129）。
"""
import datetime, json, os, subprocess, sys, tempfile

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts",
                      "retrieval_registry_check.py")
TODAY = datetime.datetime.now(datetime.timezone.utc).date()
D = lambda days_ago: (TODAY - datetime.timedelta(days=days_ago)).isoformat()

PASS, FAIL = 0, 0
FAILURES = []


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        FAILURES.append(f"{name}: {detail}")


def run(args, stdin=None):
    p = subprocess.run([sys.executable, SCRIPT, *args],
                       input=stdin, capture_output=True, text=True)
    out = None
    try:
        out = json.loads(p.stdout)
    except ValueError:
        pass
    return p.returncode, out, p.stdout, p.stderr


def run_items(items, extra=()):
    """单文件模式：临时文件写入 items 后运行。"""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                     encoding="utf-8") as f:
        f.write(items if isinstance(items, str) else json.dumps(
            items, ensure_ascii=False))
        path = f.name
    try:
        return run([path, *extra])
    finally:
        os.unlink(path)


def entry(**kw):
    """合法基线条目（官方底表 income，今日日期，零 WARNING）。"""
    e = {"city": "广州", "param": "income", "value": 76849, "unit": "元/年",
         "url": "https://www.stats.gov.cn", "entry_path": "统计数据 → 收入",
         "source_type": "官方底表", "check_date": D(0), "conf": "A",
         "falsifiable_test": "重查公报，偏差超 ±5% 即推翻"}
    e.update(kw)
    return e


def nerr(out):
    return len(out["errors"]) if out else -1


def nwarn(out):
    return len(out["warnings"]) if out else -1


# ============ v1.4 回归（单文件行为零变化） ============
code, out, _, _ = run_items([entry()])
check("R01 合法基线 exit0 零错误零警告", code == 0 and nerr(out) == 0 and nwarn(out) == 0,
      f"code={code} out={out}")

code, out, _, _ = run_items(["不是对象"])
check("R02 条目非对象→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([{k: v for k, v in entry().items() if k != "unit"}])
check("R03 缺必填字段→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(city=123)])
check("R04 必填字段类型错→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(entry_path="  ")])
check("R05 必填字段空白→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([{k: v for k, v in entry().items() if k != "value"}])
check("R06 缺 value→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(value=0)])
check("R07 value=0 合法", code == 0 and nerr(out) == 0, f"{code} {out}")

code, out, _, _ = run_items([entry(value=True)])
check("R08 value bool→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

s = json.dumps([entry()]).replace("76849", "NaN")
code, out, _, _ = run_items(s)
check("R09 value NaN→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

s = json.dumps([entry()]).replace("76849", "Infinity")
code, out, _, _ = run_items(s)
check("R10 value Infinity→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(value="")])
check("R11 value 空串→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(value="   ")])
check("R12 value 纯空白→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(value="新一线", unit="档", param="city_tier",
                                   source_type="商业平台", conf="C",
                                   url="https://www.yicai.com")])
check("R13 string 质性值合法", code == 0 and nerr(out) == 0, f"{code} {out}")

code, out, _, _ = run_items([entry(param="house_price")])
check("R14 未知 param→WARNING 不阻断",
      code == 0 and nerr(out) == 0 and nwarn(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(url="www.stats.gov.cn")])
check("R15 url 无 scheme→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(url="ftp://stats.gov.cn")])
check("R16 url ftp→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(url="https://user@stats.gov.cn")])
check("R17 url 含 @userinfo→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(url="https://1.2.3.4/x")])
check("R18 url 纯 IP host→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(url="https://1.2.3.4:8080/x")])
check("R19 url IP+端口→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(url="https://stats.gov.cn 尾部垃圾")])
check("R20 url 非整串匹配→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(url="")])
check("R21 url 空且无 reason→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(url="", no_public_url_reason="仅年鉴纸质版")])
check("R22 url 空+reason 合法", code == 0 and nerr(out) == 0, f"{code} {out}")

code, out, _, _ = run_items([entry(check_date="2026/08/24")])
check("R23 check_date 格式错→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(check_date="2026-02-30")])
check("R24 check_date 非法日期→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(check_date=D(-2))])
check("R25 check_date 超 UTC 今日+1→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(check_date=D(-1))])
check("R26 check_date=今日+1→仅 WARNING",
      code == 0 and nerr(out) == 0 and nwarn(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(param="hpi", value=10, unit="倍", check_date=D(184),
                                   calc_meta={"price": 14000, "area_sqm": 90,
                                              "income": 45000, "household_size": 2.8})])
check("R27 快变参数 184 天→超期 WARNING",
      code == 0 and nerr(out) == 0 and nwarn(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(param="hpi", value=10, unit="倍", check_date=D(183),
                                   calc_meta={"price": 14000, "area_sqm": 90,
                                              "income": 45000, "household_size": 2.8})])
check("R28 快变参数 183 天→边界无警告",
      code == 0 and nerr(out) == 0 and nwarn(out) == 0, f"{code} {out}")

code, out, _, _ = run_items([entry(check_date=D(366))])
check("R29 慢变参数 366 天→超期 WARNING",
      code == 0 and nerr(out) == 0 and nwarn(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(check_date=D(365))])
check("R30 慢变参数 365 天→边界无警告",
      code == 0 and nerr(out) == 0 and nwarn(out) == 0, f"{code} {out}")

code, out, _, _ = run_items([entry(conf="D")])
check("R31 conf 非法→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(source_type="自媒体")])
check("R32 source_type 非法→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(source_type="权威第三方", conf="A")])
check("R33 权威第三方标 A→越级错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(source_type="商业平台", conf="B")])
check("R34 商业平台标 B→越级错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(source_type="社媒风评", conf="C",
                                   url="https://www.zhihu.com")])
check("R35 社媒风评→隔离 WARNING 不阻断",
      code == 0 and nerr(out) == 0 and nwarn(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(source_type="权威第三方", conf="B",
                                   url="https://www.cih-index.com")])
check("R36 权威第三方 B 合法", code == 0 and nerr(out) == 0 and nwarn(out) == 0,
      f"{code} {out}")

code, out, _, _ = run_items([{k: v for k, v in entry().items()
                              if k != "falsifiable_test"}])
check("R37 缺 falsifiable_test→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(param="hpi", value=10, unit="倍", conf="C",
                                   source_type="商业平台",
                                   url="https://www.lianjia.com")])
check("R38 hpi conf C→进总分 WARNING",
      code == 0 and nerr(out) == 0 and nwarn(out) >= 1, f"{code} {out}")

code, out, _, _ = run_items([entry(param="rir", value=1.0, unit="-", conf="C",
                                   source_type="商业平台",
                                   url="https://www.ke.com")])
check("R39 rir conf C→进总分 WARNING",
      code == 0 and nerr(out) == 0 and nwarn(out) >= 1, f"{code} {out}")

code, out, _, _ = run_items([entry(conf="C")])
check("R40 income conf C→无进总分警告",
      code == 0 and nerr(out) == 0 and nwarn(out) == 0, f"{code} {out}")

bad = entry(); bad["conf"] = "D"
code, out, _, _ = run_items([entry(), bad])
check("R41 coverage 只统计无错误条目",
      nerr(out) == 1 and out and out["coverage"]["entry_count"] == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(city="")])
check("R42 空 city→必填字段错误且不进 coverage",
      code == 1 and nerr(out) == 1
      and out["coverage"]["cities"] == [] and out["coverage"]["entry_count"] == 0,
      f"{code} {out}")

code, out, so, se = run_items({"a": 1})
check("R43 顶层非数组→exit2", code == 2 and out is None, f"{code} {se}")

code, out, so, se = run_items("{bad json")
check("R44 坏 JSON→exit2", code == 2 and out is None, f"{code} {se}")

code, out, _, _ = run(["-"], stdin=json.dumps([entry()], ensure_ascii=False))
check("R45 stdin '-' 可用", code == 0 and out and nerr(out) == 0, f"{code} {out}")

code, out, so, se = run(["/nonexistent/entries.json"])
check("R46 文件不存在→exit2", code == 2 and out is None, f"{code} {se}")

code, out, so, _ = run_items([entry()], extra=["--pretty"])
check("R47 --pretty 人类可读输出", code == 0 and out is None and "覆盖矩阵" in so,
      f"{code} {so[:120]}")

code, out, _, _ = run_items([entry(), entry(city="深圳")])
check("R48 覆盖矩阵计数", code == 0
      and out["coverage"]["matrix"]["广州"]["income"] == 1
      and out["coverage"]["matrix"]["深圳"]["income"] == 1
      and out["coverage"]["entry_count"] == 2, f"{code} {out}")

code, out, so, se = run(["-"], stdin="{bad")
check("R49 stdin 坏 JSON→exit2 且 stdout 无 JSON",
      code == 2 and out is None, f"{code} {se}")

# ============ v1.5 calc_meta ============
HPI_CM = {"price": 14000, "area_sqm": 90, "income": 45000, "household_size": 2.8}
# 回算 = 14000*90/(45000*2.8) = 10.0（v1.6：area_sqm/household_size 用 §9 钉死值，
# 否则会触发「偏离统一口径」WARNING）
code, out, _, _ = run_items([entry(param="hpi", value=10.0, unit="倍",
                                   calc_meta=HPI_CM)])
check("C01 hpi calc_meta 自洽→零错误零警告",
      code == 0 and nerr(out) == 0 and nwarn(out) == 0, f"{code} {out}")

code, out, _, _ = run_items([entry(param="hpi", value=10.19, unit="倍",
                                   calc_meta=HPI_CM)])
check("C02 hpi 偏差 1.9%→过", code == 0 and nerr(out) == 0, f"{code} {out}")

code, out, _, _ = run_items([entry(param="hpi", value=10.21, unit="倍",
                                   calc_meta=HPI_CM)])
check("C03 hpi 偏差 2.1%→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(param="hpi", value=10.0, unit="倍")])
check("C04 hpi 缺 calc_meta→WARNING 不阻断",
      code == 0 and nerr(out) == 0 and nwarn(out) == 1
      and "calc_meta" in out["warnings"][0], f"{code} {out}")

code, out, _, _ = run_items([entry(param="hpi", value=10.0, unit="倍",
                                   calc_meta={**HPI_CM, "price": -10000})])
check("C05 calc_meta 负值→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(param="hpi", value=10.0, unit="倍",
                                   calc_meta={**HPI_CM, "income": 0})])
check("C06 calc_meta 零值→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(param="hpi", value=10.0, unit="倍",
                                   calc_meta={**HPI_CM, "price": "一万"})])
check("C07 calc_meta 类型错→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(param="hpi", value=10.0, unit="倍",
                                   calc_meta={k: v for k, v in HPI_CM.items()
                                              if k != "household_size"})])
check("C08 calc_meta 缺字段→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(param="hpi", value=10.0, unit="倍",
                                   calc_meta="不是对象")])
check("C09 calc_meta 非对象→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

s = json.dumps([entry(param="hpi", value=10.0, unit="倍", calc_meta=HPI_CM)]
               ).replace("14000", "NaN")
code, out, _, _ = run_items(s)
check("C10 calc_meta NaN→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

RIR_CM = {"rent_monthly": 3000, "income": 36000, "area_sqm": 45}
# 回算 = 3000*12/36000 = 1.0
code, out, _, _ = run_items([entry(param="rir", value=1.0, unit="-",
                                   calc_meta=RIR_CM)])
check("C11 rir calc_meta 自洽→零错误零警告",
      code == 0 and nerr(out) == 0 and nwarn(out) == 0, f"{code} {out}")

code, out, _, _ = run_items([entry(param="rir", value=1.019, unit="-",
                                   calc_meta=RIR_CM)])
check("C12 rir 偏差 1.9%→过", code == 0 and nerr(out) == 0, f"{code} {out}")

code, out, _, _ = run_items([entry(param="rir", value=1.021, unit="-",
                                   calc_meta=RIR_CM)])
check("C13 rir 偏差 2.1%→错误", code == 1 and nerr(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(param="rir", value=1.0, unit="-")])
check("C14 rir 缺 calc_meta→WARNING 不阻断",
      code == 0 and nerr(out) == 0 and nwarn(out) == 1, f"{code} {out}")

code, out, _, _ = run_items([entry(param="income", value=76849,
                                   calc_meta={"price": 1})])
check("C15 非 hpi/rir 的 calc_meta 按未知字段容忍",
      code == 0 and nerr(out) == 0 and nwarn(out) == 0, f"{code} {out}")

code, out, _, _ = run_items([entry(param="hpi", value=10.0, unit="倍",
                                   calc_meta={**HPI_CM, "note": "额外字段"})])
check("C16 calc_meta 额外字段容忍",
      code == 0 and nerr(out) == 0 and nwarn(out) == 0, f"{code} {out}")

# ============ v1.5 --merge ============
tmpdir = tempfile.mkdtemp()


def wf(name, items):
    p = os.path.join(tmpdir, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False)
    return p


hpi10 = entry(param="hpi", value=10.0, unit="倍", calc_meta=HPI_CM)
f1 = wf("f1.json", [hpi10, entry(city="深圳", value=80000)])
f2 = wf("f2.json", [dict(hpi10),  # 广州 hpi 同值重复（≤5% → WARNING 取新）
                    entry(city="长沙", param="rir", value=1.0, unit="-",
                          calc_meta=RIR_CM)])
f3 = wf("f3.json", [entry(param="hpi", value=10.3, unit="倍",  # 3% 偏差 → WARNING
                          calc_meta={"price": 14420, "area_sqm": 90,
                                     "income": 45000, "household_size": 2.8}),
                    entry(city="深圳", value=86400),  # vs 80000 偏差 8% → 错误
                    entry(city="杭州", param="hpi", value=9.0, unit="倍",
                          calc_meta={"price": 14000, "area_sqm": 90,
                                     "income": 50000, "household_size": 2.8})])
code, out, _, _ = run(["--merge", f1, f2, f3])
m_err = out["errors"] if out else []
m_warn = out["warnings"] if out else []
check("M01 merge 偏差 8%→值冲突错误 exit1",
      code == 1 and len(m_err) == 1 and "值冲突" in m_err[0], f"{code} {out}")
check("M02 merge 同值+3% 重复→WARNING 取新（+v1.7 补登提示）",
      len(m_warn) == 2 and "取新" in m_warn[0]
      and "缺 comparability" in m_warn[1], f"{m_warn}")
check("M03 merge 错误消息前缀文件名",
      m_err and ".json" in m_err[0], f"{m_err}")
check("M04 merge 覆盖矩阵含新城新参数且总条数=7",
      out and out["coverage"]["entry_count"] == 7
      and out["coverage"]["matrix"]["杭州"]["hpi"] == 1
      and out["coverage"]["matrix"]["广州"]["hpi"] == 3
      and out["coverage"]["matrix"]["深圳"]["income"] == 2, f"{out}")
check("M05 merge 输出附 files 清单",
      out and out.get("merge", {}).get("files") == ["f1.json", "f2.json", "f3.json"],
      f"{out}")

code, out, _, _ = run(["--merge", f1, f2])  # 仅同值重复 → 取新 + v1.7 补登提示
check("M06 merge 仅同值重复→exit0 仅 WARNING（取新+v1.7 补登各一）",
      code == 0 and nerr(out) == 0 and nwarn(out) == 2
      and any("取新" in w for w in out["warnings"])
      and any("缺 comparability" in w for w in out["warnings"]), f"{code} {out}")

f4 = wf("f4.json", [entry(param="city_tier", value="新一线", unit="档",
                          source_type="商业平台", conf="C",
                          url="https://www.yicai.com")])
f5 = wf("f5.json", [entry(param="city_tier", value="一线", unit="档",
                          source_type="商业平台", conf="C",
                          url="https://www.yicai.com")])
code, out, _, _ = run(["--merge", f4, f5])
check("M07 merge 质性值不等→值冲突错误",
      code == 1 and nerr(out) == 1 and "质性" in out["errors"][0], f"{code} {out}")

code, out, _, _ = run(["--merge", f4, f4])
check("M08 merge 质性值相同→WARNING 取新（+v1.7 补登提示）",
      code == 0 and nerr(out) == 0 and nwarn(out) == 2
      and "取新" in out["warnings"][0]
      and "缺 comparability" in out["warnings"][1], f"{code} {out}")

f6 = wf("f6.json", [entry(param="hpi", value=10.0, unit="倍", conf="D")])  # 带错条目
code, out, _, _ = run(["--merge", f1, f6])
check("M09 merge 文件内错误照常报且带错条目不进冲突检测",
      code == 1 and nerr(out) == 1
      and not any("merge" in e for e in out["errors"]), f"{code} {out}")

code, out, so, se = run(["--merge", f1])
check("M10 --merge 单文件→exit2", code == 2 and out is None, f"{code} {se}")

code, out, so, se = run(["--merge", f1, "-"])
check("M11 --merge 含 stdin→exit2", code == 2 and out is None, f"{code} {se}")

code, out, so, se = run([f1, f2])
check("M12 多文件不带 --merge→exit2", code == 2 and out is None, f"{code} {se}")

code, out, so, _ = run(["--merge", f1, f2, "--pretty"])
check("M13 merge --pretty 输出合并信息与矩阵",
      code == 0 and out is None and "合并模式" in so and "覆盖矩阵" in so,
      f"{code} {so[:200]}")

# ============ v1.6 对抗修复（reviewer F1–F9） ============
# F1：--merge 质性比较前先 float() 数值化，"10" 与 10.0 视为同值走数值分支
fa = wf("fa.json", [entry(value="80000")])        # 广州 income "80000"（数字字符串）
fb = wf("fb.json", [entry(value=80000)])
fc = wf("fc.json", [entry(value=90000)])
fq = wf("fq.json", [entry(value="约八万")])
code, out, _, _ = run(["--merge", fa, fb])
check("V01 F1 数字字符串与数值同值→WARNING 取新非冲突（+v1.7 补登提示）",
      code == 0 and nerr(out) == 0 and nwarn(out) == 2
      and "取新" in out["warnings"][0]
      and "缺 comparability" in out["warnings"][1], f"{code} {out}")
code, out, _, _ = run(["--merge", fa, fc])
check("V02 F1 数字字符串 12.5% 偏差→数值分支值冲突错误（非质性）",
      code == 1 and nerr(out) == 1 and "值冲突" in out["errors"][0]
      and "质性" not in out["errors"][0], f"{code} {out}")
code, out, _, _ = run(["--merge", fa, fq])
check("V03 F1 不可数值化混合→仍走质性冲突错误",
      code == 1 and nerr(out) == 1 and "质性" in out["errors"][0], f"{code} {out}")

# F2：±2% 判定 epsilon 容差 + 文案精确到 4 位小数
HPI_CM_R3 = {"price": 14000, "area_sqm": 90, "income": 150000, "household_size": 2.8}
# 回算 = 14000*90/(150000*2.8) = 3.0
code, out, _, _ = run_items([entry(param="hpi", value=3.06, unit="倍",
                                   calc_meta=HPI_CM_R3)])
check("V04 F2 数学恰好 +2.0%→放行（epsilon 消除浮点边界抖动）",
      code == 0 and nerr(out) == 0 and nwarn(out) == 0, f"{code} {out}")
code, out, _, _ = run_items([entry(param="hpi", value=3.07, unit="倍",
                                   calc_meta=HPI_CM_R3)])
check("V05 F2 +2.33%→错误且偏差文案精确到 4 位小数",
      code == 1 and nerr(out) == 1 and "2.3333%" in out["errors"][0],
      f"{code} {out}")

# F3：calc_meta 偏离 §9 钉死值（hpi 90/2.8）→ WARNING 不阻断
code, out, _, _ = run_items([entry(param="hpi", value=10.0, unit="倍",
                                   calc_meta={"price": 21000, "area_sqm": 60,
                                              "income": 45000,
                                              "household_size": 2.8})])  # 回算 10.0
check("V06 F3 hpi area_sqm=60 偏离 90→WARNING 偏离统一口径不阻断",
      code == 0 and nerr(out) == 0 and nwarn(out) == 1
      and "偏离统一口径" in out["warnings"][0], f"{code} {out}")
code, out, _, _ = run_items([entry(param="hpi", value=14.0, unit="倍",
                                   calc_meta={"price": 14000, "area_sqm": 90,
                                              "income": 45000,
                                              "household_size": 2.0})])  # 回算 14.0
check("V07 F3 hpi household_size=2.0 偏离 2.8→WARNING 偏离统一口径",
      code == 0 and nerr(out) == 0 and nwarn(out) == 1
      and "偏离统一口径" in out["warnings"][0], f"{code} {out}")

# F4：rir calc_meta.area_sqm 仅在 ≠45 时 WARNING（仍不入回算）
code, out, _, _ = run_items([entry(param="rir", value=1.0, unit="-",
                                   calc_meta={**RIR_CM, "area_sqm": 30})])
check("V08 F4 rir area_sqm=30≠45→WARNING 偏离统一口径（回算不受影响）",
      code == 0 and nerr(out) == 0 and nwarn(out) == 1
      and "偏离统一口径" in out["warnings"][0], f"{code} {out}")

# F5：无 calc_meta 且 unit 含 % / rir value>3 → WARNING 疑似百分数形态
code, out, _, _ = run_items([entry(param="rir", value=0.35, unit="%")])
check("V09 F5 rir 缺 calc_meta 且 unit 含 %→缺 calc_meta+疑似百分数双 WARNING",
      code == 0 and nerr(out) == 0 and nwarn(out) == 2
      and any("疑似百分数形态" in w for w in out["warnings"]), f"{code} {out}")
code, out, _, _ = run_items([entry(param="rir", value=35.3, unit="-")])
check("V10 F5 rir 缺 calc_meta 且 value>3→疑似百分数 WARNING",
      code == 0 and nerr(out) == 0 and nwarn(out) == 2
      and any("疑似百分数形态" in w for w in out["warnings"]), f"{code} {out}")
code, out, _, _ = run_items([entry(param="hpi", value=10.0, unit="倍")])
check("V11 F5 hpi 缺 calc_meta 正常形态→仅缺 calc_meta 单 WARNING",
      code == 0 and nerr(out) == 0 and nwarn(out) == 1, f"{code} {out}")

# F6：hpi/rir 带 calc_meta 但 value 非数值 → 错误
code, out, _, _ = run_items([entry(param="hpi", value="高", unit="倍",
                                   calc_meta=HPI_CM)])
check("V12 F6 hpi value string + calc_meta→错误",
      code == 1 and nerr(out) == 1 and "自建比值参数" in out["errors"][0],
      f"{code} {out}")
code, out, _, _ = run_items([entry(param="rir", value="高", unit="-",
                                   calc_meta=RIR_CM)])
check("V13 F6 rir value string + calc_meta→错误",
      code == 1 and nerr(out) == 1, f"{code} {out}")

# F7：质性 value strip 后相同 → WARNING 取新（行为保持，文档补声明）
ft = wf("ft.json", [entry(param="city_tier", value="一线 ", unit="档",
                          source_type="商业平台", conf="C",
                          url="https://www.yicai.com")])
code, out, _, _ = run(["--merge", f5, ft])
check("V14 F7 质性值尾空格→strip 归一化后相同 WARNING 取新（+v1.7 补登提示）",
      code == 0 and nerr(out) == 0 and nwarn(out) == 2
      and "取新" in out["warnings"][0]
      and "缺 comparability" in out["warnings"][1], f"{code} {out}")

# F8：city strip 后作 merge/coverage 键，尾空格不再绕过同键冲突检测
fg = wf("fg.json", [entry(city="广州 ", param="hpi", value=20.0, unit="倍",
                          calc_meta={"price": 28000, "area_sqm": 90,
                                     "income": 45000, "household_size": 2.8})])
code, out, _, _ = run(["--merge", f1, fg])  # 广州 hpi 10.0 vs "广州 " 20.0
check("V15 F8 city 尾空格→strip 后同键 50% 偏差值冲突错误",
      code == 1 and nerr(out) == 1 and "值冲突" in out["errors"][0],
      f"{code} {out}")
check("V16 F8 coverage 城市行无尾空格重复",
      out and out["coverage"]["cities"] == ["广州", "深圳"], f"{out}")

# F9：--merge 检测含同文件内部重复（行为保持，文档补声明）
fdup = wf("fdup.json", [entry(value=100), entry(value=108)])  # 同文件 8% 偏差
code, out, _, _ = run([fdup])
check("V17 F9 单文件模式不做重复检测→exit0",
      code == 0 and nerr(out) == 0, f"{code} {out}")
code, out, _, _ = run(["--merge", fdup, fdup])
check("V18 F9 merge 下同文件内部重复→值冲突错误",
      code == 1 and nerr(out) == 1 and "值冲突" in out["errors"][0],
      f"{code} {out}")

# ============ v1.7 口径与证据链（comparability / source_chain / evidence_band） ============
# comparability 正例：full/proxy/stale 三枚举均合法，不触发任何警告
for tag, cv in (("W01", "full"), ("W02", "proxy"), ("W03", "stale")):
    code, out, _, _ = run_items([entry(comparability=cv)])
    check(f"{tag} comparability={cv} 合法→零错误零警告",
          code == 0 and nerr(out) == 0 and nwarn(out) == 0, f"{code} {out}")

code, out, _, _ = run_items([entry(comparability="partial")])
check("W04 comparability 非法值→错误",
      code == 1 and nerr(out) == 1 and "comparability" in out["errors"][0],
      f"{code} {out}")
code, out, _, _ = run_items([entry(comparability="")])
check("W05 comparability 空串→错误", code == 1 and nerr(out) == 1, f"{code} {out}")
code, out, _, _ = run_items([entry(comparability=123)])
check("W06 comparability 非 string→错误",
      code == 1 and nerr(out) == 1, f"{code} {out}")
code, out, _, _ = run_items([entry(comparability="proxy", conf="A")])
check("W07 comparability 不与 conf 联动（proxy+官方 A 合法）",
      code == 0 and nerr(out) == 0 and nwarn(out) == 0, f"{code} {out}")

# source_chain 正例：direct+conf A 合法；indirect+conf C 合法（转引上限 C）
code, out, _, _ = run_items([entry(source_chain="direct")])
check("W08 source_chain=direct + conf A 合法",
      code == 0 and nerr(out) == 0 and nwarn(out) == 0, f"{code} {out}")
code, out, _, _ = run_items([entry(source_chain="indirect", conf="C")])
check("W09 source_chain=indirect + conf C 合法",
      code == 0 and nerr(out) == 0 and nwarn(out) == 0, f"{code} {out}")

# 强制规则：indirect 且 conf 为 A/B → 错误（官方底表 conf A/B 本身合法，隔离新规则）
code, out, _, _ = run_items([entry(source_chain="indirect", conf="B")])
check("W10 indirect+conf B→错误（转引 conf 上限 C）",
      code == 1 and nerr(out) == 1 and "转引" in out["errors"][0]
      and "上限" in out["errors"][0], f"{code} {out}")
code, out, _, _ = run_items([entry(source_chain="indirect", conf="A")])
check("W11 indirect+conf A→错误",
      code == 1 and nerr(out) == 1 and "转引" in out["errors"][0], f"{code} {out}")
code, out, _, _ = run_items([entry(source_chain="quoted")])
check("W12 source_chain 非法值→错误",
      code == 1 and nerr(out) == 1 and "source_chain" in out["errors"][0],
      f"{code} {out}")
code, out, _, _ = run_items([entry(conf="A")])  # 缺省 source_chain 视为 direct
check("W13 source_chain 缺省视为 direct 不校验（conf A 官方底表合法）",
      code == 0 and nerr(out) == 0 and nwarn(out) == 0, f"{code} {out}")

# --merge 口径混杂检测（v1.7，§9.4）
g1 = wf("g1.json", [entry(comparability="full")])                     # 广州 income full
g2 = wf("g2.json", [entry(city="南昌", value=59609, comparability="proxy")])
g3 = wf("g3.json", [entry(city="西安", value=45082, comparability="stale")])
code, out, _, _ = run(["--merge", g1, g2])
check("W14 merge full+proxy 混杂→口径剪切 WARNING 且列出城市分组",
      code == 0 and nerr(out) == 0 and nwarn(out) == 1
      and "口径剪切" in out["warnings"][0]
      and "跨城横比须先对齐" in out["warnings"][0]
      and "广州" in out["warnings"][0] and "南昌" in out["warnings"][0]
      and "full" in out["warnings"][0] and "proxy" in out["warnings"][0],
      f"{code} {out}")
code, out, _, _ = run(["--merge", g1, g2, g3])
check("W15 merge full+proxy+stale 三值混杂→单条口径剪切 WARNING 含三分组",
      code == 0 and nerr(out) == 0 and nwarn(out) == 1
      and "口径剪切" in out["warnings"][0]
      and "stale" in out["warnings"][0] and "西安" in out["warnings"][0],
      f"{code} {out}")

g4 = wf("g4.json", [entry(city="深圳", value=84945, comparability="full")])
code, out, _, _ = run(["--merge", g1, g4])
check("W16 merge 跨城全 full 无混杂→零警告零错误",
      code == 0 and nerr(out) == 0 and nwarn(out) == 0, f"{code} {out}")

code, out, _, _ = run(["--merge", g1, wf("g5.json", [entry(city="深圳",
                                                           value=84945)])])
check("W17 merge 部分条目缺 comparability→无剪切，仅一次性补登 WARNING",
      code == 0 and nerr(out) == 0 and nwarn(out) == 1
      and "缺 comparability" in out["warnings"][0]
      and "口径剪切" not in out["warnings"][0], f"{code} {out}")
code, out, _, _ = run(["--merge",
                       wf("g6.json", [entry()]), wf("g7.json", [entry(city="深圳",
                                                                  value=84945)])])
check("W18 merge 全缺 comparability（历史条目形态）→exit0 仅一次性补登 WARNING",
      code == 0 and nerr(out) == 0 and nwarn(out) == 1
      and "缺 comparability" in out["warnings"][0]
      and "建议补登" in out["warnings"][0], f"{code} {out}")

code, out, _, _ = run_items([entry(comparability="full"),
                             entry(city="南昌", value=59609,
                                   comparability="proxy")])
check("W19 单文件模式不做口径混杂检测→零警告",
      code == 0 and nerr(out) == 0 and nwarn(out) == 0, f"{code} {out}")

# 同城同 param 不同 comparability 不属跨城横比→不出口径剪切（同值仅取新 WARNING）
g8 = wf("g8.json", [entry(value=80000, comparability="full")])
g9 = wf("g9.json", [entry(value=80000, comparability="proxy")])
code, out, _, _ = run(["--merge", g8, g9])
check("W20 merge 同城同 param full+proxy→无口径剪切（仅取新 WARNING）",
      code == 0 and nerr(out) == 0 and nwarn(out) == 1
      and "取新" in out["warnings"][0]
      and not any("口径剪切" in w for w in out["warnings"]), f"{code} {out}")

# 非法 comparability 条目带错误→不进混杂检测（无剪切、无补登，错误照常报）
ga = wf("ga.json", [entry(city="南昌", value=59609, comparability="partial")])
code, out, _, _ = run(["--merge", g1, ga])
check("W21 merge 含非法 comparability 条目→错误且混杂检测跳过之",
      code == 1 and nerr(out) == 1
      and not any("口径剪切" in w or "缺 comparability" in w
                  for w in out["warnings"]), f"{code} {out}")

# evidence_band 格式校验（§10，可选不强制；fusion_* 条目示例）
fe = lambda **kw: entry(param="fusion_access", value="EAST 在运", unit="-", **kw)
code, out, _, _ = run_items([fe(evidence_band="0.70-0.90")])
check("W22 evidence_band 合法 \"0.70-0.90\"→零错误零警告",
      code == 0 and nerr(out) == 0 and nwarn(out) == 0, f"{code} {out}")
code, out, _, _ = run_items([fe(evidence_band="0.9-1")])
check("W23 evidence_band \"0.9-1\" 简写合法", code == 0 and nerr(out) == 0,
      f"{code} {out}")
code, out, _, _ = run_items([fe(evidence_band="1.00-1.00")])
check("W24 evidence_band \"1.00-1.00\" 上界 1 合法",
      code == 0 and nerr(out) == 0, f"{code} {out}")
code, out, _, _ = run_items([fe(evidence_band="0.90–1.00")])  # en dash U+2013
check("W25 evidence_band en dash→错误（须半角连字符）",
      code == 1 and nerr(out) == 1 and "evidence_band" in out["errors"][0],
      f"{code} {out}")
code, out, _, _ = run_items([fe(evidence_band="70-90")])
check("W26 evidence_band \"70-90\" 越界→错误",
      code == 1 and nerr(out) == 1, f"{code} {out}")
code, out, _, _ = run_items([fe(evidence_band="0.90-0.70")])
check("W27 evidence_band 下界>上界→错误",
      code == 1 and nerr(out) == 1 and "下界" in out["errors"][0], f"{code} {out}")
code, out, _, _ = run_items([fe(evidence_band=0.9)])
check("W28 evidence_band 非 string→错误",
      code == 1 and nerr(out) == 1, f"{code} {out}")
code, out, _, _ = run_items([fe()])
check("W29 evidence_band 缺省不强制→零错误零警告",
      code == 0 and nerr(out) == 0 and nwarn(out) == 0, f"{code} {out}")

# v1.8 F-A1：\d→[0-9]，Unicode 十进制数字（全角/数学数字）一律拒收
for tag, band in (("W30", "0.５-0.9"), ("W31", "0.5-0.９"),
                  ("W32", "0.５５-0.9"), ("W33", "0.𝟱-0.9")):
    code, out, _, _ = run_items([fe(evidence_band=band)])
    check(f"{tag} evidence_band Unicode数字 {band!r}→错误",
          code == 1 and nerr(out) == 1 and "evidence_band" in out["errors"][0],
          f"{code} {out}")

print(f"\n{PASS} passed / {PASS + FAIL} total")
if FAILURES:
    print("FAILURES:")
    for f_ in FAILURES:
        print("  -", f_)
    sys.exit(1)
print("ALL PASS")
