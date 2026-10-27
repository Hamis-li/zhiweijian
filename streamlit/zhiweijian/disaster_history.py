# -*- coding: utf-8 -*-
"""知危鉴 · 中国历史灾害事件数据模块（教学演示用）。

数据来源与编纂原则
==================
1. 本模块收录的中国历史自然灾害事件，均来自公开权威报道与官方通报，
   包括：应急管理部（全国自然灾害基本情况通报、事故灾害调查报告）、
   中国气象局（台风/寒潮/暴雨等预警与灾情通报）、国家防总与水利部
   （洪涝、干旱、凌汛）、自然资源部（地质灾害、海洋灾害预警）、
   国家海洋局（风暴潮、海冰、赤潮通报）、中国地震局、USGS（美国地质
   调查局全球地震目录）、农业农村部/国家林业和草原局（生物灾害）等。
2. 坐标（lat/lon）为事件的代表性震中或灾害发生地，精度为市/县级，
   仅用于地图可视化与统计聚合，不作为工程定位依据。
3. severity 取值 1-4，对应应急预警颜色：1=蓝色（一般）、2=黄色（较大）、
   3=橙色（重大）、4=红色（特别重大），依据伤亡与直接经济损失综合定级。
4. 仅收录自然灾害，不收录安全生产事故（如化工爆炸、矿山事故等一律不收）。
5. 本数据仅用于教学演示与统计分析，编纂时如有口径差异，以官方通报为准。

分类体系
========
严格按照我国《自然灾害分类》口径分为五大类，子类→大类映射见
SUBTYPE_TO_CATEGORY。编纂约定：
- 暴雨/洪涝默认归入"气象灾害"（平台统计口径约定）；
- 泥石流与滑坡、崩塌同属山地灾害链，归入"地质灾害"；
- 风暴潮、海啸按用户口径归入"海洋灾害"；
- 凌汛、溃坝归入"水文灾害"。
"""

import json
import urllib.request
from datetime import datetime

# ---------------------------------------------------------------------------
# 分类体系
# ---------------------------------------------------------------------------

# 我国《自然灾害分类》五大类
CATEGORIES = ["气象灾害", "地质灾害", "水文灾害", "海洋灾害", "生物灾害"]

# 子类 -> 大类映射表
# 编纂约定：
#   1) 洪涝/暴雨默认归"气象灾害"（平台统计口径统一约定）；
#   2) 泥石流归"地质灾害"（与滑坡、崩塌同属山地地质灾害链）；
#   3) 风暴潮、海啸虽属水文类灾害，但按用户口径归入"海洋灾害"；
#   4) 凌汛、溃坝归"水文灾害"。
SUBTYPE_TO_CATEGORY = {
    # —— 气象灾害 ——
    "暴雨": "气象灾害",
    "洪涝": "气象灾害",
    "干旱": "气象灾害",
    "台风": "气象灾害",
    "龙卷风": "气象灾害",
    "大风": "气象灾害",
    "沙尘暴": "气象灾害",
    "寒潮": "气象灾害",
    "霜冻": "气象灾害",
    "冰冻": "气象灾害",
    "暴雪": "气象灾害",
    "冰雹": "气象灾害",
    "雷暴": "气象灾害",
    "高温热浪": "气象灾害",
    # —— 地质灾害 ——
    "地震": "地质灾害",
    "滑坡": "地质灾害",
    "泥石流": "地质灾害",
    "崩塌": "地质灾害",
    "地面塌陷": "地质灾害",
    "地裂缝": "地质灾害",
    # —— 水文灾害 ——
    "凌汛": "水文灾害",
    "溃坝": "水文灾害",
    # —— 海洋灾害 ——
    "风暴潮": "海洋灾害",
    "海啸": "海洋灾害",
    "赤潮": "海洋灾害",
    "海冰": "海洋灾害",
    "海平面上升": "海洋灾害",
    # —— 生物灾害 ——
    "虫害": "生物灾害",
    "鼠害": "生物灾害",
    "病害": "生物灾害",
    "外来生物入侵": "生物灾害",
}

# severity 与预警颜色对应
SEVERITY_COLORS = {1: "蓝色", 2: "黄色", 3: "橙色", 4: "红色"}

