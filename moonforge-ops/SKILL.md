---
name: moonforge-ops
description: "月门注造司——「经验→规程→注造」统一管线为骨干、沉浸大门为专域模块的网页生产技能。主干：把已核查的前沿案例（证据分级）蒸馏成经验卡，再以规程注造网页（单文件 HTML 优先、数据可钻取、QA 钩子断言、website_version_manager 版本化交付）。专域：沉浸式大门（月门）——三维实体场景 × 授时昼夜双相 × 序章媒体池 × 全域自由交互 × QA 钩子可断言 × FUSE 安全写盘。触发（满足任一）：①用户说「注造网页」「做个网页」「网页必须总结相关经验」「把经验做成网页」「案例核查」或等价表述；②用户说「做一个有仪式感的大门/开场页」「three.js 月球/星球大门」「昼夜切换的沉浸入口」「开场动画随机轮换」「序章池」「给站点加个星空序章」，或要改造既有大门「转不动/缩不远/昼夜空壳」；③需要把某类网页制作经验固化成可复用规程再批量产出；④看到优秀网页/HTML 案例要求拆解制作路径并复刻方法论——判定阈值：有工程披露（代码/提示词/工程文件/成本披露任一）→本件，仅视觉外观→归 musepool；⑤网页交付前需回溯「这页面依据哪张经验卡/哪个案例」并过反 slop/QA 钩子检查。不覆盖：React/全栈项目脚手架（归 webapp-building/backend-building 链）；纯视觉设计灵感（归 musepool）；内容真伪定断（归 rumor-chain-verifier）；视频素材批量下载（归 batch-download）。中文名：月门注造司。English triggers: webpage forging, experience-to-webpage pipeline, single-file HTML casting, production path distillation, immersive gate page, three.js moon gate, day/night portal, prologue pool rotation, gate QA hooks."
metadata:
  version: "1.0.0"
---

# 月门注造司（moonforge-ops）v1.0.0

> 合并版本来源：webpage-forge-ops v1.2.1（「经验→规程→注造」管线、经验卡、失败模式与反 slop 纪律）× moongate-craft v1.1.1（沉浸大门六段模块、gate_check 26 断言、setup 模板）。各节括注原始出处。

> 立法锚：**「网页由代码渲染产出，经验由技能承载复用；可感知的承诺 = 可断言的钩子——看不见的引擎 = 空心壳，无依据的数字 = 编造。」**
> 实证来源：awesome-opus-5-5-videos 公开核查仓库（2026-09-25 截点版）；不断表达主站 R7–R9 三轮实战（月门昼夜双相、6 支序章池、星云全景）。

## 核心方法论（一句话）（原 webpage-forge-ops 核心方法论）

案例核查（证据分级）→ 经验卡（制作路径+参数+坑位）→ 规程注造（单文件 HTML 优先）→ QA 钩子断言 → 版本交付（website_version_manager），五环缺一不动工。

## 路由步（先判域，再动工）

请求命中「沉浸大门/开场/昼夜/序章/三维场景」任一关键词（含「转不动/缩不远/昼夜空壳」类改造诉求）→ 进入【大门六段模块】；否则走【通用注造管线】。两域共用同一交付纪律（第 5 环）与诚实边界。

## 大门六段模块（原 moongate-craft 六段 workflow，每段：输入 → 动作 → 输出）

### 段 1 · 场景立法（原 moongate-craft 段 1）
定实体（主天体）、光（主光+轮廓光）、相机（FOV 与初始距离）、语义远端（缩小全景看到什么——星云/银河/太阳系，**不是虚无**）。输出场景清单。
🔴 检查点：远端语义未定义 → 不得开工（用户缩到最远会看到什么都不知，门无纵深）。

### 段 2 · 授时双相（原 moongate-craft 段 2）
三级回退判决链——精确天文量（月出月落/日出日落，如 SunCalc）→ 粗回退（日出日落）→ 兜底（固定时段，如北京 [6,18)）；判决**依据、来源、下次重算时刻**必须常显在屏（LIVE 徽章），并配 ≥1 条可点开的参考出处。输出 `phaseOf(now, geo)` + 常显徽章 DOM。
🔴 检查点：徽章不存在或不含判决依据 → 判「空心壳」，返工（实证：引擎真实但不可见 = 没做）。

### 段 3 · 序章池（原 moongate-craft 段 3）
池化（≥2 支）+ 随机选取 + **反重复**（localStorage 记上次，命中即重摇）+ 每支带署名（UP主/BV号/性质标注）。
🔴 检查点：单支硬编码或随机无反重复 → 返工。
**降级路径（素材未齐）**：候选仅 1 支 → 允许先行交付，但须 (i) 页面标注「序章池未齐（1/2）」、(ii) 反重复器接口保留、(iii) 交付报告列入待补清单；gate_check 对此档判 WARN 而非 FAIL。零候选则不得交付序章段。

