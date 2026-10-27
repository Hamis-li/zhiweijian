# -*- coding: utf-8 -*-
"""学术期刊风格可视化模块（Nature/PNAS 风格中国地图组图）。

提供 render_academic_figures(events, period=None, compare_period=None)：
  图1  面板 a/b —— 中国分省 choropleth（事件计数 + 单选类别计数），
       YlOrRd 顺序色带、下方横置 colorbar（单位：事件次数）、
       右下角"南海诸岛" inset 小图、左上角指北针、左下角比例尺(0-500km)。
  图2  两个时间窗的差值图（仅当 compare_period 提供时绘制），
       RdBu_r 发散色带（蓝=减少、红=增加），colorbar 用分位数断点，
       两窗均无数据的省份以 hatch="///" 斜线标注。
  图3  统计面板 —— (a) 五大类构成堆叠柱（按年份）；(b) Top10 省份横向条形；
       (c) 各类别 severity 分布小提琴图。

地理边界合规声明（最高优先级）：
  * 主边界源为自然资源部标准地图（审图号 GS(2020)4619，底图无修改）：
      省级面  省级行政区.shp（34 面，含台湾/香港/澳门；名字段 NAME，
              pyshp 按 encoding="gbk" 解码 dbf）；
      国界线  国界线.shp（GBCODE：61010=已定国界【含南海九段线各段】、
              26080=南海群岛岸线），画完省面后以细黑线叠加。
    该 shp 坐标系为 Beijing1954 Lambert Conformal Conic（投影坐标，单位
    米，量级 1e6~1e7）：检测为投影坐标时跳过 Albers 变换直接绘制；
    南海诸岛 inset 亦直接取该投影坐标并设定 xlim/ylim 至南海范围。
    使用标准底图时图注显示"底图审图号：GS(2020)4619 号（底图无修改）"。
  * BOUNDARY_PATH 文件不存在时（如 Streamlit Cloud）降级：临时目录缓存 →
    在线下载阿里云 DataV GeoAtlas（100000_full.json，经纬度+含九段线，
    此时用正轴等积圆锥投影 Albers：中央经线 105°E、双标准纬线 25°/47°N，
    坐标单位为公里，比例尺按长度绘制；图注不显示审图号）→ 仍失败则
    不绘制地图，仅 st.warning 提示配置天地图/标准地图服务数据。
    绝不使用 Natural Earth / OSM / Google Maps / Mapbox 等不合规或瓦片底图。
  * 主图与 inset 均完整包含台湾省与南海诸岛，九段线随边界数据呈现。
  * 纯 matplotlib 面状填色，不加载任何在线瓦片底图。

空间归省方法说明：事件 dict 自带 province 字段时直接使用；对缺失 province
的记录（如 USGS 地震点），先做"点在省 bbox 内"的快速筛查，再用射线法
（ray casting，纯 Python 实现，避免引入 shapely 依赖）做严格点在多边形判定。
GS 投影底图下需将经纬度转为投影坐标（优先 pyproj 读取 .prj；pyproj 缺失
时跳过空间归省，保留原 province 字段）；DataV 经纬度底图下用手工 Albers。
"""
from __future__ import annotations

import json
import math
import os
import tempfile
import urllib.request
from collections import Counter, defaultdict

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, Normalize

import streamlit as st

from disaster_history import CATEGORIES, aggregate_by_province, filter_events, load_events

# --------------------------------------------------------------------------
# 配置项
# --------------------------------------------------------------------------
# 主边界源：自然资源部标准地图（审图号 GS(2020)4619）省级面（本机绝对路径）。
# Streamlit Cloud 等云端不存在该路径时自动降级：缓存 → DataV 在线 → warning。
BOUNDARY_PATH = r"E:\ATAIFEN\SHUJU\中国标准地图-审图号GS(2020)4619号-shp格式\省级行政区.shp"
# 国界线（GBCODE 61010 已定国界含九段线 / 26080 南海群岛岸线），叠加在省面之上
BOUNDARY_LINES_PATH = r"E:\ATAIFEN\SHUJU\中国标准地图-审图号GS(2020)4619号-shp格式\国界线.shp"

_DATAV_URL = "https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json"
_CACHE_FILE = os.path.join(
    tempfile.gettempdir(), "china_province_boundary_100000_full.json"
)

_GS_NOTE = "底图审图号：GS(2020)4619 号（底图无修改）"
_DATAV_NOTE = "底图来源：阿里云 DataV GeoAtlas（100000_full，含九段线）。"

