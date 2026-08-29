#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""奇门遁甲可视化盘面渲染器 — 自包含HTML九宫格+解盘报告"""
import sys
from pathlib import Path
from dataclasses import asdict
from datetime import datetime

WX_COLORS = {"金": "#F5DEB3", "木": "#90EE90", "水": "#87CEEB", "火": "#FFB6C1", "土": "#D2B48C"}
SHEN_COLORS = {"值符": "#FFD700", "腾蛇": "#FF6347", "太阴": "#C0C0C0", "六合": "#98FB98", "白虎": "#FFFAFA", "玄武": "#2F4F4F", "九地": "#8B4513", "九天": "#87CEEB"}
JI_MEN = {"开门", "休门", "生门"}
XIONG_MEN = {"死门", "惊门", "伤门"}
GONG_LABELS = {4: "巽四宫", 9: "离九宫", 2: "坤二宫", 3: "震三宫", 7: "兑七宫", 8: "艮八宫", 1: "坎一宫", 6: "乾六宫"}


def _ensure_dict(pan):
    if hasattr(pan, 'gongs'):
        raw = asdict(pan)
    else:
        raw = pan
    s = raw.get('sizhu', {})
    j = raw.get('jushu', {})
    z = raw.get('zhifu_zhishi', {})
    x = raw.get('xunshou', {})
    return {
        'sizhu': {'年柱': s['year_gan'] + s['year_zhi'], '月柱': s['month_gan'] + s['month_zhi'],
                  '日柱': s['day_gan'] + s['day_zhi'], '时柱': s['hour_gan'] + s['hour_zhi']},
        'jushu': {'局数': j.get('ju_num', 0), '阴阳遁': j.get('yin_yang', ''), '节气': j.get('jieqi', ''), '元': j.get('yuan', '')},
        'zhifu_zhishi': z,
        'xunshou': {'旬首': x.get('xunshou', ''), '隐仪': x.get('yinyi', ''), '空亡地支': x.get('kong_zhi', []), '空亡宫位': x.get('kong_gong', []), '马星': x.get('masa', '')},
        'gongs': {str(k): {'宫名': v['gong_name'], '方位': v['fangwei'], '五行': v['wuxing'],
                           '天盘干': v['tianpan_gan'], '地盘干': v['dipan_gan'],
                           '九星': v['jiuxing'], '八门': v['bamen'], '八神': v['bashen'],
                           '空亡': v['is_kong'], '门迫': v['men_po'], '反吟': v['fan_yin'], '伏吟': v['fu_yin'],
                           '格局': v['geju']}
                  for k, v in raw.get('gongs', {}).items() if k != 5},
    }


