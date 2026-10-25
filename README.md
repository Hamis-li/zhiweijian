# 知危鉴 ZhiWeiJian · 应急风险预警与案例复盘平台

**主品牌：知危鉴 ZhiWeiJian**　|　**子品牌：CaseRescue 知灾析策 —— 应急案例智能处理助手**

面向应急管理"知危"与"鉴验"场景的智能平台。在原「知灾析策」(Coze 知识问答智能体) 基础上升级：
保留**案例知识卡片**核心教育能力，新增**多维风险识别 + 分级预警机制 + 态势仪表盘**，
形成"数据 → 风险识别 → 预警分级 → 态势展示 → 案例复盘 → 决策支持"闭环。

> 投稿目标：WorkBuddy「1024 造物挑战」程序员节应用创作大赛（在线作品托管）。

## 品牌与定位
- 主品牌 **知危鉴**：风险识别 / 预警 / 态势感知统一入口。
- 子品牌 **知灾析策 (CaseRescue)**：灾害案例检索与知识卡片（教育场景），作为知危鉴的内容/知识引擎子模块。
- 目标用户：应急管理部门（决策）、监测操作员、科研/分析师、公众/企业（预警订阅与应急指南）。

## 功能模块
| 模块 | 说明 |
|---|---|
| 仪表盘 | 多源监测指标总览、风险指数、预警 KPI、趋势图 |
| 风险识别 | 按灾害类型多维度加权，自动定级（蓝/黄/橙/红）+ 处置建议 |
| 预警中心 | 监测指标 × 可配置规则 → 实时匹配分级预警 |
| 案例复盘 | 关键词检索标准化案例知识卡片（概况/风险因素/措施/教训） |

## 技术架构
- **前端**：原生 Web 单页（ECharts）可一键托管；可平滑演进为 React+Vite+TS 组件化。
- **后端**：Python 3.11 + FastAPI（异步、OpenAPI），模块：数据接入 / 风险引擎 / 预警规则 / 案例检索。
- **数据**：内置样例 → 可扩展为 PostgreSQL + TimescaleDB（时序）+ Redis（实时/缓存）+ 向量库（案例 RAG）。
- **接口**：REST（OpenAPI 3.0），可加 WebSocket 推送预警。
- **安全**：网关鉴权限流、最小权限角色、来源溯源与数据合规、推送通道白名单。

## 目录结构
```
zhiweijian/
├── frontend/
│   └── index.html          # 可上线演示单页（ECharts + 内置示例数据）
├── backend/
│   ├── requirements.txt
│   ├── run.py
│   └── app/
│       ├── main.py                  # FastAPI 入口
│       ├── models/schemas.py        # Pydantic 契约（前后端字段一致）
│       ├── services/engine.py       # 风险识别 + 预警匹配 + 案例检索引擎
│       ├── data/sample_data.py      # 样例案例/指标/规则（可替换为数据库）
│       └── routers/api.py          # REST 路由
└── docs/
    ├── ARCHITECTURE.md
    └── API.md
```

## 快速启动

### 方式 A：Docker 一键全栈（推荐，可托管上线）
```
cd zhiweijian
docker compose up -d --build
# → http://localhost:8080  （Nginx 单端口：前端演示页 + 反代 /api 到 FastAPI）
```

### 方式 B：纯静态演示页（最简，双击/托管即可）
浏览器打开 `frontend/index.html`。内置示例数据可离线运行；
若部署到 Nginx 反代链路（方式 A），页面自动 `fetch /api` 拉取后端真实数据，失败则回退内置数据。

### 方式 C：本地开发（无 Docker）
```
cd zhiweijian/frontend && python -m http.server 5173   # 演示页
cd zhiweijian/backend  && uvicorn app.main:app --port 8000  # API + /docs
```

### Makefile 常用命令
`make up` / `make down` / `make logs` / `make test`（见 `Makefile`）

## 接口速览
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/health | 健康检查 |
| GET | /api/cases?keyword=&top_k= | 案例知识卡片检索 |
| GET | /api/monitor/metrics | 监测指标 |
| GET | /api/monitor/rules | 预警规则 |
| GET | /api/monitor/alerts | 实时匹配预警事件 |
| POST | /api/risk | 多维风险识别（定级+建议） |

## 开发与维护
- 前端演示数据在 `frontend/index.html` 的 `METRICS/RULES/CASES` 区，可改；接真实后端时改为 fetch `/api`。
- 后端样例数据在 `backend/app/data/sample_data.py`，扩展案例/规则/指标在此。
- 引擎逻辑集中在 `backend/app/services/engine.py`，权重/阈值可参数化扩展。
- 详见 `docs/ARCHITECTURE.md`、`docs/API.md`。
