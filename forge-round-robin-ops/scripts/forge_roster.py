# -*- coding: utf-8 -*-
"""forge_roster.py v1.0.0（2026-09-17 · 轮铸调度官核心脚本）
《forge-round-robin-ops》名册状态机：登记 → 能跑门（Phase A 静态） → 轮铸排期（Phase B） → 裁定回录。

用法：
  python forge_roster.py --init ROSTER.json                     # 建册（撞名拒写 exit 2）
  python forge_roster.py --register ROSTER.json --name N --src PATH [--version V] [--note T]
  python forge_roster.py --gate ROSTER.json (--name N | --all)  # Phase A 能跑门（静态，零执行）
  python forge_roster.py --next ROSTER.json                     # 排期决策：下一件锻谁+理由
  python forge_roster.py --advance ROSTER.json --name N --verdict KEEP|REVISE|FAIL [--note T]
  python forge_roster.py --status ROSTER.json                   # 名册总览
  python forge_roster.py --smoke                                # 自检（合成夹具，含负断言）

红线：外来脚本永不执行——能跑门只做编译级 compile() 与文本级检查（编译≠执行）；
roster.json 为单一事实源；裁定未回录，指针不推进。
"""
import argparse, hashlib, json, re, sys, tempfile, time, zipfile
from pathlib import Path

VERSION = "1.0.0"
PHASES = ("A-pending", "A-passed", "A-failed", "B-rounds", "alumni")


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def md5_path(p):
    """文件→字节 md5；目录→(相对路径+字节) 按序滚 md5，确定性。"""
    p = Path(p)
    h = hashlib.md5()
    if p.is_file():
        h.update(p.read_bytes())
        return h.hexdigest()
    for f in sorted(x for x in p.rglob("*") if x.is_file()):
        h.update(str(f.relative_to(p)).replace("\\", "/").encode())
        h.update(f.read_bytes())
    return h.hexdigest()


# ---------- 名册 IO（原子写） ----------

def load_roster(path):
    fp = Path(path)
    if not fp.exists():
        print(f"名册不存在: {fp}（先 --init）", file=sys.stderr)
        sys.exit(3)
    try:
        r = json.loads(fp.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"名册不可读/损坏，拒绝操作: {e}", file=sys.stderr)
        sys.exit(3)
    if not isinstance(r.get("skills"), list):
        print("名册 schema 缺 skills 列表，拒绝操作", file=sys.stderr)
        sys.exit(3)
    return r


def save_roster(path, r):
    fp = Path(path)
    tmp = fp.with_suffix(fp.suffix + ".tmp")
    tmp.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(fp)


def init_roster(path):
    fp = Path(path)
    if fp.exists():
        print(f"名册已存在，拒绝覆盖: {fp}", file=sys.stderr)
        sys.exit(2)
    save_roster(fp, {"schema": "forge-roster/1", "engine": VERSION,
                     "doctrine": "先能跑，再完善", "created": now(), "skills": []})
    print(f"roster -> {fp}")


# ---------- 登记 ----------

def register(path, name, src, version="", note=""):
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name):
        print(f"技能名须 kebab-case: {name!r}", file=sys.stderr)
        sys.exit(2)
    sp = Path(src)
    if not sp.exists():
        print(f"源不存在: {sp}", file=sys.stderr)
        sys.exit(1)
    r = load_roster(path)
    ent = next((s for s in r["skills"] if s["name"] == name), None)
    digest = md5_path(sp)
    if ent is None:
        ent = {"name": name, "phase": "A-pending", "registered_ts": now(),
               "gate": None, "gate_ts": None, "rounds": [], "last_round_ts": None}
        r["skills"].append(ent)
    else:  # 重新登记=源更新：若曾 A-failed 回炉过门，其余相位保留
        if ent["phase"] == "A-failed":
            ent["phase"] = "A-pending"
    ent.update({"src": str(sp), "version": version, "md5": digest,
                "note": note, "src_kind": "dir" if sp.is_dir() else "pkg"})
    save_roster(path, r)
    print(json.dumps({"registered": name, "phase": ent["phase"], "md5": digest},
                     ensure_ascii=False))


# ---------- Phase A 能跑门（纯静态：编译≠执行，文本≠运行） ----------

def parse_frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return None
    fm = "\n".join(lines[1:end])
    m = re.search(r"(?m)^name:\s*(\S+)\s*$", fm)
    name = m.group(1) if m else ""
    desc = ""
    dm = re.search(r"(?m)^description:\s*(.*)$", fm)
    if dm:
        buf = [dm.group(1).strip().lstrip(">").strip()]
        for ln in fm[dm.end():].splitlines()[1:]:
            if re.match(r"^[A-Za-z_]+:\s*", ln) and not ln.startswith((" ", "\t")):
                break
            buf.append(ln.strip())
        desc = " ".join(x for x in buf if x)
    return {"name": name, "description": desc, "body": "\n".join(lines[end + 1:])}


