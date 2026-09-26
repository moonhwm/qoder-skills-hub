# Windows/终端侧修复规程（L2–L4）

来源：2026-08-26 实战档案（幻16 / Win11 / Intel AX211 / Edge + McAfee 环境）。

## 目录

1. 三命令确诊（先拿数据）
2. 手动固定 DNS（主修复手段）
3. 代理与 VPN 残留排查
4. WPAD（自动检测设置）关闭测试
5. IPv6 分流测试
6. Hosts 文件检查
7. 浏览器层隔离测试
8. iPhone/iOS 侧 DNS 固定
9. 不同系统的 DNS 容错差异（解释"同 WiFi 不同命"）

## 1. 三命令确诊

管理员 CMD（Win 键搜 cmd → 右键以管理员身份运行）：

```
ping 223.5.5.5
ping baidu.com
nslookup baidu.com
```

必须拿到完整输出再判定，判定矩阵见 SKILL.md。nslookup 输出里的"服务器"地址是关键：若是网关（192.168.1.1）且不响应 → AP/网关 DNS 转发崩溃。

## 2. 手动固定 DNS（绕过坏掉的 AP DNS 转发）

设置 → 网络和 Internet → WLAN → 点击已连 WiFi 名称 → 「DNS 服务器分配」点编辑 → 手动：

- 首选 DNS：223.5.5.5
- 备用 DNS：119.29.29.29

保存后 CMD 执行 `ipconfig /flushdns`，然后浏览器测试。若仍不通：设置 → 网络和 Internet → WLAN → 硬件属性 → 禁用 → 等 5 秒 → 启用，再 flushdns。

**修好后不要改回自动**——AP 的 DNS 转发模块若再次崩溃，手动 DNS 的终端免疫。

## 3. 代理与 VPN 残留

- 设置 → 网络和 Internet → 代理：确认「使用代理服务器」为关；若开着且非用户本意，关掉。
- Ctrl+Shift+Esc → 进程搜 McAfee：McAfee Safe Connect / VPN 异常退出后常不归还系统代理，导致全浏览器超时但 QQ 正常。
- 典型签名：ERR_TIMED_OUT + "检查代理和防火墙"提示 = 代理层问题，不是 DNS 问题（DNS 问题报"找不到主机 / DNS_PROBE_*"）。

## 4. WPAD 关闭测试

「自动检测设置」开着时，网络中异常设备可应答 WPAD 请求投毒代理脚本。测试：关掉「自动检测设置」→ 刷新浏览器。

## 5. IPv6 分流测试

```
ping -4 baidu.com
```

-4 强制 IPv4。若 IPv4 通而默认不通 → IPv6 路由故障。临时验证：控制面板 → 网络和共享中心 → 更改适配器设置 → 右键 WLAN → 属性 → 取消勾选「Internet 协议版本 6 (TCP/IPv6)」。

## 6. Hosts 检查

记事本打开 `C:\Windows\System32\drivers\etc\hosts`：正常应全为 # 注释或空白。出现非注释的 IP-域名映射即被篡改，清除之。

## 7. 浏览器层隔离

| 测试 | 操作 | 含义 |
|---|---|---|
| InPrivate | Ctrl+Shift+N 开窗访问百度 | 能开 = 扩展/缓存污染 |
| 直访 IP | 地址栏输 http://14.215.177.38 | 能开 = DNS 层已通、域名层被劫持 |
| 换浏览器 | Chrome/Firefox | 仅 Edge 不通 = Edge 或安全软件 Web 保护劫持 |

注意：下载大文件能成功（实测 86.7MB）说明 HTTP 连接本身通畅，问题在页面渲染/域名层，范围可缩到浏览器。

## 8. iPhone / iOS 侧固定 DNS

设置 → 无线局域网 → 点 WiFi 名右侧 ⓘ → 配置 DNS → 手动 → 添加 223.5.5.5、119.29.29.29。老 iPhone（如 iPhone X）无 DNS fallback 机制，AP 的 DNS 一死就死等，必须手动固定。

## 9. 各系统 DNS 容错差异（向用户解释用）

| 系统 | AP DNS 崩溃时表现 | 原因 |
|---|---|---|
| HarmonyOS 4.x（Mate60/Mate X5） | 正常 | 有私有 DNS 备用机制 + 大量 DNS 缓存 |
| Android 新版 | 多半正常 | 同上 |
| iOS 老机型（iPhone X） | 断网 | 无 fallback，死等 AP 下发的 DNS |
| Windows 11 | 全灭 | 完全依赖 DHCP 下发的 DNS，无自动 fallback |

教训：**全家所有终端都手动固定公共 DNS**，是对抗 AP DNS 转发间歇性崩溃的终局方案。
