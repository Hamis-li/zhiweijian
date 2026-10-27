"""Pydantic 数据模型（Pydantic v2）。

知危鉴 升级版的统一契约层。
所有接口请求/响应体、风险指标、预警等级都在此定义，
保证前后端字段一致，便于后续接入真实数据源时平滑替换。
"""
from enum import IntEnum
from typing import List, Optional
from pydantic import BaseModel, Field


class AlertLevel(IntEnum):
    """四级预警：蓝(Ⅳ)→黄(Ⅲ)→橙(Ⅱ)→红(Ⅰ)，数值越大越严重。"""
    BLUE = 1   # 蓝色 Ⅳ 一般
    YELLOW = 2  # 黄色 Ⅲ 较大
    ORANGE = 3  # 橙色 Ⅱ 重大
    RED = 4     # 红色 Ⅰ 特别重大

    @property
    def name_cn(self) -> str:
        return {1: "蓝色", 2: "黄色", 3: "橙色", 4: "红色"}[int(self)]

    @property
    def hex(self) -> str:
        """前端着色用（中国预警配色：蓝→黄→橙→红）。"""
        return {1: "#1E6FD9", 2: "#F5C518", 3: "#F07C24", 4: "#D6261F"}[int(self)]


class RiskDimension(BaseModel):
    """单一风险维度指标。"""
    key: str
    label: str
    value: float
    weight: float = 0.0
    desc: str = ""


class RiskAssessment(BaseModel):
    """对某区域/某类灾害的风险识别结果。"""
    hazard: str                       # 灾害类型：flood/geology/fire/storm...
    hazard_cn: str
    region: str
    score: float = 0.0                # 0-100 综合风险指数
    level: AlertLevel = AlertLevel.BLUE
    dims: List[RiskDimension] = []
    drivers: List[str] = Field(default_factory=list)   # 主要致灾驱动因素
    suggested: str = ""               # 处置/防范建议


class AlertRule(BaseModel):
    """可配置的预警阈值规则。"""
    id: str
    name: str
    hazard: str
    metric: str                       # 监测指标名
    threshold: float
    op: str = ">="                    # >= / > / <= / between
    upper: Optional[float] = None
    triggers: AlertLevel = AlertLevel.YELLOW
    enabled: bool = True
    desc: str = ""


class AlertEvent(BaseModel):
    """一条已触发的预警事件。"""
    id: str
    rule_id: str
    rule_name: str
    hazard: str
    region: str
    metric: str
    value: float
    threshold: float
    level: AlertLevel
    ts: str = "2026-10-25T00:00:00+08:00"
    status: str = "active"            # active / resolved


class CaseCard(BaseModel):
    """标准化灾害案例知识卡片（保留原 Coze 核心能力）。"""
    case_id: str
    title: str
    date: str
    location: str
    level: str                        # 事故等级
    summary: str                      # 事件概况
    risk_factors: List[str] = Field(default_factory=list)   # 风险因素
    measures: List[str] = Field(default_factory=list)        # 应急处置措施
    lessons: List[str] = Field(default_factory=list)         # 经验教训
    tags: List[str] = Field(default_factory=list)
    source: str = ""


class TrendPoint(BaseModel):
    """时序指标点。"""
    ts: str
    value: float


class RegionMetric(BaseModel):
    """区域级监测指标（看板用）。"""
    region: str
    hazard: str
    metric: str
    value: float
    unit: str = ""
    trend: List[TrendPoint] = Field(default_factory=list)
    status: str = "normal"            # normal / warning / danger
