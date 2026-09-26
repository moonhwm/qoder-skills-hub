#!/usr/bin/env python3
"""retrieval_registry_check.py — 校验外部检索登记 entries.json（schema 见 references/retrieval-paths.md 第 4 节）。

用法:
    python3 retrieval_registry_check.py entries.json [--pretty]
    cat entries.json | python3 retrieval_registry_check.py - [--pretty]   # stdin
    python3 retrieval_registry_check.py --merge f1.json f2.json ... [--pretty]  # 多文件合并校验

entries.json 顶层为数组，每条字段（详见 references/retrieval-paths.md）：
    city / param / value / unit / url / entry_path / source_type / check_date /
    conf / falsifiable_test / no_public_url_reason（可选）/ calc_meta（hpi/rir 应填）/
    comparability（可选，v1.7）/ source_chain（可选，v1.7）/
    evidence_band（可选，v1.7，fusion_* 证据带）

校验规则：
    错误（阻断，exit 1）：
        - 条目非 JSON 对象；必填字段缺失/为空/类型错误
          （value 允许数值 0；value 为空字符串/纯空白视为缺失字段错误；
          value 为 NaN/Infinity 等非有限数视为类型错误）
        - url 非空但非法（须 http/https 带域名，整串匹配；拒绝纯 IP host
          与含 userinfo（@）的 URL）；url 为空且缺 no_public_url_reason
        - check_date 非 YYYY-MM-DD / 非法日期；未来日期判定以 UTC 为基准：
          check_date 超过 UTC 今日 +1 天 → 错误
        - conf 非 A|B|C；source_type 非五类枚举
        - conf ↔ source_type 越级（权威第三方上限 B、商业平台/社媒风评仅 C；
          官方底表/官方延伸才允许 A）
        - comparability 非 full|proxy|stale（v1.7 可选字段，填了就必须合法）；
          source_chain 非 direct|indirect（v1.7 可选字段，缺省视为 direct 不校验）
        - source_chain=indirect（媒体/第三方转引）且 conf 为 A 或 B → 错误
          （v1.7 强制规则：转引条目 conf 上限 C，须降级或直取原文改标 direct）
        - evidence_band 格式非法（v1.7 可选字段，仅校验格式不强制填写：
          须为 0–1 区间字符串如 "0.70-0.90"，两端各为 [0,1] 内数值且下界 ≤ 上界）
        - 缺 falsifiable_test（必填，审计可证伪性硬要求）
        - calc_meta 回算不自洽（v1.5，自建比值口径见 retrieval-paths.md 第 9 节）：
          hpi 回算 price*area_sqm/(income*household_size)、rir 回算
          rent_monthly*12/income，与 value 相对偏差 >2% → 错误
          （v1.6：判定含 1e-9 epsilon 容差，数学恰好 2% 放行）；
          calc_meta 非对象 / 缺口径字段 / 字段非正的有限数 → 错误；
          hpi/rir 带 calc_meta 但 value 为非空白 string → 错误（v1.6，
          自建比值参数不得登记质性值，无法回算比对）
        - --merge 跨文件值冲突：同一 (city,param) 多次登记且 value 相对偏差
          >5%（分母取两值绝对值较大者；质性 string 值不等即冲突。
          v1.6：可数值化的 string 值先 float() 数值化再按数值分支比较，
          "10" 与 10.0 视为同值；city/param/质性 value 比较前 strip 空白
          归一化；merge 检测覆盖同文件内部重复）
    警告（不阻断，exit 仍为 0）：
        - check_date 晚于 UTC 今日但 ≤ UTC 今日 +1 天（时区容差，吸收
          UTC↔本地时区跨日误差，多机结果可复现）
        - 快变参数（hpi/rir/livability_rank/city_tier/aspiration_proxy）check_date
          超 6 个月（固定 183 天）；慢变参数（income/fusion_density/fusion_access）
          超 12 个月（固定 365 天）
        - 进总分参数（hpi/rir）直接采用 conf=C（须标假设并降级处理，见
          retrieval-paths.md 第 5 节）
        - source_type=社媒风评（隔离层，永不进总分，v48 裁定延续）
        - param 不在建议取值表（未知参数按慢变 12 个月判有效期）
        - hpi/rir 条目缺 calc_meta（v1.5 起硬规范，历史条目过渡提示）
        - calc_meta.area_sqm/household_size 偏离第 9 节统一钉死值
          （hpi 90/2.8；rir 45）→ WARNING 偏离统一口径（v1.6，不阻断历史条目）
        - hpi/rir 缺 calc_meta 且 unit 含 '%'，或 rir 缺 calc_meta 且
          value>3 → WARNING 疑似百分数形态（v1.6，§9.2 要求登记比值）
        - --merge 重复登记取新：同一 (city,param) 多次登记且相对偏差 ≤5%
          （含相等），以后出现文件/条目为准
        - --merge 口径剪切（v1.7）：同一 param 跨城条目 comparability 取值混杂
          （部分 full 部分 proxy/stale）→ WARNING「口径剪切：该参数跨城横比须先
          对齐」并列出城市分组；缺 comparability 的无错误条目不参与混杂检测，
          仅一次性 WARNING 建议补登（历史条目过渡）

--merge 模式（v1.5；v1.7 增口径混杂检测）：
    逐文件先各自校验（错误照常报，消息前缀文件名），再做上述跨文件检测；
    输出合并覆盖矩阵（跨文件城市×参数合计）与总 entry 数，coverage 口径同
    单文件；JSON 输出附带 "merge": {"files": [...]}。退出码契约不变。
    v1.7：同 param 跨城 comparability 取值混杂出「口径剪切」WARNING 并列出
    城市分组；缺 comparability 的无错误条目一次性 WARNING 建议补登。

输出（JSON 契约）：
    {"errors": [...], "warnings": [...],
     "coverage": {"cities": [...], "params": [...],
                  "matrix": {城市: {参数: 条数}}, "entry_count": N}}
    coverage 口径：只统计「无错误的条目」；city/param 为空字符串的条目视为
    未覆盖（不计入 cities/matrix/entry_count），故 entry_count = 合规且有效
    覆盖的条数，不一定等于 entries.json 总条数。
    --pretty 时改输人类可读文本（错误/警告清单 + 城市×参数覆盖矩阵表）。

退出码: 0=无错误（可有警告），1=有错误，2=用法/IO 错误。
纯标准库。
"""
import argparse, datetime, json, math, os, re, sys

