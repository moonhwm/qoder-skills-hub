# -*- coding: utf-8 -*-
"""decision_model_api.py —— 决策模型（单次前向：分类／是非判断／评分 ＋ 概率分布 ＋ 置信度）
提供方：302.AI（令条正文给定之入口；默认模型 deepseek-chat，备 gpt-4o-mini／kimi-k2）
★单次前向：一次调用即出结构化判定（不反复追问）；输出严格 JSON，含 probabilities 与 confidence。
用法：python decision_model_api.py [--model deepseek-chat] [--item N] [--json out.json]
（中文串一律用「」）
"""
import argparse, json, pathlib, sys, time, urllib.request, urllib.error

HOME = pathlib.Path.home()
EX = HOME/"WPSDrive"/"29969771"/"WPS云盘"/"月之暗面的Plasma游乐场"/"A2A共同体_共享交换区"

BATTERY = [
 {"id": "D1", "kind": "yesno", "q": "夜间游乐场在 2026-10-11 夜是否已开园（以本席当日出件与录像为据）"},
 {"id": "D2", "kind": "yesno", "q": "世界模型是否会驱动首帧内角色产生位移运动（以本席帧间漂移实验为据）"},
 {"id": "D3", "kind": "yesno", "q": "总线 emit 可否在事后补录而不失真（以纲要与总线格式为据）"},
 {"id": "D4", "kind": "classify", "q": "分类：本席『他人高精外观入世』之举，属（甲）世界探索（乙）实时导演（丙）角色演绎"},
 {"id": "D5", "kind": "score", "q": "评分（0–10）：本席今夜产出之可复核程度（以三闸四数与不符 0 为据）"},
 {"id": "D6", "kind": "yesno", "q": "个人基于人设的动态完善 3D 建模放进世界模型，是否已观察到涌现（以本席二十项实验为据）"},
]
SYS = ("你是结构化决策模型。对给定问题只做一次前向判断，不得追问。"
       "必须只输出 JSON：{\"label\":\"…\",\"probabilities\":{\"选项\":数值,…},\"confidence\":0到1,\"reason\":\"≤40字\"}。"
       "probabilities 之和须为 1；是非题选项用「是」「否」；分类题用「甲」「乙」「丙」；评分题 label 用 0–10 之整数并把各分值归并为 3 档概率。")


def env():
    d = {}
    p = HOME/".zcode"/"workspace"/"default"/"a2a-bridge"/".env"
    for line in p.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("="); d[k.strip()] = v.strip().strip('"').strip("'")
    return d



def tolerant_json(txt):
    """★容错解析：直取 → 首个平衡花括号块 → 去尾逗号重试。"""
    import re as _re
    if not txt: return None
    cands = []
    i = txt.find("{")
    if i >= 0:
        depth = 0
        for k in range(i, len(txt)):
            if txt[k] == "{": depth += 1
            elif txt[k] == "}":
                depth -= 1
                if depth == 0:
                    cands.append(txt[i:k+1]); break
    cands.append(txt)
    for c in cands:
        for variant in (c, _re.sub(r",\s*([}\]])", r"\1", c)):
            try:
                o = json.loads(variant)
                if isinstance(o, dict) and "label" in o: return o
            except Exception:
                continue
    return None

def call(model, q, kind, to=120):
    K = env().get("AI302_API_KEY", "")
    body = {"model": model, "messages": [{"role": "system", "content": SYS}, {"role": "user", "content": q}],
            "max_tokens": 500, "temperature": 0}
    r = urllib.request.Request("https://api.302ai.cn/v1/chat/completions",
                               data=json.dumps(body, ensure_ascii=False).encode(), method="POST")
    r.add_header("Authorization", "Bearer " + K); r.add_header("Content-Type", "application/json")
    for att in range(1, 4):                     # 戒三十四：网络带重试
        try:
            with urllib.request.urlopen(r, timeout=to) as resp:
                j = json.loads(resp.read().decode("utf-8", "replace"))
            txt = ((j.get("choices") or [{}])[0].get("message") or {}).get("content", "")
            obj = tolerant_json(txt)          # ★容错解析（纯 JSON／前有说明／尾有注释／尾逗号 皆可）
            if obj is not None:
                return 200, obj, txt[:200]
            return 200, None, txt[:200]
        except urllib.error.HTTPError as e:
            if 400 <= e.code < 500: return e.code, None, e.read().decode("utf-8", "replace")[:180]
        except Exception as e:
            if att == 3: return -1, None, str(e)[:140]
    return -1, None, "重试耗尽"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--model", default="deepseek-chat")
    ap.add_argument("--item", default=""); ap.add_argument("--json", default="")
    a = ap.parse_args()
    items = [x for x in BATTERY if not a.item or x["id"] == a.item]
    rows = []
    for it in items:
        st, j, raw = call(a.model, "[%s｜%s] %s" % (it["id"], it["kind"], it["q"]), it["kind"])
        if st == 200 and j:
            pr = j.get("probabilities") or {}
            sm = sum(v for v in pr.values() if isinstance(v, (int, float)))
            rows.append({"id": it["id"], "kind": it["kind"], "label": j.get("label"),
                         "probabilities": pr, "prob_sum": round(sm, 3),
                         "confidence": j.get("confidence"), "reason": j.get("reason"), "http": st})
            print("   %-3s %-9s label=%-6s conf=%-5s Σp=%.3f ｜ %s" % (
                it["id"], it["kind"], str(j.get("label"))[:6], str(j.get("confidence"))[:5], sm, str(j.get("reason"))[:34]))
        else:
            rows.append({"id": it["id"], "http": st, "err": raw[:120]})
            print("   %-3s HTTP %s ⇒ %s" % (it["id"], st, raw[:80]))
    ok = [r for r in rows if r.get("http") == 200]
    print("\n   ★ 成功 %d／%d ｜ 平均自报置信度 %s" % (
        len(ok), len(rows),
        round(sum(float(r["confidence"]) for r in ok if r.get("confidence") is not None)/max(1, len(ok)), 3)))
    print("   ⇒ 判：★单次前向之结构化决策（含概率分布与置信度）%s" % ("成立" if ok else "未成"))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S+0800"), "model": a.model,
            "provider": "302.AI", "note": "★单次前向；概率分布与置信度由模型自报，未做标定（须与自建链对拍）",
            "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   落盘：" + a.json)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    main()
