#!/usr/bin/env python3
"""convergence_check.py v2.1 — 收敛判定：审计发现登记表 → CONVERGED / NOT CONVERGED / STAGNATED。

用法:
    python3 convergence_check.py findings.json                 # 旧用法，行为不变
    python3 convergence_check.py --findings findings.json      # 等价旧用法
    python3 convergence_check.py findings.json --prev 上轮输出.json
    python3 convergence_check.py findings.json --usability-checks a.py b.json ...
    python3 convergence_check.py findings.json --consistency-dir <被修文档目录>
    python3 convergence_check.py findings.json --verify-evidence

findings.json 格式:
    [{"id": "P1", "severity": "blocker|high|medium|low", "status": "open|closed",
      "note": "...", "accept_reason": "...", "scheduled": "...",
      "verify": {"type": "grep", "pattern": "<正则>", "file": "<路径>",
                 "expect": "present|absent"}}]   # verify 可选，见 --verify-evidence

判定规则（与 iteration-convergence-ops 对齐）：
    CONVERGED  ⇔  无 open 的 blocker/high，且 open 的 medium 全部带 accept_reason 或 scheduled。
    NOT CONVERGED ⇔ 否则；输出最小修复清单（open 项按严重度排序）。
    STAGNATED  ⇔  提供 --prev 时，本轮与上轮 verdict 均为未收敛（NOT CONVERGED 或 STAGNATED），
                  且两轮 open 的 blocker/high 条目 id 集合完全相同【且非空】（空集不判停滞）；
                  提示主代理更换修复策略。

severity/status 规范化（v2.1）：
    severity、status 统一 lower() 后映射；未知 severity → stderr WARNING 并按 blocker
    （最严重）处理；未知/缺失 status → stderr WARNING 并视为 open。绝不静默放行。

v2 新增（全部为可选开关，不带时与 v1 行为一致）：
    --prev <上轮输出JSON>      停滞比对；命中时 verdict=STAGNATED，exit code=3。
                               --prev 文件不存在/不可读/JSON 解析失败 → exit 2（用法错误）。
    --usability-checks <f...>  可用性自动检查：.py 跑 py_compile、.json 跑 json.load；
                               失败者自动追加 blocker 级 finding（id 前缀 USE-，
                               与现有 id 碰撞时自动顺延编号，source="usability_check"）
                               后再判定。【文件不存在按检查失败处理（追加 USE- blocker）；
                               目录/其他扩展名跳过并列入输出的 usability_skipped。】
    --consistency-dir <目录>   三方一致性自动核验：CHANGELOG.md 末条数据行 change_id、
                               k3_notices.jsonl 末条 change_id、目录内 .md/.py/.txt/.tex
                               文头块（<!-- AI_READER_NOTICE ... -->、
                               # AI_READER_NOTICE ... # END_AI_READER_NOTICE、
                               % AI_READER_NOTICE ... % END_AI_READER_NOTICE）中
                               最新 change_id；三者不一致时追加 blocker CONS-1
                               （id 碰撞自动顺延）。「最新」规则：先取 date 最大者，
                               同 date 平手按 change_id 字典序取最大（change_id 由主代理
                               集中分配、序号零填充，字典序==序号序）。
                               change_id 内嵌日期（CHG-YYYYMMDD-…）与块内 date 字段
                               不一致时输出 WARNING（不阻断）。
                               目录缺 CHANGELOG.md / k3_notices.jsonl 时记 WARNING，
                               跳过判定（不追加 blocker）。

v2.1 新增：
    --verify-evidence          对 status=closed 且携带 verify 规范的 findings 条目实跑
                               证据核验（当前支持 type=grep：在 file 中搜索正则 pattern，
                               expect=present 要求命中、absent 要求不命中；file 相对路径
                               先按 cwd、再按 findings.json 所在目录解析）。核验失败
                               （含文件缺失、规范非法、expect 未知）→ 自动改回 open 并写入
                               reopen_reason，参与本轮判定（防止虚假关闭骗出 CONVERGED）。

数据错误（exit 2，JSON 契约字段仍输出并附 errors 列表，不 traceback）：
    findings 含非对象条目、open 的 blocker/high 条目缺 id、
    --prev 的 minimal_fix_list 含非对象条目或 blocker/high 条目缺 id。

退出码: 0=CONVERGED，1=NOT CONVERGED，2=用法/IO/数据错误，3=STAGNATED。
输出字段: verdict / counts / minimal_fix_list / stagnated_with / usability_failures /
          usability_skipped / verify_evidence / consistency / rounds_metrics（+ errors）。
纯标准库。
"""
import argparse, json, os, py_compile, re, sys, tempfile

