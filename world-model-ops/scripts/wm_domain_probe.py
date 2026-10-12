# -*- coding: utf-8 -*-
"""wm_domain_probe.py —— 世界模型端点之"域名 × 三模式"只读探针（2026-10-12 立）
目的：-13／-10 立"trial 域 Adventure 可用；directing／acting 403（应用级资格墙）"，并请裁"提供 WorkspaceId（llm-xxx）⇒ 换业务空间域名（可解 Directing）"。
     本件核：★我早已持有之"业务空间域名"（WS）是否能免 403。
★安全：只发 GET（不发 POST、不创建资源、不改配置）；★不回显凭据；含★阴性对照（乱名 app）以验证"403 vs 404"判据。
判据（可失败）：①阴性对照得 404（判据成立）；②adventure 在 trial 域得非 403（复现既有结论）；③★WS 域之三模式状态已逐一给出
用法：python wm_domain_probe.py [--json out]
（中文串一律用「」）
"""
import argparse, json, pathlib, sys, time, urllib.error, urllib.request

DOMAINS = {
    "trial": "https://trial.cn-beijing.maas.aliyuncs.com",
    "WS(业务空间)": "https://ws-ay6o8osb22o9dc3t.cn-beijing.maas.aliyuncs.com",
}
KINDS = ["adventure", "directing", "acting", "nonexistent-xyz"]   # ★末者为阴性对照
ENVF = pathlib.Path.home()/".zcode"/"workspace"/"default"/"a2a-bridge"/".env"


def key():
    try:
        for l in ENVF.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            if l.strip().startswith("DASHSCOPE_API_KEY"):
                return l.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return ""


def mask(s, k):
    s = str(s)
    if k and len(k) > 8: s = s.replace(k, "★KEY★")
    return s[:200].replace("\n", " ")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json", default=""); a = ap.parse_args()
    k = key()
    print("  ═══ 世界模型端点只读探针（GET only；★不回显凭据）═══")
    print("   凭据：%s" % ("已读到（值不回显）" if k else "★未读到"))
    rows = []
    for dn, dom in DOMAINS.items():
        for kind in KINDS:
            url = "%s/api/v2/apps/happyoyster-1.0-%s/openapi/v1" % (dom, kind)
            req = urllib.request.Request(url, method="GET")
            if k: req.add_header("Authorization", "Bearer " + k)
            st, body = -1, ""
            try:
                with urllib.request.urlopen(req, timeout=25) as r:
                    st, body = r.status, r.read().decode("utf-8", "replace")
            except urllib.error.HTTPError as e:
                st, body = e.code, e.read().decode("utf-8", "replace")
            except Exception as e:
                st, body = -1, str(e)[:160]
            code = ""
            try:
                j = json.loads(body); code = str(j.get("code") or j.get("Code") or j.get("error", {}).get("code") or "")[:40]
            except Exception:
                pass
            verdict = "端点存在，无资格" if st == 403 else ("端点不存在" if st == 404 else ("可访问" if st == 200 else "未判"))
            rows.append({"domain": dn, "kind": kind, "status": st, "code": code, "verdict": verdict, "body": mask(body, k)})
            print("   %-12s × %-16s ⇒ HTTP %-5s ｜ code %-28s ｜ ★%s" % (dn, kind, st, code or "-", verdict))
            if body: print("        %s" % mask(body, k)[:150])
    neg = [r for r in rows if r["kind"] == "nonexistent-xyz"]
    adv_t = [r for r in rows if r["domain"] == "trial" and r["kind"] == "adventure"]
    crit = {"①阴性对照得 404（判据成立）": all(r["status"] == 404 for r in neg),
            "②adventure 在 trial 域得非 403（复现既有结论）": all(r["status"] != 403 for r in adv_t),
            "③★WS 域之三模式状态已逐一给出": len([r for r in rows if r["domain"].startswith("WS")]) >= 3}
    print("   ── 判据 ──")
    for kk, vv in crit.items(): print("   %s ⇒ %s" % (kk, "✓" if vv else "✗"))
    ws = [r for r in rows if r["domain"].startswith("WS") and r["kind"] in ("adventure", "directing", "acting")]
    if ws:
        print("   ★WS 域之判：%s" % "；".join("%s=%s" % (r["kind"], r["verdict"]) for r in ws))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "rows": rows, "criteria": crit}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   ⇒ 已写：%s" % pathlib.Path(a.json).name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True); sys.exit(main())
