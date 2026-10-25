"""风险识别 + 预警规则引擎。

这是「知危鉴」相对原 Coze 纯问答智能体的核心升级：
- risk_identify():  多维度加权法计算综合风险指数 → 定级
- match_alerts():  监测指标对预警规则做阈值匹配 → 产出预警事件
- case_query():     案例关键词检索（保留原知识卡片能力，内置样例库可替换为 RAG）

设计为"纯函数 + 内存数据"，无外部依赖，可一键跑通；
接入真实数据源（数据库/流式监测）时只需替换 data/ 下的数据模块。
"""
from typing import Dict, List, Tuple
from ..models.schemas import (
    AlertEvent, AlertLevel, AlertRule, CaseCard, RegionMetric,
    RiskAssessment, RiskDimension,
)

# ---------------------------------------------------------------------------
# 风险维度权重（可按灾害类型覆写）。值越大风险越高。
# ---------------------------------------------------------------------------
_WEIGHTS = {
    "flood": {"exposure": 0.35, "hazard_intensity": 0.40, "preparedness": 0.15, "vulnerability": 0.10},
    "geology": {"exposure": 0.25, "hazard_intensity": 0.45, "slope": 0.15, "preparedness": 0.15},
    "fire": {"exposure": 0.20, "hazard_intensity": 0.35, "dryness": 0.25, "preparedness": 0.20},
}

_LEVEL_THRESHOLDS = [(80, AlertLevel.RED), (60, AlertLevel.ORANGE), (40, AlertLevel.YELLOW), (0, AlertLevel.BLUE)]


def risk_identify(hazard: str, region: str, signals: Dict[str, float],
                  drivers: List[str] | None = None) -> RiskAssessment:
    """signals: 各维度 0-100 分值。返回带等级与维度的风险评估。"""
    weights = _WEIGHTS.get(hazard, _WEIGHTS["flood"])
    dims: List[RiskDimension] = []
    total = 0.0
    wsum = 0.0
    label_map = {
        "exposure": "暴露度", "hazard_intensity": "致灾强度", "preparedness": "防灾准备度",
        "vulnerability": "承灾脆弱性", "slope": "地形坡度", "dryness": "干燥度",
    }
    for key, w in weights.items():
        val = float(signals.get(key, 0.0))
        total += val * w
        wsum += w
        dims.append(RiskDimension(key=key, label=label_map.get(key, key), value=round(val, 1), weight=w))
    score = round(total / wsum, 1) if wsum else 0.0
    level = _level_of(score)
    hz_cn = {"flood": "洪涝", "geology": "地质灾害", "fire": "火灾", "storm": "台风"}[hazard]
    return RiskAssessment(
        hazard=hazard, hazard_cn=hz_cn, region=region, score=score, level=level,
        dims=dims, drivers=drivers or [],
        suggested=_suggestion(hazard, level),
    )


def _level_of(score: float) -> AlertLevel:
    for th, lv in _LEVEL_THRESHOLDS:
        if score >= th:
            return lv
    return AlertLevel.BLUE


def _suggestion(hazard: str, level: AlertLevel) -> str:
    base = {
        "flood": "加密水文监测、预置转移路线与避灾点、检查排涝设备、低洼区域预警转移",
        "geology": "开展山坡体巡查、警戒地质灾害隐患点、雨季停工与临危人员撤离预案",
        "fire": "清理可燃物、排查电气与动火作业、预置灭火器材、管控火源与隔离带",
        "storm": "加固临时设施、停工停运、沿海居民转移、关注风暴潮与强降雨次生灾害",
    }[hazard]
    return base + ("；已达最高响应级别，建议启动应急预案并联动外部救援力量。" if level >= AlertLevel.RED else "")


# ---------------------------------------------------------------------------
# 预警规则匹配
# ---------------------------------------------------------------------------
def match_alerts(metrics: List[RegionMetric], rules: List[AlertRule]) -> List[AlertEvent]:
    """逐条指标 × 逐条规则匹配，命中则产出预警事件。"""
    events: List[AlertEvent] = []
    for m in metrics:
        for r in rules:
            if not r.enabled or r.hazard != m.hazard:
                continue
            if _hit(m.value, r) and m.metric == r.metric:
                events.append(AlertEvent(
                    id=f"evt_{m.region}_{m.metric}", rule_id=r.id, rule_name=r.name,
                    hazard=m.hazard, region=m.region, metric=m.metric,
                    value=m.value, threshold=r.threshold, level=r.triggers,
                    status="active",
                ))
    return events


def _hit(value: float, r: AlertRule) -> bool:
    if r.op == ">=":
        return value >= r.threshold
    if r.op == ">":
        return value > r.threshold
    if r.op == "<=":
        return value <= r.threshold
    if r.op == "<":
        return value < r.threshold
    if r.op == "between":
        return (r.threshold <= value) and (r.upper is not None and value <= r.upper)
    return False


# ---------------------------------------------------------------------------
# 案例检索（知识卡片核心，样本可替换为向量 RAG）
# ---------------------------------------------------------------------------
def case_query(cases: List[CaseCard], keyword: str, top_k: int = 3) -> List[CaseCard]:
    """基于关键词命中案例的简单评分（标题/标签/概况/措施/教训加权）。"""
    if not keyword.strip():
        return cases[:top_k]
    k = keyword.lower()
    scored: List[Tuple[float, CaseCard]] = []
    for c in cases:
        s = 0.0
        hay = (c.title + " " + " ".join(c.tags) + " " + c.summary).lower()
        if k in c.title.lower():
            s += 5
        if k in " ".join(c.tags).lower():
            s += 4
        if k in c.summary.lower():
            s += 3
        for d in c.risk_factors + c.measures + c.lessons:
            if k in d.lower():
                s += 1
        if k in hay:
            s += 2
        if s > 0:
            scored.append((s, c))
    scored.sort(key=lambda x: -x[0])
    return [c for _, c in scored[:top_k]]