# 五类信源 → 允许的 conf 集合（retrieval-paths.md 第 5 节）
SOURCE_TYPES = ("官方底表", "官方延伸", "权威第三方", "商业平台", "社媒风评")
CONF_BY_SOURCE = {
    "官方底表": {"A", "B", "C"},
    "官方延伸": {"A", "B", "C"},
    "权威第三方": {"B", "C"},
    "商业平台": {"C"},
    "社媒风评": {"C"},
}
CONF_MEANING = {"A": "实证", "B": "估算", "C": "假设"}
CONF_RANK = {"A": 0, "B": 1, "C": 2}  # 严格度 A>B>C，取「上限」用最小 rank


def conf_cap(st):
    """该信源允许的最高 conf（官方=A，权威第三方=B，商业平台/社媒=C）。"""
    return min(CONF_BY_SOURCE[st], key=lambda c: CONF_RANK[c])
# 建议参数取值与有效期（天）；快变 6 个月≈183 天，慢变 12 个月≈365 天
FAST_PARAMS = {"hpi", "rir", "livability_rank", "city_tier", "aspiration_proxy"}
SLOW_PARAMS = {"income", "fusion_density", "fusion_access"}
PARAM_ORDER = ["hpi", "rir", "income", "city_tier", "livability_rank",
               "fusion_density", "fusion_access", "aspiration_proxy"]
