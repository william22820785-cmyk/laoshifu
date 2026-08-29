"""
神盘排布模块（八神）

核心规则：
八神从值符落宫（大值符/天盘值符星所在宫）开始排列：

阳遁八神（顺排）:
值符 → 腾蛇 → 太阴 → 六合 → 勾陈 → 朱雀 → 九地 → 九天

阴遁八神（逆排）:
值符 → 腾蛇 → 太阴 → 六合 → 白虎 → 玄武 → 九地 → 九天
"""
# 顺时针宫位排列（跳过中5）
ZHUAN_ORDER = [1, 8, 3, 4, 9, 2, 7, 6]

# 八神序列
BASHEN_YANG = ["值符", "腾蛇", "太阴", "六合", "勾陈", "朱雀", "九地", "九天"]
BASHEN_YIN = ["值符", "腾蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]


def bu_shenpan(zhifu_luo_gong: int, is_yang: bool) -> dict:
    """
    排神盘（八神）

    从值符落宫（大值符所在宫）起八神，阳顺阴逆排列。

    Args:
        zhifu_luo_gong: 值符落宫（天盘值符星所在宫）
        is_yang:        True=阳遁, False=阴遁

    Returns:
        dict: {宫位: 八神名}
        注意：中五宫无神
    """
    bashen = BASHEN_YANG if is_yang else BASHEN_YIN

    # 中5寄坤2
    actual_gong = zhifu_luo_gong if zhifu_luo_gong != 5 else 2

    if actual_gong in ZHUAN_ORDER:
        start_pos = ZHUAN_ORDER.index(actual_gong)
    else:
        start_pos = 0

    shenpan = {}
    for i, shen in enumerate(bashen):
        if is_yang:
            pos = (start_pos + i) % 8
        else:
            pos = (start_pos - i) % 8
        gong = ZHUAN_ORDER[pos]
        shenpan[gong] = shen

    return shenpan
