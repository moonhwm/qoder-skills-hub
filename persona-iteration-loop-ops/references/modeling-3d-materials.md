# 3D 建模材质与面数方案穷举（modeling-3d-materials）v1.0.0

> 3ds Max 优先，Blender 次要对标。服务 §2.1 人设文档的建模映射与 body-attire-spec 的附录建议。
> conf 词表：empirical=来源实测/官方文档；estimated=行业惯例转述；assumed=推断。研究底稿（含全部来源 URL）：workspace/v120/research_3d_materials.md。

## 1. 面数预算分档（全身角色，三角面）

| 用途 | 低模 | 中模/主角 | 高模/影视 | conf |
|---|---|---|---|---|
| 手游 | 1.5k–5k tris | 10k–20k tris | — | estimated |
| 主机/PC | 20k–40k tris（身体）+发/饰 5k–15k | 40k–120k tris（UE 高精） | 150k+（含 LOD） | estimated，与 vsquad 50k–150k+ 口径冲突，偏旧风险已登记 |
| 老一代实证锚 | FFXIII 7k–14k polys；Gears of War 15k–20.2k polys | — | — | empirical |
| 影视/静帧 | — | 细分+置换无硬上限 | 单场景可达 20 亿 polys（John Carter 例） | empirical |
| 3D 打印 | FDM 100k–500k faces | 树脂 500k–1.5M faces | 关键在水密/壁厚 | estimated |

头发：发卡单独网格，图集 2048²（MetaHuman 式 32 张 512×256 卡片，empirical）；发卡统一面数区间=查无实据（普遍说法数千~1.5 万 tris，estimated）。眼睛：独立网格（角膜/虹膜/巩膜/泪线四层），单眼面数惯例=查无实据。

## 2. PBR 贴图族（角色）

Albedo 2K–4K（脸部 UDIM 单 tile 4K）｜Normal 切线空间（OpenGL/DirectX 两约定，实时 8K 上限）｜Roughness 与 albedo 同级或降一级｜Metalness 0/1 二元为主｜AO 1K–4K｜Displacement 游戏 2K–4K、影视皮肤 16K（SKAP 实证）｜SSS 权重图 2K–4K｜Translucency（耳垂等薄组织，V-Ray 用 VRay2SidedMtl）｜Specular 可省（metal/rough 流程）。

## 3. 皮肤 SSS（3ds Max）

| 方案 | 皮肤典型参数 | conf |
|---|---|---|
| Arnold aiStandardSurface | Subsurface Weight=1；Radius RGB=1.0/0.35/0.2；米制场景 Scale=0.01；深/浅肤色 R 可至 3.67–4.82 | empirical（官方+TexturingXYZ Winnie） |
| V-Ray VRayALSurface | 散射半径 5–20mm；表皮/真皮/血管三层独立着色；需 GI | empirical |
| V-Ray VRayFastSSS2 | 皮肤各向异性≈0.8 | empirical |
| Physical Material SSS | 语义同 Arnold，具体推荐值查无实据（沿用 Arnold 值） | assumed |
| 高光层 | IOR≈1.42；Specular Weight≈0.5；Roughness≈0.35；汗湿 Coat IOR 1.337 | empirical |

## 4. 头发

- **发卡（实时）**：外层轮廓卡 8-bit alpha、贴头皮卡 1-bit alpha；长发图集可 2048×4096（empirical，polycount/Reallusion）。
- **Ornatrix（离线/影视）**：程序化算子栈 guides→clump→braid；V-Ray/Arnold/Redshift 原生毛发图元；可烘焙发卡+Alembic/USD；动力学 Moov/MassFX（empirical）。
- Max 自带 Hair & Fur：已被 Ornatrix 生态取代（estimated）。

## 5. 眼睛

角膜（透明凸壳）→虹膜（内凹置角膜后）→巩膜（轻 SSS 湿润）→泪线（沿睑缘窄条几何模拟泪液弯月面）（empirical，The Rookies 案例）。角膜 IOR≈1.376 为生理常识级（assumed，文献级来源查无实据）。

## 6. 布料/穿搭材质（PBR 倾向）

| 面料 | Roughness | Metalness | 备注 |
|---|---|---|---|
| 棉 | 0.8–0.9 | 0 | empirical（Roblox 材质参考，唯一具体数值来源） |
| 牛仔 | 0.9 | 0 | 同上 |
| 丝 | 0.52 | 应为 0（该来源给 0.3 系平台风格化取值，勿照搬） | empirical+冲突登记 |
| 皮革 | 0.62 | 0 | 同上 |
| 针织/毛皮 | 0.75 | 0 | 同上 |
| 麻 | 查无实据 | 0 | 按高糙度假定 0.7–0.9（assumed） |
| 金属配饰（黄铜/钢） | 0.25–0.48 | 1.0 | empirical |

面料贴图三件套：baseColor+normal（织纹）+roughness；灯芯绒/粗花呢加 displacement（empirical，Style3D）。
**MD→Max 流程**：MD 导出 OBJ（single object/unweld/thin/Unified UV）+ 平铺参考版 → 重拓扑为四边面 basemesh → 回 ZBrush 重投影褶皱；缝纫线对象会触发拓扑重建，必要时先删缝纫关系（empirical，3DGladiator/MD 社区）。

## 7. UV 与 Texel Density

基准：hero 资产 10.24–20.48 px/cm，背景 5.12，LOD 逐级减半（10.24→5.12→2.56）（empirical，多源一致）。TD=贴图分辨率/世界尺寸（1K 覆盖 1m²=10.24 px/cm）。分岛惯例：脸/头独占一 UDIM tile，手+臂合并，躯干+腿脚 2K；影视皮肤位移多 UDIM+16K。Max 无内置 TD 工具用 TextTools 插件；Blender 用 Texel Density Checker。

## 8. Blender 对标（Principled BSDF）

Base Color←Albedo；Roughness/Metallic 直连；Normal 经 Normal Map 节点（Non-Color，OpenGL）；SSS=Subsurface Weight/Radius/Scale，方法选 **Random Walk (Skin)**（4.x+ 皮肤专用），Radius 映 RGB，Scale 单位 cm，皮肤各向异性 0.8；Weight 0.1–0.3（社区实测）与手册「0 或 1」冲突，按版本试（estimated）；Coat←汗湿层，Sheen←布料绒感；AO 无直接接口需混合。

## 已知存疑（top3_likely_wrong 随件登记）

1. 主机主角 15k–50k tris 区间偏旧（营销博客源 vs vsquad 50k–150k+ 冲突）。
2. Blender 皮肤 SSS Weight 0.1–0.3 与官方手册冲突（4.x 语义已变）。
3. 「丝 Metalness 0.3」物理上应为 0，系来源平台风格化取值。
