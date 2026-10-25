FROM nginx:1.25-alpine
# 静态演示页
COPY index.html /usr/share/nginx/html/index.html
# 网关配置（托管静态 + 反代 /api → backend:8000）
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
