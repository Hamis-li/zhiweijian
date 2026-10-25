"""天气数据获取模块 —— 从 Open-Meteo 在线 API 实时拉取。

- 免密钥、可直接运行。
- 支持按坐标或按城市名（内置地理编码）获取 当前温度/风速/降水。
- st.cache_data 缓存 5 分钟，避免频繁请求。
- 离线/失败时返回 None，UI 层做降级展示。
"""
from datetime import datetime, timezone
from typing import Optional
import urllib.request, urllib.parse, json

import streamlit as st

# Open-Meteo 免密钥端点
_FORECAST = "https://api.open-meteo.com/v1/forecast"
_GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"

# 内置常用城市坐标（离线地理编码兜底）
_CITY_COORDS = {
    "北京": (39.9042, 116.4074), "上海": (31.2304, 121.4737),
    "广州": (23.1291, 113.2644), "深圳": (22.5431, 114.0579),
    "成都": (30.5728, 104.0668), "武汉": (30.5928, 114.3055),
    "西安": (34.3416, 108.9398), "杭州": (30.2741, 120.1552),
    "重庆": (29.4316, 106.9112), "青岛": (36.0671, 120.3826),
    "天津": (39.3434, 117.5881), "大连": (38.9140, 121.6434),
    "湛江": (21.2710, 110.3594), "三亚": (18.2528, 109.5119),
    "宁波": (29.8683, 121.5440), "厦门": (24.4798, 118.0894),
    "福州": (26.0745, 119.2965), "南京": (32.0603, 118.7969),
}


def _http_get_json(url: str, timeout: int = 10) -> Optional[dict]:
    """带代理容错的 JSON 获取。"""
    req = urllib.request.Request(url, headers={"User-Agent": "zhiweijian/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def geocode(city: str) -> Optional[tuple]:
    """城市名 → (lat, lon)。优先在线地理编码，失败回退内置字典。"""
    # 1) 内置字典
    c = _CITY_COORDS.get(city.strip())
    if c:
        return c
    # 2) Open-Meteo geocoding（在线）
    q = urllib.parse.urlencode({"name": city, "count": 1, "language": "zh"})
    data = _http_get_json(f"{_GEOCODE}/?{q}")
    if data and data.get("results"):
        r = data["results"][0]
        return (r["latitude"], r["longitude"])
    return None


@st.cache_data(ttl=300, show_spinner=False)
def get_weather(lat: float, lon: float, city: str = "") -> dict:
    """拉取指定坐标的实时天气（温度/风速/降水），返回统一结构。"""
    q = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon,
        "current": "temperature_2m,wind_speed_10m,wind_direction_10m,precipitation,relative_humidity_2m",
        "timezone": "auto",
    })
    data = _http_get_json(f"{_FORECAST}?{q}")
    if not data:
        return {"available": False, "city": city, "error": "Open-Meteo 接口不可达"}
    cur = data.get("current", {})
    time_info = cur.get("time", "")
    return {
        "available": True,
        "city": city or f"({lat:.2f},{lon:.2f})",
        "temperature_2m": cur.get("temperature_2m"),
        "wind_speed_10m": cur.get("wind_speed_10m"),
        "wind_direction_10m": cur.get("wind_direction_10m"),
        "precipitation": cur.get("precipitation"),
        "relative_humidity_2m": cur.get("relative_humidity_2m"),
        "time": time_info,
        "source": "Open-Meteo (online)",
    }


@st.cache_data(ttl=300)
def get_city_weather(city: str) -> dict:
    """按城市名获取天气（内部做地理编码）。"""
    coord = geocode(city)
    if coord is None:
        return {"available": False, "city": city, "error": "城市未识别"}
    return get_weather(coord[0], coord[1], city)


def wind_level_cn(speed_ms: Optional[float]) -> str:
    """风速(m/s) → 风级描述（用于展示与风险判断）。"""
    if speed_ms is None:
        return "—"
    if speed_ms >= 32.7:
        return "超强(>12级)"
    if speed_ms >= 24.5:
        return "12级(飓风)"
    if speed_ms >= 20.8:
        return "11级(强台风)"
    if speed_ms >= 17.2:
        return "10级(台风)"
    if speed_ms >= 13.9:
        return "9级(强风)"
    if speed_ms >= 10.8:
        return "8级(大风)"
    if speed_ms >= 7.5:
        return "6-7级"
    if speed_ms >= 5.0:
        return "4-5级"
    return "微风"
