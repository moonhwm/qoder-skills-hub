#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fusion-cast-ops · 整合熔铸元技能核心脚本 v1.2.1（纯标准库，零凭证）
四段循环：萃(extract)→排(deposit)→铸(cast)→验(register+collide+hashgate+audit)。
子命令：
  extract  --qa <qa.jsonl> --out <card.json>        萃取卡生成（原话透传+conf分级+md5+top3_wrong）
  deposit  --card <card.json> --registry <reg.jsonl> --home <域>   沉淀入册（归宿唯一+写前验链）
  register --name <名> --desc "<描述>" --registry-desc <descs.jsonl>  描述入册（写 desc_md5；重名拒）
  collide  --desc "<新描述>" --registry-desc <descs.jsonl> [--threshold 0.3]  C4 注册测撞（≥阈值打回，出 top-3）
  hashgate --name <技能名> --desc "<现描述>" --registry-desc <descs.jsonl>  C2 description 哈希闸（名实漂移检）
  cast     --verdicts <v.jsonl> --version <x.y.z> --prev <x.y.z|none> [--out f]   C8/C9 轮铸裁定重算（多数决+版本锚+回滚指针）
  audit    --skill-dir <dir>                          B 四检闸可机检子集（frontmatter/指针/自指/凭据嗅探）
  --smoke                                           自检（含负断言；只测 happy path 视为无效）
