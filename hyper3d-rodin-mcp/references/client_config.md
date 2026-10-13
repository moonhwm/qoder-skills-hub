# Hyper3D Rodin MCP 客户端配置参考

端点：`https://api.hyper3d.com/api/mcp`（Streamable HTTP，服务名 `hyper3d`）
实测（2026-09-23）：initialize 免鉴（serverInfo `hyper3d-rodin` v1.0.0，protocol
2025-03-26）；tools/call 未授权回 401，WWW-Authenticate 按 RFC 9728 指向
`https://api.hyper3d.com/api/mcp/.well-known/oauth-protected-resource`，
授权服务器 `https://api.hyper3d.com/api/grant/oauth`（PKCE S256 / DCR register /
device_code / jwks），scopes：`rodin:generate rodin:read`。

## Codex CLI

1. `~/.codex/config.toml` 追加（已有其他 mcp_servers 段则保留）：
   ```toml
   [mcp_servers.hyper3d]
   url = "https://api.hyper3d.com/api/mcp"
   ```
   说明：
   - 现行 Codex 的 Streamable HTTP + OAuth 为默认路径（config-reference 中
     `mcp_servers.<id>.auth = "oauth"` 即默认值，显式写出亦可）。
   - **旧版 Codex**（2025 中过渡期构建）若按上面配置不识别/不发起 OAuth，
     再在文件顶层补一行 `experimental_use_rmcp_client = true` 并重启；
     新构建无需此行（已退役，贴上无害）。
2. 重启 Codex 会话后执行：`codex mcp login hyper3d`
3. 浏览器完成 Hyper3D 账户登录与授权（OAuth，自动回跳）。
4. 验证：`codex mcp list` 应见 hyper3d（`codex mcp get hyper3d` 看详情）；
   会话内可列出 7 件 rodin_* 工具。取消授权：`codex mcp logout hyper3d`。

## Claude Code

1. 一次性注册（Streamable HTTP 传输）：
   ```bash
   claude mcp add --transport http hyper3d https://api.hyper3d.com/api/mcp
   ```
2. 重启（或在会话内 `/mcp` 选 hyper3d → Reconnect）。
3. `/mcp` → 选 hyper3d → Authenticate → 浏览器完成授权。
4. 验证：`/mcp` 面板中 hyper3d 显示 connected 且工具就位。

## 授权走查要点

- 授权在浏览器完成；终端/会话内只收回调，不粘贴任何 key。
- 授权主体是 Hyper3D 平台账户；与 Tripo 开发者站（developers.tripo3d.com）账户体系独立。
- 若浏览器曾登录过平台账户，授权页会直接确认；换账户需先登出平台网页。
- SSH/容器等无浏览器环境：确认客户端支持的回调方式（端口转发或回调 URL 配置），
  或在本机完成授权后再行迁移——不要替用户代收验证码。

## 排错速查

| 症状 | 处置 |
|------|------|
| 配置写了但不发起 OAuth / 不识别服务 | 旧构建补 `experimental_use_rmcp_client = true` 并重启；新构建核对 TOML 段名拼写 |
| `codex mcp login` 找不到服务 | 确认 config.toml 已保存且重启了会话；`codex mcp list` 复查 |
| Claude 侧 `/mcp` 无 hyper3d | `claude mcp list` 复查注册；重跑 add 命令；重启 |
| 401 / unauthorized | 授权过期或未完成，重新走 login/Authenticate |
| 工具列表为空 | 先跑 `scripts/probe_mcp.py` 验端点；再核对 scopes 是否含 rodin:generate rodin:read |
| 回调超时 | 浏览器与客户端需同机同浏览器默认 profile；公司代理可能拦 localhost 回调 |