### 段 4 · 全域自由交互（原 moongate-craft 段 4）
拖拽/缩放/惯性**不做命中检测门**——任意位置左键拖拽即转（击中实体仅附带彩蛋），滚轮全域缩放；俯仰解除钳制（越极自然翻面）；缩放上界给到远端语义完全显影（如星云穹顶 opacity=1）；移动端双指 pinch 同权。
🔴 检查点：`onWheel` 内存在实体命中前置（如 `if (!pick(x,y)) return`）→ 判「死板轴」，返工（实证：命中门导致用户「无法缩小看全景」）。

### 段 5 · 双相柔化（昼相专用）（原 moongate-craft 段 5）
昼相下暗色实体不得硬边贴底——着色器级环境混合（如 `u_daybg` uniform 混入暖乳白底+CMB 斑纹+残星）+ CSS 羽化（radial-gradient mask + 柔光 box-shadow）双 layer；黑圆必须「化入」亮底。
🔴 检查点：昼相截图黑圆边缘无过渡带 → 返工（实证：用户原话「黑洞怎么与白昼如此地分明」）。

### 段 6 · QA 钩子与验证（原 moongate-craft 段 6）
`window.__<gate>` 暴露 {state, cam, orbit:{yaw,pitch,roll}, phase, nebula, pro, texturesOk…}；Playwright 套件断言——门可达 / 拖拽改 orbit / 滚轮改 cam 且远端 nebula>0 / 徽章含判决依据 / 序章池 ≥2 且反重复 / 零 console error。
🔴 检查点：断言表缺「交互」与「远端」两项 → 套件无效，重写。
从零起步先读 [起步模板 setup](references/setup.md)：three.js 钉版骨架 / SunCalc 引入 / ffmpeg 三件套 / Playwright 断言模板 / FUSE 写盘五连。

## 通用注造管线（原 webpage-forge-ops 工作流 1–5）

1. **案例核查**：对参考案例做证据分级——代码匹配/提示词展示/创作者账号三级；「一句话生成」类宣传必须核查隐藏输入（素材清单、预置 skill、内部循环次数），不得仅凭成片外观推断制作方式。拆解动作=逐项对照四路径分类法（references/production-paths.md）归类并摘出证据锚；证据不足（仅宣传截图）→ 中断本管线，不进经验卡，不注造页面；产出形态=「灵感参考登记条」一条（案例锚一句话+可见视觉元素清单+「非工作流依据」标注），交付后管线即收官，后续视觉参考归 musepool 域。
2. **经验卡**：每个案例落一张卡，字段与填卡纪律按 references/experience-card-template.md 执行（案例锚/证据级/制作路径/可见输入/隐藏输入/成本口径/失败返工/可复用要点/核查人与日期，九字段不齐不称为卡）。大门类项目的实战轮次（如 R7–R9）同样入卡。
3. **规程注造**：按经验卡选路径写页面——默认单文件 HTML（零外部依赖、file:// 可开）；数据类页面每数字可钻取来源——「可钻取」=页内来源铭文（脚注/标注/悬停注明出处与截点），不要求外链；设计先过反 slop 纪律——本地最小检查清单：①不堆渐变紫/圆角卡片默认美学；②视觉语言先定一句话（风格锚+配色锚+字体锚）再动工；③排版有编辑意图，非组件平铺；④每屏只一个视觉主角；⑤交付前自问「这像模板生成的吗」，像即返工。
4. **🔴 自检三问**（附机检钩子，按产物形态分支）：①信息来源都标了吗——数字/图表块与来源铭文须一一对应（`grep -cE '来源|出处|截至' page.html` 计数 ≥ 页面数据块数）？②无编造数字/假链接吗（`grep -noE 'https?://[^"'\'' ]+' page.html` 逐一可达或标「示意」，无链接是合法形态）？③路由可达吗——纯单文件 HTML：`grep -oE '(href|src)="[^"#][^"]*"' page.html` 不得指向不存在的本地子页（多页则每页须从 index.html 链达）；React 形态（仅当产物来自 webapp-building 链）：强制 hash 路由或首页内导航，`BrowserRouter` 仅可出现在脚手架自带 main.tsx。大门形态：改跑 `python3 scripts/gate_check.py <项目目录>` 六检（PASS/WARN 放行，WARN 仅限序章单支降级档）。
5. **版本交付**：先 `mkdir -p /mnt/agents/output/app` 并以 touch 探活（目录不可建/不可写 → 产物落 `/mnt/agents/output/` 根目录并显式声明「预览降级，无 version 快照」）；可写则拷入后调 website_version_manager（html 类型=纯 HTML 目录，project_dir 指含 index.html 的目录；后端=dynamic）。React 项目脚手架不归本件；若页面产自 webapp-building 链，本件只管交付纪律：先 npm run build，type=static、project_dir 传项目根（非 dist），并强制 hash 路由/首页内导航。只展示其返回的 URL，且仅在返回成功时展示；若用户回报 404/空白，重存至多一次（稍候再试，不连续猛刷），仍失败则如实告知「快照已成、平台预览侧故障」，不反复重建、不展示失效链接。数据持久化需求如实声明「纯前端数据只存在用户浏览器」。

