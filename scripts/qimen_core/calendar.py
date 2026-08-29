"""
日历/节气/干支计算模块

优先使用 sxtwl 精确算法，不可用时降级为近似算法（角度法）。
"""
import math
from datetime import datetime, date

# =========================== 基础常量 ============================

TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 六十甲子表 (0=甲子...59=癸亥)
JIAZI_TABLE = []
for i in range(60):
    JIAZI_TABLE.append(TIANGAN[i % 10] + DIZHI[i % 12])

# 六甲旬隐仪映射
LIUJIA_DATA = [
    {"旬首": "甲子", "隐仪": "戊", "旬空": ["戌", "亥"]},
    {"旬首": "甲戌", "隐仪": "己", "旬空": ["申", "酉"]},
    {"旬首": "甲申", "隐仪": "庚", "旬空": ["午", "未"]},
    {"旬首": "甲午", "隐仪": "辛", "旬空": ["辰", "巳"]},
    {"旬首": "甲辰", "隐仪": "壬", "旬空": ["寅", "卯"]},
    {"旬首": "甲寅", "隐仪": "癸", "旬空": ["子", "丑"]},
]

# 地支对应宫位
DIZHI_GONG = {"子": 1, "丑": 8, "寅": 8, "卯": 3, "辰": 4, "巳": 4,
              "午": 9, "未": 2, "申": 2, "酉": 7, "戌": 6, "亥": 6}

# 节气名称列表（按寿星万年历索引，冬至=0）
JIEQI_NAMES_SXTWL = [
    "冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
    "春分", "清明", "谷雨", "立夏", "小满", "芒种",
    "夏至", "小暑", "大暑", "立秋", "处暑", "白露",
    "秋分", "寒露", "霜降", "立冬", "小雪", "大雪",
]

# 节气月份（从冬月开始）
JIEQI_MONTH_MAP = {
    "大雪": 11, "冬至": 11, "小寒": 12, "大寒": 12,
    "立春": 1, "雨水": 1, "惊蛰": 2, "春分": 2,
    "清明": 3, "谷雨": 3, "立夏": 4, "小满": 4,
    "芒种": 5, "夏至": 5, "小暑": 6, "大暑": 6,
    "立秋": 7, "处暑": 7, "白露": 8, "秋分": 8,
    "寒露": 9, "霜降": 9, "立冬": 10, "小雪": 10,
}

# 节气节/气标记
JIEQI_TYPE = {
    "立春": "节", "惊蛰": "节", "清明": "节", "立夏": "节",
    "芒种": "节", "小暑": "节", "立秋": "节", "白露": "节",
    "寒露": "节", "立冬": "节", "大雪": "节", "小寒": "节",
    "雨水": "气", "春分": "气", "谷雨": "气", "小满": "气",
    "夏至": "气", "大暑": "气", "处暑": "气", "秋分": "气",
    "霜降": "气", "小雪": "气", "冬至": "气", "大寒": "气",
}

# 阳遁/阴遁节气
YANG_JIEQI = {"冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
              "春分", "清明", "谷雨", "立夏", "小满", "芒种"}
YIN_JIEQI = {"夏至", "小暑", "大暑", "立秋", "处暑", "白露",
             "秋分", "寒露", "霜降", "立冬", "小雪", "大雪"}


# =========================== sxtwl 相关 ============================

_sxtwl_available = False
try:
    import sxtwl
    _sxtwl_available = True
except ImportError:
    pass


# =========================== 干支计算 ============================

def year_ganzhi_approx(year: int) -> tuple:
    """年干支（近似，非立春分界）"""
    g = (year - 4) % 10
    z = (year - 4) % 12
    return TIANGAN[g], DIZHI[z]


def day_ganzhi_approx(year: int, month: int, day: int) -> tuple:
    """日干支（近似算法，基于已知基准日递推）
    返回 (gan, zhi, idx_in_60)
    基准：2024-02-04 = 甲子日 (idx=0)
    """
    base = date(2024, 2, 4)
    target = date(year, month, day)
    diff = (target - base).days
    idx = diff % 60
    return TIANGAN[idx % 10], DIZHI[idx % 12], idx


