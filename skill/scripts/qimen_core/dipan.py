"""
地盘排布模块

三奇六仪在地盘上的飞布：
- 顺序：戊→己→庚→辛→壬→癸→丁→丙→乙
- 阳遁：从局数宫位起戊，按洛书顺飞 (1→2→3→4→5→6→7→8→9)
- 阴遁：从局数宫位起戊，按洛书逆飞 (9→8→7→6→5→4→3→2→1)
"""
# 三奇六仪排列顺序
SANQI_LIUYI = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]

# 洛书顺飞序
LUOSHU_SHUN = [1, 2, 3, 4, 5, 6, 7, 8, 9]

# 洛书逆飞序
LUOSHU_NI = [9, 8, 7, 6, 5, 4, 3, 2, 1]


def bu_dipan(ju_num: int, is_yang: bool) -> dict:
    """
    布地盘三奇六仪

    Args:
        ju_num:  局数 1~9
        is_yang: True=阳遁, False=阴遁

    Returns:
        dict: {宫位编号: 天干}
        示例: {1: "癸", 2: "己", 3: "庚", ...}
    """
    order = SANQI_LIUYI

    if is_yang:
        # 阳遁：从局数宫起戊，洛书顺飞
        route = LUOSHU_SHUN
        start_idx = route.index(ju_num)
        dipan = {}
        for i, gan in enumerate(order):
            gong = route[(start_idx + i) % 9]
            dipan[gong] = gan
    else:
        # 阴遁：从局数宫起戊，洛书逆飞
        route = LUOSHU_NI
        start_idx = route.index(ju_num)
        dipan = {}
        for i, gan in enumerate(order):
            gong = route[(start_idx + i) % 9]
            dipan[gong] = gan

    return dipan


def find_gan_gong(dipan: dict, gan: str) -> int:
    """在地盘中查找某个天干所在的宫位"""
    for gong, g in dipan.items():
        if g == gan:
            return gong
    return 2  # 默认坤二