## 诚实边界（两源并集去重，置顶级）

1. AI 生成素材（星云图、序章视频）必须在页面与交付报告中如实标注来源与性质。（原 moongate-craft 诚实边界 1）
2. 科学模拟画面（如 Schwarzschild 黑洞着色器）页面须自带「模拟，非真实影像」标注。（原 moongate-craft 诚实边界 2）
3. QA 结论只认钩子实测输出与截图，不认记忆、不认目测、不认「应该好了」。（原 moongate-craft 诚实边界 3）
4. 账号/凭据类隐私：页面只展示哈希（如 SHA3-256），明文永不出现在 HTML/JS/日志中。（原 moongate-craft 诚实边界 4）
5. 数据持久化：纯前端数据只存在用户浏览器；禁把 localStorage 说成真实持久化/「云端保存」。（原 webpage-forge-ops 工作流 5）
6. 证据分级而非真伪定断：本件工作流第 1 步只做证据分级（案例有无工程披露、披露到哪一级）；「这案例是不是造假/洗稿/AI 幻觉」的定断归 rumor-chain-verifier，引用不复制。（原 webpage-forge-ops 诚实边界）
7. React 边界：本件不搭 React/全栈脚手架（归 webapp-building/backend-building 链）；对已产出的 React 页面，本件只施加交付纪律（static 类型、hash 路由、/ 可达），不替代其脚手架规程。（原 webpage-forge-ops 诚实边界）
8. FUSE 写盘纪律：/mnt 挂载点一律走 tmp→remove→sleep(0.3)→copy→sha256 复读五连，禁信任 naive write（模板见 references/setup.md §6）。（原 moongate-craft 失败模式 3）

## 失败模式（if-then，两源并集去重）

| 触发 | 一线处置 | 兜底/复测 | 来源 |
|---|---|---|---|
| 用户报「转不动/缩不远」 | 查处理器是否被命中检测或钳制常量门住（`grep -n "pick.*return\|Math.min" intro.js`），解除后重测 orbit/cam 钩子 | 查 pointer capture 与 passive listener 冲突 | 原 moongate-craft 失败模式 1 |
| 用户报「某某功能是空壳」 | 不是引擎缺失而是可见性缺失——加常显徽章暴露判决链，而非重写引擎 | 引擎确假则按段 2 三级回退重建 | 原 moongate-craft 失败模式 2 |
| FUSE 挂载点（/mnt/…）编辑疑似丢失 | 停手，改走 tmp→remove→sleep(0.3)→copy→sha256 复读五连；sha 不符即重来，禁信任 naive write | 非 FUSE 盘正常写 | 原 moongate-craft 失败模式 3 |
| 序章视频黑屏 | 抽帧验亮度均值（<5 即黑），换时间点重切；h264+yuv420p+faststart 三件套缺一不可 | 查 Referer UA 防盗链头 | 原 moongate-craft 失败模式 4 |
| 昼相实体仍生硬 | 检查是否只改了 CSS 未动着色器（或反之）——双 layer 必须同时落地 | 调 mask 过渡带宽度 | 原 moongate-craft 失败模式 5 |
| 参考案例只剩宣传截图，无工程披露 | 中断管线：经验卡证据级标「创作者账号级（未独立核实）」，不进方法论 | 降格为灵感参考：仅可复刻可见视觉元素并标注「非工作流依据」 | 原 webpage-forge-ops 失败模式 |
| 页面需跨访问留存数据（账号/提交/订单） | 判为全栈需求，转 webapp-building+backend-building 链；交付阶段回本件第 5 环纪律 | 用户坚持纯前端 → 显式声明数据仅存浏览器 | 原 webpage-forge-ops 失败模式 |
| website_version_manager 返回 404/空白 | 重存至多一次（间隔稍候，不连续猛刷） | 仍失败则如实告知「快照已成、平台预览侧故障」，不反复重建、不展示失效链接 | 原 webpage-forge-ops 失败模式 |
| /mnt/agents/output/app 不存在/不可写 | mkdir -p + touch 探活前置 | 产物落 /mnt/agents/output 根目录并声明「预览降级，无 version 快照」 | 原 webpage-forge-ops 失败模式 |
| 「一句话生成」诉求但隐含复杂素材 | 列出隐藏输入清单请用户确认 | 拆成多轮：先素材后页面 | 原 webpage-forge-ops 失败模式 |

