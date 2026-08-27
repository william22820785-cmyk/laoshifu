#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chart_bazi_ziwei.py — 复用 bazi-ziwei-skill 的权威八字+紫微排盘，输出 laoshifu 兼容 chart.json
=============================================================================================
陈总决策（2026-08-27）：复用 bazi-ziwei-skill 做排盘（准确即可），重点转向解读。

本脚本：
1. 调用 bazi-ziwei-skill 的 run-chart.js 获得权威八字+紫微完整数据（含 enrichment 补全层）
2. 转成 laoshifu-v2 兼容的 chart.json（保留 interpretation.evidence，确保 validate-consultation.cjs 通过）
3. 额外注入 ziwei 完整数据 + 八字 enrichment，供解读层深入使用

用法:
  python chart_bazi_ziwei.py --year=2000 --month=2 --day=4 --hour=12 --minute=0 \
      --gender=male --calendar=solar --timeZone=8 --currentYear=2026 --output=chart.json
"""
import sys, os, json, argparse, subprocess
from datetime import datetime
import os

# run-chart.js 路径解析：优先包内自包含引擎(engine/)，回退到开发环境 bazi-ziwei-skill
_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # skill 根目录
BAZI_ZIWEI_RUN = os.path.join(_SKILL_ROOT, 'engine', 'calculator', 'dist', 'run-chart.js')
if not os.path.exists(BAZI_ZIWEI_RUN):
    # 开发环境回退：bazi-ziwei-skill（独立 skill）
    _dev = '/root/.openclaw/workspace/skills/bazi-ziwei-skill/calculator/dist/run-chart.js'
    if os.path.exists(_dev):
        BAZI_ZIWEI_RUN = _dev
    else:
        raise RuntimeError('找不到 run-chart.js：包内 engine/ 与开发环境 bazi-ziwei-skill 均不存在')

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
    p.add_argument('--calendar', default='solar')
    p.add_argument('--timeZone', type=int, default=8)
    p.add_argument('--currentYear', type=int, default=datetime.now().year)
    p.add_argument('--output', default='chart.json')
    return p.parse_args()


def call_run_chart(args):
    """调用 bazi-ziwei-skill 的 run-chart.js，返回解析后的 JSON"""
    cmd = ['node', BAZI_ZIWEI_RUN,
           f'--year={args.year}', f'--month={args.month}', f'--day={args.day}',
           f'--hour={args.hour}', f'--minute={args.minute}', f'--gender={args.gender}']
    if args.calendar == 'lunar':
        cmd.append('--isLunar=true')
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"run-chart.js 失败: {r.stderr[:500]}")
    return json.loads(r.stdout)


def build_evidence(rc):
    """从 run-chart 的权威数据生成 interpretation.evidence（validate 兼容）"""
    evidence = []
    idn = 1
    bz = rc['bazi']
    day_gan = bz['dayMaster']
    day_el = WU_XING.get(day_gan, '?')
    enr = bz.get('enrichment', {})

    # 1. 日主性格（基于日主五行 + 自坐）
    desc = {'木':'仁德正直，重情义','火':'热情明礼，行动力强','土':'稳重诚信，能承事',
            '金':'果断刚毅，重规矩','水':'聪慧灵活，善周旋'}
    evidence.append({'id': f'E{str(idn).zfill(3)}', 'category': 'personality',
        'description': f'日主{day_gan}{day_el}，{desc.get(day_el,"")}', 'strength': 'high'})
    idn += 1

    # 2. 格局（enrichment 权威）
    ge = enr.get('格局', {})
    if ge.get('primary'):
        evidence.append({'id': f'E{str(idn).zfill(3)}', 'category': 'profile',
            'description': f'命格{ge["primary"]}（{ge.get("basis","")}），{ge.get("confidence","中")}置信',
            'strength': 'high' if ge.get('confidence')=='高' else 'medium'})
        idn += 1

    # 3. 旺衰（enrichment 权威）
    ws = enr.get('旺衰', {})
    if ws.get('verdict'):
        evidence.append({'id': f'E{str(idn).zfill(3)}', 'category': 'profile',
            'description': f'日主{day_gan}水旺衰{ws["verdict"]}（{ws.get("confidence","中")}）', 'strength': 'medium'})
        idn += 1

    # 4. 财星（十神分布判断）
    ss = enr.get('五行统计', {}).get('shiShenGroups', {})
    wealth_types = [g for g, info in ss.items() if info.get('十神类') == '财']
    if wealth_types:
        evidence.append({'id': f'E{str(idn).zfill(3)}', 'category': 'wealth',
            'description': '命带财星，财源有路', 'strength': 'high'})
        idn += 1

    # 5. 官杀/事业（格局基础）
    officer_types = [g for g, info in ss.items() if info.get('十神类') == '官杀']
    if officer_types:
        evidence.append({'id': f'E{str(idn).zfill(3)}', 'category': 'career',
            'description': '官杀有气，事业有章法', 'strength': 'medium'})
        idn += 1

    # 6. 紫微命宫（补充命盘维度）
    # 注意：gongs 按宫位名排序([0]命宫[1]兄弟...)，mingGongIndex/shenGongIndex 是"地支索引(0-11)"非数组下标
    zw = rc.get('ziwei', {})
    if zw:
        ming = next((g for g in zw['gongs'] if g.get('gong') == '命宫'), zw['gongs'][0])
        stars = ming.get('mainStars', []) or ['无主星（借对宫）']
        aux = ming.get('auxStars', [])
        evidence.append({'id': f'E{str(idn).zfill(3)}', 'category': 'personality',
            'description': f'紫微命宫{ming["tiangan"]}{ming["dizhi"]}，主星{"/".join(stars)}，辅星{"/".join(aux) if aux else "无"}',
            'strength': 'medium'})
        idn += 1

    return evidence


def build_chart(args):
    rc = call_run_chart(args)
    bz = rc['bazi']
    zw = rc.get('ziwei', {})

    # 四柱
    sp = bz['siZhu']
    pillars = {
        'year': sp['year'], 'month': sp['month'], 'day': sp['day'], 'hour': sp['hour'],
        'formatted': f"{sp['year']['gan']}{sp['year']['zhi']} {sp['month']['gan']}{sp['month']['zhi']} "
                     f"{sp['day']['gan']}{sp['day']['zhi']} {sp['hour']['gan']}{sp['hour']['zhi']}",
    }

    # 十神
    sh = bz.get('shiShen', {})
    shi_shen = {'year': sh.get('year'), 'month': sh.get('month'), 'hour': sh.get('hour')}

    # 大运（run-chart 已是精确起运）
    dayun = []
    for i, dy in enumerate(bz.get('dayun', [])):
        dayun.append({
            'order': i + 1,
            'ganZhi': f"{dy['ganZhi']['gan']}{dy['ganZhi']['zhi']}",
            'startAge': dy.get('startAge'),
            'endAge': dy.get('endAge', dy.get('startAge') + 9),
            'ganShiShen': dy.get('ganShiShen'),
            'zhiShiShen': dy.get('zhiShiShen'),
        })

    # 当前流年
    currentYear = {
        'year': args.currentYear,
        'age': args.currentYear - args.year,
        'liunian': None,
    }

    chart = {
        'meta': {
            'generatedAt': datetime.now().isoformat(),
            'calendar': args.calendar,
            'timeZone': args.timeZone,
            'gender': args.gender,
            'input': {'year': args.year, 'month': args.month, 'day': args.day,
                      'hour': args.hour, 'minute': args.minute},
            'engine': 'bazi-ziwei-skill/run-chart (权威)',
        },
        'pillars': pillars,
        'shiShen': shi_shen,
        # 权威扩展数据（解读层用）
        'bazi': bz,
        'ziwei': zw,
        'dayun': dayun,
        'currentYear': currentYear,
        'interpretation': {
            'evidence': build_evidence(rc),
            'summary': f"日主{sp['day']['gan']}{WU_XING.get(sp['day']['gan'],'')}，"
                       f"生于{sp['month']['gan']}{sp['month']['zhi']}月",
        },
    }

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(chart, f, ensure_ascii=False, indent=2)
    print(f"[OK] Chart saved to {args.output}")
    print(f"     四柱: {pillars['formatted']}")
    print(f"     引擎: bazi-ziwei-skill/run-chart")
    return chart


if __name__ == '__main__':
    build_chart(parse_args())