# GS 标准底图（Beijing1954 Lambert Conformal Conic）下南海诸岛 inset 范围（米）
_SCS_INSET_XLIM = (650000.0, 1620000.0)
_SCS_INSET_YLIM = (500000.0, 3200000.0)

# 中文 sans-serif 字体
_RC = {
    "font.sans-serif": ["SimHei", "Microsoft YaHei"],
    "axes.unicode_minus": False,
    "font.family": "sans-serif",
}

# 省份名称归一化用后缀（用于事件 province 字段与边界要素名的模糊匹配）
_PROV_SUFFIXES = (
    "特别行政区", "维吾尔自治区", "壮族自治区", "回族自治区", "自治区", "省", "市",
)


def _apply_rc():
    plt.rcParams.update(_RC)


# --------------------------------------------------------------------------
# 边界数据加载（GS 标准地图 → 自定义 geojson → DataV 缓存 → DataV 在线）
# --------------------------------------------------------------------------
def _shp_to_feats(path: str, encoding: str, name_field: str | None = None) -> list[dict]:
    """pyshp 读取面要素 → [{'name', 'rings':[N,2 数组(原始坐标)]}]。"""
    import shapefile  # pyshp

    sf = shapefile.Reader(path, encoding=encoding)
    fields = [f[0] for f in sf.fields[1:]]
    if name_field and name_field in fields:
        name_idx = fields.index(name_field)
    else:
        name_idx = 0
    feats = []
    for sr, rec in zip(sf.shapeRecords(), sf.records()):
        name = str(rec[name_idx]) if name_idx < len(rec) else ""
        pts = np.asarray(sr.shape.points, dtype=float)
        parts = list(sr.shape.parts) + [len(pts)]
        rings = [pts[parts[i]:parts[i + 1]] for i in range(len(parts) - 1)]
        if rings:
            feats.append({"name": name, "rings": rings})
    return feats


def _shp_to_lines(path: str, encoding: str, codes: dict) -> dict[str, list[np.ndarray]]:
    """pyshp 读取线要素，按字段取值分类 → {key: [N,2 数组]}。"""
    import shapefile  # pyshp

    out: dict[str, list[np.ndarray]] = {v: [] for v in codes.values()}
    if not os.path.exists(path):
        return out
    try:
        sf = shapefile.Reader(path, encoding=encoding)
    except Exception:
        return out
    fields = [f[0] for f in sf.fields[1:]]
    code_idx = fields.index(codes["__field__"]) if "__field__" in codes else None
    for sr, rec in zip(sf.shapeRecords(), sf.records()):
        try:
            val = int(rec[code_idx]) if code_idx is not None and code_idx < len(rec) else 0
        except (TypeError, ValueError):
            continue
        key = codes.get(val)
        if key is None:
            continue
        pts = np.asarray(sr.shape.points, dtype=float)
        parts = list(sr.shape.parts) + [len(pts)]
        for i in range(len(parts) - 1):
            seg = pts[parts[i]:parts[i + 1]]
            if len(seg) >= 2:
                out[key].append(seg)
    return out


def _make_gs_forward():
    """经纬度 → GS 底图投影坐标（Beijing1954 Lambert Conformal Conic）。

    优先 pyproj 读取同目录 .prj；pyproj 缺失时返回 None（此时跳过
    空间归省，事件 province 字段通常已存在，不影响主流程）。
    """
    try:
        from pyproj import CRS, Transformer

        prj = os.path.splitext(BOUNDARY_PATH)[0] + ".prj"
        with open(prj, "r", encoding="utf-8", errors="ignore") as f:
            wkt = f.read().strip()
        tr = Transformer.from_crs("EPSG:4326", CRS.from_wkt(wkt), always_xy=True)
        return lambda lon, lat: tr.transform(lon, lat)
    except Exception:
        return None


def _load_gs_pack() -> dict | None:
    """读取 GS(2020)4619 标准地图（pyshp，无需 geopandas）。

    返回 {'projected':True, 'main':34省面, 'border':国界线, 'island':南海群岛岸线,
          'fwd':经纬度→投影坐标函数, 'attrib':审图号图注}；失败返回 None。
    """
    if not (BOUNDARY_PATH and os.path.exists(BOUNDARY_PATH)):
        return None
    try:
        main = _shp_to_feats(BOUNDARY_PATH, "gbk", "NAME")
    except Exception:
        return None
    if not main:
        return None
    # 投影坐标检测：Lambert Conformal Conic 单位为米，量级 1e6~1e7；
    # 经纬度量级 <=180，以此分支
    sample = np.vstack(main[0]["rings"])
    projected = float(np.abs(sample).max()) > 1e5
    if not projected:
        return None  # 非标准投影底图，交由通用经纬度管线处理
    lines = _shp_to_lines(
        BOUNDARY_LINES_PATH, "gbk",
        {"__field__": "GBCODE", 61010: "border", 26080: "island"},
    )
    return {
        "projected": True,
        "main": main,
        "border": lines["border"],   # 已定国界（含南海九段线各段）
        "island": lines["island"],   # 南海群岛岸线
        "fwd": _make_gs_forward(),
        "attrib": _GS_NOTE,
    }


