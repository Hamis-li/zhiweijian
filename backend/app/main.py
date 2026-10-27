"""FastAPI 应用入口。

运行（开发）:
    cd zhiweijian/backend
    pip install fastapi uvicorn "pydantic>=2"
    uvicorn app.main:app --reload --port 8000

交互文档:  http://127.0.0.1:8000/docs
OpenAPI:   http://127.0.0.1:8000/openapi.json
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.api import router as api_router

app = FastAPI(
    title="知危鉴 API",
    version="1.0.0",
    description=(
        "应急管理「知危鉴」智能风险预警与案例复盘平台 API。\n\n"
        "覆盖：案例知识卡片检索、实时监测指标、预警规则匹配、多维风险识别。\n"
        "（原 Coze 问答智能体升级版：保留教育场景 + 新增风险预警能力）"
    ),
)

# 本地前后端联调开 CORS；上线时收敛到具体域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", tags=["meta"])
def root() -> dict:
    return {"name": "知危鉴", "docs": "/docs", "health": "/api/health"}
