#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""name_audit.py 音韵闸审计器（seat-naming-ops）

用法:
  python3 name_audit.py 谢如琢 任飞翰            # 自动拼音（需 pypinyin，多音字会提示人工定读）
  python3 name_audit.py --pinyin "xie4 ru2 zhuo2" 谢如琢   # 人工定读模式（零依赖，确定判读）
  python3 name_audit.py --json batch.json        # 批量: [{"name":"谢如琢","pinyin":"xie4 ru2 zhuo2"},...]
  python3 name_audit.py --surname-len 2 --pinyin "ou1 yang2 ru2 zhuo2" 欧阳如琢  # 复姓模式

判据（references/phonology-gate.md §1）：硬六 FAIL / 软五 NOTE。
退出码: 0=全部 PASS(含 NOTE)；1=存在 FAIL；2=参数/依赖错误。
"""
import sys, json, os

INITIALS = ["zh", "ch", "sh", "b", "p", "m", "f", "d", "t", "n", "l",
            "g", "k", "h", "j", "q", "x", "z", "c", "s", "r", "y", "w"]
ARTIC = {}
for _g, _s in [("唇", "bpmf"), ("舌尖中", "dtnl"), ("舌根", "gkh"), ("舌面", "jqx"),
               ("翘舌", ("zh", "ch", "sh", "r")), ("平舌", "zcs"), ("零", ("y", "w", ""))]:
    for _i in _s:
        ARTIC[_i] = _g
def _load_poly_warn():
    """POLY_WARN 外置（assets/polyphone-warn.json 存在即用之，否则内建默认；T4）"""
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "polyphone-warn.json")
    if os.path.exists(p):
        try:
            return set(json.load(open(p, encoding="utf-8"))["chars"])
        except Exception:
            pass
    return set("任曾覃单解查盖行长乐说缪重少柏惇沈车种繁华齐渐强宁兴朝尉令只")
POLY_WARN = _load_poly_warn()


def _load_compound():
    """复姓池加载（自动识别 surname_len；T2）"""
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "surnames-compound.json")
    if os.path.exists(p):
        try:
            return sorted((s["surname"] for s in json.load(open(p, encoding="utf-8"))), key=len, reverse=True)
        except Exception:
            pass
    return []
COMPOUND_SURNAMES = _load_compound()


def detect_surname_len(name, cli_len=None, entry_len=None):
    """优先级：条目字段 > 显式 CLI（含显式 1）> 复姓池自动识别 > 1。
    entry_len 经 main 入口校验（正整数），此处只判 None。"""
    if entry_len is not None:
        return entry_len
    if cli_len is not None:
        return cli_len
    for cs in COMPOUND_SURNAMES:
        if name.startswith(cs):
            return len(cs)
    return 1  # 常见多音字，自动模式下提示人工定读


def parse_pinyin(pinyin_str):
    """'xie4 ru2 zhuo2' -> [(initial, final, tone), ...]，ü 写作 v。"""
    out = []
    for syl in pinyin_str.strip().lower().replace("ü", "v").split():
        tone = 0
        if syl and syl[-1].isdigit():
            tone = int(syl[-1])
            syl = syl[:-1]
        ini = ""
        for cand in INITIALS:
            if syl.startswith(cand):
                ini = cand
                break
        out.append((ini, syl[len(ini):], tone))
    return out


def auto_pinyin(name):
    try:
        from pypinyin import pinyin, Style
    except ImportError:
        return None
    toks = pinyin(name, style=Style.TONE3, heteronym=False)
    return " ".join(t[0] for t in toks)


def audit(name, parsed, surname_len=1):
    """返回 (verdict, fails, notes)。parsed = parse_pinyin 输出。
    surname_len：姓的字数（单姓=1，复姓=2）。复姓时判据重映射——
    接合处=姓末字(idx surname_len-1)与名首字(idx surname_len)：
    R2/R4/R5a 作用于接合处，R3/N4 首尾=姓首字与名尾字，R5b/N1/N2 作用于名内两字。
    复姓内部二字不施任何判据（姓为既定单元，非命名选择）。"""
    n = len(parsed)
    if len(name) != n or n < 2:
        return ("FAIL", ["R0 字数与拼音音节数不符"], [])
    if surname_len < 1 or surname_len >= n:
        return ("FAIL", ["R0 姓长参数异常(surname_len=%d, n=%d)" % (surname_len, n)], [])
    j = surname_len - 1   # 接合姓字
    m1, m2 = surname_len, surname_len + 1  # 名首/名次
    inis = [p[0] for p in parsed]
    fins = [p[1] for p in parsed]
    tones = [p[2] for p in parsed]
    fails, notes = [], []
    if len(set(tones)) == 1:
        fails.append("R1 逐字声调全同(%s)" % "-".join(map(str, tones)))
    if fins[j] == fins[m1]:
        fails.append("R2 姓与名首字同韵母(%s)" % fins[j])
    degenerate = (surname_len == 1 and n == 2)  # 两字名：首尾即接合，R3 退化为 R4 不重复计
    if not degenerate and inis[0] == inis[-1] and inis[0] != "":
        fails.append("R3 首尾同声母回环(%s)" % inis[0])
    if inis[j] == inis[m1]:
        if inis[j] != "":
            fails.append("R4 姓与名首字双声(%s)" % inis[j])
        else:
            notes.append("N3 姓与名首字皆零声母(同组)")
    if tones[j] == 3 and tones[m1] == 3:
        fails.append("R5a 上声连读链(3-3)")
    if m2 < n and tones[m1] in (3, 4) and tones[m2] in (3, 4):  # 名内两字俱在方判（两字名不触发）
        fails.append("R5b 名内仄仄相连(%d-%d)" % (tones[m1], tones[m2]))
    if m2 < n and fins[m1] == fins[m2]:
        notes.append("N1 名内叠韵(%s，成例豁免)" % fins[m1])
    if m2 < n and inis[m1] == inis[m2] and inis[m1] != "":
        notes.append("N2 名内双声(%s，成例豁免)" % inis[m1])
    for a, b in ((j, m1),) + (((m1, m2),) if m2 < n else ()):
        if inis[a] != inis[b] and ARTIC.get(inis[a]) == ARTIC.get(inis[b]):
            notes.append("N3 相邻同组声母(%s/%s，%s)" % (inis[a] or "零", inis[b] or "零", ARTIC.get(inis[a])))
    if not degenerate and fins[0] == fins[-1]:  # 两字名：N4 退化为 R2 域不触发
        notes.append("N4 首尾同韵(%s)" % fins[0])
    notes.append("N5 末字%s声(%s)" % ("平" if tones[-1] in (1, 2) else "仄",
                                      "响亮取向" if tones[-1] in (1, 2) else "沉稳取向"))
    return (("FAIL" if fails else "PASS"), fails, notes)


def audit_one(name, pin=None, surname_len=None, entry_len=None):
    src = "条目字段" if entry_len is not None else ("CLI" if surname_len is not None else None)
    sl = detect_surname_len(name, surname_len, entry_len)
    if src is None and sl != 1:
        src = "复姓池自动识别"
    pin = pin or auto_pinyin(name)
    if pin is None:
        return (name, None, None, ["pypinyin 未安装且未给 --pinyin，无法定读；pip install pypinyin 或用人工定读模式"])
    warns = ["多音字「%s」建议人工定读" % c for c in name if c in POLY_WARN]
    verdict, fails, notes = audit(name, parse_pinyin(pin), surname_len=sl)
    if src:
        notes = ["姓长=%d（生效来源：%s）" % (sl, src)] + notes
    return (name, pin, verdict, fails + notes + warns if verdict == "FAIL" else notes + warns)


def report(name, pin, verdict, msgs):
    if pin is None:
        print("%s: ERROR %s" % (name, msgs[0]))
        return
    tag = "FAIL" if verdict == "FAIL" else "PASS"
    print("%s [%s] %s" % (name, pin, tag))
    for m in msgs:
        print("   - %s" % m)


def main(argv):
    args = argv[1:]
    strict_names, pins, batch = [], {}, None
    surname_len_cli = None
    i = 0
    while i < len(args):
        if args[i] in ("--pinyin", "--json", "--surname-len"):
            need = 2 if args[i] == "--pinyin" else 1
            if i + need >= len(args) or any(args[i + k].startswith("--") for k in range(1, need + 1)):
                sys.stderr.write("参数错误：%s 缺值（须跟 %d 参）\n" % (args[i], need))
                return 2
        if args[i] == "--pinyin":
            if i + 2 >= len(args) or args[i + 1].startswith("--") or args[i + 2].startswith("--"):
                sys.stderr.write("参数错误：--pinyin 须跟 <拼音串> <人名> 两参\n")
                return 2
            pins[args[i + 2]] = args[i + 1]
            strict_names.append(args[i + 2])
            i += 3
        elif args[i] == "--surname-len" and i + 1 < len(args):
            try:
                surname_len_cli = int(args[i + 1])
                if surname_len_cli < 1:
                    raise ValueError
            except ValueError:
                sys.stderr.write("参数错误：--surname-len 须为正整数\n")
                return 2
            i += 2
        elif args[i] == "--json" and i + 1 < len(args):
            batch = args[i + 1]
            i += 2
        else:
            strict_names.append(args[i])
            i += 1
    items = []
    if batch:
        try:
            with open(batch, encoding="utf-8") as f:
                batch_data = json.load(f)
            if not isinstance(batch_data, list):
                raise ValueError("顶层须为数组")
        except (OSError, ValueError, json.JSONDecodeError) as ex:
            sys.stderr.write("参数错误：--json 文件不可读或格式非法（%s）\n" % ex)
            return 2
        for e in batch_data:
            if not isinstance(e, dict) or not e.get("name"):
                sys.stderr.write("参数错误：batch 条目须为含 name 键的对象\n")
                return 2
            sl = e.get("surname_len")
            if sl is not None and (not isinstance(sl, int) or isinstance(sl, bool) or sl < 1):
                sys.stderr.write("参数错误：batch 条目 surname_len 须为正整数（name=%s）\n" % e.get("name"))
                return 2
            items.append((e["name"], e.get("pinyin"), sl))
    items = [(nm, pin if pin is not None else pins.get(nm), sl) for nm, pin, sl in items]
    seen_names = {x[0] for x in items}
    items += [(nm, pins.get(nm), None) for nm in strict_names if nm not in seen_names]
    if not items:
        print(__doc__)
        return 2
    any_fail = False
    for name, pin, entry_len in items:
        nm, pi, verdict, msgs = audit_one(name, pin, surname_len=surname_len_cli, entry_len=entry_len)
        report(nm, pi, verdict, msgs)
        if verdict == "FAIL" or pi is None:
            any_fail = True
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
