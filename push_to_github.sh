#!/usr/bin/env bash
# 一键推送 zhiweijian 到 GitHub（在 zhiweijian/ 目录执行）
# 用法:
#   1) 先在 GitHub 建一个空仓库(不勾README)，命名 zhiweijian
#   2) 本目录执行:  bash push_to_github.sh <你的用户名> zhiweijian
#   例:             bash push_to_github.sh Hamis-li zhiweijian
set -e
USER="${1:-Hamis-li}"
REPO="${2:-zhiweijian}"
BRANCH="${3:-main}"

cd "$(dirname "$0")"

echo ">>> 远程仓库: https://github.com/$USER/$REPO"
git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/$USER/$REPO.git"
git branch -M "$BRANCH"

echo ">>> 推送中（若弹出密码框，粘贴你的 PAT 个人访问令牌）..."
git push -u origin "$BRANCH"

echo ">>> 完成！克隆地址: https://github.com/$USER/$REPO"
echo ">>> 部署到 Streamlit Cloud: 登录 share.streamlit.io → New app"
echo "    目录填 streamlit/zhiweijian ，主文件填 app.py"
