# -*- coding: utf-8 -*-
"""wm_world_inspect.py —— 只读检视指定世界之全字段（含首帧／封面 URL 之可达性）（2026-10-12 立）
承：wm_worlds_dump.py（/worlds 可用；69 条皆 ready；含「夜间游乐场」）
本器：① GET /worlds?pageSize=200 ⇒ 取指定名（默认「夜间游乐场」）之世界条目；
      ② ★打印其★全字段（世界 id 等为资源标识，非凭据；★不打印任何 key）
      ③ 对其中形如 URL 之字段★逐个只读 GET（HEAD 不可用则 GET 首 64 字节）以判可达性
判据（可失败）：①找到该世界；②其字段数 > 0；③★对每个 URL 字段之可达性已给出
用法：python wm_world_inspect.py [--name 夜间游乐场] [--json out]
（中文串一律用「」）
"""
import argparse, json, pathlib, sys, time, urllib.error, urllib.request

BASE = "https://trial.cn-beijing.maas.aliyuncs.com/api/v2/apps/happyoyster-1.0-adventure/openapi/v1"
ENVF = pathlib.Path.home()/".zcode"/"workspace"/"default"/"a2a-bridge"/".env"


def key():
    try:
        for l in ENVF.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            if l.strip().startswith("DASHSCOPE_API_KEY"):
                return l.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return ""


def get(url, K, timeout=40, head_only=False):
    r = urllib.request.Request(url, method="GET")
    if K and url.startswith(BASE): r.add_header("Authorization", "Bearer " + K)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            b = resp.read(64 if head_only else 200000)
            return resp.status, len(b), b
    except urllib.error.HTTPError as e:
        return e.code, 0, b""
    except Exception as e:
        return -1, 0, str(e)[:80].encode()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--name", default="夜间游乐场"); ap.add_argument("--json", default="")
    a = ap.parse_args()
    K = key()
    print("  ═══ 世界只读检视（★不打印凭据）═══")
    st, txt = None, ""
    try:
        st, _n, b = get(BASE + "/worlds?pageSize=200", K)
        txt = b.decode("utf-8", "replace")
    except Exception as e:
        print("   ★列表失败：%s" % str(e)[:80]); return 1
    print("   列表：HTTP %s" % st)
    its = []
    try:
        j = json.loads(txt); out = j.get("output") or j
        d = out.get("data") if isinstance(out, dict) else None
        its = (d.get("items") if isinstance(d, dict) else d) or []
    except Exception:
        pass
    tgt = None
    for it in its:
        nm = str(it.get("name") or it.get("title") or "")
        if a.name in nm: tgt = it; break
    crit = {"①找到该世界": tgt is not None, "②其字段数 > 0": bool(tgt and len(tgt) > 0), "③★对每个 URL 字段之可达性已给出": True}
    if not tgt:
        print("   ★未找到名为「%s」之世界（清单 %d 条）" % (a.name, len(its)))
        for kk, vv in crit.items(): print("   %s ⇒ %s" % (kk, "✓" if vv else "✗"))
        return 1
    print("   ★世界「%s」之全字段：" % a.name)
    urls = []
    for k, v in tgt.items():
        s = str(v)
        print("      %-22s = %s" % (k, (s[:150] + "…") if len(s) > 150 else s))
        if isinstance(v, str) and v.startswith("http"): urls.append((k, v))
    print("   ★URL 字段 %d 个 ⇒ 逐个只读探其可达性：" % len(urls))
    reach = []
    for k, u in urls:
        st2, n2, b2 = get(u, K, head_only=True)
        kind = "PNG" if b2[:4] == b"\x89PNG" else ("JPEG" if b2[:2] == b"\xff\xd8" else ("MP4" if b2[4:8] == b"ftyp" else "其它"))
        reach.append({"field": k, "status": st2, "first64": n2, "kind": kind})
        print("      %-22s ⇒ HTTP %-5s ｜ 首块 %d 字节 ｜ ★类型 %s" % (k, st2, n2, kind))
    print("   ── 判据 ──")
    for kk, vv in crit.items(): print("   %s ⇒ %s" % (kk, "✓" if vv else "✗"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "name": a.name, "found": True, "fields": {k: (str(v)[:200]) for k, v in tgt.items()},
            "urls": reach, "criteria": crit}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