VALIDITY_DAYS = {**{p: 183 for p in FAST_PARAMS}, **{p: 365 for p in SLOW_PARAMS}}
# 进总分参数：C 级只许标假设并降级处理，不得直接取值
SCORE_PARAMS = {"hpi", "rir"}
# v1.5 自建比值口径（retrieval-paths.md 第 9 节）：calc_meta 必带字段与回算容差
CALC_META_FIELDS = {
    "hpi": ("price", "area_sqm", "income", "household_size"),
    "rir": ("rent_monthly", "income", "area_sqm"),
}
CALC_TOLERANCE = 0.02   # calc_meta 回算与 value 相对偏差 >2% → 错误
CALC_EPS = 1e-9         # v1.6：>2% 判定 epsilon，消除浮点边界抖动（恰好 2% 放行）
# v1.6 §9 统一钉死值：calc_meta 偏离出 WARNING「偏离统一口径」（不阻断历史条目）
PINNED_CALC = {"hpi": {"area_sqm": 90.0, "household_size": 2.8},
               "rir": {"area_sqm": 45.0}}
MERGE_TOLERANCE = 0.05  # --merge 同 (city,param) value 相对偏差 >5% → 错误
# v1.7 可选字段枚举（retrieval-paths.md 第 4 节）：填了就必须合法（非法值 → 错误）
COMPARABILITY = ("full", "proxy", "stale")  # 口径完全可比/代理口径（如城镇代全体）/滞后口径（如用上年值）
SOURCE_CHAIN = ("direct", "indirect")       # 官网/公报原文直取 / 媒体/第三方转引
# v1.7 强制规则：source_chain=indirect 时 conf 上限 C（标 A/B → 错误）
INDIRECT_CONF_CAP = "C"
# v1.7 §10：evidence_band 仅校验格式——0–1 区间字符串如 "0.70-0.90"（下界 ≤ 上界）
# v1.8 F-A1：\d → [0-9]，拒全角/数学等 Unicode 十进制数字（\d 默认 UNICODE 会放行）
RE_EVIDENCE_BAND = re.compile(
    r"^(?:0(?:\.[0-9]{1,2})?|1(?:\.0{1,2})?)-(?:0(?:\.[0-9]{1,2})?|1(?:\.0{1,2})?)$")
REQUIRED_STR = ("city", "param", "unit", "url", "entry_path",
                "source_type", "check_date", "conf", "falsifiable_test")
# 整串匹配（fullmatch）：http/https + 含点域名 + 可选路径；
# host 段禁 @（userinfo 伪装），纯 IPv4 host 由 RE_IPV4_HOST 另行拒绝
RE_URL = re.compile(r"^https?://[^@\s/]+\.[^@\s/]+(/[^\s]*)?$", re.I)
RE_IPV4_HOST = re.compile(r"^https?://\d{1,3}(\.\d{1,3}){3}(:\d+)?(/|$)", re.I)


def die(msg):
    """用法/IO 错误：stderr 打印，exit 2（无 JSON 输出）。"""
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def valid_date(s):
    """严格 YYYY-MM-DD 且为真实日期；返回 date 或 None。"""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return None
    try:
        return datetime.date.fromisoformat(s)
    except ValueError:
        return None