ORDER = {"blocker": 0, "high": 1, "medium": 2, "low": 3}
# 文头块扫描的扩展名（协议规定 .md/.txt 用 HTML 注释块，.py 用 # 行块，.tex 用 % 行块）
HEADER_EXTS = {".md", ".py", ".txt", ".tex"}
# 文头块内的机器可读字段
RE_CHANGE_ID = re.compile(r"change_id:\s*(\S+)")
RE_DATE = re.compile(r"\bdate:\s*(\d{4}-\d{2}-\d{2})")
# change_id 内嵌日期（CHG-YYYYMMDD-…），用于 G3 日期一致性 WARNING
RE_CID_DATE = re.compile(r"CHG-(\d{4})(\d{2})(\d{2})-")
# 三种文头块格式（与 notice_stamp.py 生成格式对齐）
RE_HTML_BLOCK = re.compile(r"<!-- AI_READER_NOTICE(.*?)-->", re.S)
RE_HASH_BLOCK = re.compile(r"# AI_READER_NOTICE\n((?:#.*\n)*?)# END_AI_READER_NOTICE")
RE_PERCENT_BLOCK = re.compile(r"% AI_READER_NOTICE\n((?:%.*\n)*?)% END_AI_READER_NOTICE")


def die(msg):
    """用法/IO 错误：打印到 stderr，退出码 2（无 JSON 输出）。"""
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def emit(out, code):
    """输出 JSON 契约并以 code 退出（数据错误路径也走这里，保证契约字段在）。"""
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(code)


def load_json(path, what):
    """读取 JSON 文件；失败视为 IO 错误（exit 2）。"""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        die(f"无法读取{what} {path}: {e}")


def base_out():
    """JSON 契约骨架（数据错误路径也输出此结构 + errors）。"""
    return {"verdict": None,
            "counts": {s: 0 for s in ("blocker", "high", "medium", "low")},
            "minimal_fix_list": [],
            "stagnated_with": None,
            "usability_failures": [],
            "usability_skipped": [],
            "verify_evidence": None,
            "consistency": None,
            "rounds_metrics": {
                "open_count_this_round": 0,
                "rounds_to_converge": None,
                "note": "rounds_to_converge 与轮均关闭率由调用方在轮次日志中累计，"
                        "本字段仅为占位"},
            "errors": []}


def fail_data(errors, out=None):
    """数据错误：stderr 逐条告警 + 输出契约 JSON（含 errors）+ exit 2。"""
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    out = out or base_out()
    out["errors"] = errors
    emit(out, 2)


def norm_severity(raw, ctx, warnings):
    """severity 规范化：lower() 后映射；未知值 → WARNING + 按 blocker（最严重）处理。"""
    s = raw.strip().lower() if isinstance(raw, str) else None
    if s not in ORDER:
        warnings.append(f"{ctx}: 未知 severity {raw!r}，按 blocker（最严重）处理")
        return "blocker"
    return s


def norm_status(raw, ctx, warnings):
    """status 规范化：lower() 后映射；未知/缺失 → WARNING + 视为 open。"""
    s = raw.strip().lower() if isinstance(raw, str) else None
    if s not in ("open", "closed"):
        warnings.append(f"{ctx}: 未知/缺失 status {raw!r}，视为 open")
        return "open"
    return s


