# 推 GitHub + 部署 Streamlit Cloud 操作手册

> 本地已 `git init` 并 commit（31 文件）。下面命令都在 `zhiweijian/` 目录执行。

## 一、推 GitHub

### 1. 在 GitHub 建一个空仓库（不勾选 README/license）
- 仓库名建议：`zhiweijian`
- 类型：Private（比赛用）/ Public（参赛展示建议 Public）

### 2. 添加 remote 并推送
```bash
cd zhiweijian
# 把下面替换成你的仓库地址
git remote add origin https://github.com/<你的用户名>/zhiweijian.git
git branch -M main
git push -u origin main
```

### 3. 若提示认证（无 GitHub CLI / token）
- 用 **PAT（个人访问令牌）** 当密码：Settings → Developer settings → Tokens
- 或在 GitHub 客户端 / `gh auth login` 后 `gh repo create zhiweijian --source=. --remote=origin --push`

> 我这边没有你的 GitHub 凭据，所以 remote 留占位，你填上用户名即可推送。

## 二、部署到 share.streamlit.io（Streamlit Cloud / Streamlit Community Cloud）

1. 打开 https://share.streamlit.io → 登录（用 GitHub 账号）。
2. 点 **Create / New app**，选刚推的仓库 `zhiweijian`。
3. 目录（directory）填：`streamlit/zhiweijian`（`app.py` 所在目录）。
4. **Main Python file**：`app.py`
5. **Python version**：3.9+
6. 点 **Deploy** → 几秒后得到 `https://<用户名>-<应用名>.streamlit.app` 在线链接。

> Streamlit Cloud 会自动读 `requirements.txt`（已含 streamlit/folium/plotly）。
> 应用运行在云端，USGS/Open-Meteo 在线数据会从云端服务器拉取（比本地稳定）。

## 三、可选：GitHub Actions 自动部署
若要用 Actions 而非 Streamlit Cloud，见 `.github/workflows/streamlit.yml`（按需启用）。

## 四、目录结构（可克隆即用）
```
zhiweijian/
├─ backend/        FastAPI 引擎（RAG/风险/预警）
├─ streamlit/zhiweijian/   Streamlit 应用（app.py 入口，推 GitHub 部署用这个）
├─ web/index.html  零安装独立网页版（浏览器直接开）
├─ frontend/       React/静态演示页
└─ docs/           架构/API/投稿说明
```
