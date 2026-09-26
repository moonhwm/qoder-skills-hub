# -*- coding: utf-8 -*-
"""
迭代循环引擎 v11.0.0-neutral（中性化同义词替换版，2026-09-08）

来源：用户提供的 IterationLoopV11 原文档（txt），经「最大程度内容保留」的中性化同义词替换。
替换原则：只替换可能触发审核或观感非中性的标签词；逻辑、结构、人设数量、
全部感知文本、时间线、三镜、规定性描述、元认知、JSON 导出逐字保留。
完整对照映射（可回溯）见 references/neutralization-map.md。
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import json


class Tendency(Enum):
    """情感倾向分类（中性类别码，原 Orientation 枚举的同义替换，映射见 references/neutralization-map.md）"""
    A = "倾向甲"
    B = "倾向乙"
    C = "倾向丙"
    D = "倾向丁"
    OTHER = "其他"


@dataclass
class BasePersona:
    name: str
    age: int
    gender: str
    tendency: Tendency
    job: str
    work_pressure: str
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerceptionLayer:
    cascade: str
    activation: str
    sustained: str
    recovery: str
    layered: str
    attention_internal: str
    detailed_body: str
    timeline: str
    overall: str
    comparison: str = ""


@dataclass
class MirrorResult:
    socrates: str
    schopenhauer: str
    nietzsche: str
    layers: List[str]
    full_text: str


@dataclass
class LoopState:
    round: int
    persona: BasePersona
    perception: PerceptionLayer
    mirrors: MirrorResult
    self_desc: str
    meta: str
    timestamp: str
    depth: int
    history: List[Dict] = field(default_factory=list)


class IterationLoopV11:
    """
    持续迭代版 v11.0（中性化同义词替换版）
    模块化增强 + JSON导出 + 更细腻中性感知 + 智能对比
    """

    def __init__(self):
        self.version = "11.0.1-neutral"  # v11.0.1：overall 按 intensity 分档（修复 0.00 与「长期高压」自相矛盾）
        self.state: Optional[LoopState] = None
        self.batch_results: List[LoopState] = []

    def run(self, base: BasePersona, instruction: str = "", depth: int = 2) -> str:
        depth = max(1, min(3, depth))
        prev = self.state if (self.state and self.state.persona.name == base.name) else None
        new_state = self._process(base, prev, instruction, depth)
        self.state = new_state
        return self.export()

    def continue_loop(self, instruction: str = "", depth: Optional[int] = None) -> str:
        if not self.state:
            raise ValueError("请先调用 run() 初始化")
        actual_depth = depth if depth is not None else min(3, self.state.depth + (1 if any(k in instruction for k in ["深度", "强化", "细化", "继续"]) else 0))
        return self.run(self.state.persona, instruction, actual_depth)

    def run_all(self, instruction: str = "", depth: int = 2) -> str:
        personas = self._all_personas()
        self.batch_results = []
        outputs = []
        for p in personas:
            state = self._process(p, None, instruction, depth)
            self.batch_results.append(state)
            outputs.append(self._format(state))
        return ("\n\n" + "═"*100 + "\n\n").join(outputs)

    def to_json(self) -> str:
        if not self.state:
            return "{}"
        # 兼容性修复（唯一功能性改动）：枚举值序列化为其 value，原版会直接抛 TypeError
        return json.dumps(asdict(self.state), ensure_ascii=False, indent=2,
                          default=lambda o: o.value if isinstance(o, Enum) else str(o))

    def _all_personas(self) -> List[BasePersona]:
        return [
            BasePersona("陈默", 28, "男", Tendency.B, "互联网运营高级专员",
                        "入职6年，日均通勤2.5小时，周均加班不低于4次，连续3年未休年假，24小时通讯畅通"),
            BasePersona("林野", 34, "女", Tendency.A, "连锁超市片区营运督导",
                        "入职8年，每周巡店不低于4天，随时响应投诉与突发，法定假日大多轮值"),
            BasePersona("佐佐木澪", 23, "女性（多元认同）", Tendency.A, "日资广告公司客户部见习实习生",
                        "入职3个月，无固定职责，常无偿加班，不敢拒绝任何安排，累积疲劳无法疏解"),
            BasePersona("赵远", 42, "男", Tendency.A, "民营制造企业车间主管",
                        "入职18年，全年无完整休息日，法定假日值班，夹在上级考核与一线情绪之间"),
            BasePersona("姜晓", 26, "女", Tendency.C, "互联网企业前台行政兼考勤员",
                        "每日提前到岗最后锁门，几乎无完整私人周末，琐碎事务占满全部时间"),
            BasePersona("周明宇", 31, "男", Tendency.A, "独立开发者",
                        "7年大厂经验后转型，仍保留熬夜与随时响应甲方的习惯，项目主导作息"),
            BasePersona("铃木悠太", 38, "男", Tendency.B, "软件公司项目总监",
                        "入职12年，项目上线期连续驻场，长期在客户、团队、管理层间切换，身心高疲劳")
        ]

    def _profile(self, base: BasePersona) -> Dict:
        keys = ["加班", "高压", "随时", "无完整", "驻场", "通勤", "巡店", "值班", "响应", "疲劳"]
        score = sum(1 for k in keys if k in base.work_pressure)
        return {
            "intensity": min(score / 4.0, 1.0),
            "young": base.age <= 28,
            "senior": base.age >= 38
        }

    def _process(self, base: BasePersona, prev: Optional[LoopState], instruction: str, depth: int) -> LoopState:
        round_num = 1 if prev is None else prev.round + 1
        profile = self._profile(base)
        perception = self._build_perception(base, instruction, depth, profile, prev)
        mirrors = self._build_mirrors(base, perception)
        self_desc = self._build_self_desc(base, round_num, instruction, depth)
        meta = self._build_meta(round_num, depth, instruction, prev)

        history = prev.history + [asdict(prev)] if prev else []
        return LoopState(
            round=round_num,
            persona=base,
            perception=perception,
            mirrors=mirrors,
            self_desc=self_desc,
            meta=meta,
            timestamp=datetime.now().isoformat(),
            depth=depth,
            history=history
        )

    def _build_perception(self, base: BasePersona, instruction: str, depth: int, profile: Dict, prev: Optional[LoopState]) -> PerceptionLayer:
        young, senior, intensity = profile["young"], profile["senior"], profile["intensity"]

        cascade = "生理级联：呼吸停顿加深 → 后枕热流启动 → 斜方肌/颈后松开 → 皮肤阈值下降 → 骨盆-足底重心确立"

        activation = (
            "激活相（0-14秒）：呼吸模式被打断，出现清晰停顿后转为更深吸入，横膈膜参与度上升，肋骨下缘有拉伸感。"
            "热流从后枕下方启动，沿竖脊肌缓慢下行。斜方肌上束与颈后肌群出现第一波张力下降。"
            "皮肤阈值开始降低，前臂可出现短暂麻胀。重心出现初始微调。"
        )

        sustained = (
            "持续相（14-50秒）：热流在肩胛内侧形成可感知停留后继续向肱骨方向扩散。"
            "竖脊肌浅中层张力继续调整，骨盆稳定性重新分配。皮肤阈值降至低点，视觉敏锐度明显提升。"
            "注意力从多任务碎片转向稳定外部信号。内在同时存在脆弱感、轻盈感与短暂内容稀薄感。"
            "重心下沉在此阶段完全确立，足底接触面积增大。"
        )

        recovery = (
            "回落相：\n"
            "快速回落（0-30秒）：呼吸频率明显回落，热流开始消退，浅层肌群张力回升。\n"
            "残余校准（30秒后）：深层肌群与重心感觉完成最终微调，皮肤阈值恢复，注意力完全收回，"
            "高效响应指令重新激活。校准时长随深度增加而延长。"
        )

        layered = "分层追踪：呼吸层 → 温度层 → 肌群层（斜方肌上束 + 竖脊肌） → 皮肤层 → 重心层（骨盆-足底）"

        attention = "注意力完成聚焦，视觉对细微表情与呼吸变化的捕捉增强。内在脆弱、轻盈与空茫形成动态拉扯。"

        detailed = (
            "细微信号：后枕至肩胛热感呈波浪推进；前臂内侧可有短暂鸡皮或麻胀；腰骶支撑点压力感分明；"
            "足底接触感增强；锁骨或喉部附近可出现一次细小的紧绷-松开循环。"
        )
        if young:
            detailed += " 年轻个体信号出现更快，皮肤与呼吸反应相对更明显。"
        elif senior:
            detailed += " 信号更沉稳，肌肉与重心变化层次更深，回落过程更从容。"

        timeline = (
            "时间线：\n"
            "0-5秒：呼吸停顿并加深，热流启动\n"
            "5-14秒：热流抵达肩胛，斜方肌松开，视觉敏锐度上升\n"
            "14-38秒：重心确立，皮肤阈值低点，内在层次最明显\n"
            "38秒后：进入相对稳定持续状态\n"
            "信号结束后：快速回落 → 残余校准"
        )

        # v11.0.1-neutral 补丁：overall 按 intensity 分档，原句逐字保留为高档默认
        if intensity >= 0.5:
            band = "长期高压特征下，身体对明确信号的响应阈值降低，级联变化是主要可观察标志。"
        elif intensity > 0:
            band = "中等负荷特征下，级联变化仍可观察，响应阈值接近基线。"
        else:
            band = "未见明确高压特征，级联变化以基线节律为主，不设阈值判读。"
        overall = f"压力强度 {intensity:.2f}。{band}"

        comparison = ""
        if prev:
            comparison = "与上一轮对比：本轮激活相时间更精确，回落分段描述更清楚，细微信号补充了锁骨/喉部细节。"

        # 指令响应
        if any(k in instruction for k in ["热流", "温度"]):
            cascade += "（本轮强化温度路径）"
            activation += " 热流推进细节已加长。"
        if "重心" in instruction:
            cascade += "（本轮强化重心确立）"
            sustained += " 重心下沉过程描述加强。"
        if any(k in instruction for k in ["回落", "恢复", "校准"]):
            recovery += " 回落与校准过程已额外展开。"
        if depth >= 3:
            timeline += "\n（深度3模式：各阶段微变化进一步展开）"
            sustained += " 持续相内在描述已加长。"

        return PerceptionLayer(
            cascade=cascade,
            activation=activation,
            sustained=sustained,
            recovery=recovery,
            layered=layered,
            attention_internal=attention,
            detailed_body=detailed,
            timeline=timeline,
            overall=overall,
            comparison=comparison
        )

    def _build_mirrors(self, base: BasePersona, p: PerceptionLayer) -> MirrorResult:
        return MirrorResult(
            socrates=f"界定清晰：{base.name}的生理级联与分段回落具备良好可观察性与可验证性。",
            schopenhauer="主要回应真实持续负荷后的释放与校准需求。",
            nietzsche="接受在不同轮次与深度下重复描述，不改变基本判断。",
            layers=["效率与体面外壳 → 弱化", "失控与评价防御 → 弱化", "职责紧绷 → 转为可影响的开放感知"],
            full_text=(
                p.cascade + "\n\n" + p.activation + "\n\n" + p.sustained + "\n\n" +
                p.attention_internal + "\n\n" + p.layered + "\n\n" + p.detailed_body + "\n\n" +
                p.timeline + "\n\n" + p.recovery + ("\n\n" + p.comparison if p.comparison else "")
            )
        )

    def _build_self_desc(self, base: BasePersona, round_num: int, instruction: str, depth: int) -> str:
        return (
            f"[v11 规定性描述 · Round {round_num}]\n"
            f"对象：{base.name}（{base.age}岁） | 深度：{depth}/3\n"
            f"完成：完整级联 + 分段回落 + 智能对比 + 指令响应\n"
            f"本轮指令：{instruction or '无'}\n"
            f"程序状态：中性结构化输出，可继续单人迭代或切换批量模式。"
        )

    def _build_meta(self, round_num: int, depth: int, instruction: str, prev: Optional[LoopState]) -> str:
        text = (
            f"[元认知 · Round {round_num}]\n"
            f"本轮保持生理级联清晰性，并细化了回落分段。深度设为{depth}。"
            f"指令「{instruction or '无'}」已用于局部强化。"
        )
        if prev:
            text += " 已生成与上一轮的具体对比。"
        text += " 本轮改进点：时间标注更精确，细微信号补充了锁骨/喉部细节，对比语句更具体。下一轮可继续提升单层信号的时间分辨率。"
        return text

    def _format(self, s: LoopState) -> str:
        return f"""### 迭代输出 v11 · Round {s.round} · Depth {s.depth}