def _load_boundary_geojson(path: str) -> list[dict]:
    """读取 GeoJSON，返回 [{'name':str,'rings':[(lon,lat)顶点数组,...]}, ...]。"""
    with open(path, "r", encoding="utf-8") as f:
        gj = json.load(f)
    feats = []
    for ft in gj.get("features", []):
        props = ft.get("properties", {}) or {}
        name = props.get("name") or ""
        geom = ft.get("geometry") or {}
        rings: list[np.ndarray] = []
        gtype = geom.get("type")
        if gtype == "Polygon":
            rings = [np.asarray(r, dtype=float) for r in geom.get("coordinates", [])]
        elif gtype == "MultiPolygon":
            for poly in geom.get("coordinates", []):
                rings.extend(np.asarray(r, dtype=float) for r in poly)
        elif gtype == "GeometryCollection":
            for g in geom.get("geometries", []):
                if g.get("type") == "Polygon":
                    rings.extend(np.asarray(r, float) for r in g.get("coordinates", []))
                elif g.get("type") == "MultiPolygon":
                    for poly in g.get("coordinates", []):
                        rings.extend(np.asarray(r, float) for r in poly)
        if rings:
            feats.append({"name": name, "rings": rings})
    return feats


def _fetch_datav() -> list[dict] | None:
    """DataV GeoAtlas：优先临时目录缓存，否则在线下载并缓存。"""
    if os.path.exists(_CACHE_FILE):
        try:
            return _load_boundary_geojson(_CACHE_FILE)
        except Exception:
            pass
    try:
        req = urllib.request.Request(_DATAV_URL, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=20).read()
        tmp = _CACHE_FILE + ".tmp"
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, _CACHE_FILE)
        return _load_boundary_geojson(_CACHE_FILE)
    except Exception:
        return None


def load_provinces() -> dict | None:
    """加载省界要素包；失败返回 None（调用方据此降级为 warning）。

    降级链：GS(2020)4619 标准地图（本机，投影坐标直绘）→ 自定义 geojson →
    DataV GeoAtlas 缓存/在线（经纬度，Albers 投影绘制，云端兜底）。
    """
    # 1) GS 标准地图（合规性最高，审图号图注）
    pack = _load_gs_pack()
    if pack:
        return pack
    # 2) 显式指定的自定义 geojson（经纬度）
    if (
        BOUNDARY_PATH
        and BOUNDARY_PATH.lower().endswith((".geojson", ".json"))
        and os.path.exists(BOUNDARY_PATH)
    ):
        try:
            feats = _load_boundary_geojson(BOUNDARY_PATH)
            if feats:
                return {"projected": False, "main": feats, "border": [],
                        "island": [], "fwd": None, "attrib": None}
        except Exception:
            pass
    # 3) DataV GeoAtlas（含九段线，云端兜底；图注不显示审图号）
    feats = _fetch_datav()
    if feats:
        return {"projected": False, "main": feats, "border": [],
                "island": [], "fwd": None, "attrib": _DATAV_NOTE}
    return None


# --------------------------------------------------------------------------
# 投影与几何工具（纯 Python / numpy；GS 投影坐标直绘，DataV 用手工 Albers）
# --------------------------------------------------------------------------
_R_EARTH_KM = 6371.0
_PHI1, _PHI2 = math.radians(25.0), math.radians(47.0)  # 双标准纬线
_N = (math.sin(_PHI1) + math.sin(_PHI2)) / 2.0
_C = math.cos(_PHI1) ** 2 + 2.0 * _N * math.sin(_PHI1)
_RHO0 = math.sqrt(_C) / _N  # 赤道处 rho（投影原点）

_ALBERS_PARAMS = (_PHI1, _PHI2, _N, _C, _RHO0)  # ChinaAlbers: 中央经线105，标准纬线25/47


