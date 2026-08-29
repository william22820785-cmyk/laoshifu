#!/usr/bin/env python3
"""
算命老师傅 V2.0 — 六爻+奇门遁甲双法融合算事引擎
用法: python fusion.py --question="..." [--category=...] [--method=time|numbers] [--numbers=...]
                          --year=2026 --month=7 --day=30 --hour=14 --minute=10
                          [--timeZone=8] --output=fusion.json

内部黑箱：同时调用六爻和奇门，融合对比后输出统一结果。
用户只看到：统一断语 + 标准六爻卦图（奇门九宫不可见）
"""
import sys, os, json, argparse, shutil, subprocess, tempfile
from datetime import datetime

# Windows 控制台可能使用本地代码页；脚本输出统一 UTF-8，避免宿主读取日志乱码。
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# ── 自包含运行时 ──
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))


def _node_command():
    """Find a host Node.js runtime without assuming the author's machine path."""
    configured = os.environ.get("NODE") or os.environ.get("NODEJS")
    candidates = []
    if configured:
        candidates.extend([configured, shutil.which(configured) or ""])
    for candidate in ("node", "nodejs"):
        candidates.append(shutil.which(candidate) or "")
    # OpenClaw's Linux image may expose the bundled Playwright Node runtime but
    # intentionally omit node from the service user's PATH.
    candidates.extend([
        "/usr/local/lib/python3.11/site-packages/playwright/driver/node",
        "/usr/local/lib/python3.11/site-packages/patchright/driver/node",
        "/usr/local/bin/node", "/usr/bin/node",
    ])
    for candidate in candidates:
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    raise RuntimeError("未找到 Node.js。请安装 Node.js 18+，设置 NODE 环境变量，或提供可执行的宿主 Node 运行时。")


def _run_local_chart(script_name, args):
    """Run a bundled chart script without a shell and return its JSON output."""
    script = os.path.join(SCRIPT_ROOT, script_name)
    if not os.path.isfile(script):
        raise RuntimeError(f"技能包缺少内置排盘脚本: {script_name}")
    with tempfile.TemporaryDirectory(prefix="laoshifu-event-") as tmp:
        output = os.path.join(tmp, "chart.json")
        command = [_node_command(), script, *args, f"--output={output}"]
        proc = subprocess.run(command, cwd=SKILL_ROOT, capture_output=True, text=True, encoding="utf-8")
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "未知错误").strip()
            raise RuntimeError(f"{script_name} 运行失败: {detail}")
        try:
            with open(output, "r", encoding="utf-8-sig") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"{script_name} 未生成有效排盘 JSON: {exc}") from exc


def paipan_liuyao(dt, method='time', numbers=None, time_zone=8, category='general', question=''):
    """Call the bundled deterministic Liuyao engine and map it to the V4 fusion shape."""
    args = [
        f"--question={question}", f"--category={category}", f"--method={method}",
        f"--year={dt.year}", f"--month={dt.month}", f"--day={dt.day}",
        f"--hour={dt.hour}", f"--minute={dt.minute}", f"--timeZone={time_zone}",
    ]
    if method == 'numbers':
        if not numbers or len(numbers) != 3 or any(int(value) <= 0 for value in numbers):
            raise ValueError("报数起卦必须提供恰好三个正整数")
        args.append("--numbers=" + ",".join(str(int(value)) for value in numbers))
    chart = _run_local_chart('liuyao.cjs', args)
    lines = chart.get('lines', [])
    moving = []
    shi = ying = None
    for line in lines:
        item = {
            '爻位': line.get('position'), '六亲': line.get('sixRelative', ''),
            '纳支': line.get('najiaDizhi', ''), '五行': line.get('wuxing', ''),
            '六神': line.get('sixGod', ''),
        }
        if line.get('isWorld'):
            shi = item
        if line.get('isResponse'):
            ying = item
        if line.get('isChanging'):
            moving.append(item)
    hexagrams = chart.get('hexagrams', {})
    calendar = chart.get('calendar', {})
    return {
        '本卦': hexagrams.get('primary', {}).get('name', ''),
        '变卦': hexagrams.get('changed', {}).get('name', ''),
        '动爻': moving, '世爻': shi or {}, '应爻': ying or {},
        '日柱': calendar.get('ganzhi', {}).get('day', ''),
        '日空亡': '、'.join(calendar.get('voidBranches', [])),
        'diagram': chart.get('diagram', ''), 'raw_output': chart,
    }

