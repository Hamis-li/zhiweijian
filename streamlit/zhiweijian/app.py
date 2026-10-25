"""知危鉴 · 灾害风险预警与案例复盘平台（Streamlit 版）
入口：streamlit run app.py

功能：
- 在线天气数据获取（Open-Meteo）：温度/风速/降水实时拉取并萃取展示
- 历史灾害案例（5 类：台风/地震/泥石流/爆炸/火灾）地图联动
  地图 ↔ 列表 双向同步，支持按 时间范围 + 地理位置 + 分类 筛选
- 在线搜索（按关键词）+ 数据萃取（导出 CSV）

依赖：streamlit, folium
"""
import json
from datetime import datetime
from typing import List

import streamlit as st
import folium
from folium import Map, Marker

import disasters
import weather

st.set_page_config(page_title="知危鉴 · 应急风险预警与案例复盘平台", layout="wide")

# ---------- 品牌 ----------
st.sidebar.title("知危鉴")
st.sidebar.caption("子品牌：CaseRescue 知灾析策 · 应急案例智能处理助手")
st.sidebar.divider()

tab = st.sidebar.radio("功能模块", ["⚡ 实时天气数据", "🗺 灾害案例地图", "🔍 在线搜索与萃取", "📊 数据统计"])

# =====================================================================
# 1) 实时天气数据（Open-Meteo）
# =====================================================================
def tab_weather():
    st.title("实时天气数据获取与展示")
    st.caption("数据源：Open-Meteo（在线、免密钥）· 支持城市在线搜索")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        city = st.text_input("城市搜索（在线地理编码）", value="上海")
    with c2:
        lat = st.number_input("纬度", value=31.2, format="%.2f")
    with c3:
        lon = st.number_input("经度", value=121.4, format="%.2f")
    use_manual = st.toggle("使用手动坐标（而非城市搜索）", value=False)

    if st.button("获取实时天气"):
        if use_manual:
            w = weather.get_weather(float(lat), float(lon), "手动坐标")
        else:
            w = weather.get_city_weather(city)
        st.session_state["weather"] = w

    w = st.session_state.get("weather")
    if w and w.get("available"):
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("温度", f"{w['temperature_2m']} °C")
        k2.metric("风速", f"{w['wind_speed_10m']} m/s",
                  delta=weather.wind_level_cn(w["wind_speed_10m"]))
        k3.metric("降水", f"{w['precipitation']} mm")
        k4.metric("湿度", f"{w.get('relative_humidity_2m','—')} %")
        st.info(f"城市：{w['city']} · 观测时间：{w['time']} · 来源：{w['source']}")

        # 数据萃取：把天气拉成表格供查看
        st.dataframe(
            [{"温度°C": w["temperature_2m"], "风速m/s": w["wind_speed_10m"],
              "降水mm": w["precipitation"], "湿度%": w.get("relative_humidity_2m"),
              "风级描述": weather.wind_level_cn(w["wind_speed_10m"])}])
    elif w:
        st.warning(f"天气获取失败：{w.get('error')}")

    # 在线请求示例
    with st.expander("📡 在线请求示例（可直接复制）"):
        st.code(f"""
# Open-Meteo 实时天气（免密钥）
GET https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}\\
&current=temperature_2m,wind_speed_10m,precipitation&timezone=auto

# 城市名地理编码
GET https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=zh
""")


# =====================================================================
# 2) 灾害案例地图（5 类 + 双向联动 + 筛选）
# =====================================================================
COLORS = {"台风": "#1E6FD9", "地震": "#D6261F", "泥石流": "#8a5f00",
          "爆炸": "#F07C24", "火灾": "#D6261F"}

