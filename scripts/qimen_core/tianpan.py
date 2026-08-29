"""
天盘排布模块（九星飞布）

核心算法（转盘奇门）：
1. 找值符星：旬首隐仪在地盘哪一宫 → 该宫的原始九星 = 值符星
2. 找值符落宫：时干在地盘哪一宫 → 值符星连带天盘干旋转至此宫
3. 转盘：所有九星按顺时针整体转位

注意：中五宫寄坤二宫（天禽寄天芮）
"""
from dipan import find_gan_gong

# 九星原始宫位
JIUXING = {
    1: "天蓬", 2: "天芮", 3: "天冲", 4: "天辅",
    5: "天禽", 6: "天心", 7: "天柱", 8: "天任", 9: "天英",
}

# 顺时针宫位排列（跳过中5，用于转盘）
ZHUAN_ORDER = [1, 8, 3, 4, 9, 2, 7, 6]


def bu_tianpan(dipan: dict, xunshou_info: dict, shi_gan: str) -> dict:
    """
    排天盘（九星）+ 天盘干

    Returns:
        {
            "tianpan_xing": dict,       # {宫位: 九星名}
            "tianpan_gan": dict,        # {宫位: 天盘干}
            "zhifu_xing": str,          # 值符星名
            "zhifu_orig_gong": int,     # 值符星原始宫位
            "zhifu_luo_gong": int,      # 值符落宫
        }
    """
    yinyi = xunshou_info["隐仪"]

    # 1. 旬首隐仪在地盘哪一宫 → 值符星原始宫位
    zhifu_orig_gong = find_gan_gong(dipan, yinyi)
    zhifu_xing = JIUXING.get(zhifu_orig_gong, JIUXING[2])

    # 2. 时干在地盘哪一宫 → 值符落宫
    zhifu_luo_gong = find_gan_gong(dipan, shi_gan)

    # 3. 转盘：所有九星按顺时针整体转位
    # 中5寄坤2
    orig_actual = zhifu_orig_gong if zhifu_orig_gong != 5 else 2
    target_actual = zhifu_luo_gong if zhifu_luo_gong != 5 else 2

    orig_pos = ZHUAN_ORDER.index(orig_actual) if orig_actual in ZHUAN_ORDER else 0
    target_pos = ZHUAN_ORDER.index(target_actual) if target_actual in ZHUAN_ORDER else 0
    shift = target_pos - orig_pos

    tianpan_xing = {}
    tianpan_gan = {}

    for i, gong in enumerate(ZHUAN_ORDER):
        src_idx = (i - shift) % 8
        src_gong = ZHUAN_ORDER[src_idx]
        tianpan_xing[gong] = JIUXING.get(src_gong, "")
        tianpan_gan[gong] = dipan.get(src_gong, "")

    # 中5宫特殊处理（天禽寄坤二）
    tianpan_xing[5] = "天禽"
    tianpan_gan[5] = dipan.get(5, dipan.get(2, ""))

    return {
        "tianpan_xing": tianpan_xing,
        "tianpan_gan": tianpan_gan,
        "zhifu_xing": zhifu_xing,
        "zhifu_orig_gong": zhifu_orig_gong,
        "zhifu_luo_gong": zhifu_luo_gong if zhifu_luo_gong != 5 else 2,
    }