def build_liuyao_diagram(pan):
    """构建标准的六爻卦图 Markdown 表格"""
    p = pan['盘']
    # 获取本卦卦标头和变卦卦标头
    header_line = ''
    for k in sorted(p.keys(), key=lambda x: int(x)):
        v = p[k]
        if k == '10':
            header_line += f"上{v.get('上卦','')}下{v.get('下卦','')} {v.get('六十四卦','')}({v.get('卦宫','')}宫)"
        if k == '20':
            header_line += f"  之  " + f"上{v.get('上卦','')}下{v.get('下卦','')} {v.get('六十四卦','')}({v.get('卦宫','')}宫)"

    lines = [header_line]

    # 从初爻到上爻 (6->1)
    for idx in [6, 5, 4, 3, 2, 1]:
        key_ben = f'1{idx}'
        key_bian = f'2{idx}'
        b = p.get(key_ben, {})
        bb = p.get(key_bian, {})

        ben_str = ''
        if b:
            ben_str = f"{b.get('六神',''):6s} {b.get('卦爻',''):.6s} {b.get('六亲',''):.4s}{b.get('纳干','')}{b.get('纳支','')}{b.get('五行','')}"
            if b.get('世应', '').strip():
                ben_str += f"{b['世应']}"
            if b.get('动爻', '').strip() in ('O', 'X'):
                ben_str += f" {b['动爻'].strip()}"

        bian_str = ''
        if bb:
            bian_str = f"{bb.get('六亲',''):.4s}{bb.get('纳干','')}{bb.get('纳支','')}{bb.get('五行','')}"
            if bb.get('世应', '').strip():
                bian_str += f"{bb['世应']}"
            if bb.get('动爻', '').strip():
                bian_str += f" {bb['动爻'].strip()}"

        line = f"{ben_str:40s} → {bian_str:25s}"
        lines.append(line)

    return "\n".join(lines)


def paipan_qimen(y, m, d, h, mi, question, time_zone=8, category='general'):
    """Call the bundled deterministic Qimen engine and map it to the V4 fusion shape."""
    chart = _run_local_chart('qimen.cjs', [
        f"--question={question}", f"--category={category}",
        f"--year={y}", f"--month={m}", f"--day={d}",
        f"--hour={h}", f"--minute={mi}", f"--timeZone={time_zone}",
    ])
    pan = chart.get('pan', {})
    jushu = pan.get('jushu', {})
    xunshou = pan.get('xunshou', {})
    zhifu = pan.get('zhifu_zhishi', {})
    interpretation = chart.get('interpretation', {})
    return {
        '局数': f"{jushu.get('阴阳遁', '')}{jushu.get('局数', '')}局",
        '节气': f"{jushu.get('节气', '')}{jushu.get('元', '')}",
        '四柱': ' '.join(pan.get('sizhu', {}).get(key, '') for key in ('年柱', '月柱', '日柱', '时柱')),
        '值符': f"{zhifu.get('值符星', '')}(落{zhifu.get('值符落宫', '')}宫)",
        '值使': f"{zhifu.get('值使门', '')}(落{zhifu.get('值使落宫', '')}宫)",
        '空亡': '、'.join(xunshou.get('空亡地支', [])),
        '用神定位': interpretation.get('用神定位', {}),
        '格局分析': interpretation.get('格局分析', []),
        '特殊状态': interpretation.get('特殊状态', []),
        '综合结论': interpretation.get('综合结论', ''),
        'signals': chart.get('signals', {}),
        'raw_output': chart,
    }