def validate_entry(x, i, errors, warnings, today, ctx_prefix="entries"):
    """单条校验；返回规范化的 (city, param)（非法时返回 None）供覆盖矩阵使用。"""
    ctx = f"{ctx_prefix}[{i}]"
    if not isinstance(x, dict):
        errors.append(f"{ctx} 不是 JSON 对象: {x!r}")
        return None
    city, param = x.get("city"), x.get("param")
    ctx = f"{ctx_prefix}[{i}](city={city!r}, param={param!r})"

    # ---- 必填字段缺失/为空/类型错误 ----
    for f in REQUIRED_STR:
        v = x.get(f)
        if v is None:
            errors.append(f"{ctx}: 缺必填字段 {f}")
        elif not isinstance(v, str):
            errors.append(f"{ctx}: 字段 {f} 应为 string，实为 {type(v).__name__}: {v!r}")
        # url 允许空串（走 no_public_url_reason 分支），其余必填串不得空白
        elif f != "url" and not v.strip():
            errors.append(f"{ctx}: 必填字段 {f} 为空")
    if "value" not in x or x["value"] is None:
        errors.append(f"{ctx}: 缺必填字段 value")
    else:
        v = x["value"]
        if isinstance(v, bool) or not isinstance(v, (int, float, str)):
            errors.append(f"{ctx}: 字段 value 应为 number 或 string，"
                          f"实为 {type(v).__name__}: {v!r}")
        elif isinstance(v, (int, float)) and not math.isfinite(v):
            errors.append(f"{ctx}: 字段 value 不得为非有限数（NaN/Infinity）: {v!r}")
        elif isinstance(v, str) and not v.strip():
            # 数值 0 合法；空字符串/纯空白视为缺失字段
            errors.append(f"{ctx}: 必填字段 value 为空（空字符串/纯空白视为缺失）")
    if isinstance(param, str) and param and param not in PARAM_ORDER:
        warnings.append(f"{ctx}: param {param!r} 不在建议取值表 "
                        f"({'/'.join(PARAM_ORDER)})，有效期按慢变 12 个月处理")

    # ---- url 合法性 / 无公开链接理由 ----
    url = x.get("url")
    if isinstance(url, str):
        if url.strip() == "":
            reason = x.get("no_public_url_reason")
            if not (isinstance(reason, str) and reason.strip()):
                errors.append(f"{ctx}: url 为空但未填 no_public_url_reason")
        elif not RE_URL.fullmatch(url):
            errors.append(f"{ctx}: url 非法（须 http/https 带域名，整串匹配，"
                          f"禁含 @userinfo；宁给入口首页，禁止编造深链）: {url!r}")
        elif RE_IPV4_HOST.match(url):
            errors.append(f"{ctx}: url 非法（须带域名，不接受纯 IP host）: {url!r}")

    # ---- check_date 格式 / 未来日期 / 超期 ----
    cd_raw = x.get("check_date")
    cd = valid_date(cd_raw) if isinstance(cd_raw, str) else None
    if isinstance(cd_raw, str) and cd_raw and cd is None:
        errors.append(f"{ctx}: check_date 非合法 YYYY-MM-DD 日期: {cd_raw!r}")
    elif cd is not None:
        # 未来日期判定钉死 UTC：> UTC 今日 +1 天 → 错误；
        # UTC 今日 < check_date ≤ +1 天 → WARNING（时区容差，多机结果可复现）
        if cd > today + datetime.timedelta(days=1):
            errors.append(f"{ctx}: check_date {cd} 是未来日期"
                          f"（超过 UTC 今日 {today} +1 天时区容差）")
        elif cd > today:
            warnings.append(f"{ctx}: check_date {cd} 晚于 UTC 今日 {today}，"
                            f"在 +1 天时区容差内（本地时区跨日所致），按当日处理")
        else:
            limit = VALIDITY_DAYS.get(param if isinstance(param, str) else "", 365)
            age = (today - cd).days
            if age > limit:
                kind = "快变" if param in FAST_PARAMS else "慢变"
                warnings.append(
                    f"{ctx}: {kind}参数 check_date {cd} 距今 {age} 天，"
                    f"超有效期 {limit} 天，引用前须复检")

    # ---- conf / source_type 枚举与越级 ----
    conf, st = x.get("conf"), x.get("source_type")
    if isinstance(conf, str) and conf and conf not in CONF_MEANING:
        errors.append(f"{ctx}: conf 非法（应 A|B|C，映射 实证|估算|假设）: {conf!r}")
    if isinstance(st, str) and st and st not in SOURCE_TYPES:
        errors.append(f"{ctx}: source_type 非法（应 {'/'.join(SOURCE_TYPES)}）: {st!r}")
    if (isinstance(conf, str) and conf in CONF_MEANING
            and isinstance(st, str) and st in CONF_BY_SOURCE
            and conf not in CONF_BY_SOURCE[st]):
        errors.append(
            f"{ctx}: conf↔source_type 越级——{st} 上限 conf={conf_cap(st)}，"
            f"不得标 {conf}；请降级 conf 或换官方信源重查")
    # ---- v1.7 comparability / source_chain 可选字段（retrieval-paths.md 第 4 节）----
    comp = x.get("comparability")
    if comp is not None and comp not in COMPARABILITY:
        errors.append(f"{ctx}: comparability 非法（应 {'/'.join(COMPARABILITY)}="
                      f"口径完全可比/代理口径/滞后口径）: {comp!r}")
    sc = x.get("source_chain")
    if sc is not None and sc not in SOURCE_CHAIN:
        errors.append(f"{ctx}: source_chain 非法（应 {'/'.join(SOURCE_CHAIN)}="
                      f"直取/转引；缺省视为 direct 不校验）: {sc!r}")
    # v1.7 强制规则：转引条目 conf 上限 C（宜居榜单等媒体转引历史教训）
    if sc == "indirect" and conf in ("A", "B"):
        errors.append(
            f"{ctx}: source_chain=indirect（媒体/第三方转引）conf 上限 "
            f"{INDIRECT_CONF_CAP}，不得标 {conf}；请降级 conf 或直取发布方原文"
            f"改标 direct（retrieval-paths.md 第 4/5 节）")
    # ---- v1.7 evidence_band 可选字段（§10 fusion 证据阶梯；仅校验格式，不强制）----
    eb = x.get("evidence_band")
    if eb is not None:
        if not isinstance(eb, str):
            errors.append(f"{ctx}: evidence_band 应为 string（0–1 区间如 "
                          f"\"0.70-0.90\"），实为 {type(eb).__name__}: {eb!r}")
        elif not RE_EVIDENCE_BAND.fullmatch(eb):
            errors.append(f"{ctx}: evidence_band 格式非法——须为 0–1 区间字符串"
                          f"如 \"0.70-0.90\"（两端各为 [0,1] 内数值，至多两位小数，"
                          f"半角连字符）: {eb!r}")
        else:
            lo, hi = (float(p) for p in eb.split("-"))
            if lo > hi:
                errors.append(f"{ctx}: evidence_band 区间下界 {lo:g} 大于上界 "
                              f"{hi:g}: {eb!r}")
    # ---- 隔离与降级提醒（WARNING）----
    if st == "社媒风评":
        warnings.append(f"{ctx}: 社媒风评为隔离层证据，永不进总分（v48 裁定延续），"
                        f"仅允许进筛选/标注层")
    if conf == "C" and param in SCORE_PARAMS:
        warnings.append(f"{ctx}: {param} 为进总分参数，不得直接采用 conf=C；"
                        f"须标假设并作降级处理（交叉验证/敏感性标注/暂不计入）")
    # ---- calc_meta 自建比值口径校验（v1.5，retrieval-paths.md 第 9 节）----
    if isinstance(param, str) and param in CALC_META_FIELDS:
        cm = x.get("calc_meta")
        if cm is None:
            warnings.append(
                f"{ctx}: {param} 条目缺 calc_meta——v1.5 起自建比值口径硬规范"
                f"要求随条目登记（retrieval-paths.md 第 9 节），历史条目按统一口径重算")
            # v1.6：无 calc_meta 的百分数形态提示（§9.2 要求 value 一律登记比值）
            unit_v = x.get("unit")
            if isinstance(unit_v, str) and "%" in unit_v:
                warnings.append(
                    f"{ctx}: {param} 缺 calc_meta 且 unit 含 '%'——疑似百分数形态，"
                    f"§9.2 要求 value 一律登记比值（如 0.35 而非 35.3%）")
            v_raw = x.get("value")
            if (param == "rir" and isinstance(v_raw, (int, float))
                    and not isinstance(v_raw, bool) and math.isfinite(v_raw)
                    and v_raw > 3):
                warnings.append(
                    f"{ctx}: rir 缺 calc_meta 且 value={v_raw:g} > 3——疑似百分数"
                    f"形态，§9.2 要求 value 一律登记比值（如 0.35 而非 35.3%）")
        elif not isinstance(cm, dict):
            errors.append(f"{ctx}: calc_meta 应为 JSON 对象，"
                          f"实为 {type(cm).__name__}: {cm!r}")
        else:
            fields = CALC_META_FIELDS[param]
            vals, cm_ok = {}, True
            for f in fields:
                v = cm.get(f)
                if v is None:
                    errors.append(f"{ctx}: calc_meta 缺口径字段 {f}"
                                  f"（{param} 要求 {'/'.join(fields)}）")
                    cm_ok = False
                elif isinstance(v, bool) or not isinstance(v, (int, float)):
                    errors.append(f"{ctx}: calc_meta.{f} 应为正数，"
                                  f"实为 {type(v).__name__}: {v!r}")
                    cm_ok = False
                elif not math.isfinite(v) or v <= 0:
                    errors.append(f"{ctx}: calc_meta.{f} 应为正的有限数: {v!r}")
                    cm_ok = False
                else:
                    vals[f] = float(v)
            # v1.6：偏离 §9 统一钉死值（hpi 90/2.8；rir 45）→ WARNING 不阻断；
            # rir 的 area_sqm 不入回算公式（§9.2），仅作钉死值口径校验
            for f, pin in PINNED_CALC[param].items():
                if f in vals and vals[f] != pin:
                    warnings.append(
                        f"{ctx}: calc_meta.{f}={vals[f]:g} 偏离统一口径钉死值 "
                        f"{pin:g}（retrieval-paths.md 第 9 节），跨城不可比，"
                        f"须按钉死值重算或书面说明口径理由")
            val = x.get("value")
            val_ok = (isinstance(val, (int, float)) and not isinstance(val, bool)
                      and math.isfinite(val))
            # v1.6：自建比值参数登记质性 string 值属登记事故，无法回算比对 → 错误
            if isinstance(val, str) and val.strip():
                errors.append(
                    f"{ctx}: {param} 为自建比值参数且带 calc_meta，value 须为数值"
                    f"以回算比对（retrieval-paths.md 第 9 节），"
                    f"实为 string: {val!r}")
            elif cm_ok and val_ok:
                if param == "hpi":
                    recomputed = (vals["price"] * vals["area_sqm"]
                                  / (vals["income"] * vals["household_size"]))
                else:
                    recomputed = vals["rent_monthly"] * 12 / vals["income"]
                dev = abs(val - recomputed) / abs(recomputed)
                # v1.6：epsilon 容差消除浮点边界抖动（数学恰好 2% 放行）
                if dev > CALC_TOLERANCE + CALC_EPS:
                    errors.append(
                        f"{ctx}: calc_meta 回算值 {recomputed:g} 与登记 value {val} "
                        f"相对偏差 {dev:.4%} > 2%——value 与 calc_meta 不自洽，"
                        f"须按第 9 节统一口径重算")
    # city/param 为空字符串视为未覆盖，不进 coverage 矩阵；
    # v1.6：键 strip 空白归一化（与质性 value 的 strip 对齐），
    # 避免尾空格绕过 merge 同键检测或在 coverage 产生重复城市行
    if isinstance(city, str) and city.strip() and isinstance(param, str):
        return (city.strip(), param.strip())
    return None


