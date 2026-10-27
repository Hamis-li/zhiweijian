# 知危鉴 HazardLens · 项目总说明
### 品牌 · 定位 · 数据来源 · 技术实现 · 展望

> 版本 v1.0（2026-10-27）｜本文是发布文档的**总纲**，与同文件夹另两份文档配合阅读：
> ① `知危鉴_项目说明文档.md`（仓库架构与模块逐项说明）② `数据与可视化说明.md`（逐图数据来源与处理链）。
> **发布时只同步上传 `发布文档/` 这一个文件夹。**

---

## 一、品牌与命名体系

### 1.1 命名结构（英文名-子项目）

| 层级 | 中文名 | 英文名 | 说明 |
|---|---|---|---|
| **总品牌** | 知危鉴 | **HazardLens** | 整个子品牌的总名称。Hazard（灾害）+ Lens（镜/透镜），呼应"鉴"之本义——镜鉴、鉴察、以史为鉴 |
| **子项目方向** | 知灾析策 | HazardLens–ZhiZaiXiCe | 知危鉴下的具体项目方向："知灾"（认识灾害）+"析策"（析出对策） |
| **当前分册** | 知危鉴–知灾 | **HazardLens–ZhiZai** | 当前仓库全部工作（案例萃取 + 案例可视化分布），属知灾析策的"**知灾**"部分 |
| **下一分册（规划）** | 知危鉴–析策 | HazardLens–XiCe | 政策分析，**下一个项目**，暂不实现 |

> 命名缘起：品牌名"知危鉴"最早取意"知乎生态 + 应急灾害领域 + 复盘镜鉴"（知乎黑客松时期），现升格为整个子品牌的总名称；仓库名/部署子域名保留拼音 `zhiweijian` 不变，对外展示统一用 HazardLens 体系。

### 1.2 命名沿革（从一开始到现在怎么改的）

| 阶段 | 名称 | 载体 | 说明 |
|---|---|---|---|
| v0.5（2026-09 知乎黑客松） | 知危鉴 · 灾害应急案例 AI 萃取助手 | 知乎开放 API + Streamlit（app.py 约1400行） | 四层链路：智能检索→案例萃取→案例分析→AI综合复盘；防幻觉（强制附原文证据）；参赛"知识炼金场"赛道，评审得分 5.53 |
| v0.8（2026-09） | CaseRescue 知灾析策 | Coze(扣子) 知识卡片智能体 | 五份官方事故报告 → 四维知识卡片（概况/风险因素/措施/教训）；"每发表做成应用" |
| v1.0（2026-10） | 知危鉴（zhiweijian 仓库） | FastAPI + 静态前端 + Streamlit 双栈 | 新增风险识别引擎、预警规则、RAG、SSE 实时流、在线态势地图（USGS/Open-Meteo/NHC 真实数据） |
| v1.1（2026-10-27 定稿） | 知危鉴（单品牌） | 同上 | 命名统一（CaseRescue/知灾析策/智微界 清零、"数据萃取"→"在线数据整合"）、SCI 学术主题、修 CI |
| v1.2（2026-10-27） | HazardLens–ZhiZai | 同上 | 新增「灾害数据可视化」：《自然灾害分类》五大类历史事件 + GS(2020)4619 标准底图分省 choropleth |
| v2.0（规划） | HazardLens–XiCe | 新项目 | 政策分析；配套云平台（上传数据→云端处理→Docker 部署） |

---

## 二、整体定位与三大内容板块

**一句话定位**：HazardLens–ZhiZai（知危鉴–知灾）是面向应急管理的**知识生产与风险展示平台**——把分散的灾害案例与在线监测数据，萃取成结构化知识，落到行政地图上直观展示。

