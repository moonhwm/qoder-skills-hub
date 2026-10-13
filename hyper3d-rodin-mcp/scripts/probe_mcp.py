#!/usr/bin/env python3
"""Hyper3D Rodin MCP 端点探活与能力盘点（免授权部分）。

用法:
    python3 probe_mcp.py [--url https://api.hyper3d.com/api/mcp] [--token-file PATH]

输出 (JSON 到 stdout):
    endpoint_ok     端点可达且 initialize 成功
    server_info     initialize 返回的 serverInfo
    protocol        协商到的 protocolVersion
    tools           tools/list 返回的工具名清单（若端点免鉴列工具）
    auth_challenge  tools/call 未授权时的 WWW-Authenticate 头（用于核对 OAuth 链路）
    protected_resource / scopes  从 401 挑战中解析

说明:
    - initialize 实测免鉴；tools/call 需 OAuth Bearer（scope: rodin:generate rodin:read）。
    - 提供 --token-file（内含一行 access_token）时，附带做一次授权 tools/call 冒烟（rodin_get_status 传假 task_id，预期业务报错而非 401）。
"""
import argparse, json, sys, urllib.request, urllib.error

MCP_URL = "https://api.hyper3d.com/api/mcp"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}

def _parse_body(raw: bytes):
    """MCP Streamable HTTP 可能回 JSON 或 SSE 流，统一提取最后一个 JSON-RPC 消息。"""
    text = raw.decode("utf-8", "replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        last = None
        for line in text.splitlines():
            if line.startswith("data:"):
                try:
                    last = json.loads(line[5:].strip())
                except json.JSONDecodeError:
                    pass
        return last

def _post(url, payload, token=None):
    headers = dict(HEADERS)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, dict(resp.headers), _parse_body(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), _parse_body(e.read() or b"{}")
    except Exception as e:  # 网络层失败
        return None, {}, {"error": f"{type(e).__name__}: {e}"}

def _rpc(method, params=None, rid=1):
    return {"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=MCP_URL)
    ap.add_argument("--token-file", default=None)
    args = ap.parse_args()

    out = {"url": args.url, "endpoint_ok": False}

    # 1) initialize（实测免鉴）
    st, hdr, body = _post(args.url, _rpc("initialize", {
        "protocolVersion": "2025-03-26",
        "capabilities": {},
        "clientInfo": {"name": "hyper3d-rodin-mcp-probe", "version": "1.0.0"},
    }))
    if st == 200 and body and "result" in body:
        out["endpoint_ok"] = True
        out["server_info"] = body["result"].get("serverInfo")
        out["protocol"] = body["result"].get("protocolVersion")
        # notifications/initialized
        _post(args.url, {"jsonrpc": "2.0", "method": "notifications/initialized"})
    else:
        out["initialize_status"] = st
        out["initialize_body"] = body
        print(json.dumps(out, ensure_ascii=False, indent=2))
        sys.exit(1)

    # 2) tools/list
    st, hdr, body = _post(args.url, _rpc("tools/list", rid=2))
    if st == 200 and body and "result" in body:
        out["tools"] = [t.get("name") for t in body["result"].get("tools", [])]
    else:
        out["tools_list_status"] = st
        out["tools_list_body"] = body

    # 3) 未授权 tools/call → 期望 401 + WWW-Authenticate（RFC 9728）
    st, hdr, body = _post(args.url, _rpc("tools/call", {
        "name": "rodin_get_status", "arguments": {"task_id": "probe-nonexistent"},
    }, rid=3))
    out["unauth_call_status"] = st
    if st == 401:
        chal = hdr.get("WWW-Authenticate") or hdr.get("www-authenticate") or ""
        out["auth_challenge"] = chal
        for part in chal.replace('"', "").split(","):
            kv = part.strip().split("=", 1)
            if len(kv) == 2:
                if kv[0].endswith("resource_metadata"):
                    out["protected_resource"] = kv[1]
                elif kv[0].strip() == "scope":
                    out["scopes"] = kv[1].split()
    elif st == 200:
        out["note"] = "tools/call 未返回 401（端点策略可能已变更）"

    # 4) 可选：授权冒烟
    if args.token_file:
        try:
            token = open(args.token_file).read().strip()
        except OSError as e:
            out["auth_smoke"] = f"token 读取失败: {e}"
        else:
            st, hdr, body = _post(args.url, _rpc("tools/call", {
                "name": "rodin_get_status",
                "arguments": {"generation_id": "probe-nonexistent"},
            }, rid=4), token=token)
            out["auth_smoke_status"] = st
            out["auth_smoke_note"] = (
                "授权链路通（业务错误属预期）" if st == 200
                else f"授权冒烟异常（HTTP {st}）：若 401 则 token 失效需重授权")

    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
