#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""registry_search.py v0.1.0 — 注册处知识库检索引擎（2026-09-09 创刊）
本地化铁律：只读注册处，零写零出域。中文按 bigram 切词，英文按单词。
用法：
  registry_search.py build [--root 注册处路径]            # 建索引（落 .rk_index.json）
  registry_search.py query "<词1 词2>" [--top 10] [--root 路径]   # 全文检索
  registry_search.py round <N> [--root 路径]              # 锚链 round N 原文调阅
  registry_search.py sections [--root 路径]               # INDEX.md 分区目录
  registry_search.py --self-test                          # 五夹具自检
"""
import json, os, re, sys, math, hashlib

DEFAULT_ROOT = '/mnt/agents/upload/skill-iteration-registry'
INDEX_FILE = '.rk_index.json'
SCAN_EXT = ('.md', '.json', '.jsonl', '.txt')
SKIP_DIRS = {'vault', 'skill-work', '__pycache__', '.git'}  # vault 永不入索引（凭证铁律）
SKIP_FILES = {INDEX_FILE}
MAX_FILE_BYTES = 2_000_000

def tokenize(text):
    toks = []
    for seg in re.findall(r'[一-鿿]+|[A-Za-z0-9_\-\.]+', text):
        if re.match(r'^[一-鿿]', seg):
            if len(seg) == 1:
                toks.append(seg)
            else:
                toks.extend(seg[i:i + 2] for i in range(len(seg) - 1))
        else:
            toks.append(seg.lower())
    return toks

def iter_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn in SKIP_FILES or not fn.endswith(SCAN_EXT):
                continue
            p = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(p) > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            yield p

def build(root=DEFAULT_ROOT):
    docs = {}
    for p in iter_files(root):
        try:
            text = open(p, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        rel = os.path.relpath(p, root)
        docs[rel] = {'tokens': tokenize(text),
                     'head': re.sub(r'\s+', ' ', text[:200]).strip(),
                     'md5': hashlib.md5(text.encode()).hexdigest()[:16],
                     'size': len(text)}
    df = {}
    for rel, d in docs.items():
        for t in set(d['tokens']):
            df[t] = df.get(t, 0) + 1
    idx = {'root': os.path.abspath(root), 'n_docs': len(docs), 'df': df,
           'docs': {rel: {'head': d['head'], 'md5': d['md5'], 'size': d['size'],
                          'tokens': d['tokens']} for rel, d in docs.items()}}
    ipath = os.path.join(root, INDEX_FILE)
    # 索引落盘属写动作：仅写隐藏索引文件，不改任何被索引件
    open(ipath, 'w', encoding='utf-8').write(json.dumps(idx, ensure_ascii=False))
    return idx

def load(root=DEFAULT_ROOT):
    ipath = os.path.join(root, INDEX_FILE)
    if not os.path.exists(ipath):
        return build(root)
    try:
        return json.load(open(ipath, encoding='utf-8'))
    except Exception:
        return build(root)

def query(q, top=10, root=DEFAULT_ROOT):
    idx = load(root)
    qtoks = tokenize(q)
    if not qtoks:
        return []
    n = max(idx['n_docs'], 1)
    df = idx['df']
    scores = {}
    for rel, d in idx['docs'].items():
        tf = {}
        for t in d['tokens']:
            tf[t] = tf.get(t, 0) + 1
        s = 0.0
        hit = []
        for t in qtoks:
            if t in tf:
                idf = math.log((n + 1) / (df.get(t, 0) + 0.5)) + 1
                s += (1 + math.log(tf[t])) * idf
                hit.append(t)
        if s > 0:
            scores[rel] = (round(s, 3), hit, d['head'])
    ranked = sorted(scores.items(), key=lambda kv: -kv[1][0])[:top]
    return [{'file': rel, 'score': v[0], 'hits': v[1], 'head': v[2]}
            for rel, v in ranked]

def round_lookup(n, root=DEFAULT_ROOT):
    pl = os.path.join(root, 'playlog.jsonl')
    if not os.path.exists(pl):
        return {'error': 'playlog_missing'}
    for line in open(pl, encoding='utf-8', errors='replace'):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get('round') == n:
            return rec
    return {'error': 'round_not_found', 'round': n}

def sections(root=DEFAULT_ROOT):
    ip = os.path.join(root, 'INDEX.md')
    if not os.path.exists(ip):
        return []
    return [l.strip() for l in open(ip, encoding='utf-8', errors='replace')
            if l.startswith('#')]

# ---------- self-test ----------
def self_test():
    import tempfile, shutil
    ok = []
    td = tempfile.mkdtemp()
    try:
        open(os.path.join(td, '投标纪律.md'), 'w', encoding='utf-8').write(
            '# 投标评分博弈\n偏差率扣分公式与围标禁令。')
        open(os.path.join(td, '音视频.md'), 'w', encoding='utf-8').write(
            '# 音视频转写\n低置信段存疑禁猜读。')
        open(os.path.join(td, 'playlog.jsonl'), 'w', encoding='utf-8').write(
            json.dumps({'round': 1, 'note': '测试锚', 'msg_hash': 'abc'}) + '\n')
        os.makedirs(os.path.join(td, 'vault'))
        open(os.path.join(td, 'vault', 'secret.key'), 'w').write('x')
        idx = build(td)
        ok.append(('F1 build_index', idx['n_docs'] == 3))
        r = query('投标 偏差率', root=td)
        ok.append(('F2 query_hit', len(r) >= 1 and r[0]['file'] == '投标纪律.md'))
        r2 = query('围标', root=td)
        ok.append(('F3 partial_hit', len(r2) == 1))
        ok.append(('F4 vault_excluded', all('vault' not in x['file'] for x in query('x', root=td))))
        rec = round_lookup(1, root=td)
        ok.append(('F5 round_lookup', rec.get('note') == '测试锚'))
    finally:
        shutil.rmtree(td, ignore_errors=True)
    for name, v in ok:
        print('%s %s' % ('PASS' if v else 'FAIL', name))
    allpass = all(v for _, v in ok)
    print('SELF-TEST', 'PASS' if allpass else 'FAIL')
    return 0 if allpass else 1

def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__); return 2
    root = DEFAULT_ROOT
    if '--root' in argv:
        root = argv[argv.index('--root') + 1]
    cmd = argv[0]
    if cmd == '--self-test':
        return self_test()
    if cmd == 'build':
        idx = build(root)
        print(json.dumps({'built': idx['n_docs'], 'root': idx['root']},
                         ensure_ascii=False)); return 0
    if cmd == 'query' and len(argv) >= 2:
        top = 10
        if '--top' in argv:
            top = int(argv[argv.index('--top') + 1])
        print(json.dumps(query(argv[1], top, root), ensure_ascii=False, indent=1))
        return 0
    if cmd == 'round' and len(argv) == 2:
        print(json.dumps(round_lookup(int(argv[1]), root),
                         ensure_ascii=False, indent=1)); return 0
    if cmd == 'sections':
        print('\n'.join(sections(root))); return 0
    print('bad args'); print(__doc__); return 2

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
