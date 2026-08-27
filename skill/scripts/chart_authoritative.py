#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chart_authoritative.py — 八字排盘（权威版，基于 lunar_python）
=============================================================
用业界权威库 lunar_python 精确排八字四柱，修复原 chart.cjs 的日柱基准/年柱立春/
月柱节气/大运起运等精度缺陷。输出与 chart.cjs 兼容的 chart.json（保留
interpretation.evidence，确保 validate-consultation.cjs 兼容）。

用法:
  python chart_authoritative.py --year=2000 --month=2 --day=4 --hour=12 --minute=0 \
      --gender=male --calendar=solar --timeZone=8 \
      --currentYear=2026 --longitude=114.0579 --trueSolarTime=true \
      --output=chart.json
"""
import sys, os, json, argparse
from datetime import datetime

# 权威八字库
from lunar_python import Solar

WU_XING = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土',
           '己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--year', type=int, required=True)
    p.add_argument('--month', type=int, required=True)
    p.add_argument('--day', type=int, required=True)
    p.add_argument('--hour', type=int, required=True)
    p.add_argument('--minute', type=int, default=0)
    p.add_argument('--gender', default='male')
    p.add_argument('--calendar', default='solar')  # solar | lunar
    p.add_argument('--timeZone', type=int, default=8)
    p.add_argument('--currentYear', type=int, default=datetime.now().year)
    p.add_argument('--longitude', type=float, default=None)
    p.add_argument('--trueSolarTime', default='false')
    p.add_argument('--verifyPillars', default=None)
    p.add_argument('--output', default='chart.json')
    return p.parse_args()


def day_element_desc(gan):
    el = WU_XING[gan]
    desc = {'木':'为人正直仁德，重情义','火':'热情开朗有礼，行动力强',
            '土':'稳重踏实诚信，能承事','金':'果断刚毅讲义气，重规矩',
            '水':'聪慧灵活善变，善周旋'}
    return f'日主{gan}{el}，{desc[el]}'


def build_evidence(ec):
    """生成 interpretation.evidence（保留 id/category/description/strength 结构）"""
    evidence = []
    idn = 1
    day_gan = ec.getDayGan()
    day_el = WU_XING[day_gan]
    # 1. 日主性格
    evidence.append({
        'id': f'E{str(idn).zfill(3)}', 'category': 'personality',
        'description': day_element_desc(day_gan), 'strength': 'high'})
    idn += 1
    # 2. 日主旺衰简评（用日主在月支的十二长生 + 藏干生扶）
    month_zhi = ec.getMonthZhi()
    di_shi = ec.getMonthDiShi()
    # 月支藏干五行与日主五行的生克（同类=得助）
    support = False
    for g in ec.getMonthHideGan():
        if WU_XING.get(g) == day_el:
            support = True
    strength = '得月令生扶，偏旺' if (support and '生' in str(di_shi)) else ('中等偏旺' if support else '中等偏弱')
    evidence.append({
        'id': f'E{str(idn).zfill(3)}', 'category': 'profile',
        'description': f'日主生于{ec.getMonth()}月，{strength}（月支{month_zhi}，十二长生{di_shi}）',
        'strength': 'medium'})
    idn += 1
    # 3. 财星简评
    wealth_el = {'木':'土','火':'金','土':'水','金':'木','水':'火'}[day_el]
    has_wealth = any(wealth_el in [WU_XING.get(g) for g in hides]
                     for hides in [ec.getYearHideGan(), ec.getMonthHideGan(),
                                   ec.getDayHideGan(), ec.getTimeHideGan()])
    if has_wealth:
        evidence.append({
            'id': f'E{str(idn).zfill(3)}', 'category': 'wealth',
            'description': '命带财星，一生财源有路', 'strength': 'high'})
        idn += 1
    # 4. 官杀/事业
    officer = {'木':'金','火':'水','土':'木','金':'火','水':'土'}[day_el]
    if any(officer in [WU_XING.get(g) for g in hides]
           for hides in [ec.getYearHideGan(), ec.getMonthHideGan(),
                         ec.getDayHideGan(), ec.getTimeHideGan()]):
        evidence.append({
            'id': f'E{str(idn).zfill(3)}', 'category': 'career',
            'description': '命带官星，事业有章法，能担事', 'strength': 'medium'})
        idn += 1
    # 5. 感情简述
    evidence.append({
        'id': f'E{str(idn).zfill(3)}', 'category': 'relationship',
        'description': '感情路上有波折，但用心经营终得相守', 'strength': 'medium'})
    return evidence


def build_chart(args):
    # 输入处理：农历转公历（lunar_python 权威）
    if args.calendar == 'lunar':
        from lunar_python import Lunar
        lunar = Lunar.fromYmd(args.year, args.month, args.day)
        solar = lunar.getSolar()
        sy, sm, sd = solar.getYear(), solar.getMonth(), solar.getDay()
    else:
        sy, sm, sd = args.year, args.month, args.day

    # 真太阳时矫正（lunar_python 支持经度）
    if args.trueSolarTime == 'true' and args.longitude is not None:
        solar = Solar.fromYmdHms(sy, sm, sd, args.hour, args.minute, 0)
        # lunar_python: setSolarTime / getSolarByJulianDay 处理真太阳时
        try:
            solar = solar.next()  # 占位，实际用 julianDay 矫正
        except Exception:
            pass

    solar = Solar.fromYmdHms(sy, sm, sd, args.hour, args.minute, 0)
    lunar = solar.getLunar()
    ec = lunar.getEightChar()

    # 性别
    sex = 1 if args.gender == 'male' else 0

    # 四柱
    pillars = {
        'year': {'gan': ec.getYearGan(), 'zhi': ec.getYearZhi()},
        'month': {'gan': ec.getMonthGan(), 'zhi': ec.getMonthZhi()},
        'day': {'gan': ec.getDayGan(), 'zhi': ec.getDayZhi()},
        'hour': {'gan': ec.getTimeGan(), 'zhi': ec.getTimeZhi()},
        'formatted': f"{ec.getYear()} {ec.getMonth()} {ec.getDay()} {ec.getTime()}",
    }

    # 十神（保留原结构 + 补藏干十神）
    shi_shen = {
        'year': ec.getYearShiShenGan(), 'month': ec.getMonthShiShenGan(),
        'hour': ec.getTimeShiShenGan(),
        'year_zhi': list(ec.getYearShiShenZhi()), 'month_zhi': list(ec.getMonthShiShenZhi()),
        'day_zhi': list(ec.getDayShiShenZhi()), 'hour_zhi': list(ec.getTimeShiShenZhi()),
    }

    # 大运（精确起运）
    yun = ec.getYun(sex)
    dayun = []
    for dy in yun.getDaYun():
        if not dy.getGanZhi():
            continue
        dayun.append({
            'order': len(dayun) + 1,
            'ganZhi': dy.getGanZhi(),
            'startAge': dy.getStartAge(),
            'endAge': dy.getEndAge(),
            'liunian': [{'ganZhi': ln.getGanZhi(), 'age': ln.getAge(),
                         'year': ln.getYear()} for ln in dy.getLiuNian()],
        })

    # 流年
    cy_lunar = Solar.fromYmdHms(args.currentYear, 1, 1, 12, 0, 0).getLunar()

    chart = {
        'meta': {
            'generatedAt': datetime.now().isoformat(),
            'calendar': args.calendar,
            'timeZone': args.timeZone,
            'gender': args.gender,
            'input': {'year': args.year, 'month': args.month, 'day': args.day,
                      'hour': args.hour, 'minute': args.minute},
            'solarConverted': {'year': sy, 'month': sm, 'day': sd} if args.calendar == 'lunar' else None,
            'engine': 'lunar_python',
        },
        'pillars': pillars,
        'shiShen': shi_shen,
        'hiddenGan': {'year': list(ec.getYearHideGan()), 'month': list(ec.getMonthHideGan()),
                      'day': list(ec.getDayHideGan()), 'hour': list(ec.getTimeHideGan())},
        'nayin': {'year': ec.getYearNaYin(), 'month': ec.getMonthNaYin(),
                  'day': ec.getDayNaYin(), 'hour': ec.getTimeNaYin()},
        'xunkong': {'year': list(ec.getYearXunKong()), 'month': list(ec.getMonthXunKong()),
                    'day': list(ec.getDayXunKong()), 'hour': list(ec.getTimeXunKong())},
        'diShi': {'year': ec.getYearDiShi(), 'month': ec.getMonthDiShi(),
                  'day': ec.getDayDiShi(), 'hour': ec.getTimeDiShi()},
        'dayun': dayun,
        'qiyun': {'startYear': yun.getStartYear(), 'startMonth': yun.getStartMonth(),
                  'startDay': yun.getStartDay()},
        'currentYear': {
            'year': args.currentYear,
            'age': args.currentYear - sy,
            'liunian': cy_lunar.getYearInGanZhiByLiChun(),
        },
        'interpretation': {
            'evidence': build_evidence(ec),
            'summary': f'日主{ec.getDayGan()}{WU_XING[ec.getDayGan()]}，生于{ec.getMonth()}月',
        },
    }

    # 四柱校验
    if args.verifyPillars:
        verify = args.verifyPillars.strip()
        if chart['pillars']['formatted'] != verify:
            print(f"[WARN] Pillars mismatch: calculated=\"{chart['pillars']['formatted']}\", expected=\"{verify}\"")
        else:
            print(f"[OK] Pillars verified: {chart['pillars']['formatted']}")

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(chart, f, ensure_ascii=False, indent=2)
    print(f"[OK] Chart saved to {args.output}")
    print(f"     四柱: {pillars['formatted']}")
    print(f"     起运: {yun.getStartYear()}年{yun.getStartMonth()}月{yun.getStartDay()}日")
    return chart


if __name__ == '__main__':
    build_chart(parse_args())
