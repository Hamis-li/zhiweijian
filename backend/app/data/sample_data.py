"""内置样例数据。

原 Coze 版以 5 份国务院官方事故调查报告做知识库；此处抽象为结构化案例，
保留"事件概况/风险因素/应急处置措施/经验教训"四大模块（与原知识卡片一致）。
上线时本模块可被 PostgreSQL + 向量库替换，接口契约不变。
"""
from ..models.schemas import AlertRule, CaseCard, RegionMetric

# ---------------------------------------------------------------------------
# 案例库（样本：可扩充至完整官方事故调查报告）
# ---------------------------------------------------------------------------
CASES: list[CaseCard] = [
    CaseCard(
        case_id="C-2015-08", title="某化工园区 8·4 液化气爆炸事故",
        date="2015-08-04", location="某省某市化工园区", level="特别重大",
        summary="液化石油气储罐区发生爆炸并引发连续爆燃，造成重大人员伤亡与财产损失。",
        risk_factors=["储罐区违规操作与巡检缺位", "安全防护装置失效", "园区布局间距不足", "应急处置滞后"],
        measures=["立即封锁现场并切断周边气源", "启动危化品专项预案", "消防力量分段控火并降温监护", "组织相邻企业人员疏散"],
        lessons=["强化危化品重大危险源双重预防机制", "落实安全仪表系统（SIS）可靠性检验", "优化园区风险等级与布局间距", "完善企业间应急联动"],
        tags=["化工", "爆炸", "液化气", "重大危险源"], source="国务院安委会事故调查报告（样例）",
    ),
    CaseCard(
        case_id="C-2011-09", title="某煤矿 9·20 瓦斯爆炸事故",
        date="2011-09-20", location="某省某煤矿", level="特别重大",
        summary="煤矿采掘工作面发生瓦斯爆炸并引发火灾，救援中遇二次爆炸，造成重大伤亡。",
        risk_factors=["采掘布局不合理超通风能力生产", "瓦斯监测预警不到位", "安全管理责任落实不到位"],
        measures=["紧急撤出井下人员", "切断采掘区电源防止二次爆炸", "控制通风系统防止瓦斯积聚", "开展自救互救与专业救援"],
        lessons=["严格执行通风与瓦斯管理制度", "按核定能力组织生产", "完善安全避险六大系统", "强化基层安全责任考核"],
        tags=["煤矿", "瓦斯", "爆炸", "超能力生产"], source="国务院安委会事故调查报告（样例）",
    ),
    CaseCard(
        case_id="C-2016-09", title="某化工企业 9·1 硝基氯苯灼伤及中毒事故",
        date="2016-09-01", location="某省某化工企业", level="较大",
        summary="硝基氯苯装置在检修过程中发生介质泄漏，造成现场作业人员灼伤及中毒。",
        risk_factors=["检修作业许可与隔离措施不到位", "个体防护装备配备不足", "现场应急管理缺失"],
        measures=["紧急撤离并隔离泄漏源", "现场急救与送医", "佩戴防护装备处置泄漏", "停止相关装置运行"],
        lessons=["严格动火与检维修作业许可", "强化有限空间与泄漏作业防护", "配齐应急物资与急救培训"],
        tags=["化工", "中毒", "灼伤", "检维修"], source="国务院安委会事故调查报告（样例）",
    ),
    CaseCard(
        case_id="C-2009-07", title="某钢铁厂 7·26 钢水包爆炸事故",
        date="2009-07-26", location="某省某钢铁企业", level="重大",
        summary="转炉冶炼过程中钢水与带湿物料接触，引发爆炸与钢水外溢，造成人员伤亡。",
        risk_factors=["原料含湿量控制不严", "冶炼操作不规范", "风险辨识与现场管理缺失"],
        measures=["紧急停止冶炼并疏散", "隔离危险区域", "伤员急救转运", "现场警戒与原因勘查"],
        lessons=["加强原料含水率检验", "规范冶炼操作与岗位培训", "完善岗位安全操作规程"],
        tags=["钢铁", "爆炸", "钢水", "冶炼"], source="国务院安委会事故调查报告（样例）",
    ),
    CaseCard(
        case_id="C-2014-02", title="某客运索道 2·3 坠索事故",
        date="2014-02-03", location="某省某景区", level="较大",
        summary="景区客运索道发生坠索，造成游客被困，后经救援全部安全转移。",
        risk_factors=["索道设备维护保养不到位", "突发大风等不利气象", "应急自救设施不足"],
        measures=["启动设备应急制动", "组织被困游客安抚与救援转移", "现场医疗救护"],
        lessons=["落实特种设备定期维保", "制定恶劣天气停运机制", "配齐救援与自救设施并演练"],
        tags=["特种设备", "索道", "高处", "游客"], source="国务院安委会事故调查报告（样例）",
    ),
]

# ---------------------------------------------------------------------------
# 监测指标（示例，可替换为真实流式数据）
# ---------------------------------------------------------------------------
METRICS: list[RegionMetric] = [
    RegionMetric(region="A 区", hazard="flood", metric="rainfall_24h", value=142.0, unit="mm",
                 trend=[{"ts": "10:00", "value": 18}, {"ts": "12:00", "value": 52},
                        {"ts": "14:00", "value": 96}, {"ts": "16:00", "value": 142}], status="danger"),
    RegionMetric(region="B 区", hazard="geology", metric="slope_displacement", value=12.5, unit="mm/24h",
                 trend=[{"ts": "08:00", "value": 3}, {"ts": "12:00", "value": 8},
                        {"ts": "16:00", "value": 12.5}], status="warning"),
    RegionMetric(region="C 区", hazard="fire", metric="fire_risk_index", value=71.0, unit="idx",
                 trend=[{"ts": "06:00", "value": 30}, {"ts": "12:00", "value": 55},
                        {"ts": "16:00", "value": 71}], status="warning"),
    RegionMetric(region="沿海", hazard="storm", metric="wind_speed", value=24.6, unit="m/s",
                 trend=[{"ts": "06:00", "value": 12}, {"ts": "12:00", "value": 18},
                        {"ts": "16:00", "value": 24.6}], status="normal"),
]

# ---------------------------------------------------------------------------
# 预警规则
# ---------------------------------------------------------------------------
RULES: list[AlertRule] = [
    AlertRule(id="R-F1", name="特大降雨预警", hazard="flood", metric="rainfall_24h",
              threshold=120, op=">=", triggers=4, desc="24h 累计降雨 ≥120mm 触发红色预警"),
    AlertRule(id="R-F2", name="大雨预警", hazard="flood", metric="rainfall_24h",
              threshold=50, op=">=", triggers=2, desc="24h 累计降雨 ≥50mm 触发黄色预警"),
    AlertRule(id="R-G1", name="边坡位移超限", hazard="geology", metric="slope_displacement",
              threshold=10, op=">=", triggers=3, desc="边坡 24h 位移 ≥10mm 触发橙色预警"),
    AlertRule(id="R-FR1", name="火灾高风险", hazard="fire", metric="fire_risk_index",
              threshold=60, op=">=", triggers=3, desc="火险指数 ≥60 触发橙色预警"),
    AlertRule(id="R-S1", name="大风预警", hazard="storm", metric="wind_speed",
              threshold=17.5, op=">=", triggers=2, desc="瞬时风速 ≥17.5m/s（34 节）触发黄色预警"),
]