def _pkg_reader(src):
    """统一读取接口：返回 (files: {relpath: bytes}, skill_rel) 或 (None, 错误串)。
    dir → skill 根为 SKILL.md 所在层；pkg(.skill/.zip) → 内存读，不落盘。"""
    p = Path(src)
    if p.is_dir():
        cand = [p / "SKILL.md"] + sorted(p.glob("*/SKILL.md"))
        cand = [c for c in cand if c.exists()]
        if not cand:
            return None, "SKILL.md 缺失（根或一层子目录均未找到）"
        root = cand[0].parent
        files = {str(f.relative_to(root)).replace("\\", "/"): f.read_bytes()
                 for f in root.rglob("*") if f.is_file()}
        return files, "SKILL.md"
    try:
        zf = zipfile.ZipFile(p)
    except zipfile.BadZipFile:
        return None, "包非合法 zip"
    with zf:
        bad = zf.testzip()
        if bad:
            return None, f"zip 完整性失败: {bad}"
        names = zf.namelist()
        sk = [n for n in names if n.rstrip("/").endswith("SKILL.md") and n.count("/") <= 1]
        if not sk:
            return None, "包内 SKILL.md 缺失"
        prefix = sk[0][: -len("SKILL.md")]
        files = {n[len(prefix):]: zf.read(n) for n in names
                 if n.startswith(prefix) and not n.endswith("/")}
        return files, "SKILL.md"


def gate(src):
    """能跑门六检（全部静态）：1 源在 2 SKILL.md 在 3 frontmatter 合规
    4 相对链接可解 5 .py 编译级语法（compile 不 exec）6 scripts/ 引用在位。"""
    checks = []
    p = Path(src)
    ok0 = p.exists()
    checks.append({"check": "src-exists", "ok": ok0, "detail": str(src)})
    if not ok0:
        return {"runnable": False, "checks": checks}
    files, info = _pkg_reader(src)
    checks.append({"check": "skill-md", "ok": files is not None, "detail": info})
    if files is None:
        return {"runnable": False, "checks": checks}
    text = files["SKILL.md"].decode("utf-8", errors="replace")
    fm = parse_frontmatter(text)
    d3 = "frontmatter 无法解析"
    if fm:
        probs = []
        if not fm["name"] or not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", fm["name"]):
            probs.append(f"name 缺/非法: {fm['name']!r}")
        if not fm["description"]:
            probs.append("description 缺失")
        elif len(fm["description"]) > 1024:
            probs.append(f"description 超长 {len(fm['description'])}>1024")
        d3 = "；".join(probs) if probs else f"name={fm['name']} desc={len(fm['description'])}字符"
    checks.append({"check": "frontmatter", "ok": bool(fm) and "；" not in d3 and not d3.endswith("缺失"), "detail": d3})
    body = fm["body"] if fm else text
    dangling = []
    for ln in re.findall(r"\[[^\]]*\]\(([^)\s]+)(?:\s[^)]*)?\)", body):
        if "://" in ln or ln.startswith(("#", "mailto:")):
            continue
        ln = ln.split("#")[0]
        if ln and ln not in files:
            dangling.append(ln)
    checks.append({"check": "links", "ok": not dangling,
                   "detail": "悬空: " + ", ".join(dangling) if dangling else "全部可解"})
    bad_py = []
    for rel, data in files.items():
        if rel.endswith(".py"):
            try:
                compile(data.decode("utf-8", errors="replace"), rel, "exec")  # 编译≠执行
            except SyntaxError as e:
                bad_py.append(f"{rel}:{e.lineno}")
    checks.append({"check": "py-compile", "ok": not bad_py,
                   "detail": "语法错误: " + ", ".join(bad_py) if bad_py else "全部可编译"})
    missing = [m for m in re.findall(r"scripts/[\w.\-]+", body) if m not in files]
    checks.append({"check": "scripts-ref", "ok": not missing,
                   "detail": "缺: " + ", ".join(sorted(set(missing))) if missing else "引用均在位"})
    return {"runnable": all(c["ok"] for c in checks), "checks": checks}