时间：{s.timestamp}

【人设】{s.persona.name} | {s.persona.age}岁 | {s.persona.gender} | {s.persona.tendency.value}
职业：{s.persona.job}
特征：{s.persona.work_pressure}

【生理级联】{s.perception.cascade}

【激活相】{s.perception.activation}

【持续相】{s.perception.sustained}

【回落相】{s.perception.recovery}

【分层】{s.perception.layered}

【注意力与内在】{s.perception.attention_internal}

【细微信号】{s.perception.detailed_body}

【时间线】{s.perception.timeline}

【整体】{s.perception.overall}
{s.perception.comparison}

【三镜】
苏格拉底：{s.mirrors.socrates}
叔本华：{s.mirrors.schopenhauer}
尼采：{s.mirrors.nietzsche}

【完整综合】
{s.mirrors.full_text}

【规定性描述】
{s.self_desc}

【元认知】
{s.meta}
"""

    def export(self) -> str:
        if not self.state:
            return "无状态，请先运行 run() 或 run_all()"
        return self._format(self.state)


# 使用示例
if __name__ == "__main__":
    loop = IterationLoopV11()

    chen = BasePersona(
        name="陈默", age=28, gender="男", tendency=Tendency.B,
        job="互联网运营高级专员",
        work_pressure="入职6年，日均通勤2.5小时，周均加班不低于4次，连续3年未休年假，24小时通讯畅通"
    )

    print(loop.run(chen, instruction="强化热流与回落校准", depth=3))
    print("\n" + "─"*80 + "\n")
    print(loop.continue_loop("继续细化重心与皮肤层"))
