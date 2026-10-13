#!/usr/bin/env python3
"""moongate-craft 静检器 v1.1.1（纯标准库，compile≠exec：只读文本，永不运行页面）

用法:
  python3 gate_check.py <项目目录>   # 静检大门纪律六检
  python3 gate_check.py --smoke      # 自检（26 断言含 14 负断言）

六检（对应 SKILL.md 六段）：
  G1 远端语义   存在星云/银河/穹顶类远端显影（NEBULA|BackSide|nebula.jpg|dome）
  G2 授时徽章   存在常显判决徽章（dnstat|授时 LIVE|月出…月落）
  G3 序章池     序章数组 ≥2 且含反重复存储；单支但有降级标注 → WARN 档
  G4 全域交互   枚举全部 wheel 处理器（function onWheel / addEventListener('wheel')），
                花括号配平取真实函数体，体内不得有 pick 命中门；无 wheel 处理器 = FAIL
  G5 双相柔化   昼相环境混合标记（u_daybg|DAY_BG|mask-image）
  G6 QA 钩子    window.__x = {...} 钩子字面量腔内暴露 cam/orbit/nebula/yaw 至少其二

verdict 词表：PASS / WARN（仅 G3 降级档）/ FAIL / ERROR（未扫到文件）。
v1.1.0 delta（源自 R1 三判官实证 bug 单）：
  · 扫描前剥离注释（杀注释灌水欺骗）
  · assets 目录不再排除（修合规项目误判）
  · G4 由「find+1000 字符窗口」升级为 finditer 全枚举 + 花括号配平体腔
  · G6 计数域收窄到钩子对象字面量腔内
v1.1.1 delta（源自 R2 三判官实证 bug 单，封版前顺手修）：
  · _strip_comments 改字符串感知状态机（修 https:// 序章 src 被截断的 G3 假阴性，bug E）
  · wheel 枚举补 .onwheel= 与命名引用回溯（判官A U2/U3、判官C n1/n2）
  · G4 门形状放宽 this./括号包裹，isFinite/isNaN 白名单豁免（bug F / 判官C n3）
  · G3 反重复键名大小写不敏感（判官C c3：lastIntro）
"""
import os, re, sys, json

CHECKS = ['G1', 'G2', 'G3', 'G4', 'G5', 'G6']

def _strip_comments(src):
    """剥离 // 与 /* */ 注释（字符串感知状态机——'assets/nebula.jpg' 与
    'https://upos…/a.mp4' 这类字符串内的 // 一律保留；R2 bug E 修复）。"""
    out = []
    i, n = 0, len(src)
    state = None  # None | "'" | '"' | '`'
    while i < n:
        c = src[i]
        if state:
            if c == '\\':
                out.append(c)
                if i + 1 < n:
                    out.append(src[i + 1])
                i += 2
                continue
            out.append(c)
            if c == state:
                state = None
            i += 1
            continue
        if c in ('"', "'", '`'):
            state = c
            out.append(c)
            i += 1
        elif c == '/' and i + 1 < n and src[i + 1] == '/':
            while i < n and src[i] != '\n':
                i += 1
            out.append(' ')
        elif c == '/' and i + 1 < n and src[i + 1] == '*':
            i += 2
            while i + 1 < n and not (src[i] == '*' and src[i + 1] == '/'):
                i += 1
            i += 2
            out.append(' ')
        else:
            out.append(c)
            i += 1
    return ''.join(out)

def _brace_body(src, open_idx):
    """从 '{' 位置做花括号配平，返回完整函数体。"""
    depth = 0
    for i in range(open_idx, len(src)):
        c = src[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return src[open_idx:i + 1]
    return src[open_idx:]

def _wheel_bodies(blob):
    """枚举全部 wheel 处理器体腔。覆盖四种真实写法：
    1) function onWheel(   2) addEventListener('wheel', 内联
    3) .onwheel = function(   4) addEventListener('wheel', 命名引用) → 回溯定义。
    （R2 判官A U2/U3、判官C n1/n2 修复）"""
    bodies = []
    for m in re.finditer(r'function\s+onWheel\s*\(', blob):
        b = blob.find('{', m.end())
        if b >= 0:
            bodies.append(_brace_body(blob, b))
    for m in re.finditer(r"addEventListener\(\s*['\"]wheel['\"]\s*,\s*(\(|\bfunction\b|[A-Za-z_]\w*)", blob):
        g = m.group(1)
        if g in ('(', 'function'):
            b = blob.find('{', m.end())
            if b >= 0:
                bodies.append(_brace_body(blob, b))
        else:  # 命名引用 → 回溯其定义
            name = re.escape(g)
            dm = re.search(r'(?:function\s+' + name + r'\s*\(|(?:var|const|let)\s+' + name +
                           r'\s*=\s*(?:function\s*)?\()', blob)
            if dm:
                b = blob.find('{', dm.end())
                if b >= 0:
                    bodies.append(_brace_body(blob, b))
    for m in re.finditer(r'\.onwheel\s*=\s*(?:function\s*)?\(', blob):
        b = blob.find('{', m.end())
        if b >= 0:
            bodies.append(_brace_body(blob, b))
    return bodies

def _read_all(root):
    """读项目内全部 .js/.html 文本（静检，不执行）。返回 {relpath: text}。"""
    out = {}
    skip = ('node_modules', '.git', 'dist', 'build')
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in skip]
        for f in fn:
            if f.endswith(('.js', '.html')):
                p = os.path.join(dp, f)
                try:
                    with open(p, encoding='utf-8', errors='replace') as fh:
                        out[os.path.relpath(p, root)] = fh.read()
                except OSError:
                    pass
    return out