def _albers(lon: float, lat: float) -> tuple[float, float]:
    """正轴等积圆锥（Albers）投影，中央经线 105°E，返回坐标单位为公里。"""
    phi, lam = math.radians(lat), math.radians(lon - 105.0)
    rho = math.sqrt(max(_C - 2.0 * _N * math.sin(phi), 0.0)) / _N * _R_EARTH_KM
    theta = _N * lam
    x = rho * math.sin(theta)
    y = _RHO0 * _R_EARTH_KM - rho * math.cos(theta)
    return x, y


def _ring_centroid_lonlat(ring: np.ndarray) -> tuple[float, float]:
    """环质心（仅对经纬度环有意义；DataV 南海要素分流用）。"""
    return float(np.mean(ring[:, 0])), float(np.mean(ring[:, 1]))


def _point_in_ring(x: float, y: float, ring_xy: np.ndarray) -> bool:
    """射线法判断点是否在环内（纯 Python，替代 shapely）。"""
    inside = False
    n = len(ring_xy)
    j = n - 1
    for i in range(n):
        xi, yi = ring_xy[i]
        xj, yj = ring_xy[j]
        if (yi > y) != (yj > y):
            xint = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < xint:
                inside = not inside
        j = i
    return inside


def _norm_prov(name: str) -> str:
    """省份名归一化：去掉行政区后缀，便于 '广东' 与 '广东省' 匹配。"""
    s = (name or "").strip()
    for suf in _PROV_SUFFIXES:
        if s.endswith(suf):
            return s[: -len(suf)]
    return s


def _assign_province(lon: float, lat: float, prov_index: list, fwd) -> str:
    """点归省：先 bbox 粗筛，再射线法精判（见模块 docstring 方法说明）。"""
    if fwd is None:
        return ""  # 无经纬度→投影坐标转换能力时跳过（GS 底图且缺 pyproj）
    x, y = fwd(lon, lat)
    for name, bbox, rings_xy in prov_index:
        if bbox[0] <= x <= bbox[1] and bbox[2] <= y <= bbox[3]:
            if any(_point_in_ring(x, y, r) for r in rings_xy):
                return name
    return ""


# --------------------------------------------------------------------------
# disaster_history 调用封装（防御式，兼容多种可能签名）
# --------------------------------------------------------------------------
def _parse_date(v) -> str:
    s = str(v or "")[:10]
    return s if len(s) == 10 and s[4] == "-" else ""


def _safe_filter(events: list[dict], period: tuple[str, str] | None) -> list[dict]:
    """优先调用 filter_events(events, period)，失败则退回手工按 date 过滤。"""
    if period is None:
        return list(events)
    try:
        res = filter_events(events, period)
        if isinstance(res, list):
            return res
    except TypeError:
        try:
            res = filter_events(events, period[0], period[1])
            if isinstance(res, list):
                return res
        except Exception:
            pass
    except Exception:
        pass
    lo, hi = str(period[0])[:10], str(period[1])[:10]
    return [e for e in events if lo <= _parse_date(e.get("date")) <= hi]


def _safe_agg(events: list[dict]) -> dict:
    """优先调用 aggregate_by_province(events)；异常或结构不符时手工按省计数。"""
    try:
        res = aggregate_by_province(events)
        if isinstance(res, dict) and all(
            isinstance(v, (int, float)) for v in res.values()
        ):
            return {str(k): float(v) for k, v in res.items()}
    except Exception:
        pass
    return {k: float(v) for k, v in Counter(_norm_prov(e.get("province")) for e in events).items() if k}


def _ensure_province(events: list[dict], geom: dict) -> list[dict]:
    """对缺失 province 的事件做空间归省（bbox + 射线法），原字典不被修改。"""
    fwd = geom["fwd_draw"]
    out = []
    for e in events:
        if e.get("province"):
            out.append(e)
            continue
        try:
            lon, lat = float(e.get("lon")), float(e.get("lat"))
        except (TypeError, ValueError):
            out.append(e)
            continue
        e2 = dict(e)
        e2["province"] = _assign_province(lon, lat, geom["prov_index"], fwd)
        out.append(e2)
    return out


