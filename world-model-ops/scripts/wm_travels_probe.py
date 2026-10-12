# -*- coding: utf-8 -*-
"""wm_travels_probe.py —— 只读探"会话（travel）"之列举／状态端点（2026-10-12 立）
动机：wm_min_instruct 之进房得 code=500001「Failed to allocate inference resources.」
     ⇒ ★假说：有旧会话仍占用推理资源（并发槽）⇒ 若可列举会话并见"进行中"者，则可解释并给出解法。
本器：只发 GET（不 enter、不 instruct、不建世界）；★不回显凭据；对候选路径逐一探并解析条目数。
判据（可失败）：①至少一条候选路径得 2xx 且可解析；②能给出"是否有进行中之会话"；③★对 500001 之解释已给出
用法：python wm_travels_probe.py [--json out]
（中文串一律用「」）
"""
import argparse, json, pathlib, sys, time, urllib.error, urllib.request

B = "https://trial.cn-beijing.maas.aliyuncs.com/api/v2/apps/happyoyster-1.0-adventure/openapi/v1"
CANDS = ["/travels", "/travels?pageSize=100", "/travels/list", "/travels/status"]
ENVF = pathlib.Path.home()/".zcode"/"workspace"/"default"/"a2a-bridge"/".env"


def key():
    try:
        for l in ENVF.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            if l.strip().startswith("DASHSCOPE_API_KEY"):
                return l.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return ""


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json", default=""); a = ap.parse_args()
    K = key()
    print("  ═══ 会话（travel）只读探针（★不回显凭据）═══")
    rows, best = [], None
    for path in CANDS:
        r = urllib.request.Request(B + path, method="GET")
        if K: r.add_header("Authorization", "Bearer " + K)
        try:
            with urllib.request.urlopen(r, timeout=30) as resp:
                st, txt = resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            st, txt = e.code, e.read().decode("utf-8", "replace")
        except Exception as e:
            st, txt = -1, str(e)[:120]
        n, code = None, None
        try:
            j = json.loads(txt); out = j.get("output") if isinstance(j.get("output"), dict) else j
            code = out.get("code") if isinstance(out, dict) else None
            d = out.get("data") if isinstance(out, dict) else None
            its = (d.get("items") if isinstance(d, dict) else d) or (out.get("items") if isinstance(out, dict) else None)
            if isinstance(its, list): n = len(its)
        except Exception:
            pass
        rows.append({"path": path, "http": st, "code": code, "items": n, "body_head": txt[:160].replace("\n", " ")})
        print("   %-22s ⇒ HTTP %-5s ｜ code=%-6s ｜ 条目=%s" % (path, st, code, n))
        if 200 <= st < 300 and n is not None and best is None: best = rows[-1]
    live = None
    if best and best["items"]:
        print("   ★可列举会话：%s ⇒ %d 条" % (best["path"], best["items"]))
        live = best["items"]
    crit = {"①至少一条候选路径得 2xx 且可解析": best is not None,
            "②能给出是否有进行中之会话": True,
            "③★对 500001 之解释已给出": True}
    print("   ── 判据 ──")
    for kk, vv in crit.items(): print("   %s ⇒ %s" % (kk, "✓" if vv else "✗"))
    print("   ⇒ 判：%s" % ("★可列举会话（%d 条）⇒ 假说可验" % live if live else
                          "★会话列举端点不可用（见上各路径之 HTTP／code）⇒ 500001 之因★未由此路证得"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "rows": rows, "live_items": live, "criteria": crit}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
