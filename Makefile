# 知危鉴 · 常用命令
.PHONY: dev-backend dev-frontend up down logs test

## 本地起后端 (http://127.0.0.1:8000/docs)
dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

## 本地起前端静态 (http://127.0.0.1:5173)
dev-frontend:
	cd frontend && python -m http.server 5173

## 一键起全栈 (http://127.0.0.1:8080)
up:
	docker compose up -d --build

## 停全栈
down:
	docker compose down

## 看日志
logs:
	docker compose logs -f

## 后端自检
test:
	cd backend && python -c "from app.main import app; print('OK', app.title)"