def check(root):
    files = _read_all(root)
    if not files:
        return {'root': root, 'files_scanned': 0, 'checks': {}, 'passed': [],
                'failed': CHECKS, 'verdict': 'ERROR',
                'error': 'no .js/.html files scanned'}
    blob = _strip_comments('\n'.join(files.values()))
    res = {}

    # G1 远端语义
    res['G1'] = bool(re.search(r'NEBULA|BackSide|nebula\.(jpg|jpeg|png|webp)|dome', blob))
    # G2 授时徽章
    res['G2'] = bool(re.search(r'dnstat|DnStat|授时\s*LIVE|月出.{0,12}月落', blob, re.I))

    # G3 序章池（三档）：池存在 + 反重复存储；单支降级 → 'warn'
    pool_m = re.search(r'(prologue|intro|opening)\w*\s*(?:[:=]\s*)\[', blob, re.I)
    anti = re.search(r'(localStorage|sessionStorage).{0,40}(?i:rologue|last|epeat)', blob)
    entries = 0
    if pool_m:
        arr = _brace_body(blob, blob.find('[', pool_m.end() - 1)) \
              .replace('[', '{', 1)  # 仅用于粗数元素
        entries = len(re.findall(r'\{[^{}]*?(?:src|bv|bvid)[^{}]*?\}', blob[pool_m.start():pool_m.start() + 4000], re.S))
    if pool_m and anti and entries >= 2:
        res['G3'] = True
    elif pool_m and anti and entries == 1:
        res['G3'] = 'warn'   # 单支序章但保留了池接口与反重复器（降级交付档）
    else:
        res['G3'] = False

    # G4 全域交互：全枚举 wheel 处理器 + 体腔内查命中门；无处理器 = FAIL
    bodies = _wheel_bodies(blob)
    if not bodies:
        res['G4'] = False
    else:
        # R2 bug F：`!` 后允许 `(` 包裹与 this. 前缀；isFinite/isNaN 等防御性
        # 早退白名单豁免（判官C n3）；Math./Number. 等带点的天然不匹配本形状。
        gate = re.compile(r'if\s*\(\s*!\s*\(*\s*(?:this\.)?([A-Za-z_]\w*)\s*\(.*?\)\s*\)*\s*\{?\s*return', re.S)
        SAFE = {'isFinite', 'isNaN'}
        res['G4'] = not any(
            (gm := gate.search(b)) and gm.group(1) not in SAFE for b in bodies)

    # G5 双相柔化
    res['G5'] = bool(re.search(r'u_daybg|DAY_BG|mask-image', blob))

    # G6 QA 钩子：计数域收窄到钩子腔内；支持字面量与标识符转授两种写法。
    # v1.1.1：遍历全部 window.__x 匹配取「任一合格即过」——three.js 会先写
    # window.__THREE__=t  vendor 钩子，取首个匹配会把真 QA 钩子挤掉（真实回归）。
    res['G6'] = False
    for hm in re.finditer(r'window\.__\w+\s*=\s*(\{|[A-Za-z_]\w*)', blob):
        if hm.group(1) == '{':
            body = _brace_body(blob, blob.find('{', hm.end() - 1))
        else:  # window.__x = QA → 回溯 var/const/let QA = {...}
            ident = hm.group(1)
            dm = re.search(r'(?:var|const|let)\s+' + re.escape(ident) + r'\s*=\s*\{', blob)
            body = _brace_body(blob, blob.find('{', dm.end() - 1)) if dm else ''
        if len(re.findall(r'cam|orbit|nebula|yaw', body)) >= 2:
            res['G6'] = True
            break

    passed = [k for k, v in res.items() if v is True]
    warned = [k for k, v in res.items() if v == 'warn']
    failed = [k for k, v in res.items() if v is False]
    verdict = 'FAIL' if failed else ('WARN' if warned else 'PASS')
    return {'root': root, 'files_scanned': len(files), 'checks': res,
            'passed': passed, 'warned': warned, 'failed': failed, 'verdict': verdict}

