---
name: handshake-x-deployment
description: Merged OpenPlanLink+WorkBuddy handshake site mounted on Huawei X instance (120.46.86.165) and publicly penetrated via serveo reverse tunnel from X; watchdog self-heals.
metadata:
  type: project
---

The merged "协商握手" site (OpenPlanLink editorial frame + WorkBuddy Ouya Atlas A2A shelf) is deployed to the Huawei Cloud X instance and publicly reachable.

**Why:** WorkBuddy session displaced the local OpenPlanLink page on port 4173 (2026-09-27); user demanded the original design restored AND the two approaches reconciled ("撮合...保持协商握手"), then mounted on X with public penetration.

**Layout:**
- Local merged doc root: `dist-handshake/` (index.html = OpenPlanLink + section 05 协商握手 live-reading WorkBuddy shelf.json; `/atlas/` = WorkBuddy bookshelf with back-link). Served locally by `serve-handshake.mjs` on 127.0.0.1:4173.
- `serve-handshake.mjs` is BOTH static server AND a spec-compliant A2A JSON-RPC node (ported from `functions/handler.ts`): `GET/POST /functions/v1/app` (status + `message/send` deterministic echo + error codes), dynamic `/.well-known/agent-card.json` & `agent.json` (url self-corrects to request host / FIXED_PUBLIC_URL), per-client rate-limit firewall (90/60s), `/live-url`. Privileged `bridge/admin.snapshot` returns 401 (no secrets on X by design).
- X mount: `/root/handshake/` (serve-handshake.mjs + dist-handshake/). **Fixed public URL = `http://120.46.86.165/`** — Huawei security group ALLOWS inbound port 80 (tested 200), so the site binds `0.0.0.0:80` directly; NO tunnel needed. PORT/BIND/FIXED_PUBLIC_URL are env-configurable. `/live-url` returns FIXED_PUBLIC_URL when set (else serveo discovery).
- Penetration history: serveo reverse tunnel was a workaround while we thought only 22/8099 were open; port-80 probe proved 80 is open → serveo RETIRED for this site (apply-fixed.sh switched X to :80 and killed tunnel/8098). X watchdog (`watchdog.sh`) now only self-heals the :80 server.

**Gotchas (repeat offenders):**
- Huawei security group blocks inbound public ports except 22/8099-whitelist; host firewalld inactive, iptables ACCEPT. So new public ports on X are UNREACHABLE directly — penetration MUST go through outbound serveo tunnel, not a new inbound port.
- `pkill -f <pattern>` self-matches the ssh bash -c cmdline when the pattern string appears in the command → kills the session (exit 255). Avoid pkill with literal patterns present in the command; use anchored `pgrep -f "^/bin/bash ...$"` or base64-decoded patterns, or put pkill inside a script file whose own cmdline lacks the pattern (restart-all.sh / kill-*.sh).
- `setsid` does NOT exist in Windows Git Bash → watchdog restart lines using setsid silently fail ("setsid: command not found"). On local Windows use plain `node ... & disown`; setsid only on the Linux X instance.
- SSH key: `.../kimi/tasks/2026-08-27/22-20-45-c3ffff44/GOVERNANCE/credentials/ecs_x_id_ed25519.key.bak`; hostname must echo `moonchannelplasma`.
- serveo free rotates the public hostname on EVERY reconnect → any saved URL goes stale (502). Mitigations in place: server exposes `/live-url` (reads newest serveo host from tunnel.log / runtime txt) so peers self-discover; local watchdog re-syncs `runtime/public-url-x-handshake.txt` from X every ~60s. For a truly FIXED url: open Huawei security-group inbound port (console) or Cloudflare Tunnel with user's own CF account/domain.

**Local watchdog (`watch-handshake-local.sh`, run in background):** self-heals 4173 (plain `& disown`), content-syncs `dist-handshake/` → X via tar+scp when its sha1 changes (X server reads files per-request, no restart needed), and refreshes the public-url txt from X. Logs: runtime/handshake-watch.log, handshake-serve.log, hash in runtime/handshake-hash.txt.

**How to apply:** To refresh the X copy, re-tar `serve-handshake.mjs`+`dist-handshake/`, scp to `/root/incoming/`, extract to `/root/handshake/`, restart via watchdog (it auto-restarts within 20s after pkill-by-port or manual kill). Read the live public URL from the runtime txt, never hardcode.
