"""
人盘排布模块（八门）

核心算法（转盘奇门）：
1. 找值使门：值符原始宫位对应的八门 = 值使门
2. 值使随时支：从旬首地支到当前时支的步数，阳顺阴逆转宫
3. 八门全体顺势（与值使门同向、同步数）转盘
"""
from calendar import DIZHI

# 八门原始宫位
BAMEN = {1: "休门", 2: "死门", 3: "伤门", 4: "杜门",
         9: "景门", 6: "开门", 7: "惊门", 8: "生门"}

# 顺时针宫位排列（跳过中5）
ZHUAN_ORDER = [1, 8, 3, 4, 9, 2, 7, 6]


def bu_renpan(xunshou_info: dict, shi_zhi: str,
              zhifu_orig_gong: int, is_yang: bool) -> dict:
    """
    排人盘（八门）

    Args:
        xunshou_info: 旬首信息字典 {"旬首": "甲子", ...}
        shi_zhi:      时支
        zhifu_orig_gong: 值符原始宫位
        is_yang:      True=阳遁, False=阴遁

    Returns:
        {
            "renpan": dict,           # {宫位: 八门名}
            "zhishi_men": str,        # 值使门名
            "zhishi_men_gong": int,   # 值使门原始宫位
            "zhishi_luo_gong": int,   # 值使落宫
        }
    """
    # 1. 值使门 = 值符原宫的八门
    zhishi_men_gong = zhifu_orig_gong if zhifu_orig_gong != 5 else 2
    zhishi_men = BAMEN.get(zhishi_men_gong, "死门")

    # 2. 值使随时支：计算步数
    xunshou_str = xunshou_info["旬首"]  # "甲子" → "子"
    xunshou_zhi = xunshou_str[1]  # 取第二个字符即地支
    xunshou_zhi_idx = DIZHI.index(xunshou_zhi)
    shi_zhi_idx = DIZHI.index(shi_zhi)
    steps = (shi_zhi_idx - xunshou_zhi_idx) % 12

    # 值使门原始宫位在ZHUAN_ORDER中的位置
    if zhishi_men_gong in ZHUAN_ORDER:
        orig_pos = ZHUAN_ORDER.index(zhishi_men_gong)
    else:
        orig_pos = 0

    # 阳顺阴逆
    if is_yang:
        target_pos = (orig_pos + steps) % 8
    else:
        target_pos = (orig_pos - steps) % 8

    zhishi_luo_gong = ZHUAN_ORDER[target_pos]

    # 3. 全体转盘
    renpan = {}
    for i, gong in enumerate(ZHUAN_ORDER):
        src_idx = (i - (target_pos - orig_pos)) % 8
        src_gong = ZHUAN_ORDER[src_idx]
        renpan[gong] = BAMEN.get(src_gong, "")

    return {
        "renpan": renpan,
        "zhishi_men": zhishi_men,
        "zhishi_men_gong": zhishi_men_gong,
        "zhishi_luo_gong": zhishi_luo_gong,
    }
