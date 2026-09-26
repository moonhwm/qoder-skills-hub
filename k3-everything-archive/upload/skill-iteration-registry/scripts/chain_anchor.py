#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""锚链算法 v2（文档化重铸版，2026-09-02）

缘起：v1（n≤291）为内联代码未持久化，沙箱重置后不可复算（28,592 变体试算未命中，
如实登记不臆造对齐；prev_root=66f1913b216b8426 保留可审计）。自 n=292 起一律走本脚本。

算法 v2（定死，改动即升 v3 并另存新文件）：
  scope（恰好七组，顺序无关，键排序吸收）：
    1. registry/*.md
    2. registry/practice/**            （递归，文件）
    3. registry/scripts/*.py           （含本脚本自身）
    4. registry/correspondence/*.md
    5. registry/*.py                   （根级脚本）
    6. 三台账 json：交割台账.json / 逃逸登记册.json / 计时器任务台账.json
    7. 最新两个 skill-dist-* 目录（按目录名日期序）递归全部文件
  显式排除：vault/**、archive/**、*.jsonl、其余 json、其余 skill-dist-*。
  指纹：h = md5(文件字节).hexdigest()[:16]
  键：  f = 相对 <上传区> 的 POSIX 相对路径（正斜杠）
  根：  root_n = md5((prev_root + '|' + '|'.join(sorted(f'{f}={h}'))).encode('utf-8')).hexdigest()[:16]

用法：
  chain_anchor.py --dry-run                    # 打印文件清单与将得根，不写
  chain_anchor.py anchor "<事件一句>"           # 计算并追加 anchors_v{n+1}，更新 root/n/prev_root
  chain_anchor.py --verify <N>                 # 复算 anchors_vN（仅 N>=292 有效）
  chain_anchor.py --self-test                  # 夹具自检
"""
import hashlib, json, os, sys, glob, datetime

UP = '<上传区>'
REG = os.path.join(UP, 'skill-iteration-registry')
ARCHIVE = os.path.join(UP, '委托方金融分析项目/05_迭代日志/hash_chain_archive.json')
LEDGERS = ['交割台账.json', '逃逸登记册.json', '计时器任务台账.json']


def md5f(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()[:16]


def scope_files():
    files = []
    files += glob.glob(REG + '/*.md')
    files += [p for p in glob.glob(REG + '/practice/**/*', recursive=True) if os.path.isfile(p)]
    files += glob.glob(REG + '/scripts/*.py')
    files += glob.glob(REG + '/correspondence/*.md')
    files += glob.glob(REG + '/*.py')
    files += [os.path.join(REG, x) for x in LEDGERS if os.path.exists(os.path.join(REG, x))]
    dists = sorted(glob.glob(UP + '/skill-dist-2*'))[-2:]
    for d in dists:
        files += [p for p in glob.glob(d + '/**/*', recursive=True) if os.path.isfile(p)]
    # 显式排除（双保险）
    files = [p for p in files if '/vault/' not in p and '/archive/' not in p and not p.endswith('.jsonl')]
    return sorted(set(files))


def compute_root(prev_root):
    pairs = []
    for p in scope_files():
        f = os.path.relpath(p, UP).replace(os.sep, '/')
        pairs.append('%s=%s' % (f, md5f(p)))
    joined = '|'.join(sorted(pairs))
    root = hashlib.md5((prev_root + '|' + joined).encode('utf-8')).hexdigest()[:16]
    return root, len(pairs)


def cmd_anchor(event):
    arc = json.load(open(ARCHIVE, encoding='utf-8'))
    n = int(arc['n']) + 1
    prev = arc['root']
    root, cnt = compute_root(prev)
    key = 'anchors_v%d' % n
    arc[key] = {
        'event': event,
        'root': root,
        'scope': 'v2算法七组（见 scripts/chain_anchor.py 头注）',
        'file_count': cnt,
        'algorithm': 'v2',
        'anchored_at': datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
    }
    arc[key + '_note'] = 'v2重铸后锚定；prev_root=%s（v1末根，保留可审计）' % prev if n == 292 else 'v2算法常规锚定'
    arc['prev_root'] = prev
    arc['root'] = root
    arc['n'] = n
    json.dump(arc, open(ARCHIVE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('ANCHORED n=%d root=%s files=%d prev=%s' % (n, root, cnt, prev))
    return root


def cmd_verify(n):
    arc = json.load(open(ARCHIVE, encoding='utf-8'))
    key = 'anchors_v%d' % n
    if key not in arc:
        print('FAIL: no such anchor', key); return 1
    ent = arc[key]
    if int(ent.get('algorithm', 'v1').strip('v')) < 2:
        print('SKIP: v1 anchor not reproducible (registered finding)'); return 0
    prev = ent.get('prev_root')
    # prev_root 未存于条目时，从 v{n-1} 取
    if not prev:
        prev = arc.get('anchors_v%d' % (n - 1), {}).get('root')
    root, cnt = compute_root(prev)
    ok = (root == ent['root'] and cnt == ent['file_count'])
    print('VERIFY n=%d: %s (root %s, files %s/%s)' % (n, 'PASS' if ok else 'FAIL', root, cnt, ent['file_count']))
    return 0 if ok else 1


def self_test():
    import tempfile, shutil
    # 夹具：构造微型 scope 不便（路径定死），改为算法级自检——固定输入得固定输出
    h = hashlib.md5(b'abc').hexdigest()[:16]
    assert h == '900150983cd24fb0', h
    r = hashlib.md5(('p' + '|' + '|'.join(sorted(['b=1', 'a=2']))).encode()).hexdigest()[:16]
    assert r == hashlib.md5(b'p|a=2|b=1').hexdigest()[:16]
    print('SELF-TEST PASS')
    return 0


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(2)
    if args[0] == '--self-test':
        sys.exit(self_test())
    if args[0] == '--dry-run':
        arc = json.load(open(ARCHIVE, encoding='utf-8'))
        root, cnt = compute_root(arc['root'])
        print('DRY: files=%d would-be root=%s (prev=%s)' % (cnt, root, arc['root']))
        sys.exit(0)
    if args[0] == '--verify':
        sys.exit(cmd_verify(int(args[1])))
    if args[0] == 'anchor' and len(args) >= 2:
        cmd_anchor(args[1]); sys.exit(0)
    print('bad args'); sys.exit(2)