# --------------------------------------------------------------------------
# 地图绘制
# --------------------------------------------------------------------------
def _prep_geometry(pack: dict) -> dict:
    """要素包 → 绘制几何。

    GS 投影底图：坐标为 Lambert Conformal Conic（米），直接绘制（跳过
    Albers），叠加国界线/群岛岸线细黑线，inset 用固定南海范围；
    DataV 经纬度底图：手工 Albers（公里），南海要素按质心分流至 inset。
    """
    projected = pack.get("projected", False)
    if projected:
        fwd_draw = pack.get("fwd")  # 经纬度 → 底图投影坐标（可为 None）
        def to_draw(ring):
            return ring  # 省面/线要素已是投影坐标，直接绘制
        km_to_draw = 1000.0  # 米
    else:
        fwd_draw = _albers
        def to_draw(ring):
            xs, ys = [], []
            for lon, lat in np.asarray(ring, dtype=float):
                x, y = _albers(lon, lat)
                xs.append(x)
                ys.append(y)
            return np.column_stack([xs, ys])
        km_to_draw = 1.0

    main, sea, prov_index = [], [], []
    for ft in pack["main"]:
        rings_xy = [to_draw(r) for r in ft["rings"]]
        entry = {"name": ft["name"], "rings_xy": rings_xy}
        allpts = np.vstack(rings_xy)
        bbox = (float(allpts[:, 0].min()), float(allpts[:, 0].max()),
                float(allpts[:, 1].min()), float(allpts[:, 1].max()))
        prov_index.append((ft["name"], bbox, rings_xy))
        if projected:
            main.append(entry)  # GS 34 省面（最南为海南）全部留主图
        else:
            # DataV：南海诸岛/九段线独立面要素按质心分流至 inset
            cents = [_ring_centroid_lonlat(r) for r in ft["rings"]]
            lat_med = float(np.median([c[1] for c in cents])) if cents else 90.0
            lon_med = float(np.median([c[0] for c in cents])) if cents else 0.0
            if lat_med < 15.5 and lon_med >= 105.0 and ft["name"] != "海南省":
                sea.append(entry)
            else:
                main.append(entry)

    geom = {
        "projected": projected,
        "fwd_draw": fwd_draw,
        "prov_index": prov_index,
        "main": main,
        "sea": sea,
        "border": pack.get("border", []),
        "island": pack.get("island", []),
        "attrib": pack.get("attrib"),
        "km_to_draw": km_to_draw,
    }
    if projected:
        # GS 标准底图：inset 范围由数据动态计算（九段线短段 + 群岛岸线外接矩形），
        # 保证全部九段线段可见；无边数据时退回固定范围
        nine = [s for s in pack.get("border", []) if len(s) <= 40]
        sea_pts = [s for s in nine + pack.get("island", []) if len(s) >= 2]
        if sea_pts:
            ap = np.vstack(sea_pts)
            px = 0.06 * (ap[:, 0].max() - ap[:, 0].min())
            py = 0.06 * (ap[:, 1].max() - ap[:, 1].min())
            geom["inset_xlim"] = (ap[:, 0].min() - px, ap[:, 0].max() + px)
            geom["inset_ylim"] = (ap[:, 1].min() - py, ap[:, 1].max() + py)
        else:
            geom["inset_xlim"] = _SCS_INSET_XLIM
            geom["inset_ylim"] = _SCS_INSET_YLIM
    else:
        geom["inset_xlim"] = geom["inset_ylim"] = None
    return geom


def _draw_boundaries(ax, entries, fill_values=None, cmap=None, norm=None,
                     edge="0.15", lw=0.35, fill_default="white",
                     hatch_missing=False):
    """面状填色 + 省界细黑线（纯 matplotlib 多边形，无瓦片底图）。"""
    for entry in entries:
        for ring in entry["rings_xy"]:
            if len(ring) < 3:
                continue
            face = fill_default
            hatch = None
            if fill_values is not None:
                v = fill_values.get(_norm_prov(entry["name"]))
                if v is None or (isinstance(v, float) and math.isnan(v)):
                    face = "0.96"
                    if hatch_missing:
                        hatch = "///"
                else:
                    face = cmap(norm(v))
            ax.add_patch(
                plt.Polygon(ring, closed=True, facecolor=face, edgecolor=edge,
                            linewidth=lw, hatch=hatch, zorder=2)
            )


def _draw_lines(ax, lines, color="0.15", lw=1.0):
    for pts in lines:
        if len(pts) >= 2:
            ax.plot(pts[:, 0], pts[:, 1], color=color, lw=lw, zorder=3,
                    solid_capstyle="round")


def _add_north_arrow(ax):
    ax.annotate("N", xy=(0.055, 0.955), xytext=(0.055, 0.875),
                xycoords="axes fraction", textcoords="axes fraction",
                ha="center", va="center", fontsize=11, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.2),
                zorder=10)