def build_matrix(keys):
    """城市×参数覆盖矩阵：{城市: {参数: 条数}}，列序固定 PARAM_ORDER 再附未知参数。"""
    matrix = {}
    for city, param in keys:
        if not city or not param:
            continue
        matrix.setdefault(city, {}).setdefault(param, 0)
        matrix[city][param] += 1
    params = [p for p in PARAM_ORDER if any(p in m for m in matrix.values())]
    extra = sorted({p for m in matrix.values() for p in m} - set(PARAM_ORDER))
    return {"cities": sorted(matrix), "params": params + extra,
            "matrix": matrix, "entry_count": len(keys)}


def _as_finite_float(v):
    """数值或可数值化 string 统一为有限 float（"10" 与 10.0 视为同值，v1.6）；
    不可数值化（含 "nan"/"inf" 等非有限形态）返回 None，走质性比较。"""
    if isinstance(v, float):
        return v
    if isinstance(v, str):
        try:
            f = float(v)
        except ValueError:
            return None
        return f if math.isfinite(f) else None
    return None


def merge_conflicts(occurrences, errors, warnings):
    """--merge 跨文件检测：同一 (city,param) 多次登记时按 5% 阈值判冲突/取新。

    occurrences: {(city, param): [(value, ctx), ...]}，value 为有限数值或非空 string。
    v1.6：质性比较前先尝试 float() 数值化——全体可数值化即走数值偏差分支。
    """
    for (city, param), occ in sorted(occurrences.items()):
        if len(occ) < 2:
            continue
        detail = "，".join(f"{ctx}={v!r}" for v, ctx in occ)
        head = f"[merge] ({city!r}, {param!r}) 多次登记（{detail}）"
        nums = [_as_finite_float(v) for v, _ in occ]
        if all(n is not None for n in nums):
            vals = nums
            max_dev = max(
                (abs(a - b) / max(abs(a), abs(b)) if max(abs(a), abs(b)) else 0.0)
                for x, a in enumerate(vals) for b in vals[x + 1:])
            if max_dev > MERGE_TOLERANCE:
                errors.append(f"{head}：value 相对偏差 {max_dev:.1%} > 5%，"
                              f"值冲突——须核对口径后保留一个")
            else:
                warnings.append(f"{head}：相对偏差 {max_dev:.1%} ≤ 5%，"
                                f"重复登记取新（以后出现文件/条目为准）")
        elif len({v for v, _ in occ}) == 1:
            warnings.append(f"{head}：质性值相同，重复登记取新"
                            f"（以后出现文件/条目为准）")
        else:
            errors.append(f"{head}：质性 string 值不一致，值冲突"
                          f"（无偏差口径，须核对后保留一个）")


