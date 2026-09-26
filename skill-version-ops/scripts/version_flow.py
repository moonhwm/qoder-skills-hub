#!/usr/bin/env python3
# version_flow.py v1.0.0 — 技能版本流转共库（skill-version-ops）
# 三模式收编：
#   refresh-check  ← skill-refresh-ops/scripts/refresh_check.sh（预检/盘点/包源搜索）
#   reinstall      ← skill-reinstall-ops/scripts/reinstall.sh（备份换位/逐包核验/零伪装）
#   sync-check     ← portable-sync-ops/scripts/portable_sync_check.py（四重判定，原样内嵌）
# 纯标准库。用法：
#   python3 version_flow.py refresh-check [--upload DIR] [--out FILE]
#   python3 version_flow.py reinstall [--dist DIR] [--install DIR] [--pkgs "a b c"]
#   python3 version_flow.py sync-check [--registry FILE] [--json FILE]
#   python3 version_flow.py self-test
import argparse, datetime, hashlib, json, os, re, shutil, sys, tempfile, zipfile

USER_SKILLS = "/app/.user/skills"
AGENTS_SKILLS = "/app/.agents/skills"
DEFAULT_UPLOAD = "/mnt/agents/upload"
DEFAULT_DIST = "/mnt/agents/upload/skill-dist-20260829"

VER_RE = re.compile(r'^\s*version\s*:\s*["\']?([0-9A-Za-z.\-]+)["\']?\s*$', re.M)
TITLE_RE = re.compile(r'[（(]\s*v?([0-9]+\.[0-9][0-9A-Za-z.\-]*)\s*[·)）]')


def _ver_from_text(t):
    m = VER_RE.search(t[:4000])
    if m:
        return m.group(1)
    m = TITLE_RE.search(t[:300])
    return m.group(1) if m else None


