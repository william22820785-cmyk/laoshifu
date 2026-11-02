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
import sys, os, json, argparse, subprocess, shutil
from datetime import datetime
from pathlib import Path
import os
try:
    from birth_location import resolve_birthplace, true_solar_time, utc_offset_hours
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from birth_location import resolve_birthplace, true_solar_time, utc_offset_hours

# run-chart.js 路径解析：优先包内自包含引擎(engine/)，回退到开发环境 bazi-ziwei-skill
_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # skill 根目录
BAZI_ZIWEI_RUN = os.path.join(_SKILL_ROOT, 'engine', 'calculator', 'dist', 'run-chart.js')
if not os.path.exists(BAZI_ZIWEI_RUN):
    # 可选开发环境回退：仅接受显式环境变量，不写死作者机器路径。
    _dev = os.environ.get('BAZI_ZIWEI_RUN')
    if _dev and os.path.exists(_dev):
        BAZI_ZIWEI_RUN = _dev
    else:
        raise RuntimeError('找不到 run-chart.js：包内 engine/ 不存在；如需外部引擎请设置 BAZI_ZIWEI_RUN')

def _node_command():
    configured = os.environ.get('NODE') or os.environ.get('NODEJS')
    candidates = [configured, shutil.which(configured) if configured else None,
                  shutil.which('node'), shutil.which('nodejs'),
                  '/usr/local/lib/python3.11/site-packages/playwright/driver/node',
                  '/usr/local/lib/python3.11/site-packages/patchright/driver/node',
                  '/usr/local/bin/node', '/usr/bin/node']
    for candidate in candidates:
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    raise RuntimeError('找不到 Node.js 运行时；请安装 Node.js 或设置 NODE')

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
    p.add_argument('--calendar', choices=['solar','lunar'], default='solar')
    p.add_argument('--isLeapMonth', choices=['true','false'], default='false')
    p.add_argument('--verifyPillars', default=None)
    p.add_argument('--timeZone', type=float, default=8)
    p.add_argument('--market', choices=['cn', 'international'], default='cn')
    p.add_argument('--birthPlace', default=None)
    p.add_argument('--birthTimezone', default=None)
    p.add_argument('--longitude', type=float, default=None)
    p.add_argument('--latitude', type=float, default=None)
    p.add_argument('--trueSolarTime', choices=['true', 'false'], default='false')
    p.add_argument('--currentYear', type=int, default=datetime.now().year)
    p.add_argument('--output', default='chart.json')
    return p.parse_args()


def normalized_solar_input(args):
    """Normalize lunar input ONCE, then send identical solar values to both engines."""
    leap = getattr(args, 'isLeapMonth', 'false') == 'true'
    if leap and args.calendar != 'lunar':
        raise ValueError('闰月只用于农历输入')
    if args.calendar != 'lunar':
        return {'year': args.year, 'month': args.month, 'day': args.day}
    module = str(Path(__file__).resolve().parents[1] / 'engine/calculator/node_modules/lunar-typescript')
    script = """const {Lunar}=require(process.argv[1]);
const v=JSON.parse(process.argv[2]);
const s=Lunar.fromYmdHms(v.y,v.leap?-v.m:v.m,v.d,v.h,v.min,0).getSolar();
process.stdout.write(JSON.stringify({year:s.getYear(),month:s.getMonth(),day:s.getDay()}));"""
    r = subprocess.run([_node_command(), '-e', script, module,
                        json.dumps({'y':args.year,'m':args.month,'d':args.day,'h':args.hour,'min':args.minute,'leap':leap})],
                       capture_output=True, text=True, encoding='utf-8', timeout=30)
    if r.returncode != 0:
        raise ValueError('农历日期或闰月无效：' + r.stderr[:300])
    return json.loads(r.stdout)


def call_run_chart(args):
    solar = normalized_solar_input(args)
    civil_time = datetime(
        solar['year'], solar['month'], solar['day'], args.hour, args.minute,
    )
    location_meta = None
    effective_time = civil_time
    engine_time_zone = args.timeZone
    if args.market == 'international':
        if args.trueSolarTime != 'true':
            raise ValueError('海外命盘必须启用真太阳时')
        location = resolve_birthplace(
            args.birthPlace,
            timezone_id=args.birthTimezone,
            longitude=args.longitude,
            latitude=args.latitude,
        )
        engine_time_zone = utc_offset_hours(civil_time, location)
        effective_time, location_meta = true_solar_time(civil_time, location)
    cmd = [_node_command(), BAZI_ZIWEI_RUN,
           f'--year={effective_time.year}', f'--month={effective_time.month}', f'--day={effective_time.day}',
           f'--hour={effective_time.hour}', f'--minute={effective_time.minute}', f'--gender={args.gender}',
           f'--timeZone={engine_time_zone}']
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='strict', timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"run-chart.js 失败: {r.stderr[:500]}")
    result = json.loads(r.stdout)
    result['_normalizedSolarInput'] = solar
    result['_birthTime'] = {
        'market': args.market,
        'birthPlace': args.birthPlace,
        'civilLocalTime': civil_time.isoformat(),
        'effectiveLocalTime': effective_time.isoformat(),
        'trueSolarTimeApplied': args.market == 'international',
        'timeZone': engine_time_zone,
        'location': location_meta,
    }
    return result


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
            'description': f'日主{day_gan}{day_el}旺衰{ws["verdict"]}（{ws.get("confidence","中")}）', 'strength': 'medium'})
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

    expected = getattr(args, 'verifyPillars', None)
    if expected and ''.join(expected.split()) != ''.join(pillars['formatted'].split()):
        raise ValueError('输入四柱与排盘不一致，请核对历法、日期与时辰')

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
        'age': args.currentYear - rc['_normalizedSolarInput']['year'],
        'liunian': None,
    }

    chart = {
        'meta': {
            'generatedAt': datetime.now().isoformat(),
            'calendar': args.calendar,
            'normalizedSolarInput': rc['_normalizedSolarInput'],
            'isLeapMonth': getattr(args, 'isLeapMonth', 'false') == 'true',
            'timeZoneConvention': (
                'International mode resolves birthplace timezone and longitude, applies historical local UTC offset '
                'and true solar time before calculation; solar-term boundary cases still require disclosure.'
                if args.market == 'international'
                else 'Birth clock fields are used as supplied after lunar-to-solar conversion; timezone offset is recorded, not used to localize solar terms. Non-UTC+8 boundary cases require separate verification.'
            ),
            'timeZone': rc['_birthTime']['timeZone'],
            'market': args.market,
            'birthPlace': args.birthPlace,
            'birthTime': rc['_birthTime'],
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
    import sys
    if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')
    build_chart(parse_args())