def validate_findings(items, errors, warnings):
    """findings 条目校验 + 规范化（就地）。

    - 非 dict 条目 → errors（数据错误，exit 2）
    - severity/status 规范化（未知值 WARNING，保守处理）
    - open 的 blocker/high 缺 id → errors（无法参与停滞 id 集比对）
    """
    for i, x in enumerate(items):
        ctx = f"findings[{i}]"
        if not isinstance(x, dict):
            errors.append(f"{ctx} 不是 JSON 对象: {x!r}")
            continue
        ctx = f"findings[{i}](id={x.get('id')!r})"
        x["severity"] = norm_severity(x.get("severity"), ctx, warnings)
        x["status"] = norm_status(x.get("status"), ctx, warnings)
        if (x["status"] == "open" and x["severity"] in ("blocker", "high")
                and not x.get("id")):
            errors.append(f"{ctx} 是 open 的 blocker/high 但缺 id，"
                          f"无法参与停滞判定，请补 id")


def validate_prev(prev, errors, warnings):
    """--prev 输出校验 + severity 规范化（就地）。返回 (prev_verdict, prev_list)。"""
    if not isinstance(prev, dict):
        warnings.append("--prev 输出不是 JSON 对象，按无上轮处理（不判停滞）")
        return None, []
    prev_verdict = prev.get("verdict")
    prev_list = prev.get("minimal_fix_list", [])
    if not isinstance(prev_list, list):
        errors.append("--prev 的 minimal_fix_list 不是数组")
        return prev_verdict, []
    for i, x in enumerate(prev_list):
        ctx = f"prev.minimal_fix_list[{i}]"
        if not isinstance(x, dict):
            errors.append(f"{ctx} 不是 JSON 对象: {x!r}")
            continue
        ctx = f"{ctx}(id={x.get('id')!r})"
        x["severity"] = norm_severity(x.get("severity"), ctx, warnings)
        if x["severity"] in ("blocker", "high") and not x.get("id"):
            errors.append(f"{ctx} 是 blocker/high 但缺 id，无法参与停滞判定")
    return prev_verdict, prev_list


def open_blocker_high_ids(items):
    """open 的 blocker/high 条目 id 集合（停滞比对基准）。调用前须经 validate_findings。"""
    return sorted(x["id"] for x in items
                  if isinstance(x, dict)
                  and x.get("status") == "open"
                  and x.get("severity") in ("blocker", "high"))


def next_free_id(items, prefix):
    """分配不与现有 id 碰撞的自动编号（USE-1/CONS-1 碰撞时顺延）。"""
    existing = {x.get("id") for x in items if isinstance(x, dict)}
    i = 1
    while f"{prefix}{i}" in existing:
        i += 1
    return f"{prefix}{i}"


def usability_checks(paths):
    """可用性检查：.py → py_compile（不落地 .pyc），.json → json.load。

    返回 (failures, checked, skipped)；failures 元素为 {file, check, error}。
    文件不存在按失败处理（OSError → failures）；目录/其他扩展名进 skipped。
    """
    failures, checked, skipped = [], [], []
    for p in paths:
        ext = os.path.splitext(p)[1].lower()
        try:
            if ext == ".py":
                # cfile 指向临时文件，避免在目标目录生成 __pycache__
                fd, tmp = tempfile.mkstemp(suffix=".pyc")
                os.close(fd)
                try:
                    py_compile.compile(p, cfile=tmp, doraise=True)
                finally:
                    os.unlink(tmp)
                checked.append(p)
            elif ext == ".json":
                with open(p, encoding="utf-8") as f:
                    json.load(f)
                checked.append(p)
            else:
                skipped.append(p)  # 非 .py/.json 不在检查范围
        except (py_compile.PyCompileError, OSError, ValueError) as e:
            failures.append({"file": p,
                             "check": "py_compile" if ext == ".py" else "json.load",
                             # 保留完整错误文本（PyCompileError 首行只是文件名，
                             # 真正的 SyntaxError 描述在后续行）
                             "error": str(e).strip() or repr(e)})
    return failures, checked, skipped