# ---------------------------------------------------------------------------
# 历史灾害事件库（2010—2024 为主，仅自然灾害）
# 字段：id / name / category / subtype / date(YYYY-MM-DD) / lat / lon /
#       province / severity(1-4, 蓝黄橙红) / source
# ---------------------------------------------------------------------------

EVENTS = [
    # ============ 气象灾害：暴雨洪涝 ============
    {"id": "hw-001", "name": "吉林永吉特大洪水", "category": "气象灾害", "subtype": "暴雨",
     "date": "2010-07-28", "lat": 43.7, "lon": 126.5, "province": "吉林", "severity": 2,
     "source": "国家防总洪涝灾害通报"},
    {"id": "hw-002", "name": "北京'7·21'特大暴雨", "category": "气象灾害", "subtype": "暴雨",
     "date": "2012-07-21", "lat": 39.7, "lon": 116.1, "province": "北京", "severity": 4,
     "source": "中国气象局灾情通报、北京市政府灾后通报"},
    {"id": "hw-003", "name": "四川盆地'7·9'暴雨洪涝（都江堰特大山洪）", "category": "气象灾害", "subtype": "暴雨",
     "date": "2013-07-09", "lat": 31.0, "lon": 103.6, "province": "四川", "severity": 3,
     "source": "中国气象局、应急管理部全国自然灾害基本情况通报"},
    {"id": "hw-004", "name": "长江中下游梅雨期特大暴雨", "category": "气象灾害", "subtype": "暴雨",
     "date": "2016-07-01", "lat": 30.6, "lon": 114.3, "province": "湖北", "severity": 3,
     "source": "中国气象局、应急管理部全国自然灾害基本情况通报"},
    {"id": "hw-005", "name": "台风'温比亚'致山东寿光洪涝", "category": "气象灾害", "subtype": "洪涝",
     "date": "2018-08-19", "lat": 36.9, "lon": 118.7, "province": "山东", "severity": 3,
     "source": "应急管理部全国自然灾害基本情况通报"},
    {"id": "hw-006", "name": "长江流域特大洪水", "category": "气象灾害", "subtype": "洪涝",
     "date": "2020-07-17", "lat": 30.3, "lon": 112.2, "province": "湖北", "severity": 3,
     "source": "应急管理部2020年全国自然灾害基本情况通报、水利部长江水利委员会"},
    {"id": "hw-007", "name": "郑州'7·20'特大暴雨", "category": "气象灾害", "subtype": "暴雨",
     "date": "2021-07-20", "lat": 34.75, "lon": 113.6, "province": "河南", "severity": 4,
     "source": "国务院河南郑州'7·20'特大暴雨灾害调查报告、应急管理部"},
    {"id": "hw-008", "name": "京津冀极端降雨（'杜苏芮'残余环流）", "category": "气象灾害", "subtype": "暴雨",
     "date": "2023-07-29", "lat": 39.9, "lon": 116.1, "province": "河北", "severity": 4,
     "source": "应急管理部2023年全国自然灾害基本情况通报、中国气象局"},
    # ============ 气象灾害：台风 ============
    {"id": "hw-009", "name": "台风'彩虹'（湛江登陆）", "category": "气象灾害", "subtype": "台风",
     "date": "2015-10-04", "lat": 21.2, "lon": 110.4, "province": "广东", "severity": 2,
     "source": "中国气象局台风年鉴"},
    {"id": "hw-010", "name": "台风'山竹'（台山登陆）", "category": "气象灾害", "subtype": "台风",
     "date": "2018-09-16", "lat": 22.25, "lon": 112.8, "province": "广东", "severity": 3,
     "source": "中国气象局、应急管理部全国自然灾害基本情况通报"},
    {"id": "hw-011", "name": "超强台风'利奇马'（温岭登陆）", "category": "气象灾害", "subtype": "台风",
     "date": "2019-08-10", "lat": 28.4, "lon": 121.4, "province": "浙江", "severity": 3,
     "source": "应急管理部2019年全国自然灾害基本情况通报"},
    {"id": "hw-012", "name": "台风'烟花'（舟山登陆）", "category": "气象灾害", "subtype": "台风",
     "date": "2021-07-25", "lat": 30.0, "lon": 122.3, "province": "浙江", "severity": 2,
     "source": "中国气象局、应急管理部全国自然灾害基本情况通报"},
    {"id": "hw-013", "name": "台风'杜苏芮'（晋江登陆）", "category": "气象灾害", "subtype": "台风",
     "date": "2023-07-28", "lat": 24.8, "lon": 118.6, "province": "福建", "severity": 3,
     "source": "应急管理部2023年全国自然灾害基本情况通报、中国气象局"},
    {"id": "hw-014", "name": "台风'苏拉'（珠海登陆）", "category": "气象灾害", "subtype": "台风",
     "date": "2023-09-02", "lat": 22.1, "lon": 113.3, "province": "广东", "severity": 1,
     "source": "中国气象局台风预警通报"},
    {"id": "hw-015", "name": "超强台风'摩羯'（文昌登陆）", "category": "气象灾害", "subtype": "台风",
     "date": "2024-09-06", "lat": 20.0, "lon": 110.9, "province": "海南", "severity": 3,
     "source": "应急管理部2024年全国自然灾害基本情况通报、中国气象局"},
    # ============ 气象灾害：干旱 ============
    {"id": "hw-016", "name": "西南五省特大干旱", "category": "气象灾害", "subtype": "干旱",
     "date": "2010-03-22", "lat": 24.9, "lon": 102.7, "province": "云南", "severity": 4,
     "source": "国家防总、应急管理部抗旱灾情通报"},
    {"id": "hw-017", "name": "河南特大夏旱（平顶山供水告急）", "category": "气象灾害", "subtype": "干旱",
     "date": "2014-07-15", "lat": 33.8, "lon": 113.2, "province": "河南", "severity": 2,
     "source": "国家防总旱情通报"},
    {"id": "hw-018", "name": "长江流域罕见夏伏旱", "category": "气象灾害", "subtype": "干旱",
     "date": "2022-08-15", "lat": 29.6, "lon": 106.5, "province": "重庆", "severity": 3,
     "source": "应急管理部2022年全国自然灾害基本情况通报"},
    {"id": "hw-019", "name": "云南冬春干旱", "category": "气象灾害", "subtype": "干旱",
     "date": "2023-04-15", "lat": 25.0, "lon": 102.7, "province": "云南", "severity": 2,
     "source": "应急管理部2023年全国自然灾害基本情况通报"},
    # ============ 气象灾害：寒潮/暴雪 ============
    {"id": "hw-020", "name": "'世纪寒潮'（广州罕见降雪）", "category": "气象灾害", "subtype": "寒潮",
     "date": "2016-01-23", "lat": 23.1, "lon": 113.3, "province": "广东", "severity": 3,
     "source": "中国气象局寒潮预警与灾情通报"},
    {"id": "hw-021", "name": "全国强寒潮（北京-19.6℃创1966年来最低）", "category": "气象灾害", "subtype": "寒潮",
     "date": "2021-01-06", "lat": 39.9, "lon": 116.4, "province": "北京", "severity": 2,
     "source": "中国气象局寒潮预警通报"},
    {"id": "hw-022", "name": "东北特大暴雪（通辽特大暴雪）", "category": "气象灾害", "subtype": "暴雪",
     "date": "2021-11-07", "lat": 43.6, "lon": 122.3, "province": "内蒙古", "severity": 2,
     "source": "中国气象局暴雪预警通报"},
    {"id": "hw-023", "name": "华北黄淮寒潮暴雪", "category": "气象灾害", "subtype": "寒潮",
     "date": "2023-12-13", "lat": 38.0, "lon": 114.5, "province": "河北", "severity": 3,
     "source": "中国气象局、应急管理部2023年全国自然灾害基本情况通报"},
    # ============ 气象灾害：强对流/大风/沙尘/高温/霜冻 ============
    {"id": "hw-024", "name": "盐城阜宁EF4级龙卷风", "category": "气象灾害", "subtype": "龙卷风",
     "date": "2016-06-23", "lat": 33.8, "lon": 119.8, "province": "江苏", "severity": 4,
     "source": "中国气象局龙卷等级确认通报"},
    {"id": "hw-025", "name": "江南江淮持续高温热浪（上海40.8℃）", "category": "气象灾害", "subtype": "高温热浪",
     "date": "2013-08-01", "lat": 31.2, "lon": 121.5, "province": "上海", "severity": 2,
     "source": "中国气象局高温预警通报"},
    {"id": "hw-026", "name": "全国性强霜冻害（苹果主产区冻害）", "category": "气象灾害", "subtype": "霜冻",
     "date": "2018-04-07", "lat": 35.8, "lon": 109.4, "province": "陕西", "severity": 2,
     "source": "中国气象局、农业农村部农业气象灾害通报"},
    {"id": "hw-027", "name": "近十年最强沙尘暴（蒙古气旋）", "category": "气象灾害", "subtype": "沙尘暴",
     "date": "2021-03-15", "lat": 43.6, "lon": 111.9, "province": "内蒙古", "severity": 3,
     "source": "中国气象局沙尘暴预警通报"},
    {"id": "hw-028", "name": "江苏南通极端大风冰雹", "category": "气象灾害", "subtype": "大风",
     "date": "2021-04-30", "lat": 32.0, "lon": 120.9, "province": "江苏", "severity": 3,
     "source": "中国气象局强对流灾情通报"},
    {"id": "hw-029", "name": "苏州吴江盛泽龙卷风", "category": "气象灾害", "subtype": "龙卷风",
     "date": "2021-05-14", "lat": 30.9, "lon": 120.6, "province": "江苏", "severity": 2,
     "source": "中国气象局龙卷等级确认通报"},
    {"id": "hw-030", "name": "川渝极端高温热浪（重庆44℃）", "category": "气象灾害", "subtype": "高温热浪",
     "date": "2022-08-10", "lat": 29.6, "lon": 106.5, "province": "重庆", "severity": 3,
     "source": "中国气象局2022年高温事件评估"},
    # ============ 地质灾害：地震 ============
    {"id": "hw-031", "name": "玉树7.1级地震", "category": "地质灾害", "subtype": "地震",
     "date": "2010-04-14", "lat": 33.0, "lon": 97.0, "province": "青海", "severity": 4,
     "source": "中国地震局、USGS地震目录"},
    {"id": "hw-032", "name": "盈江5.8级地震", "category": "地质灾害", "subtype": "地震",
     "date": "2011-03-10", "lat": 24.7, "lon": 97.9, "province": "云南", "severity": 2,
     "source": "中国地震局地震目录"},
    {"id": "hw-033", "name": "芦山7.0级地震", "category": "地质灾害", "subtype": "地震",
     "date": "2013-04-20", "lat": 30.3, "lon": 103.0, "province": "四川", "severity": 3,
     "source": "中国地震局、USGS地震目录"},
    {"id": "hw-034", "name": "岷县漳县6.6级地震", "category": "地质灾害", "subtype": "地震",
     "date": "2013-07-22", "lat": 34.6, "lon": 104.0, "province": "甘肃", "severity": 3,
     "source": "中国地震局地震目录"},
    {"id": "hw-035", "name": "鲁甸6.5级地震", "category": "地质灾害", "subtype": "地震",
     "date": "2014-08-03", "lat": 27.1, "lon": 103.3, "province": "云南", "severity": 3,
     "source": "中国地震局、USGS地震目录"},
    {"id": "hw-036", "name": "景谷6.6级地震", "category": "地质灾害", "subtype": "地震",
     "date": "2014-10-07", "lat": 23.4, "lon": 100.5, "province": "云南", "severity": 2,
     "source": "中国地震局地震目录"},
    {"id": "hw-037", "name": "九寨沟7.0级地震", "category": "地质灾害", "subtype": "地震",
     "date": "2017-08-08", "lat": 33.2, "lon": 103.9, "province": "四川", "severity": 3,
     "source": "中国地震局、USGS地震目录"},
    {"id": "hw-038", "name": "长宁6.0级地震", "category": "地质灾害", "subtype": "地震",
     "date": "2019-06-17", "lat": 28.4, "lon": 104.9, "province": "四川", "severity": 2,
     "source": "中国地震局地震目录"},
    {"id": "hw-039", "name": "漾濞6.4级地震", "category": "地质灾害", "subtype": "地震",
     "date": "2021-05-21", "lat": 25.7, "lon": 99.9, "province": "云南", "severity": 2,
     "source": "中国地震局地震目录"},
    {"id": "hw-040", "name": "玛多7.4级地震", "category": "地质灾害", "subtype": "地震",
     "date": "2021-05-22", "lat": 34.8, "lon": 98.3, "province": "青海", "severity": 2,
     "source": "中国地震局、USGS地震目录"},
    {"id": "hw-041", "name": "门源6.9级地震", "category": "地质灾害", "subtype": "地震",
     "date": "2022-01-08", "lat": 37.7, "lon": 101.3, "province": "青海", "severity": 2,
     "source": "中国地震局地震目录"},
    {"id": "hw-042", "name": "泸定6.8级地震", "category": "地质灾害", "subtype": "地震",
     "date": "2022-09-05", "lat": 29.6, "lon": 102.1, "province": "四川", "severity": 3,
     "source": "应急管理部、中国地震局地震灾情通报"},
    {"id": "hw-043", "name": "积石山6.2级地震", "category": "地质灾害", "subtype": "地震",
     "date": "2023-12-18", "lat": 35.8, "lon": 102.8, "province": "甘肃", "severity": 3,
     "source": "应急管理部2023年全国自然灾害基本情况通报、中国地震局"},
    {"id": "hw-044", "name": "乌什7.1级地震", "category": "地质灾害", "subtype": "地震",
     "date": "2024-01-23", "lat": 41.3, "lon": 79.2, "province": "新疆", "severity": 2,
     "source": "中国地震局、USGS地震目录"},
    # ============ 地质灾害：滑坡/崩塌/泥石流 ============
    {"id": "hw-045", "name": "舟曲特大山洪泥石流", "category": "地质灾害", "subtype": "泥石流",
     "date": "2010-08-08", "lat": 33.8, "lon": 104.4, "province": "甘肃", "severity": 4,
     "source": "国务院舟曲灾后调查报告、应急管理部"},
    {"id": "hw-046", "name": "深圳光明新区'12·20'渣土受纳场滑坡", "category": "地质灾害", "subtype": "滑坡",
     "date": "2015-12-20", "lat": 22.77, "lon": 113.94, "province": "广东", "severity": 3,
     "source": "国务院深圳光明新区'12·20'滑坡灾害调查报告"},
    {"id": "hw-047", "name": "茂县新磨村高位山体滑坡", "category": "地质灾害", "subtype": "滑坡",
     "date": "2017-06-24", "lat": 31.73, "lon": 103.87, "province": "四川", "severity": 4,
     "source": "原国土资源部、应急管理部地质灾害通报"},
    {"id": "hw-048", "name": "纳雍普洒村山体崩塌", "category": "地质灾害", "subtype": "崩塌",
     "date": "2017-08-28", "lat": 26.7, "lon": 105.3, "province": "贵州", "severity": 3,
     "source": "自然资源部地质灾害通报"},
    {"id": "hw-049", "name": "乡宁枣岭乡山体滑坡", "category": "地质灾害", "subtype": "滑坡",
     "date": "2019-03-15", "lat": 35.9, "lon": 110.5, "province": "山西", "severity": 2,
     "source": "应急管理部地质灾害通报"},
    {"id": "hw-050", "name": "水城鸡场镇特大山体滑坡", "category": "地质灾害", "subtype": "滑坡",
     "date": "2019-07-23", "lat": 26.4, "lon": 104.95, "province": "贵州", "severity": 3,
     "source": "应急管理部2019年全国自然灾害基本情况通报"},
    {"id": "hw-051", "name": "恩施沙子坝滑坡及清江堰塞湖", "category": "地质灾害", "subtype": "滑坡",
     "date": "2020-07-21", "lat": 30.5, "lon": 109.4, "province": "湖北", "severity": 2,
     "source": "自然资源部地质灾害通报"},
    {"id": "hw-052", "name": "镇雄凉水村山体滑坡", "category": "地质灾害", "subtype": "滑坡",
     "date": "2024-01-22", "lat": 27.4, "lon": 104.8, "province": "云南", "severity": 3,
     "source": "应急管理部2024年地质灾害灾情通报"},
    # ============ 海洋灾害 ============
    {"id": "hw-053", "name": "渤海及黄海北部严重海冰", "category": "海洋灾害", "subtype": "海冰",
     "date": "2010-01-15", "lat": 39.5, "lon": 120.5, "province": "辽宁", "severity": 2,
     "source": "国家海洋局海洋灾害通报"},
    {"id": "hw-054", "name": "福建沿海赤潮", "category": "海洋灾害", "subtype": "赤潮",
     "date": "2012-05-30", "lat": 25.5, "lon": 119.8, "province": "福建", "severity": 1,
     "source": "国家海洋局赤潮应急通报"},
    {"id": "hw-055", "name": "台风'菲特'风暴潮（余姚洪涝）", "category": "海洋灾害", "subtype": "风暴潮",
     "date": "2013-10-07", "lat": 30.0, "lon": 121.2, "province": "浙江", "severity": 2,
     "source": "国家海洋局海洋灾害公报"},
    {"id": "hw-056", "name": "超强台风'威马逊'风暴潮", "category": "海洋灾害", "subtype": "风暴潮",
     "date": "2014-07-18", "lat": 20.0, "lon": 110.9, "province": "海南", "severity": 4,
     "source": "国家海洋局海洋灾害公报、应急管理部灾情通报"},
    # ============ 水文灾害 ============
    {"id": "hw-057", "name": "黄河杭锦旗奎素段凌汛决口", "category": "水文灾害", "subtype": "凌汛",
     "date": "2009-03-20", "lat": 40.7, "lon": 108.7, "province": "内蒙古", "severity": 2,
     "source": "水利部黄河防凌通报、新华社报道"},
    {"id": "hw-058", "name": "山西洪洞曲亭水库溃坝险情致下游受淹", "category": "水文灾害", "subtype": "溃坝",
     "date": "2013-02-15", "lat": 36.2, "lon": 111.7, "province": "山西", "severity": 2,
     "source": "水利部水库险情通报、新华社报道"},
    # ============ 生物灾害 ============
    {"id": "hw-059", "name": "草地贪夜蛾首次入侵为害", "category": "生物灾害", "subtype": "虫害",
     "date": "2019-01-11", "lat": 22.6, "lon": 101.9, "province": "云南", "severity": 3,
     "source": "农业农村部草地贪夜蛾防控通报"},
    {"id": "hw-060", "name": "黄淮麦区小麦条锈病偏重流行", "category": "生物灾害", "subtype": "病害",
     "date": "2020-04-10", "lat": 32.5, "lon": 112.5, "province": "河南", "severity": 2,
     "source": "农业农村部农作物病虫害监测通报"},
    {"id": "hw-061", "name": "云南黄脊竹蝗入侵（中老边境）", "category": "生物灾害", "subtype": "虫害",
     "date": "2020-07-06", "lat": 21.5, "lon": 101.5, "province": "云南", "severity": 2,
     "source": "国家林业和草原局、农业农村部虫情通报"},
    {"id": "hw-062", "name": "红火蚁扩散蔓延（12省435县）", "category": "生物灾害", "subtype": "外来生物入侵",
     "date": "2021-03-30", "lat": 23.1, "lon": 113.3, "province": "广东", "severity": 2,
     "source": "农业农村部等九部门红火蚁联合防控行动通报"},
]

