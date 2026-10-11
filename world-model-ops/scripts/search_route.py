# -*- coding: utf-8 -*-
"""search_route.py —— 搜索路由接入口（应纲要行 62：Bing 与 Google 固化为指定引擎）
★现状：无凭据 ⇒ 只做"待凭据"自检；凭据一到即可跑（本器为预备接入，不擅自爬取）
凭据来源：.env 之 BING_API_KEY／GOOGLE_CSE_KEY+GOOGLE_CSE_CX／SERPAPI_KEY／AI302_API_KEY
用法：python search_route.py --query "…" [--engine auto|bing|google|serpapi]
（中文串一律用「」）
"""
import argparse, json, pathlib, sys, urllib.request, urllib.error

HOME = pathlib.Path.home()
ENVP = HOME/".zcode"/"workspace"/"default"/"a2a-bridge"/".env"


def env():
    d = {}
    if ENVP.exists():
        for line in ENVP.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("="); d[k.strip()] = v.strip().strip('"').strip("'")
    return d


def probe():
    e = env()
    cand = {"bing": "BING_API_KEY" in e, "google": ("GOOGLE_CSE_KEY" in e and "GOOGLE_CSE_CX" in e),
            "serpapi": "SERPAPI_KEY" in e, "ai302": "AI302_API_KEY" in e}
    print("  ═══ 搜索路由凭据自检 ═══")
    for k, v in cand.items():
        print("   %-8s %s" % (k, "✓ 有" if v else "— 无"))
    ok = [k for k, v in cand.items() if v]
    print("   ⇒ 判：%s" % ("可用引擎：" + "、".join(ok) if ok else "★无凭据 ⇒ 待授权/待凭据（本器暂只自检）"))
    return ok


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--query", default=""); ap.add_argument("--engine", default="auto")
    a = ap.parse_args()
    ok = probe()
    if not a.query:
        return 0
    if not ok:
        print("   ⇒ 查询未执行（无凭据）。★建议：以 API 之 key 入 .env（键名见本器文档串），或授我直连爬取之许可。")
        return 1
    print("   ⇒ 查询：%s（引擎 %s）" % (a.query[:60], a.engine if a.engine != "auto" else ok[0]))
    print("   ★实现待凭据到位后补（本器已留接入口；不擅自写死端点，以免误用）")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.exit(main())
