# 知危鉴 · 知灾析策 API

Base URL: `http://127.0.0.1:8000`（本地）/ 部署域名为 Base
交互文档: `/docs` · OpenAPI: `/openapi.json`

## 通用说明
- 认证：本地演示默认开放；生产走网关 JWT。
- 数据：当前为内置样例；接真实数据源后接口契约不变。

## 接口

### GET /api/health
返回 `{"status":"ok","service":"zhiweijian-api","version":"1.0.0"}`

### GET /api/cases?keyword=&top_k=
按关键词检索案例知识卡片。
- `keyword`（可选）：灾害关键词，如 `瓦斯`/`爆炸`/`化工`。
- `top_k`（可选，1–20，默认 3）。
返回 `CaseCard[]`：`case_id/title/date/location/level/summary/risk_factors/measures/lessons/tags/source`。

### GET /api/monitor/metrics
返回 `RegionMetric[]`：`region/hazard/metric/value/unit/trend[]/status`。

### GET /api/monitor/rules
返回预警规则列表：`id/name/hazard/metric/threshold/op/triggers/enabled/desc`。

### GET /api/monitor/alerts
实时按"指标 × 规则"匹配出的预警事件 `AlertEvent[]`：
`id/rule_id/rule_name/hazard/region/metric/value/threshold/level/status`。
`level` 映射：1 蓝 / 2 黄 / 3 橙 / 4 红。

### POST /api/risk
多维风险识别。请求体：
```json
{
  "hazard": "flood",          // flood | geology | fire | storm
  "region": "A 区",
  "signals": {"hazard_intensity": 90, "exposure": 70, "preparedness": 40, "vulnerability": 50},
  "drivers": ["强降雨", "低洼人口密集"]
}
```
返回 `RiskAssessment`：`score(0-100)/level/dims[]/drivers/suggested`。
定级：`>=80` 红 · `>=60` 橙 · `>=40` 黄 · 否则 蓝。

## 错误
统一 REST 语义码；5xx 表示引擎/数据异常，4xx 表示入参错误。