| 板块 | 内容 | 现状 |
|---|---|---|
| ① **案例萃取** | 知乎四层萃取链路（检索→萃取→分析→复盘，强制附原文证据防幻觉）+ 官方案例知识卡片（四维结构化 + TF-IDF RAG 检索） | ✅ 已完成（知乎黑客松版 + Coze 版 + 仓库内案例模块） |
| ② **案例可视化分布** | 在线态势地图（实时地震/台风/隐患点）+ 灾害数据可视化（五大类历史事件分省 choropleth、差值图、统计面板） | ✅ 已完成（本仓库 Streamlit 应用） |
| ③ **政策分析** | 基于②的分布规律与①的经验教训，做政策成效对比、对策建议生成 | ⏳ **下一个项目**（HazardLens–XiCe），本仓库仅预留接口 |

---

## 三、MERGE Initiative 核实结论与引用建议

**核实结果（真实存在，可间接引用）**：

> Guha-Sapir, D. et al. The MERGE Dataset: A Harmonized Global Resource for Climate Disaster Impacts and Human Vulnerability. *Scientific Data* (Nature Portfolio), 2026 年 6 月。**DOI: 10.1038/s41597-026-07522-7**

- **是什么**：MERGE Initiative/MERGE Consortium 推进的全球数据基础设施，概念验证（PoC）阶段发布公开试点数据集：**整合 10 个数据库的 250+ 变量**（含 EM-DAT 紧急事件数据库、IDMC-GIDD 全球境内流离失所数据库），在多个行政层级上把人员/经济损失与环境、气候、社会人口背景对齐。
- **能否在本项目间接引用**：**能，建议按以下方式**——
  1. **作为参考文献**：在本项目"数据来源清单"中列为同类权威上游源（见第四节），注明 DOI；
  2. **作为扩展路径**：本项目当前 71 条事件为"展示优先"的公开事件编纂集；将来若要规模化，直接接 EM-DAT（https://www.emdat.be/ ，学术免费申请）或 MERGE 试点数据集的**中国子集**，按本项目"事件 dict"契约（id/name/category/subtype/date/lat/lon/province/severity/source）转换后即可注入——**换数据不换代码**；
  3. **许可注意**：MERGE 采用 CC BY-NC-ND 4.0，署名后可非商业引用；本项目为教学演示用途，合规。

---

## 四、数据来源与参考文献清单（主流来源，带链接）

| # | 来源 | 用途 | 链接 | 许可/获取 |
|---|---|---|---|---|
| 1 | USGS Earthquake Hazards Program | 实时+历史地震（FDSN API，本项目 `usgs_history()` 动态补充） | https://earthquake.usgs.gov/ ｜ API: https://earthquake.usgs.gov/fdsnws/event/1/ | 公开 |
| 2 | Open-Meteo | 实时天气（温度/风速/降水/湿度）+ 在线地理编码 | https://open-meteo.com/ ｜ https://geocoding-api.open-meteo.com | 公开免费 |
| 3 | NHC ATCF（美国国家飓风中心） | 台风轨迹在线解析 | https://www.nhc.noaa.gov/atcf/ | 公开 |
| 4 | IBTrACS（内置坐标序列回退） | NHC 不可达时的台风轨迹兜底 | https://www.ncei.noaa.gov/products/international-best-track-archive | 公开 |
| 5 | EM-DAT（CRED/UCLouvain） | 全球灾害数据库（1900 至今 2.7 万+ 条） | https://www.emdat.be/ | 学术免费申请 |
| 6 | **MERGE Initiative** | 10 库 250+ 变量的调和型灾害数据集（见第三节） | https://doi.org/10.1038/s41597-026-07522-7 | CC BY-NC-ND 4.0 |
| 7 | IDMC-GIDD | 境内流离失所数据库（MERGE 上游之一，后续扩展用） | https://www.internal-displacement.org/database | 公开 |
| 8 | 应急管理部·全国自然灾害基本情况通报 | 历史事件编纂集主要出处（损失/等级口径） | https://www.mem.gov.cn/ | 公开发布 |
| 9 | 中国气象局 / 水利部 / 自然资源部海洋灾害通报 | 气象/洪涝/海洋灾害事件出处 | https://www.cma.gov.cn/ ｜ https://www.mwr.gov.cn/ ｜ https://www.mnr.gov.cn/ | 公开发布 |
| 10 | 中国地震局 / USGS | 地震事件出处 | https://www.cea.gov.cn/ | 公开发布 |
| 11 | **GS(2020)4619 标准地图**（自然资源部） | 全部中国地图的合规底图（34省面+九段线，图注"底图无修改"） | 标准地图服务：http://bzdt.ch.mnr.gov.cn/ ｜ 本机：`E:\ATAIFEN\SHUJU\中国标准地图-审图号GS(2020)4619号-shp格式\` | 免费商用需遵循审图号规则 |
| 12 | 阿里 DataV GeoAtlas | 云端部署时的边界兜底（含九段线） | https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json | 公开 |
| 13 | 天地图 1:100 万行政边界 | 备选省级边界（本项目台风论文线常用） | https://www.webmap.cn/ | 公开 |
| 14 | GB/T 29639-2020《生产经营单位生产安全事故应急预案编制导则》 | 应急方案模块的规范依据 | 全国标准信息公共服务平台 https://std.samr.gov.cn/ | 国标 |
| 15 | 《自然灾害分类》（五大类口径） | 事件分类体系（气象/地质/水文/海洋/生物；洪涝默认归气象、泥石流归地质、海啸风暴潮归海洋） | 教材通行口径（本库 `disaster_history.SUBTYPE_TO_CATEGORY` 内置映射） | — |