纪律：一切输入文件缺失即报错点名路径（禁静默吞空）；账本路径一律 --registry 显式指定无默认；
异常一律非零退出；smoke 临时目录建在本脚本同级并 finally 清理（不入 /tmp）。
"""
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tempfile, time

GENESIS = "0" * 16


def md5s(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def tokens(text):
    """路由测撞词表：拉丁词 + CJK 字与双字元。"""
    text = (text or "").lower()
    lat = set(re.findall(r"[a-z0-9]+", text))
    cjk = re.findall(r"[一-鿿]", text)
    cjkb = set("".join(p) for p in zip(cjk, cjk[1:])) | set(cjk)
    return lat | cjkb


def jaccard(a, b):
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def must_exist(p, what):
    if not os.path.exists(p):
        sys.exit(f"FAIL: {what}不存在 {p}——先创建或检查路径（禁静默吞空）")


def load_jsonl(p):
    if not os.path.exists(p):
        return []
    rows = []
    for i, line in enumerate(open(p, encoding="utf-8")):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            sys.exit(f"FAIL: {p} 第 {i + 1} 行 JSON 坏行（{e.msg}）——修行或删行后重跑")
    return rows


def chain_verify(rows, p):
    prev = GENESIS
    for i, r in enumerate(rows):
        if "lhash" not in r:
            sys.exit(f"FAIL: {p} 第 {i + 1} 行缺 lhash——链结构残缺疑篡改，停工上报（禁静默跳过）")
        h = r.pop("lhash")
        canon = json.dumps(r, sort_keys=True, ensure_ascii=False)
        if md5s(prev + canon)[:16] != h:
            sys.exit(f"FAIL: {p} 哈希链断裂于 {r.get('type', '?')}——登记台被篡改，停工上报")
        r["lhash"] = h
        prev = h


def append_jsonl(p, row):
    rows = load_jsonl(p)
    chain_verify(rows, p)
    prev = rows[-1]["lhash"] if rows else GENESIS
    row["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    canon = json.dumps(row, sort_keys=True, ensure_ascii=False)
    row["lhash"] = md5s(prev + canon)[:16]
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows + [row]:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, p)
    return row["lhash"]


# ---------- 萃 ----------
def cmd_extract(a):
    """从问答日志萃取卡片。qa.jsonl 每行 {"q":...,"a":...,"conf":"实证|估算|假设"}。
    铁律：原话透传（禁摘要改写）；conf 必填且 ∈ {实证,估算,假设}；每次必含一条对 Agent 本体问答。"""
    must_exist(a.qa, "问答日志")
    rows = load_jsonl(a.qa)
    if not rows:
        sys.exit("FAIL: 空问答日志，无物可萃")
    for i, r in enumerate(rows):
        if not r.get("q") or not r.get("a"):
            sys.exit(f"FAIL: 第 {i + 1} 行缺 q/a——萃取只做透传，不补写")
        if r.get("conf") not in ("实证", "估算", "假设"):
            sys.exit(f"FAIL: 第 {i + 1} 行 conf 缺失或非法（须 实证/估算/假设）")
    if not any(r.get("about_agent") for r in rows):
        sys.exit("FAIL: 缺对 Agent 本体问答（about_agent=true 至少一条）——对齐原始积累不可跳")
    wrong = [r for r in rows if r.get("verdict") == "wrong"][:3]
    card = {
        "type": "extract_card",
        "n_qa": len(rows),
        "qa_md5": md5s(open(a.qa, encoding="utf-8").read()),
        "conf_dist": {c: sum(1 for r in rows if r["conf"] == c) for c in ("实证", "估算", "假设")},
        "top3_wrong": [{"q": r["q"], "a": r["a"], "why": r.get("why", "")} for r in wrong],
        "claims": [{"q": r["q"], "a": r["a"], "conf": r["conf"]} for r in rows],
    }
    card["card_md5"] = md5s(json.dumps(card, sort_keys=True, ensure_ascii=False))
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(card, f, ensure_ascii=False, indent=1)
    print(f"extract ok: {len(rows)} 条 → {a.out} card_md5={card['card_md5'][:12]} "
          f"conf={card['conf_dist']} wrong={len(card['top3_wrong'])}")


# ---------- 排 ----------
def cmd_deposit(a):
    """沉淀入册：归宿域唯一（同 card_md5 重复入册=幂等跳过；同卡异归宿=拒绝）；写前验链。"""
    must_exist(a.card, "萃取卡")
    try:
        card = json.load(open(a.card, encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: 萃取卡 JSON 坏: {a.card}（{e}）——先重跑 extract 产卡")
    if card.get("type") != "extract_card":
        sys.exit("FAIL: 非萃取卡，拒绝入册（沉淀只认 extract 产物）")
    rows = load_jsonl(a.registry)
    chain_verify(rows, a.registry)
    for r in rows:
        if r.get("card_md5") == card.get("card_md5"):
            if r.get("home") == a.home:
                print(f"deposit 幂等: card={card['card_md5'][:12]} 已在域 {a.home}，跳过")
                return
            sys.exit(f"FAIL: 归宿冲突——卡 {card['card_md5'][:12]} 已属 {r.get('home')}，拒绝再入 {a.home}（正交检）")
    h = append_jsonl(a.registry, {"type": "deposit", "card_md5": card["card_md5"], "home": a.home,
                                  "n_claims": card.get("n_qa")})
    print(f"deposit ok: 域={a.home} 卡={card['card_md5'][:12]} lhash={h}")


# ---------- 描述入册 ----------
def cmd_register(a):
    """描述入册：写 {name, desc, desc_md5}；重名拒。入册前先跑 collide 是调用方纪律（段4 顺序：collide→register）。"""
    if not a.name or not a.desc.strip():
        sys.exit("FAIL: name/desc 不能为空")
    rows = load_jsonl(a.registry_desc) if os.path.exists(a.registry_desc) else []
    if any(r.get("name") == a.name for r in rows):
        sys.exit(f"FAIL: 重名 {a.name}——改名或先走 hashgate 核查在册件")
    with open(a.registry_desc, "a", encoding="utf-8") as f:
        f.write(json.dumps({"name": a.name, "desc": a.desc, "desc_md5": md5s(a.desc)},
                           ensure_ascii=False) + "\n")
    print(f"register ok: {a.name} desc_md5={md5s(a.desc)[:12]} → {a.registry_desc}")


# ---------- 验：C4 测撞 ----------
def cmd_collide(a):
    """C4 注册即测撞：新 description vs 注册表全量，Jaccard≥threshold 打回（默认 0.3——
    标定依据：同文=1.0、低撞面≈0 的取值中点偏上，0.2-0.4 可调）；C6 出 top-3 近邻供澄清。"""
    must_exist(a.registry_desc, "注册表描述")
    if not (0.05 <= a.threshold <= 0.95):
        sys.exit(f"FAIL: --threshold={a.threshold} 越界（合法域 [0.05,0.95]）——C4 闸禁被参数整体绕过")
    descs = load_jsonl(a.registry_desc)
    if not descs:
        sys.exit("FAIL: 注册表描述为空——测撞无基线，拒绝放行（禁静默）")
    t = tokens(a.desc)
    if len(t) < 8:
        sys.exit(f"FAIL: 描述词表过小（{len(t)}<8）——触发面太短无法测撞，补触发词后重测")
    scored = sorted(((jaccard(t, tokens(d.get("desc", ""))), d.get("name", "?")) for d in descs), reverse=True)
    top3 = [(n, round(j, 3)) for j, n in scored[:3]]
    hit = next(((j, n) for j, n in scored if j >= a.threshold), None)
    if hit:
        print(f"COLLIDE_REJECT: 撞 {hit[1]} J={hit[0]:.3f}≥{a.threshold} | top3={top3}")
        sys.exit(3)
    print(f"collide ok: maxJ={top3[0][1]} | top3={top3} | threshold={a.threshold}")


# ---------- 验：C2 哈希闸 ----------
def cmd_hashgate(a):
    """C2 description 入哈希闸：在册 md5(desc) 与现 desc 比对，不一致=名实漂移；重名即拒。"""
    must_exist(a.registry_desc, "注册表描述")
    rows = load_jsonl(a.registry_desc)
    names = [r.get("name") for r in rows]
    if len(names) != len(set(names)):
        sys.exit("FAIL: 注册表重名——台账先修，哈希闸拒在脏表上判决")
    descs = {d.get("name"): d for d in rows}
    if a.name not in descs:
        sys.exit(f"FAIL: 注册表无 {a.name}——先注册（register）再过闸（装过≠在册）")
    want = descs[a.name].get("desc_md5") or md5s(descs[a.name].get("desc", ""))
    got = md5s(a.desc)
    if got != want:
        print(f"HASHGATE_FAIL: {a.name} 描述漂移 got={got[:12]} want={want[:12]}")
        sys.exit(4)
    print(f"hashgate ok: {a.name} desc_md5={got[:12]} 一致")


# ---------- 铸 ----------
def cmd_cast(a):
    """C8/C9 轮铸裁定：判官 verdict 重算（不采信自述多数），奇数多数决：
    better 多数=KEEP / worse 多数=REVERT / 否则=DRAW；margin 按多数方票内 slight 计数（KEEP/REVERT 对称）。"""
    must_exist(a.verdicts, "判官票")
    vs = load_jsonl(a.verdicts)
    if len(vs) < 3 or len(vs) % 2 == 0:
        sys.exit(f"FAIL: 判官票数须为奇数且 ≥3（实收 {len(vs)}）——奇数多数决")
    if not re.fullmatch(r"\d+\.\d+\.\d+", a.version or ""):
        sys.exit(f"FAIL: --version={a.version!r} 非 x.y.z——C9 版本锚禁垃圾值污染")
    if a.prev != "none" and not re.fullmatch(r"\d+\.\d+\.\d+", a.prev or ""):
        sys.exit(f"FAIL: --prev={a.prev!r} 须为 x.y.z 或 none——回滚指针禁垃圾值")
    votes = [v.get("vote") for v in vs]
    for i, v in enumerate(votes):
        if v not in ("better", "worse", "same"):
            sys.exit(f"FAIL: 第 {i + 1} 票 vote 非法（合法枚举 better/worse/same，实收 {v!r}）")
    for i, v in enumerate(vs):
        if v["vote"] in ("better", "worse") and v.get("margin") not in ("slight", "clear"):
            sys.exit(f"FAIL: 第 {i + 1} 票缺 margin 或非法——缺省拒收（禁向 clear 方向 fail-open）")
    b, w = votes.count("better"), votes.count("worse")
    n = len(vs)

    def margin_of(side):
        ms = [v.get("margin") for v in vs if v["vote"] == side]
        return "slight" if ms.count("slight") >= 1 else "clear"

    if b > n // 2:
        margin, decision = margin_of("better"), "KEEP"
    elif w > n // 2:
        margin, decision = margin_of("worse"), "REVERT"
    else:
        margin, decision = "tie", "DRAW"
    rec = {"type": "cast", "version": a.version, "prev": a.prev, "decision": decision,
           "margin": margin, "votes": {"better": b, "worse": w, "same": votes.count("same")},
           "judges": [v.get("judge") for v in vs]}
    rec["rollback_to"] = a.prev if decision == "REVERT" else None
    out = a.out or f"cast_{a.version}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print(f"cast ok: {decision}/{margin} votes={rec['votes']} version={a.version} "
          f"rollback_to={rec['rollback_to']} → {out}")


# ---------- 验：B 四检闸（可机检子集） ----------
def extract_description(fm):
    """frontmatter description 提取：支持 双引号行 / >- > |- | 块标量（取后续缩进块）/ 裸行。"""
    m = re.search(r'^description:\s*"((?:[^"\\]|\\.)*)"', fm, re.M)
    if m:
        return m.group(1).strip()
    m = re.search(r'^description:\s*[>|][+-]?[0-9]?\s*\n', fm, re.M)  # 覆盖 > >- >+ | |- |+ |2 等合法 YAML 块标量指示符（实证席 N-1 根绝）
    if m:
        blk = []
        for ln in fm[m.end():].split("\n"):
            if ln.strip() == "":
                continue  # 块标量内空行属内容（YAML 规范），不因空行截断
            if re.match(r"^[ \t]+\S", ln):
                blk.append(ln.strip())
                continue
            break  # 首个非空 dedent 行 = 块结束
        return re.sub(r"\s+", " ", " ".join(blk)).strip()
    m = re.search(r'^description:\s*(\S.*)$', fm, re.M)
    return (m.group(1) if m else "").strip()


def cmd_audit(a):
    """可机检项：①frontmatter description ≤1024 且非空（含块标量写法）②自指频度 ③references 指针可达
    ④凭据嗅探。语义层（偏差度量/保真判读）归人工+判官，本命令不冒充。"""
    d = a.skill_dir
    sk = os.path.join(d, "SKILL.md")
    if not os.path.exists(sk):
        sys.exit("FAIL: SKILL.md 缺失")
    t = open(sk, encoding="utf-8").read()
    fails = []
    m = re.search(r"^---\n(.*?)\n---", t, re.S)
    if not m:
        fails.append("frontmatter 缺失")
    else:
        desc = extract_description(m.group(1))
        if not desc or len(desc) > 1024:
            fails.append(f"description 长度 {len(desc)} 越界(0,1024]")
    for ref in re.findall(r'\(([^)]+\.md)\)|references/([\w.-]+)', t):
        ref = ref[0] or ("references/" + ref[1])
        rp = ref if os.path.isabs(ref) else os.path.join(d, ref)
        if not os.path.exists(rp):
            fails.append(f"指针断裂: {ref}")
    name_m = re.search(r"name:\s*(\S+)", t)
    if name_m and t.count(name_m.group(1)) > 40:
        fails.append("疑似自指过载（名频>40）")
    pat = re.compile("PRIV" + r"ATE KEY|Bearer\s+[A-Za-z0-9]|eyJ[A-Za-z0-9_-]{20,}", re.I)
    for dp, _, fns in os.walk(d):
        if "__pycache__" in dp:
            continue
        for fn in fns:
            p = os.path.join(dp, fn)
            try:
                c = open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            if pat.search(c):
                fails.append(f"凭据嗅探命中: {os.path.relpath(p, d)}")
    if fails:
        print("AUDIT_FAIL: " + "; ".join(fails))
        sys.exit(5)
    print(f"audit ok: {d} 四检闸可机检子集全过")


# ---------- 自检 ----------
def smoke():
    here = os.path.dirname(os.path.abspath(__file__))
    tmp = tempfile.mkdtemp(prefix="fusion_cast_smoke_", dir=here)
    ok = []
    try:
        def run(args):
            return subprocess.run([sys.executable, os.path.abspath(__file__)] + args,
                                  capture_output=True, text=True)

        # 正例 1：萃取→沉淀 链路
        qa = os.path.join(tmp, "qa.jsonl")
        with open(qa, "w", encoding="utf-8") as f:
            f.write(json.dumps({"q": "折扣率取多少", "a": "r=4%-8% 上限12%", "conf": "实证", "about_agent": False}) + "\n")
            f.write(json.dumps({"q": "本席上次误判在哪", "a": "把窄带说成更宽", "conf": "实证", "about_agent": True, "verdict": "wrong", "why": "16.3pp→14.1pp"}) + "\n")
        card = os.path.join(tmp, "card.json")
        r = run(["extract", "--qa", qa, "--out", card])
        ok.append(("萃取正例", r.returncode == 0))
        reg = os.path.join(tmp, "reg.jsonl")
        r = run(["deposit", "--card", card, "--registry", reg, "--home", "金融折扣"])
        ok.append(("沉淀正例", r.returncode == 0))

        # 负断言 1：conf 非法必拒，报错行号 1 基
        qa_bad = os.path.join(tmp, "qa_bad.jsonl")
        with open(qa_bad, "w", encoding="utf-8") as f:
            f.write(json.dumps({"q": "x", "a": "y", "conf": "听说", "about_agent": True}) + "\n")
        r = run(["extract", "--qa", qa_bad, "--out", os.path.join(tmp, "c2.json")])
        ok.append(("负断言:conf非法拒萃取+行号1基", r.returncode != 0 and "第 1 行" in (r.stdout + r.stderr)))

        # 负断言 2：缺 Agent 本体问答必拒
        qa_bad2 = os.path.join(tmp, "qa_bad2.jsonl")
        with open(qa_bad2, "w", encoding="utf-8") as f:
            f.write(json.dumps({"q": "x", "a": "y", "conf": "实证"}) + "\n")
        r = run(["extract", "--qa", qa_bad2, "--out", os.path.join(tmp, "c3.json")])
        ok.append(("负断言:缺本体问答拒萃取", r.returncode != 0))

        # 负断言 3：异归宿必拒（正交检）
        r = run(["deposit", "--card", card, "--registry", reg, "--home", "别域"])
        ok.append(("负断言:归宿冲突拒入册", r.returncode != 0))

        # 负断言 4：输入文件不存在必点名路径
        r = run(["collide", "--desc", "随便一段足够长的描述文本用于触发", "--registry-desc", os.path.join(tmp, "nope.jsonl")])
        ok.append(("负断言:缺文件点名路径", r.returncode != 0 and "不存在" in (r.stdout + r.stderr)))

        # register → collide/hashgate 链路
        descs = os.path.join(tmp, "descs.jsonl")
        r = run(["register", "--name", "alpha-ops", "--desc", "技能锻造 萃取 沉淀 轮铸 判官 复评 收敛", "--registry-desc", descs])
        ok.append(("register 入册", r.returncode == 0))
        r = run(["register", "--name", "alpha-ops", "--desc", "别的", "--registry-desc", descs])
        ok.append(("负断言:重名拒入册", r.returncode != 0))
        with open(descs, "a", encoding="utf-8") as f:
            f.write(json.dumps({"name": "beta-ops", "desc": "通勤 路线 规划 地铁 公交"}) + "\n")

        # C4 测撞：同文必打回；低撞面放行；短描述报错指人话
        r = run(["collide", "--desc", "技能锻造 萃取 沉淀 轮铸 判官 复评 收敛", "--registry-desc", descs])
        ok.append(("负断言:同文测撞打回", r.returncode == 3))
        r = run(["collide", "--desc", "量子 引力 波函数 坍缩 观测 实验", "--registry-desc", descs])
        ok.append(("测撞放行低撞面", r.returncode == 0))
        r = run(["collide", "--desc", "融合铸造", "--registry-desc", descs])
        ok.append(("负断言:短描述拒且提示补触发词", r.returncode != 0 and "补触发词" in (r.stdout + r.stderr)))

        # C2 哈希闸：篡改必拒
        r = run(["hashgate", "--name", "alpha-ops", "--desc", "技能锻造 萃取 沉淀 轮铸 判官 复评 收敛", "--registry-desc", descs])
        ok.append(("哈希闸放行原描述", r.returncode == 0))
        r = run(["hashgate", "--name", "alpha-ops", "--desc", "篡改过的描述", "--registry-desc", descs])
        ok.append(("负断言:漂移描述打回", r.returncode == 4))

        # C8 裁定重算：KEEP / REVERT-slight 对称 / 偶数拒
        v = os.path.join(tmp, "v.jsonl")
        with open(v, "w", encoding="utf-8") as f:
            for j, vote in (("DS", "better"), ("GLM", "better"), ("KIMI", "same")):
                f.write(json.dumps({"judge": j, "vote": vote, "margin": "clear"}) + "\n")
        r = run(["cast", "--verdicts", v, "--version", "1.1.0", "--prev", "1.0.0", "--out", os.path.join(tmp, "cast.json")])
        d = json.load(open(os.path.join(tmp, "cast.json"))) if r.returncode == 0 else {}
        ok.append(("裁定重算 KEEP", r.returncode == 0 and d.get("decision") == "KEEP"))
        with open(v, "w", encoding="utf-8") as f:
            for j, vote, mg in (("DS", "worse", "slight"), ("GLM", "worse", "clear"), ("KIMI", "same", "clear")):
                f.write(json.dumps({"judge": j, "vote": vote, "margin": mg}) + "\n")
        r = run(["cast", "--verdicts", v, "--version", "1.1.0", "--prev", "1.0.0", "--out", os.path.join(tmp, "cast2.json")])
        d = json.load(open(os.path.join(tmp, "cast2.json"))) if r.returncode == 0 else {}
        ok.append(("REVERT margin 对称 slight", r.returncode == 0 and d.get("decision") == "REVERT" and d.get("margin") == "slight" and d.get("rollback_to") == "1.0.0"))
        with open(v, "w", encoding="utf-8") as f:
            for j in ("A", "B"):
                f.write(json.dumps({"judge": j, "vote": "better", "margin": "clear"}) + "\n")
        r = run(["cast", "--verdicts", v, "--version", "1.1.0", "--prev", "1.0.0"])
        ok.append(("负断言:偶数票拒裁", r.returncode != 0))

        # 负断言 5：audit 对 >- 块标量超长描述必须打回（fail-closed）
        ev = os.path.join(tmp, "evskill")
        os.makedirs(ev)
        with open(os.path.join(ev, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write("---\nname: evskill\ndescription: >-\n  " + "长" * 1200 + "\n---\n# x\n")
        r = run(["audit", "--skill-dir", ev])
        ok.append(("负断言:块标量超长描述打回", r.returncode == 5))

        # 负断言 6：registry 哈希链篡改必断链停工
        rows = [json.loads(l) for l in open(reg, encoding="utf-8") if l.strip()]
        rows[0]["home"] = "被篡改"
        with open(reg, "w", encoding="utf-8") as f:
            for rrow in rows:
                f.write(json.dumps(rrow, ensure_ascii=False) + "\n")
        r = run(["deposit", "--card", card, "--registry", reg, "--home", "金融折扣"])
        ok.append(("负断言:链篡改断链停工", r.returncode != 0 and "断裂" in (r.stdout + r.stderr)))

        # 负断言 7：块标量内空行截断绕过必堵（实证席 D-1 反用例：900+空行+900 应判超长）
        ev2 = os.path.join(tmp, "evskill2")
        os.makedirs(ev2)
        with open(os.path.join(ev2, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write("---\nname: evskill2\ndescription: >-\n  " + "甲" * 900 + "\n\n  " + "乙" * 900 + "\n---\n# x\n")
        r = run(["audit", "--skill-dir", ev2])
        ok.append(("负断言:块标量空行绕过打回", r.returncode == 5))

        # 负断言 8：registry 混入无 lhash 影子行必停工（实证席 D-2 反用例）
        reg3 = os.path.join(tmp, "reg3.jsonl")
        r = run(["deposit", "--card", card, "--registry", reg3, "--home", "金融折扣"])
        with open(reg3, "a", encoding="utf-8") as f:
            f.write(json.dumps({"type": "deposit", "card_md5": "shadow", "home": "影"}) + "\n")
        r = run(["deposit", "--card", card, "--registry", reg3, "--home", "金融折扣"])
        ok.append(("负断言:缺lhash影子行断链停工", r.returncode != 0 and "缺 lhash" in (r.stdout + r.stderr)))

        # 负断言 9：判官票缺 margin 必拒收（对抗席 P2-4 反用例：禁向 clear fail-open）
        v2 = os.path.join(tmp, "v2.jsonl")
        with open(v2, "w", encoding="utf-8") as f:
            f.write(json.dumps({"judge": "A", "vote": "better"}) + "\n")
            f.write(json.dumps({"judge": "B", "vote": "better", "margin": "clear"}) + "\n")
            f.write(json.dumps({"judge": "C", "vote": "same"}) + "\n")
        r = run(["cast", "--verdicts", v2, "--version", "1.2.0", "--prev", "1.1.0"])
        ok.append(("负断言:缺margin票拒收", r.returncode != 0 and "margin" in (r.stdout + r.stderr)))

        # 负断言 10：>+/|2 等块标量变体不得绕过 1024 闸（实证席 N-1 反用例）
        ev3 = os.path.join(tmp, "evskill3")
        os.makedirs(ev3)
        with open(os.path.join(ev3, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write("---\nname: evskill3\ndescription: >+\n  " + "甲" * 1200 + "\n---\n# x\n")
        r = run(["audit", "--skill-dir", ev3])
        ok.append(("负断言:块标量变体绕过打回", r.returncode == 5))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    fails = [n for n, good in ok if not good]
    for n, good in ok:
        print(("PASS " if good else "FAIL ") + n)
    print(f"\nSMOKE {'PASS' if not fails else 'FAIL'} ({len(ok) - len(fails)}/{len(ok)})")
    sys.exit(1 if fails else 0)


def main():
    ap = argparse.ArgumentParser(prog="fusion_cast")
    ap.add_argument("--smoke", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("extract"); p.add_argument("--qa", required=True); p.add_argument("--out", required=True); p.set_defaults(f=cmd_extract)
    p = sub.add_parser("deposit"); p.add_argument("--card", required=True); p.add_argument("--registry", required=True); p.add_argument("--home", required=True); p.set_defaults(f=cmd_deposit)
    p = sub.add_parser("register"); p.add_argument("--name", required=True); p.add_argument("--desc", required=True); p.add_argument("--registry-desc", required=True); p.set_defaults(f=cmd_register)
    p = sub.add_parser("collide"); p.add_argument("--desc", required=True); p.add_argument("--registry-desc", required=True); p.add_argument("--threshold", type=float, default=0.3); p.set_defaults(f=cmd_collide)
    p = sub.add_parser("hashgate"); p.add_argument("--name", required=True); p.add_argument("--desc", required=True); p.add_argument("--registry-desc", required=True); p.set_defaults(f=cmd_hashgate)
    p = sub.add_parser("cast"); p.add_argument("--verdicts", required=True); p.add_argument("--version", required=True); p.add_argument("--prev", required=True); p.add_argument("--out"); p.set_defaults(f=cmd_cast)
    p = sub.add_parser("audit"); p.add_argument("--skill-dir", required=True); p.set_defaults(f=cmd_audit)
    a = ap.parse_args()
    if a.smoke:
        smoke()
    elif hasattr(a, "f"):
        a.f(a)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
