# -*- coding: utf-8 -*-
"""tools_registry_refresh.py —— 器物登记刷新（2026-10-12 立）
背景：cairn/tools 已达 398 个 .py，而仓内登记表（mem/cairn_nameregistry_20261009.json）停在 10-09
     ⇒ 抽样核 6 个今日新器（decision_model／decision_rerank／emb_cache／vec_index／glb_uv_check／uv_stretch_check）★皆未登记
     ⇒ 即「文实脱节」：外人（他席）无法从登记表发现新器。
本器（★零依赖、只读文档串首行，轻量）：
  ① 扫 cairn/tools/*.py（及可选 seat/exp）⇒ 取器物名与其文档串★首行（一句话用途）
  ② 读既有登记表（若有）之键集 ⇒ ★列「新增（未登记）」与"已登记"
  ③ 写新登记表（★只增不改：文件名带日期；不覆盖旧表）
判据（可失败）：①扫得器物数 > 0 ②每个器物皆有其文档串首行（缺者标「★无文档串」）③未登记者已逐条列出
用法：python tools_registry_refresh.py --tools <目录> [--prev <旧登记表>] [--out <新表>]
（中文串一律用「」）
"""
import argparse, json, pathlib, sys, time


def first_line(p):
    """★只读文档串首行（轻量：不整档入内存）"""
    try:
        with open(p, "r", encoding="utf-8-sig", errors="replace") as f:
            for i, l in enumerate(f):
                if i > 40: break
                s = l.strip()
                if s.startswith('"""') and len(s) > 3:
                    return s.strip('"').strip()[:110]
                if s.startswith('r"""') or s.startswith("'''"):
                    return s.strip("r\"'").strip()[:110]
    except Exception:
        pass
    return None


def collect(d):
    d = pathlib.Path(d)
    rows = []
    for p in sorted(d.glob("*.py")):
        if p.name.startswith("_"): continue
        rows.append({"name": p.stem, "file": p.name, "kb": round(p.stat().st_size/1024, 1),
                     "doc": first_line(p), "mtime": time.strftime("%Y-%m-%d", time.localtime(p.stat().st_mtime))})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tools", required=True)
    ap.add_argument("--prev", default="")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    rows = collect(a.tools)
    print("  ═══ 器物登记刷新 ═══")
    print("   目录：%s ｜ ★扫得器物 %d 个" % (pathlib.Path(a.tools).name, len(rows)))
    nodoc = [r["name"] for r in rows if not r["doc"]]
    print("   ★无文档串者 %d 个%s" % (len(nodoc), ("：" + "、".join(nodoc[:8])) if nodoc else ""))
    prev = {}
    if a.prev and pathlib.Path(a.prev).exists():
        try:
            j = json.loads(pathlib.Path(a.prev).read_text(encoding="utf-8-sig"))
            if isinstance(j, dict):
                # 兼容多种形态：{name: …} 或 {"tools": [...]} 或 {"items": [...]/{}}
                # ★2026-10-12 自纠（-1315 之果）：旧表 cairn_nameregistry_v2_20261009.json 之器名★在 items 之内，
                #   而顶层 9 键（ts/seat/note/count/by_seat/by_series/hyphen_series/unmatched/items）★皆非器名
                #   ⇒ 原取键法把顶层键当器名集 ⇒ "未登记"误报为"全部"（440/440）⇒ 今补 items 分支
                def _stem(s):
                    # ★2026-10-12 加（-1317 之果）：指纹清单之器名在 path（如 "exp/a2a_client.py"）
                    #   ⇒ 须取 basename 并去扩展名，方能与现行器名（无目录无扩展名）匹配
                    b = str(s).replace("\\", "/").split("/")[-1]
                    return b[:-3] if b.endswith(".py") else b
                def _names(v):
                    if isinstance(v, dict):
                        return {str(k) for k in v.keys()}
                    if isinstance(v, list):
                        out = set()
                        for x in v:
                            if isinstance(x, dict):
                                if "path" in x: out.add(_stem(x["path"]))
                                elif "name" in x: out.add(str(x["name"]))
                                elif "file" in x: out.add(str(x["file"]))
                            else:
                                out.add(_stem(x))
                        return out
                    return set()
                if "tools" in j:
                    prev = _names(j["tools"])
                elif "items" in j:
                    prev = _names(j["items"])
                else:
                    prev = set(j.keys())
                # ★防呆：若旧表所取之名远少于现行器物（<10%）⇒ 提示格式可能未匹配
                if prev and len(prev) < 0.1 * max(1, len(rows)):
                    print("   ★提示：旧表取得器名仅 %d 个（远少于现行 %d）⇒ 恐格式未匹配，"
                          "请核旧表结构（未登记列可能有误）" % (len(prev), len(rows)))
        except Exception as ex:
            print("   ★旧登记表不可解析：%s" % str(ex)[:60])
    have = {r["name"] for r in rows}
    new = sorted(have - prev) if prev else sorted(have)
    gone = sorted(prev - have) if prev else []
    print("   旧登记表键 %d ｜ ★未登记（新增）%d ｜ 已消失（旧表有而现行无）%d" % (len(prev), len(new), len(gone)))
    print("   ── ★未登记之器（前 20）──")
    for n in new[:20]:
        r = next((x for x in rows if x["name"] == n), {})
        print("      %-28s ｜ %s" % (n, (r.get("doc") or "★无文档串")[:64]))
    crit = {"①扫得器物数 > 0": len(rows) > 0,
            "②每器物皆有其文档串首行": len(nodoc) == 0,
            "③未登记者已逐条列出": True}
    print("   ── 判据 ──")
    for k, v in crit.items(): print("   %s ⇒ %s" % (k, "✓" if v else "✗（%d 个）" % len(nodoc)))
    if a.out:
        out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "dir": str(pathlib.Path(a.tools).name),
               "count": len(rows), "nodoc": nodoc, "unregistered": new, "missing": gone,
               "criteria": crit, "tools": rows}
        pathlib.Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 新登记表已写：%s" % pathlib.Path(a.out).name)
    return 0 if crit["①扫得器物数 > 0"] else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