def merge_comparability(comp_by_param, n_missing, warnings):
    """v1.7 --merge 口径混杂检测：同一 param 跨城条目 comparability 取值混杂 → WARNING。

    comp_by_param: {param: {comparability: set(cities)}}，仅含填了合法
    comparability 的无错误条目；n_missing 为缺 comparability 的无错误条目数。
    缺失条目不参与混杂检测（历史条目过渡），仅一次性 WARNING 建议补登。
    """
    for param in sorted(comp_by_param):
        groups = comp_by_param[param]
        cities_all = set().union(*groups.values())
        # 跨城横比才判口径剪切：≥2 个取值且横跨 ≥2 个城市
        if len(groups) >= 2 and len(cities_all) >= 2:
            detail = "；".join(f"{c}: {'、'.join(sorted(groups[c]))}"
                              for c in COMPARABILITY if c in groups)
            warnings.append(
                f"[merge] 口径剪切：param {param!r} 跨城条目 comparability "
                f"取值混杂（{detail}）——该参数跨城横比须先对齐"
                f"（retrieval-paths.md 第 9.4 节）")
    if n_missing:
        warnings.append(
            f"[merge] {n_missing} 条无错误条目缺 comparability 字段——缺失条目"
            f"不参与口径混杂检测；v1.7 起建议补登 full/proxy/stale"
            f"（retrieval-paths.md 第 4 节），跨城横比前逐条核对口径")


