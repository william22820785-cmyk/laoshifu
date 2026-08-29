"""
奇门遁甲排盘引擎 — QimenEngine

时家转盘奇门（拆补法 v1.0）

用法：
    engine = QimenEngine()
    pan = engine.paipan(2026, 7, 30, 12)
    print(pan.to_json())
"""
from datetime import datetime

import calendar
import jieqi as jieqi_module
import dipan as dipan_module
import tianpan as tianpan_module
import renpan as renpan_module
import shenpan as shenpan_module
from models import (
    Sizhu, Jushu, Xunshou, ZhifuZhishi, GongData, PanResult
)

# 宫位基础数据
GONG_NAME = {1: "坎一宫", 2: "坤二宫", 3: "震三宫", 4: "巽四宫",
             5: "中五宫", 6: "乾六宫", 7: "兑七宫", 8: "艮八宫", 9: "离九宫"}
GONG_FANGWEI = {1: "北", 2: "西南", 3: "东", 4: "东南", 5: "中",
                6: "西北", 7: "西", 8: "东北", 9: "南"}
GONG_WUXING = {1: "水", 2: "土", 3: "木", 4: "木", 5: "土",
               6: "金", 7: "金", 8: "土", 9: "火"}


class QimenEngine:
    """奇门遁甲排盘引擎"""

    def __init__(self, method: str = "拆补"):
        """
        Args:
            method: 定局方法，当前仅支持 "拆补"
        """
        if method not in ("拆补",):
            raise ValueError(f"不支持的计算方法: {method}，当前仅支持「拆补」")
        self.method = method

    def paipan(self, year: int, month: int, day: int,
               hour: int, minute: int = 0, calendar_data: dict | None = None) -> PanResult:
        """
        排盘主函数

        Args:
            year, month, day: 公历日期
            hour, minute:     公历时间（24小时制）

        Returns:
            PanResult: 完整盘面结果
        """
        input_dt = datetime(year, month, day, hour, minute)

        # Step 1: 排四柱 + 日历信息。V2 优先使用外部已校准数据，
        # 避免运行环境缺少 sxtwl 时退回到低精度近似算法。
        cal = calendar_data if calendar_data is not None else calendar.calc_sizhu(year, month, day, hour)
        required = {
            "year_gan", "year_zhi", "month_gan", "month_zhi",
            "day_gan", "day_zhi", "hour_gan", "hour_zhi",
            "day_idx_60", "current_jieqi",
        }
        missing = sorted(required.difference(cal))
        if missing:
            raise ValueError(f"日历数据缺少字段: {', '.join(missing)}")

        sizhu = Sizhu(
            year_gan=cal["year_gan"], year_zhi=cal["year_zhi"],
            month_gan=cal["month_gan"], month_zhi=cal["month_zhi"],
            day_gan=cal["day_gan"], day_zhi=cal["day_zhi"],
            hour_gan=cal["hour_gan"], hour_zhi=cal["hour_zhi"],
        )

        # Step 2-3: 定节气 + 局数（三元计算）
        jieqi_name = cal["current_jieqi"]
        jushu_info = jieqi_module.get_jushu(jieqi_name, cal["day_idx_60"])

        jushu = Jushu(
            ju_num=jushu_info["ju_num"],
            yin_yang=jushu_info["yin_yang"],
            jieqi=jushu_info["jieqi"],
            method=jushu_info["method"],
            yuan=jushu_info["yuan"],
        )

        # Step 4: 查旬首（以时柱为准）
        xunshou_info = calendar.find_xunshou(sizhu.hour_gan, sizhu.hour_zhi)
        kong_gong, kong_zhi = calendar.get_kongwang(xunshou_info)
        masa = calendar.get_masa(cal)

        xunshou = Xunshou(
            xunshou=xunshou_info["旬首"],
            yinyi=xunshou_info["隐仪"],
            kong_zhi=kong_zhi,
            kong_gong=kong_gong,
            masa=masa,
        )

        # Step 5: 布地盘
        dipan = dipan_module.bu_dipan(jushu.ju_num, jushu_info["is_yang"])

        # Step 6: 排天盘（九星）
        tianpan_result = tianpan_module.bu_tianpan(dipan, xunshou_info, sizhu.hour_gan)

        zhifu_zhishi = ZhifuZhishi(
            zhifu_xing=tianpan_result["zhifu_xing"],
            zhifu_xing_gong=tianpan_result["zhifu_orig_gong"],
            zhifu_luo_gong=tianpan_result["zhifu_luo_gong"],
            zhishi_men="",   # 由人盘填充
            zhishi_men_gong=0,
            zhishi_luo_gong=0,
        )

        # Step 7: 排人盘（八门）
        renpan_result = renpan_module.bu_renpan(
            xunshou_info, sizhu.hour_zhi,
            tianpan_result["zhifu_orig_gong"],
            jushu_info["is_yang"],
        )

        zhifu_zhishi.zhishi_men = renpan_result["zhishi_men"]
        zhifu_zhishi.zhishi_men_gong = renpan_result["zhishi_men_gong"]
        zhifu_zhishi.zhishi_luo_gong = renpan_result["zhishi_luo_gong"]

        # Step 8: 排神盘（八神）
        shenpan = shenpan_module.bu_shenpan(
            tianpan_result["zhifu_luo_gong"], jushu_info["is_yang"]
        )

        # 组装九宫数据
        gongs = {}
        tianpan_xing = tianpan_result["tianpan_xing"]
        tianpan_gan = tianpan_result["tianpan_gan"]
        renpan = renpan_result["renpan"]

        for gong in range(1, 10):
            gong_data = GongData(
                gong_num=gong,
                gong_name=GONG_NAME[gong],
                fangwei=GONG_FANGWEI[gong],
                wuxing=GONG_WUXING[gong],
                dipan_gan=dipan.get(gong, ""),
                tianpan_gan=tianpan_gan.get(gong, dipan.get(gong, "")),
                jiuxing=tianpan_xing.get(gong, ""),
                bamen=renpan.get(gong, ""),
                bashen=shenpan.get(gong, ""),
                is_kong=gong in kong_gong,
            )
            if gong == 5:
                gong_data.beizhu = "天禽寄坤二宫"
                gong_data.bamen = ""
                gong_data.bashen = ""
            gongs[gong] = gong_data

        # 盘面校验（反吟/伏吟/门迫检测）
        _verify_pan(gongs, dipan, tianpan_xing, renpan, jushu_info["is_yang"])

        return PanResult(
            input_time=input_dt,
            sizhu=sizhu,
            jushu=jushu,
            xunshou=xunshou,
            zhifu_zhishi=zhifu_zhishi,
            gongs=gongs,
        )