def fuse(question, liuyao, qimen, category='general'):
    """六爻+奇门双法融合"""
    agree_points = []
    conflict_points = []
    conclusions = []

    # 1. 总体吉凶 (六爻)
    ly_ji_score = 0
    ly_reasons = []
    for d in liuyao.get('动爻', []):
        if d.get('六亲') in ('妻财', '子孙'):
            ly_ji_score += 1
            ly_reasons.append('有转机之象')
        elif d.get('六亲') in ('父母',):
            ly_ji_score += 0.5
        elif d.get('六亲') in ('兄弟', '官鬼'):
            ly_ji_score -= 1
            ly_reasons.append('阻力较大')
    ly_tendency = '吉' if ly_ji_score > 0 else ('凶' if ly_ji_score < 0 else '平')

    # 总体吉凶 (奇门)
    qm_gejus = qimen.get('格局分析', [])
    qm_ji = sum(1 for g in qm_gejus if g.get('吉凶', '') in ['吉', '大吉', '中上'])
    qm_xiong = sum(1 for g in qm_gejus if g.get('吉凶', '') in ['凶', '大凶', '中下'])
    qm_tendency = '吉' if qm_ji > qm_xiong else ('凶' if qm_xiong > qm_ji else '平')

    overall_agree = (ly_tendency == qm_tendency)
    overall_status = 'same' if overall_agree else ('complementary' if ly_tendency != qm_tendency and ly_tendency != '平' and qm_tendency != '平' else 'conflict')

    ji_verdict = f'偏{ly_tendency}' if overall_agree else f'角度不同，有{ly_tendency}的压力，也有{qm_tendency}的转圜'
    ji_delivery = 'firm' if overall_agree and ly_tendency in ('吉', '凶') else 'probable'

    agree_points.append({
        'dimension': '总体态势',
        'verdict': ji_verdict,
        'delivery': ji_delivery,
        'detail': '',
    })

    # 2. 时间窗口
    ri_kong = liuyao.get('日空亡', '')
    qm_kong = qimen.get('空亡', '')
    has_kong = bool(ri_kong or qm_kong)

    if has_kong:
        timing_text = '近期时机未到，事情有虚浮之象，急不得。等条件落定之后转机更明朗。'
        conclusions.append({
            'id': 'timing',
            'appliesTo': question,
            'verdict': timing_text,
            'timing': '需等待条件落定',
            'conditions': ['保持耐心，不急于求成'],
            'guidance': ['静观其变，不要在这个阶段做重大决定'],
            'delivery': 'probable' if has_kong else 'firm',
            'liuyao_evidence_ids': ['time_pattern'],
            'qimen_evidence_ids': ['time_gate'],
            'counter_evidence_ids': [],
            'liuyao_level': 'medium' if ri_kong else 'low',
            'qimen_level': 'medium' if qm_kong else 'low',
            'agreement': 'same' if ri_kong and qm_kong else 'complementary',
        })

    # 3. 核心结论 (outcome)
    outcome_verdict, outcome_timing, outcome_conditions, outcome_guidance = build_outcome(
        question, liuyao, qimen, category, has_kong
    )
    if outcome_verdict:
        ly_lvl = 'medium' if overall_agree else 'low'
        qm_lvl = 'medium' if overall_agree else 'low'
        conclusions.append({
            'id': 'outcome',
            'appliesTo': question,
            'verdict': outcome_verdict,
            'timing': outcome_timing,
            'conditions': outcome_conditions,
            'guidance': outcome_guidance,
            'delivery': 'firm' if overall_agree and ly_tendency in ('吉', '凶') else 'probable',
            'liuyao_evidence_ids': ['outcome_analysis'],
            'qimen_evidence_ids': ['outcome_analysis'],
            'counter_evidence_ids': [],
            'liuyao_level': ly_lvl,
            'qimen_level': qm_lvl,
            'agreement': 'same' if overall_agree else 'complementary',
        })

    # 4. soulNote
    soul_note = build_soul_note(question, ly_tendency, overall_agree)

    return {
        'schemaVersion': 'aceworld-liuyao-qimen-fusion.v2',
        'stage': 'reading',
        'question': {
            'text': question,
            'category': category,
            'answerNeed': 'outcome',
        },
        'methods': {
            'liuyao': {
                '本卦': liuyao.get('本卦', ''),
                '变卦': liuyao.get('变卦', ''),
                '动爻': liuyao.get('动爻', []),
                '世爻': liuyao.get('世爻', {}),
                '应爻': liuyao.get('应爻', {}),
            },
            'qimen': {
                '局数': qimen.get('局数', ''),
                '节气': qimen.get('节气', ''),
                '值符': qimen.get('值符', ''),
                '值使': qimen.get('值使', ''),
                '空亡': qimen.get('空亡', ''),
            },
        },
        'agreement': {
            'overall': overall_status,
            'points': agree_points,
            'conflicts': conflict_points,
        },
        'conclusions': conclusions,
        'diagram': liuyao.get('diagram', ''),
        'soulNote': soul_note,
    }


