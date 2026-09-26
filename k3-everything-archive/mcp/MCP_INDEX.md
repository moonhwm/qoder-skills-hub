# MCP 接口层说明（mcp/）

## 诚实边界（先说清）

活 MCP server **无法随包分发**——MCP 连接依赖宿主平台的插件装载、OAuth/凭据授权与网络通道，这些是运行时绑定而非文件资产。本层入包的是**接口资产**：接口规格（kimi.plugin.json 清单）、全部技能说明书（SKILL.md 树）、连接自检脚本与配置模板。接收端在支持同名 MCP 的平台上装入插件后，本层文档即生效；无此平台能力时，文档作为人工调用 API 的规程参考。

## 内容

| 目录/文件 | 内容 |
|---|---|
| cloudflare/ | 插件清单 + cloudflare-mcp-usage 技能文档（2500+ 端点 Code Mode 调用规程） |
| lark/ | 插件清单 + 26 件 lark-* 技能文档（消息/文档/多维表格/日历/邮箱/任务/审批/OKR/会议/妙记/知识库/画板） |
| other-mcp-manifests.json | <通道库> / neon / github / context7 接口清单登记 |
| check_mcp.py | 连接自检：探测当前环境可见的 MCP 工具名前缀，输出 在场/缺席 清单 |
| config-template.json | 连接配置模板（凭据字段一律占位符，零明文） |

## 安全红线

- 本层不含任何凭据；config-template.json 全占位；
- 凡 plugin_status 报某 MCP 失败：不调用、不伪造、告知重连/重授权（项目既有立法，随包传递）。