def _verify_pan(gongs: dict, dipan: dict, tianpan_xing: dict,
                renpan: dict, is_yang: bool) -> None:
    """
    盘面一致性校验：反吟、伏吟、门迫检测。
    直接修改 gongs 中每个宫位的标记。
    """
    # 宫位五行
    gong_wuxing = GONG_WUXING
    # 门五行
    men_wuxing = {"休门": "水", "死门": "土", "伤门": "木", "杜门": "木",
                  "景门": "火", "开门": "金", "惊门": "金", "生门": "土"}
    # 九星原始宫位
    xing_orig = {"天蓬": 1, "天芮": 2, "天冲": 3, "天辅": 4,
                 "天禽": 5, "天心": 6, "天柱": 7, "天任": 8, "天英": 9}
    # 八门原始宫位
    men_orig = {"休门": 1, "死门": 2, "伤门": 3, "杜门": 4,
                "景门": 9, "开门": 6, "惊门": 7, "生门": 8}

    # 反吟检测（星门到对冲宫）
    duichong = {1: 9, 9: 1, 2: 8, 8: 2, 3: 7, 7: 3, 4: 6, 6: 4}

    # 五行生克
    wuxing_ke = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

    for gong_num, gong_data in gongs.items():
        if gong_num == 5:
            continue

        # 伏吟：天盘干 = 地盘干
        if gong_data.tianpan_gan == gong_data.dipan_gan:
            gong_data.fu_yin = True

        # 反吟：天盘干与地盘干互为对冲宫的天干
        #  简化：星是否到对冲宫
        if gong_data.jiuxing:
            star_orig_gong = xing_orig.get(gong_data.jiuxing, gong_num)
            if star_orig_gong in duichong and duichong[star_orig_gong] == gong_num:
                gong_data.fan_yin = True
        if gong_data.bamen:
            men_orig_gong = men_orig.get(gong_data.bamen, gong_num)
            if men_orig_gong in duichong and duichong[men_orig_gong] == gong_num:
                gong_data.fan_yin = True

        # 门迫：宫克门（宫的五行克门的五行）
        if gong_data.bamen:
            mw = men_wuxing.get(gong_data.bamen, "")
            gw = gong_wuxing.get(gong_num, "")
            if mw and gw and wuxing_ke.get(gw, "") == mw:
                gong_data.men_po = True


