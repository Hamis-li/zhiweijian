"""知危鉴 · 灾害风险预警与案例复盘平台（Streamlit · 纯在线版）

入口：streamlit run app.py

架构：纯在线 —— 数据全部来自在线 API（USGS 地震 / Open-Meteo 天气 / NHC 台风），
无本地文件存储、无本地计算兜底。链路：在线搜索 → 在线清洗整合 → 在线可视化。
模块：① 在线态势地图（实时+历史轨迹统一承载）② 在线搜索·可视化
      ③ 应急方案模块 ④ 实时天气仪表盘
"""
import json
from datetime import datetime, timezone

import streamlit as st
import folium
from streamlit_folium import st_folium  # 修复(2026-10-30)：folium 地图需经 st_folium 渲染，st.write 不支持
import pandas as pd
import altair as alt

import data_online

# ---------------- 品牌与页面 ----------------
st.set_page_config(page_title="知危鉴 · 应急风险预警与案例复盘平台", layout="wide",
                   page_icon="⚠️")
st.sidebar.title("⚠️ 知危鉴")
st.sidebar.caption("纯在线 · 灾害风险预警与案例复盘\n案例复盘模块")
st.sidebar.divider()

# ---------------- SCI 学术美感 · 明暗双模全局样式（GV 米白纸张底 + a16z 深炭黑底 + 衬线大标题 + 克制金棕品牌色）----------------
dark_mode = st.sidebar.toggle("深色模式（学术暗色大屏）", value=False, key="dark_mode")

