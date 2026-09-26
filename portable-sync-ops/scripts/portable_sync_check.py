#!/usr/bin/env python3
# portable_sync_check.py v1.0 — 便携件同步检测器（portable-sync-ops）
# 唯一真相源 = assets/portable_registry.json；未入册的便携件=不受同步纪律保护。
# 纯标准库。用法：
#   python3 portable_sync_check.py --registry assets/portable_registry.json [--json out.json]
#   python3 portable_sync_check.py --self-test
import argparse, hashlib, json, os, re, sys, tempfile, zipfile

VER_RE = re.compile(r'^\s*version\s*:\s*["\']?([0-9A-Za-z.\-]+)["\']?\s*$', re.M)
TITLE_RE = re.compile(r'[（(]\s*v?([0-9]+\.[0-9][0-9A-Za-z.\-]*)\s*[·)）]')  # 标题行「（v1.1 · 2026-…）」形态

def _ver_from_text(t):
    m = VER_RE.search(t[:4000])
    if m:
        return m.group(1)
    m = TITLE_RE.search(t[:300])  # 无 frontmatter 时只在文首 300 字符认标题版本，防正文误匹配
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
    """.skill = zip，根目录一层，找 */SKILL.md 读 frontmatter version。"""
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
    """按形态取版本号：目录→SKILL.md；.skill→解包；其他→当 md 直读。"""
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

def check_registry(reg_path):
    with open(reg_path, encoding="utf-8") as f:
        reg = json.load(f)
    report = {"registry": reg_path, "page": reg.get("page"), "items": [], "packs": []}
    n_cur = n_stale = n_missing = 0
    for it in reg.get("items", []):
        ent = {"id": it.get("id"), "kind": it.get("kind"), "portable_path": it.get("portable_path"),
               "status": "CURRENT", "problems": []}
        # 1) 便携件本身存在性
        pp = it.get("portable_path") or ""
        if not pp or not os.path.exists(pp):
            ent["status"] = "MISSING"
            ent["problems"].append("portable_path 不存在: %s" % pp)
        # 1b) 便携件自身版本号 vs 登记（防「文件改了、台账没跟」与反方向漂移）
        pv = it.get("portable_version")
        live_pv = _ver_from_source(pp) if ent["status"] != "MISSING" else None
        if pv and live_pv and live_pv != pv:
            ent["problems"].append("便携件版本与登记不符: 登记=%s 文件=%s" % (pv, live_pv))
        # 2) 源件版本比对
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
        # 3) 镜像一致性：app/ 正本与交接镜像须逐字节一致
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
    # 4) 整包便携动态枚举：output 目录递归全部 .skill，标注入册/未入册
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

def self_test():
    """三夹具：CURRENT / STALE(版本漂移) / MISSING(便携件丢失)。"""
    td = tempfile.mkdtemp(prefix="psc_")
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
    ok = st == {"ok": "CURRENT", "stale": "STALE", "gone": "MISSING"} and r["verdict"] == "SYNC-DRIFT"
    print("SELF-TEST %s | %s | verdict=%s" % ("PASS" if ok else "FAIL", st, r["verdict"]))
    return 0 if ok else 1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "portable_registry.json"))
    ap.add_argument("--json", dest="json_out", default=None)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(self_test())
    r = check_registry(os.path.abspath(a.registry))
    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=1)
    s = r["summary"]
    print("VERDICT: %s | items=%d current=%d stale=%d missing=%d | packs=%d 未入册=%d"
          % (r["verdict"], s["items_total"], s["current"], s["stale"], s["missing"], s["packs_scanned"], s["packs_unregistered"]))
    for e in r["items"]:
        mark = {"CURRENT": "✓", "STALE": "⚠", "MISSING": "✗"}[e["status"]]
        print(" %s %s [%s] %s" % (mark, e["id"], e["status"], "; ".join(e["problems"]) or "同步"))
    sys.exit(1 if r["verdict"] == "SYNC-DRIFT" else 0)

if __name__ == "__main__":
    main()
