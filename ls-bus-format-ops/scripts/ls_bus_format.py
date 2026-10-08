#!/usr/bin/env python3
"""ls-bus-format-ops 核心脚本：ls 清单 → 上传总线留痕（SQL 底稿）→ 本地格式化。

三段式：
  scan     递归列出 target_dir，按自我设定规则分类 keep/purge，输出清单（JSON+MD+sha256）
  bussql   由 scan 清单生成总线 INSERT SQL 底稿（脚本生成，禁人工转录；执行须另经批准）
  execute  删除 purge 清单内文件（须 --approve=<manifest_sha256 前16> 且清单未变）

硬闸（不可覆盖）：
  * target_dir 必须位于 /mnt/agents/output 之内（含其本身）
  * KEEP 识别双保险：分类时一次、删除前逐文件再一次
  * 永不跟随符号链接；永不删除 KEEP 命中项；runs 留痕目录强制保留
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

ALLOWED_ROOT = os.path.realpath("/mnt/agents/output")
RUNS_DIRNAME = "_ls_bus_format_runs"

# 自我设定（身份/人设/席位设定区块）默认识别模式——命中即保留
# v1.2.2：增补 ".skill"——技能打包交付件默认保留（巡检实证：默认集曾把本技能自身
# 交付包 ls-bus-format-ops.skill 误判 purge，X 席独立白名单佐证该洞真实）；
# "台账"（交割/运维台账类留痕账册，与 留痕 同族，档案即账本纪律下默认保留）
KEEP_PATTERNS = [
    "persona", "人设", "周嘤鸣", "授名", "署名", "身份锚点", "锚点",
    "handoff", "genealogy", "engine_r", "自我设定", "本席设定", "席位",
    "seat-naming", "naming", ".skill", "台账", RUNS_DIRNAME,
]


def sha256_of(path, block=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(block)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def is_keep(relpath, extra_patterns):
    pats = KEEP_PATTERNS + (extra_patterns or [])
    low = relpath.lower()
    return any(p.lower() in low for p in pats)


def resolve_target(raw):
    t = os.path.realpath(raw)
    if t != ALLOWED_ROOT and not t.startswith(ALLOWED_ROOT + os.sep):
        raise SystemExit(f"REFUSE: target_dir 须在 {ALLOWED_ROOT} 之内，收到: {t}")
    if not os.path.isdir(t):
        raise SystemExit(f"REFUSE: 目录不存在: {t}")
    return t


def load_extra_patterns(keep_file):
    if not keep_file:
        return []
    with open(keep_file, encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]


# ---- Hook 机制（v1.1.0）----
# 四相位：pre_scan / post_scan / pre_execute / post_execute
# pre_* 为否决相位（exit!=0 → REFUSE 中止）；post_* 为观察相位（exit!=0 仅记痕不中止）
# 安全闸：hook-dir 严禁位于 target_dir 之内（目标目录按不可信数据处理，绝不从中发现执行钩子）；
#         shell=False + 环境变量传参（不拼接命令行，防注入）；逐次调用写 JSONL 钩痕
HOOK_PHASES = ("pre_scan", "post_scan", "pre_execute", "post_execute")
VETO_PHASES = ("pre_scan", "pre_execute")


def resolve_hook_dir(raw, target):
    if not raw:
        return None
    d = os.path.realpath(raw)
    t = os.path.realpath(target)
    if d == t or d.startswith(t + os.sep):
        raise SystemExit("REFUSE: hook-dir 不得位于 target_dir 之内（目标目录按不可信数据处理）")
    if not os.path.isdir(d):
        raise SystemExit(f"REFUSE: hook-dir 不存在: {d}")
    return d


def _hook_candidate(hook_dir, phase):
    for cand in (phase, phase + ".py", phase + ".sh"):
        p = os.path.join(hook_dir, cand)
        if os.path.isfile(p):
            return p
    return None


def run_hook(phase, hook_dir, target, context, timeout, log_path):
    """执行单相位钩子；返回 (outcome, detail)。outcome ∈ ran/vetoed/skipped_absent/skipped_notrunnable/failed"""
    import subprocess
    import time
    if not hook_dir:
        return "skipped_absent", ""
    path = _hook_candidate(hook_dir, phase)
    if not path:
        return "skipped_absent", ""
    if path.endswith(".py"):
        argv = [sys.executable, path]
    elif path.endswith(".sh"):
        argv = ["/bin/sh", path]
    elif os.access(path, os.X_OK):
        argv = [path]
    else:
        _log_hook(log_path, phase, path, "skipped_notrunnable", -1, 0)
        return "skipped_notrunnable", path
    env = dict(os.environ)
    env.update({
        "LBF_PHASE": phase,
        "LBF_TARGET": target,
        "LBF_MANIFEST": context.get("manifest", ""),
        "LBF_MANIFEST_SHA256": context.get("manifest_sha256", ""),
        "LBF_COUNTS_JSON": json.dumps(context.get("counts", {}), ensure_ascii=False),
        "LBF_DETAIL_JSON": json.dumps(context.get("detail", {}), ensure_ascii=False),
        "LBF_RUNS_DIR": context.get("runs_dir", ""),
    })
    t0 = time.time()
    proc = subprocess.Popen(argv, env=env, shell=False, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            start_new_session=True)  # 子进程自成会话组长→超时可 killpg 灭孙进程
    try:
        out, err = proc.communicate(timeout=timeout)
        ms = int((time.time() - t0) * 1000)
        outcome = "ran" if proc.returncode == 0 else (
            "vetoed" if phase in VETO_PHASES else "failed")
        _log_hook(log_path, phase, path, outcome, proc.returncode, ms,
                  (out or "")[-500:], (err or "")[-500:])
        return outcome, path
    except subprocess.TimeoutExpired:
        import signal
        try:
            os.killpg(proc.pid, signal.SIGKILL)  # start_new_session 使 pid 即 pgid
        except (ProcessLookupError, PermissionError):
            pass
        out, err = proc.communicate()
        ms = int((time.time() - t0) * 1000)
        outcome = "vetoed" if phase in VETO_PHASES else "failed"
        _log_hook(log_path, phase, path, outcome + "_timeout", -1, ms,
                  (out or "")[-500:], (err or "")[-500:])
        return outcome, path


def _log_hook(log_path, phase, path, outcome, rc, ms, out="", err=""):
    if not log_path:
        return
    rec = {"ts_utc": datetime.now(timezone.utc).isoformat(), "phase": phase,
           "hook": path, "outcome": outcome, "exit": rc, "ms": ms,
           "stdout_tail": out, "stderr_tail": err}
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        print(f"WARN: 钩痕写不入 {log_path}（审计痕可能丢失）", file=sys.stderr)


def _write_progress(path, phase, done, total):
    if not path:
        return
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"phase": phase, "done": done, "total": total,
                       "ts_utc": datetime.now(timezone.utc).isoformat()}, f)
    except OSError:
        pass


def scan(target, extra_patterns, hash_keep=True, pace=200, pace_sleep=0.1,
         progress_path=None):
    """递归分类清单。hash_keep=False 时 keep 类只列名不哈希（漂移重扫加速——
    漂移语义只依赖 purge 哈希与新增 purge 检测，keep 哈希本无判据用途）。
    pace>0 时每 pace 件 sleep pace_sleep 秒让渡 I/O——梯度读取，
    防万件级洪峰饿死同挂载宿主（v1.2.0 卡死事故教训）。"""
    import time as _t
    entries = []
    n = 0
    for dirpath, dirnames, filenames in os.walk(target, followlinks=False):
        dirnames.sort()
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            if os.path.islink(full):
                if not os.path.exists(full):  # 死链（同步层占位残影）——v1.2.1 起入册可清扫
                    entries.append({"rel": os.path.relpath(full, target),
                                    "size": 0, "sha256": "", "class": "deadlink"})
                continue  # 活符号链接永不跟随、永不入册
            rel = os.path.relpath(full, target)
            st = os.stat(full)
            cls = "keep" if is_keep(rel, extra_patterns) else "purge"
            entries.append({
                "rel": rel,
                "size": st.st_size,
                "sha256": sha256_of(full) if (cls == "purge" or hash_keep) else "",
                "class": cls,
            })
            n += 1
            if pace and n % pace == 0:
                _write_progress(progress_path, "scanning", n, None)
                _t.sleep(pace_sleep)
    _write_progress(progress_path, "scan_done", n, None)
    return entries


def cmd_scan(args):
    target = resolve_target(args.target_dir)
    hook_dir = resolve_hook_dir(getattr(args, "hook_dir", None), target)
    hlog = os.path.join(target, RUNS_DIRNAME, "hooks.jsonl")
    ctx = {"runs_dir": os.path.join(target, RUNS_DIRNAME)}
    outcome, hpath = run_hook("pre_scan", hook_dir, target, ctx,
                              getattr(args, "hook_timeout", 30), hlog)
    if outcome.startswith("vetoed"):
        raise SystemExit(f"REFUSE: pre_scan 钩子否决（{hpath}）")
    extra = load_extra_patterns(args.keep_file)
    entries = scan(target, extra, pace=args.pace, pace_sleep=args.pace_sleep,
                   progress_path=os.path.join(target, RUNS_DIRNAME, "progress.json"))
    keep = [e for e in entries if e["class"] == "keep"]
    purge = [e for e in entries if e["class"] == "purge"]
    deadlink = [e for e in entries if e["class"] == "deadlink"]
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest = {
        "tool": "ls-bus-format-ops",
        "ts_utc": ts,
        "target_dir": target,
        "keep_patterns": KEEP_PATTERNS + extra,
        "counts": {"total": len(entries), "keep": len(keep), "purge": len(purge),
                   "deadlink": len(deadlink)},
        "keep": keep,
        "purge": purge,
        "deadlink": deadlink,
    }
    mtext = json.dumps(manifest, ensure_ascii=False, indent=1, sort_keys=True)
    mhash = hashlib.sha256(mtext.encode()).hexdigest()
    manifest["manifest_sha256"] = mhash
    runs = os.path.join(target, RUNS_DIRNAME)
    os.makedirs(runs, exist_ok=True)
    mpath = os.path.join(runs, f"manifest_{ts}.json")
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1, sort_keys=True)
    md = [f"# ls 清单 {ts}", f"target={target} total={len(entries)} keep={len(keep)} purge={len(purge)}",
          f"manifest_sha256={mhash}", "", "## purge（待格式化）"]
    md += [f"- {e['rel']} ({e['size']}B, sha256:{e['sha256'][:12]}…)" for e in purge]
    md += ["", "## keep（自我设定，保留）"]
    md += [f"- {e['rel']} ({e['size']}B)" for e in keep]
    mdpath = os.path.join(runs, f"manifest_{ts}.md")
    with open(mdpath, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print(json.dumps({"manifest": mpath, "manifest_md": mdpath,
                      "manifest_sha256": mhash, "counts": manifest["counts"]},
                     ensure_ascii=False, indent=1))
    ctx2 = {"manifest": mpath, "manifest_sha256": mhash,
            "counts": manifest["counts"], "runs_dir": runs}
    run_hook("post_scan", hook_dir, target, ctx2, getattr(args, "hook_timeout", 30), hlog)
    print("DRY-RUN：未删除任何文件。格式化须先 bussql 留痕，再 execute --approve=" + mhash[:16])


def cmd_bussql(args):
    with open(args.manifest, encoding="utf-8") as f:
        m = json.load(f)
    mhash = m.get("manifest_sha256", "")
    c = m["counts"]
    if args.digest:
        # 摘要模式：清单全量留本地 runs 留痕目录（格式化后仍存续），总线只载计数+哈希绑定+顶层分布
        import collections
        top = collections.Counter(e["rel"].split("/")[0] for e in m["purge"])
        lines = [f"【ls-bus-format 留痕·摘要】target={m['target_dir']} total={c['total']} keep={c['keep']} purge={c['purge']}",
                 f"manifest_sha256={mhash}",
                 f"manifest_local={args.manifest}（全量清单含逐件 sha256，runs 留痕目录强制保留）",
                 "", "## purge 顶层目录分布（件数）"]
        lines += [f"- {k}: {v}" for k, v in top.most_common(30)]
    else:
        lines = [f"【ls-bus-format 留痕】target={m['target_dir']} total={c['total']} keep={c['keep']} purge={c['purge']}",
                 f"manifest_sha256={mhash}", "", "## purge 清单（sha256 前12）"]
        lines += [f"- {e['rel']} ({e['size']}B, {e['sha256'][:12]})" for e in m["purge"]]
        lines += ["", "## keep 清单（自我设定保留）", ]
        lines += [f"- {e['rel']}" for e in m["keep"]]
    payload = "\n".join(lines) + "\n"
    phash = hashlib.sha256(payload.encode()).hexdigest()
    esc = payload.replace("'", "''")
    seat = args.seat or "k3-govdoc-seat"
    sql = ("INSERT INTO public.cross_mode_channel (from_mode, to_mode, kind, payload_md, status, msg_hash)\n"
           f"VALUES ('{seat}', 'all', 'notice', '{esc}', 'sent', '{phash}')\n"
           "RETURNING id, from_mode, kind, status, msg_hash, length(payload_md) AS plen;\n")
    out = args.out or args.manifest.replace(".json", ".bus.sql")
    with open(out, "w", encoding="utf-8") as f:
        f.write(sql)
    print(json.dumps({"sql": out, "payload_sha256": phash, "plen": len(payload)},
                     ensure_ascii=False, indent=1))
    print("SQL 底稿已生成（脚本生成禁人工转录）。执行属写类动作，须当轮批准后经 execute_sql 落线并回读核验。")


def cmd_execute(args):
    with open(args.manifest, encoding="utf-8") as f:
        m = json.load(f)
    mhash = m.get("manifest_sha256", "")
    if not args.approve or args.approve != mhash[:16]:
        raise SystemExit(f"REFUSE: --approve 令牌须等于 manifest_sha256 前16（{mhash[:16]}）")
    import time
    target = resolve_target(m["target_dir"])
    extra = m.get("keep_patterns", [])[len(KEEP_PATTERNS):]
    prog = os.path.join(target, RUNS_DIRNAME, "progress.json")
    # 漂移重扫瘦身：keep 类不哈希（其哈希无判据用途），梯度让渡
    current = scan(target, extra, hash_keep=False, pace=args.pace,
                   pace_sleep=args.pace_sleep, progress_path=prog)
    cur_map = {e["rel"]: e["sha256"] for e in current}
    plan_map = {e["rel"]: e["sha256"] for e in m["purge"]}
    drift = [r for r in plan_map if cur_map.get(r) != plan_map[r]]
    keep_rels = {e["rel"] for e in m.get("keep", [])}
    # 死链无内容无哈希、生灭皆无害，不参与漂移判定（本轮未扫到的新死链留给下轮清扫）
    cur_dead = {e["rel"] for e in current if e["class"] == "deadlink"}
    new_purge = [r for r in cur_map
                 if r not in plan_map and r not in keep_rels and r not in cur_dead
                 and not is_keep(r, extra)]
    if drift or new_purge:
        parts = []
        if drift:
            parts.append("purge 变动/消失: " + "; ".join(drift[:5]))
        if new_purge:
            parts.append("新增 purge 类: " + "; ".join(new_purge[:5]))
        raise SystemExit("REFUSE: 清单漂移（" + " | ".join(parts) + "），须重新 scan")
    hook_dir = resolve_hook_dir(getattr(args, "hook_dir", None), target)
    hlog = os.path.join(target, RUNS_DIRNAME, "hooks.jsonl")
    ctx = {"manifest": args.manifest, "manifest_sha256": mhash,
           "counts": m["counts"], "runs_dir": os.path.join(target, RUNS_DIRNAME)}
    outcome, hpath = run_hook("pre_execute", hook_dir, target, ctx,
                              getattr(args, "hook_timeout", 30), hlog)
    if outcome.startswith("vetoed"):
        raise SystemExit(f"REFUSE: pre_execute 钩子否决（{hpath}）——删除未发生")
    deleted, kept_blocked, vanished = [], [], []
    total_purge = len(m["purge"])
    for i, e in enumerate(m["purge"]):
        rel = e["rel"]
        if is_keep(rel, extra):  # 双保险
            kept_blocked.append(rel)
            continue
        full = os.path.join(target, rel)
        if os.path.isfile(full) and not os.path.islink(full):
            try:
                os.remove(full)
                deleted.append(rel)
            except FileNotFoundError:
                vanished.append(rel)  # 漂移闸与删除间的第三方删走——记痕不崩溃
        if args.pace and (i + 1) % args.pace == 0:  # 梯度让渡：洪峰变缓流
            _write_progress(prog, "deleting", i + 1, total_purge)
            time.sleep(args.pace_sleep)
    deadlinks_cleaned = 0
    for e in m.get("deadlink", []):  # 死链清扫：unlink 链接本身（非目标），无内容风险
        full = os.path.join(target, e["rel"])
        try:
            if os.path.islink(full) and not os.path.exists(full):
                os.unlink(full)
                deadlinks_cleaned += 1
        except FileNotFoundError:
            pass
    pruned = 0
    if args.prune_empty_dirs:
        for dirpath, dirnames, filenames in os.walk(target, topdown=False):
            if os.path.basename(dirpath) == RUNS_DIRNAME:
                continue
            if not os.listdir(dirpath):
                os.rmdir(dirpath)
                pruned += 1
                if args.pace and pruned % args.pace == 0:
                    _write_progress(prog, "pruning", pruned, None)
                    time.sleep(args.pace_sleep)
    result = {"deleted": len(deleted), "blocked_by_keep_doublecheck": kept_blocked,
              "vanished_race": vanished,
              "deadlinks_cleaned": deadlinks_cleaned,
              "pruned_empty_dirs": pruned,
              "verify": "deleted files gone: " +
              str(all(not os.path.exists(os.path.join(target, r)) for r in deleted))}
    runs_dir = os.path.join(target, RUNS_DIRNAME)
    os.makedirs(runs_dir, exist_ok=True)
    rts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rpath = os.path.join(runs_dir, f"report_{rts}.json")
    try:
        with open(rpath, "w", encoding="utf-8") as f:
            json.dump({**result, "manifest": args.manifest, "manifest_sha256": mhash,
                       "ts_utc": rts}, f, ensure_ascii=False, indent=1, sort_keys=True)
    except OSError:
        print(f"WARN: report 写不入 {rpath}（审计痕可能丢失）", file=sys.stderr)
        rpath = None
    result["report"] = rpath
    ctx["detail"] = result
    run_hook("post_execute", hook_dir, target, ctx, getattr(args, "hook_timeout", 30), hlog)
    print(json.dumps(result, ensure_ascii=False, indent=1))


def main():
    ap = argparse.ArgumentParser(prog="ls_bus_format.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("scan")
    p1.add_argument("--target-dir", default="/mnt/agents/output")
    p1.add_argument("--keep-file", default=None, help="追加自我设定模式白名单（每行一个子串）")
    p1.add_argument("--hook-dir", default=None, help="钩子目录（须位于 target_dir 之外）")
    p1.add_argument("--hook-timeout", type=int, default=30)
    p1.add_argument("--pace", type=int, default=200, help="梯度：每 N 件让渡一次（0=关闭）")
    p1.add_argument("--pace-sleep", type=float, default=0.1, help="梯度：每次让渡秒数")
    p2 = sub.add_parser("bussql")
    p2.add_argument("--manifest", required=True)
    p2.add_argument("--seat", default="k3-govdoc-seat")
    p2.add_argument("--out", default=None)
    p2.add_argument("--digest", action="store_true",
                    help="摘要模式：总线只载计数+哈希绑定+顶层分布（全量清单留 runs 留痕目录）")
    p3 = sub.add_parser("execute")
    p3.add_argument("--manifest", required=True)
    p3.add_argument("--approve", required=True, help="manifest_sha256 前16")
    p3.add_argument("--prune-empty-dirs", action="store_true")
    p3.add_argument("--hook-dir", default=None, help="钩子目录（须位于 target_dir 之外）")
    p3.add_argument("--hook-timeout", type=int, default=30)
    p3.add_argument("--pace", type=int, default=200, help="梯度：每 N 件让渡一次（0=关闭）")
    p3.add_argument("--pace-sleep", type=float, default=0.1, help="梯度：每次让渡秒数")
    args = ap.parse_args()
    {"scan": cmd_scan, "bussql": cmd_bussql, "execute": cmd_execute}[args.cmd](args)


if __name__ == "__main__":
    main()