_SCI_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@600;700&family=Noto+Sans+SC:wght@400;500;700&family=JetBrains+Mono:wght@400;600&display=swap');
:root{--primary-color:#A6761D;--background-color:#F7F8FA;--secondary-background-color:#FFFFFF;--text-color:#0A0E1A;}
.stApp{background:#F7F8FA;font-family:'Noto Sans SC','Inter',-apple-system,Segoe UI,Roboto,sans-serif;color:#0A0E1A;}
.stApp h1,.stApp h2,.stApp h3,.stTitle{font-family:'Noto Serif SC','Source Serif 4',Georgia,serif !important;color:#0A0E1A !important;font-weight:700 !important;letter-spacing:.01em;}
.stSidebar,.stSidebar>div:first-child{background-color:#FCFCFD !important;border-right:1px solid #E3E8EF;}
.stSidebar h1,.stSidebar .stTitle{color:#A6761D !important;}
.stCaption,.stCaption p{color:#5B6478 !important;font-size:.85rem;}
.stButton>button{background-color:#8C6014;color:#FFFFFF;border:none;border-radius:8px;font-weight:600;padding:.5rem 1rem;}
.stButton>button:hover{background-color:#6F4B10;}
.stMetric{background:#FFFFFF;border:1px solid #E3E8EF;border-radius:10px;padding:.6rem .8rem;}
.stMetric label{color:#5B6478 !important;}
code,.stCode,.stJson{font-family:'JetBrains Mono',monospace !important;}
</style>
"""

# 深色模式覆盖层（a16z 深炭黑底招牌）
_DARK_CSS = """
<style>
:root{--primary-color:#C9972E;--background-color:#0B1430;--secondary-background-color:#121B33;--text-color:#E8EDF7;}
.stApp{background:#0B1430 !important;color:#E8EDF7 !important;}
.stApp h1,.stApp h2,.stApp h3,.stTitle{color:#E8EDF7 !important;}
.stSidebar,.stSidebar>div:first-child{background-color:#0E1830 !important;border-right:1px solid #2C3550 !important;}
.stSidebar h1,.stSidebar .stTitle{color:#C9972E !important;}
.stCaption,.stCaption p{color:#9AA6C0 !important;}
.stButton>button{background-color:#C9972E !important;color:#0B1430 !important;}
.stButton>button:hover{background-color:#E0B455 !important;}
.stMetric{background:#121B33 !important;border:1px solid #2C3550 !important;}
.stMetric label{color:#9AA6C0 !important;}
</style>
"""

st.markdown(_SCI_CSS, unsafe_allow_html=True)
if dark_mode:
    st.markdown(_DARK_CSS, unsafe_allow_html=True)

# 在线数据集（USGS + NHC/IBTrACS + 隐患点；缓存 10 分钟）
dataset = data_online.build_dataset(min_mag=4.5)

# 自动刷新（在线大屏）：到点整页重拉数据
if "last_refresh" not in st.session_state:
    st.session_state["last_refresh"] = datetime.now()
auto_on = st.sidebar.toggle("自动实时刷新（预警大屏）", value=True)
interval = st.sidebar.select_slider("刷新间隔（秒）", options=[30, 60, 120, 300],
                                   value=60, disabled=not auto_on)
if auto_on:
    import streamlit.components.v1 as _components
    _components.html(
        f"<script>setTimeout(function(){{window.location.reload();}}),{int(interval)*1000});</script>",
        height=0)
    st.sidebar.caption(f"⏱ 每 {int(interval)}s 自动刷新 · 上次 {st.session_state['last_refresh'].strftime('%H:%M:%S')}")
st.session_state["last_refresh"] = datetime.now()


# =====================================================================
# ① 在线态势地图（统一承载：实时地震 + 台风历史轨迹 + 隐患点 + 实时天气点）
# =====================================================================
def tab_map():
    st.title("在线态势地图")
    st.caption("一张地图统一承载：实时状态（在线地震/天气）+ 历史数据（台风轨迹/隐患点）")

    eq = dataset["earthquakes"]
    ty = dataset["typhoon_tracks"]
    spots = dataset["risk_spots"]

    show_eq = st.toggle("显示实时地震（USGS）", value=True, key="m_eq")
    show_ty = st.toggle(f"显示台风历史轨迹（{dataset['typhoon_source']}）", value=True, key="m_ty")
    show_rs = st.toggle("显示隐患点", value=True, key="m_rs")

    dark = st.session_state.get("dark_mode", False)
    if dark:
        m = folium.Map(location=[30, 115], zoom_start=4, tiles="CartoDB Dark Matter")
        folium.Element(
            "<style>.folium-map{position:relative !important}"
            ".leaflet-container{background:#0b1430} "
            ".leaflet-popup-content-wrapper,.leaflet-popup-tip"
            "{background:#0b1430;color:#e8edf7;border:1px solid #2c3550}</style>"
        ).add_to(m)
    else:
        m = folium.Map(location=[30, 115], zoom_start=4, tiles="CartoDB Positron")
        folium.Element(
            "<style>.folium-map{position:relative !important}"
            ".leaflet-container{background:#eef1f5} "
            ".leaflet-popup-content-wrapper,.leaflet-popup-tip"
            "{background:#ffffff;color:#0a0e1a;border:1px solid #d6dbe4;"
            "box-shadow:0 2px 8px rgba(10,14,26,.12)}"
            ".leaflet-bar a,.leaflet-control-zoom a"
            "{background:#fff;color:#0a0e1a;border-color:#d6dbe4}"
            ".leaflet-control-attribution{background:rgba(255,255,255,.85);color:#5b6478}"
            ".leaflet-control-layers{background:rgba(255,255,255,.92);color:#0a0e1a;"
            "border:1px solid #d6dbe4}</style>"
        ).add_to(m)

    # 学术地图图例（红=地震/高危隐患，蓝=台风轨迹，琥珀=低危隐患；白卡在明暗底图均清晰）
    folium.Element(
        """<div style="position:absolute;bottom:12px;left:12px;z-index:1000;
        background:rgba(255,255,255,.92);border:1px solid #d6dbe4;border-radius:8px;
        padding:8px 10px;font:12px/1.6 'Noto Sans SC',sans-serif;color:#0a0e1a;
        box-shadow:0 2px 8px rgba(10,14,26,.12)">
        <b style="font-family:'Noto Serif SC',serif">图例</b><br>
        <span style="color:#ff5a4d">●</span> 实时地震（USGS，半径∝震级）<br>
        <span style="color:#3fa9ff">━</span> 台风历史轨迹<br>
        <span style="color:#ff5a4d">◆</span> 隐患点（高）&nbsp;&nbsp;
        <span style="color:#F07C24">◆</span> 隐患点（低）</div>"""
    ).add_to(m)
    layers = []

    if show_eq and eq:
        g = folium.FeatureGroup(name="🌏 实时地震")
        for c in eq:
            r = 3 + (c["magnitude"] or 0) * 1.4
            folium.CircleMarker(location=[c["lat"], c["lon"]], radius=r,
                                color="#ff5a4d", fill=True, fillColor="#ff5a4d",
                                fillOpacity=.85, weight=1,
                                popup=f"""<b>M{c['magnitude']} · {c['title']}</b><br>
                                          {c['date']} · {c['source']}""").add_to(g)
        g.add_to(m)
        layers.append(g)

    if show_ty and ty:
        g = folium.FeatureGroup(name="🌀 台风历史轨迹")
        for t in ty:
            pts = [[p[1], p[2]] for p in t["points"]]
            folium.PolyLine(pts, color="#3fa9ff", weight=3, dash_array="6 6").add_to(g)
            folium.Marker(pts[0], icon=folium.Icon(color="blue", icon="info-sign"),
                          popup=f"{t['name']} 起点").add_to(g)
            folium.Marker(pts[-1], icon=folium.Icon(color="red", icon="flag"),
                          popup=f"{t['name']} 登陆/终点").add_to(g)
        g.add_to(m)
        layers.append(g)

    if show_rs and spots:
        g = folium.FeatureGroup(name="⚠️ 隐患点")
        for s in spots:
            col = "#ff5a4d" if s["level"] >= 4 else "#F07C24"
            folium.Marker([s["lat"], s["lon"]],
                          icon=folium.DivIcon(
                              html=(f'<div style="width:14px;height:14px;background:{col};'
                                    f'transform:rotate(45deg);margin:4px"></div>'),
                              icon_size=(14, 14), icon_anchor=(7, 7)),
                          popup=f"""<b>{s['name']}</b><br>{s.get('desc','')}<br>等级：{s['level']}""").add_to(g)
        g.add_to(m)
        layers.append(g)

    # 图层开关面板
    if layers:
        folium.LayerControl(collapsed=True).add_to(m)

    m.fit_bounds([[min([c["lat"] for c in eq] + [s["lat"] for s in spots]) - 5,
                   min([c["lon"] for c in eq] + [s["lon"] for s in spots]) - 5],
                  [max([c["lat"] for c in eq] + [s["lat"] for s in spots]) + 5,
                   max([c["lon"] for c in eq] + [s["lon"] for s in spots]) + 5]])
    st_folium(m, height=560)


# =====================================================================
# ② 在线搜索 · 数据整合 · 可视化
# =====================================================================
def tab_search_viz():
    st.title("在线搜索 · 数据整合 · 可视化")
    st.caption("在线拉取 → 关键词过滤 → 在线清洗/标准化 → 图表/表格/仪表盘 呈现（全在线，无本地存储）")

    c1, c2, c3 = st.columns([2, 1, 1])
    kw = c1.text_input("在线搜索关键词", placeholder="如：Japan / Beijing / M / Tsunami", value="")
    geo = c2.selectbox("区域", ["全部", "中国大陆", "沿海", "日本", "东南亚"], index=0)
    min_mag = c3.slider("最小震级", 0.0, 10.0, 4.5, 0.5)

    # 在线清洗 + 过滤 + 整合 + 复盘升级（每案例 enrich：过程线/动因/可迁移/证据分级/叙事/三层视角）
    rows = [e for e in dataset["earthquakes"] if (e.get("magnitude") or 0) >= min_mag]
    if kw:
        k = kw.lower()
        rows = [e for e in rows if k in json.dumps(e, ensure_ascii=False).lower()]
    geo_boxes = {"中国大陆": (18, 54, 73, 135), "沿海": (18, 32, 110, 125),
                 "日本": (30, 46, 128, 146), "东南亚": (5, 25, 95, 125)}
    if geo in geo_boxes:
        a, b, c, d = geo_boxes[geo]
        rows = [e for e in rows if a <= e["lat"] <= b and c <= e["lon"] <= d]
    rows = data_online.clean_unify(rows)
    rows = [data_online.enrich_case(e) for e in rows]  # 案例复盘三层拆解

    st.subheader(f"命中 {len(rows)} 条在线事件（清洗/去重/标准化后）")

    # 仪表盘 KPI
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("事件总数", len(rows))
    k2.metric("最大震级", f"{max((e['magnitude'] or 0) for e in rows) if rows else 0}")
    k3.metric("≥M6", sum(1 for e in rows if (e["magnitude"] or 0) >= 6))
    k4.metric("≥M5", sum(1 for e in rows if (e["magnitude"] or 0) >= 5))

    if rows:
        df = pd.DataFrame([{
            "时间": e["date"], "标题": e["title"], "震级": e["magnitude"],
            "纬度": e["lat"], "经度": e["lon"], "区域": e["region"], "来源": e["source"]}
            for e in rows])

        # 冲突叙事时间轴（平稳-冲突-应对-蜕变）
        st.markdown("**🎬 冲突叙事时间轴**（平稳→冲突→应对→蜕变，非纯时间平铺）")
        tl = data_online.narrative_timeline(rows)
        if tl:
            tl_df = pd.DataFrame([{"阶段": c.get("narrative_phase", "突发冲突"),
                                   "时间": c["date"], "事件": c["title"]} for c in tl])
            st.dataframe(tl_df, width="stretch", hide_index=True)

        # 三层视角（宏观-中观-微观）
        st.markdown("**🔍 三层视角**（政策层/地方层/现场层）")
        l3 = data_online.three_layer_view(rows)
        if l3:
            l3_df = pd.DataFrame(l3)
            st.dataframe(l3_df, width="stretch", hide_index=True)

        # 证据来源分级（六类证据交叉印证）
        st.markdown("**📑 证据来源分布**（六类证据交叉印证）")
        ev = data_online.evidence_summary(rows)
        st.dataframe(pd.DataFrame(ev), width="stretch", hide_index=True)

        # 横向对照验证（同类灾害不同处置效果对比）
        st.markdown("**⚖️ 横向对照验证**（同类灾害不同处置效果）")
        cm = pd.DataFrame(data_online.comparison_matrix())
        if not cm.empty:
            # 修复(2026-10-30)：原 transform_stack(pivot=...) 为无效 altair API(TypeError)；
            # 长表(cm: 案例/维度/评分)直接 mark_bar 即自动堆叠
            st.altair_chart(
                alt.Chart(cm).mark_bar().encode(
                    x="案例:N", y="评分:Q", color="维度:N",
                    tooltip=["案例", "维度", "评分"]),
                width="stretch")

        t1, t2, t3 = st.tabs(["📈 图表", "📋 表格", "📖 案例复盘卡"])
        with t1:
            st.markdown("**震级分布**")
            # 修复(2026-10-30)：原 groupby(...)[...].count() 的 index 名与 Series 名
            # 均为"震级"，reset_index 冲突(ValueError)；改用 size() 并重命名，区间转字符串
            hist = (df.groupby(pd.cut(df["震级"], bins=[0, 4, 5, 6, 8, 12]), observed=False)
                      .size().rename("次数").reset_index())
            hist["震级"] = hist["震级"].astype(str)
            st.altair_chart(
                alt.Chart(hist)
                .mark_bar().encode(x="震级:N", y="次数:Q", tooltip=["震级", "次数"]),
                width="stretch")
            st.markdown("**震中空间分布（在线）**")
            # 修复(2026-10-30)：原 mark_circle(size="mag") 把字段名传给了像素参数；
            # 大小映射应放 encode(size=...)
            chart = (alt.Chart(df.assign(lon=df["经度"], lat=df["纬度"], mag=df["震级"]))
                     .mark_circle()
                     .encode(x="lon:Q", y="lat:Q", size="mag:Q", color="mag:Q",
                              tooltip=["标题", "时间", "震级", "区域"])
                     .properties(width=700, height=420))
            st.altair_chart(chart, width="stretch")
        with t2:
            st.dataframe(df, width="stretch")
            st.caption(f"数据源：USGS (online) · 抓取于 {dataset['fetched_at']} · 无本地缓存文件")
        with t3:
            st.markdown("点击案例查看 **过程线 → 动因 → 可迁移经验 + 证据强度**：")
            sel = st.selectbox("选择案例", [r["title"] for r in rows], index=0)
            c = next(r for r in rows if r["title"] == sel)
            col_a, col_b = st.columns([1, 1])
            with col_a:
                st.markdown(f"**事件过程线**（{len(c.get('process', []))} 步）")
                for i, s in enumerate(c.get("process", []), 1):
                    st.markdown(f"{i}. {s}")
                st.markdown(f"**可迁移经验**：{c.get('transferable','')}")
            with col_b:
                st.markdown(f"**动因分析**：{c.get('cause','')}")
                st.markdown(f"**证据类型**：{c.get('evidence_type','')} · "
                            f"**强度 {c.get('evidence_strength','—')}/4** · "
                            f"**叙事阶段**：{c.get('narrative_phase','')}")
    else:
        st.info("未命中在线数据，换关键词或调低震级。")


# =====================================================================
# ③ 应急方案模块（流程 / 责任人 / 触发条件 / 处置步骤）
# =====================================================================
def tab_plan():
    st.title("应急方案模块")
    st.caption("基于 GB/T 29639-2020 三级预案体系：环节 → 触发条件 → 责任人 → 处置步骤")

    plans = data_online.EMERGENCY_PLANS
    sel = st.selectbox("选择应急环节", [p["name"] for p in plans], index=0)
    p = next(x for x in plans if x["name"] == sel)

    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.markdown(f"**触发条件**\n{p['trigger']}")
        st.markdown(f"**责任人**\n{p['owner']}")
        st.markdown(f"**响应级别**\n{p['level']}")
    with col_b:
        st.markdown("**处置步骤**")
        for i, s in enumerate(p["steps"], 1):
            st.markdown(f"{i}. {s}")

    st.markdown("**处置流程链**")
    flow = pd.DataFrame({"stage": p["flow"], "owner": p["flow_owners"]})
    chart = (alt.Chart(flow).mark_rect().encode(
        x="stage:N", y=alt.value(1),
        # 修复(2026-10-30)：alt.condition 不收 pandas Series（altair6.x TypeError），改用表达式谓词；
        # 逻辑不变：报告/判级→橙(#F07C24)，其他→蓝(#4a76d9)
        color=alt.condition("datum.stage == '报告' || datum.stage == '判级'",
                            alt.value("#F07C24"), alt.value("#4a76d9")),
        tooltip=["stage", "owner"])
        .properties(width=560, height=120))
    st.altair_chart(chart, width="stretch")


# =====================================================================
# ④ 实时天气仪表盘（在线 Open-Meteo）
# =====================================================================
def tab_weather():
    st.title("实时天气仪表盘（在线）")
    st.caption("在线地理编码 + Open-Meteo 实时拉取（温度/风速/降水/湿度）· 无本地存储")

    city = st.text_input("城市（在线搜索）", value="北京")
    coord = data_online.geocode_online(city.strip())
    if coord:
        lat, lon, name = coord[0], coord[1], coord[2]
    else:
        lat, lon, name = 39.9, 116.4, city
        st.warning("在线地理编码未命中，使用默认坐标 (39.9, 116.4)")

    w = data_online.fetch_weather(lat, lon, name)
    if w.get("available"):
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("温度", f"{w['temperature_2m']} °C")
        k2.metric("风速", f"{w['wind_speed_10m']} m/s")
        k3.metric("降水", f"{w['precipitation']} mm")
        k4.metric("湿度", f"{w.get('relative_humidity_2m', '—')} %")
        st.info(f"城市：{w['city']} · 观测时间：{w['time']} · 来源：{w['source']}")

        # 在线可视化：天气仪表盘
        df = pd.DataFrame([
            {"项": "温度(°C)", "值": w["temperature_2m"]},
            {"项": "风速(m/s)", "值": w["wind_speed_10m"]},
            {"项": "降水(mm)", "值": w["precipitation"]},
            {"项": "湿度(%)", "值": w.get("relative_humidity_2m", 0)},
        ])
        st.altair_chart(
            alt.Chart(df).mark_bar().encode(
                x="项:N", y="值:Q", color="项:N",
                tooltip=["项", "值"]).properties(width=560, height=320),
            width="stretch")
    else:
        st.warning(f"在线天气获取失败：{w.get('error')}")


# =====================================================================
# ⑤ 灾害数据可视化（历史灾害事件 · 分省 choropleth，Nature 系制图规范）
# =====================================================================
def tab_academic():
    st.title("灾害数据可视化 · 历史灾害事件态势")
    st.caption("数据：编纂事件集（2009–2026 重大灾害，来源：应急管理部/中国气象局/水利部/"
               "自然资源部/USGS）+ USGS 历史地震动态补充 · 分类依据《自然灾害分类》五大类")

    try:
        from viz_academic import render_academic_figures
        from disaster_history import load_events, filter_events, usgs_history, CATEGORIES
    except Exception as e:
        st.warning(f"灾害数据可视化依赖未就绪（{e}）：需 matplotlib 环境（requirements 已含）")
        return

    c1, c2, c3 = st.columns([1, 1, 2])
    d1 = c1.date_input("时间窗 起", value=pd.Timestamp("2009-01-01").date())
    d2 = c2.date_input("时间窗 止", value=pd.Timestamp("2026-12-31").date())
    cats = c3.multiselect("灾害大类（五大类）", CATEGORIES, default=CATEGORIES)

    with st.expander("对比时间窗（生成差值图，可选）", expanded=False):
        use_cmp = st.toggle("启用差值图（RdBu_r：蓝=减少 红=增加）", value=False)
        cc1, cc2 = st.columns(2)
        e1 = cc1.date_input("对比窗 起", value=pd.Timestamp("2015-01-01").date(), disabled=not use_cmp)
        e2 = cc2.date_input("对比窗 止", value=pd.Timestamp("2019-12-31").date(), disabled=not use_cmp)

    merge_usgs = st.toggle("并入 USGS 历史地震（在线补充）", value=False)

    period = (str(d1), str(d2))
    events = filter_events(load_events(), start=period[0], end=period[1],
                           categories=cats or None)
    if merge_usgs:
        events = events + usgs_history(period[0], period[1], min_mag=5.0)

    compare_period = (str(e1), str(e2)) if use_cmp else None

    k1, k2, k3 = st.columns(3)
    provs = {e.get("province", "") for e in events if e.get("province")}
    k1.metric("事件总数", len(events))
    k2.metric("覆盖省级行政区", len(provs))
    k3.metric("涉及大类数", len({e.get("category") for e in events}))

    # viz 模块约定：compare_period 提供即自动追加差值图（对比窗事件由模块内部重算）
    render_academic_figures(events, period=period, compare_period=compare_period)

    st.caption("底图：GS(2020)4619 号标准地图（本地优先）/ 阿里 DataV GeoAtlas（云端兜底），底图无修改 · "
               "色带：YlOrRd 顺序 / RdBu_r 发散 · 制图要素：南海诸岛 inset、九段线、指北针、比例尺")

    # 来源清单（display-first：来源必须像参考文献一样列清单 + 可点击原始链接）
    with st.expander("📑 数据来源清单（含可点击原始链接）", expanded=False):
        src_rows = [{"日期": e["date"], "事件": e["name"], "大类": e["category"],
                     "子类": e["subtype"], "来源": e.get("source", ""),
                     "原始链接": e.get("source_url", "—")}
                    for e in events if e.get("source")]
        if src_rows:
            st.dataframe(pd.DataFrame(src_rows), width="stretch", hide_index=True)
            n_url = sum(1 for r in src_rows if r["原始链接"] != "—")
            st.caption(f"当前筛选 {len(src_rows)} 条，全部附来源链接。"
                       "2026-10-28 新增条目为事件专属官方通报页；早期编纂条目链接指向来源机构权威栏目页"
                       "（应急管理部历年《全国自然灾害基本情况》/中国地震台网历史地震查询/中央气象台台风网/"
                       "自然资源部《中国海洋灾害公报》等，可检索对应年份资料），非事件专属页。")
        else:
            st.caption("当前筛选条件下无事件。")


# ---------------- 主流程 ----------------
tab = st.sidebar.radio("模块",
                       ["🔍 在线搜索·可视化", "📊 灾害数据可视化", "🗺 在线态势地图", "🧭 应急方案模块", "⚡ 实时天气仪表盘"],
                       index=0)
if tab.startswith("🔍"):
    tab_search_viz()
elif tab.startswith("📊"):
    tab_academic()
elif tab.startswith("🗺"):
    tab_map()
elif tab.startswith("🧭"):
    tab_plan()
else:
    tab_weather()
