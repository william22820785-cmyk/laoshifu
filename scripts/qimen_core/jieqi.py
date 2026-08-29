"""
节气判定与三元计算模块

实现：
- 当前所在节气判定
- 三元（上/中/下元）计算 — 符头查找法
- 阴阳遁与局数定夺
"""
# 阳遁局数表（上元/中元/下元）
YANGDUN_JU = {
    "冬至": [1, 7, 4], "小寒": [2, 8, 5], "大寒": [3, 9, 6],
    "立春": [8, 5, 2], "雨水": [9, 6, 3], "惊蛰": [1, 7, 4],
    "春分": [3, 9, 6], "清明": [4, 1, 7], "谷雨": [5, 2, 8],
    "立夏": [4, 1, 7], "小满": [5, 2, 8], "芒种": [6, 3, 9],
}

# 阴遁局数表（上元/中元/下元）
YINDUN_JU = {
    "夏至": [9, 3, 6], "小暑": [8, 2, 5], "大暑": [7, 1, 4],
    "立秋": [2, 5, 8], "处暑": [1, 4, 7], "白露": [9, 3, 6],
    "秋分": [7, 1, 4], "寒露": [6, 9, 3], "霜降": [5, 8, 2],
    "立冬": [6, 9, 3], "小雪": [5, 8, 2], "大雪": [4, 7, 1],
}

# 符头映射（六十甲子序号 → 元）
# 0=上元, 1=中元, 2=下元
FUTOU_MAP = {
    0: 0,    # 甲子 → 上元
    30: 0,   # 甲午 → 上元
    16: 0,   # 己卯 → 上元
    46: 0,   # 己酉 → 上元
    50: 1,   # 甲寅 → 中元
    20: 1,   # 甲申 → 中元
    26: 1,   # 己丑 → 中元
    56: 1,   # 己未 → 中元
    40: 2,   # 甲辰(戌) → 下元
    10: 2,   # 甲戌 → 下元
    6: 2,    # 己巳 → 下元
    36: 2,   # 己亥 → 下元
}

YUAN_NAMES = ["上元", "中元", "下元"]


def is_yangdun(jieqi_name: str) -> bool:
    """判断是否阳遁"""
    return jieqi_name in YANGDUN_JU


def is_yindun(jieqi_name: str) -> bool:
    """判断是否阴遁"""
    return jieqi_name in YINDUN_JU


def determine_yuan(day_ganzhi_idx: int) -> int:
    """
    确定三元（拆补法）

    符头查找规则：
    - 从当前日柱的六十甲子序号往回找5天内的符头
    - 符头 = 甲子/己卯/甲午/己酉 → 上元
    - 符头 = 甲寅/己丑/甲申/己未 → 中元
    - 符头 = 甲辰/己巳/甲戌/己亥 → 下元

    Returns:
        0=上元, 1=中元, 2=下元
    """
    adjusted_idx = day_ganzhi_idx % 60
    for back in range(5):
        check_idx = (adjusted_idx - back) % 60
        if check_idx in FUTOU_MAP:
            return FUTOU_MAP[check_idx]
    return 0  # 默认上元


def determine_ju_num(jieqi_name: str, yuan: int) -> tuple:
    """
    根据节气和三元确定局数

    Returns:
        (ju_num: int, is_yang: bool)
    """
    if jieqi_name in YANGDUN_JU:
        return YANGDUN_JU[jieqi_name][yuan], True
    if jieqi_name in YINDUN_JU:
        return YINDUN_JU[jieqi_name][yuan], False
    # 默认返回阳遁1局
    return 1, True


def get_jushu(jieqi_name: str, day_ganzhi_idx: int) -> dict:
    """
    完整定局：根据节气名和日柱序号计算局数信息

    Returns:
        {
            "ju_num": int,         # 局数 1~9
            "is_yang": bool,       # True=阳遁, False=阴遁
            "yin_yang": str,       # "阳遁" / "阴遁"
            "jieqi": str,          # 节气名
            "yuan": str,           # "上元"/"中元"/"下元"
            "method": str          # "拆补"
        }
    """
    yuan_idx = determine_yuan(day_ganzhi_idx)

    if jieqi_name in YANGDUN_JU:
        ju_num = YANGDUN_JU[jieqi_name][yuan_idx]
        is_yang = True
        yin_yang = "阳遁"
    elif jieqi_name in YINDUN_JU:
        ju_num = YINDUN_JU[jieqi_name][yuan_idx]
        is_yang = False
        yin_yang = "阴遁"
    else:
        ju_num = 1
        is_yang = True
        yin_yang = "阳遁"

    return {
        "ju_num": ju_num,
        "is_yang": is_yang,
        "yin_yang": yin_yang,
        "jieqi": jieqi_name,
        "yuan": YUAN_NAMES[yuan_idx],
        "method": "拆补",
    }