def _ver_from_md(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return _ver_from_text(f.read())
    except OSError:
        return None


def _ver_from_skill_pack(path):
    if not os.path.exists(path):
        return None
    try:
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                parts = n.strip("/").split("/")
                if len(parts) == 2 and parts[1] == "SKILL.md":
                    return _ver_from_text(z.read(n).decode("utf-8", "ignore"))
    except (zipfile.BadZipFile, OSError):
        return None
    return None


def _ver_from_source(src_path):
    if os.path.isdir(src_path):
        return _ver_from_md(os.path.join(src_path, "SKILL.md"))
    if src_path.endswith(".skill"):
        return _ver_from_skill_pack(src_path)
    return _ver_from_md(src_path)


def _md5(path):
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except OSError:
        return None


# ============ 模式一 refresh-check（原 refresh_check.sh 逐拍移植） ============
def mode_refresh_check(upload=DEFAULT_UPLOAD, out=None, install_dir=USER_SKILLS):
    lines = []
    now = datetime.datetime.now()
    if out is None:
        out = "/mnt/agents/output/skill_refresh_report_%s.txt" % now.strftime("%Y%m%d_%H%M%S")
    lines.append("===== skill-version-ops refresh-check 刷新报告 %s =====" % now.strftime("%F %T"))
    lines.append("")
    lines.append("[① 安装位可写性预检]")
    wt = os.path.join(install_dir, ".writetest")
    try:
        with open(wt, "w"):
            pass
        os.remove(wt)
        lines.append("USER_SKILLS=WRITABLE（可移交 reinstall 模式）")
        writable = True
    except OSError:
        lines.append("USER_SKILLS=READ-ONLY（重装如实停止，禁止假装成功）")
        writable = False
    lines.append("")
    lines.append("[② 库盘点与版本漂移]")
    try:
        u = len(os.listdir(install_dir))
    except OSError:
        u = 0
    try:
        a = len(os.listdir(AGENTS_SKILLS))
    except OSError:
        a = 0
    lines.append("user_skills=%d  builtin_skills=%d" % (u, a))
    lines.append("-- 含 version 字段的用户技能 --")
    vers = []
    if os.path.isdir(install_dir):
        for d in sorted(os.listdir(install_dir)):
            v = _ver_from_md(os.path.join(install_dir, d, "SKILL.md"))
            if v:
                vers.append("%s|%s" % (d, v))
    lines.extend(vers)
    lines.append("")
    lines.append("[⑤ dist 包源搜索（%s）]" % upload)
    found = []
    if os.path.isdir(upload):
        for root, dirs, files in os.walk(upload):
            if root[len(upload):].count(os.sep) >= 3:
                dirs[:] = []
                continue
            for fn in files:
                if fn.lower().endswith(".skill") or fn.lower().startswith("skill-dist"):
                    found.append(os.path.join(root, fn))
    if found:
        lines.append("PACKAGES_FOUND:")
        lines.extend(found)
    else:
        lines.append("PACKAGES_FOUND=NONE")
    lines.append("")
    lines.append("[结论] 移交重装条件=可写∧有包；缺一即如实停止并给降级路径。")
    text = "\n".join(lines)
    try:
        with open(out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        lines.append("报告落盘: %s" % out)
    except OSError as e:
        lines.append("报告落盘失败: %s" % e)
    print("\n".join(lines))
    return 0


# ============ 模式二 reinstall（原 reinstall.sh 四规程逐拍移植） ============
def mode_reinstall(dist=DEFAULT_DIST, install_dir=USER_SKILLS, pkgs=None):
    if pkgs is None:
        pkgs = ["autonomous-advance-ops", "skill-dispatch-hq",
                "plugin-datasource-ops", "rumor-chain-verifier"]
    print("== 预检：安装位可写性 ==")
    wt = os.path.join(install_dir, ".w_test_reinstall")
    try:
        with open(wt, "w"):
            pass
        os.remove(wt)
    except OSError:
        print("[FAIL] 安装位只读：%s ——本模式无法写入。" % install_dir)
        print("降级路径：①Kimi 界面「与 Kimi 对话创建技能」粘贴对应 SKILL.md 全文；")
        print("         ②Kimi Claw Desktop 桌面端会话中执行（其环境可能可写）。")
        print("如实停止，未做任何改动。")
        return 2
    ok = fail = 0
    for pkg in pkgs:
        src = os.path.join(dist, pkg + ".skill")
        if not os.path.isfile(src):
            print("[SKIP] %s：包不存在 %s" % (pkg, src))
            fail += 1
            continue
        newdir = os.path.join(install_dir, pkg + ".new")
        bakdir = os.path.join(install_dir, pkg + ".bak")
        target = os.path.join(install_dir, pkg)
        shutil.rmtree(newdir, ignore_errors=True)
        os.makedirs(newdir, exist_ok=True)
        try:
            with zipfile.ZipFile(src) as z:
                z.extractall(newdir)
        except (zipfile.BadZipFile, OSError):
            print("[FAIL] %s：解压失败" % pkg)
            shutil.rmtree(newdir, ignore_errors=True)
            fail += 1
            continue
        if not os.path.isfile(os.path.join(newdir, "SKILL.md")):
            for root, _d, files in os.walk(newdir):
                if "SKILL.md" in files:
                    inner = root
                    for item in os.listdir(inner):
                        shutil.move(os.path.join(inner, item), newdir)
                    break
        shutil.rmtree(bakdir, ignore_errors=True)
        if os.path.isdir(target):
            shutil.move(target, bakdir)
        shutil.move(newdir, target)
        v = _ver_from_md(os.path.join(target, "SKILL.md"))
        print("[OK] %s 重装完成（%s）" % (pkg, ('version: "%s"' % v) if v else "无版本位"))
        ok += 1
    print("== 结果：成功 %d / 失败或跳过 %d ==" % (ok, fail))
    return 0 if fail == 0 else 1


# ============ 模式三 sync-check（原 portable_sync_check.py 判定逻辑原样内嵌） ============
def check_registry(reg_path):
    with open(reg_path, encoding="utf-8") as f:
        reg = json.load(f)
    report = {"registry": reg_path, "page": reg.get("page"), "items": [], "packs": []}
    n_cur = n_stale = n_missing = 0
    for it in reg.get("items", []):
        ent = {"id": it.get("id"), "kind": it.get("kind"), "portable_path": it.get("portable_path"),
               "status": "CURRENT", "problems": []}
        pp = it.get("portable_path") or ""
        if not pp or not os.path.exists(pp):
            ent["status"] = "MISSING"
            ent["problems"].append("portable_path 不存在: %s" % pp)
        pv = it.get("portable_version")
        live_pv = _ver_from_source(pp) if ent["status"] != "MISSING" else None
        if pv and live_pv and live_pv != pv:
            ent["problems"].append("便携件版本与登记不符: 登记=%s 文件=%s" % (pv, live_pv))
        for s in it.get("sources", []):
            sp, sv = s.get("path"), s.get("version")
            live = _ver_from_source(sp)
            srec = {"source": sp, "registered": sv, "live": live}
            if live is None:
                srec["cmp"] = "UNREADABLE"
                ent["problems"].append("源件不可读或无 version: %s" % sp)
            elif sv and live != sv:
                srec["cmp"] = "STALE"
                ent["problems"].append("源件版本漂移: 登记=%s 实际=%s (%s)" % (sv, live, sp))
            else:
                srec["cmp"] = "CURRENT"
            ent.setdefault("sources", []).append(srec)
        mp = it.get("mirror")
        if mp and ent["status"] != "MISSING":
            a, b = _md5(pp), _md5(mp)
            ent["mirror"] = {"path": mp, "md5_same": (a is not None and a == b)}
            if a is None or b is None or a != b:
                ent["problems"].append("镜像漂移: 正本与镜像 md5 不一致 (%s)" % mp)
        if ent["status"] != "MISSING" and ent["problems"]:
            ent["status"] = "STALE"
        n_cur += ent["status"] == "CURRENT"
        n_stale += ent["status"] == "STALE"
        n_missing += ent["status"] == "MISSING"
        report["items"].append(ent)
    scan_dirs = ["/mnt/agents/output"]
    registered_paths = {it.get("portable_path") for it in reg.get("items", [])}
    for d in scan_dirs:
        if not os.path.isdir(d):
            continue
        for root, _dirs, files in os.walk(d):
            for fn in sorted(files):
                if not fn.endswith(".skill"):
                    continue
                full = os.path.join(root, fn)
                v = _ver_from_skill_pack(full)
                report["packs"].append({"pack": full, "version": v,
                    "registered": full in registered_paths,
                    "note": "整包便携=原技能归档，同步看源技能版本；入册后可受控" if full not in registered_paths else "已入册"})
    report["summary"] = {"items_total": len(report["items"]), "current": n_cur,
                         "stale": n_stale, "missing": n_missing,
                         "packs_scanned": len(report["packs"]),
                         "packs_unregistered": sum(1 for p in report["packs"] if not p["registered"])}
    report["verdict"] = "SYNC-OK" if (n_stale == 0 and n_missing == 0) else "SYNC-DRIFT"
    return report


def mode_sync_check(registry=None, json_out=None):
    if registry is None:
        registry = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "assets", "portable_registry.json")
    r = check_registry(os.path.abspath(registry))
    if json_out:
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=1)
    s = r["summary"]
    print("VERDICT: %s | items=%d current=%d stale=%d missing=%d | packs=%d 未入册=%d"
          % (r["verdict"], s["items_total"], s["current"], s["stale"], s["missing"],
             s["packs_scanned"], s["packs_unregistered"]))
    for e in r["items"]:
        mark = {"CURRENT": "✓", "STALE": "⚠", "MISSING": "✗"}[e["status"]]
        print(" %s %s [%s] %s" % (mark, e["id"], e["status"], "; ".join(e["problems"]) or "同步"))
    return 1 if r["verdict"] == "SYNC-DRIFT" else 0


