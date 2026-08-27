# -*- coding: utf-8 -*-
"""四柱算法精度审计：现有 chart.cjs 算法 vs lunar_python 权威基准"""
from lunar_python import Solar

TIAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DIZ = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

def authoritative(y, m, d, h):
    """lunar_python 权威四柱（东八区）"""
    solar = Solar.fromYmdHms(y, m, d, h, 0, 0)
    lunar = solar.getLunar()
    return (lunar.getYearInGanZhi(), lunar.getMonthInGanZhi(),
            lunar.getDayInGanZhi(), lunar.getTimeInGanZhi())

# 覆盖各种边界：1970-2000年（避开1900基准附近的歧义）
samples = [
    (2000, 1, 1, 12), (2000, 2, 4, 12), (2000, 2, 5, 12), (2000, 2, 20, 12),
    (1999, 2, 3, 12), (1999, 2, 4, 12), (2024, 2, 3, 12), (2024, 2, 4, 12),
    (2024, 2, 10, 12), (1988, 1, 1, 12), (1988, 3, 15, 8), (1995, 7, 7, 14),
    (2003, 5, 20, 6), (2010, 11, 11, 20), (2015, 8, 8, 9), (1970, 1, 1, 12),
    (1968, 10, 1, 4), (1975, 6, 15, 18), (1982, 12, 31, 23), (1998, 9, 9, 3),
    (1985, 2, 3, 12), (1985, 2, 5, 12), (1992, 8, 8, 8), (2006, 12, 25, 22),
]
print(f"{'公历':<18}{'权威日柱':<8}{'权威时柱':<8}")
print("=" * 40)
for y, m, d, h in samples:
    ygz, mgz, dgz, hgz = authoritative(y, m, d, h)
    print(f"{y}-{m:02d}-{d:02d} {h:02d}:00  {dgz:<8}{hgz}")