# 数据合法性自检：确保 EVENTS 中每条记录字段完整、子类映射一致
for _e in EVENTS:
    _required = {"id", "name", "category", "subtype", "date", "lat", "lon",
                 "province", "severity", "source"}
    assert _required.issubset(_e.keys()), f"事件 {_e.get('id')} 缺少字段"
    assert _e["category"] in CATEGORIES, f"事件 {_e['id']} 大类非法"
    assert SUBTYPE_TO_CATEGORY.get(_e["subtype"]) == _e["category"], \
        f"事件 {_e['id']} 子类 {_e['subtype']} 与大类 {_e['category']} 不一致"
    assert 1 <= _e["severity"] <= 4, f"事件 {_e['id']} severity 越界"
    assert len(_e["date"]) == 10, f"事件 {_e['id']} 日期格式应为 YYYY-MM-DD"


# ---------------------------------------------------------------------------
# 数据访问函数
# ---------------------------------------------------------------------------

def load_events() -> list:
    """返回历史灾害事件列表（深拷贝，避免调用方污染原始数据）。"""
    return [dict(e) for e in EVENTS]


def filter_events(events, start=None, end=None, categories=None, provinces=None):
    """按时间范围 / 大类 / 省份过滤事件。

    :param events: 事件列表（load_events() 或 usgs_history() 的返回值）
    :param start: 起始日期 "YYYY-MM-DD"（含），None 表示不限
    :param end: 结束日期 "YYYY-MM-DD"（含），None 表示不限
    :param categories: 大类列表（如 ["气象灾害", "地质灾害"]），None 表示不限
    :param provinces: 省份列表（如 ["四川", "云南"]），None 表示不限
    :return: 过滤后的事件列表
    """
    result = []
    for e in events:
        if start and e.get("date", "") < start:
            continue
        if end and e.get("date", "") > end:
            continue
        if categories and e.get("category") not in categories:
            continue
        if provinces and e.get("province") not in provinces:
            continue
        result.append(e)
    return result