---

## 五、技术实现说明（语言 · 库 · 制图 · 部署）

### 5.1 语言与运行环境
- **Python 3.11+**（Streamlit Cloud 实际运行 3.11；本机制图自检用 `D:\Program Files\Python314\python.exe`）。

### 5.2 库清单（`requirements.txt`）
| 库 | 用途 |
|---|---|
| `streamlit` | Web 应用框架（在线作品托管入口） |
| `folium` | 交互式态势地图（Leaflet；CartoDB Positron/Dark Matter 瓦片） |
| `altair` | 统计图表（KPI、直方图、流程链） |
| `pandas` | 数据表处理 |
| `matplotlib` | **灾害数据可视化**（choropleth/差值图/小提琴，Nature 风格） |
| `pyshp`（可选） | 读取 GS(2020)4619 标准底图 .shp（不依赖 geopandas，轻量） |
| FastAPI 栈（工程化后端）：`fastapi / uvicorn / pydantic / scikit-learn` | 风险引擎、RAG（TF-IDF）、SSE 实时流 |

### 5.3 制图方法（怎么画的）
1. **交互式地图**（在线态势地图）：`folium.Map(tiles="CartoDB Positron")` + 图层（地震 CircleMarker 半径∝震级 / 台风 PolyLine / 隐患点菱形）+ 左下角图例 + LayerControl。
2. **灾害数据可视化**（Nature 风格展示，**只借风格不搬方法**）：
   - 底图：GS(2020)4619 标准地图省级行政区.shp（pyshp + GBK 解码；Beijing1954-Lambert 投影坐标**直绘**，量级>1e5 自动判别），叠加国界线.shp（GBCODE=61010 九段线、26080 南海群岛岸线）；云端无本机文件时自动回退 DataV GeoAtlas；
   - 分省填色：事件经纬度→`bbox 粗筛 + 射线法`归省（或直接用 province 字段）→ 按省计数 → YlOrRd 顺序色带 / RdBu_r 发散色带（分位断点 BoundaryNorm）；
   - 制图要素：右下角**南海诸岛 inset**（九段线加粗）、左上**指北针**、左下 **0–500km 比例尺**、无数据省 **hatch="///"**、面板标号 (a)(b)(c)、colorbar 带单位"事件次数"；图注自动标注"底图审图号：GS(2020)4619 号（底图无修改）"；
   - 字体：SimHei / Microsoft YaHei（中文），`axes.unicode_minus=False`。