def emit_pretty(out, code):
    """人类可读输出：错误/警告清单 + 覆盖矩阵表。"""
    cov = out["coverage"]
    print(f"检索登记校验：{cov['entry_count']} 条，"
          f"{len(out['errors'])} 错误 / {len(out['warnings'])} 警告")
    if "merge" in out:
        print(f"合并模式：{len(out['merge']['files'])} 文件（"
              + "、".join(out['merge']['files']) + "）")
    if out["errors"]:
        print("\n[错误]（阻断）")
        for e in out["errors"]:
            print(f"  - {e}")
    if out["warnings"]:
        print("\n[警告]")
        for w in out["warnings"]:
            print(f"  - {w}")
    print("\n[城市×参数覆盖矩阵]")
    if not cov["cities"]:
        print("  （无有效条目）")
    else:
        header = "城市".ljust(8) + "".join(p.ljust(16) for p in cov["params"])
        print("  " + header)
        for c in cov["cities"]:
            row = c.ljust(8) + "".join(
                str(cov["matrix"][c].get(p, "·")).ljust(16) for p in cov["params"])
            print("  " + row)
    sys.exit(code)


def load_entries(path):
    """读取 entries.json（'-' 表示 stdin）；失败 die(exit 2)。"""
    if path == "-":
        try:
            items = json.load(sys.stdin)
        except ValueError as e:
            die(f"stdin 不是合法 JSON: {e}")
    else:
        try:
            with open(path, encoding="utf-8") as f:
                items = json.load(f)
        except (OSError, ValueError) as e:
            die(f"无法读取 entries.json {path}: {e}")
    if not isinstance(items, list):
        die("entries.json must be a JSON array")
    return items


