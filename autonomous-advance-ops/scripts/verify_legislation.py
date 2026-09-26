#!/usr/bin/env python3
# verify_legislation.py v1.1 —— 执行幻觉校验（autonomous-advance-ops v1.0.0 §7.10 配套）
# v1.1（2026-08-29）：随集成组件迁移——PROTO 自动指向本文件的 SKILL.md（相对路径不变）；
#   宪章/版本尾部文件改为通过 glob 获取最新版本（此前硬编码的 charter_v3.2.10/L3_v1.0/勘误表v1.3 已过时）；
#   项目侧路径检查仍依赖 PROJ_DIR 环境变量，路径失效≠立法失效（检查清单自身待刷新时将如实标注）。
# 用法: python3 scripts/verify_legislation.py
# 退出码: 0=全命中; 1=存在未命中(落实幻觉,按逃逸登记)
import os, sys, json, glob

def latest(pattern):
    """版本尾号文件取 glob 最新（按文件名排序末位），无命中返回原 pattern 使检查如实 FAIL。"""
    hits = sorted(glob.glob(pattern))
    return hits[-1] if hits else pattern

PROTO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "SKILL.md")
BRIDGE = os.environ.get("BRIDGE_SKILL", "/mnt/agents/output/cross-session-workflow-bridge/SKILL.md")
PROJ = os.environ.get("PROJ_DIR", "/mnt/agents/upload/金融分析项目/")  # v1.2 脱敏闸：默认路径去实名，私藏真名经 PROJ_DIR 注入

CHECKS = [
    ("v2.5.1 epsilon-delta", PROTO, "ε"),
    ("v2.5.2 conf词表统一", PROTO, "estimated+"),
    ("v2.5.3 铁规律+2/3表决", PROTO, "2/3"),
    ("v2.5.3 交叉-交叉检查", PROTO, "交叉"),
    ("称呼缺省（便携版：注册表由使用方自定义）", PROTO, "称呼不携带任务严肃度信息"),
    ("v2.5.4 头注计数核验", PROTO, "头注"),
    ("v2.5.5 边际递减硬停止", PROTO, "边际递减"),
    ("v2.5.5 行为改变证据", PROTO, "变化物"),
    ("v2.5.5 语音甄别⑧", PROTO, "同音"),
    ("v2.5.5 写类例外", PROTO, "写类例外"),
    ("v2.5.6 空转停用", PROTO, "空转"),
    ("v2.5.6 ROI度量", PROTO, "ROI"),
    ("v2.5.6 未来技能不可用", PROTO, "期权"),
    ("v2.5.7 压缩失真规程", PROTO, "压缩"),
    ("v2.5.8 代码外发禁令", PROTO, "外发禁令"),
    ("v2.5.8 安理会映射", PROTO, "76/262"),
    ("v2.5.8 逃逸三问", PROTO, "逃逸三问"),
    ("v2.5.8 分块审核条例", PROTO, "重叠带"),
    ("v2.5.9 全局共同遵守", PROTO, "全局共同遵守"),
    ("v2.5.9 落实幻觉核验", PROTO, "落实幻觉"),
    ("bridge 8技能路由表", BRIDGE, "路由"),
    ("bridge 截断治理", BRIDGE, "截断"),
    ("bridge 名称对应表", BRIDGE, "名称对应表"),
    ("bridge 回灌核验清单", BRIDGE, "回灌后核验清单"),
    ("宪章现行版存在", latest(PROJ+"01_宪章/charter_v3.2.*.md"), "（本文件"),
    ("评分卡滞后带", latest(PROJ+"08_方法论/源权威性评分卡_v*.md"), "滞后带"),
    ("压缩边界界定", PROJ+"08_方法论/上下文压缩边界界定_v1.0.md", "工具摄入限"),
    ("期权附带更新通知", PROJ+"08_方法论/期权条款附带更新通知_v1.0.md", "聚变期权"),
    ("SQL台账schema", PROJ+"06_证据链/external_ingestion_schema_v1.0.sql", "CREATE TABLE"),
    ("Supabase审计", PROJ+"06_证据链/supabase权限审计_v1.0.md", "S-2"),
    ("L3评审包", latest(PROJ+"10_毕业评审/L3评审申请_v*.md"), "失效模式"),
    ("适老层v1.3", PROJ+"07_推送桥接/适老呈现层规范.md", "术语+一句白话括注"),
    ("勘误表", latest(PROJ+"08_方法论/语音输入勘误对应表_v*.md"), "主程序"),
    ("决策卡8登记", PROJ+"07_推送桥接/decisions_log.md", "收敛容差 ε=2 追认"),  # v1.1 修正：原针「信箱id=8」指错对象，卡8本体=ε=2追认条目
]

def main():
    fails = []
    for name, path, needle in CHECKS:
        try:
            ok = needle in open(path, encoding="utf-8").read()
        except Exception:
            ok = False
        if not ok:
            fails.append(name)
        print(("PASS" if ok else "FAIL"), name)
    print(f"\n命中 {len(CHECKS)-len(fails)}/{len(CHECKS)}")
    if fails:
        print("落实幻觉项(按逃逸登记):", json.dumps(fails, ensure_ascii=False))
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
