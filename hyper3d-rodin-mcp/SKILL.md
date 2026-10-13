---
name: hyper3d-rodin-mcp
description: >
  配置并核验 Hyper3D Rodin MCP 服务（Streamable HTTP，
  https://api.hyper3d.com/api/mcp，OAuth 授权），并指导使用其 7 件
  rodin_* 生成工具。适用场景：在 Codex CLI 或 Claude Code 中新增/修复
  hyper3d 服务配置；引导浏览器 OAuth 授权；验证连接与列出工具；解释
  rodin_create_uploads / rodin_import_images / rodin_generate /
  rodin_generate_bang / rodin_get_status / rodin_wait / rodin_get_result
  的用法与调用链；排查 401、工具缺失、授权失败等问题。中文触发词：
  配置 Hyper3D、Rodin MCP、hyper3d 授权、rodin 工具、Hyper3D 连接验证。
  不适用：Tripo 开发者站（developers.tripo3d.com，tripo_* 工具线）——
  那是独立账户体系，勿混用。
---

# Hyper3D Rodin MCP

## 定位

Hyper3D Rodin 线 = `https://api.hyper3d.com/api/mcp`（Streamable HTTP）+
OAuth（授权服务器 `api.hyper3d.com/api/grant/oauth`，scopes
`rodin:generate rodin:read`）+ 7 件 `rodin_*` 工具（Rodin Gen-2.5 / BANG 拆件）。
与 Tripo 开发者站（tripo_* 工具、credits 计费）是**两套独立账户与端点**，
回答用户问题时先辨明走的是哪条线。

## 工作流

1. **探活盘点** — 先跑 `scripts/probe_mcp.py`，确认端点在线、serverInfo、
   工具清单与 401 挑战（RFC 9728）符合预期；用户给了 token 文件时附做授权冒烟。
   实测基线（2026-09-23）：initialize 免鉴，serverInfo `hyper3d-rodin` v1.0.0，
   protocol 2025-03-26，tools/call 未授权 401。
2. **按客户端配置** — 读 `references/client_config.md`，按用户实际客户端
   （Codex / Claude Code）给即贴配置与授权步骤；沙箱/远端无客户端时必须
   诚实声明"无法代写本机配置"，只交付指南。
3. **引导授权** — 全程浏览器完成 OAuth；永不向用户索取 API key 粘贴到对话。
4. **验证交付** — 确认连接后列出 7 件工具；用法与调用链见
   `references/rodin_tools.md`。
5. **需重启则明说** — Codex 改 config.toml 后须重启会话；Claude Code 注册后
   重启或 `/mcp` Reconnect。

## 纪律

- 禁编造端点、参数、工具签名——以 `probe_mcp.py` 实测为准，实测漂移要报。
- 生成类调用消耗用户配额，批量前先确认余量；失败任务如实回传原因。
- `rodin_wait` 返回 ≠ 产物；success 后再 `rodin_get_result`。对用户只展示
  永久结果页 display_url，永不暴露 files[].url 临时签名链。
- `rodin_generate_bang` 是**后置拆件**（asset_id=已完成生成的 generation_id），
  不是与 rodin_generate 平行的生成入口；generate/generate_bang 超时不自动重试，
  让用户查 Hyper3D Mine。
- 凭据零落盘：token 只在用户指定文件/环境变量中，不写进任何交付件。

## 文件

- `scripts/probe_mcp.py` — 端点探活 + 工具盘点 + 401 挑战解析 + 可选授权冒烟
- `references/client_config.md` — Codex / Claude Code 配置、授权走查、排错速查
- `references/rodin_tools.md` — 7 件工具明细、三条典型调用链、使用纪律
