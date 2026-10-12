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


# ── 真路径（2026-10-11 实测可用）：以 302.AI 之联网检索模型作为"指定外部搜索入口" ──
ENDPOINT = "https://api.302ai.cn/v1/chat/completions"
ONLINE = ("sonar-pro", "sonar", "sonar-reasoning", "gemini-2.0-flash-search", "searchapi")


def online_search(query, model="sonar-pro", timeout=120):
    """以 302.AI 联网模型检索；返回 (状态码, 答案, 引用列表)。★引用之真实性未逐一核验。"""
    e = env(); K = e.get("AI302_API_KEY", "")
    if not K:
        return -1, "无 AI302 凭据", []
    body = {"model": model, "messages": [{"role": "user", "content": query}], "max_tokens": 700}
    r = urllib.request.Request(ENDPOINT, data=json.dumps(body, ensure_ascii=False).encode(), method="POST")
    r.add_header("Authorization", "Bearer " + K); r.add_header("Content-Type", "application/json")
    for att in range(1, 4):                       # 戒三十四：网络带重试
        try:
            with urllib.request.urlopen(r, timeout=timeout) as resp:
                j = json.loads(resp.read().decode("utf-8", "replace"))
            msg = (j.get("choices") or [{}])[0].get("message", {}) or {}
            cites = msg.get("citations") or j.get("citations") or []
            return resp.status, (msg.get("content") or ""), list(cites)
        except urllib.error.HTTPError as e2:
            """★墙闸"""
            try:
                _wb = e2.read().decode("utf-8", "replace")
                import sys as _ws, pathlib as _wp
                _ws.path.insert(0, str(_wp.Path(__file__).resolve().parent))
                import wall_guard as _wg
                if _wg.classify(_wb)[0] == "wall":
                    _wg.record(_wb, source=_wp.Path(__file__).name, channel="wall")
                    print("   ★撞墙即停（零重试）")
                    return e2.code, _wb[:200], []
            except Exception:
                pass
            if 400 <= e2.code < 500:
                return e2.code, e2.read().decode("utf-8", "replace")[:200], []
        except Exception as e3:
            if att == 3:
                return -1, str(e3)[:120], []
    return -1, "重试耗尽", []
