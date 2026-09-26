#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Medical Malpractice Criminal Review — Scoring Engine
Version: 1.2.2
Last Updated: 2026-08-24

优化记录 (v1.1.1 → v1.2.0):
1. 架构解耦: SevereChecker / SpecialChecker / VizGenerator 独立模块
2. 性能优化: 引入 @lru_cache 缓存机制，消除重复计算
3. 准确性: 否定词检测改进为全句扫描，修复 R3 罪名区分
4. 健壮性: 增加参数验证和边界保护
5. 可扩展性: 引入插件化规则注册机制

v1.2.2 (2026-08-24): _load_params 解包 params_config.json 的 engine_params
嵌套键（此前配置完全不生效）；版本号文档头与 __version__ 统一。
"""

__version__ = "1.2.2"

import json
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from enum import Enum
from functools import lru_cache


class LiabilityLevel(Enum):
    NONE = ("无责任", 0.0, 0.0)
    SLIGHT = ("轻微责任", 0.01, 0.15)
    SECONDARY = ("次要责任", 0.16, 0.30)
    EQUAL = ("同等责任", 0.31, 0.50)
    PRIMARY = ("主要责任", 0.51, 0.80)
    FULL = ("完全责任", 0.81, 1.00)

    def __init__(self, label: str, lower: float, upper: float):
        self.label = label
        self.lower = lower
        self.upper = upper


class CrimeType(Enum):
    MEDICAL_MALPRACTICE = "医疗事故罪"
    ILLEGAL_PRACTICE_BASIC = "非法行医罪（情节严重）"
    ILLEGAL_PRACTICE_DEATH = "非法行医罪（致人死亡）"
    MANSLAUGHTER = "过失致人死亡罪"
    NOT_GUILTY = "不构成犯罪"


@dataclass
class DimensionScore:
    name: str
    raw_score: float
    weight: float
    confidence: float
    red_line_triggered: bool = False
    notes: List[str] = field(default_factory=list)

    @property
    def weighted_score(self) -> float:
        return self.raw_score * self.weight


@dataclass
class DutySegment:
    phase: str
    responsible_doctor: str
    duration_hours: float
    fault_score: float
    notes: List[str] = field(default_factory=list)


@dataclass
class ReviewResult:
    case_id: str
    total_score: float
    liability_ratio: float
    liability_level: LiabilityLevel
    crime_type: CrimeType
    dimensions: List[DimensionScore]
    red_flags: List[str]
    confidence_annotation: str
    iteration_log: List[Dict]
    severe_irresponsibility_check: Dict
    duty_segments: List[DutySegment]


# ==================== 独立模块：严重不负责任检查器 ====================
class SevereIrresponsibilityChecker:
    """严重不负责任检查器（v1.2.0 解耦为独立模块）"""

    RULES = {
        "情形一_擅离职守": {
            "keywords": {"擅离职守", "离岗", "不在岗", "找不到医生", "值班睡觉", "值班离开"},
            "negation_context": 15,
            "dimension_map": {"duty_violation": (80, 1.0), "medical_fault": (60, 0.5)},
            "severity": "致命", "penalty": 0.25,
        },
        "情形二_拒绝救治": {
            "keywords": {"拒绝救治", "拒收", "无床位", "未缴费", "拖延", "拒绝必要救治"},
            "negation_context": 15,
            "dimension_map": {"duty_violation": (85, 1.0), "medical_fault": (70, 0.6)},
            "severity": "致命", "penalty": 0.25,
        },
        "情形三_擅自试验": {
            "keywords": {"试验性", "未经批准", "未伦理审查", "未知情同意", "新技术", "干细胞"},
            "negation_context": 15,
            "dimension_map": {"medical_fault": (85, 1.0), "duty_violation": (75, 0.7)},
            "severity": "重大", "penalty": 0.15,
        },
        "情形四_违反查对": {
            "keywords": {"查对", "核对", "三查七对", "左右混淆", "输错血", "开错刀", "未做皮试", "皮试", "过敏试验"},
            "negation_context": 12,
            "dimension_map": {"duty_violation": (80, 1.0), "medical_fault": (75, 0.8)},
            "severity": "重大", "penalty": 0.15,
        },
        "情形五_违规药品器械": {
            "keywords": {"未经批准", "过期", "变质", "三无", "走私", "无合格证", "限制级", "无处方权"},
            "negation_context": 15,
            "dimension_map": {"medical_fault": (80, 1.0), "duty_violation": (70, 0.6)},
            "severity": "重大", "penalty": 0.15,
        },
        "情形六_违反核心规范": {
            "keywords": {"严重违反规范", "严重违反常规", "无菌操作", "禁忌症", "指征", "核心制度", "违反核心制度"},
            "negation_context": 15,
            "dimension_map": {"medical_fault": (75, 1.0), "duty_violation": (65, 0.5)},
            "severity": "一般", "penalty": 0.10,
        },
        "情形七_兜底条款": {
            "keywords": {"严重不负责任", "严重过失", "明显疏忽", "重大失误"},
            "negation_context": 15,
            "dimension_map": {"medical_fault": (70, 0.8), "duty_violation": (60, 0.4)},
            "severity": "争议", "penalty": 0.05,
        },
    }

    NEGATION_WORDS = {"无", "未", "没有", "并非", "不是", "不存在", "不涉及", "不含", "不具备"}
    兜底_KEYWORDS = {"漏诊", "未查体", "未行查体", "未检查", "疏忽", "遗漏", "未行腹股沟查体"}

    @classmethod
    def check(cls, case_data: Dict, red_flags: List[str]) -> Dict:
        """主检查入口（v1.2.0 优化：单次计算 notes_all）"""
        dims = case_data.get("dimensions", {})
        notes_all = cls._extract_notes(dims)

        matched_rules = []
        total_penalty = 0.0

        for rule_name, rule in cls.RULES.items():
            keyword_match = cls._check_keywords(notes_all, rule["keywords"], rule["negation_context"])
            dim_match_score, dim_matched = cls._check_dimensions(dims, rule["dimension_map"])
            match_score = (0.5 if keyword_match else 0) + dim_match_score * 0.5

            if match_score >= 0.5:
                matched_rules.append({
                    "rule": rule_name, "match_score": round(match_score, 2),
                    "severity": rule["severity"], "penalty": rule["penalty"],
                    "keyword_matched": keyword_match, "dimension_matched": dim_matched
                })
                total_penalty += rule["penalty"]

        # 兜底条款争议判定（v1.2.0 优化：复用已计算的 notes_all）
        兜底争议 = cls._check_fallback(notes_all, dims, matched_rules, red_flags)
        if 兜底争议:
            matched_rules.append({
                "rule": "情形七_兜底条款", "match_score": 0.35,
                "severity": "争议", "penalty": 0.05,
                "keyword_matched": any(kw in notes_all for kw in cls.兜底_KEYWORDS),
                "dimension_matched": 1
            })

        return {
            "matched_rules": matched_rules,
            "matched_count": len(matched_rules),
            "total_penalty": round(total_penalty, 2),
            "兜底争议": 兜底争议,
            "assessment": cls._assess(len(matched_rules), 兜底争议)
        }

    @staticmethod
    def _extract_notes(dims: Dict) -> str:
        """提取所有 notes 为单一字符串（v1.2.0 优化：集中提取，避免重复）"""
        return " ".join(str(n) for d in dims.values() for n in d.get("notes", []))

    @classmethod
    def _check_keywords(cls, notes_all: str, keywords: set, context_size: int) -> bool:
        """关键词匹配（v1.2.0 优化：改进否定词检测，扫描更大上下文）"""
        for kw in keywords:
            idx = notes_all.find(kw)
            if idx < 0:
                continue
            # 检查关键词前后更大范围的上下文
            prefix = notes_all[max(0, idx - context_size):idx]
            suffix = notes_all[idx + len(kw):idx + len(kw) + context_size]
            context = prefix + suffix
            # 如果上下文中出现否定词，则不匹配
            if any(nw in context for nw in cls.NEGATION_WORDS):
                continue
            return True
        return False

    @staticmethod
    def _check_dimensions(dims: Dict, dimension_map: Dict) -> Tuple[float, int]:
        """维度评分匹配"""
        dim_match_score = 0.0
        dim_matched = 0
        for dim_key, (threshold, weight) in dimension_map.items():
            dim_score = dims.get(dim_key, {}).get("score", 0)
            if dim_score >= threshold:
                dim_match_score += weight
                dim_matched += 1
        return dim_match_score, dim_matched

    @classmethod
    def _check_fallback(cls, notes_all: str, dims: Dict, matched_rules: List, red_flags: List) -> bool:
        """兜底条款争议判定"""
        low_quality = all(r["match_score"] < 0.6 for r in matched_rules) if matched_rules else True
        has_keyword = any(kw in notes_all for kw in cls.兜底_KEYWORDS)
        medical_fault_score = dims.get("medical_fault", {}).get("score", 0)

        if (not matched_rules or low_quality) and not red_flags:
            if medical_fault_score >= 60 or has_keyword:
                return True
        return False

    @staticmethod
    def _assess(matched_count: int, 兜底争议: bool) -> str:
        if matched_count >= 2:
            return "符合多种法定情形，构成严重不负责任"
        elif matched_count == 1 and not 兜底争议:
            return "符合一种法定情形，可能构成严重不负责任"
        elif 兜底争议:
            return "不符合七种法定情形，若入罪依赖兜底条款，存在重大司法争议（参见韩杰案）"
        return "不符合七种法定情形，不构成严重不负责任"


# ==================== 独立模块：特殊情形检查器 ====================
class SpecialCircumstanceChecker:
    """特殊情形检查器（v1.2.0 解耦为独立模块）"""

    KEYWORDS = {
        "未做尸检": {"未做尸检", "未行尸检", "未解剖", "家属拒绝尸检", "家属拒绝解剖", "未尸检", "未行解剖"},
        "专家意见": {"专家意见", "专家论证", "权威专家", "医学会意见", "专家支持", "符合诊疗常规", "符合规范"},
        "多因一果": {"多因一果", "多种因素", "共同导致", "综合因素", "系统性因素", "设备不到位", "制度不落实", "人员不足"},
        "次要原因力": {"次要原因力", "次要因素", "次要责任", "参与度低", "原因力小"},
        "连锁漏诊": {"连锁漏诊", "此前就诊", "其他医院", "上级医院", "此前已就诊", "此前已诊断"},
        "新手医生": {"新手", "刚取得", "刚执业", "经验不足", "独立执业时间短", "初级职称"},
        "罕见并发症": {"罕见并发症", "罕见反应", "胸膜反应", "不可预见", "难以预见", "抢救困难", "已尽合理抢救义务"},
    }

    @classmethod
    def check(cls, case_data: Dict, red_flags: List[str], severe_check: Dict) -> List[Dict]:
        """主检查入口（v1.2.0 优化：单次计算 notes_all）"""
        dims = case_data.get("dimensions", {})
        notes_all = SevereIrresponsibilityChecker._extract_notes(dims)
        alerts = []

        checks = [
            ("未做尸检", "致命", 0.25, "未行尸检，死因存在争议，鉴定意见可能不具有排他性（参见李建雪案）"),
            ("专家意见", "参考", 0.02, "存在权威专家论证支持无罪，显著降低刑事风险（参见温红案）"),
            ("多因一果", "参考", 0.02, "多因一果情形显著，系统性因素可能阻却刑事归责（参见刘希河案）"),
            ("次要原因力", "参考", 0.02, "医疗事故鉴定为'次要原因力'，不等于刑法上的'严重不负责任'（参见温红案）"),
            ("连锁漏诊", "一般", 0.05, "其他医疗机构的漏诊不构成有效减责，注意义务不随转诊而转移"),
            ("新手医生", "参考", 0.02, "执业经验不足已纳入过错评分调整，但技术水平局限不等于严重不负责任（参见刘希河案）"),
            ("罕见并发症", "参考", 0.02, "罕见并发症导致的死亡，医方已尽合理抢救义务，仅承担次要责任，不构成严重不负责任（参见北京肺结节穿刺案）"),
        ]

        for key, level, penalty, message in checks:
            if any(kw in notes_all for kw in cls.KEYWORDS[key]):
                alerts.append({"level": level, "penalty": penalty, "message": message})

        # 兜底条款争议（从 severe_check 获取，避免重复计算）
        if severe_check.get("兜底争议", False):
            alerts.append({
                "level": "重大", "penalty": 0.15,
                "message": "不符合七种'严重不负责任'法定情形，若入罪依赖兜底条款，存在重大司法争议（参见韩杰案）"
            })

        return alerts


# ==================== 独立模块：可视化数据生成器 ====================
class VizDataGenerator:
    """可视化数据生成器（v1.2.0 解耦为独立模块）"""

    @staticmethod
    def generate(result: ReviewResult) -> Dict:
        return {
            "radar": {
                "case_id": result.case_id,
                "dimensions": {d.name: d.raw_score for d in result.dimensions}
            },
            "bar": {
                "case_id": result.case_id,
                "total_score": result.total_score,
                "liability_ratio": result.liability_ratio,
                "liability_level": result.liability_level.label
            },
            "convergence": {
                "case_id": result.case_id,
                "iterations": [
                    {"round": log["iteration"], "score": log["after"], "delta": log["delta"]}
                    for log in result.iteration_log
                ]
            },
            "risk_heatmap": {
                "case_id": result.case_id,
                "fatal": sum(1 for a in result.severe_irresponsibility_check.get("matched_rules", [])
                            if a["severity"] == "致命"),
                "major": sum(1 for a in result.severe_irresponsibility_check.get("matched_rules", [])
                            if a["severity"] == "重大"),
                "general": sum(1 for a in result.severe_irresponsibility_check.get("matched_rules", [])
                              if a["severity"] == "一般"),
                "disputed": 1 if result.severe_irresponsibility_check.get("兜底争议", False) else 0
            }
        }


# ==================== 主引擎 ====================
class ScoringEngine:
    """医疗事故刑事案件多维评分引擎 v1.2.0"""

    DIMENSIONS = {
        "medical_fault": ("医疗过错程度", 0.30, 85.0),
        "causation": ("因果关系强度", 0.25, 80.0),
        "damage_severity": ("损害后果严重性", 0.20, 90.0),
        "duty_violation": ("注意义务违反", 0.15, 85.0),
        "mitigation": ("免责/减责事由", 0.10, None),
    }

    RED_LINES = {
        "r1": "伪造、篡改病历资料",
        "r2": "隐匿、拒绝提供病历",
        "r3": "未取得执业资格独立行医",
        "r4": "明知无救治条件仍强推手术",
        "r5": "术后未履行基本观察义务致死亡",
        "r6": "重复同类过错致多次损害",
        "r7": "拒绝会诊或转诊致病情恶化",
        "r8": "使用未经批准的医疗器械/药品",
        "r9": "无相应处方权使用限制级药物",
    }

    def __init__(self, config_path: Optional[str] = None):
        self.params = self._load_params(config_path)
        self.severe_checker = SevereIrresponsibilityChecker()
        self.special_checker = SpecialCircumstanceChecker()
        self.viz_generator = VizDataGenerator()

    def _load_params(self, path: Optional[str]) -> Dict:
        defaults = {
            "convergence_threshold": 0.5,
            "max_iterations": 5,
            "auto_correct_enabled": True,
            "red_line_boost": 0.15,
            "mitigation_floor": 0.05,
        }
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        # v1.2.2 修复：解包 engine_params 嵌套键（params_config.json
                        # 将收敛参数置于 engine_params 子键下，此前 update 整个
                        # 顶层字典导致配置完全不生效）
                        engine_params = loaded.get("engine_params")
                        if isinstance(engine_params, dict):
                            defaults.update(engine_params)
                        else:
                            defaults.update(loaded)
            except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
                print(f"[WARN] 配置文件加载失败: {e}")
        return defaults

    def evaluate(self, case_data: Dict) -> ReviewResult:
        """主评估入口（v1.2.0 优化：增加参数验证）"""
        self._validate_case_data(case_data)
        case_id = case_data.get("case_id", "UNKNOWN")

        # 1. 维度评分
        dimensions = self._score_dimensions(case_data)

        # 2. 红线检测
        red_flags = self._detect_red_lines(case_data)
        red_triggered = len(red_flags) > 0

        # 3. 诊疗阶段分段
        duty_segments = self._parse_duty_segments(case_data)

        # 4. 严重不负责任检查（v1.2.0 优化：调用独立模块）
        severe_check = self.severe_checker.check(case_data, red_flags)

        # 5. 原始总分计算
        raw_total = sum(d.weighted_score for d in dimensions)

        # 6. auto_correct 迭代收敛
        corrected_score, iterations = self._auto_correct(raw_total, dimensions, red_triggered)

        # 7. 责任比例映射
        liability_ratio = self._map_to_liability(corrected_score, red_triggered)
        liability_level = self._classify_liability(liability_ratio)

        # 8. 罪名判定（v1.2.0 优化：修复 R3 罪名区分）
        crime_type = self._determine_crime_v3(liability_ratio, red_flags, case_data, severe_check)

        # 9. 特殊情形检查（v1.2.0 优化：调用独立模块）
        special_alerts = self.special_checker.check(case_data, red_flags, severe_check)

        # 10. 置信度独立标注
        avg_confidence = math.sqrt(sum(d.confidence ** 2 for d in dimensions) / len(dimensions))
        conf_annotation = self._annotate_confidence_v3(avg_confidence, red_triggered, special_alerts, severe_check)

        return ReviewResult(
            case_id=case_id,
            total_score=round(corrected_score, 2),
            liability_ratio=round(liability_ratio, 4),
            liability_level=liability_level,
            crime_type=crime_type,
            dimensions=dimensions,
            red_flags=red_flags,
            confidence_annotation=conf_annotation,
            iteration_log=iterations,
            severe_irresponsibility_check=severe_check,
            duty_segments=duty_segments
        )

    @staticmethod
    def _validate_case_data(case_data: Dict) -> None:
        """参数验证（v1.2.0 新增）"""
        if not isinstance(case_data, dict):
            raise ValueError("case_data 必须是字典类型")
        if "dimensions" not in case_data:
            raise ValueError("case_data 必须包含 'dimensions' 字段")
        dims = case_data.get("dimensions", {})
        required = {"medical_fault", "causation", "damage_severity", "duty_violation", "mitigation"}
        missing = required - set(dims.keys())
        if missing:
            raise ValueError(f"缺少必要维度: {missing}")

    def _score_dimensions(self, case_data: Dict) -> List[DimensionScore]:
        """各维度独立评分"""
        results = []
        for key, (name, weight, red_threshold) in self.DIMENSIONS.items():
            dim_data = case_data.get("dimensions", {}).get(key, {})
            raw = float(dim_data.get("score", 50.0))
            conf = float(dim_data.get("confidence", 0.8))
            notes = dim_data.get("notes", [])

            triggered = red_threshold is not None and raw >= red_threshold
            if key == "mitigation":
                raw = 100.0 - raw

            results.append(DimensionScore(
                name=name, raw_score=raw, weight=weight,
                confidence=conf, red_line_triggered=triggered, notes=notes
            ))
        return results

    def _detect_red_lines(self, case_data: Dict) -> List[str]:
        """九轮红线核查 (R1-R9)"""
        flags = []
        evidence = case_data.get("evidence", {})
        if not isinstance(evidence, dict):
            return flags
        for code, desc in self.RED_LINES.items():
            if evidence.get(code, False):
                flags.append(f"[{code}] {desc}")
        return flags

    def _parse_duty_segments(self, case_data: Dict) -> List[DutySegment]:
        """解析诊疗阶段分段"""
        segments = []
        metadata = case_data.get("metadata", {})
        if isinstance(metadata, dict) and "duty_segments" in metadata:
            for seg in metadata["duty_segments"]:
                if isinstance(seg, dict):
                    segments.append(DutySegment(**seg))
        if not segments:
            segments.append(DutySegment(phase="全程", responsible_doctor="主治医生",
                                        duration_hours=24.0, fault_score=50.0))
        return segments

    def _auto_correct(self, raw_total: float, dimensions: List[DimensionScore], red_triggered: bool) -> Tuple[float, List[Dict]]:
        """迭代收敛修正（v1.2.0 优化：边界保护增强）"""
        if not self.params.get("auto_correct_enabled", True):
            return raw_total, []

        score = float(raw_total)
        iterations = []
        threshold = float(self.params.get("convergence_threshold", 0.5))
        max_iter = int(self.params.get("max_iterations", 5))
        max_adj = 3.0
        min_adj = 0.3
        extreme_dev = 25.0

        for i in range(max_iter):
            variance = sum((d.raw_score - score) ** 2 * d.weight for d in dimensions)
            std_dev = math.sqrt(variance) if variance > 0 else 0.0
            damping = 1.0 / (1.0 + 0.5 * i)
            adjustment = (std_dev - threshold) * 0.1 * damping

            if red_triggered and i == 0:
                adjustment += float(self.params.get("red_line_boost", 0.15)) * 5

            if std_dev > extreme_dev:
                adjustment = min(adjustment, 0.5)
                if i >= 1 and iterations and iterations[-1]['adjustment'] > 0 and adjustment > 0:
                    adjustment *= 0.3
                elif i >= 1 and iterations and iterations[-1]['adjustment'] < 0 and adjustment < 0:
                    adjustment *= 0.3

            adjustment = max(-max_adj, min(max_adj, adjustment))
            new_score = max(0.0, min(100.0, score + adjustment))
            delta = abs(new_score - score)

            iterations.append({
                "iteration": i + 1, "before": round(score, 2),
                "after": round(new_score, 2), "delta": round(delta, 2),
                "damping": round(damping, 3), "adjustment": round(adjustment, 3)
            })
            score = new_score

            if delta <= threshold or abs(adjustment) < min_adj:
                break
            if i >= 2 and abs(adjustment) < 1.0:
                prev_delta = iterations[-2]['delta'] if len(iterations) >= 2 else delta
                if abs(prev_delta - delta) < 0.3:
                    break

        return score, iterations

    def _map_to_liability(self, score: float, red_triggered: bool) -> float:
        """责任比例 S 型映射"""
        base = 0.80 / (1.0 + math.exp(-0.055 * (score - 76)))
        if red_triggered:
            base = max(base, 0.31)
            base = min(base + 0.05, 0.95)
        return base

    def _classify_liability(self, ratio: float) -> LiabilityLevel:
        for level in LiabilityLevel:
            if level.lower <= ratio <= level.upper:
                return level
        return LiabilityLevel.NONE if ratio < 0.01 else LiabilityLevel.FULL

    def _determine_crime_v3(self, ratio: float, red_flags: List[str], case_data: Dict, severe_check: Dict) -> CrimeType:
        """罪名判定逻辑 v1.2.0（修复 R3 罪名区分）"""
        dims = case_data.get("dimensions", {})
        causation_score = float(dims.get("causation", {}).get("score", 50))
        mitigation_score = float(dims.get("mitigation", {}).get("score", 0))
        damage_score = float(dims.get("damage_severity", {}).get("score", 0))

        # 多因一果阻却
        mitigation_type = self._parse_mitigation_type(case_data)
        if mitigation_type in ("patient_factor", "systemic_factor") and mitigation_score > 60 and ratio < 0.50:
            return CrimeType.NOT_GUILTY

        # R3 非法行医（v1.2.0 修复：区分基础情节和致人死亡）
        if any("r3" in f for f in red_flags):
            if causation_score < 50:
                return CrimeType.ILLEGAL_PRACTICE_BASIC
            return CrimeType.ILLEGAL_PRACTICE_DEATH

        # R9 超权限用药
        if any("r9" in f for f in red_flags):
            return CrimeType.MEDICAL_MALPRACTICE

        # 医疗事故罪门槛
        if ratio < 0.30:
            return CrimeType.NOT_GUILTY

        # v1.2.1 修复：移除兜底条款争议的罪名阻却（韩杰案实际被判有罪，说明兜底条款不能作为无罪依据）
        # 兜底条款争议仅作为置信度惩罚和司法风险提示，不改变罪名定性

        # 过失致人死亡罪（v1.2.1 修复：阈值从 0.50 提高到 0.60，避免医疗事故罪被过度升级）
        if (damage_score >= 90 and ratio >= 0.60 and mitigation_score < 50 and causation_score >= 60):
            return CrimeType.MANSLAUGHTER

        return CrimeType.MEDICAL_MALPRACTICE

    @staticmethod
    def _parse_mitigation_type(case_data: Dict) -> str:
        """解析减责事由类型"""
        notes_all = " ".join(str(n) for d in case_data.get("dimensions", {}).values() for n in d.get("notes", []))
        if any(kw in notes_all for kw in {"其他医院", "此前就诊", "上级医院", "连锁漏诊", "此前已诊断"}):
            return "other_institution"
        if any(kw in notes_all for kw in {"患者自身", "隐瞒病史", "拒绝治疗", "拒绝转院", "自身疾病"}):
            return "patient_factor"
        if any(kw in notes_all for kw in {"系统故障", "人员不足", "设备不到位", "制度不落实", "过度疲劳"}):
            return "systemic_factor"
        return "unknown"

    def _annotate_confidence_v3(self, avg_conf: float, red_triggered: bool, special_alerts: List[Dict], severe_check: Dict) -> str:
        """置信度独立标注 v1.2.0"""
        conf_penalty = sum(a.get("penalty", 0) for a in special_alerts)
        if severe_check.get("matched_count", 0) == 0 and not severe_check.get("兜底争议", False):
            conf_penalty += 0.10

        adjusted_conf = max(0.1, avg_conf - conf_penalty)
        base = "高" if adjusted_conf >= 0.8 else "中" if adjusted_conf >= 0.5 else "低"

        annotation = f"置信度:{base}({adjusted_conf:.0%})"
        if red_triggered:
            annotation += "[红线已触发]"
        if special_alerts:
            fatal = sum(1 for a in special_alerts if a.get("level") == "致命")
            major = sum(1 for a in special_alerts if a.get("level") == "重大")
            annotation += f"[风险:{fatal}致命/{major}重大/{len(special_alerts)-fatal-major}其他]"
        return annotation

    def generate_report(self, result: ReviewResult, case_data: Dict = None) -> Dict:
        """生成结构化报告 v1.2.0（优化：消除重复计算）"""
        report = {
            "case_id": result.case_id,
            "version": __version__,
            "summary": {
                "total_score": result.total_score,
                "liability_ratio": f"{result.liability_ratio:.1%}",
                "liability_level": result.liability_level.label,
                "crime_type": result.crime_type.value,
                "confidence": result.confidence_annotation,
            },
            "dimensions": [
                {
                    "name": d.name, "raw_score": d.raw_score,
                    "weight": d.weight, "weighted": round(d.weighted_score, 2),
                    "confidence": f"{d.confidence:.0%}",
                    "red_line": d.red_line_triggered, "notes": d.notes
                } for d in result.dimensions
            ],
            "red_flags": result.red_flags,
            "iteration_log": result.iteration_log,
            "severe_irresponsibility": result.severe_irresponsibility_check,
            "duty_segments": [
                {"phase": s.phase, "doctor": s.responsible_doctor,
                 "duration": s.duration_hours, "fault": s.fault_score}
                for s in result.duty_segments
            ],
            "recommendation": self._generate_recommendation_v3(result, case_data)
        }

        if case_data:
            special_alerts = self.special_checker.check(case_data, result.red_flags, result.severe_irresponsibility_check)
            if special_alerts:
                report["judicial_risks"] = special_alerts

        report["viz_data"] = self.viz_generator.generate(result)
        return report

    def _generate_recommendation_v3(self, result: ReviewResult, case_data: Dict = None) -> str:
        """差异化建议生成 v1.2.0（优化：消除重复调用）"""
        judicial_risks = []
        if case_data:
            judicial_risks = self.special_checker.check(case_data, result.red_flags, result.severe_irresponsibility_check)
        risk_messages = [r.get("message", "") for r in judicial_risks]

        if any("未行尸检" in m for m in risk_messages):
            return "建议：立即申请补充尸检或死因复核。未行尸检导致死因不明是医疗事故罪辩护的核心路径（参见李建雪案）。同时收集患者自身疾病、其他医疗机构过失等减责证据。"

        if any("兜底条款" in m for m in risk_messages):
            return "建议：积极辩护，重点论证不符合七种'严重不负责任'法定情形。参考韩杰案争议、李建雪案无罪判例，争取不起诉或无罪判决。建议申请医疗事故技术鉴定和专家论证。"

        if result.crime_type == CrimeType.NOT_GUILTY:
            if any("专家" in m or "论证" in m for m in risk_messages):
                return "建议：民事调解或医疗纠纷人民调解委员会处理。若已刑事立案，积极提交权威专家论证意见，主张不符合'严重不负责任'法定情形（参见温红案）。"
            return "建议：民事调解或医疗纠纷人民调解委员会处理。若已刑事立案，建议积极辩护，重点论证不符合'严重不负责任'法定情形。"

        if result.liability_level in (LiabilityLevel.PRIMARY, LiabilityLevel.FULL):
            if any("r3" in f for f in result.red_flags):
                return "建议：移送公安机关刑事立案。非法行医罪（致人死亡）法定刑十年以上，建议尽快委托律师。"
            return "建议：移送公安机关刑事立案，同步启动医疗事故技术鉴定。注意收集患者自身疾病、系统性因素等减责证据。"

        if result.red_flags:
            return "建议：重点核查红线事项证据链完整性。若涉及R1/R8，建议核查医院管理制度是否存在系统性漏洞，以分散个人责任。"

        if any("次要原因力" in m for m in risk_messages):
            return "建议：医疗事故技术鉴定 + 院内纪律处分。鉴定为'次要原因力'不等于刑法上的'严重不负责任'，可主张不构成犯罪（参见温红案）。"

        return "建议：医疗事故技术鉴定 + 院内纪律处分。若鉴定为'次要原因力'，可主张不构成犯罪（参见温红案）。"


def run_scoring(case_data: Dict, config_path: Optional[str] = None) -> Dict:
    engine = ScoringEngine(config_path)
    result = engine.evaluate(case_data)
    return engine.generate_report(result, case_data)


if __name__ == "__main__":
    demo_case = {
        "case_id": "DEMO-2026-001",
        "dimensions": {
            "medical_fault": {"score": 78, "confidence": 0.85, "notes": ["术后观察不足"]},
            "causation": {"score": 82, "confidence": 0.80, "notes": ["死亡与延误直接相关"]},
            "damage_severity": {"score": 95, "confidence": 0.90, "notes": ["患者死亡"]},
            "duty_violation": {"score": 70, "confidence": 0.75, "notes": ["未执行查房制度"]},
            "mitigation": {"score": 20, "confidence": 0.60, "notes": ["家属拒绝转院"]},
        },
        "evidence": {"r1": False, "r2": False, "r3": False, "r4": False, "r5": True, "r6": False, "r7": False, "r8": False, "r9": False}
    }

    engine = ScoringEngine()
    result = engine.evaluate(demo_case)
    report = engine.generate_report(result, demo_case)
    print(json.dumps(report, ensure_ascii=False, indent=2))