def _add_scale_bar(ax, geom, length_km=500):
    """比例尺：GS 投影底图单位为米、DataV 单位为公里，按 km_to_draw 换算。"""
    length = length_km * geom["km_to_draw"]
    tick = 15000.0 if geom["projected"] else 8.0  # 端刻线半高（绘制坐标单位）
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    x0 = xmin + 0.04 * (xmax - xmin)
    y0 = ymin + 0.05 * (ymax - ymin)
    ax.plot([x0, x0 + length], [y0, y0], color="black", lw=2.2,
            solid_capstyle="butt", zorder=10)
    ax.plot([x0, x0], [y0 - tick, y0 + tick], color="black", lw=1.0, zorder=10)
    ax.plot([x0 + length, x0 + length], [y0 - tick, y0 + tick],
            color="black", lw=1.0, zorder=10)
    ax.text(x0 + length / 2, y0 + tick * 1.4, "0                500 km",
            ha="center", va="bottom", fontsize=8, zorder=10)


def _add_scs_inset(ax, geom):
    """右下角'南海诸岛' inset 小图（带边框，学术画法）。

    GS 投影底图：省面 + 国界线(61010 含九段线) + 群岛岸线(26080)，
    固定 xlim/ylim 至南海范围；DataV：南海诸岛面要素按外接矩形。
    """
    main, sea = geom["main"], geom["sea"]
    border, island = geom["border"], geom["island"]
    if geom["projected"]:
        if not (border or island):
            return
        ix = ax.inset_axes([0.68, 0.015, 0.30, 0.36])
        ix.set_facecolor("white")
        _draw_boundaries(ix, main, edge="0.3", lw=0.25, fill_default="white")
        _draw_lines(ix, island, color="0.3", lw=0.6)
        _draw_lines(ix, border, color="black", lw=1.3)  # 国界+九段线加粗突出
        ix.set_xlim(*geom["inset_xlim"])
        ix.set_ylim(*geom["inset_ylim"])
    else:
        if not sea:
            return
        ix = ax.inset_axes([0.68, 0.015, 0.30, 0.36])
        ix.set_facecolor("white")
        _draw_boundaries(ix, main, edge="0.3", lw=0.25, fill_default="white")
        _draw_boundaries(ix, sea, edge="0.3", lw=0.45, fill_default="white")
        pts = [r for e in sea for r in e["rings_xy"] if len(r)]
        if not pts:
            return
        pts = np.vstack(pts)
        pad = 60.0
        ix.set_xlim(pts[:, 0].min() - pad, pts[:, 0].max() + pad)
        ix.set_ylim(pts[:, 1].min() - pad, pts[:, 1].max() + pad)
    ix.set_xticks([])
    ix.set_yticks([])
    ix.set_aspect("equal")
    for sp in ix.spines.values():
        sp.set_edgecolor("black")
        sp.set_linewidth(0.9)
    ix.set_title("南海诸岛", fontsize=7, pad=1.5)


def _map_extent(ax, main_entries):
    pts = np.vstack([r for e in main_entries for r in e["rings_xy"]])
    pad = 0.03 * max(pts[:, 0].max() - pts[:, 0].min(),
                     pts[:, 1].max() - pts[:, 1].min())
    ax.set_xlim(pts[:, 0].min() - pad, pts[:, 0].max() + pad)
    ax.set_ylim(pts[:, 1].min() - pad, pts[:, 1].max() + pad)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_facecolor("white")


def _hcolorbar(fig, cmap, norm, label, cax_rect):
    """横置于子图下方的 colorbar。"""
    cax = fig.add_axes(cax_rect)
    from matplotlib.cm import ScalarMappable
    cb = fig.colorbar(ScalarMappable(norm=norm, cmap=cmap), cax=cax,
                      orientation="horizontal")
    cb.set_label(label, fontsize=9)
    cb.ax.tick_params(labelsize=8)
    return cax


def _add_attrib(fig, attrib, y=0.012):
    """合规图注：GS 标准底图显示审图号；DataV 兜底时不显示审图号（仅来源说明）。"""
    if attrib:
        fig.text(0.5, y, attrib, ha="center", va="bottom", fontsize=7.5,
                 color="0.3")