def build_outcome(question, liuyao, qimen, category, has_kong):
    """生成核心结论"""
    verdict = ''
    timing = ''
    conditions = []
    guidance = []

    # 寻物
    if any(kw in question for kw in ['丢', '找', '遗失', '寻物', '不见了', '在哪']):
        # 能否找回
        shi = liuyao.get('世爻', {})
        ying = liuyao.get('应爻', {})
        qm_conclusion = qimen.get('综合结论', '')
        kezhao = '能找到' in qm_conclusion or '寻回希望' in qm_conclusion

        if kezhao:
            verdict = '东西还在，没有被毁，能找到。但需要花些工夫去找。'
            timing = '一周内多加留意，尤其在自己常去但不常翻的地方'
            conditions = ['仔细回想最后见过的时间地点', '检查角落、柜子底部、袋子夹层']
            guidance = ['不要等，今天就动手找', '先查家里再问身边人']
        else:
            verdict = '东西不在原来的地方了，找回有一定难度。但不是完全没有机会。'
            timing = '一两周内如果还找不到，可能就要做最坏的打算了'
            conditions = ['先确定最后一次见到的时间和地点', '问一问曾经同行或接触过的人']
            guidance = ['扩大查找范围，不只局限在一个房间', '准备好替代方案，有备无患']

    # 事业
    elif any(kw in question for kw in ['工作', '事业', '面试', 'offer', '升职', '跳槽', '职场']):
        shi = liuyao.get('世爻', {})
        shi_qin = shi.get('六亲', '')
        if shi_qin in ('妻财', '子孙'):
            verdict = '这件事能成，而且比你预想的要顺。'
            timing = '变化很快会来，本月到三个月内就有消息'
            conditions = ['保持现在的工作节奏，不要急于表态', '准备好自己，机会来的时候抓得住']
            guidance = ['安静等待通知，不要频繁催促对方', '自己先整理好思路，想清楚最想要什么']
        elif shi_qin in ('兄弟', '官鬼'):
            verdict = '这件事有点阻力，不是不成，是路不太顺。可能要等一等或者换一种方式。'
            timing = '可能要等上两三个月，中间会有一次反复'
            conditions = ['不要在一棵树上吊死，多找几条路', '听取身边有经验的人的建议']
            guidance = ['先稳住心态，不要因为一时不顺就否定自己', '可以考虑调整方向或者降低预期']
        else:
            verdict = '眼下不是最好的时机，但也不是最坏的。稳住，别急。'
            timing = '入秋以后变化会更明显'
            conditions = ['不要在当前的事情上过度投入']
            guidance = ['把精力放在自己能控制的事情上']

    # 感情
    elif any(kw in question for kw in ['感情', '恋爱', '婚姻', '分手', '吵架', '男朋友', '女朋友', '老公', '老婆', '在一起']):
        verdict = '关系本身没什么大问题，主要是近期的沟通方式和情绪积累。不是你或者对方不好，是这段时间的节奏不对。'
        timing = '走完这个阶段，自然就松了'
        conditions = ['先让自己冷静几天，不要把当下的情绪当成结论', '找一个合适的时机，心平气和地聊一次']
        guidance = ['少说一句伤人的话，比多说一句有用的话更重要', '把重心放回自己身上，关系不是人生的全部']

    # 财运
    elif any(kw in question for kw in ['财', '钱', '赚', '投资', '股票', '基金']):
        verdict = '财路在，但财不会自己来找你。要主动，但不要莽撞。'
        timing = '年内有一次比较明显的进财机会'
        conditions = ['先把风险和底线算清楚再动', '别把所有资源都压在一个地方']
        guidance = ['小步快走比一把定输赢更稳妥', '多听多看少冲动']

    # 通用
    else:
        if has_kong:
            verdict = '眼下时机未到，条件还不成熟。但事有转圜余地，不要放弃。'
            timing = '等条件落定再作判断'
            conditions = ['保持耐心']
            guidance = ['做好眼前的事，静待变化']
        else:
            verdict = '这件事有它的走向，不必太过担心。做你该做的，剩下交给时间。'
            timing = '近期就会有变化'
            conditions = ['保持观察，及时调整']
            guidance = ['不要因为一时看不清就什么都不做']

    return verdict, timing, conditions, guidance


