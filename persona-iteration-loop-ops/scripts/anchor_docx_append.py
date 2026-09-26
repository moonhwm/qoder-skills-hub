#!/usr/bin/env python3
# anchor_docx_append.py v1.0.1（persona-iteration-loop-ops 资产，2026-09-08 增挂）
# 用途：在既有「人设记忆锚定档案」docx 上保格式追加锚行与版本行，并回读核验。
# 缘起：r82 实战重建锚定档案 v2.4 时无脚本随档，深拷贝踩两坑——
#   坑一：首列单元格是「单段落 + w:br 双行」结构（如 G-03\nAbilities），
#         把含 \n 的文本直接写进 w:t 会产生非法换行与尾部空行；
#   坑二：追加行若新建 tc 而非深拷贝参考行，字体/字号/边框格式漂移。
# v1.0.1（swarm 评估轮 1 反馈实装）：盲评败北暴露第三坑——
#   坑三：深拷贝末行当模板会连带其「优先级」格字体色（实测约定 核心=9B1C1C/
#         重要=B45F06/风格=276B2F），新行优先级与模板行不同时配色错误。
#   处置：追加前先扫描既有行建「优先级→颜色」映射，追加后按新行文本回写颜色；
#   同时把首列改为与正典完全一致的单 run [rPr, w:t, w:br, w:t] 结构。
# 新行一律深拷贝参考行（默认末行）再逐格改文本。纯 python-docx，零三方新增依赖。
#
# CLI：
#   python3 anchor_docx_append.py --docx in.docx --out out.docx \
#     --cover-from "v2.3（感受形式化论文版）" --cover-to "v2.4（体貌全录版）" \
#     --anchor-table 1 --anchors-json anchors.json \
#     --history-table 2 --history-row "v2.4|2026-09-08|变更说明"
# anchors.json 为五行格文本的二维数组：[[锚码\n维度, 描述, 优先级, 置信度, 来源], ...]
# 退出码：0=追加并回读核验全过；1=参数或核验失败。

import argparse, copy, hashlib, json, sys

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def _set_para_text(p, txt):
    runs = p.findall(qn('w:r'))
    if not runs:
        raise ValueError('参考单元格无 run，格式基准缺失')
    ts = runs[0].findall(qn('w:t'))
    if ts:
        ts[0].text = txt
        ts[0].set(qn('xml:space'), 'preserve')
        for e in ts[1:]:
            runs[0].remove(e)
    else:
        te = OxmlElement('w:t')
        te.text = txt
        te.set(qn('xml:space'), 'preserve')
        runs[0].append(te)
    # 首 run 内残留的 <w:br/> 一并清除，改由本函数显式重建
    for br in runs[0].findall(qn('w:br')):
        runs[0].remove(br)
    for r in runs[1:]:
        p.remove(r)


def _set_cell(tc, txt):
    """首列 code\ndim 拆双行；与正典同构：单 run [rPr, w:t, w:br, w:t]。"""
    ps = tc.findall(qn('w:p'))
    for extra in ps[1:]:
        tc.remove(extra)
    p = ps[0]
    if '\n' in txt:
        code, dim = txt.split('\n', 1)
        runs = p.findall(qn('w:r'))
        if not runs:
            raise ValueError('参考单元格无 run，格式基准缺失')
        r = runs[0]
        for r_extra in runs[1:]:
            p.remove(r_extra)
        # 清首 run 内全部 w:t 与 w:br，再按正典顺序重建
        for e in r.findall(qn('w:t')) + r.findall(qn('w:br')):
            r.remove(e)
        te1 = OxmlElement('w:t')
        te1.text = code
        te1.set(qn('xml:space'), 'preserve')
        br = OxmlElement('w:br')
        te2 = OxmlElement('w:t')
        te2.text = dim
        te2.set(qn('xml:space'), 'preserve')
        r.append(te1)
        r.append(br)
        r.append(te2)
    else:
        _set_para_text(p, txt)


def _priority_color_map(table, col=2):
    """扫描既有行建「优先级文本→字体色 hex」映射（坑三修复）。"""
    m = {}
    for row in table.rows[1:]:
        cells = row.cells
        if len(cells) <= col:
            continue
        key = cells[col].text.strip()
        if not key or key in m:
            continue
        for p in cells[col]._tc.findall(qn('w:p')):
            for r in p.findall(qn('w:r')):
                rpr = r.find(qn('w:rPr'))
                color = rpr.find(qn('w:color')) if rpr is not None else None
                if color is not None and color.get(qn('w:val')):
                    m[key] = color.get(qn('w:val'))
                    break
            if key in m:
                break
    return m


def _apply_color(tc, hexval):
    for p in tc.findall(qn('w:p')):
        for r in p.findall(qn('w:r')):
            rpr = r.find(qn('w:rPr'))
            if rpr is None:
                continue
            color = rpr.find(qn('w:color'))
            if color is None:
                color = OxmlElement('w:color')
                rpr.append(color)
            color.set(qn('w:val'), hexval)