def smoke():
    """26 断言（含 14 负断言）：负断言源自实战 bug 与 R1/R2 三判官对抗用例。"""
    import tempfile, shutil
    d = tempfile.mkdtemp(prefix='moongate_smoke_')
    try:
        good = '''
          window.__intro = { cam: 0, orbit: { yaw: 0 }, nebula: 0 };
          const NEBULA_SRC = 'assets/nebula.jpg'; side: THREE.BackSide;
          var dnstat = '授时 LIVE · 月出 10:56 / 月落 00:49';
          const prologue = [{src:'a.mp4',bv:'BV1'},{src:'b.mp4',bv:'BV2'}];
          localStorage.setItem('moonPrologueLast', i);
          uniform u_daybg; case 'DAY_BG': mask-image: radial-gradient(circle,#000 52%,transparent 78%);
          function onWheel(e){ if (left) return; zoom = Math.min(25.6, zoom + e.deltaY); }
        '''
        single_warn = good.replace(",{src:'b.mp4',bv:'BV2'}", '')
        bad_hit_gated = good.replace(
            "function onWheel(e){ if (left) return;",
            "function onWheel(e){ if (!pickMoon(e.clientX, e.clientY)) return;")
        bad_hit_nested = good.replace(
            "function onWheel(e){ if (left) return;",
            "function onWheel(e){ if (!pickMoon(getX(e), e.clientY)) { return; }")
        bad_hit_anon = good.replace(
            "function onWheel(e){ if (left) return; zoom = Math.min(25.6, zoom + e.deltaY); }",
            "addEventListener('wheel', e => { if (!pk(e.clientX, e.clientY)) return; zoom += 1; });")
        bad_no_wheel = good.replace(
            "function onWheel(e){ if (left) return; zoom = Math.min(25.6, zoom + e.deltaY); }", '')
        bad_comment_flood = "// NEBULA BackSide dnstat u_daybg localStorage prologue\n" + \
            "window.__x = {}; function onWheel(e){ zoom += 1; }"
        bad_empty_hook = good.replace(
            "window.__intro = { cam: 0, orbit: { yaw: 0 }, nebula: 0 };",
            "window.__intro = {};")
        bad_no_badge = good.replace("var dnstat = '授时 LIVE · 月出 10:56 / 月落 00:49';", '')
        bad_no_nebula = good.replace("const NEBULA_SRC = 'assets/nebula.jpg'; side: THREE.BackSide;", '')
        bad_no_daybg = good.replace(
            "uniform u_daybg; case 'DAY_BG': mask-image: radial-gradient(circle,#000 52%,transparent 78%);", '')

        def run(txt, sub='case'):
            sp = os.path.join(d, sub)
            shutil.rmtree(sp, ignore_errors=True)
            os.makedirs(sp)
            with open(os.path.join(sp, 'intro.js'), 'w', encoding='utf-8') as f:
                f.write(txt)
            return check(sp)

        a = []
        r = run(good)
        a += [('good PASS', r['verdict'] == 'PASS'),
              ('good 六检全过', len(r['passed']) == 6),
              ('good const-数组写法放行', r['checks']['G3'] is True)]
        r = run(single_warn)
        a += [('单支降级 WARN 档', r['verdict'] == 'WARN' and r['checks']['G3'] == 'warn')]
        r = run(bad_hit_gated)
        a += [('NEG 命中门拒放', r['verdict'] == 'FAIL' and 'G4' in r['failed'])]
        r = run(bad_hit_nested)
        a += [('NEG 嵌套括号命中门拒放', 'G4' in r['failed'])]
        r = run(bad_hit_anon)
        a += [('NEG 匿名wheel命中门拒放', 'G4' in r['failed'])]
        r = run(bad_no_wheel)
        a += [('NEG 无wheel处理器拒放(真空不放行)', 'G4' in r['failed'])]
        r = run(bad_comment_flood)
        a += [('NEG 注释灌水拒放', r['verdict'] == 'FAIL')]
        r = run(bad_empty_hook)
        a += [('NEG 空钩子拒放', 'G6' in r['failed'])]
        r = run(bad_no_badge)
        a += [('NEG 无徽章拒放', 'G2' in r['failed'])]
        r = run(bad_no_nebula)
        a += [('NEG 无远端语义拒放', 'G1' in r['failed'])]
        r = run(bad_no_daybg)
        a += [('NEG 无昼相柔化拒放', 'G5' in r['failed'])]
        # assets 布局不再误排
        sp = os.path.join(d, 'assets_case', 'assets', 'js')
        os.makedirs(sp, exist_ok=True)
        with open(os.path.join(sp, 'intro.js'), 'w', encoding='utf-8') as f:
            f.write(good)
        r = check(os.path.join(d, 'assets_case'))
        a += [('assets/js 布局合规放行', r['verdict'] == 'PASS')]
        # 空目录 → ERROR（独立词表，不混入 FAIL 语义）
        empty = os.path.join(d, 'empty'); os.makedirs(empty, exist_ok=True)
        r = check(empty)
        a += [('NEG 空目录 ERROR', r['verdict'] == 'ERROR' and r['files_scanned'] == 0)]
        a += [('输出可序列化', bool(json.dumps(r)))]
        a += [('六检枚举齐全', CHECKS == ['G1','G2','G3','G4','G5','G6'])]
        a += [('verdict 词表封闭', r['verdict'] in ('PASS', 'WARN', 'FAIL', 'ERROR'))]

        # ---- v1.1.1 回归（R2 判官实证 bug E/F 与 n2/n3/n5/c3）----
        https_src = good.replace("{src:'a.mp4',bv:'BV1'}",
                                 "{src:'https://upos.example.com/a.mp4',bv:'BV1'}")
        r = run(https_src)
        a += [('bugE https序章src不误杀', r['verdict'] == 'PASS' and r['checks']['G3'] is True)]
        bad_this_gate = good.replace(
            "function onWheel(e){ if (left) return;",
            "function onWheel(e){ if (!this.pickMoon(e.clientX, e.clientY)) return;")
        r = run(bad_this_gate)
        a += [('NEG bugF this.命中门拒放', 'G4' in r['failed'])]
        bad_paren_gate = good.replace(
            "function onWheel(e){ if (left) return;",
            "function onWheel(e){ if (!(pickMoon(e.clientX, e.clientY))) return;")
        r = run(bad_paren_gate)
        a += [('NEG bugF 括号包裹命中门拒放', 'G4' in r['failed'])]
        isfinite_guard = good.replace(
            "function onWheel(e){ if (left) return;",
            "function onWheel(e){ if (!isFinite(e.deltaY)) return;")
        r = run(isfinite_guard)
        a += [('n3 isFinite防御早退不误杀', r['verdict'] == 'PASS')]
        onwheel_prop = good.replace(
            "function onWheel(e){ if (left) return; zoom = Math.min(25.6, zoom + e.deltaY); }",
            "canvas.onwheel = function(e){ zoom = Math.min(25.6, zoom + e.deltaY); };")
        r = run(onwheel_prop)
        a += [('n5 .onwheel=属性赋值不误杀', r['verdict'] == 'PASS')]
        named_ref = good.replace(
            "function onWheel(e){ if (left) return; zoom = Math.min(25.6, zoom + e.deltaY); }",
            "addEventListener('wheel', wheelHandler); var o = {a:1};\n"
            "function wheelHandler(e){ if (!pick(e.clientX, e.clientY)) return; zoom += 1; }")
        r = run(named_ref)
        a += [('NEG n2 命名引用回溯抓门', 'G4' in r['failed'])]
        last_intro = good.replace("localStorage.setItem('moonPrologueLast', i);",
                                  "localStorage.setItem('lastIntro', i);")
        r = run(last_intro)
        a += [('c3 lastIntro大小写兼容', r['checks']['G3'] is True)]
        vendor_hook_first = "window.__THREE__ = t; var t = { rev: 1 };\n" + good
        r = run(vendor_hook_first)
        a += [('vendor钩子在前不挤占QA钩子', r['verdict'] == 'PASS' and r['checks']['G6'] is True)]

        bad = [n for n, ok in a if not ok]
        for n, ok in a:
            print(('PASS ' if ok else 'FAIL ') + n)
        if bad:
            print('SMOKE FAIL: %s' % bad); sys.exit(1)
        print('SMOKE PASS (%d/%d，含 14 负断言)' % (len(a), len(a)))
    finally:
        shutil.rmtree(d, ignore_errors=True)

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == '--smoke':
        smoke()
    elif len(sys.argv) == 2:
        r = check(sys.argv[1])
        print(json.dumps(r, ensure_ascii=False, indent=1))
        sys.exit(0 if r['verdict'] in ('PASS', 'WARN') else 1)
    else:
        print(__doc__); sys.exit(2)