def format_pan(pan: PanResult) -> str:
    """格式化输出盘面（九宫格文本）"""
    lines = []
    lines.append("═══════════════════════════════════════════")
    lines.append(f"  {pan.jushu.yin_yang}{pan.jushu.ju_num}局  {pan.jushu.jieqi} {pan.jushu.yuan}")
    lines.append(f"  四柱：{pan.sizhu.year} {pan.sizhu.month} {pan.sizhu.day} {pan.sizhu.hour}")
    lines.append(f"  旬首：{pan.xunshou.xunshou}  隐仪：{pan.xunshou.yinyi}")
    lines.append(f"  值符：{pan.zhifu_zhishi.zhifu_xing}(落{GONG_NAME[pan.zhifu_zhishi.zhifu_luo_gong]})")
    lines.append(f"  值使：{pan.zhifu_zhishi.zhishi_men}(落{GONG_NAME[pan.zhifu_zhishi.zhishi_luo_gong]})")
    lines.append(f"  空亡：{''.join(pan.xunshou.kong_zhi)}"
                 f"({','.join(GONG_NAME[g] for g in pan.xunshou.kong_gong)})")
    lines.append(f"  马星：{pan.xunshou.masa}")
    lines.append("═══════════════════════════════════════════")

    # 九宫格布局（上南下北）
    layout = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]
    for row_idx, row in enumerate(layout):
        line1 = line2 = line3 = line4 = ""
        for gong in row:
            if gong == 5:
                line1 += "│  中五宫(中)    "
                line2 += "│  天禽寄坤二宫  "
                line3 += "│                "
                line4 += "│                "
            else:
                d = pan.gongs[gong]
                kong_mark = "空" if d.is_kong else "  "
                po_mark = "迫" if d.men_po else "  "
                line1 += f"│{d.gong_name[:5]:　<5}  {kong_mark}{po_mark}"
                line2 += f"│神:{d.bashen:<4} 星:{d.jiuxing:<4}"
                line3 += f"│门:{d.bamen:<4} {d.tianpan_gan}/{d.dipan_gan}   "
                line4 += f"│{d.fangwei:<6}          "
        sep = "┌────────────────┬────────────────┬────────────────┐" if row_idx == 0 else \
              "├────────────────┼────────────────┼────────────────┤"
        lines.append(sep)
        lines.append(line1 + "│")
        lines.append(line2 + "│")
        lines.append(line3 + "│")
        lines.append(line4 + "│")
    lines.append("└────────────────┴────────────────┴────────────────┘")

    return "\n".join(lines)