def render(pan, duanju_report=None):
    pd = _ensure_dict(pan)
    sizhu, jushu, zz, xs, gongs = pd['sizhu'], pd['jushu'], pd['zhifu_zhishi'], pd['xunshou'], pd['gongs']
    title = jushu['阴阳遁'] + str(jushu['局数']) + "局  " + jushu['节气'] + " " + jushu['元']

    def gong_html(gid, gong):
        if not gong:
            return '<div class="gong empty"></div>'
        cls = ["gong"]
        badges = []
        if gong.get('空亡'):
            cls.append("kong")
            badges.append('<span class="b b-k">空</span>')
        if gong.get('门迫'):
            badges.append('<span class="b b-p">迫</span>')
        if gong.get('反吟'):
            badges.append('<span class="b b-fa">反</span>')
        if gong.get('伏吟'):
            badges.append('<span class="b b-fu">伏</span>')
        if gid == zz.get('zhifu_luo_gong', 0):
            cls.append("zf")
            badges.insert(0, '<span class="b b-zf">值符</span>')
        if gid == zz.get('zhishi_luo_gong', 0):
            badges.append('<span class="b b-zs">值使</span>')
        men = gong.get('八门', '')
        mc = "m-ji" if men in JI_MEN else ("m-x" if men in XIONG_MEN else "m-zh")
        shen = gong.get('八神', '')
        sc = SHEN_COLORS.get(shen, '#e0d6c2')
        gj_str = ''
        if gong.get('格局'):
            g = gong['格局'][0]
            name = g.get("格局名", "") if isinstance(g, dict) else str(g)
            if name:
                gj_str = '<div class="gj">' + name + '</div>'
        wx = gong.get('五行', '')
        border_color = WX_COLORS.get(wx, '#555') + '66'
        return (
            '<div class="' + ' '.join(cls) + '" style="border-left:3px solid ' + border_color + ';">'
            '<div class="gh"><span class="gn">' + gong.get('宫名', '') + '</span>'
            '<span class="gbs">' + ''.join(badges) + '</span></div>'
            '<div class="gbo">'
            '<div class="gs" style="color:' + sc + '">' + shen + '</div>'
            '<div class="gst">' + gong.get('九星', '') + '</div>'
            '<div class="gm ' + mc + '">' + men + '</div>'
            '<div class="gg"><span class="tian">天' + gong.get('天盘干', '') + '</span>'
            '<span class="sep"> / </span><span class="di">地' + gong.get('地盘干', '') + '</span></div>'
            '<div class="gf">' + gong.get('方位', '') + ' \u00b7 ' + wx + '</div>' + gj_str +
            '</div></div>'
        )

    def zhong_gong():
        return '<div class="gong" style="display:flex;align-items:center;justify-content:center;flex-direction:column;background:rgba(100,100,100,.1)"><div style="color:#888">中五宫</div><div style="color:#666;font-size:.75em">天禽寄坤二</div></div>'

    order = [4, 9, 2, 3, 5, 7, 8, 1, 6]
    cells = [gong_html(g, gongs.get(str(g))) if g != 5 else zhong_gong() for g in order]

    geju_part = ''
    if duanju_report:
        geju_part = render_duanju(duanju_report)

    kong_label = '\u3001'.join(GONG_LABELS.get(g, '') for g in xs.get('空亡宫位', []))
    kong_str = '\u3001'.join(xs.get('空亡地支', [])) + f'（{kong_label}）' if kong_label else '\u3001'.join(xs.get('空亡地支', []))

    return CSS + f'''</style></head><body><div class="c">
<div class="h"><h1>奇门遁甲排盘</h1><div class="st">{title}</div>
<div class="il">
<span class="ic">四柱：{sizhu['年柱']} {sizhu['月柱']} {sizhu['日柱']} {sizhu['时柱']}</span>
<span class="ic">值符{zz.get('zhifu_xing','')} / 值使{zz.get('zhishi_men','')}</span>
<span class="ic">旬首{xs['旬首']} 隐仪{xs['隐仪']}</span></div>
<div class="il">
<span class="ac">空亡：{kong_str}</span>
<span class="ic">马星：{xs.get('马星','')}</span>
</div></div>
<div class="grid">{''.join(cells)}</div>
{geju_part}
<div class="ft">仅供研究参考  ·  qimen_core v1.0</div></div></body></html>'''