def run_gate(path, name, all_):
    r = load_roster(path)
    targets = r["skills"] if all_ else [s for s in r["skills"] if s["name"] == name]
    if not targets:
        print(f"名册无此技能: {name}", file=sys.stderr)
        sys.exit(1)
    n_fail = 0
    for s in targets:
        rep = gate(s["src"])
        rep["ts"] = now()
        s["gate"] = rep
        s["gate_ts"] = rep["ts"]
        s["phase"] = "A-passed" if rep["runnable"] else "A-failed"
        n_fail += 0 if rep["runnable"] else 1
        print(json.dumps({"name": s["name"], "runnable": rep["runnable"],
                          "fails": [c["check"] for c in rep["checks"] if not c["ok"]]},
                         ensure_ascii=False))
    save_roster(path, r)
    if n_fail:
        sys.exit(1)


# ---------- Phase B 轮铸排期 ----------

def decide(r):
    acts = [s for s in r["skills"] if s["phase"] != "alumni"]
    if not acts:
        return None, "名册为空或全部 alumni（定案出队）"
    pending = [s for s in acts if s["phase"] in ("A-pending", "A-failed")]
    if pending:  # 先能跑：过门优先于一切完善
        pending.sort(key=lambda s: (s.get("gate_ts") or "", s["registered_ts"]))
        return pending[0], "先能跑：能跑门未过者优先（未检/失败早候）"
    pool = sorted(acts, key=lambda s: (s.get("last_round_ts") or "", s["registered_ts"]))
    return pool[0], "再完善：最久未锻者先轮（从未锻过最优先）"


def show_next(path):
    r = load_roster(path)
    s, why = decide(r)
    if s is None:
        print(json.dumps({"next": None, "reason": why}, ensure_ascii=False))
        return
    print(json.dumps({"next": s["name"], "phase": s["phase"], "version": s.get("version"),
                      "src": s["src"], "reason": why,
                      "action": "过能跑门 --gate" if s["phase"] in ("A-pending", "A-failed")
                      else "进完善轮（走 skill-forge-pipeline：D+短链/外池审判），裁定后 --advance 回录"},
                     ensure_ascii=False))


def advance(path, name, verdict, note):
    r = load_roster(path)
    s = next((x for x in r["skills"] if x["name"] == name), None)
    if s is None:
        print(f"名册无此技能: {name}", file=sys.stderr)
        sys.exit(1)
    if s["phase"] in ("A-pending", "A-failed"):
        print(f"硬闸：{name} 能跑门未过（{s['phase']}），禁入完善轮；先修复再过门", file=sys.stderr)
        sys.exit(3)
    s["rounds"].append({"ts": now(), "verdict": verdict, "note": note})
    s["last_round_ts"] = now()
    s["phase"] = "alumni" if verdict == "KEEP" else "B-rounds"
    save_roster(path, r)
    print(json.dumps({"advanced": name, "verdict": verdict, "phase": s["phase"],
                      "rounds": len(s["rounds"])}, ensure_ascii=False))


def status(path):
    r = load_roster(path)
    rows = [{"name": s["name"], "version": s.get("version"), "phase": s["phase"],
             "runnable": (s.get("gate") or {}).get("runnable"),
             "rounds": len(s["rounds"]),
             "last": (s["rounds"][-1]["verdict"] if s["rounds"] else "-")}
            for s in r["skills"]]
    nxt, why = decide(r)
    print(json.dumps({"engine": VERSION, "doctrine": r["doctrine"], "total": len(rows),
                      "by_phase": {p: sum(1 for x in r["skills"] if x["phase"] == p) for p in PHASES},
                      "next": nxt["name"] if nxt else None, "next_reason": why,
                      "skills": rows}, ensure_ascii=False, indent=1))


# ---------- 自检 ----------