def aggregate_by_province(events) -> dict:
    """按省份聚合事件统计。

    :return: {province: {"count": n, "by_category": {cat: n}, "max_severity": x}}
             province 为空字符串的事件归入 "未知"。
    """
    agg = {}
    for e in events:
        prov = e.get("province") or "未知"
        bucket = agg.setdefault(prov, {"count": 0, "by_category": {}, "max_severity": 0})
        bucket["count"] += 1
        cat = e.get("category", "未知")
        bucket["by_category"][cat] = bucket["by_category"].get(cat, 0) + 1
        sev = e.get("severity", 0) or 0
        if sev > bucket["max_severity"]:
            bucket["max_severity"] = sev
    return agg


def usgs_history(start: str, end: str, min_mag: float = 5.0) -> list:
    """从 USGS 地震目录获取中国及周边区域的历史地震（实时接口）。

    查询范围为 lat 15-55 / lon 70-140（覆盖中国陆域及周边），返回结构
    与本地事件 dict 一致，category 固定为"地质灾害"、subtype 为"地震"，
    province 留空（USGS 目录不含中国省级行政区划，如需省份归属可由
    调用方依据 lat/lon 二次判定）。

    :param start: 起始日期 "YYYY-MM-DD"
    :param end: 结束日期 "YYYY-MM-DD"
    :param min_mag: 最小震级，默认 5.0
    :return: 事件 dict 列表；网络异常或超时（15s）时返回空列表
    """
    url = (
        "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"
        f"&starttime={start}&endtime={end}"
        "&minlatitude=15&maxlatitude=55&minlongitude=70&maxlongitude=140"
        f"&minmagnitude={min_mag}"
    )
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []

    result = []
    for feat in data.get("features", []):
        props = feat.get("properties") or {}
        coords = (feat.get("geometry") or {}).get("coordinates") or [0.0, 0.0, 0.0]
        mag = props.get("mag") or 0.0
        ts_ms = props.get("time")
        date = ""
        if ts_ms:
            date = datetime.utcfromtimestamp(ts_ms / 1000.0).strftime("%Y-%m-%d")
        if mag >= 7.5:
            severity = 4
        elif mag >= 6.5:
            severity = 3
        elif mag >= 5.8:
            severity = 2
        else:
            severity = 1
        place = props.get("place") or ""
        result.append({
            "id": f"usgs-{feat.get('id', '')}",
            "name": f"M{mag:.1f}地震 {place}".strip(),
            "category": "地质灾害",
            "subtype": "地震",
            "date": date,
            "lat": coords[1],
            "lon": coords[0],
            "province": "",
            "severity": severity,
            "source": "USGS地震目录",
        })
    return result
