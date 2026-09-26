#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Medical Malpractice Criminal Review — Batch Case Comparison
Version: 1.2.0
Last Updated: 2026-08-23

批量案件对比模块：支持同时输入2+案件，输出对比报告、相似度分析、趋势统计。
"""

import json
import math
from typing import Dict, List
from scoring_engine import ScoringEngine, __version__ as ENGINE_VERSION


class BatchComparator:
    """批量案件对比器 v1.2.0"""

    def __init__(self, config_path=None):
        self.engine = ScoringEngine(config_path)

    def compare(self, cases: List[Dict]) -> Dict:
        """批量对比入口"""
        if len(cases) < 2:
            return {"error": "至少需要2个案件进行对比"}

        # 逐案评分
        results = []
        for case in cases:
            result = self.engine.evaluate(case)
            report = self.engine.generate_report(result, case)
            results.append(report)

        # 生成对比报告
        return {
            "version": ENGINE_VERSION,  # v1.2.2: 版本号单一来源 scoring_engine.__version__
            "case_count": len(cases),
            "cases": results,
            "comparison": self._generate_comparison(results),
            "trends": self._analyze_trends(results),
            "similarity_matrix": self._calculate_similarity(results)
        }

    def _generate_comparison(self, results: List[Dict]) -> Dict:
        """生成横向对比表"""
        return {
            "total_score_ranking": sorted(
                [(r["case_id"], r["summary"]["total_score"]) for r in results],
                key=lambda x: x[1], reverse=True
            ),
            "liability_ratio_ranking": sorted(
                [(r["case_id"], float(r["summary"]["liability_ratio"].rstrip("%"))) for r in results],
                key=lambda x: x[1], reverse=True
            ),
            "crime_type_distribution": self._count_crime_types(results),
            "red_flags_summary": self._summarize_red_flags(results),
            "judicial_risks_summary": self._summarize_judicial_risks(results)
        }

    def _count_crime_types(self, results: List[Dict]) -> Dict:
        """统计罪名分布"""
        distribution = {}
        for r in results:
            ct = r["summary"]["crime_type"]
            distribution[ct] = distribution.get(ct, 0) + 1
        return distribution

    def _summarize_red_flags(self, results: List[Dict]) -> Dict:
        """汇总红线触发情况"""
        all_flags = {}
        for r in results:
            for flag in r.get("red_flags", []):
                all_flags[flag] = all_flags.get(flag, 0) + 1
        return all_flags

    def _summarize_judicial_risks(self, results: List[Dict]) -> Dict:
        """汇总司法风险"""
        risk_levels = {"致命": 0, "重大": 0, "一般": 0, "参考": 0}
        for r in results:
            for risk in r.get("judicial_risks", []):
                level = risk.get("level", "参考")
                risk_levels[level] = risk_levels.get(level, 0) + 1
        return risk_levels

    def _analyze_trends(self, results: List[Dict]) -> Dict:
        """趋势分析"""
        scores = [r["summary"]["total_score"] for r in results]
        ratios = [float(r["summary"]["liability_ratio"].rstrip("%")) for r in results]

        return {
            "total_score": {
                "max": max(scores), "min": min(scores),
                "avg": round(sum(scores) / len(scores), 2),
                "range": round(max(scores) - min(scores), 2)
            },
            "liability_ratio": {
                "max": max(ratios), "min": min(ratios),
                "avg": round(sum(ratios) / len(ratios), 2),
                "range": round(max(ratios) - min(ratios), 2)
            },
            "convergence_rate": sum(1 for r in results if len(r.get("iteration_log", [])) <= 3) / len(results)
        }

    def _calculate_similarity(self, results: List[Dict]) -> List[List[float]]:
        """计算案件相似度矩阵（基于维度评分欧氏距离）"""
        n = len(results)
        matrix = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i][j] = 1.0
                else:
                    # 提取维度原始分
                    dims_i = {d["name"]: d["raw_score"] for d in results[i]["dimensions"]}
                    dims_j = {d["name"]: d["raw_score"] for d in results[j]["dimensions"]}

                    # 计算欧氏距离
                    distance = math.sqrt(
                        sum((dims_i.get(k, 50) - dims_j.get(k, 50)) ** 2 for k in set(dims_i) | set(dims_j))
                    )
                    # 转换为相似度 (0-1)
                    similarity = max(0, 1 - distance / 100)
                    matrix[i][j] = round(similarity, 2)

        return matrix


def run_batch_comparison(cases: List[Dict], config_path=None) -> Dict:
    comparator = BatchComparator(config_path)
    return comparator.compare(cases)


if __name__ == "__main__":
    # 批量对比验证：韩杰案 vs 李建雪案 vs 温红案
    cases = [
        {
            "case_id": "韩杰案",
            "metadata": {"experience_months": 4},
            "dimensions": {
                "medical_fault": {"score": 65, "confidence": 0.75, "notes": ["漏诊嵌顿性腹股沟斜疝，未行腹股沟查体", "患儿此前已在其他医院就诊，存在连锁漏诊"]},
                "causation": {"score": 75, "confidence": 0.80, "notes": ["漏诊与死亡存在直接因果关系，参与度85-95%"]},
                "damage_severity": {"score": 95, "confidence": 0.95, "notes": ["死亡"]},
                "duty_violation": {"score": 50, "confidence": 0.65, "notes": ["未请外科会诊，但无擅离职守"]},
                "mitigation": {"score": 25, "confidence": 0.60, "notes": ["患儿此前已在其他医院就诊，存在连锁漏诊"]}
            },
            "evidence": {"r1": False, "r2": False, "r3": False, "r4": False, "r5": False, "r6": False, "r7": False, "r8": False, "r9": False}
        },
        {
            "case_id": "李建雪案",
            "dimensions": {
                "medical_fault": {"score": 60, "confidence": 0.60, "notes": ["产后出血处理不及时，但存在争议"]},
                "causation": {"score": 50, "confidence": 0.50, "notes": ["未做尸检，死因不明，因果关系无法锁定"]},
                "damage_severity": {"score": 95, "confidence": 0.95, "notes": ["死亡"]},
                "duty_violation": {"score": 45, "confidence": 0.55, "notes": ["值班处理存在疏忽，但未达严重不负责任"]},
                "mitigation": {"score": 40, "confidence": 0.70, "notes": ["医院已赔偿150万，多因一果（羊水栓塞等可能）"]}
            },
            "evidence": {"r1": False, "r2": False, "r3": False, "r4": False, "r5": False, "r6": False, "r7": False, "r8": False, "r9": False}
        },
        {
            "case_id": "温红案",
            "dimensions": {
                "medical_fault": {"score": 55, "confidence": 0.65, "notes": ["化疗方案调整存在争议"]},
                "causation": {"score": 40, "confidence": 0.50, "notes": ["次要原因力，非直接主要原因"]},
                "damage_severity": {"score": 95, "confidence": 0.95, "notes": ["死亡"]},
                "duty_violation": {"score": 35, "confidence": 0.60, "notes": ["未严重违反诊疗规范"]},
                "mitigation": {"score": 60, "confidence": 0.85, "notes": ["权威专家论证支持无罪，治疗方案符合常规"]}
            },
            "evidence": {"r1": False, "r2": False, "r3": False, "r4": False, "r5": False, "r6": False, "r7": False, "r8": False, "r9": False}
        }
    ]

    result = run_batch_comparison(cases)
    print(json.dumps(result["comparison"], ensure_ascii=False, indent=2))
