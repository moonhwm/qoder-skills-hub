#!/usr/bin/env python3
"""test_notice_stamp.py — v1.8 notice_stamp.py 对抗修复回归：strip_legacy 回溯 P0
计时用例（F-B1/F-B2）、删除一致性、HTML 4KB 界、未闭合块语义（F-B3）、扩展名优先。

用法：python3 tests/test_notice_stamp.py
阈值约定（ reviewer_notes F-B1 复现矩阵的修复目标）：
  CLI 盖章+幂等重盖 30/50/100/5000 行连续 # 注释 .py 全部 <1s；
  进程内 strip_legacy 5000 行 <0.1s（实测 ~0.01ms 量级，阈值留足 CI 余量）；
  .tex 30 行 % 注释同验；畸形 .md 20 万行 <5s。
"""
import importlib.util, io, os, contextlib, subprocess, sys, tempfile, time

NS = os.path.join(os.path.dirname(__file__), "..", "scripts", "notice_stamp.py")
_spec = importlib.util.spec_from_file_location("notice_stamp", NS)
ns = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ns)

PASS, FAIL = 0, 0
FAILURES = []


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        FAILURES.append(f"{name}: {detail}")


def cli(path, tmpd):
    """CLI 幂等重盖一次，返回 (耗时秒, returncode, stderr)。"""
    t0 = time.perf_counter()
    p = subprocess.run([sys.executable, NS, "--file", path,
                        "--change-id", "CHG-20260824-T1", "--reason", "P1 计时回归",
                        "--audit-ref", "/tmp/audit.md", "--agent", "test",
                        "--changelog", os.path.join(tmpd, "CHANGELOG.md"),
                        "--k3-log", os.path.join(tmpd, "k3.jsonl")],
                       capture_output=True, text=True)
    return time.perf_counter() - t0, p.returncode, p.stderr


def strip(text, ext):
    """进程内 strip_legacy，返回 (耗时秒, 结果文本, 是否移除, stderr)。"""
    err = io.StringIO()
    t0 = time.perf_counter()
    with contextlib.redirect_stderr(err):
        out, removed = ns.strip_legacy(text, ext)
    return time.perf_counter() - t0, out, removed, err.getvalue()


def hash_block():
    body = ("change_id: CHG-20260824-X1\n", "date: 2026-08-24\n", "agent: t\n",
            "reason: P1 修复\n", "audit_ref: /a.md\n", "summary: s\n", "notice_to: x\n")
    return ("# AI_READER_NOTICE\n" + "".join("# " + l for l in body)
            + "# END_AI_READER_NOTICE\n\n")


def pct_block():
    return ("% AI_READER_NOTICE\n% change_id: C\n% date: 2026-08-24\n"
            "% END_AI_READER_NOTICE\n\n")


TMP = tempfile.mkdtemp()