# ============ self-test（五夹具：三模式全覆盖） ============
def self_test():
    td = tempfile.mkdtemp(prefix="vf_")
    results = []

    # F1 sync-check 三夹具：CURRENT / STALE / MISSING
    src = os.path.join(td, "src"); os.makedirs(src)
    with open(os.path.join(src, "SKILL.md"), "w") as f:
        f.write("---\nname: demo\nversion: \"2.0\"\n---\n")
    good = os.path.join(td, "good.md"); open(good, "w").write("x")
    reg = {"page": "p", "items": [
        {"id": "ok", "kind": "t", "portable_path": good, "sources": [{"path": src, "version": "2.0"}]},
        {"id": "stale", "kind": "t", "portable_path": good, "sources": [{"path": src, "version": "1.0"}]},
        {"id": "gone", "kind": "t", "portable_path": os.path.join(td, "nope.md"), "sources": []}]}
    rp = os.path.join(td, "reg.json"); json.dump(reg, open(rp, "w"))
    r = check_registry(rp)
    st = {e["id"]: e["status"] for e in r["items"]}
    f1 = st == {"ok": "CURRENT", "stale": "STALE", "gone": "MISSING"} and r["verdict"] == "SYNC-DRIFT"
    results.append(("F1 sync-check CURRENT/STALE/MISSING", f1))

    # F2 reinstall 成功路径：假安装位 + 两包，核验备份与版本
    dist = os.path.join(td, "dist"); os.makedirs(dist)
    inst = os.path.join(td, "install"); os.makedirs(inst)
    os.makedirs(os.path.join(inst, "pkgA"))  # 旧版
    open(os.path.join(inst, "pkgA", "SKILL.md"), "w").write("---\nname: pkgA\nversion: \"0.9\"\n---\n")
    for name, ver in (("pkgA", "1.0"), ("pkgB", "2.1")):
        zf = os.path.join(dist, name + ".skill")
        with zipfile.ZipFile(zf, "w") as z:
            z.writestr("%s/SKILL.md" % name, "---\nname: %s\nversion: \"%s\"\n---\n" % (name, ver))
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = mode_reinstall(dist=dist, install_dir=inst, pkgs=["pkgA", "pkgB"])
    f2 = (rc == 0
          and _ver_from_md(os.path.join(inst, "pkgA", "SKILL.md")) == "1.0"
          and _ver_from_md(os.path.join(inst, "pkgB", "SKILL.md")) == "2.1"
          and _ver_from_md(os.path.join(inst, "pkgA.bak", "SKILL.md")) == "0.9")
    results.append(("F2 reinstall 成功路径（备份+版本核验）", f2))

    # F3 reinstall 只读预检：不可写目录如实停止 exit 2
    ro = os.path.join(td, "nonexistent_parent", "ro")  # 不存在父目录=不可写（root 下 chmod 0555 无效，改此夹具）
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc3 = mode_reinstall(dist=dist, install_dir=ro, pkgs=["pkgA"])
    f3 = rc3 == 2 and "如实停止" in buf.getvalue() and not os.path.exists(os.path.join(ro, "pkgA"))
    results.append(("F3 reinstall 只读如实停止", f3))

    # F4 refresh-check：假安装位盘点 + 包源搜索
    up = os.path.join(td, "upload"); os.makedirs(up)
    open(os.path.join(up, "x.skill"), "w").write("z")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc4 = mode_refresh_check(upload=up, out=os.path.join(td, "rep.txt"), install_dir=inst)
    o = buf.getvalue()
    f4 = (rc4 == 0 and "USER_SKILLS=WRITABLE" in o and "pkgA|1.0" in o
          and "x.skill" in o and "PACKAGES_FOUND:" in o)
    results.append(("F4 refresh-check 盘点+包源", f4))

    # F5 refresh-check 只读预检如实记录
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        mode_refresh_check(upload=up, out=os.path.join(td, "rep2.txt"), install_dir=ro)
    f5 = "READ-ONLY" in buf.getvalue()
    results.append(("F5 refresh-check 只读如实记录", f5))

    allok = all(v for _, v in results)
    for name, v in results:
        print("SELF-TEST %s %s" % ("PASS" if v else "FAIL", name))
    print("SELF-TEST %s（%d/%d）" % ("PASS" if allok else "FAIL", sum(1 for _, v in results if v), len(results)))
    return 0 if allok else 1