def changelog_last_change_id(path):
    """CHANGELOG.md 最后一行数据行的 change_id（表行第二列）。"""
    last = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s.startswith("|"):
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) < 2:
                continue
            # 跳过表头行与分隔行
            if cells[0] == "date" or all(re.fullmatch(r":?-+:?", c) for c in cells):
                continue
            last = cells[1]
    return last


def k3_last_change_id(path):
    """k3_notices.jsonl 末条 JSON 的 change_id（跳过空行与坏行）。"""
    last = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            try:
                rec = json.loads(s)
            except ValueError:
                continue
            if isinstance(rec, dict) and rec.get("change_id"):
                last = rec["change_id"]
    return last


def header_blocks(directory):
    """扫描目录内 .md/.py/.txt/.tex 文头块。

    返回 [{file, change_id, date}]（date 缺失为 ""）。三种块格式均识别。
    """
    found = []
    for name in sorted(os.listdir(directory)):
        if os.path.splitext(name)[1].lower() not in HEADER_EXTS:
            continue
        path = os.path.join(directory, name)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
        blocks = [m.group(1) for m in RE_HTML_BLOCK.finditer(text)]
        blocks += [m.group(1) for m in RE_HASH_BLOCK.finditer(text)]
        blocks += [m.group(1) for m in RE_PERCENT_BLOCK.finditer(text)]
        for b in blocks:
            cid = RE_CHANGE_ID.search(b)
            if not cid:
                continue
            dt = RE_DATE.search(b)
            found.append({"file": name, "change_id": cid.group(1),
                          "date": dt.group(1) if dt else ""})
    return found


def consistency_check(directory):
    """三方一致性核验。

    「文头块最新」规则（v2.1 修订，修复同日多文件平手误报）：
        先取 date 最大的全部块；同 date 平手按 change_id 字典序取最大。
        change_id 由主代理集中分配且序号零填充（CHG-YYYYMMDD-###），
        字典序 == 分配先后序，故同日修多文件时真实最新者必胜出，与文件名无关。

    返回 (result_dict, cons_finding_or_None)。
    """
    warnings = []
    res = {"dir": directory, "changelog_last": None, "k3_last": None,
           "header_latest": None, "header_latest_set": [],
           "consistent": None, "warnings": warnings}
    changelog = os.path.join(directory, "CHANGELOG.md")
    k3log = os.path.join(directory, "k3_notices.jsonl")
    # 缺 CHANGELOG / k3_notices → WARNING，跳过判定（不判 blocker）
    missing = [p for p in (changelog, k3log) if not os.path.isfile(p)]
    if missing:
        warnings.append("缺少留痕文件，跳过三方一致性判定: " + ", ".join(missing))
        return res, None
    try:
        res["changelog_last"] = changelog_last_change_id(changelog)
        res["k3_last"] = k3_last_change_id(k3log)
        headers = header_blocks(directory)
    except OSError as e:
        warnings.append(f"读取留痕文件失败，跳过判定: {e}")
        return res, None
    # G3：change_id 内嵌日期与块内 date 字段不一致 → WARNING（不阻断）
    for h in headers:
        m = RE_CID_DATE.search(h["change_id"])
        if m and h["date"]:
            cid_date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
            if cid_date != h["date"]:
                warnings.append(
                    f"{h['file']}: change_id {h['change_id']} 内嵌日期 {cid_date} "
                    f"与块内 date 字段 {h['date']} 不一致")
    if headers:
        max_date = max(h["date"] for h in headers)
        latest_set = sorted(h["change_id"] for h in headers if h["date"] == max_date)
        res["header_latest_set"] = latest_set
        res["header_latest"] = latest_set[-1]  # 同 date 平手取 change_id 最大者
    vals = (res["changelog_last"], res["k3_last"], res["header_latest"])
    res["consistent"] = vals[0] is not None and len(set(vals)) == 1
    if res["header_latest"] is None:
        warnings.append("目录内 .md/.py/.txt/.tex 未找到含 change_id 的 "
                        "AI_READER_NOTICE 文头块")
    if not res["consistent"]:
        finding = {"id": "CONS-1", "severity": "blocker", "status": "open",
                   "source": "consistency_check",
                   "note": ("三方 change_id 不一致: CHANGELOG末行=%s, k3_notices末条=%s, "
                            "文头块最新=%s（同date集合=%s）"
                            % (vals[0], vals[1], vals[2], res["header_latest_set"]))}
        return res, finding
    return res, None


