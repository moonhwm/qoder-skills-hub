#!/usr/bin/env python3
"""MCP 连接自检（纯标准库）：扫描环境变量/常见配置位，输出各 MCP 接口在场/缺席清单。
诚实边界：本脚本只能做文件/环境位探测；活连接状态以宿主平台 plugin_status 为准。"""
import os, json, sys

EXPECTED = ["cloudflare", "lark", "<通道库>", "neon", "github", "context7"]
PLUGIN_ROOTS = ["/app/.agents/plugins", os.path.expanduser("~/.k3-plugins"), os.path.expanduser("~/.config/mcp")]

def main():
    rows = []
    for name in EXPECTED:
        found = []
        for root in PLUGIN_ROOTS:
            p = os.path.join(root, name)
            if os.path.isdir(p):
                found.append(p)
        rows.append({"mcp": name, "status": "在场(文件位)" if found else "缺席", "paths": found})
    for r in rows:
        print(f"{r['mcp']:<12} {r['status']:<14} {'; '.join(r['paths'])}")
    absent = [r["mcp"] for r in rows if r["status"] == "缺席"]
    print(f"\n汇总: {len(rows)-len(absent)}/{len(rows)} 在场; 缺席={absent or '无'}")
    print("注: 文件位在场≠活连接; 活连接以宿主平台 plugin_status 为准, 失败即重连/重授权, 禁伪造。")
    return 0
if __name__ == "__main__":
    sys.exit(main())
