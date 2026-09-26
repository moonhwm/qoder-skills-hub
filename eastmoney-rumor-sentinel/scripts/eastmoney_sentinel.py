#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""eastmoney_sentinel.py — 东财传闻哨兵采集判级器 v2.1.0

谱系：guba_scan.py v1.0（2026-09-05 实测固化：股吧列表页纯 HTTP 直读）
      → v2.0 技能化（观察名单/判级/去重/白话报告）
      → v2.2.0 全量正文（2026-09-09 spike 实证：帖页内嵌 post_article JSON 可直解，
        含正文/发布时间/阅读数/评论数/post_guba 权威标的；财富号 //caifuhao 链接为
        异构站，本版不抓，标 note 跳过）。正文抓取 v2.2.0 起**全量穷举**（机主令：重大决策沉没/机会成本高，三档皆抓）；跨股吧标的=post_guba 权威字段 vs 列表吧代码不一致即 cross_flag。

用法：
  python3 eastmoney_sentinel.py [--codes 300059,600030] [--tag 标签] [--out 采集目录] [--report 报告md]
  python3 eastmoney_sentinel.py --self-test   # 四夹具零网络：列表解析/判级/去重/帖JSON
纪律：礼貌抓取（单页单代码、帖间 1 秒、失败如实登记）、只碰公开面；判级=词面信号不证真伪；
      真伪核验走 rumor-chain-verifier + 一级信源（xhcj 公告检索/交易所官网）。
