"""向量 RAG 案例检索 + AI 分析报告生成。

- 检索：TF-IDF 向量化 + 余弦相似度（scikit-learn，纯 CPU，无 GPU 亦可跑）。
  相比原"子串匹配"，支持"瓦斯/煤矿"等多词、同义近义命中，召回更稳。
- 报告：基于检索结果 + 风险评估自动装配结构化事故分析/复盘报告（模板生成，
  可平滑替换为大模型生成；字段稳定便于前端直接渲染）。
"""
from typing import List
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from ..models.schemas import CaseCard, RiskAssessment


class CaseRAG:
    """轻量向量案例库：对案例做 TF-IDF 向量化，支持相似度检索。"""

    def __init__(self, cases: List[CaseCard]):
        self._cases = cases
        self._ids = [c.case_id for c in cases]
        # 拼接多字段提升召回
        self._texts = [self._doc_text(c) for c in cases]
        self._vec = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b", lowercase=False)
        self._mat = self._vec.fit_transform(self._texts)

    @staticmethod
    def _doc_text(c: CaseCard) -> str:
        return " ".join(
            [c.title, c.location, c.level, c.summary,
             " ".join(c.risk_factors), " ".join(c.measures),
             " ".join(c.lessons), " ".join(c.tags)]
        )

    def search(self, query: str, top_k: int = 3, min_score: float = 0.0) -> List[tuple]:
        """返回 [(score, CaseCard), ...]，按相似度降序。"""
        if not query.strip():
            return [(1.0, c) for c in self._cases[:top_k]]
        qv = self._vec.transform([query])
        scores = (self._mat @ qv.T).toarray().ravel()
        idx = np.argsort(scores)[::-1][:top_k]
        return [(round(float(scores[i]), 3), self._cases[i]) for i in idx if scores[i] > min_score]

    def report(self, query: str, risk: RiskAssessment | None = None, top_k: int = 3) -> dict:
        """生成结构化复盘/分析报告（模板；可替换为大模型生成）。"""
        results = self.search(query, top_k)
        top_score, top = (results[0] if results else (0, None))
        hits = [
            {"title": c.title, "similarity": s, "level": c.level,
             "lessons": c.lessons, "measures": c.measures}
            for s, c in results
        ]
        return {
            "query": query,
            "generated": True,
            "engine": "TF-IDF cosine + 模板装配（可替换为大模型）",
            "headline": (
                f"围绕「{query}」共命中 {len(hits)} 条高相关案例；"
                f"最相似为《{top.title if top else '无'}》（相似度 {top_score}）。"
            ),
            "risk": {
                "hazard": risk.hazard, "region": risk.region, "score": risk.score,
                "level": int(risk.level), "suggested": risk.suggested,
            } if risk else None,
            "hits": hits,
            "key_actions": self._actions(hits, risk),
            "notes": "报告由检索 + 模板自动装配生成，正式场景可接入大模型生成自然语言。",
        }

    @staticmethod
    def _actions(hits: List[dict], risk: RiskAssessment | None) -> List[str]:
        acts: List[str] = []
        for h in hits[:2]:
            for m in h["measures"][:2]:
                acts.append(m)
        if risk and risk.suggested:
            acts.append("【当前风险】" + risk.suggested)
        return acts[:6] or ["建议完善案例与规则库后重评。"]


# 模块级单例（由路由注入 CASES）
_rag: CaseRAG | None = None


def build_rag(cases: List[CaseCard]) -> CaseRAG:
    global _rag
    _rag = CaseRAG(cases)
    return _rag


def get_rag() -> CaseRAG:
    return _rag
