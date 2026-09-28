# -*- coding: utf-8 -*-
"""verify_edit.py v1.1.0 — 改必验闸：patch 落锤的确定性验证（skill-forge-pipeline v2.3 配套）。
用法：
  python verify_edit.py <文件> <必须存在的字符串> [--must-not <禁止存在的字符串>] [--test "<命令>"]
  python verify_edit.py --smoke
退出码：0=全过；1=断言失败（must/must-not/test 任一未过，或文件读不了）；2=用法错误（参数缺失、未知参数、空 must/空 must-not）。
纪律：宣称修复前必须跑本闸并引用输出原文；静态断言（must/must-not）有失败时不执行 --test。
CLI 契约（exit 0/1/2）专用，勿 import 调用（GLM-B1 文档化采纳——代码契约不变）。
--smoke：自构造临时夹具跑负断言套件（空 must 必败、must-not 命中必败、未知参数必败、
静态失败后 --test 未被执行、真阳性 PASS），全部符合预期则 PASS 收尾。
"""
import argparse
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

TEST_TIMEOUT = 60  # 秒


def build_parser():
    p = argparse.ArgumentParser(
        prog="verify_edit.py",
        description="改必验闸：patch 落锤的确定性验证。退出码 0=全过/1=断言失败/2=用法错误。",
    )
    p.add_argument("file", help="目标文件")
    p.add_argument("must", help="必须存在的字符串（拒绝空串）")
    p.add_argument("--must-not", dest="must_not", default=None,
                   help="禁止存在的字符串（拒绝空串）")
    p.add_argument("--test", dest="test", default=None,
                   help="静态断言全过后执行的自检命令（shlex 切分，shell=False，timeout=60s）")
    return p


def run_verify(argv):
    """主验证流程。返回退出码。"""
    args = build_parser().parse_args(argv)  # 未知参数/缺参数由 argparse 报错并 exit 2

    # 空断言闸门：空串 must 必败（空串恒为子串，空过等于没验）
    if args.must == "":
        print("FAIL: 用法错误——must 为空串（空断言闸门拒绝空过）", file=sys.stderr)
        return 2
    if args.must_not is not None and args.must_not == "":
        print("FAIL: 用法错误——must-not 为空串（空断言闸门拒绝空过）", file=sys.stderr)
        return 2

    fp = Path(args.file)
    try:
        content = fp.read_text(encoding="utf-8")
    except Exception as e:
        print(f"FAIL: 目标文件读取失败: {fp} ({type(e).__name__}: {e})", file=sys.stderr)
        return 1

    # 静态断言（must / must-not）
    fails = []
    if args.must not in content:
        fails.append(f"must-exist 未命中: {args.must[:60]!r}")
    if args.must_not is not None and args.must_not in content:
        fails.append(f"must-not 仍存在: {args.must_not[:60]!r}")

    # 静态断言有失败 → 不执行 --test（防止在已破状态上跑副作用命令）
    if fails:
        for f in fails:
            print("FAIL:", f)
        if args.test is not None:
            print("FAIL: 静态断言未过，--test 未执行")
        return 1

    # 动态自检：shlex.split + shell=False + timeout=60 + stdin=DEVNULL
    if args.test is not None:
        try:
            r = subprocess.run(
                shlex.split(args.test),
                shell=False,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=TEST_TIMEOUT,
                stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired:
            print(f"FAIL: test 超时（>{TEST_TIMEOUT}s）: {args.test[:60]!r}")
            return 1
        except Exception as e:
            print(f"FAIL: test 启动失败: {type(e).__name__}: {e}")
            return 1
        if r.returncode != 0:
            print(f"FAIL: test 退出码 {r.returncode}: {(r.stderr or r.stdout)[-200:]}")
            return 1
        print("test PASS:", (r.stdout.strip().splitlines() or [""])[-1][:100])

    print("verify_edit PASS:", fp.name)
    return 0


def _expect(case, got, want_codes):
    ok = got in want_codes
    print(f"smoke[{case}] exit={got} 预期={sorted(want_codes)} -> {'OK' if ok else 'NG'}")
    return ok


def smoke():
    """负断言套件：全部用例符合预期才 PASS。"""
    self_py = str(Path(__file__).resolve())
    results = []
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        fixture = tdp / "fixture.txt"
        fixture.write_text("hello world\n", encoding="utf-8")
        marker = tdp / "marker.txt"  # --test 副作用标记：出现即说明 test 被误执行

        def run(*argv):
            return subprocess.run(
                [sys.executable, self_py, *argv],
                capture_output=True, encoding="utf-8", errors="replace",
                timeout=TEST_TIMEOUT, stdin=subprocess.DEVNULL,
            ).returncode

        # 1. 空 must 必败（用法错误 exit 2）
        results.append(_expect("空must必败", run(str(fixture), ""), {2}))
        # 2. must-not 命中必败（断言失败 exit 1）
        results.append(_expect("must-not命中必败",
                               run(str(fixture), "hello", "--must-not", "world"), {1}))
        # 3. 未知参数必败（argparse exit 2）
        results.append(_expect("未知参数必败",
                               run(str(fixture), "hello", "--bogus", "x"), {2}))
        # 4. 静态失败后 --test 未被执行（标记文件断言）
        code = run(str(fixture), "不存在的新串",
                   "--test", f'{shlex.quote(sys.executable)} -c "import pathlib;pathlib.Path(r\'{marker}\').write_text(\'x\')"')
        side_effect_free = not marker.exists()
        print(f"smoke[静态失败后--test未执行] exit={code} 标记文件未生成={side_effect_free} "
              f"-> {'OK' if code == 1 and side_effect_free else 'NG'}")
        results.append(code == 1 and side_effect_free)
        # 5. 真阳性 PASS（静态过 + test 过 → exit 0）
        results.append(_expect("真阳性PASS",
                               run(str(fixture), "hello", "--must-not", "旧串",
                                   "--test", f'{shlex.quote(sys.executable)} -c "print(\'ok\')"'), {0}))

    passed = sum(results)
    total = len(results)
    if passed == total:
        print(f"verify_edit --smoke PASS ({passed}/{total} 用例符合预期)")
        return 0
    print(f"verify_edit --smoke FAIL ({passed}/{total} 用例符合预期)")
    return 1


def main():
    argv = sys.argv[1:]
    if argv and argv[0] == "--smoke":
        if len(argv) > 1:
            print("FAIL: 用法错误——--smoke 不接受其他参数", file=sys.stderr)
            sys.exit(2)
        sys.exit(smoke())
    sys.exit(run_verify(argv))


if __name__ == "__main__":
    main()