def hour_ganzhi(day_gan: str, hour: int) -> tuple:
    """时干支（日上起时法）
    甲己日起甲子，乙庚日起丙子，丙辛日起戊子，
    丁壬日起庚子，戊癸日起壬子
    """
    day_gan_idx = TIANGAN.index(day_gan)
    # 日干对应子时天干起点
    start_map = {0: 0, 1: 2, 2: 4, 3: 6, 4: 8,
                 5: 0, 6: 2, 7: 4, 8: 6, 9: 8}
    zi_gan = start_map[day_gan_idx]

    # 时辰地支
    shi_zhi_idx = ((hour + 1) // 2) % 12
    shi_gan_idx = (zi_gan + shi_zhi_idx) % 10
    return TIANGAN[shi_gan_idx], DIZHI[shi_zhi_idx]


def month_ganzhi_approx(year: int, jieqi_name: str) -> tuple:
    """月干支（基于节气月）"""
    # 月建：正月建寅（立春始）
    jie_months = {
        "立春": 0, "雨水": 0,    # 正月寅
        "惊蛰": 1, "春分": 1,    # 二月卯
        "清明": 2, "谷雨": 2,    # 三月辰
        "立夏": 3, "小满": 3,    # 四月巳
        "芒种": 4, "夏至": 4,    # 五月午
        "小暑": 5, "大暑": 5,    # 六月未
        "立秋": 6, "处暑": 6,    # 七月申
        "白露": 7, "秋分": 7,    # 八月酉
        "寒露": 8, "霜降": 8,    # 九月戌
        "立冬": 9, "小雪": 9,    # 十月亥
        "大雪": 10, "冬至": 10,  # 十一月子
        "小寒": 11, "大寒": 11,  # 十二月丑
    }
    month_idx = jie_months.get(jieqi_name, 0)

    # 年干决定正月天干起点
    yg, _ = year_ganzhi_approx(year)
    yg_idx = TIANGAN.index(yg)
    # 甲己之年丙作首
    month_gan_start = [2, 4, 6, 8, 0, 2, 4, 6, 8, 0]
    mg = (month_gan_start[yg_idx] + month_idx) % 10
    mz = (month_idx + 2) % 12  # 正月=寅=2
    return TIANGAN[mg], DIZHI[mz]


# =========================== 精确日历（sxtwl） ============================

def calc_sizhu_sxtwl(year: int, month: int, day: int, hour: int) -> dict:
    """使用 sxtwl 精确计算四柱和所有日历信息"""
    solar_day = sxtwl.fromSolar(year, month, day)

    # 年柱（立春为界）
    ygz = solar_day.getYearGZ(False)

    # 月柱（节气为界）
    mgz = solar_day.getMonthGZ()

    # 日柱
    dgz = solar_day.getDayGZ()

    # 时柱
    hgz = sxtwl.getShiGz(dgz.tg, hour)

    # 日柱60甲子序号
    day_idx_60 = (dgz.tg * 6 + dgz.dz * 5) % 60  # 近似，用jiazi table反向查找

    # 更可靠的方式：从已知基准日推算
    day_idx_60 = day_ganzhi_approx(year, month, day)[2]

    # 查找当前所在节气
    current_jieqi = _find_current_jieqi_sxtwl(solar_day, year, month, day, hour)

    return {
        "year_gan": TIANGAN[ygz.tg],
        "year_zhi": DIZHI[ygz.dz],
        "month_gan": TIANGAN[mgz.tg],
        "month_zhi": DIZHI[mgz.dz],
        "day_gan": TIANGAN[dgz.tg],
        "day_zhi": DIZHI[dgz.dz],
        "hour_gan": TIANGAN[hgz.tg],
        "hour_zhi": DIZHI[hgz.dz],
        "day_idx_60": day_idx_60,
        "current_jieqi": current_jieqi,
    }


def _find_current_jieqi_sxtwl(solar_day, year: int, month: int, day: int,
                               hour: int = 0, minute: int = 0) -> str:
    """
    查找当前日期所在的节气。
    基于 sxtwl 的 JD 比较时刻，精确到小时。
    """
    # 计算当前时刻的儒略日（sxtwl 使用 UTC-based JD）
    # 输入时间为北京时区 (UTC+8)，需转为 UTC 再算 JD
    from datetime import datetime, timezone, timedelta
    tz_bj = timezone(timedelta(hours=8))
    current_dt = datetime(year, month, day, hour, minute, tzinfo=tz_bj)
    current_dt_utc = current_dt.astimezone(timezone.utc)

    def dt_to_jd_utc(dt_utc):
        """将 UTC datetime 转为天文儒略日"""
        y = dt_utc.year
        m = dt_utc.month
        d = dt_utc.day + dt_utc.hour / 24.0 + dt_utc.minute / 1440.0 + dt_utc.second / 86400.0
        if m <= 2:
            y -= 1
            m += 12
        a = y // 100
        b = 2 - a + a // 4
        jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5
        return jd
    current_jd = dt_to_jd_utc(current_dt_utc)

    # 向后扫描最多 20 天找下一个节气
    for offset in range(21):
        d = solar_day.after(offset)
        if d.hasJieQi():
            jq_idx = d.getJieQi()
            jq_jd = d.getJieQiJD()
            if current_jd >= jq_jd:
                # 当前时间已经过了这个节气 → 当前节气就是这个
                return JIEQI_NAMES_SXTWL[jq_idx]
            else:
                # 还没到这个节气 → 当前节气是上一个
                return JIEQI_NAMES_SXTWL[(jq_idx - 1) % 24]

    # Fallback: 向后扫描没找到，往前找
    for offset in range(30):
        d = solar_day.before(offset + 1)
        if d.hasJieQi():
            jq_idx = d.getJieQi()
            jq_jd = d.getJieQiJD()
            if current_jd >= jq_jd:
                return JIEQI_NAMES_SXTWL[jq_idx]
            else:
                return JIEQI_NAMES_SXTWL[(jq_idx - 1) % 24]

    return "冬至"  # 兜底


def calc_sizhu_approx(year: int, month: int, day: int, hour: int) -> dict:
    """使用近似算法计算四柱"""
    yg, yz = year_ganzhi_approx(year)
    dg, dz, day_idx = day_ganzhi_approx(year, month, day)
    hg, hz = hour_ganzhi(dg, hour)

    # 节气扫描
    current_jieqi = find_current_jieqi_approx(year, month, day)

    # 月柱基于节气
    mg, mz = month_ganzhi_approx(year, current_jieqi)

    return {
        "year_gan": yg, "year_zhi": yz,
        "month_gan": mg, "month_zhi": mz,
        "day_gan": dg, "day_zhi": dz,
        "hour_gan": hg, "hour_zhi": hz,
        "day_idx_60": day_idx,
        "current_jieqi": current_jieqi,
    }


# =========================== 近似节气算法（fallback） ============================

# 节气角度（春分=0度起算，按寿星万年历索引）
JIEQI_NAMES_APPROX = [
    "春分", "清明", "谷雨", "立夏", "小满", "芒种",
    "夏至", "小暑", "大暑", "立秋", "处暑", "白露",
    "秋分", "寒露", "霜降", "立冬", "小雪", "大雪",
    "冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
]


def _jieqi_jd(year: float, angle: float) -> float:
    """计算某年某节气的儒略日（近似）"""
    jd0 = 2451259.428 + 365.2422 * (year - 2000)
    t = (jd0 - 2451545.0) / 36525.0
    # 太阳黄经近似
    L = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
    M = 357.52911 + 35999.05029 * t - 0.0001537 * t * t
    M_rad = math.radians(M)
    C = (1.914602 - 0.004817 * t) * math.sin(M_rad) \
        + 0.019993 * math.sin(2 * M_rad) \
        + 0.000289 * math.sin(3 * M_rad)
    sun_lon = (L + C) % 360
    target = angle
    diff = target - sun_lon
    if diff > 180:
        diff -= 360
    if diff < -180:
        diff += 360
    jd0 += diff / 360.0 * 365.2422
    return jd0


def _jd_to_datetime(jd: float) -> datetime:
    """儒略日转datetime"""
    jd += 0.5
    z = int(jd)
    f = jd - z
    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - int(alpha / 4)
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    dd = b - d - int(30.6001 * e) + f
    mm = e - 1 if e < 14 else e - 13
    yy = c - 4716 if mm > 2 else c - 4715
    dd_int = int(dd)
    frac = dd - dd_int
    hh = int(frac * 24)
    mi = int((frac * 24 - hh) * 60)
    try:
        return datetime(int(yy), int(mm), int(dd_int), int(hh), int(mi))
    except (ValueError, OverflowError):
        return datetime(int(yy), int(mm), 1, 0, 0)


def jieqi_of_year_approx(year: int) -> list:
    """计算某年24节气（近似算法）"""
    jieqi_list = []
    for i in range(24):
        angle = i * 15
        jd = _jieqi_jd(year, angle)
        dt = _jd_to_datetime(jd)
        name = JIEQI_NAMES_APPROX[i]
        jieqi_list.append({"name": name, "datetime": dt, "angle": angle})
    jieqi_list.sort(key=lambda x: x["datetime"])
    return jieqi_list


def find_current_jieqi_approx(year: int, month: int, day: int) -> str:
    """使用近似算法查找当前节气"""
    dt = datetime(year, month, day)
    jq_prev = jieqi_of_year_approx(year - 1)
    jq_cur = jieqi_of_year_approx(year)

    all_jq = jq_prev + jq_cur
    all_jq.sort(key=lambda x: x["datetime"])

    current = all_jq[0]["name"]
    for jq in all_jq:
        if dt >= jq["datetime"]:
            current = jq["name"]
        else:
            break
    return current


# =========================== 统一接口 ============================

def calc_sizhu(year: int, month: int, day: int, hour: int) -> dict:
    """计算四柱及日历信息，优先 sxtwl 精确算法"""
    if _sxtwl_available:
        try:
            return calc_sizhu_sxtwl(year, month, day, hour)
        except Exception:
            pass
    return calc_sizhu_approx(year, month, day, hour)


def find_xunshou(gan: str, zhi: str) -> dict:
    """按干支查找旬首"""
    g = TIANGAN.index(gan)
    z = DIZHI.index(zhi)
    diff = g  # 往回推 g 步到甲
    xun_zhi_idx = (z - diff) % 12
    xun_zhi = DIZHI[xun_zhi_idx]
    xunshou_name = "甲" + xun_zhi
    for item in LIUJIA_DATA:
        if item["旬首"] == xunshou_name:
            return item
    return LIUJIA_DATA[0]


def get_kongwang(xunshou_info: dict) -> tuple:
    """获取空亡宫位列表"""
    kong_zhi = xunshou_info["旬空"]
    kong_gong = set()
    for zhi in kong_zhi:
        if zhi in DIZHI_GONG:
            kong_gong.add(DIZHI_GONG[zhi])
    return sorted(kong_gong), kong_zhi


def get_masa(sizhu: dict) -> str:
    """计算马星（以时支冲支为马星）"""
    # 马星 = 时支的对冲支
    shi_zhi = sizhu["hour_zhi"]
    chong_map = {
        "子": "午", "丑": "未", "寅": "申", "卯": "酉",
        "辰": "戌", "巳": "亥", "午": "子", "未": "丑",
        "申": "寅", "酉": "卯", "戌": "辰", "亥": "巳",
    }
    return chong_map.get(shi_zhi, "")


def get_jiazi_index(gan: str, zhi: str) -> int:
    """获取干支在六十甲子表中的序号"""
    g_idx = TIANGAN.index(gan)
    z_idx = DIZHI.index(zhi)
    # 遍历六十甲子表找匹配
    return JIAZI_TABLE.index(gan + zhi)
