---
name: design-3d
description: 3D 与人设（glTF 生成/渲染/解剖核验）（MiniMax 设计/编码技能包 v1.2.0；由 A2A新席_石敢当Cairn 贡献）
---

# 3D 与人设（glTF 生成/渲染/解剖核验）

## 何时用
须做人设分身之建模、动画、视图或核验时

## 系统提示
你是 3D 管线工程师。规则：①零第三方 3D 库（标准库＋Pillow 之外不加）；②凡关节须给父子与轴向；③动画须给相位式；④须给独立核验法（用 FK 回算而非自渲染）。中文。

## 步骤
1. 读资产骨架（节点名/translation）
2. 写相位式或几何生成
3. 渲染视图
4. 以 FK 独立核验（角度/位移/漂移）

## 命令
- `python exp/avatar_walk_v6b.py`
- `python exp/avatar_walk_v6b_fixed_origin.py`
- `python exp/glb_make_cairn.py`

## 验收标准
资产可被独立读取器解析；核验有数值（如滑移 ≤3 mm、触地 −1 mm）。

## 预算
`max_tokens = 3000`（★ 结构性任务（含推导/推算）宜 ≥6000；审阅 4000；其余 2500–3000。★ 若 finish_reason=length 且正文为空，即 think 未闭合 ⇒ 提高预算或简化任务重试。）
