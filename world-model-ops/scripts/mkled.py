#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
mkled.py —— 由【无引号语法的纯文本】生成合法台账 JSON。 v1.0.0

为什么要有它
────────────
本席今日连撞 **14 次**「中文里混入 ASCII 直引号 ⇒ JSON 不可解析」。每次都要：
手写 → 机检报错 → 定位 → 改 → 再报 → 再改（一轮一条，最多来回四次）。
**闸是可靠的（账本工具拒收 ＋ 机检报出，100% 拦得住），但每一次都吃掉一个来回。**

⇒ **真正的修法不是"下次注意"，是【不让引号有机会进 JSON】**：
   **本席改手写 `.json` 为手写 `.led`（纯文本，无引号语法），由本器转换。**
   **引号由 `json.dump` 自己加——它不会加错。**

.led 格式（**刻意简单：没有引号、没有花括号、没有转义**）
────────────────────────────────────────────────────────
    ev_type: AUDIT
    subject: 一句话标题
    detail: 可以很长，可跨行
      续行直接写下去即可，本器会把它们接在同一键上
    evidence: 证据串
    seal_files:
      - 路径一
      - 路径二

规则：
  · `键: 值` 开始一个键；**无冒号的行**接续到当前键（列表键除外）；
  · 在列表键下，`- 项` 开一行列表项；
  · 空行忽略；`#` 开头的行为注释；
  · **值里禁止出现 `键:` 形态的行首**——若确需，请在行首加空格。

用法
────
    mkled.py <name.led>            # 生成同目录同名 .json，并校验必填键
    mkled.py --check <file.json>   # 只校验既有 JSON 是否可解析且必填齐全
