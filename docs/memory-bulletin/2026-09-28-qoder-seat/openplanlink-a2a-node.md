---
name: openplanlink-a2a-node
description: Persistent local A2A node ("OpenPlanLink · 幻16 Bridge Node") running as a long-lived service on this device, publicly mapped via a serveo SSH tunnel. How to operate it and where the live URL lives.
metadata:
  type: project
---

This device long-hosts the **OpenPlanLink · 幻16 A2A bridge node** — an editorial magazine-cover site plus a real, spec-compliant A2A (Agent2Agent) JSON-RPC endpoint. Built 2026-09-26. It is **not** a Qoder-Sites deployment (the `sites` MCP server isn't registered in CLI sessions; only Desktop Qoder activates it).

**Why:** the user wanted the node "ecosystemically" resident on this machine — persistent, auto-starting, self-healing — and publicly reachable over HTTP so real A2A peers can call it.

**How it runs (project root = the conversation dir):**
- `dev/server.ts` (Node type-stripping) serves `dist/` AND routes `/functions/v1/app` to `functions/handler.ts`. It also serves `/.well-known/agent-card.json` **dynamically** from the handler so the card's `url` self-corrects to the real public host. Listens on `127.0.0.1:4180`.
- `ops/watch-server.bat` + `ops/watch-tunnel.bat` = restart-on-exit watchdogs. Tunnel = `ssh -i ~/.ssh/id_ed25519 -R 80:localhost:4180 serveo.net`. `watch-server.bat` loads `runtime/secrets.env` for the auth secrets.
- `ops/url-sync.mjs` tails `runtime/tunnel.log` and rewrites `runtime/public-url.txt` to the current serveo host on every rotation (verifies `/healthz` first). Launched + stopped by start-all/stop-all.
- `ops/start-all.ps1` launches watchdogs + url-sync hidden and writes the assigned URL. `ops/stop-all.ps1` stops everything (incl. url-sync). Logs in `runtime/`.
- Autostart: user **Startup folder** entry `OpenPlanLink-node.cmd` (runs start-all.ps1 at logon). Task Scheduler registration was **denied (0x80070005)** non-elevated, so Startup is the mechanism.

**Security / agent-readability (added 2026-09-26):**
- Agent-readable surfaces (all public, no auth): `/` cover, `GET /functions/v1/app` status (includes `ecosystem` + `security` blocks), dynamic Agent Card (enriched: `securitySchemes` workbuddyKey/workbuddyTotp/cloudflareAccess, `capabilities.extensions[0]` = WorkBuddy ecosystem directory, `documentationUrl`→`/llms.txt`, `iconUrl`), `/llms.txt` orientation file. WorkBuddy seat `workbuddy-hy4` is the ecosystem initialization point.
- In-process firewall: 90 req/60s per client IP (CF-Connecting-IP/X-Forwarded-For aware), 64 KiB body cap. Rate-limit → HTTP 429 / `-32000`.
- Two-factor auth gates the privileged `bridge/admin.snapshot` method: `X-OpenPlanLink-Key` + 6-digit RFC-6238 `X-OpenPlanLink-TOTP` (or a `Cf-Access-Jwt-Assertion`). `message/send` echo stays public for interop. Secrets in `runtime/secrets.env` (loaded by watchdog). `node ops/totp-now.mjs` prints the current code. Tests: `dev/test-handler.ts` (21) + `dev/test-auth.ts` (13) all pass.
- Cloudflare edge firewall + MFA is a **turnkey kit** in `ops/cloudflare/` (setup-cloudflared.ps1 + run-tunnel.bat + config.yml + README). NOT yet applied — needs the user's own free Cloudflare account + domain + one-time `cloudflared tunnel login`. `cloudflared` is not installed and there is no CF account on the machine. It gives a stable hostname, WAF/rate-limiting, and Access(MFA) on `/functions/v1/app` while leaving discovery paths public.
- Declined by design: no "burn compute"/stress workloads; no auto-downloading/auto-executing remote skills. The URL `skillgiven.ok.kimi.link` the user cited is NOT a skill — it's a Three.js webcam demo HTML page, not installable.

**How to apply / operate:**
- Current public URL is **ephemeral** (serveo free changes the `*.serveousercontent.com` host on every reconnect). Always read `runtime/public-url.txt` for the live URL; never trust a hardcoded one. The dynamic agent card is the canonical discovery source.
- Start/stop/status: `powershell -ExecutionPolicy Bypass -File ops\start-all.ps1` / `ops\stop-all.ps1`; `type runtime\public-url.txt`.
- Verified: server-to-server `POST /functions/v1/app` `message/send` works publicly (serveo has no same-origin gateway limit, unlike Qoder Sites). Watchdog auto-restart confirmed by kill test.
- Limits to re-flag if relevant: needs user logon; live only while processes run; serveo free may show a browser interstitial (programmatic calls unaffected). For a fixed URL, switch to serveo Pro/custom domain or a Cloudflare Tunnel/VPS.
