"""实时推送：SSE 流 + 模拟实时监测数据生成器。

真实现里可接气象/地质实时源；此处用"当前值 + 随机游走"生成
一个持续跳动的实时流，便于前端演示"实时跳动 + 预警触发"。
"""
import asyncio, json, random, time
from typing import AsyncIterator

from ..data import sample_data
from . import engine


def _step(metric: str, cur: float) -> float:
    """模拟一次实时读数：围绕阈值做随机游走，便于触发预警。"""
    base = {"rainfall_24h": 70, "slope_displacement": 6,
            "fire_risk_index": 50, "wind_speed": 18}.get(metric, 10)
    return max(0, min(150, cur + random.uniform(-3, 5)))


async def live_stream() -> AsyncIterator[str]:
    """SSE 事件流：每 ~2s 推一帧 {metrics, alerts}。"""
    current = {m.region + m.hazard + m.metric: m.value for m in sample_data.METRICS}
    n = 0
    while True:
        n += 1
        for m in sample_data.METRICS:
            key = m.region + m.hazard + m.metric
            current[key] = _step(m.metric, current.get(key, m.value))
        metrics_now = []
        for m in sample_data.METRICS:
            key = m.region + m.hazard + m.metric
            t = m.trend + [{"ts": f"t{n}", "value": round(current.get(key, m.value), 1)}]
            metrics_now.append(m.model_copy(update={"value": round(current.get(key, m.value), 1), "trend": t}))
        alerts = engine.match_alerts(metrics_now, sample_data.RULES)
        payload = {
            "ts": n,
            "metrics": [
                {"region": m.region, "hazard": m.hazard, "metric": m.metric,
                 "value": m.value, "unit": m.unit} for m in metrics_now
            ],
            "alerts": [
                {"id": a.id, "region": a.region, "hazard": a.hazard, "metric": a.metric,
                 "value": a.value, "threshold": a.threshold, "level": int(a.level),
                 "rule_name": a.rule_name, "ts": time.strftime("%H:%M:%S")}
                for a in alerts
            ],
        }
        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        await asyncio.sleep(2)
