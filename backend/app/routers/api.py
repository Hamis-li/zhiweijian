"""REST 路由 + SSE 实时推送 + RAG 案例检索 + 真实气象代理。"""
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import urllib.request, urllib.parse, json as _json

from ..models.schemas import AlertEvent, CaseCard, RegionMetric, RiskAssessment
from ..services import engine, live, rag
from ..data import sample_data

router = APIRouter(prefix="/api", tags=["zhiweijian"])

# 应用启动时构建案例 RAG 向量库
_rag = rag.build_rag(sample_data.CASES)


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "zhiweijian-api", "version": "1.1.0"}


# --------------------------- 案例知识卡片（向量 RAG） ---------------------------
@router.get("/cases", response_model=list[CaseCard])
def list_cases(keyword: str = Query("", description="灾害关键词"),
               top_k: int = Query(3, ge=1, le=20)) -> list[CaseCard]:
    """关键词检索案例（保留原 Coze 知识卡片核心能力）。"""
    return engine.case_query(sample_data.CASES, keyword, top_k)


@router.get("/cases/rag")
def rag_search(keyword: str = Query("", description="支持多词/近义，如 瓦斯 煤矿 爆炸"),
               top_k: int = Query(3, ge=1, le=10)) -> list[dict]:
    """TF-IDF 余弦相似度检索，返回带相似度分。"""
    return [{"case": c, "similarity": s} for s, c in _rag.search(keyword, top_k)]


@router.get("/cases/report")
def rag_report(keyword: str = Query("爆炸"), hazard: str = "flood",
               region: str = "演示区域") -> dict:
    """AI 复盘/分析报告（RAG 命中 + 风险评估 + 处置建议，模板生成，可替换大模型）。"""
    risk = engine.risk_identify(hazard, region, {"hazard_intensity": 70, "exposure": 60})
    return _rag.report(keyword, risk)


# --------------------------- 监测与预警 ---------------------------
@router.get("/monitor/metrics", response_model=list[RegionMetric])
def list_metrics() -> list[RegionMetric]:
    return sample_data.METRICS


@router.get("/monitor/alerts", response_model=list[AlertEvent])
def list_alerts() -> list[AlertEvent]:
    """基于当前指标与规则实时匹配的预警事件。"""
    return engine.match_alerts(sample_data.METRICS, sample_data.RULES)


@router.get("/monitor/rules", response_model=list[dict])
def list_rules() -> list[dict]:
    return [r.model_dump() for r in sample_data.RULES]


@router.get("/monitor/live", response_class=StreamingResponse)
async def live_feed() -> StreamingResponse:
    """SSE 实时跳动：每 1.5s 推送一次指标随机游走 + 触发预警。"""
    return StreamingResponse(live.sse_stream(), media_type="text/event-stream")


# --------------------------- 风险识别 ---------------------------
class RiskReq(BaseModel):
    hazard: str = "flood"
    region: str = "演示区域"
    signals: dict[str, float] = Field(default_factory=dict)   # 维度 -> 0-100
    drivers: list[str] = Field(default_factory=list)


@router.post("/risk", response_model=RiskAssessment)
def risk(req: RiskReq) -> RiskAssessment:
    """
    入参: {hazard, region, signals: {维度: 0-100}, drivers: []}
    返回带等级、维度明细与处置建议的风险评估。
    """
    return engine.risk_identify(
        hazard=req.hazard,
        region=req.region,
        signals=req.signals,
        drivers=req.drivers or None,
    )


# --------------------------- 真实气象（Open-Meteo 代理） ---------------------------
@router.get("/weather")
def weather(lat: float = Query(39.9), lon: float = Query(116.4), city: str = "") -> dict:
    """真实气象代理：lat/lon → 当前温度/风速/降水。前端可据此替换演示 rainfall/wind。"""
    import time
    q = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon,
        "current": "temperature_2m,wind_speed_10m,precipitation",
        "timezone": "auto",
    })
    last_err = ""
    for _ in range(3):  # 重试 3 次，抵御偶发超时
        try:
            with urllib.request.urlopen(f"https://api.open-meteo.com/v1/forecast?{q}", timeout=8) as r:
                data = _json.loads(r.read().decode("utf-8"))
            cur = data.get("current", {})
            return {"source": "open-meteo", "available": True, "city": city,
                    "latitude": lat, "longitude": lon,
                    "temperature_2m": cur.get("temperature_2m"),
                    "wind_speed_10m": cur.get("wind_speed_10m"),
                    "precipitation": cur.get("precipitation"),
                    "time": cur.get("time")}
        except Exception as e:
            last_err = str(e)
            time.sleep(0.6)
    return {"source": "open-meteo", "available": False, "city": city, "error": last_err}