def verify_closed_evidence(items, findings_dir):
    """--verify-evidence：对 status=closed 且带 verify 规范的条目实跑核验。

    当前支持 type=grep：在 file 中搜索正则 pattern，expect=present 要求命中、
    absent 要求不命中。核验失败（含文件缺失/规范非法/expect 未知）→ 改回 open
    并写 reopen_reason。返回结果列表（供输出）。
    """
    results = []
    for x in items:
        if not isinstance(x, dict):
            continue
        v = x.get("verify")
        if v is None or x.get("status") != "closed":
            continue
        rec = {"id": x.get("id"), "ok": False, "detail": ""}
        if not isinstance(v, dict) or v.get("type") != "grep":
            rec["detail"] = f"不支持的 verify 规范（仅支持 type=grep）: {v!r}"
        else:
            pattern, file, expect = v.get("pattern"), v.get("file"), v.get("expect")
            if not pattern or not file:
                rec["detail"] = f"verify 规范缺 pattern/file: {v!r}"
            elif expect not in ("present", "absent"):
                rec["detail"] = f"verify.expect 未知（应 present|absent）: {expect!r}"
            else:
                path = file
                if not os.path.isabs(path) and not os.path.exists(path):
                    alt = os.path.join(findings_dir, path)
                    if os.path.exists(alt):
                        path = alt
                if not os.path.isfile(path):
                    rec["detail"] = f"verify.file 不存在: {file}"
                else:
                    try:
                        rx = re.compile(pattern)
                        with open(path, encoding="utf-8", errors="replace") as f:
                            matched = bool(rx.search(f.read()))
                        ok = matched if expect == "present" else not matched
                        rec["ok"] = ok
                        rec["detail"] = (f"grep {pattern!r} {file}: "
                                         f"{'命中' if matched else '未命中'}"
                                         f"（expect={expect}）")
                    except re.error as e:
                        rec["detail"] = f"verify.pattern 正则非法: {e}"
        results.append(rec)
        if not rec["ok"]:
            x["status"] = "open"
            x["reopen_reason"] = f"verify-evidence 复核失败: {rec['detail']}"
    return results


