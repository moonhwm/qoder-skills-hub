# plan.md — 第四轮：MCP 接口入包 + 安全模块 + 零依赖审计（逐项串行）

## 用户校正
「不要贪，一项一项走」→ 本轮严格串行四项，每项验完再下一项。

## 四项
1. **MCP 接口入包**：cloudflare + lark 插件接口件打包进安装包 mcp/ 层。诚实边界：活 MCP server 无法随包分发（需平台侧连接与授权），入包=接口规格文档+技能说明+配置模板+连接自检脚本；其余已装机 MCP（<通道库>/neon/github/context7）同法登记。
2. **安全模块 security/**：MFA（TOTP，RFC 6238，纯 stdlib hmac）、设备指纹（多源特征哈希）、慢哈希（PBKDF2/scrypt，hashlib 原生）三件套 + 自测脚本，挂入 autonomous-advance-ops 体系（作为其 security/ 附件）与安装包。
3. **零依赖审计**：全部 106 脚本 import 扫描——凡非 stdlib 依赖逐一登记：能去依赖则改、不能则 vendor 入包或显式声明。目标：包内技能开箱零 pip。
4. **重打包复测**：安装包 v2（skills+mcp+security+installer）+ omnibus 同步更新 + 台账/锚/verifier v24。