# --------------------------------------------------------------------------
# 图1：分省 choropleth（a: 总计数；b: 单选类别计数）
# --------------------------------------------------------------------------
def _fig1(events, geom, category):
    _apply_rc()
    main = geom["main"]
    counts = _safe_agg(events)
    cat_events = [e for e in events if _norm_prov(str(e.get("category") or "")) == _norm_prov(category)]
    cat_counts = _safe_agg(cat_events)

    # 无事件省份按 0 值着色（灰色仅用于图2 的无数据标注）
    all_names = {_norm_prov(e["name"]) for e in main}
    counts = {n: counts.get(n, 0.0) for n in all_names}
    cat_counts = {n: cat_counts.get(n, 0.0) for n in all_names}

    cmap = plt.get_cmap("YlOrRd")
    norm_a = Normalize(vmin=0, vmax=max(max(counts.values()), 1))
    norm_b = Normalize(vmin=0, vmax=max(max(cat_counts.values()), 1))

    fig = plt.figure(figsize=(13.2, 8.6), facecolor="white")
    axa = fig.add_axes([0.045, 0.30, 0.44, 0.60])
    axb = fig.add_axes([0.525, 0.30, 0.44, 0.60])

    for ax, vals, norm, title in (
        (axa, counts, norm_a, "(a) 事件按省计数"),
        (axb, cat_counts, norm_b, f"(b) {category}·按省计数"),
    ):
        _draw_boundaries(ax, main, fill_values=vals, cmap=cmap, norm=norm)
        # GS 标准底图：省面之上叠加国界线（含九段线）与群岛岸线细黑线
        _draw_lines(ax, geom["island"], color="0.35", lw=0.4)
        _draw_lines(ax, geom["border"], color="black", lw=0.6)
        _map_extent(ax, main)
        _add_scs_inset(ax, geom)
        _add_north_arrow(ax)
        _add_scale_bar(ax, geom)
        ax.set_title(title, fontsize=12, fontweight="bold", loc="left", pad=6)

    _hcolorbar(fig, cmap, norm_a, "事件次数", [0.10, 0.17, 0.33, 0.018])
    _hcolorbar(fig, cmap, norm_b, "事件次数", [0.58, 0.17, 0.33, 0.018])
    _add_attrib(fig, geom["attrib"], y=0.055)
    return fig


# --------------------------------------------------------------------------
# 图2：两个时间窗差值图
# --------------------------------------------------------------------------
def _fig2(events, geom, period, compare_period):
    _apply_rc()
    main = geom["main"]
    ev1 = _safe_filter(events, period)
    ev2 = _safe_filter(events, compare_period)
    c1, c2 = _safe_agg(ev1), _safe_agg(ev2)

    names = {**c1, **c2}
    diffs = {k: float(c1.get(k, 0.0)) - float(c2.get(k, 0.0)) for k in names}
    nz = np.array([v for v in diffs.values() if v != 0.0])
    if nz.size >= 5:
        # 分位数断点 colorbar
        qs = np.unique(np.quantile(nz, [0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]))
        if qs.size < 3:
            qs = np.array([nz.min(), 0.0, nz.max()])
        norm = BoundaryNorm(qs, ncolors=256, clip=True)
    elif diffs:
        vmax = max(abs(v) for v in diffs.values()) or 1.0
        norm = Normalize(vmin=-vmax, vmax=vmax)
    else:
        norm = Normalize(vmin=-1, vmax=1)
    cmap = plt.get_cmap("RdBu_r")

    fig = plt.figure(figsize=(8.6, 9.0), facecolor="white")
    ax = fig.add_axes([0.06, 0.26, 0.88, 0.64])
    _draw_boundaries(ax, main, fill_values=diffs, cmap=cmap, norm=norm,
                     hatch_missing=True)
    _draw_lines(ax, geom["island"], color="0.35", lw=0.4)
    _draw_lines(ax, geom["border"], color="black", lw=0.6)
    _map_extent(ax, main)
    _add_scs_inset(ax, geom)
    _add_north_arrow(ax)
    _add_scale_bar(ax, geom)
    ax.set_title(f"事件计数差值  {period[0]}~{period[1]} 减去 {compare_period[0]}~{compare_period[1]}",
                 fontsize=12, fontweight="bold", loc="left", pad=6)
    _hcolorbar(fig, cmap, norm, "差值（事件次数；蓝=减少，红=增加）",
               [0.22, 0.115, 0.56, 0.022])
    fig.text(0.06, 0.065, "注：斜线填充表示该时间范围内无事件记录的省份。",
             fontsize=8, color="0.35")
    _add_attrib(fig, geom["attrib"], y=0.015)
    return fig


