#!/usr/bin/env python3
"""corpus_map.py — 语料价值测绘：主题聚类 + 高相关筛选 + 归宿映射表。

输入：语料 JSONL（batch_*.jsonl 形态，字段 seq/url/title/topic_tags/abstract 等）。
用法：
  python3 corpus_map.py <语料目录> --tags Skills,Prompt,AI安全   # 高相关标签过滤
  python3 corpus_map.py <语料目录> --map 归宿映射.json           # 标签→归宿技能映射
  python3 corpus_map.py --smoke                                  # 离线自测
输出：Markdown 测绘表（stdout），含簇计数、逐条 seq/标题/标签/日期。
"""
import sys, os, json, glob, collections

def load_corpus(d):
    rows = []
    for f in sorted(glob.glob(os.path.join(d, '*.jsonl'))):
        for line in open(f, encoding='utf-8'):
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def map_rows(rows, key_tags, tag_map=None):
    sel = [r for r in rows if any(t in key_tags for t in r.get('topic_tags', []))]
    clusters = collections.Counter()
    lines = ['| seq | 标题 | 标签 | 日期 | 归宿 |', '|---|---|---|---|---|']
    for r in sel:
        tags = r.get('topic_tags', [])
        dest = ''
        if tag_map:
            dest = next((tag_map[t] for t in tags if t in tag_map), '（未映射）')
        for t in tags:
            if t in key_tags:
                clusters[t] += 1
        lines.append(f"| {r.get('seq','')} | {str(r.get('title',''))[:40]} | {'/'.join(tags)} | {r.get('publish_date')} | {dest} |")
    return sel, clusters, lines

def smoke():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        demo = [
            {"seq": 1, "title": "Skills 科普", "topic_tags": ["Skills"], "publish_date": "2026-01-01", "url": "u1"},
            {"seq": 2, "title": "产品评测", "topic_tags": ["产品评测"], "publish_date": None, "url": "u2"},
            {"seq": 3, "title": "信源筛选法", "topic_tags": ["信源", "AI安全"], "publish_date": "2026-02-01", "url": "u3"},
        ]
        with open(os.path.join(td, 'batch_1.jsonl'), 'w', encoding='utf-8') as f:
            for r in demo:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        rows = load_corpus(td)
        assert len(rows) == 3
        sel, clusters, lines = map_rows(rows, ['Skills', '信源'], {'Skills': 'mentor', '信源': 'source-semantics-sentinel'})
        assert len(sel) == 2 and clusters['Skills'] == 1 and clusters['信源'] == 1
        assert 'mentor' in ''.join(lines) and 'source-semantics-sentinel' in ''.join(lines)
        # 零命中路径
        sel2, c2, _ = map_rows(rows, ['不存在的标签'])
        assert len(sel2) == 0 and not c2
        print('[SMOKE OK] 聚类/映射/零命中三路径通过')

if __name__ == '__main__':
    if '--smoke' in sys.argv:
        smoke(); sys.exit(0)
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    d = sys.argv[1]
    tags = sys.argv[sys.argv.index('--tags') + 1].split(',') if '--tags' in sys.argv else []
    tag_map = None
    if '--map' in sys.argv:
        tag_map = json.load(open(sys.argv[sys.argv.index('--map') + 1], encoding='utf-8'))
    rows = load_corpus(d)
    sel, clusters, lines = map_rows(rows, tags, tag_map)
    print(f"全库 {len(rows)} 条，高相关 {len(sel)} 条\n")
    print('簇计数：' + json.dumps(clusters.most_common(), ensure_ascii=False) + '\n')
    print('\n'.join(lines))
