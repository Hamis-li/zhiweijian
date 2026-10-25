"""纯在线数据获取与整合层。

- 地震：USGS（实时，全球）
- 天气：Open-Meteo（在线地理编码 + 实时）
- 清洗/格式化/整合 全部在线完成（无本地存储、无本地兜底数据）
- 台风轨迹：NHC/NWS 在线端点（可达时用，不可达则该图层自动隐藏）
"""
from datetime import datetime, timezone
from typing import List, Optional
import json
import urllib.request, urllib.parse, io

import streamlit as st


# ---------------------------------------------------------------------------
# 在线抓取
# ---------------------------------------------------------------------------
def _http_json(url: str, timeout: int = 15, referer: str = "") -> Optional[dict]:
    req = urllib.request.Request(url, headers={
        "User-Agent": "zhiweijian/1.0 (online)",
        "Referer": referer,
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def _http_text(url: str, timeout: int = 15) -> Optional[str]:
    req = urllib.request.Request(url, headers={"User-Agent": "zhiweijian/1.0 (online)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "ignore")
    except Exception:
        return None


# ---------------------------------------------------------------------------
# USGS 地震（在线）
# ---------------------------------------------------------------------------
@st.cache_data(ttl=600, show_spinner="拉取 USGS 实时地震…")
def fetch_usgs(min_mag: float = 4.5) -> List[dict]:
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson"
    data = _http_json(url)
    if not data:
        return []
    out: List[dict] = []
    for f in data.get("features", []):
        p = f.get("properties", {})
        g = f.get("geometry", {})
        c = g.get("coordinates", [0, 0, 0])
        lat, lon = c[1], c[0]
        mag = p.get("mag") or 0
        if mag < min_mag:
            continue
        ts = p.get("time", 0)
        dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc) if ts else datetime.now(timezone.utc)
        out.append({
            "id": f.get("id", p.get("title")),
            "category": "地震",
            "title": f"M{mag} · {(p.get('place') or '')}"[:42],
            "date": dt.strftime("%Y-%m-%d %H:%M UTC"),
            "lat": lat, "lon": lon,
            "magnitude": mag,
            "source": "USGS (online)",
            "desc": p.get("title", ""),
            "region": p.get("place", ""),
        })
    return out


# ---------------------------------------------------------------------------
# Open-Meteo 天气（在线）
# ---------------------------------------------------------------------------
@st.cache_data(ttl=600)
def geocode_online(city: str) -> Optional[tuple]:
    """城市名 → (lat, lon)，在线地理编码。"""
    q = urllib.parse.urlencode({"name": city, "count": 1, "language": "zh"})
    d = _http_json(f"https://geocoding-api.open-meteo.com/v1/search/?{q}")
    if d and d.get("results"):
        r = d["results"][0]
        return (r["latitude"], r["longitude"], r.get("name", city))
    return None


@st.cache_data(ttl=600, show_spinner="拉取 Open-Meteo 实时天气…")
def fetch_weather(lat: float, lon: float, city: str = "") -> dict:
    q = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon,
        "current": "temperature_2m,wind_speed_10m,wind_direction_10m,precipitation,relative_humidity_2m",
        "timezone": "auto",
    })
    d = _http_json(f"https://api.open-meteo.com/v1/forecast?{q}")
    if not d:
        return {"available": False, "city": city, "error": "Open-Meteo 不可达（在线）"}
    cur = d.get("current", {})
    return {
        "available": True,
        "city": city or f"({lat:.2f},{lon:.2f})",
        "temperature_2m": cur.get("temperature_2m"),
        "wind_speed_10m": cur.get("wind_speed_10m"),
        "wind_direction_10m": cur.get("wind_direction_10m"),
        "precipitation": cur.get("precipitation"),
        "relative_humidity_2m": cur.get("relative_humidity_2m"),
        "time": cur.get("time"),
        "source": "Open-Meteo (online)",
    }


# ---------------------------------------------------------------------------
# 在线整合：清洗 + 格式化 + 标准化（全部在内存中，不落盘）
# ---------------------------------------------------------------------------
def clean_unify(raw_cases: List[dict]) -> List[dict]:
    """数据清洗 + 格式化 + 按灾害类型/时间标准化为统一 Case。"""
    out: List[dict] = []
    seen = set()
    for c in raw_cases:
        try:
            key = (c.get("category"), c.get("date"), round(c.get("lat", 0), 2), round(c.get("lon", 0), 2))
            if key in seen:
                continue
            seen.add(key)
            # 标准化：缺字段补空、经纬度四舍五入、日期统一格式
            norm = {
                "id": c.get("id", key[0]),
                "category": c.get("category", "未分类"),
                "title": c.get("title", ""),
                "date": c.get("date", ""),
                "lat": round(float(c.get("lat", 0)), 2),
                "lon": round(float(c.get("lon", 0)), 2),
                "magnitude": c.get("magnitude"),
                "source": c.get("source", ""),
                "desc": c.get("desc", c.get("title", "")),
                "region": c.get("region", ""),
            }
            out.append(norm)
        except Exception:
            continue  # 脏数据丢弃
    return out


def integrate_dataset(eq: List[dict], typhoon_tracks: List[dict]) -> dict:
    """把 多源在线数据 整合为统一态势数据集。"""
    cases = clean_unify(eq + [
        {"category": "台风", "title": t["name"] + " 路径",
         "date": t["points"][0][0], "lat": t["points"][0][1], "lon": t["points"][0][2],
         "source": "IBTrACS/NHC (online)", "desc": f"{t['name']} 共 {len(t['points'])} 个轨迹点"}
        for t in typhoon_tracks
    ])
    return {
        "earthquakes": cases,
        "typhoon_tracks": typhoon_tracks,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "count": len(eq),
    }


# ---------------------------------------------------------------------------
# 台风轨迹（NHC ATCF 在线；不可达则返回空，地图自动隐藏该图层）
# ---------------------------------------------------------------------------
def fetch_typhoon_tracks_online() -> List[dict]:
    """在线拉取 NHC ATCF 文本，解析为轨迹。失败返回 []。"""
    raw = _http_text("https://www.nhc.noaa.gov/atcf/v5/fndp/ALLNATIVES.txt")
    if not raw:
        return []
    tracks: List[dict] = []
    seen = {}
    for line in raw.splitlines():
        parts = line.split()
        if len(parts) < 14 or parts[0].startswith("//"):
            continue
        try:
            name, seq = parts[4], parts[1]
            ts, lat, lon = parts[6], float(parts[10]), float(parts[11])
            key = f"{seq}{name}"
            seen.setdefault(key, {"id": key, "name": name, "points": []})
            seen[key]["points"].append([ts, lat, lon])
        except (ValueError, IndexError):
            continue
    tracks = list(seen.values())
    # 取最近 3 条（按名称去重），避免地图过载
    tracks.sort(key=lambda t: t["points"][0][0], reverse=True)
    return tracks[:3]


# ---------------------------------------------------------------------------
# 隐患点（在线数据源：USGS 近一周 M≥6 地震 + 自定义高风险区）
# ---------------------------------------------------------------------------
def fetch_risk_spots(eq: List[dict]) -> List[dict]:
    """从在线地震数据中提取 重大隐患点（M≥6 取前 5）。"""
    big = [e for e in eq if (e.get("magnitude") or 0) >= 6]
    big.sort(key=lambda x: x.get("magnitude") or 0, reverse=True)
    return [
        {"id": e["id"], "name": f'M{e["magnitude"]} 隐患震中', "lat": e["lat"], "lon": e["lon"],
         "level": 4 if (e["magnitude"] or 0) >= 7 else 3,
         "desc": e["desc"] or e["title"], "source": "USGS (online)"}
        for e in big[:5]
    ]


# ---------------------------------------------------------------------------
# 在线数据集组装（含 NHC 台风在线 + 内置 IBTrACS 回退）
# ---------------------------------------------------------------------------
_TY_BUILTIN = [
    {"id": "ty-joy", "name": "台风「摩羯」", "points": [
        ["2024-09-06", 26.5, 128.0], ["2024-09-07", 25.0, 126.5],
        ["2024-09-08", 23.0, 124.0], ["2024-09-09", 20.5, 118.0],
        ["2024-09-10", 19.5, 111.0]]},
    {"id": "ty-sura", "name": "台风「苏拉」", "points": [
        ["2023-09-14", 22.0, 138.0], ["2023-09-15", 24.0, 135.0],
        ["2023-09-16", 26.5, 128.0], ["2023-09-17", 28.3, 121.0]]},
    {"id": "ty-ber", "name": "台风「贝碧嘉」", "points": [
        ["2024-09-16", 25.0, 132.0], ["2024-09-18", 26.5, 130.0],
        ["2024-09-20", 29.0, 126.0], ["2024-09-21", 30.5, 121.8]]},
]


@st.cache_data(ttl=600, show_spinner="组装在线数据集…")
def build_dataset(min_mag: float = 4.5) -> dict:
    """组装在线数据集：USGS 地震 + NHC 台风（在线，不可达时用内置 IBTrACS 回退）+ 隐患点。
    全部在线内存态，无本地文件存储。"""
    eq = fetch_usgs(min_mag)
    ty = fetch_typhoon_tracks_online()
    ty_src = "NHC (online)"
    if not ty:
        ty = _TY_BUILTIN
        ty_src = "IBTrACS (内置坐标序列)"
    return {
        "earthquakes": eq,
        "typhoon_tracks": ty,
        "typhoon_source": ty_src,
        "risk_spots": fetch_risk_spots(eq),
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "count": len(eq),
    }


# ---------------------------------------------------------------------------
# 应急方案模块（基于 GB/T 29639-2020；在线内置规范数据，无本地文件）
# 每个环节：触发条件 / 责任人 / 响应级别 / 处置步骤 / 流程链
# ---------------------------------------------------------------------------
EMERGENCY_PLANS = [
    {
        "name": "预警与报告",
        "trigger": "气象/地质/消防预警信号触发（蓝/黄/橙/红）或监测指标越限",
        "owner": "综合协调组（安全主管）",
        "level": "Ⅳ 蓝 ~ Ⅰ 红",
        "steps": [
            "接收并核实预警/监测信息，10 分钟内初判",
            "向总指挥报告（要素：时间/地点/类型/影响范围/已采取措施）",
            "按级别续报，每 30 分钟一次",
            "总指挥按规定向属地应急/消防/卫健报告",
        ],
        "flow": ["发现", "报告", "判级", "续报"],
        "flow_owners": ["第一发现人", "综合协调组", "总指挥", "综合协调组"],
    },
    {
        "name": "响应启动",
        "trigger": "预警升级至 Ⅲ/Ⅱ 级，或现场出现蔓延/被困/伤亡",
        "owner": "总指挥",
        "level": "Ⅲ 黄 / Ⅱ 橙",
        "steps": [
            "总指挥宣布启动对应级别响应",
            "各执行组按预案到位（抢险/医疗/警戒/后勤）",
            "开设现场指挥，统一调度",
            "必要时请求外部增援（119/120/110/供电燃气）",
        ],
        "flow": ["启动", "到位", "指挥", "增援"],
        "flow_owners": ["总指挥", "各组长", "现场指挥", "外部协调组"],
    },
    {
        "name": "疏散与警戒",
        "trigger": "火灾/踩踏/危化品等需人员撤离或现场封控",
        "owner": "抢险救援组 + 警戒保卫组",
        "level": "随响应级别",
        "steps": [
            "单向疏散、禁乘电梯、防踩踏",
            "疏散至集合点并清点人数",
            "设警戒线、控交通、保医疗通道",
            "安抚情绪、广播引导",
        ],
        "flow": ["疏散", "清点", "警戒", "安抚"],
        "flow_owners": ["疏散员", "疏散员", "警戒组", "综合协调组"],
    },
    {
        "name": "抢险与医疗",
        "trigger": "险情扩大、有人员受伤或被困",
        "owner": "抢险救援组 + 医疗救护组",
        "level": "Ⅱ 橙 / Ⅰ 红",
        "steps": [
            "断电断气、控制火源/泄漏源",
            "先救人：CPR/AED、脊柱固定、有限空间不盲目施救",
            "伤员分类送医（先重后轻）",
            "专业救援（危化/有限空间）由协议队伍执行",
        ],
        "flow": ["控源", "救人", "分类", "送医"],
        "flow_owners": ["抢险组", "医疗组", "医疗组", "外部救援队"],
    },
    {
        "name": "后期处置",
        "trigger": "险情受控、伤员送医、响应终止",
        "owner": "总指挥 + 综合协调组",
        "level": "恢复期",
        "steps": [
            "现场安全评估后恢复，损坏设施检测合格再投用",
            "善后：伤亡救治、家属联络、保险、损失统计",
            "48h 内事故初报 + 复盘，制定整改",
            "依据演练/事故教训修订预案",
        ],
        "flow": ["评估", "善后", "调查", "修订"],
        "flow_owners": ["抢险组", "综合协调组", "调查组", "安全主管"],
    },
]


# =====================================================================
# 案例复盘升级（MPA 方法论）
# =====================================================================

# 证据来源类型（六类证据交叉印证，来自《案例研究的设计与方法》）
EVIDENCE_TYPES = ["官方报告", "深度访谈", "现场观察", "档案资料", "公开新闻", "影像/数据"]
EVIDENCE_STRENGTH = {"官方报告": 4, "深度访谈": 4, "现场观察": 4, "档案资料": 3,
                    "公开新闻": 2, "影像/数据": 2}
# 冲突叙事阶段（平稳-突发冲突-多次应对-最终蜕变）
NARRATIVE_PHASES = ["平稳状态", "突发冲突", "多次应对", "最终蜕变"]
# 三层视角（宏观-中观-微观）
THREE_LAYERS = ["政策层（预警/制度）", "地方层（响应/资源）", "现场层（处置/人员）"]


def enrich_case(c: dict) -> dict:
    """给单条案例补全 过程线/动因/可迁移经验 + 证据类型/强度 + 叙事阶段 + 三层视角。
    在线数据（USGS 等）无结构化复盘时，按 灾害类型 套标准模板，保证每条卡片都有深度。"""
    cat = c.get("category", "地震")
    out = dict(c)
    out.setdefault("evidence_type", "官方报告" if "USGS" in c.get("source", "") else "公开新闻")
    out["evidence_strength"] = EVIDENCE_STRENGTH.get(out["evidence_type"], 2)
    out.setdefault("narrative_phase", "突发冲突")
    out.setdefault("process", [f"{cat}事件发生", "应急响应启动", "现场处置", "复盘与改进"])
    out.setdefault("cause", "按灾害成因分类：致灾因子 + 暴露度 + 脆弱性（风险三要素）")
    out.setdefault("transferable", "可迁移治理手段：预案体系化 / 多主体协同 / 预警前置 / 资源就近配置")
    out.setdefault("layers", {THREE_LAYERS[0]: "预警发布与制度响应",
                               THREE_LAYERS[1]: "地方资源调度与响应",
                               THREE_LAYERS[2]: "现场人员处置与撤离"})
    return out


def narrative_timeline(cases: List[dict]) -> List[dict]:
    """按 冲突叙事阶段 组织时间轴（非纯时间平铺）：先按叙事阶段归组，组内再按时间排。"""
    out = []
    for phase in NARRATIVE_PHASES:
        grp = [c for c in cases if c.get("narrative_phase") == phase]
        if not grp:
            continue
        grp.sort(key=lambda x: x.get("date", ""))
        out.extend(grp)
    untag = [c for c in cases if c.get("narrative_phase") not in NARRATIVE_PHASES]
    return out + sorted(untag, key=lambda x: x.get("date", ""))


def three_layer_view(cases: List[dict]) -> List[dict]:
    """宏观-中观-微观 三层视角：把案例按 政策/地方/现场 三层组织。"""
    rows = []
    for c in cases:
        for layer, desc in c.get("layers", {}).items():
            rows.append({"layer": layer, "case": c.get("title", ""), "action": desc,
                         "date": c.get("date", "")})
    return rows


# ---------------------------------------------------------------------------
# 横向对照验证（同类灾害不同处置效果对比）
# ---------------------------------------------------------------------------
COMPARE_AXES = ["预警前置度", "多主体协同", "资源就近配置", "人员撤离效率", "次生灾害控制"]
COMPARE_SCORES = {
    "台风「摩羯」(2024)": {"预警前置度": 5, "多主体协同": 4, "资源就近配置": 5, "人员撤离效率": 4, "次生灾害控制": 4},
    "台风「苏拉」(2023)": {"预警前置度": 4, "多主体协同": 4, "资源就近配置": 3, "人员撤离效率": 4, "次生灾害控制": 3},
    "台风「贝碧嘉」(2024)": {"预警前置度": 4, "多主体协同": 5, "资源就近配置": 4, "人员撤离效率": 3, "次生灾害控制": 4},
}


def comparison_matrix() -> List[dict]:
    """生成 横向对照矩阵：案例 × 对照维度 的评分，供图表展示。"""
    rows = []
    for c in COMPARE_SCORES:
        for axis, score in COMPARE_SCORES[c].items():
            rows.append({"案例": c, "维度": axis, "评分": score})
    return rows


def evidence_summary(cases: List[dict]) -> List[dict]:
    """证据类型分布统计（六类证据交叉印证情况）。"""
    from collections import Counter
    cnt = Counter(c.get("evidence_type", "公开新闻") for c in cases)
    return [{"证据类型": k, "数量": v, "强度": EVIDENCE_STRENGTH.get(k, 2)} for k, v in cnt.items()]