def run_validation(files, merge, today):
    """校验一个或多个 entries 文件；返回输出 dict（merge 时含跨文件检测）。"""
    errors, warnings, keys = [], [], []
    occurrences = {}  # (city,param) -> [(value, ctx)]，仅无错误条目，供 merge 检测
    comp_by_param = {}  # param -> {comparability: set(cities)}，v1.7 口径混杂检测
    n_comp_missing = 0  # 缺 comparability 的无错误条目数（v1.7，一次性补登提示）
    for path in files:
        items = load_entries(path)
        # 单文件保持历史消息格式；merge 消息前缀文件名
        ctx_prefix = (f"{os.path.basename(path)}:entries"
                      if merge and path != "-" else "entries")
        for i, x in enumerate(items):
            n_err = len(errors)
            k = validate_entry(x, i, errors, warnings, today, ctx_prefix)
            # coverage/merge 检测只统计无错误的条目；空 city/param 已由返回 None 排除
            if k and len(errors) == n_err:
                keys.append(k)
                v = x["value"]
                if isinstance(v, (int, float)) and not isinstance(v, bool) \
                        and math.isfinite(v):
                    occurrences.setdefault(k, []).append(
                        (float(v), f"{ctx_prefix}[{i}]"))
                elif isinstance(v, str) and v.strip():
                    occurrences.setdefault(k, []).append(
                        (v.strip(), f"{ctx_prefix}[{i}]"))
                # v1.7：收集 comparability 供 merge 口径混杂检测（缺失则计数）
                comp_v = x.get("comparability")
                if isinstance(comp_v, str) and comp_v in COMPARABILITY:
                    comp_by_param.setdefault(k[1], {}).setdefault(
                        comp_v, set()).add(k[0])
                else:
                    n_comp_missing += 1
    out = {"errors": errors, "warnings": warnings, "coverage": build_matrix(keys)}
    if merge:
        merge_conflicts(occurrences, errors, warnings)
        merge_comparability(comp_by_param, n_comp_missing, warnings)
        out["merge"] = {"files": [os.path.basename(p) for p in files]}
    return out


def main():
    ap = argparse.ArgumentParser(
        description="校验外部检索登记 entries.json：schema/URL/check_date/"
                    "conf↔source_type 越级/有效期超期/calc_meta 回算/覆盖矩阵；"
                    "v1.7 可选字段 comparability/source_chain/evidence_band 校验"
                    "（indirect 转引 conf 上限 C）；"
                    "--merge 做多文件合并校验与跨文件值冲突检测（v1.7 增同 param "
                    "跨城 comparability 口径混杂 WARNING）。",
        epilog="退出码: 0=无错误（可有警告），1=有错误，2=用法/IO 错误。"
               "schema 与纪律见 references/retrieval-paths.md"
               "（calc_meta 与 --merge 口径见第 9 节，"
               "comparability/source_chain 见第 4 节，evidence_band 见第 10 节）。",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entries_json", nargs="+",
                    help="entries.json 路径；'-' 表示从 stdin 读取（单文件模式）")
    ap.add_argument("--pretty", action="store_true",
                    help="输出人类可读文本（默认输出 JSON 契约）")
    ap.add_argument("--merge", action="store_true",
                    help="多文件合并校验：逐文件校验后跨文件检测同一 (city,param) "
                         "值冲突（相对偏差 >5%% 错误，≤5%% 重复登记取新 WARNING），"
                         "输出合并覆盖矩阵；v1.7 增同 param 跨城 comparability "
                         "口径混杂 WARNING（口径剪切）；需 ≥2 个文件，不支持 stdin")
    a = ap.parse_args()

    if a.merge:
        if len(a.entries_json) < 2:
            die("--merge 需要至少两个 entries.json 文件")
        if "-" in a.entries_json:
            die("--merge 模式不支持 stdin（'-'）")
    elif len(a.entries_json) != 1:
        die("多文件校验须显式使用 --merge（单文件用法不变）")

    today = datetime.datetime.now(datetime.timezone.utc).date()  # UTC 钉死
    out = run_validation(a.entries_json, a.merge, today)
    code = 1 if out["errors"] else 0
    if a.pretty:
        emit_pretty(out, code)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(code)


if __name__ == "__main__":
    main()
