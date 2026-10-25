# 知危鉴 后端镜像（FastAPI + uvicorn）
FROM python:3.11-slim

WORKDIR /srv/app
# 先装依赖（利用缓存层）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝应用
COPY app ./app

EXPOSE 8000
# 生产用多 worker（按需 CPU 调整）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
