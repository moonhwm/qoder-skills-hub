# pip 化分发参考（pipify.md）

> 实证来源：2026-09-03「k3_skill_os-3.0.0」wheel 全链验收（74 技能 / 832 文件 / file:// 与 http:// 双直链安装 exit 0 / md5 832/832 全同 / 中文零乱码）。pip 化任务开工前通读本文。

## 一、一条链接安装的四种形态（PEP 508 直引）

核心语法：`pip install "<分发名> @ <URL>"`（direct reference，`name @ URL`）。

1. **本地直链**：`pip install "name @ file:///abs/path/pkg-1.0.0-py3-none-any.whl"`
2. **HTTP 直链**：`pip install "name @ https://host/path/pkg-1.0.0-py3-none-any.whl"`（任意静态托管/GitHub Release 资产均可）
3. **压缩包直链**：URL 指向 sdist（.tar.gz）亦可，但 wheel 更稳（免构建步骤）。
4. **requirements 钉版**：requirements.txt 里写 `name @ URL` 同样生效，适合批量分发。

注意：URL 里带查询串的分享页链接不是直链——需先解析出真实文件 URL 再拼 `name @ URL`。

## 二、容器套容器（反 compileall 漂移，铁律 1 的展开）

- 症状：散装 package-data 方案下，pip 安装时的 compileall 会重编译 payload 内 `.pyc` → md5 漂移；package-data 的 glob 还会漏收 dotfile。
- 治法：整个技能集合压成**单个 `payload.zip`** 作为 wheel 内唯一 package-data blob；安装后由包的入口 CLI（如 `xxx install`）自解到目标目录。
- 附带红利：wheel 规范即 UTF-8，payload.zip 内非 ASCII 条目显式置 0x800 标志位可根治中文乱码。

## 三、构建卫生（铁律 2 的展开）

- 沙箱工作盘若是 FUSE 挂载（实证：drive9 有 rmdir ENOTEMPTY 怪癖，构建中丢过 4 件 .pyc）——**构建全程在 /tmp 做**，产物核验后再拷回工作区。
- 构建前后各跑一次文件计数/清单快照，差异即丢文件信号。

## 四、验收链（不过不交付）

1. file:// 与 http:// 两种直链安装均 exit 0；
2. 安装后 MANIFEST 逐条核验：命中数/0 不符/0 缺失；
3. 安装产物 vs 原包**逐条目 md5 比对**全同（内容零漂移）；
4. 中文抽验：含中文路径与中文正文的代表性文件各至少一件，可读且交叉引用可解析；
5. 全部 runs 轨迹留档（verifier/runs/ 目录惯例）。

## 五、边界与红线

- **消毒扫描先行**：pip 化扩大传播面。打包前对全量内容跑敏感串扫描（激活码/凭据/API key/私人邮箱）；命中明文敏感串的包不 pip 化，登记理由并知会委托方。
- 版本运营：wheel 文件名自带版本号（`pkg-x.y.z-py3-none-any.whl`），同链接换版本要换文件名或显式声明覆盖。
- pip 化 ≠ 重装：本件管分发形态；装入安装位仍走 SKILL.md 主规程（预检/备份/核验/回写）。
