# -*- coding: utf-8 -*-
"""index_switch.py —— 索引档切换与回退（★设计为「改数据不改代码」：仅写指针文件 exp/.cache/index_pointer.json）
两器之索引解析顺序：①环境变量 OPL_SECTION_IDX ②★指针文件 index_pointer.json 之 index 字段 ③默认档 section_index.json
用法：
  python index_switch.py --status              # 列出所有档之指纹／节数／tf／映射一致性／时效 ＋ 当前指向与来源
  python index_switch.py --to <档名或路径>      # 切换（写指针；★先核对目标存在且可读）
  python index_switch.py --rollback            # 回退（删指针 ⇒ 回到默认档）；原指针另存 index_pointer_prev.json
（中文串一律用「」）
"""
import argparse, hashlib, json, os, pathlib, re, sys, time

HOME = pathlib.Path.home()
SEAT = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A新席_石敢当Cairn_20260928"
EX = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"
CACHE = SEAT/"exp"/".cache"
PTR = CACHE/"index_pointer.json"
DEF = CACHE/"section_index.json"

def facts(p):
    if not p.exists(): return None
    try:
        j = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"name": p.name, "bad": True}
    secs = j.get("sections") or []
    docs = {s["doc"] for s in secs}
    m = {}
    for f in EX.glob("*.otl"):
        mm = re.search(r"CAIRN-(\d{1,3})", f.name)
        if mm: m["CAIRN-%s" % mm.group(1)] = f.name.split("_")[0]
    hit = sum(1 for v in m.values() if v in docs)
    newest = max((q.stat().st_mtime for q in EX.glob("*.otl")), default=0)
    return {"name": p.name, "sha16": hashlib.sha3_256(p.read_bytes()).hexdigest()[:16], "sections": len(secs),
            "docs": len(docs), "tf": bool(secs) and ("tf" in secs[0]), "map_pct": round(100.0*hit/max(1, len(m)), 1),
            "fresh": p.stat().st_mtime >= newest, "mtime": time.strftime("%m-%d %H:%M", time.localtime(p.stat().st_mtime))}

def cur():
    e = os.environ.get("OPL_SECTION_IDX")
    if e: return pathlib.Path(e), "env"
    if PTR.exists():
        try:
            return pathlib.Path(json.loads(PTR.read_text(encoding="utf-8"))["index"]), "pointer"
        except Exception: pass
    return DEF, "default"

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--status", action="store_true")
    ap.add_argument("--to", default=""); ap.add_argument("--rollback", action="store_true")
    a = ap.parse_args()
    if a.status or not (a.to or a.rollback):
        print("  ═══ 索引档一览 ═══")
        for p in sorted(CACHE.glob("section_index*.json")):
            f = facts(p)
            if not f: continue
            mark = "★当前" if p.name == (cur()[0].name) else "     "
            print("   %s %-34s 节 %5s ｜ 文档 %4s ｜ tf %s ｜ 映射 %5s%% ｜ %s ｜ %s ｜ %s" % (
                mark, f["name"], f.get("sections"), f.get("docs"), "有" if f.get("tf") else "★无",
                f.get("map_pct"), "新" if f.get("fresh") else "★陈旧", f.get("mtime"), f.get("sha16")))
        p, src = cur(); print("   当前指向：%s（来源 %s）｜指针文件：%s" % (p.name, src, PTR.name if PTR.exists() else "无"))
        return 0
    if a.to:
        t = pathlib.Path(a.to)
        if not t.exists(): t = CACHE/a.to
        if not t.exists(): print("  ★目标档不存在：%s" % a.to); return 2
        f = facts(t)
        if not f or f.get("bad"): print("  ★目标档不可读 ⇒ 拒绝切换"); return 2
        if PTR.exists():
            (CACHE/"index_pointer_prev.json").write_text(PTR.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
        PTR.write_text(json.dumps({"index": str(t), "switched_at": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "sha16": f["sha16"], "sections": f["sections"], "tf": f["tf"], "map_pct": f["map_pct"],
            "note": "★由 index_switch.py 写入；回退：--rollback（删指针）"}, ensure_ascii=False, indent=1),
            encoding="utf-8", newline="\n")
        print("  ✓ 已切换至 %s（指纹 %s｜节 %s｜tf %s｜映射 %s%%）" % (t.name, f["sha16"], f["sections"], f["tf"], f["map_pct"]))
        print("    ⇒ 两器（section_search／retrieval_eval）将经指针解析取此档；回退：--rollback")
        return 0
    # rollback
    if PTR.exists():
        prev = CACHE/"index_pointer_prev.json"
        (CACHE/("index_pointer_rolled_back_%s.json" % time.strftime("%Y%m%d_%H%M"))).write_text(
            PTR.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
        PTR.unlink()
        print("  ✓ 已回退：指针删除 ⇒ 回到默认档 %s（原指针另存）" % DEF.name)
    else:
        print("  · 无指针文件 ⇒ 本就在默认档（无需回退）")
    return 0

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