"""
import json, os, re, sys, time, urllib.request, datetime

VERSION = "2.2.1"
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
      'Accept': 'text/html,application/xhtml+xml', 'Accept-Language': 'zh-CN,zh;q=0.9'}

RED_WORDS = ["立案", "立案调查", "处罚", "退市", "造假", "财务造假", "暴雷", "维权", "ST", "问询函",
             "内幕", "听说", "朋友在里面", "可靠消息", "保证涨停"]
YELLOW_WORDS = ["重组", "并购", "借壳", "中标", "大单", "减持", "增持", "回购", "解禁", "定增",
                "转债", "预增", "预减", "业绩", "分红", "送转", "消息称", "据悉", "爆料", "传闻"]
DISCLAIMER = "> 免责锚：本报告为公开网页采集的词面信号整理，不构成投资建议；无目标价、无评级、不预测涨跌；股吧帖一律按未经证实传闻处理。"

class ChannelBlocked(Exception):
    """v2.2.1：通道被反爬拦截（身份核实页/域名校验），与「零新增」严格区分——被拦须报障，不得报零。"""

def _looks_blocked(t):
    return ('身份核实' in t) or ('check you domain' in t) or ('fd_guba_validate' in t) \
        or (len(t) < 3000 and 'listitem' not in t)

def fetch_guba(code, timeout=20):
    """股吧列表页直读（v1.0 实测正则原样继承；v2.2.1 增反爬识别）。"""
    url = 'https://guba.eastmoney.com/list,%s.html' % code
    req = urllib.request.Request(url, headers=UA)
    t = urllib.request.urlopen(req, timeout=timeout).read().decode('utf-8', errors='ignore')
    if _looks_blocked(t):
        raise ChannelBlocked('东财返回身份核实/域名校验页（len=%d），通道被人机验证拦截' % len(t))
    items = re.findall(r'class="listitem"[\s\S]{0,900}?href="([^"]+)"[^>]*>([^<]{4,120})<', t)
    if not items and len(t) < 20000:
        raise ChannelBlocked('页面过短且无 listitem（len=%d），疑通道异常，如实报障不报零' % len(t))
    return [{'url': u, 'title': ti.strip()} for u, ti in items]

def fetch_post(url, timeout=20):
    """帖正文直解（v2.1.0 spike 实证）：/news,<code>,<id>.html 内嵌 post_article JSON。
    返回 dict；财富号(//caifuhao)等异构链接返回 {'skipped': 原因}；失败返回 {'error': ...}。"""
    if url.startswith('//'):
        return {'skipped': '财富号/异构站链接，本版不抓正文'}
    full = url if url.startswith(('http', 'file:')) else 'https://guba.eastmoney.com' + url
    try:
        t = urllib.request.urlopen(urllib.request.Request(full, headers=UA), timeout=timeout).read().decode('utf-8', 'ignore')
        i = t.find('post_article=')
        if i < 0:
            return {'error': 'post_article 未嵌入（页面结构变更？）'}
        i += len('post_article=')
        raw = t[i:t.find('</script>', i)].rstrip().rstrip(';')
        d = json.loads(raw)
        guba = d.get('post_guba') or {}
        body = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', d.get('post_content', ''))).strip()
        return {'title': d.get('post_title'), 'body': body[:1500],
                'publish_time': d.get('post_publish_time'), 'clicks': d.get('post_click_count'),
                'comments': d.get('post_comment_count'), 'likes': d.get('post_like_count'),
                'target_code': guba.get('stockbar_code'), 'target_name': guba.get('stockbar_name')}
    except Exception as e:
        return {'error': '%s: %s' % (type(e).__name__, e)}

def classify(title):
    """词面三档判级：红=监管/造假/内幕声称；黄=基本面传闻词；蓝=一般帖。"""
    red = [w for w in RED_WORDS if w in title]
    if red:
        return "红", red
    yellow = [w for w in YELLOW_WORDS if w in title]
    if yellow:
        return "黄", yellow
    return "蓝", []

def _load_seen(path):
    if not os.path.exists(path):
        return set()
    with open(path, encoding='utf-8') as f:
        return {l.strip() for l in f if l.strip()}

def scan(codes, out_dir, tag="scan", detail_levels=("红", "黄", "蓝")):  # v2.2.0 机主令：全量穷举抓，三档皆取正文
    """逐码采集判级；全部新帖追加正文抓取（v2.2.0 全量穷举令）。失败如实登记不中断。"""
    os.makedirs(out_dir, exist_ok=True)
    day = datetime.datetime.now().strftime('%Y%m%d')
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    result = {}
    for code in codes:
        ent = {"fetched": 0, "new": 0, "error": None, "items": []}
        try:
            items = fetch_guba(code)
            ent["fetched"] = len(items)
            seen_fp = os.path.join(out_dir, '%s_seen.txt' % code)
            seen = _load_seen(seen_fp)
            fresh = [it for it in items if it['url'] not in seen]
            fp = os.path.join(out_dir, '%s_%s.jsonl' % (code, day))
            with open(fp, 'a', encoding='utf-8') as f:
                for it in fresh:
                    lv, hits = classify(it['title'])
                    rec = {'ts': ts, 'tag': tag, 'url': it['url'], 'title': it['title'], 'level': lv, 'hits': hits}
                    if lv in detail_levels:
                        time.sleep(1)  # 帖间礼貌间隔
                        det = fetch_post(it['url'])
                        rec['detail'] = det
                        tc = det.get('target_code')
                        if tc and tc != code:
                            rec['cross_flag'] = '帖属吧 %s(%s) 与采集吧 %s 不一致' % (det.get('target_name'), tc, code)
                    f.write(json.dumps(rec, ensure_ascii=False) + '\n')
                    ent["items"].append(rec)
            with open(seen_fp, 'a', encoding='utf-8') as f:
                for it in fresh:
                    f.write(it['url'] + '\n')
            ent["new"] = len(fresh)
        except ChannelBlocked as e:
            ent["blocked"] = str(e)  # v2.2.1：通道受阻单列，报障而非报零
        except Exception as e:
            ent["error"] = "%s: %s" % (type(e).__name__, e)
        result[code] = ent
        time.sleep(1)
    return result

def render_md(result, day=None):
    """白话呈报（避险守则第三条：禁黑话；首行免责锚；无预测/无评级）。"""
    day = day or datetime.datetime.now().strftime('%Y-%m-%d')
    lines = ["# 东财传闻哨兵报告（%s）" % day, "", DISCLAIMER, ""]
    any_new = False
    for code, ent in result.items():
        lines.append("## %s" % code)
        if ent.get("blocked"):
            lines.append("- ⚠ 通道受阻（如实报障，非零新增）：%s" % ent["blocked"])
            lines.append("- 处置：暂停本通道密集抓取，待验证页消退；本日扫档据不得作为「无传闻」依据。")
            lines.append(""); continue
        if ent["error"]:
            lines.append("- 采集失败（如实登记）：%s" % ent["error"]); lines.append(""); continue
        if not ent["items"]:
            lines.append("- 本轮无新增帖（已见 %d 帖对表完毕）。" % ent["fetched"]); lines.append(""); continue
        any_new = True
        for lv in ("红", "黄", "蓝"):
            bucket = [r for r in ent["items"] if r["level"] == lv]
            if not bucket:
                continue
            head = {"红": "🔴 红色档（监管/造假/内幕声称类词面信号——一律按未经证实传闻处理，涉「内幕」须示警）",
                    "黄": "🟡 黄色档（基本面传闻词——记录待核，核验走拆链流程）",
                    "蓝": "🔵 蓝色档（一般帖，无信号词，归档）"}[lv]
            lines.append("### %s" % head)
            for r in bucket:
                hit = ("（命中：%s）" % "、".join(r["hits"])) if r["hits"] else ""
                lines.append("- %s %s — %s" % (r["title"], hit, r["url"]))
                det = r.get('detail') or {}
                if det.get('body') or det.get('publish_time'):
                    meta = "发 %s｜阅 %s｜评 %s｜标的 %s(%s)" % (det.get('publish_time'), det.get('clicks'),
                           det.get('comments'), det.get('target_name'), det.get('target_code'))
                    lines.append("  - %s" % meta)
                    if det.get('body') and det['body'] != r['title']:
                        lines.append("  - 正文：%s%s" % (det['body'][:120], "…" if len(det['body']) > 120 else ""))
                elif det.get('skipped') or det.get('error'):
                    lines.append("  - 正文未取：%s" % (det.get('skipped') or det.get('error')))
                if r.get('cross_flag'):
                    lines.append("  - ⚑ 跨吧标记：%s" % r['cross_flag'])
            lines.append("")
    if any(e.get("blocked") for e in result.values()):
        lines.append("> 本轮存在通道受阻码位：报告完整性受限，已如实标障；请结合一级信源（交易所公告/新华财经通道）补核。")
    if not any_new and not any(e.get("blocked") for e in result.values()):
        lines.append("> 本轮全名单无新增传闻帖，如实报零。")
    lines.append("")
    lines.append("> 白话提示：以上只是「网上有人在说什么」的整理，不代表事情是真的；「听说/内幕」类说法不可验证，靠消息炒股长期必亏。真伪核验须对照交易所公告等一级信源。")
    return '\n'.join(lines) + '\n'

def self_test():
    """四夹具零网络：①列表解析 ②词面判级 ③跨日去重 ④帖 post_article JSON 直解。"""
    html = '<div class="listitem"><a href="/news,300059,1768897644.html">公司被立案调查是真的吗</a></div>' \
           '<div class="listitem"><a href="/news,300059,1768897645.html">消息称下季度重组</a></div>' \
           '<div class="listitem"><a href="/news,300059,1768897646.html">今天盘面聊聊</a></div>'
    items = re.findall(r'class="listitem"[\s\S]{0,900}?href="([^"]+)"[^>]*>([^<]{4,120})<', html)
    ok1 = len(items) == 3
    ok2 = [classify(t)[0] for _, t in items] == ["红", "黄", "蓝"]
    import tempfile
    td = tempfile.mkdtemp(prefix="ems_")
    with open(os.path.join(td, '300059_seen.txt'), 'w') as f:
        f.write('/news,300059,1768897644.html\n')
    ok3 = len(_load_seen(os.path.join(td, '300059_seen.txt'))) == 1
    # 夹具④：本地 HTML 文件模拟帖页（post_article 直解路径，不走网络）
    fixture = '<html><script>var x=1;post_article={"post_id":1,"post_guba":{"stockbar_code":"600651","stockbar_name":"飞乐音响"},"post_title":"t","post_content":"<p>正文内容测试</p>","post_publish_time":"2026-09-09 10:00:00","post_click_count":7,"post_comment_count":2,"post_like_count":1};</script></html>'
    fp = os.path.join(td, 'post.html')
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(fixture)
    # 直接复用 fetch_post 的解析段（文件路径转 file:// 由 urllib 直读）
    det = fetch_post('file://' + fp)
    ok4 = det.get('target_code') == '600651' and det.get('body') == '正文内容测试' and det.get('clicks') == 7
    ok5 = fetch_post('//caifuhao.eastmoney.com/news/x').get('skipped') is not None
    ok = ok1 and ok2 and ok3 and ok4 and ok5
    print("SELF-TEST %s | 列表=%s 判级=%s 去重=%s 帖JSON=%s 异构跳过=%s" % ("PASS" if ok else "FAIL", ok1, ok2, ok3, ok4, ok5))
    return 0 if ok else 1

def main(argv):
    def arg(name, default=None):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default
    codes = (arg('--codes', '300059')).split(',')
    tag = arg('--tag', 'scan')
    reg = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out_dir = arg('--out', os.path.join(reg, '哨兵采集'))
    result = scan([c.strip() for c in codes if c.strip()], out_dir, tag)
    summary = {c: {"fetched": e["fetched"], "new": e["new"], "error": e["error"], "blocked": e.get("blocked")} for c, e in result.items()}
    print(json.dumps({"version": VERSION, "summary": summary, "out": out_dir}, ensure_ascii=False))
    rp = arg('--report')
    if rp:
        with open(rp, 'w', encoding='utf-8') as f:
            f.write(render_md(result))
        print("report -> %s" % rp)

if __name__ == '__main__':
    if '--self-test' in sys.argv:
        sys.exit(self_test())
    main(sys.argv)