# --------------------------------------------------------------------------
# 图3：统计面板
# --------------------------------------------------------------------------
def _fig3(events):
    _apply_rc()
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 5.2), facecolor="white")
    axa, axb, axc = axes

    # (a) 五大类构成堆叠柱（按年份）
    year_cat = defaultdict(Counter)
    for e in events:
        d = _parse_date(e.get("date"))
        cat = str(e.get("category") or "")
        if d and cat:
            year_cat[d[:4]][_norm_prov(cat)] += 1
    years = sorted(year_cat)
    cat_norm_map = {_norm_prov(c): c for c in CATEGORIES}
    ordered_cats = list(cat_norm_map)
    cat_colors = plt.get_cmap("Set2")(np.linspace(0, 1, len(ordered_cats)))
    bottom = np.zeros(len(years))
    for ci, cn in enumerate(ordered_cats):
        vals = np.array([year_cat[y].get(cn, 0) for y in years], dtype=float)
        axa.bar(years, vals, bottom=bottom, label=cat_norm_map[cn],
                color=cat_colors[ci], edgecolor="white", linewidth=0.4, width=0.72)
        bottom += vals
    axa.set_title("五类灾害构成（按年份）", fontsize=11, loc="left")
    axa.set_ylabel("事件次数")
    axa.legend(fontsize=7, frameon=False, ncol=2)
    axa.tick_params(axis="x", rotation=45, labelsize=8)

    # (b) Top10 省份横向条形
    pc = _safe_agg(events)
    top = sorted(pc.items(), key=lambda kv: kv[1], reverse=True)[:10]
    if top:
        labels = [k for k, _ in top][::-1]
        vals = [v for _, v in top][::-1]
        axb.barh(labels, vals, color="#3b6ea5", edgecolor="white", height=0.62)
        for y, v in enumerate(vals):
            axb.text(v, y, f" {int(v)}", va="center", fontsize=8)
    axb.set_title("Top10 省份", fontsize=11, loc="left")
    axb.set_xlabel("事件次数")
    axb.tick_params(labelsize=8)

    # (c) 各类别 severity 分布小提琴图
    datasets, used = [], []
    for cn in ordered_cats:
        arr = np.array([float(e.get("severity")) for e in events
                        if _norm_prov(str(e.get("category") or "")) == cn
                        and e.get("severity") is not None], dtype=float)
        if arr.size == 0:
            arr = np.array([np.nan])
        datasets.append(arr)
        used.append(cat_norm_map[cn])
    vp = axc.violinplot([d[np.isfinite(d)] if np.isfinite(d).any() else np.array([np.nan])
                         for d in datasets], showmeans=True, showmedians=False)
    for body in vp["bodies"]:
        body.set_facecolor("#d1495b")
        body.set_alpha(0.55)
        body.set_edgecolor("0.2")
    axc.set_xticks(range(1, len(used) + 1))
    axc.set_xticklabels(used, rotation=30, ha="right", fontsize=8)
    axc.set_ylabel("severity（1-4）")
    axc.set_title("severity 分布（按类别）", fontsize=11, loc="left")

    for ax, lab in zip(axes, ("(a)", "(b)", "(c)")):
        ax.text(-0.02, 1.06, lab, transform=ax.transAxes, fontsize=13,
                fontweight="bold", va="top", ha="right")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return fig


# --------------------------------------------------------------------------
# 主入口
# --------------------------------------------------------------------------
def render_academic_figures(
    events: list[dict],
    period: tuple[str, str] | None = None,
    compare_period: tuple[str, str] | None = None,
) -> None:
    """在 Streamlit 页面渲染学术期刊风格组图（图1/图2/图3）。"""
    _apply_rc()

    # events 为空时支持内部加载
    if not events:
        try:
            events = load_events()
        except Exception:
            events = []
    if not events:
        st.info("暂无事件数据，无法绘制学术图表。")
        return

    if period is not None:
        window_events = _safe_filter(events, period)
    else:
        window_events = list(events)

    pack = load_provinces()
    st.subheader("学术期刊风格组图")

    if pack:
        geom = _prep_geometry(pack)
        window_events = _ensure_province(window_events, geom)

        # 图1：a/b 面板（b 为单选类别）
        category = st.radio("图1(b) 灾害类别", list(CATEGORIES), horizontal=True,
                            index=0)
        st.caption(f"时间窗：{period[0]} ~ {period[1]}" if period else "时间窗：全部数据")
        fig1 = _fig1(window_events, geom, category)
        st.pyplot(fig1)
        plt.close(fig1)

        # 图2：差值图（仅在提供 compare_period 时绘制）
        if compare_period is not None and period is not None:
            ev_all = _ensure_province(events, geom)
            fig2 = _fig2(ev_all, geom, period, compare_period)
            st.pyplot(fig2)
            plt.close(fig2)
        elif compare_period is not None:
            st.warning("图2 差值图需要同时提供 period 与 compare_period，已跳过。")
    else:
        st.warning(
            "未配置合规省界数据（建议从天地图1:100万或标准地图服务下载），"
            "地图功能暂不可用"
        )

    # 图3：统计面板（不依赖边界数据）
    fig3 = _fig3(window_events)
    st.pyplot(fig3)
    plt.close(fig3)
