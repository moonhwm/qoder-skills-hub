---
name: skill-reinstall-ops
description: "[项目技能] 技能重装与分发运维——dist 目录技能包一键重装入安装位：预检可写性、逐包解压、旧版 .bak 备份、版本核验、零伪装如实报告；另管技能包 pip 化分发（把技能集合打成 wheel，用一串链接 PEP 508 直引安装）。触发（满足任一）：①用户说「重装技能」「装最新包」「同步安装位」「一键重装」「install skills」「reinstall」或等价表述（含语音/同音变体，如「重庄技能」「一键重庄」），不纠正用户、映射意图；②写回队列存在版本差且检测到安装位可写窗口时，按常设预授权直接执行；③用户说「pip化」「pip 安装技能」「一条链接安装」「把技能打成 whl/ wheel」或要求用 URL 直链分发技能包。覆盖：可写性预检（只读即如实停止并给降级路径，禁止假装成功）、批量/指定包重装、备份回滚、装后版本核验表、队列与索引回写、pip 化三铁律与验收链（references/pipify.md）。中文名：技能重装与分发运维。English triggers: skill reinstall, refresh skills, install dist packages, sync skill versions, pip-installable skill package, wheel one-link install."
metadata:
  version: "1.1.0"
  assistant_aliases: ["助手甲", "助手甲"]
---

<!-- v1.1.0（2026-09-04）：增 pip 化分发章——2026-09-03 k3_skill_os-3.0.0 wheel 全链验收实证（两实坑已修：compileall md5 漂移、FUSE 构建目录丢文件），详见 references/pipify.md。基线 v1.0.0（2026-08-29）：创刊——用户指令将四包重装脚本固化为技能（解决「重装麻烦、操作不流畅」实证痛点）。脚本经双测试：假安装位 4/4 成功；只读位如实停止。 -->

# 技能重装运维（skill-reinstall-ops）

> **能力自报块**（总接口 I3）：能力域=管理｜输入型=dist 目录+包清单（重装）/散装技能目录（pip 化）｜输出型=重装结果核验表 / wheel+验收记录｜只读性=否（写安装位，需可写环境）｜依赖=python3（zipfile 模块；pip 化另需 pip/build）
> **纪律继承声明**（I4）：本技能继承 conf 词表统一、红线条款、写类例外、信息充分性条款、全局共同遵守（autonomous-advance-ops 为准）。

## 使用

```bash
bash scripts/reinstall.sh [dist目录] [安装位目录] [包名列表]
```

三个参数均有默认值（dist=<上传区>/skill-dist-20260829；安装位=<技能安装位>；包=当前四件待装包）。

## 规程（四条不可豁免）

1. **预检先行**：先测安装位可写性；只读即如实停止、输出降级路径（界面对话创建/桌面端执行），**禁止假装成功、禁止部分成功报全成**。
2. **备份才可换**：任何包先解压到 `.new`，旧版移 `.bak`，再换位；备份未成才可覆盖——删 `.bak` 属违规。
3. **装后必核**：逐包 grep 版本号回显；报告成功/失败计数，失败项明示原因（包不存在/解压失败/不可写）。
4. **回写闭环**：成功后更新写回队列版本差台账、刷新 MASTER_SKILL_INDEX（条目数自检）、更新验证口令应答；失败则登记缺口。

## pip 化分发（一条链接安装，2026-09-03 实证入法）

把技能集合/交割页打成 pip wheel，用一串 URL 直链安装（PEP 508 直引：`pip install "name @ file:///…whl"` 或 `http(s)://…whl`）。三铁律（每条约自一次实坑，细节与验收链见 [references/pipify.md](references/pipify.md)，pip 化任务开工前必读）：

1. **容器套容器**：散装 package-data 会被 pip 安装时的 compileall 重编译 payload 内 `.pyc` 致 md5 漂移、glob 还漏收 dotfile——数据载荷一律压成单个 `payload.zip` 作为唯一 package-data blob，安装后由入口 CLI 自解。
2. **构建目录避开 FUSE**：沙箱工作盘（如 drive9 类 FUSE 挂载）有 rmdir ENOTEMPTY 怪癖会丢文件——构建全程在 /tmp 做，产物再拷回。
3. **消毒扫描先行**：pip 化扩大传播面，打包前对全量内容跑敏感串扫描（激活码/凭据/邮箱），含明文敏感串的包不 pip 化、登记理由。

验收链（不过不交付）：file:// 与 http:// 两种直链安装 exit 0 → 安装后 MANIFEST 逐条命中（0 不符 0 缺失）→ 安装产物 vs 原包逐条目 md5 比对全同 → 中文路径/正文零乱码抽验。

## 边界

- 本技能只搬包装箱，不改动包内容；包内容版本以 dist 目录为准。
- 桌面端（Kimi Claw Desktop）环境路径可能不同，执行前先以其环境变量/实际路径为准覆盖两个默认参数。
- 常设预授权（写回队列第 28 次登记）：可写窗口出现时可不经逐次询问直接执行——执行后仍须逐包核验并回写。