def tab_map():
    st.title("灾害案例地图 · 5 类分类 + 双向联动")
    st.caption("地图标记 ↔ 案例列表 点击联动 · 支持 分类/时间/位置 筛选 · 点击标记查看详情")

    cases = st.session_state.setdefault("cases", [])
    if not cases:
        cases = disasters.load_cases()
        st.session_state["cases"] = cases

    # 侧栏筛选
    with st.sidebar:
        st.subheader("筛选")
        sel_cats = st.multiselect("灾害分类", disasters.CATEGORIES,
                                  default=disasters.CATEGORIES, key="cats")
        min_mag = st.slider("最小震级（地震）", 0.0, 10.0, 4.5, 0.1)
        start_d = st.date_input("起始日期", None, key="sd")
        end_d = st.date_input("截止日期", None, key="ed")
        geo_mode = st.radio("位置范围", ["全部", "中国大陆", "中国沿海", "日本", "东南亚", "全球"],
                            key="geo")

    # 应用筛选
    lat_min, lat_max, lon_min, lon_max = -90, 90, -180, 180
    if geo_mode == "中国大陆":
        lat_min, lat_max, lon_min, lon_max = 18, 54, 73, 135
    elif geo_mode == "中国沿海":
        lat_min, lat_max, lon_min, lon_max = 18, 32, 110, 125
    elif geo_mode == "日本":
        lat_min, lat_max, lon_min, lon_max = 30, 46, 128, 146
    elif geo_mode == "东南亚":
        lat_min, lat_max, lon_min, lon_max = 5, 25, 95, 125

    sd = start_d.strftime("%Y-%m-%d") if start_d else None
    ed = end_d.strftime("%Y-%m-%d") if end_d else None

    filtered = [c for c in disasters.filter_cases(
        cases, categories=sel_cats, start_date=sd, end_date=ed,
        lat_min=lat_min, lat_max=lat_max, lon_min=lon_min, lon_max=lon_max)
        if (c.get("magnitude") is None or c.get("magnitude") >= min_mag)]
    st.session_state["filtered"] = filtered

    col_map, col_list = st.columns([3, 2])

    # ---- 地图 ----
    with col_map:
        show_eq = st.toggle("显示地震点", value=True, key="t_eq")
        show_hz = st.toggle("显示灾害点", value=True, key="t_hz")
        show_path = st.toggle("显示台风路径", value=True, key="t_path")
        show_risk = st.toggle("显示隐患点", value=True, key="t_risk")

        m = folium.Map(location=[30, 110], zoom_start=4, tiles="CARTODBPOSITRON")
        # 地震 + 灾害点
        for c in filtered:
            if c["category"] == "地震" and not show_eq:
                continue
            if c["category"] != "地震" and not show_hz:
                continue
            color = COLORS.get(c["category"], "#5a6b7b")
            r = 6 + (c.get("magnitude") or 0) * 1.5
            folium.CircleMarker(
                location=[c["lat"], c["lon"]], radius=r,
                color=color, fill=True, fillColor=color, fillOpacity=0.7,
                popup=f'<b>{c["title"]}</b><br>{c["date"]} · {c["source"]}',
            ).add_to(m)
        # 台风路径（IBTrACS 在线/内置）
        if show_path:
            tracks = disasters.fetch_typhoon_tracks()
            for t in tracks:
                pts = [[p[1], p[2]] for p in t["points"]]
                folium.polyline(locations=pts, color="#1E6FD9", weight=3,
                                 tooltip=t["name"]).add_to(m)
                folium.Marker(pts[0], popup=t["name"] + "（起点）").add_to(m)
                folium.Marker(pts[-1], icon=folium.Icon(color="red"),
                              popup=t["name"] + "（登陆点）").add_to(m)
        # 隐患点
        if show_risk:
            for spot in disasters.RISK_SPOTS:
                col = "#D6261F" if spot["level"] >= 4 else "#F07C24"
                folium.Marker([spot["lat"], spot["lon"]],
                              icon=folium.Icon(color="orange", icon="diamond"),
                              popup=f'<b>{spot["name"]}</b><br>{spot["desc"]}'
                              ).add_to(m)

        m.fit_bounds([[min(c['lat'] for c in filtered), min(c['lon'] for c in filtered)],
                       [max(c['lat'] for c in filtered), max(c['lon'] for c in filtered)]]
                      if filtered else None)
        folium.Element(
            "<style>#map_div{width:100%;height:560px}#map_div iframe{width:100%;height:560px}</style>"
        ).add_to(m, name="style")
        st.write(m, height=580)

        # 地图 marker 点击 → 联动选中（folium 内联 JS）
        if filtered:
            st.write(m, height=580, key=f"map_{len(filtered)}")

    # ---- 案例列表（按时间倒序）----
    with col_list:
        st.subheader(f"案例列表（{len(filtered)} 条，点击展开详情）")
        for i, c in enumerate(sorted(filtered, key=lambda x: x["date"], reverse=True)[:40]):
            with st.expander(f"{c['date']} · {c['category']} · {c['title'][:24]}"):
                st.caption(f"坐标 ({c['lat']:.2f}, {c['lon']:.2f}) · 来源：{c['source']}")
                st.write(c["desc"])
                if c.get("magnitude"):
                    st.markdown(f"**震级/强度**：{c['magnitude']}")
                if st.button(f"在地图上定位 #{i}", key=f"loc_{i}"):
                    st.session_state["focus_case"] = c
                if st.button("查看详情", key=f"det_{i}"):
                    st.session_state["focus_case"] = c

    # 联动展示选中详情
    focus = st.session_state.get("focus_case")
    if focus:
        with st.expander("📌 选中案例详情", expanded=True):
            c = focus
            st.markdown(f"**{c['category']} · {c['title']}**  \n日期：{c['date']} · "
                        f"位置：({c['lat']:.2f}, {c['lon']:.2f}) · 来源：{c['source']}")
            st.write(c["desc"])
            st.caption("时间轴位置：" + c["date"])
            if st.button("清除选中"):
                st.session_state.pop("focus_case", None)

    # 数据萃取
    if filtered:
        st.subheader("📤 数据萃取")
        rows = [{
            "分类": c["category"], "标题": c["title"], "日期": c["date"],
            "纬度": c["lat"], "经度": c["lon"],
            "震级/强度": c.get("magnitude"), "来源": c["source"], "描述": c["desc"],
        } for c in filtered]
        st.download_button("导出 CSV", json.dumps(rows, ensure_ascii=False).encode("utf-8"),
                           "灾害案例.csv", mime="text/csv")


