#!/usr/bin/env python3
"""source_triage.py

信源通道初判与验证状态登记工具（source-semantics-sentinel 功能一的自动化部分）。

按 references/verification_channels.md 的通道阶梯（C0-C4）对来源清单做
启发式分类，给出验证状态登记与上升建议（T0-T3）。分类为启发式初判：
域名未命中内置表时落 C3 并注明 unrecognized_source，须人工复核；
C2 交叉三角仅按 claim_key 聚类给出候选，独立性须人工确认。

输入：JSONL（位置参数文件路径，可省略读 stdin），每行一个来源：
  {
    "id": "S1",                          // 可选，缺省自动生成 L<行号>
    "url": "https://www.sec.gov/...",    // 与 source_desc 至少其一
    "source_desc": "某财经媒体报道",     // 与 url 至少其一
    "title": "10-K 原文",                // 可选
    "retrieved_at": "YYYY-MM-DD",        // 可选，非法格式进 warnings
    "claim_key": "营收数据"              // 可选，同事实多来源用同一 key
  }

输出：向 stdout 写入 JSON：
  - items:   每条含 id / input_ref / channel_tier / tier_name / tier_reason /
             cross_evidence / verification_status / escalation
             （escalation 含 level 与 action，对应 T0 自动判 / T1 交叉复核 /
             T2 权威源或插件核验 / T3 人工裁决）
  - errors:   行级错误（非法 JSON、url 与 source_desc 双缺）
  - warnings: 非阻断警告（如 retrieved_at 非法）
  - summary:  各通道档计数
  - notes:    启发式局限声明

仅使用 Python 标准库。退出码：0 正常（即使有行级 errors）；1 --smoke
断言失败；2 输入错误（文件不可读/输入为空）。
"""

import argparse
import json
import re
import sys
from urllib.parse import urlparse

# ---------------- 通道档定义 ----------------

TIERS = {
    "C0": "tier0_primary",
    "C1": "tier1_authoritative_plugin",
    "C2": "tier2_cross_triangulated",
    "C3": "tier3_single_relay",
    "C4": "tier4_anonymous_social",
}

# C0 一手原始：监管/交易所/政府底表类域名（原文文档，非数据产品）
C0_DOMAINS = {
    "sec.gov", "cninfo.com.cn", "sse.com.cn", "szse.cn", "hkexnews.hk",
    "bse.cn", "neeq.com.cn", "chinacourt.org", "wenshu.court.gov.cn",
    "samr.gov.cn", "gsxt.gov.cn", "pbc.gov.cn", "stats.gov.cn",
    "customs.gov.cn", "mee.gov.cn", "miit.gov.cn", "mof.gov.cn",
}
C0_SUFFIXES = (".gov.cn", ".gov.hk", ".gov", ".europa.eu")

# C1 官方/权威数据源插件：数据产品、学术库
C1_DOMAINS = {
    "wind.com.cn", "10jqka.com.cn", "ifind.com", "gildata.com",
    "choice.eastmoney.com", "csmar.com", "cnki.net", "wanfangdata.com.cn",
    "pubmed.ncbi.nlm.nih.gov", "webofscience.com", "scopus.com",
    "sciencedirect.com", "ieeexplore.ieee.org", "link.springer.com",
    "scholar.google.com", "jstor.org", "ssrn.com", "arxiv.org",
}

# C4 匿名/弱实名社媒
C4_DOMAINS = {
    "weibo.com", "x.com", "twitter.com", "reddit.com", "tieba.baidu.com",
    "guba.eastmoney.com", "xiaohongshu.com", "zhihu.com", "douyin.com",
    "tiktok.com", "facebook.com", "instagram.com", "4chan.org",
    "v2ex.com", "t.me", "telegram.org", "quora.com",
}

ESC_BY_TIER = {
    "C0": ("T0", "自动判：记录即采用；R-高命题按需抽查字段口径"),
    "C1": ("T0", "自动判：记录即采用并标注 data_cutoff 与库口径；R-高升 T1 交叉复核"),
    "C2": ("T0", "自动判：记录即采用；R-高升 T2 权威源/插件核验一次"),
    "C3": ("T1", "交叉复核：另找 ≥1 个独立信源核对；R-高升 T2"),
    "C4": ("T2", "权威源/插件核验：仅作线索，须回到 C0/C1；R-高考核失败禁入结论、登记 T3 人工裁决"),
}

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ---------------- 分类 ----------------

def registrable_domain(url):
    """取可注册域（近似）：处理 .com.cn/.gov.cn 等复合后缀。"""
    try:
        host = urlparse(url if "://" in url else "https://" + url).netloc
    except ValueError:
        return ""
    host = host.split("@")[-1].split(":")[0].lower()
    if host.startswith("www."):
        host = host[4:]
    labels = host.split(".")
    if len(labels) >= 3 and labels[-2] in ("com", "gov", "org", "net", "edu", "ac"):
        return ".".join(labels[-3:])
    return ".".join(labels[-2:]) if len(labels) >= 2 else host