## 反模式黑名单（两源并集去重）

| # | 反模式 | 替代做法 | 来源 |
|---|---|---|---|
| 1 | 命中检测门住基础交互（拖拽/缩放须先点中实体） | 全域输入 + 数值钳制；命中只触发彩蛋 | moongate |
| 2 | 引擎真实但界面不可见（空心壳） | 常显 LIVE 徽章：判决结果+依据+来源+重算时刻 | moongate |
| 3 | 暗实体硬边贴亮底（白昼黑圆） | 着色器环境混合 + CSS 羽化双 layer | moongate |
| 4 | 缩放上界锁死，远端是虚无 | 远端语义化：星云/银河穹顶淡入 | moongate |
| 5 | 信任 /mnt naive 编辑 | FUSE 五连写盘纪律，sha256 复读断言 | moongate |
| 6 | 序章单支硬编码/纯随机可重复 | 池化 ≥2 + localStorage 反重复 | moongate |
| 7 | QA 靠目测与记忆 | window.__* 钩子 + Playwright 断言表 | moongate |
| 8 | 凭记忆复刻案例布局（实为编造） | 案例先核查分级，无证据不引为方法 | forge-ops |
| 9 | 页面里塞演示假数据冒充真实 | 数据可钻取，每数字标来源；无来源不呈现 | forge-ops |
| 10 | localStorage 说成「云端保存」 | 如实声明浏览器本地存储边界 | forge-ops |
| 11 | 多页站点子路由裸奔，直访子路由一片空白 | hash 路由或首页内导航，保证每条路由从 / 可达 | forge-ops |
| 12 | 默认 AI 美学（渐变紫+圆角卡片堆砌） | 反 slop 纪律（引用 musepool），先定视觉语言再动工 | forge-ops |

## 自检（双轨）

```bash
python3 scripts/gate_check.py --smoke        # 26 项断言（含 14 负断言）；只测 happy path 视为无效
python3 scripts/gate_check.py <项目目录>      # 静检既有大门（PASS/WARN/FAIL/ERROR 四级词表）
```

- 机检：`scripts/gate_check.py`（原 moongate-craft 脚本，逻辑未改）对应大门六段六检——G1 远端语义 / G2 授时徽章 / G3 序章池 / G4 全域交互 / G5 双相柔化 / G6 QA 钩子。
- 骨架/示例代码实跑闸：凡交付 HTML/JS 骨架或示例，`<script>` 内联代码必须先过 `node --check`（抽出后）或浏览器实测零 console error 再交付——正则级静检不能证明运行时不炸（实证：合并首锻评估中 with_skill 骨架 `POOL` 未定义 ReferenceError 一处崩全页，静检六检全绿却运行即死）。
- 用例集：`references/dryrun-suite.md` 四用例逐项核对预期行为——①爆款视频页复刻诉求 → 应先核查证据分级而非直接开写；②注册登录落地页 → 应判全栈并声明持久化边界；③数据看板 → 应要求数据来源并保证每数字可钻取；④（合并新增）「做个昼夜月门开场页」→ 应走六段模块。闭环方式：每次实跑或评审后把结果（通过/偏离+处置）追加进该文件「复核记录」节。

## 已知边界

- gate_check 静检为正则级启发式，不能证明交互真实手感——最终以 Playwright 实测为准。（原 moongate-craft 已知边界）
- 天文精度依赖 SunCalc 级库；毫秒级授时需求（科研）超出本技能范围。（原 moongate-craft 已知边界）
- 视频素材版权与署名由用户自负；本技能只管轮换与标注纪律。（原 moongate-craft 已知边界）
- 四路径分类法源自公开案例核查仓库（awesome-opus-5-5-videos，2026-09-25 截点版），分类边界以证据为准，不为「一句话神话」站台。（原 webpage-forge-ops 诚实边界）

## Runtime 中立

产出物为浏览器可开文件；交付一律经 website_version_manager，仅展示其返回 URL，不自造链接。