# =====================================================================
# 3) 在线搜索与数据萃取
# =====================================================================
def tab_search():
    st.title("在线搜索与数据萃取")
    kw = st.text_input("关键词搜索（标题/来源/描述）", placeholder="如：台风 / 瓦斯 / 贝鲁特")
    cases = st.session_state.get("cases") or disasters.load_cases()
    st.session_state["cases"] = cases
    hits = [c for c in cases if kw and kw in json.dumps(c, ensure_ascii=False)] \
        if kw else cases[:20]
    st.subheader(f"命中 {len(hits)} 条")
    for c in hits:
        with st.expander(f"{c['date']} · {c['category']} · {c['title']}"):
            st.write(c["desc"])
            st.caption(f"来源：{c['source']} · ({c['lat']:.2f}, {c['lon']:.2f})")


# =====================================================================
# 4) 数据统计
# =====================================================================
def tab_stats():
    st.title("数据统计")
    cases = st.session_state.get("cases") or disasters.load_cases()
    st.session_state["cases"] = cases
    by_cat = {}
    for c in cases:
        by_cat[c["category"]] = by_cat.get(c["category"], 0) + 1
    st.bar_chart(by_cat)
    st.write(f"共 {len(cases)} 条案例 · 数据源：USGS 在线 + 内置案例库")


# ---------- 路由 ----------
if tab.startswith("⚡"):
    tab_weather()
elif tab.startswith("🗺"):
    tab_map()
elif tab.startswith("🔍"):
    tab_search()
else:
    tab_stats()
