# 知危鉴 ZhiWeiJian · 技术架构

> 主品牌 **知危鉴**，子品牌 **CaseRescue 知灾析策**（应急案例智能处理）。

## 1. 品牌与产品定位
- 主品牌「知危鉴」：应急风险预警与态势感知平台。
- 子品牌「知灾析策 (CaseRescue)」：灾害案例检索 + 标准化知识卡片，承担"教育/复盘"场景，是知危鉴的知识与内容引擎。
- 从纯 Coze 知识问答 → 升级为"数据 + 风险 + 预警 + 案例"闭环 Web 应用，可在线托管体验。

## 2. 分层架构
表现层(React/原生+TS+ECharts) → API 网关(Nginx, REST+WebSocket, 鉴权限流)
→ 服务层(FastAPI: 数据接入 / 风险识别 / 预警规则 / 案例知识) → 消息(RabbitMQ)+缓存(Redis)
→ 数据层(PostgreSQL 业务 / TimescaleDB 时序 / MinIO 对象 / 向量库 RAG) → 外部数据源与推送通道。

> 当前交付为可演示原型：前端内置示例数据 + 后端 FastAPI + 内存数据，
> 各层已按可扩展边界解耦，接真实数据源时替换 `data/` 与 `services/` 即可。

## 3. 模块职责
| 模块 | 职责 | 现状 / 演进 |
|---|---|---|
| 数据接入 | 多源采集、清洗、标准化、时空对齐 | 样例数据 → DB/流式 |
| 风险识别 | 多维加权评分 → 分级 + 建议 | engine.risk_identify（权重可配） |
| 预警机制 | 规则配置 + 阈值匹配 + 发布 | engine.match_alerts + RULES |
| 态势可视化 | 仪表盘/地图/趋势/热力 | 前端 ECharts（可扩展天地图） |
| 案例复盘 | 关键词/语义检索知识卡片 | engine.case_query（可接向量 RAG） |
| 决策支持 | 风险报告、处置建议、时间线 | 后续扩展 |

## 4. 接口规范（REST/OpenAPI）
- `/api/health`、`/api/cases`、`/api/monitor/{metrics,rules,alerts}`、`/api/risk`
- 统一 Pydantic 契约（`models/schemas.py`），前后端字段一致。
- 文档：后端 `/docs`、`/openapi.json`。

## 5. 数据库设计（演进）
- `cases`(id, title, date, location, level, summary, tags[], risk_factors[], measures[], lessons[], source)
- `monitor_metrics`(region, hazard, metric, value, unit, ts) → TimescaleDB 时序
- `alert_rules`(id, hazard, metric, threshold, op, upper, triggers, enabled)
- `alert_events`(rule_id, region, value, level, ts, status)
- `users/roles/audit`：账号、最小权限、审计日志

## 6. 安全考虑
- 传输 TLS；网关鉴权(JWT)+ 限流；RBAC 最小权限。
- 数据合规：外部数据源授权与脱敏；来源溯源；AI 内容人工审核与幻觉约束。
- 预警推送通道白名单；操作审计日志；敏感信息(身份证号等)不落明文。

## 7. 部署
- 本地：`pip install -r requirements.txt; uvicorn app.main:app --port 8000`；前端静态托管。
- 上线：Docker + docker-compose（frontend nginx + backend uvicorn + postgres + redis）；可扩展 K8s。
- 一键演示：`python backend/run.py`。

## 8. 开发计划
需求分析 → 原型设计 → 功能实现（MVP 已交付）→ 测试部署 → 持续维护/数据接入。