# ============ F-B1 计时回归：合法块 + N 行连续 # 注释（a_after 实战形态） ============
for tag, N in (("T01", 30), ("T02", 50), ("T03", 100), ("T04", 5000)):
    path = os.path.join(TMP, f"f{N}.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(hash_block() + "".join(f"# 注释行 {i}\n" for i in range(N)) + "x = 1\n")
    t1, rc1, se1 = cli(path, TMP)   # 幂等重盖（块已存在 → strip + 前插）
    t2, rc2, se2 = cli(path, TMP)   # 再次重盖
    with open(path, encoding="utf-8") as f:
        n_begin = f.read().count("# AI_READER_NOTICE")
    check(f"{tag} HASH {N}行#注释 重盖两次 <1s 且块恰一次",
          t1 < 1 and t2 < 1 and rc1 == 0 and rc2 == 0 and n_begin == 1
          and "未闭合" not in se1 + se2,
          f"t1={t1:.3f} t2={t2:.3f} rc={rc1},{rc2} begin={n_begin}")

# 进程内 5000 行 strip <0.1s（P0 原为 O(2^N)，实测现 ~0.01ms）
txt5000 = hash_block() + "".join(f"# 注释行 {i}\n" for i in range(5000)) + "x = 1\n"
t, out, removed, _ = strip(txt5000, ".py")
check("T05 strip_legacy 5000行#注释 <0.1s 且删除正确",
      t < 0.1 and removed and out == "".join(f"# 注释行 {i}\n" for i in range(5000)) + "x = 1\n",
      f"t={t:.4f} removed={removed}")

# ============ F-B2 PCT 分支（.tex）对称用例 ============
ptex = os.path.join(TMP, "t30.tex")
with open(ptex, "w", encoding="utf-8") as f:
    f.write(pct_block() + "".join(f"% 注释 {i}\n" for i in range(30))
            + "\\documentclass{article}\n")
t1, rc1, _ = cli(ptex, TMP)
t2, rc2, _ = cli(ptex, TMP)
with open(ptex, encoding="utf-8") as f:
    n_begin = f.read().count("% AI_READER_NOTICE")
check("T06 PCT .tex 30行%注释 重盖两次 <1s 且块恰一次",
      t1 < 1 and t2 < 1 and rc1 == 0 and rc2 == 0 and n_begin == 1,
      f"t1={t1:.3f} t2={t2:.3f} rc={rc1},{rc2} begin={n_begin}")

# ============ 删除一致性：正常文件（合法旧块）strip 结果逐字节等于期望 ============
# （期望串同时与 v1.7 旧正则在同 fixture 上的产物逐字节一致，发布前已对拍）
cases = [
    ("T07 HASH块+shebang/coding",
     "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n" + hash_block() + "print(1)\n",
     ".py",
     "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\nprint(1)\n"),
    ("T08 PCT块", pct_block() + "\\documentclass{article}\n% c\n", ".tex",
     "\\documentclass{article}\n% c\n"),
    ("T09 HTML块", "<!-- AI_READER_NOTICE\nchange_id: C\ndate: 2026-08-24\n-->\n\n# 标题\n",
     ".md", "# 标题\n"),
    ("T10 HASH块+20行注释", hash_block() + "".join(f"# c{i}\n" for i in range(20)) + "x=1\n",
     ".py", "".join(f"# c{i}\n" for i in range(20)) + "x=1\n"),
]
for tag, src, ext, expect in cases:
    _, out, removed, se = strip(src, ext)
    check(f"{tag} strip 逐字节一致", removed and out == expect and "未闭合" not in se,
          f"removed={removed} out={out!r}")

# ============ F-B2 HTML 分支：畸形 .md 20 万行不挂起、不误删远处正文（4KB 界） ============
mal = ("<!-- AI_READER_NOTICE 旧格式\n"
       + "".join(f"正文第{i}节 -->\n" if i == 50000 else f"正文第{i}节\n"
                 for i in range(200000)))
t, out, removed, se = strip(mal, ".md")
check("T11 畸形.md 20万行 <5s 且内容零改动+WARNING（--> 在 4KB 界外）",
      t < 5 and not removed and out == mal and "未闭合" in se,
      f"t={t:.3f} removed={removed} changed={out != mal}")

# 4KB 界内闭合小块仍正常删除
small = "<!-- AI_READER_NOTICE\nchange_id: C\n-->\n\n# 正文\n"
_, out, removed, _ = strip(small, ".md")
check("T12 HTML 合法小块（4KB 界内）正常删除", removed and out == "# 正文\n",
      f"removed={removed} out={out!r}")

# ============ F-B3 未闭合旧块：WARNING + 内容零改动 ============
unclosed = "# AI_READER_NOTICE\n# change_id: X\n# 被截断\nx = 1\n"
_, out, removed, se = strip(unclosed, ".py")
check("T13 未闭合HASH块 零改动+WARNING「未闭合留痕块」",
      not removed and out == unclosed and "未闭合留痕块" in se and "人工核查" in se,
      f"removed={removed} se={se!r}")
_, out, removed, se = strip("% AI_READER_NOTICE\n% 截断\ntext\n", ".tex")
check("T14 未闭合PCT块 零改动+WARNING",
      not removed and "未闭合留痕块" in se, f"removed={removed} se={se!r}")

# CLI：未闭合旧块重盖 → rc=0、stderr WARNING、新块照常前插（旧残留待人工）
punc = os.path.join(TMP, "unclosed.py")
with open(punc, "w", encoding="utf-8") as f:
    f.write(unclosed)
t1, rc1, se1 = cli(punc, TMP)
with open(punc, encoding="utf-8") as f:
    stamped = f.read()
check("T15 未闭合块CLI重盖 rc=0+WARNING+新块前插（BEGIN=2 残留待人工）",
      rc1 == 0 and "未闭合留痕块" in se1 and stamped.startswith("# AI_READER_NOTICE")
      and stamped.count("# AI_READER_NOTICE") == 2 and "# 被截断" in stamped,
      f"rc={rc1} se={se1!r} begin={stamped.count('# AI_READER_NOTICE')}")

# ============ F-B2 扩展名优先：.py 跑 HASH 分支；HASH 未命中且确含 HTML 块才迁移 ============
pyhtml = '"""\n留痕: <!-- AI_READER_NOTICE\nchange_id: C\n-->\n"""\nx=1\n'
_, out, removed, _ = strip(pyhtml, ".py")
check("T16 .py 含闭合HTML块（HASH未命中）→ 迁移删除",
      removed and out == '"""\n留痕: """\nx=1\n', f"removed={removed} out={out!r}")
pyhash = hash_block() + "x=1\n"
_, out, removed, _ = strip(pyhash, ".py")
check("T17 .py HASH块经HASH分支删除", removed and out == "x=1\n",
      f"removed={removed} out={out!r}")

print(f"\n{PASS} passed / {PASS + FAIL} total")
if FAILURES:
    print("FAILURES:")
    for f_ in FAILURES:
        print("  -", f_)
    sys.exit(1)
print("ALL PASS")