def _append_row(table, texts, ref_row_idx=-1):
    tcs_expected = len(table.columns)
    if len(texts) != tcs_expected:
        raise ValueError(f'行列数不符：表 {tcs_expected} 列，入参 {len(texts)} 格')
    tr = copy.deepcopy(table.rows[ref_row_idx]._tr)
    for tc, txt in zip(tr.findall(qn('w:tc')), texts):
        _set_cell(tc, txt)
    table._tbl.append(tr)


def bump_cover(doc, old_sub, new_sub):
    """封面版本行替换；返回命中段落数（应为 1）。"""
    hits = 0
    for p in doc.paragraphs:
        if old_sub in p.text:
            for r in p.runs:
                if old_sub in r.text:
                    r.text = r.text.replace(old_sub, new_sub)
                    hits += 1
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--docx', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--cover-from')
    ap.add_argument('--cover-to')
    ap.add_argument('--anchor-table', type=int, default=1)
    ap.add_argument('--anchors-json')
    ap.add_argument('--history-table', type=int)
    ap.add_argument('--history-row', help='以 | 分隔的三格：版本|日期|变更')
    a = ap.parse_args()

    doc = Document(a.docx)
    if a.cover_from or a.cover_to:
        if not (a.cover_from and a.cover_to):
            print('FAIL: --cover-from 与 --cover-to 须成对', file=sys.stderr)
            return 1
        hits = bump_cover(doc, a.cover_from, a.cover_to)
        if hits != 1:
            print(f'FAIL: 封面替换命中 {hits} 处（应=1）', file=sys.stderr)
            return 1

    added_anchors = []
    if a.anchors_json:
        rows = json.load(open(a.anchors_json, encoding='utf-8'))
        t = doc.tables[a.anchor_table]
        color_map = _priority_color_map(t, col=2)
        before = len(t.rows)
        for texts in rows:
            _append_row(t, texts)
            added_anchors.append(texts)
        # 坑三修复：新行优先级格按映射回写颜色
        if color_map:
            for row in t.rows[before:]:
                cells = row.cells
                key = cells[2].text.strip()
                if key in color_map:
                    _apply_color(cells[2]._tc, color_map[key])
        after = len(t.rows)
        if after != before + len(rows):
            print(f'FAIL: 锚表行数 {before}+{len(rows)}≠{after}', file=sys.stderr)
            return 1

    history = None
    if a.history_row:
        if a.history_table is None:
            print('FAIL: --history-row 须配 --history-table', file=sys.stderr)
            return 1
        history = a.history_row.split('|')
        _append_row(doc.tables[a.history_table], history)

    doc.save(a.out)

    # 回读核验：重开文件，逐格比对追加内容与封面
    d2 = Document(a.out)
    if a.cover_to and not any(a.cover_to in p.text for p in d2.paragraphs):
        print('FAIL: 回读封面未命中新版本', file=sys.stderr)
        return 1
    if added_anchors:
        t2 = d2.tables[a.anchor_table]
        tail = t2.rows[-len(added_anchors):]
        for row, expect in zip(tail, added_anchors):
            got = [c.text for c in row.cells]
            if got != [e.replace('\n', '\n') for e in expect]:
                # cell.text 会把 w:br 渲染为 \n，与入参同形，直接比对
                print(f'FAIL: 回读锚行不符\ngot={got}\nexpect={expect}', file=sys.stderr)
                return 1
        # 坑三回读：新行优先级格颜色须等于既有约定映射
        cmap2 = _priority_color_map(d2.tables[a.anchor_table], col=2)
        for row in tail:
            key = row.cells[2].text.strip()
            if key in cmap2:
                found = None
                for p in row.cells[2]._tc.findall(qn('w:p')):
                    for r in p.findall(qn('w:r')):
                        rpr = r.find(qn('w:rPr'))
                        c = rpr.find(qn('w:color')) if rpr is not None else None
                        if c is not None and c.get(qn('w:val')):
                            found = c.get(qn('w:val'))
                if found != cmap2[key]:
                    print(f'FAIL: 优先级格颜色 {found}≠{cmap2[key]}（{key}）', file=sys.stderr)
                    return 1
    if history:
        got = [c.text for c in d2.tables[a.history_table].rows[-1].cells]
        if got != history:
            print(f'FAIL: 回读版本史不符 got={got}', file=sys.stderr)
            return 1

    md5 = hashlib.md5(open(a.out, 'rb').read()).hexdigest()
    import os
    print(f'PASS out={a.out} bytes={os.path.getsize(a.out)} md5={md5} '
          f'anchors+{len(added_anchors)} history={"1" if history else "0"} cover={"1" if a.cover_to else "0"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