def main():
    ap = argparse.ArgumentParser(
        description="收敛判定 v2.1：findings.json → CONVERGED / NOT CONVERGED / STAGNATED，"
                    "可选可用性检查、三方一致性核验与 closed 证据复核。",
        epilog="退出码: 0=CONVERGED, 1=NOT CONVERGED, 2=用法/IO/数据错误（数据错误仍输出"
               " JSON 契约 + errors 字段）, 3=STAGNATED。不带任何 v2 开关时行为与 v1 一致。"
               "缺失文件策略：findings/--prev 文件不可读 → exit 2；--usability-checks "
               "点名的文件不存在 → 按检查失败追加 USE- blocker（exit 1）；"
               "--consistency-dir 缺留痕文件 → 仅 WARNING 跳过判定。",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("findings_json", nargs="?", default=None,
                    help="findings.json 路径（位置参数，旧用法；文件不可读 → exit 2）")
    ap.add_argument("--findings", dest="findings_opt", default=None,
                    help="findings.json 路径（与位置参数等价，二选一）")
    ap.add_argument("--prev", default=None, metavar="上轮输出JSON",
                    help="上一轮本脚本的输出 JSON（文件不可读 → exit 2）；两轮均未收敛且 "
                         "open 的 blocker/high id 集合完全相同且非空时判 STAGNATED（exit 3）"
                         "；空集不判停滞")
    ap.add_argument("--usability-checks", nargs="+", default=None,
                    metavar="FILE", help="可用性检查文件清单：.py 跑 py_compile、"
                                         ".json 跑 json.load；失败（含文件不存在）自动追加 "
                                         "USE- 前缀的 blocker finding 后再判定；目录/其他"
                                         "扩展名跳过并列入输出的 usability_skipped")
    ap.add_argument("--consistency-dir", default=None, metavar="目录",
                    help="三方一致性核验目录：CHANGELOG.md 末行 change_id、"
                         "k3_notices.jsonl 末条 change_id、文头块最新 change_id（同 date "
                         "平手取 change_id 最大者）三者不一致时追加 blocker CONS-1；"
                         "缺留痕文件只记 WARNING；change_id 内嵌日期与块内 date 不一致"
                         "只记 WARNING")
    ap.add_argument("--verify-evidence", action="store_true",
                    help="对 status=closed 且带 verify 规范（type=grep）的条目实跑证据"
                         "核验；失败自动改回 open 并标 reopen_reason（防虚假关闭）")
    a = ap.parse_args()

    findings_path = a.findings_opt or a.findings_json
    if not findings_path:
        ap.error("必须提供 findings.json（位置参数或 --findings）")  # exit 2

    items = load_json(findings_path, "findings.json")
    if not isinstance(items, list):
        die("findings.json must be a JSON array")

    # ---- 数据校验 + severity/status 规范化（M1/M2/M3：不 traceback、不静默放行）----
    errors, warnings = [], []
    validate_findings(items, errors, warnings)
    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    if errors:
        fail_data(errors)

    # ---- v2.1：closed 条目证据复核（在判定前把假关闭改回 open）----
    verify_evidence = None
    if a.verify_evidence:
        findings_dir = os.path.dirname(os.path.abspath(findings_path))
        verify_evidence = verify_closed_evidence(items, findings_dir)
        for rec in verify_evidence:
            if not rec["ok"]:
                print(f"WARNING: verify-evidence 复核失败，已改回 open: "
                      f"id={rec['id']} {rec['detail']}", file=sys.stderr)

    # ---- v2 特性 2：可用性自动检查（在判定前把失败项追加为 blocker finding）----
    usability_failures, usability_checked, usability_skipped = [], [], []
    if a.usability_checks:
        usability_failures, usability_checked, usability_skipped = \
            usability_checks(a.usability_checks)
        for fail in usability_failures:
            items.append({"id": next_free_id(items, "USE-"),
                          "severity": "blocker", "status": "open",
                          "source": "usability_check",
                          "note": f"可用性检查失败: {fail['file']} "
                                  f"未通过 {fail['check']} ({fail['error']})"})

    # ---- v2 特性 3：三方一致性自动核验（同样在判定前追加 CONS-n）----
    consistency = None
    if a.consistency_dir:
        if not os.path.isdir(a.consistency_dir):
            die(f"--consistency-dir 不是目录: {a.consistency_dir}")
        consistency, cons_finding = consistency_check(a.consistency_dir)
        for w in consistency["warnings"]:
            print(f"WARNING: {w}", file=sys.stderr)
        if cons_finding:
            cons_finding["id"] = next_free_id(items, "CONS-")
            items.append(cons_finding)

    # ---- 判定（与 v1 相同；自动追加/改回的 finding 已并入 items）----
    open_items = [x for x in items if x.get("status") == "open"]
    blockers = [x for x in open_items if x.get("severity") in ("blocker", "high")]
    meds_unjustified = [x for x in open_items
                        if x.get("severity") == "medium"
                        and not (x.get("accept_reason") or x.get("scheduled"))]
    verdict = "CONVERGED" if not blockers and not meds_unjustified else "NOT CONVERGED"
    residual = sorted(open_items,
                      key=lambda x: ORDER.get(x.get("severity", "low"), 9))

    # ---- v2 特性 1：STAGNATED 判定（与上轮输出比对 open blocker/high id 集合）----
    stagnated_with = None
    if a.prev:
        prev = load_json(a.prev, "--prev 上轮输出")
        prev_errors, prev_warnings = [], []
        prev_verdict, prev_list = validate_prev(prev, prev_errors, prev_warnings)
        for w in prev_warnings:
            print(f"WARNING: {w}", file=sys.stderr)
        if prev_errors:
            out = base_out()
            out.update({"verdict": verdict,
                        "counts": {s: sum(1 for x in open_items
                                        if x.get("severity") == s)
                                   for s in ("blocker", "high", "medium", "low")},
                        "usability_failures": usability_failures,
                        "usability_skipped": usability_skipped,
                        "verify_evidence": verify_evidence,
                        "consistency": consistency})
            fail_data(prev_errors, out)
        prev_ids = sorted(x["id"] for x in prev_list
                          if isinstance(x, dict)
                          and x.get("severity") in ("blocker", "high")
                          and x.get("id"))
        cur_ids = open_blocker_high_ids(items)
        identical = prev_ids == cur_ids
        # H2 修复：空集恒等是假停滞——open blocker/high 集合为空时不判停滞
        # M4 修复：停滞措辞仅在 identical 且确实判停滞时写
        is_stagnated = (verdict == "NOT CONVERGED"
                        and prev_verdict in ("NOT CONVERGED", "STAGNATED")
                        and identical and bool(cur_ids))
        if is_stagnated:
            note = ("两轮均未收敛且 open blocker/high id 集合完全相同 → 停滞，"
                    "主代理须更换修复策略")
        elif identical and not cur_ids:
            note = "两轮 open blocker/high id 集合均为空，空集恒等不判停滞"
        elif identical:
            note = "id 集合相同但停滞条件未全部满足（本轮/上轮并非均未收敛），未判停滞"
        else:
            note = "id 集合有变化，未判停滞"
        stagnated_with = {
            "prev_file": a.prev,
            "prev_verdict": prev_verdict,
            "current_open_blocker_high_ids": cur_ids,
            "prev_open_blocker_high_ids": prev_ids,
            "identical": identical,
            "note": note,
        }
        # 上轮 STAGNATED 视为未收敛的延续，允许连续判定停滞
        if is_stagnated:
            verdict = "STAGNATED"

    out = {
        "verdict": verdict,
        "counts": {s: sum(1 for x in open_items if x.get("severity") == s)
                   for s in ("blocker", "high", "medium", "low")},
        "minimal_fix_list": [
            {"id": x.get("id"), "severity": x.get("severity"),
             "note": x.get("note", ""),
             **({"source": x["source"]} if x.get("source") else {}),
             **({"reopen_reason": x["reopen_reason"]} if x.get("reopen_reason") else {})}
            for x in residual],
        "stagnated_with": stagnated_with,
        "usability_failures": usability_failures,
        "usability_skipped": usability_skipped,
        "verify_evidence": verify_evidence,
        "consistency": consistency,
        # rounds_to_converge / 轮均关闭率由调用方（主代理）跨轮累计，
        # 本脚本只输出本轮 open 计数占位
        "rounds_metrics": {
            "open_count_this_round": len(open_items),
            "rounds_to_converge": None,
            "note": "rounds_to_converge 与轮均关闭率由调用方在轮次日志中累计，"
                    "本字段仅为占位",
        },
        "errors": [],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit({"CONVERGED": 0, "NOT CONVERGED": 1, "STAGNATED": 3}[verdict])


if __name__ == "__main__":
    main()