def main():
    ap = argparse.ArgumentParser(prog="version_flow")
    sub = ap.add_subparsers(dest="mode", required=True)
    p1 = sub.add_parser("refresh-check")
    p1.add_argument("--upload", default=DEFAULT_UPLOAD)
    p1.add_argument("--out", default=None)
    p1.add_argument("--install-dir", default=USER_SKILLS)
    p2 = sub.add_parser("reinstall")
    p2.add_argument("--dist", default=DEFAULT_DIST)
    p2.add_argument("--install-dir", default=USER_SKILLS)
    p2.add_argument("--pkgs", default=None, help="空格分隔包名列表")
    p3 = sub.add_parser("sync-check")
    p3.add_argument("--registry", default=None)
    p3.add_argument("--json", dest="json_out", default=None)
    sub.add_parser("self-test")
    a = ap.parse_args()
    if a.mode == "refresh-check":
        sys.exit(mode_refresh_check(upload=a.upload, out=a.out, install_dir=a.install_dir))
    if a.mode == "reinstall":
        pkgs = a.pkgs.split() if a.pkgs else None
        sys.exit(mode_reinstall(dist=a.dist, install_dir=a.install_dir, pkgs=pkgs))
    if a.mode == "sync-check":
        sys.exit(mode_sync_check(registry=a.registry, json_out=a.json_out))
    if a.mode == "self-test":
        sys.exit(self_test())


if __name__ == "__main__":
    main()