### 5.4 部署方式（GitHub 加什么）
```
本地编码 → git commit/push → GitHub (github.com/Hamis-li/zhiweijian)
        → Streamlit Cloud 自动拉取重建（Main file path: streamlit/zhiweijian/app.py）
        → 在线 Demo（*.streamlit.app）
```
- 云端 Secrets 无需（纯公开 API）；依赖由 `requirements.txt` 自动安装；
- 本地全栈演示：`docker compose up -d --build`（Nginx 单端口 8080 + FastAPI 反代）；
- **规划**：数据上传 → 云服务器/对象存储 → Docker 化云平台（见第七节）。

---

## 六、数据展示原则（display-first，以展示为主）

> **核心思想**：公开渠道能搜到多少就先展示多少，**把"可以这样表示"的方法立起来**；数据规模不是门槛，方法可复制才是价值。

1. **仅展示 N 条**：当前内置 71 条真实公开事件（示例集），**五大类全覆盖、每大类至少 3 条**（气象 30 / 地质 23 / 海洋 5 / 生物 6 / 水文 7，覆盖 25 个省级行政区，2009–2026）。2026-10-28 扩充：新增「山洪」子类归水文灾害，水文由 2 条补至 7 条（原为唯一未达标大类）。
2. **时间跨度从"有数据的起点"写起**：早期数据不齐全属正常现象，有多少放多少；后续做定量计算时再做数据清洗与口径校准——展示阶段不因此设限。
3. **展示窗口灵活**：可看全部尺度，也可只看近五年（应用内时间窗控件随意切换）。
4. **举一反三（方法可复制）**：任何用户/机构想替换数据——只需按"事件 dict"契约（id/name/category/subtype/date/lat/lon/province/severity/source）准备 CSV/JSON **上传即可填充**；EM-DAT、MERGE、应急管理部通报等主流源都可对接，代码零改动（这就是"换数据不换方法"）。
5. **来源必须标注**：每条事件带 `source` 字段；整套来源见第四节参考文献清单——像论文引用一样可追溯。
6. **可视化一律落到行政单元**：所有统计（次数/类型/严重度）都按省级行政区聚合填色；气温、降雨等气象要素同样可按此路径接入（API 实时获取或历史 **NC(NetCDF)→TIF** 转栅格后按行政区统计——转换能力已具备，云平台阶段可让用户自行上传处理）。

---

## 七、展望（下一个项目与云平台）

| 方向 | 说明 |
|---|---|
| **HazardLens–XiCe（知危鉴–析策）** | 政策分析：基于知灾板块的分布规律 + 萃取经验教训，做政策成效横向对比、对策建议生成（下一个独立项目） |
| **数据上传与云平台** | 用户上传自有事件数据（CSV/JSON，按契约）→ 云服务器存储 → 平台自动出图；Docker 一键部署（compose 编排已就绪） |
| **NC→TIF 栅格链路** | 接入气象历史再分析 NetCDF（气温/降水），转 TIF 后按行政区统计，扩展"气象灾害"板块的连续场数据 |
| **向 MERGE/EM-DAT 规模化** | 接入其中国子集并按契约转换，事件量从"展示示例"升级为"全量分析" |

---

## 附：发布文档清单（本文件夹即发布包）

> 注：下表为建库初期快照；当前发布文档已扩至 12 份（新增总日志/任务卡/整理纪要等），**以文件夹实际清单为准**。

| 文件 | 内容 |
|---|---|
| `知危鉴HazardLens_项目总说明.md` | 本文（总纲：品牌/定位/数据/技术/展望） |
| `知危鉴_项目说明文档.md` | 仓库架构与全部模块、函数、设计取舍、现存问题 |
| `数据与可视化说明.md` | 分类标准映射、逐图数据来源→处理链→图型说明、参考图风格对照、合规声明 |