def smoke():
    import subprocess
    root = Path(tempfile.mkdtemp(prefix="roster_smoke_"))
    roster = root / "roster.json"

    def mk_skill(d, desc="x", broken_py=False, bad_link=False, boom=False):
        d = Path(d)
        (d / "scripts").mkdir(parents=True, exist_ok=True)
        (d / "references").mkdir(exist_ok=True)
        (d / "scripts" / "a.py").write_text(
            "raise SystemExit('EXECUTED')\n" if boom else
            ("def f(:\n" if broken_py else "print('ok')\n"), encoding="utf-8")
        (d / "references" / "r.md").write_text("# r\n", encoding="utf-8")
        (d / "SKILL.md").write_text(
            "---\nname: %s\ndescription: >\n  %s\n---\n\n# t\n见 [r](references/r.md)%s\n"
            % (d.name, desc, " [坏](references/none.md)" if bad_link else ""), encoding="utf-8")
        return d

    good = mk_skill(root / "good-skill")
    brok = mk_skill(root / "broken-skill", broken_py=True)
    dang = mk_skill(root / "dangle-skill", bad_link=True)
    boom = mk_skill(root / "boom-skill", boom=True)
    nodesc = root / "nodesc-skill"
    nodesc.mkdir()
    (nodesc / "SKILL.md").write_text("---\nname: nodesc-skill\n---\n# t\n", encoding="utf-8")

    assert gate(str(good))["runnable"], "好件未过门"
    assert not gate(str(brok))["runnable"], "语法坏件漏过（负断言失效）"
    assert not gate(str(dang))["runnable"], "悬空链接漏过"
    assert not gate(str(nodesc))["runnable"], "缺 description 漏过"
    g_boom = gate(str(boom))
    assert g_boom["runnable"], "模块顶层 raise 件应过门：compile 不 exec（铁律自证）"

    zpkg = root / "zipped.skill"
    with zipfile.ZipFile(zpkg, "w") as z:
        for f in good.rglob("*"):
            if f.is_file():
                z.write(f, "good-skill/" + str(f.relative_to(good)).replace("\\", "/"))
    assert gate(str(zpkg))["runnable"], ".skill 包件未过门"
    (root / "corrupt.skill").write_bytes(b"not-a-zip")
    assert not gate(str(root / "corrupt.skill"))["runnable"], "坏 zip 漏过"

    init_roster(roster)
    try:  # 撞名拒写（负断言）
        init_roster(roster)
        raise SystemExit("init 撞名未拒")
    except SystemExit as e:
        assert e.code == 2
    for nm, src, ph in (("good-skill", good, None), ("broken-skill", brok, None),
                        ("zipped-one", zpkg, None)):
        register(roster, nm, str(src), version="1.0.0")
    r = load_roster(roster)
    nxt, why = decide(r)
    assert nxt["phase"] == "A-pending", "首决策应指向能跑门"
    try:  # 汇总 exit 码契约（负断言）：有失败件必须 exit 1
        run_gate(roster, None, True)
        raise SystemExit("gate 汇总退出码失效：有失败件未 exit 1")
    except SystemExit as e:
        assert e.code == 1, f"gate 退出码异常: {e.code}"
    r = load_roster(roster)
    by = {s["name"]: s for s in r["skills"]}
    assert by["broken-skill"]["phase"] == "A-failed", "坏件未标 A-failed"
    nxt, why = decide(r)
    assert nxt["name"] == "broken-skill", "先能跑：失败件应最先回炉"
    # 硬闸：门未过禁 advance（负断言）
    try:
        advance(roster, "broken-skill", "KEEP", "x")
        raise SystemExit("硬闸失效：A-failed 被 advance")
    except SystemExit as e:
        assert e.code == 3
    advance(roster, "good-skill", "REVISE", "R1 修")
    advance(roster, "zipped-one", "KEEP", "定案")
    r = load_roster(roster)
    by = {s["name"]: s for s in r["skills"]}
    assert by["zipped-one"]["phase"] == "alumni", "KEEP 未出队"
    assert by["good-skill"]["phase"] == "B-rounds", "REVISE 未留队"
    nxt, _ = decide(r)
    assert nxt["name"] == "broken-skill", "坏件修复前仍是最高优先"
    register(roster, "broken-skill", str(good), version="1.0.1")  # 换源回炉
    r = load_roster(roster)
    assert {s["name"]: s for s in r["skills"]}["broken-skill"]["phase"] == "A-pending", "回炉未复位"
    import shutil
    shutil.rmtree(root, ignore_errors=True)
    print(f"forge_roster smoke PASS（v{VERSION}：门六检/负断言/compile不exec自证/包件/排期/硬闸/回炉 全过）")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", metavar="ROSTER")
    ap.add_argument("--register", metavar="ROSTER")
    ap.add_argument("--gate", metavar="ROSTER")
    ap.add_argument("--next", dest="next_", metavar="ROSTER")
    ap.add_argument("--advance", metavar="ROSTER")
    ap.add_argument("--status", metavar="ROSTER")
    ap.add_argument("--name")
    ap.add_argument("--src")
    ap.add_argument("--version", default="")
    ap.add_argument("--note", default="")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--verdict", choices=["KEEP", "REVISE", "FAIL"])
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    if a.smoke:
        smoke()
    elif a.init:
        init_roster(a.init)
    elif a.register:
        if not (a.name and a.src):
            print("--register 须配 --name 与 --src", file=sys.stderr)
            sys.exit(2)
        register(a.register, a.name, a.src, a.version, a.note)
    elif a.gate:
        if not (a.all or a.name):
            print("--gate 须配 --name 或 --all", file=sys.stderr)
            sys.exit(2)
        run_gate(a.gate, a.name, a.all)
    elif a.next_:
        show_next(a.next_)
    elif a.advance:
        if not (a.name and a.verdict):
            print("--advance 须配 --name 与 --verdict", file=sys.stderr)
            sys.exit(2)
        advance(a.advance, a.name, a.verdict, a.note)
    elif a.status:
        status(a.status)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