def build_soul_note(question, tendency, overall_agree):
    """生成 soulNote"""
    if '丢' in question or '找' in question or '遗失' in question:
        return '有些东西不是丢了，是暂时藏起来，等你安静下来才能找到。'
    if '工作' in question or '事业' in question or '面试' in question:
        return '你要过的关不是有没有机会，而是愿不愿意离开已经不合身的位置。'
    if '感情' in question or '恋爱' in question or '分手' in question:
        return '人有时候也有意思，嘴上说随缘，心里那根绳攥得比谁都紧。'
    if tendency == '吉':
        return '天时在你这边，但地利靠做事，人和靠做人。'
    if tendency == '凶':
        return '难关不是惩罚，是让你知道什么才是真正重要的。'
    return '事在人为，卦只是映照。'


def main():
    parser = argparse.ArgumentParser(description='六爻+奇门双法融合算事')
    parser.add_argument('--question', required=True, help='所问之事')
    parser.add_argument('--category', default='general', choices=['general','relationship','career','wealth','health','legal','study','travel','property'], help='问事类别')
    parser.add_argument('--method', default='time', choices=['time', 'numbers'])
    parser.add_argument('--numbers', help='报数起卦的三个数，逗号分隔')
    parser.add_argument('--year', type=int, required=True)
    parser.add_argument('--month', type=int, required=True)
    parser.add_argument('--day', type=int, required=True)
    parser.add_argument('--hour', type=int, required=True)
    parser.add_argument('--minute', type=int, default=0)
    parser.add_argument('--timeZone', type=int, default=8)
    parser.add_argument('--output', default='fusion.json')

    args = parser.parse_args()
    dt = datetime(args.year, args.month, args.day, args.hour, args.minute)

    # 解析报数
    numbers = None
    if args.method == 'numbers' and args.numbers:
        try:
            numbers = [int(n.strip()) for n in args.numbers.split(",")]
            if len(numbers) != 3:
                print("错误: 必须输入恰好 3 个正整数", file=sys.stderr)
                sys.exit(1)
        except ValueError:
            print("错误: 参数格式不正确，请输入 3 个正整数，用逗号分隔", file=sys.stderr)
            sys.exit(1)

    # 1. 六爻排盘
    liuyao = paipan_liuyao(dt, method=args.method, numbers=numbers, time_zone=args.timeZone, category=args.category, question=args.question)

    # 2. 奇门排盘+解盘
    qimen = paipan_qimen(args.year, args.month, args.day, args.hour, args.minute, args.question, time_zone=args.timeZone, category=args.category)

    # 3. 融合
    result = fuse(args.question, liuyao, qimen, category=args.category)

    # 写入结果
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Fusion complete → {args.output}")
    print(f"  Agree points: {len(result['agreement']['points'])}")
    print(f"  Conflict points: {len(result['agreement']['conflicts'])}")
    print(f"  Conclusions: {len(result['conclusions'])}")


if __name__ == '__main__':
    main()
