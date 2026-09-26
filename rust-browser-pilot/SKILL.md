---
name: rust-browser-pilot
description: 基于 Rust 的高性能无头浏览器 obscura，单二进制内嵌渲染引擎（无需系统 Chrome），通过 CDP 协议工作，执行页面抓取、DOM 提取、截图、批量采集与反检测抓取。启动快、内存省（约 30MB），适合网页抓取、自动化与 AI 代理场景。当用户需要自动化浏览器任务、网页抓取、DOM 提取、页面截图、批量采集，或需要绕过反爬检测时触发。
metadata:
  displayName: 极速浏览器自动化
  emoji: ⚡
  summary: Rust 单二进制无头浏览器（obscura），自带渲染引擎，支持 stealth 反检测。
  homepage: https://github.com/h4ckf0r0day/obscura
  primaryEnv: bash
  os:
  - darwin
  - linux
  requires:
    bins:
    - obscura
  install:
  - kind: binary
    note: 预编译二进制，无需 cargo/brew/Chrome
    example: '# Linux x86_64（其他平台见 Releases 页）

      curl -LO https://github.com/h4ckf0r0day/obscura/releases/latest/download/obscura-x86_64-linux.tar.gz

      tar xzf obscura-x86_64-linux.tar.gz

      # 注意：agent 沙箱容器层跨调用不持久，/usr/local/bin 会丢失。

      # 必须装到持久卷并用绝对路径调用：

      mkdir -p 「输出区」/tools/obscura

      cp obscura obscura-worker 「输出区」/tools/obscura/

      「输出区」/tools/obscura/obscura --version  # 验证

      '
---

<!-- 后端已迁移：原 fast-browser-use 上游 404（2026-08-26 核实），现基于 obscura（h4ckf0r0day/obscura，Apache/MIT，活跃维护）。 -->

# 极速浏览器自动化（obscura）

单二进制 Rust 无头浏览器，内嵌渲染引擎（**不依赖系统 Chrome**），所有命令均为 `obscura` 子命令。

## 🧪 Agent 使用场景

### 1. 抓取页面（最常用）

```bash
obscura fetch "https://example.com" --dump markdown   # markdown|text|html|links
obscura fetch "https://example.com" --selector "#content" --wait 3 --timeout 30
```

### 2. 绕过反爬检测

```bash
obscura fetch "https://protected-site.com" --dump text --stealth
# --stealth：一致浏览器指纹 + TLS 伪装 + tracker 拦截（全局选项，各子命令通用）
```

### 3. 页面截图

```bash
obscura fetch "https://example.com" -s page.png       # PNG 截图（需 render feature）
```

### 4. 批量/结构化采集

```bash
obscura scrape "https://a.com" "https://b.com" --format json --concurrency 10
obscura scrape "https://a.com" -e "document.title"    # 注入 JS 提取
# 大批量：URLs 写入文件，每行一个
obscura fetch --file urls.txt --concurrency 4
```

### 5. 给 Puppeteer / Playwright 当后端（CDP 服务）

```bash
obscura serve -p 9222 --workers 4
# 然后 Puppeteer/Playwright 连接 ws://127.0.0.1:9222
```

### 6. 会话/Cookie 提取（反爬挑战后的会话令牌）

```bash
obscura fetch "https://site.com" --dump cookies       # 含 HttpOnly cookie，JSON 数组
```

### 7. MCP 模式

```bash
obscura mcp   # 作为 MCP server 供支持 MCP 的客户端调用
```

## 全局选项

| 选项 | 用途 |
|---|---|
| `--stealth` | 反检测（指纹/TLS/tracker） |
| `--proxy <URL>` | 代理 |
| `--user-agent <UA>` | 自定义 UA |
| `--obey-robots` | 遵守 robots.txt（fetch/scrape） |
| `--storage-dir <DIR>` | 持久化浏览器状态（会话复用） |
| `--allow-private-network` | 允许访问 localhost/内网（默认拦截，SSRF 防护） |

## 使用说明

- 优先 `fetch --dump markdown` 取正文；需要结构化数据用 `scrape --format json`；需要截图用 `fetch -s`。
- 遇到反爬/滑块先加 `--stealth` 重试；仍被拦截则属目标站点强防护，报告用户即可，不要硬闯。
- 安全默认：不访问内网地址（`--allow-private-network` 仅限本地开发时显式开启）。
