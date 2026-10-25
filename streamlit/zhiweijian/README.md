# 知危鉴 · 灾害风险预警与案例复盘（Streamlit 版）

**主品牌**：知危鉴 ZhiWeiJian　**子品牌**：CaseRescue 知灾析策（应急案例智能处理助手）

面向应急管理的灾害风险预警与案例复盘平台：
- ⚡ **实时天气数据获取**：Open-Meteo 在线 API（温度/风速/降水），支持城市在线搜索，数据萃取展示。
- 🗺 **灾害案例地图联动**：5 类（台风/地震/泥石流/爆炸/火灾），地震来自 USGS 真实在线数据；地图标记 ↔ 案例列表**双向同步**，支持按**时间范围 + 地理位置 + 分类 + 震级**筛选，点击查看详情（新闻来源/时间轴/文字描述）。
- 🔍 **在线搜索与数据萃取**：关键词检索，导出 CSV。

## 快速运行

```bash
cd streamlit/zhiweijian
pip install -r requirements.txt
streamlit run app.py
# 打开 http://localhost:8501
```

> 本环境无法自动安装 Streamlit（pip 被环境限制），故另附**零安装独立网页版**
> `../../web/index.html`（浏览器双击即开，在线拉取真实数据）。

## 数据源（全部免密钥、可直接运行）
| 数据 | API | 说明 |
|---|---|---|
| 实时天气 | `https://api.open-meteo.com/v1/forecast?latitude=39.9&longitude=116.4&current=temperature_2m,wind_speed_10m,wind_direction_10m,precipitation,relative_humidity_2m&timezone=auto` | 温度/风/雨/湿 |
| 城市地理编码 | `https://geocoding-api.open-meteo.com/v1/search?name=Beijing&count=1&language=zh` | 在线城市搜索 |
| 历史地震 | `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson` | 真实、带经纬度/震级/时间 |
| 中国地图底图 | `https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json` | ECharts/folium 用 |

## 目录
```
zhiweijian/
├─ app.py          # Streamlit 入口（4 个功能模块）
├─ weather.py      # 天气获取 + 地理编码 + 风级转换
├─ disasters.py    # 案例数据（内置5类 + USGS在线地震 + 筛选）
├─ requirements.txt
└─ README.md
```

## 推 GitHub / 部署
```bash
git init && git add . && git commit -m "知危鉴 Streamlit 版"
git remote add origin <你的仓库>
git push -u origin main
# 可选：GitHub Actions 部署到 Streamlit Cloud / share.streamlit.io
```

## 扩展
- 把内置台风/泥石流/爆炸/火灾替换为 EM-DAT / 新闻 API 抓取。
- 加台风路径（IBTrACS）与海啸（NOAA）数据源。
- 预警规则与风险模型接入前面 `backend/` 的 FastAPI 引擎。