def _host_match(host, domain_set):
    """host 与集合中任一域相同或为其子域时，返回该域，否则 None。"""
    for d in domain_set:
        if host == d or host.endswith("." + d):
            return d
    return None


def classify_base(url):
    """按域名启发式定基础通道档，返回 (tier, reason)。"""
    if not url:
        return "C3", "无 URL 仅文字描述，按单一转述初判"
    try:
        host = urlparse(url if "://" in url else "https://" + url).netloc
    except ValueError:
        host = ""
    host = host.split("@")[-1].split(":")[0].lower()
    if host.startswith("www."):
        host = host[4:]
    if not host:
        return "C3", "URL 无法解析域名，按单一转述初判"
    hit = _host_match(host, C0_DOMAINS)
    if hit or any(host.endswith(s) for s in C0_SUFFIXES):
        return "C0", "监管/交易所/政府底表类域名（%s），初判一手原始" % (hit or host)
    hit = _host_match(host, C1_DOMAINS)
    if hit:
        return "C1", "权威数据源插件/学术库域名（%s）" % hit
    hit = _host_match(host, C4_DOMAINS)
    if hit:
        return "C4", "匿名/弱实名社媒域名（%s），仅作线索" % hit
    return "C3", "unrecognized_source：域名（%s）未命中内置表，落 C3 待人工复核" % registrable_domain(url)


def triage(items):
    """主分类：基础定级 + claim_key 聚类给 C2 候选。"""
    out = []
    for it in items:
        tier, reason = classify_base(it.get("url", ""))
        out.append({
            "id": it["id"],
            "input_ref": it.get("url") or it.get("source_desc"),
            "channel_tier": tier,
            "tier_name": TIERS[tier],
            "tier_reason": reason,
            "claim_key": it.get("claim_key"),
            "domain": registrable_domain(it.get("url", "")) or None,
            "cross_evidence": False,
        })

    # claim_key 聚类：≥2 个不同域且非全 C4 → C2 候选升级（仅对 C3 成员）
    groups = {}
    for rec in out:
        key = rec.get("claim_key")
        if key:
            groups.setdefault(key, []).append(rec)
    for key, members in sorted(groups.items()):
        domains = {m["domain"] for m in members if m["domain"]}
        non_c4 = [m for m in members if m["channel_tier"] != "C4"]
        if len(members) >= 2 and len(domains) >= 2 and len(non_c4) >= 2:
            for m in non_c4:
                m["cross_evidence"] = True
                if m["channel_tier"] == "C3":
                    m["channel_tier"] = "C2"
                    m["tier_name"] = TIERS["C2"]
                    m["tier_reason"] = (
                        "claim_key「%s」聚类命中 ≥2 个不同域来源，"
                        "C2 交叉三角候选（独立性未经脚本核验，须人工确认"
                        "无互相引用/共同上游）；基础定级：%s"
                        % (key, m["tier_reason"]))

    for rec in out:
        level, action = ESC_BY_TIER[rec["channel_tier"]]
        rec["verification_status"] = (
            "T0_auto_judged" if level == "T0" else "pending_" + level)
        rec["escalation"] = {"level": level, "action": action}
        rec.pop("claim_key", None)
        rec.pop("domain", None)
    return out


def parse_jsonl(text):
    """逐行解析，返回 (items, errors, warnings)。"""
    items, errors, warnings = [], [], []
    for lineno, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append({"line": lineno,
                           "error": "非法 JSON: %s" % e})
            continue
        if not isinstance(obj, dict):
            errors.append({"line": lineno, "error": "行不是 JSON 对象"})
            continue
        if not obj.get("url") and not obj.get("source_desc"):
            errors.append({"line": lineno,
                           "error": "url 与 source_desc 双缺"})
            continue
        obj.setdefault("id", "L%d" % lineno)
        ra = obj.get("retrieved_at")
        if ra and not _DATE_RE.match(str(ra)):
            warnings.append({"line": lineno, "id": obj["id"],
                             "warning": "retrieved_at 非 YYYY-MM-DD: %r" % ra})
        items.append(obj)
    return items, errors, warnings


def run(text):
    items, errors, warnings = parse_jsonl(text)
    records = triage(items)
    summary = {}
    for rec in records:
        key = "%s %s" % (rec["channel_tier"], rec["tier_name"])
        summary[key] = summary.get(key, 0) + 1
    return {
        "items": records,
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
        "notes": "通道定级为启发式初判：unrecognized_source 落 C3 须人工按 "
                 "references/verification_channels.md 第 1 节复核；C2 候选的"
                 "来源独立性须人工确认；信源矛盾一律按 Conflict→人工铁律"
                 "阻断，不得降级硬塞 conf。",
    }