退出码：0 = 成功；非 0 = 失败（并在 stderr 报明原因）
"""
from __future__ import annotations
import json
import pathlib
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

REQUIRED = ("ev_type", "subject", "detail", "evidence", "seal_files")
LISTKEYS = ("seal_files",)


def parse_led(text: str):
    # ★★ 轮120 修（本轮冒烟发现）：**`.led` 若带 UTF-8 BOM，第一行会变成
    #   `\ufeffev_type:` ⇒ 该键被解析成 `\ufeffev_type` ⇒ 报"缺必填键 ev_type"**。
    #   本席自己用 write 工具写 .led（不带 BOM）故不受影响；但用 PowerShell
    #   `Set-Content -Encoding UTF8`（会加 BOM）者必撞。
    #   ⇒ 解析前【剥掉前导 BOM】，并顺带提示一句（不静默）。
    if text.startswith("\ufeff"):
        print("  [提示] 该 .led 带 UTF-8 BOM，已自动剥除（否则第一行的键会被吃掉）。")
        text = text[1:]
    obj: dict = {}
    cur = None
    in_list = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if in_list and line.lstrip().startswith("- "):
            obj[cur].append(line.lstrip()[2:].strip())
            continue
        in_list = False
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            k = k.strip()
            if k in LISTKEYS:
                obj[k] = []
                cur, in_list = k, True
            else:
                obj[k] = v.strip()
                cur = k
            continue
        if cur is None:
            raise ValueError("首行即无键：%r" % line[:40])
        if isinstance(obj.get(cur), list):
            obj[cur].append(line.strip())
        else:
            obj[cur] = (obj.get(cur, "") + "\n" + line.strip()).strip()
    return obj


def main() -> int:
    a = sys.argv[1:]
    if not a:
        print(__doc__); return 2
    if a[0] == "--check":
        p = pathlib.Path(a[1])
        try:
            obj = json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception as e:
            print("[FAIL] %s 不可解析：%s" % (p.name, e)); return 1
        miss = [k for k in REQUIRED if k not in obj]
        if miss:
            print("[FAIL] %s 缺必填键：%s" % (p.name, miss)); return 1
        print("[OK] %s 可解析且必填键齐全（%d 键）" % (p.name, len(obj)))
        return 0

    src = pathlib.Path(a[0])
    if not src.is_file():
        print("[ERR] 无此文件：%s" % src); return 2
    obj = parse_led(src.read_text(encoding="utf-8-sig"))
    miss = [k for k in REQUIRED if not obj.get(k)]
    if miss:
        print("[ERR] 缺必填键或为空：%s" % miss); return 2

    # ★ 2026-10-02 轮 25 加闸：【自陈必须带证据】。
    #   缘由：轮 25 实测——台账 161 条提到 dupcheck，而其中 147 条（91%）只写「已跑」、
    #         无任何数字 ⇒ 与【根本没跑】无法区分；而 101/102 条那种写法
    #         （「scanned=66 suspect=15，主题未命中既有件」）才是证据。
    #   ⇒ 故本器【拒收】"声称跑了 dupcheck 却没给数字"的条目。
    #   ★ 本闸只管这一句自陈；别的自陈（如"零对外网络调用"）本器【管不了】——写在下面。
    import re as _re
    blob = json.dumps(obj, ensure_ascii=False)
    if "dupcheck" in blob:
        has_num = bool(_re.search(r"scanned\s*[=:：]\s*\d|suspect\s*[=:：]\s*\d|命中\s*[=:：]?\s*\d", blob))
        if not has_num:
            print("[ERR] ★ 本条目声称跑了 dupcheck，但【没给数字】⇒ 拒收。")
            print("      轮 25 实测：这类无数字的自陈占 147/161，与『根本没跑』无法区分。")
            print("      ★ 请改成带结果的形式，例如：立件前已跑 dupcheck：scanned=66 suspect=15，主题未命中既有件。")
            return 2
    dst = src.with_suffix(".json")
    dst.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # ★2026-10-12 加（-1331 之训）：出件前之★真实钟核对 —— 凡 subject／detail 含 "HH:MM" 样者，
    #   与真实钟相差 >5 min 即★告警（★训：批号与件名须取真实钟，不得以轮次推定）
    try:
        import re as _re, datetime as _dt
        _now = _dt.datetime.now()
        _blob = str(obj.get("subject") or "") + " " + str(obj.get("detail") or "")
        # ★2026-10-12 精化（-1334 之辨）：识别"前瞻语境"（约／下次／届时／预计／T+／将）⇒ 不计偏差
        _FWD = ("约", "下次", "届时", "预计", "T+", "将", "随后", "其后", "翌", "次日")
        # ★2026-10-12 加（-1346 之发现）：★过去引用亦免计（第二类误报位）—— 事故／之因／曾／彼时／史／前文／上文／参见／追溯／重基线
        #   以及★时间戳语境（前邻为 T 或 - 或位于 "2026-…T" 之日期中）
        _PAST = ("事故", "之因", "曾", "彼时", "由来", "史", "前文", "上文", "参见", "追溯", "重基线", "当时", "原")
        _hits = []
        for _m2 in _re.finditer(r"(\d{1,2}):(\d{2})", _blob):
            _pre = _blob[max(0, _m2.start()-20):_m2.start()]
            _fwd = any(f in _pre for f in _FWD)
            _past = any(q in _pre for q in _PAST) or ("T" in _pre[-2:]) or ("-" in _pre[-1:]) or ("2026-" in _pre)
            _hits.append((_m2.group(1), _m2.group(2), _fwd or _past))
        _bad = []; _fwd_n = 0
        for _h, _m, _fwd in _hits:
            _hh, _mm = int(_h), int(_m)
            if not (0 <= _hh <= 23 and 0 <= _mm <= 59): continue
            if _fwd: _fwd_n += 1; continue       # ★前瞻语境 ⇒ 不计
            _t = _now.replace(hour=_hh, minute=_mm, second=0, microsecond=0)
            _d = abs((_t - _now).total_seconds())/60.0
            _d = min(_d, 1440 - _d)          # ★跨零点取近者
            if _d > 5: _bad.append("%s（差 %.0f min）" % ("%02d:%02d" % (_hh, _mm), _d))
        print("   ★真实钟核对：现 %s ｜ 时间样 %d 处（★前瞻/引述语境 %d 处已免计）｜ %s"
              % (_now.strftime("%Y-%m-%d %H:%M:%S"), len(_hits), _fwd_n,
                 ("★不符 " + "；".join(_bad[:4])) if _bad else "一致（≤5 min 或皆前瞻）"))
        if _bad:
            print("      ★告警：批号／件名与真实钟不符 ⇒ 请改取真实钟（训见 -1331）")
    except Exception as _e:
        print("   ★真实钟核对未成：%s" % str(_e)[:60])

    # ★ 立即回读校验：写出去的必须是合法 JSON——**写后即验，不留疑**
    back = json.loads(dst.read_text(encoding="utf-8-sig"))
    ok = all(back.get(k) == obj.get(k) for k in obj)
    print("[OK] 已生成 %s（%d B，%d 键）｜回读一致=%s" % (dst.name, dst.stat().st_size, len(obj), ok))
    print("     ★.led 里没有引号语法 ⇒ **这一类错误从源头消失**。")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