def render_duanju(r):
    parts = []
    y = r.get('用神定位', {})
    if y:
        parts.append(f'<div class="db"><div class="dl">用神定位</div><div class="dv">主用神：<b>{", ".join(y.get("主用神",["日干"]))}</b>  |  辅助：{", ".join(y.get("辅助用神",[]))}</div><div class="dv2">{y.get("判断要点","")}</div></div>')
    dun = r.get('经典遁格', [])
    if dun:
        dun_items = ''.join('<span class="gi gx">' + d['遁格'] + '  ' + d.get('宫位', '') + '</span>' for d in dun)
        parts.append(f'<div class="db"><div class="dl">经典遁格</div>{dun_items}</div>')
    gejus = r.get('格局分析', [])
    if gejus:
        items_parts = []
        for g in gejus[:10]:
            jx = g.get('吉凶', '')
            cls = 'gx' if jx in ('吉', '大吉', '中上') else ('gg' if jx in ('凶', '大凶', '中下') else 'gy')
            items_parts.append('<span class="gi ' + cls + '">' + g['宫位'] + ' ' + g['组合'] + ' ' + g['格局名'] + '</span>')
        items = ''.join(items_parts)
        parts.append(f'<div class="db"><div class="dl">十干克应格局</div>{items}</div>')
    states = r.get('特殊状态', [])
    if states:
        state_lines = '<br>'.join('<span class="wn">' + s['宫位'] + '</span>：' + '; '.join(s.get('问题', [])) for s in states)
        parts.append(f'<div class="db"><div class="dl">特殊状态</div><div class="dv">{state_lines}</div></div>')
    xy = r.get('用神宫位象意', [])
    if xy:
        xy_parts = []
        for x in xy:
            line = '<div class="xy"><b style="color:#d4af37">' + x.get('宫位', '') + '</b>  '
            line += x.get('八门', '') + '  ' + x.get('九星', '') + '  ' + x.get('八神', '') + '<br>'
            line += '<span class="xy2">门：' + ', '.join(x.get('门象意', [])[:3]) + '</span><br>'
            line += '<span class="xy2">星：' + ', '.join(x.get('星象意', [])[:3]) + '</span><br>'
            line += '<span class="xy2">神：' + ', '.join(x.get('神象意', [])[:3]) + '</span>'
            if x.get('格局提示'):
                line += '<br><span class="xyg">格局：' + x['格局提示'] + '</span>'
            if x.get('状态'):
                line += '<br><span class="warn">状态：' + ', '.join(x['状态']) + '</span>'
            line += '</div>'
            xy_parts.append(line)
        xy_html = ''.join(xy_parts)
        parts.append(f'<div class="db"><div class="dl">关键宫位象意</div>{xy_html}</div>')
    c = r.get('综合结论', '')
    if c:
        parts.append(f'<div class="cb"><b style="color:#d4af37">综合结论</b><br><br>{c.replace(chr(10),"<br>")}</div>')
    return f'<div class="ds"><h2>奇门解盘报告</h2>{"".join(parts)}</div>' if parts else ''