# ---------------- smoke ----------------

SMOKE_JSONL = "\n".join([
    json.dumps({"id": "S1", "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany",
                "title": "10-K 原文", "retrieved_at": "2026-08-24"}),
    json.dumps({"id": "S2", "url": "https://www.wind.com.cn/portal/zhanghu",
                "retrieved_at": "2026-08-24"}),
    json.dumps({"id": "S3", "url": "https://www.caixin.com/2026-08-20/a.html",
                "claim_key": "某公司营收"}),
    json.dumps({"id": "S4", "url": "https://finance.sina.com.cn/stock/b.html",
                "claim_key": "某公司营收"}),
    json.dumps({"id": "S5", "url": "https://weibo.com/u/123456",
                "source_desc": "匿名爆料"}),
    json.dumps({"id": "S6", "source_desc": "行业会议纪要（口头转述）",
                "retrieved_at": "08-24"}),
    json.dumps({"id": "S8", "url": "https://guba.eastmoney.com/news,123.html"}),
    '{"id": "S7", broken json',
])


def run_smoke():
    failures = []

    def expect(cond, msg):
        if not cond:
            failures.append(msg)

    res = run(SMOKE_JSONL)
    by_id = {r["id"]: r for r in res["items"]}

    expect(by_id["S1"]["channel_tier"] == "C0",
           "smoke: S1 sec.gov 应判 C0，实为 %s" % by_id["S1"]["channel_tier"])
    expect(by_id["S2"]["channel_tier"] == "C1",
           "smoke: S2 wind 应判 C1，实为 %s" % by_id["S2"]["channel_tier"])
    expect(by_id["S3"]["channel_tier"] == "C2" and
           by_id["S4"]["channel_tier"] == "C2",
           "smoke: S3/S4 同 claim_key 不同域应升 C2，实为 %s/%s"
           % (by_id["S3"]["channel_tier"], by_id["S4"]["channel_tier"]))
    expect(by_id["S3"]["cross_evidence"] and by_id["S4"]["cross_evidence"],
           "smoke: S3/S4 cross_evidence 应为 True")
    expect(by_id["S5"]["channel_tier"] == "C4",
           "smoke: S5 weibo 应判 C4，实为 %s" % by_id["S5"]["channel_tier"])
    expect(by_id["S6"]["channel_tier"] == "C3",
           "smoke: S6 无 URL 应落 C3，实为 %s" % by_id["S6"]["channel_tier"])
    expect("unrecognized_source" in by_id["S3"]["tier_reason"],
           "smoke: S3 未识别域名升 C2 前应为 unrecognized_source 初判")
    expect(by_id["S5"]["escalation"]["level"] == "T2",
           "smoke: C4 上升建议应为 T2")
    expect(by_id["S3"]["verification_status"] == "T0_auto_judged",
           "smoke: C2 状态应为 T0_auto_judged")
    expect(by_id["S8"]["channel_tier"] == "C4",
           "smoke: S8 guba.eastmoney.com 子域应判 C4，实为 %s"
           % by_id["S8"]["channel_tier"])
    expect(len(res["errors"]) == 1 and res["errors"][0]["line"] == 8,
           "smoke: 第 8 行非法 JSON 应记 error，实为 %s" % res["errors"])
    expect(len(res["warnings"]) == 1,
           "smoke: S6 非法 retrieved_at 应记 warning")

    if failures:
        print("SMOKE FAILED:")
        for f_ in failures:
            print("  - " + f_)
        return 1
    print("SMOKE OK: C0/C1/C2聚类升级/C4/C3兜底/行级error/warning 全命中；"
          "summary=%s" % res["summary"])
    return 0


# ---------------- CLI ----------------

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="信源通道初判（C0-C4）+ 验证状态登记 + 上升建议（T0-T3），"
                    "输入 JSONL，输出 JSON。启发式初判，须人工复核。")
    p.add_argument("file", nargs="?", help="JSONL 文件路径；缺省读 stdin")
    p.add_argument("--pretty", action="store_true",
                   help="以缩进格式输出 JSON（默认紧凑输出）")
    p.add_argument("--smoke", action="store_true",
                   help="运行内置合成样例自检后退出")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.smoke:
        return run_smoke()

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                text = fh.read()
        except OSError as e:
            print("输入错误：无法读取文件 %s: %s" % (args.file, e),
                  file=sys.stderr)
            return 2
    else:
        text = sys.stdin.read()
    if not text.strip():
        print("输入错误：输入为空", file=sys.stderr)
        return 2

    result = run(text)
    json.dump(result, sys.stdout, ensure_ascii=False,
              indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