CSS = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>奇门遁甲排盘</title><style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"PingFang SC","Microsoft YaHei","Noto Sans SC",sans-serif;background:linear-gradient(135deg,#0a0a0a,#1a1a2e 50%,#16213e);color:#e0d6c2;min-height:100vh;padding:20px}
.c{max-width:920px;margin:0 auto}
.h{text-align:center;padding:30px 20px 10px;border-bottom:2px solid rgba(212,175,55,.3);margin-bottom:20px}
.h h1{font-size:2em;background:linear-gradient(135deg,#d4af37,#f5e6a3,#d4af37);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px}
.st{font-size:1.5em;color:#c9a84c;margin-bottom:4px}
.il{display:flex;justify-content:center;gap:20px;flex-wrap:wrap;margin-top:12px;font-size:.93em;color:#a09070}
.ic{background:rgba(212,175,55,.1);border:1px solid rgba(212,175,55,.25);padding:4px 14px;border-radius:20px}
.ac{background:rgba(220,53,69,.15);border:1px solid rgba(220,53,69,.4);color:#f8a4a8;padding:4px 14px;border-radius:20px}
.grid{display:grid;grid-template-columns:1fr 1fr 1fr;grid-template-rows:auto auto auto;gap:2px;background:rgba(212,175,55,.2);border:2px solid rgba(212,175,55,.4);border-radius:12px;overflow:hidden;margin-bottom:24px}
.gong{padding:16px 12px;min-height:150px;transition:all .2s;position:relative}
.gong:hover{filter:brightness(1.08)}
.gong.empty{opacity:0}
.gong.kong{background-image:repeating-linear-gradient(45deg,transparent,transparent 4px,rgba(220,53,69,.05) 4px,rgba(220,53,69,.05) 8px)}
.gong.zf{box-shadow:inset 0 0 0 2px #d4af37}
.gh{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px}
.gn{font-size:.85em;font-weight:600;color:#c9a84c}
.gbs{display:flex;gap:4px;flex-wrap:wrap}
.b{font-size:.68em;padding:1px 6px;border-radius:10px;font-weight:600}
.b-k{background:rgba(220,53,69,.2);color:#f8a4a8;border:1px solid rgba(220,53,69,.4)}
.b-p{background:rgba(255,193,7,.2);color:#ffc107;border:1px solid rgba(255,193,7,.4)}
.b-fa{background:rgba(111,66,193,.2);color:#b388ff;border:1px solid rgba(111,66,193,.4)}
.b-fu{background:rgba(32,201,151,.2);color:#20c997;border:1px solid rgba(32,201,151,.4)}
.b-zf{background:rgba(212,175,55,.2);color:#d4af37;border:1px solid rgba(212,175,55,.5)}
.b-zs{background:rgba(73,160,120,.2);color:#49a078;border:1px solid rgba(73,160,120,.5)}
.gbo{font-size:.82em;line-height:1.65}
.gs{font-weight:600;font-size:.92em;margin-bottom:3px}
.gst{color:#b0b0b0}
.gm{font-weight:600;font-size:.88em}
.m-ji{color:#4caf50}.m-x{color:#f44336}.m-zh{color:#ffc107}
.gg{font-family:"KaiTi","STKaiti",serif;font-size:1.15em;margin:2px 0}
.gg .tian{color:#ffd700}.gg .sep{color:#555}.gg .di{color:#aaa}
.gf{font-size:.7em;color:#666;margin-top:2px}
.gj{font-size:.7em;color:#d4af37;margin-top:3px}
.ds{background:rgba(20,20,40,.8);border:1px solid rgba(212,175,55,.2);border-radius:12px;padding:24px;margin-bottom:16px}
.ds h2{font-size:1.25em;color:#d4af37;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid rgba(212,175,55,.2)}
.db{margin-bottom:14px}
.dl{color:#a09070;font-size:.82em;margin-bottom:4px}
.dv{color:#e0d6c2;line-height:1.5}
.dv2{font-size:.82em;color:#888;margin-top:2px}
.gi{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;margin:3px;border-radius:6px;font-size:.84em}
.gx{background:rgba(76,175,80,.1);border:1px solid rgba(76,175,80,.3)}
.gg{background:rgba(244,67,54,.1);border:1px solid rgba(244,67,54,.3)}
.gy{background:rgba(255,193,7,.1);border:1px solid rgba(255,193,7,.3)}
.wn{color:#ff6b6b;font-weight:600}
.xy{margin-bottom:10px;padding-left:12px;border-left:2px solid rgba(212,175,55,.3);line-height:1.55}
.xy2{font-size:.82em;color:#aaa}
.xyg{font-size:.82em;color:#d4af37}
.warn{font-size:.78em;color:#ff6b6b}
.cb{background:rgba(212,175,55,.08);border-left:3px solid #d4af37;padding:16px 20px;border-radius:0 8px 8px 0;margin-top:12px;line-height:1.8}
.ft{text-align:center;color:#555;font-size:.72em;margin-top:20px;padding:10px}
@media(max-width:600px){.gong{padding:10px 6px;min-height:110px;font-size:.72em}.h h1{font-size:1.4em}}
"""


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="奇门遁甲可视化排盘")
    p.add_argument("--year", type=int)
    p.add_argument("--month", type=int)
    p.add_argument("--day", type=int)
    p.add_argument("--hour", type=int)
    p.add_argument("--minute", type=int, default=0)
    p.add_argument("--question", type=str, default="综合", help="所问之事")
    p.add_argument("--output", type=str, default="qimen_pan.html")
    args = p.parse_args()
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from engine import QimenEngine
    from qimen_duanju.engine import DuanjuEngine
    if args.year:
        pan = QimenEngine().paipan(args.year, args.month, args.day, args.hour, args.minute)
    else:
        now = datetime.now()
        pan = QimenEngine().paipan(now.year, now.month, now.day, now.hour, now.minute)
    engine = DuanjuEngine()
    report = engine.duanju(pan, args.question)
    html = render(pan, report)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(html)
    print("OK: " + args.output)
