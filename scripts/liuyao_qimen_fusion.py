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
from diagram_render import build_diagram_data

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


def paipan_qimen(y, m, d, h, mi, question, time_zone=8, category='general', time_basis='local'):
    """Call the bundled deterministic Qimen engine and map it to the V4 fusion shape."""
    chart = _run_local_chart('qimen.cjs', [
        f"--question={question}", f"--category={category}",
        f"--year={y}", f"--month={m}", f"--day={d}",
        f"--hour={h}", f"--minute={mi}", f"--timeZone={time_zone}",
        f"--timeBasis={time_basis}",
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
        'eventTime': chart.get('eventTime', {}),
        'basisComparison': chart.get('basisComparison', {}),
        'raw_output': chart,
    }

LEVEL_RANK = {'none': 0, 'low': 1, 'medium': 2, 'high': 3}
HEDGE_WORDS = ('大概率', '可能', '也许', '或许', '多半', '不一定', '说不准', '难说', '未必', '倾向于')
RESIDUAL_WORDS = ('多半', '可能', '取决于', '要看', '不算板上钉钉', '留有余地')

CATEGORY_SAFETY = {
    'health': '这次只看压力、节奏和恢复倾向，不能当诊断，身体不适要以专业检查为准。',
    'legal': '程序和证据的事只作节奏参考，不能替代律师意见和正式期限。',
    'wealth': '这里只说财路和节奏，不承诺收益，也不点具体标的。',
    'relationship': '只说关系里的节奏和相处方式，不替你判离婚、复合这类不可逆的事。',
    'travel': '行程以出票、签证、天气和当地通知为准。',
    'property': '价格、产权和交付条件要逐项核实，不能只看口头承诺。',
    'study': '结果以正式评审和截止时间为准。',
}

CATEGORY_CONDITIONS = {
    'career': '把节点、交付物和对方要签的字先落成书面',
    'relationship': '先把情绪和事实分开，再谈条件',
    'wealth': '先算清自己能亏多少，再谈能赚多少',
    'property': '把价格、产权和交付逐项写进合同',
    'study': '按截止时间倒排准备节点',
    'travel': '先把票、证件和备用方案定下来',
    'general': '先把可控的那一步做扎实',
}

# 只有像"要先处理什么"的判据才进条件清单；纯象辞留在断语里，不当作行动项。
ACTIONABLE_MARKERS = ('空亡', '破', '克', '伏吟', '反吟', '待', '需', '等', '避免', '不宜', '未匹配', '入墓')


def _text_of(item, *keys):
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ''


def _has_marker(text, markers):
    return any(marker in text for marker in markers)


# 判据性质分三档：结构性反证（用神被否）、延后（空亡/伏吟一类）、状态偏弱（休囚）。
# 这三档只决定方向与交付档位，不换算成准确率、成功率或吉凶分。
SEVERE_MARKERS = ('回头克', '化空', '化退', '月破', '日破', '入墓', '未匹配', '受制', '冲破')
DELAY_MARKERS = ('空亡', '伏吟', '反吟', '虚象', '推迟', '延期', '停滞')
MILD_MARKERS = ('休', '囚', '死', '泄', '弱', '受克')


def _severity(texts):
    severe = sum(1 for text in texts if _has_marker(text, SEVERE_MARKERS))
    delay = sum(1 for text in texts if _has_marker(text, DELAY_MARKERS))
    mild = sum(1 for text in texts if _has_marker(text, MILD_MARKERS))
    return severe, delay, mild


def _summarize(book, evidence_ids, fallback='本盘未见明确判据'):
    """挑一条最能说明问题的判据；只有短语时补上它出自哪一爻或哪一宫。"""
    for evidence_id in evidence_ids:
        text = book.text_of(evidence_id)
        if len(text) >= 6:
            return text
    if evidence_ids:
        index = int(evidence_ids[0].split('-')[1]) - 1
        if 0 <= index < len(book.items):
            item = book.items[index]
            return f"{item['label']}{item['text']}"
    return fallback


class EvidenceBook:
    """收集本次盘面的真实判据，并给每条判据一个有编号、可回指的记录。"""

    def __init__(self, prefix, method_key):
        self.prefix = prefix
        self.method_key = method_key
        self.items = []

    def add(self, kind, label, text):
        text = (text or '').strip()
        if not text:
            return None
        self.items.append({'kind': kind, 'label': label, 'text': text})
        return f'{self.prefix}-{len(self.items):02d}'

    @property
    def evidence(self):
        return [
            {
                'id': f'{self.prefix}-{index + 1:02d}',
                'system': self.method_key,
                'label': item['label'],
                'kind': item['kind'],
                'sourcePath': f'/methods/{self.method_key}/evidence/items/{index}/text',
                'value': item['text'],
            }
            for index, item in enumerate(self.items)
        ]

    @property
    def document(self):
        return {'items': self.items}

    def text_of(self, evidence_id):
        if not evidence_id:
            return ''
        index = int(evidence_id.split('-')[1]) - 1
        if 0 <= index < len(self.items):
            return self.items[index]['text']
        return ''


def read_liuyao(liuyao):
    """从六爻引擎输出的结构化证据里读判据，不再按问事类别套固定文案。"""
    chart = liuyao.get('raw_output') or {}
    analysis = ((chart.get('interpretation') or {}).get('analysis') or {})
    book = EvidenceBook('ly', 'liuyao')

    selection = analysis.get('selectionFact') or {}
    selected = analysis.get('selectedCandidate') or {}
    references = selected.get('references') or []
    counter_summary = analysis.get('counterSummaryFact') or {}
    counter_facts = analysis.get('counterEvidenceFacts') or []
    timing_facts = analysis.get('timingFacts') or []
    structure_facts = analysis.get('structureFacts') or []
    line_facts = analysis.get('lineFacts') or []

    useful_id = book.add(
        '用神', '六爻用神',
        _text_of(selection, 'promptText') or _text_of(selected, 'promptText')
        or '本卦未见与问事主题匹配的用神候选',
    )

    help_ids, hurt_ids = [], []
    for reference in references[:3]:
        label = '第{position}爻{relative}{branch}{wuxing}'.format(
            position=reference.get('position', ''),
            relative=reference.get('sixRelative', ''),
            branch=reference.get('branch', ''),
            wuxing=reference.get('wuxing', ''),
        )
        for text in (reference.get('support') or [])[:1]:
            evidence_id = book.add('得助', label, text)
            if evidence_id:
                help_ids.append(evidence_id)
        for text in (reference.get('constraints') or [])[:1]:
            evidence_id = book.add('受限', label, text)
            if evidence_id:
                hurt_ids.append(evidence_id)
        changed = reference.get('changedYao') or {}
        relation = changed.get('relation') or ''
        if relation:
            evidence_id = book.add('动变', label + '动变', f'动变关系：{relation}')
            if evidence_id and _has_marker(relation, ('回头生', '化进')):
                help_ids.append(evidence_id)
            if evidence_id and _has_marker(relation, ('回头克', '化空', '化退', '冲')):
                hurt_ids.append(evidence_id)

    void_present = any(reference.get('isVoid') for reference in references)
    world = next((item for item in line_facts if '世爻' in (item.get('roles') or [])), None)
    if world:
        if world.get('isVoid'):
            void_present = True
        for text in (world.get('support') or [])[:1]:
            evidence_id = book.add('世爻得助', '世爻', text)
            if evidence_id:
                help_ids.append(evidence_id)
        for text in (world.get('constraints') or [])[:1]:
            evidence_id = book.add('世爻受限', '世爻', text)
            if evidence_id:
                hurt_ids.append(evidence_id)

    counter_ids = []
    for fact in counter_facts[:3]:
        evidence_id = book.add(
            '反证', fact.get('candidateLabel') or '反证',
            _text_of(fact, 'detail') or _text_of(fact, 'promptText'),
        )
        if evidence_id:
            counter_ids.append(evidence_id)

    timing_ids = []
    for fact in timing_facts[:2]:
        evidence_id = book.add('应期条件', fact.get('type') or '应期', _text_of(fact, 'promptText'))
        if evidence_id:
            timing_ids.append(evidence_id)

    structure_ids = []
    for fact in structure_facts[:2]:
        evidence_id = book.add(
            '卦内结构', fact.get('kind') or '卦内结构',
            _text_of(fact, 'promptText') or _text_of(fact, 'originalText'),
        )
        if evidence_id:
            structure_ids.append(evidence_id)

    hurt_texts = [book.text_of(evidence_id) for evidence_id in hurt_ids]
    severe, delay, mild = _severity(hurt_texts)
    balance = 2 * len(help_ids) - 2 * severe - delay - mild
    if not references:
        direction, level = '平', 'low'
    else:
        direction = '吉' if balance >= 2 else ('凶' if balance <= -2 else '平')
        if severe:
            level = 'low'
        elif delay or mild >= 2 or void_present:
            level = 'medium'
        elif help_ids and direction in ('吉', '凶'):
            level = 'high'
        else:
            level = 'medium'

    support_text = _summarize(book, help_ids, fallback='')
    limit_text = _summarize(book, hurt_ids, fallback='')
    if not support_text and not limit_text:
        support_text = book.text_of(useful_id)

    return {
        'direction': direction,
        'level': level,
        'usefulGod': book.text_of(useful_id),
        'evidence': book,
        'helpIds': help_ids,
        'hurtIds': hurt_ids,
        'counterIds': counter_ids,
        'timingIds': timing_ids,
        'structureIds': structure_ids,
        'supportText': support_text,
        'limitText': limit_text,
        'summary': '；'.join(part for part in (support_text, limit_text) if part) or '本盘未见明确判据',
    }


def read_qimen(qimen):
    """从奇门盘面的格局、用神与空亡里读判据。"""
    book = EvidenceBook('qm', 'qimen')
    signals = qimen.get('signals') or {}
    geju = qimen.get('格局分析') or []
    special = qimen.get('特殊状态') or []
    yong = qimen.get('用神定位') or {}
    kong = (qimen.get('空亡') or '').strip()

    favorable_ids, risky_ids = [], []
    for item in geju[:4]:
        name = _text_of(item, '格局', '名称', '遁格') or '格局'
        tone = item.get('吉凶') or ''
        evidence_id = book.add('格局', name, _text_of(item, '含义', 'promptText') or f'{name}（{tone}）')
        if not evidence_id:
            continue
        if tone in ('吉', '大吉', '中上'):
            favorable_ids.append(evidence_id)
        elif tone in ('凶', '大凶', '中下'):
            risky_ids.append(evidence_id)

    for item in special[:3]:
        problems = item.get('问题')
        text = problems if isinstance(problems, str) else '、'.join(problems or [])
        evidence_id = book.add('特殊状态', _text_of(item, '名称') or '特殊状态', text or _text_of(item, 'promptText'))
        if evidence_id:
            risky_ids.append(evidence_id)

    for text in (signals.get('warnings') or [])[:2]:
        evidence_id = book.add('提示', '奇门提示', text)
        if evidence_id:
            risky_ids.append(evidence_id)

    zhu = yong.get('主用神') if isinstance(yong.get('主用神'), list) else []
    fu = yong.get('辅助用神') if isinstance(yong.get('辅助用神'), list) else []
    useful_parts = []
    if zhu:
        useful_parts.append('主用神' + '、'.join(zhu))
    if fu:
        useful_parts.append('辅看' + '、'.join(fu))
    useful_id = book.add(
        '用神宫', '奇门用神',
        '；'.join(useful_parts) or _text_of(yong, 'promptText') or '未定位到用神宫',
    )
    kong_id = book.add('空亡', '奇门空亡', f'本次盘面空亡：{kong}') if kong else None

    direction_map = {'favorable': '吉', 'unfavorable': '凶', 'mixed': '平'}
    direction = direction_map.get(signals.get('direction'), '平')
    strength = signals.get('strength') or 'low'
    risky_texts = [book.text_of(evidence_id) for evidence_id in risky_ids]
    severe, delay, mild = _severity(risky_texts)
    if not geju and not yong and not special:
        level = 'low'
    elif severe:
        level = 'low'
    elif direction in ('吉', '凶') and favorable_ids and not delay and mild == 0:
        level = 'high'
    elif strength in ('high', 'medium') and delay <= 2:
        level = 'medium'
    elif favorable_ids or risky_ids:
        level = 'medium'
    else:
        level = 'low'

    support_text = _summarize(book, favorable_ids, fallback='')
    limit_text = _summarize(book, risky_ids, fallback='')
    if not limit_text and kong_id:
        limit_text = book.text_of(kong_id)
    if not support_text and not limit_text:
        support_text = book.text_of(useful_id)

    return {
        'direction': direction,
        'level': level,
        'usefulGod': book.text_of(useful_id),
        'evidence': book,
        'helpIds': favorable_ids,
        'hurtIds': risky_ids,
        'counterIds': [],
        'timingIds': ([kong_id] if kong_id else []),
        'structureIds': risky_ids[:1],
        'supportText': support_text,
        'limitText': limit_text,
        'summary': '；'.join(part for part in (support_text, limit_text) if part) or '本盘未见明确判据',
    }


def _overall_status(liuyao_direction, qimen_direction):
    if liuyao_direction == qimen_direction:
        return 'same'
    if {'吉', '凶'} == {liuyao_direction, qimen_direction}:
        return 'conflict'
    return 'complementary'


def _decide_delivery(ly, qm, status, counter_ids):
    """双高同向且无同级反证才说死；双中留余地；依据弱或相左如实并列。"""
    if (
        ly['level'] == 'high'
        and qm['level'] == 'high'
        and status == 'same'
        and not counter_ids
        and ly['direction'] in ('吉', '凶')
    ):
        return 'firm'
    if 'low' in (ly['level'], qm['level']) or status == 'conflict' or counter_ids:
        return 'tentative'
    return 'probable'


def _verdict_text(direction, delivery, ly, qm, category):
    support = ly['supportText'] or qm['supportText'] or '盘面给了明确指向'
    limit = ly['limitText'] or qm['limitText'] or CATEGORY_CONDITIONS.get(category, CATEGORY_CONDITIONS['general'])
    if delivery == 'firm':
        if direction == '吉':
            return f'能成。{support}，方向是顺的，这事会往前走。'
        return f'不成，或者只能成个样子。{limit}，再往上加筹码只会更被动。'
    if delivery == 'probable':
        if direction == '吉':
            return f'多半能成，但不是板上钉钉。{support}；会不会卡住，取决于{limit}。'
        if direction == '凶':
            return f'多半不成。{limit}；除非{support}，否则别硬推。'
        return f'眼下看不出明显一边倒。{support}，同时{limit}，要再看一步。'
    return (
        f'两法指向不一致：六爻讲{ly["direction"]}，奇门讲{qm["direction"]}。'
        f'两种可能都得放上桌——偏成的情形是{support}；偏不成的情形是{limit}。'
    )


def _timing_text(ly, qm):
    hints = []
    for evidence_id in ly['timingIds'][:1]:
        hints.append(ly['evidence'].text_of(evidence_id))
    for evidence_id in qm['timingIds'][:1]:
        hints.append(qm['evidence'].text_of(evidence_id))
    if not hints:
        return '盘面没给明确应期，先按下一步反馈判断；具体还要看条件是否出现'
    return '；'.join(hint for hint in hints if hint) + '；具体还要看条件是否出现'


def fuse(question, liuyao, qimen, category='general', time_basis='local',
         desired_outcome='', known_context=None):
    """六爻+奇门双法融合：两法各出判据，再在同一时基上比方向、定交付口径。"""
    ly = read_liuyao(liuyao)
    qm = read_qimen(qimen)
    known_context = [item for item in (known_context or []) if str(item).strip()]

    status = _overall_status(ly['direction'], qm['direction'])
    counter_ids = ly['counterIds'] + qm['counterIds']
    delivery = _decide_delivery(ly, qm, status, counter_ids)

    agree_points = [
        {
            'dimension': '总体吉凶',
            'verdict': f'六爻偏{ly["direction"]}，奇门偏{qm["direction"]}',
            'delivery': delivery,
            'detail': f'六爻：{ly["summary"]}；奇门：{qm["summary"]}',
        }
    ]
    conflict_points = []
    if status == 'conflict':
        conflict_points.append({
            'dimension': '总体吉凶',
            'liuyao': ly['summary'],
            'qimen': qm['summary'],
            'resolution': '两法方向相反，如实说明两种可能，不强行统一',
        })

    conditions = [CATEGORY_CONDITIONS.get(category, CATEGORY_CONDITIONS['general'])]
    for text in (ly['limitText'], qm['limitText']):
        if text and len(text) <= 24 and _has_marker(text, ACTIONABLE_MARKERS) \
                and f'先处理：{text}' not in conditions:
            conditions.append(f'先处理：{text}')
    guidance = [CATEGORY_CONDITIONS.get(category, CATEGORY_CONDITIONS['general'])]
    safety = CATEGORY_SAFETY.get(category, '')
    if safety:
        conditions.append(safety)

    conclusions = [
        {
            'id': 'outcome',
            'appliesTo': desired_outcome.strip() or question,
            'verdict': _verdict_text(ly['direction'] if status != 'conflict' else '平', delivery, ly, qm, category),
            'timing': _timing_text(ly, qm),
            'conditions': conditions,
            'guidance': guidance,
            'delivery': delivery,
            'liuyao_evidence_ids': (ly['helpIds'][:2] + ly['hurtIds'][:1]) or ly['structureIds'][:1],
            'qimen_evidence_ids': (qm['helpIds'][:2] + qm['hurtIds'][:1]) or qm['timingIds'][:1],
            'counter_evidence_ids': counter_ids[:3],
            'liuyao_level': ly['level'],
            'qimen_level': qm['level'],
            'agreement': status,
        }
    ]

    if ly['timingIds'] or qm['timingIds']:
        conclusions.append({
            'id': 'timing',
            'appliesTo': desired_outcome.strip() or question,
            'verdict': _timing_text(ly, qm),
            'timing': '以盘内触发条件为准，不锁定具体日期',
            'conditions': ['等触发条件出现再推进'],
            'guidance': ['不要在条件未出现前反复催问'],
            'delivery': 'probable' if (ly['timingIds'] and qm['timingIds']) else 'tentative',
            'liuyao_evidence_ids': ly['timingIds'][:1],
            'qimen_evidence_ids': qm['timingIds'][:1],
            'counter_evidence_ids': [],
            'liuyao_level': 'medium' if ly['timingIds'] else 'low',
            'qimen_level': 'medium' if qm['timingIds'] else 'low',
            'agreement': 'same' if (ly['timingIds'] and qm['timingIds']) else 'complementary',
        })

    basis = qimen.get('basisComparison') or {}
    document = {
        'schemaVersion': 'aceworld-liuyao-qimen-fusion.v3',
        'stage': 'reading',
        'timeBasis': time_basis,
        'basisComparison': {
            'localPillars': basis.get('localPillars', ''),
            'beijingPillars': basis.get('beijingPillars', ''),
            'diverges': bool(basis.get('diverges')),
            'differences': basis.get('differences', []),
        },
        'question': {
            'text': question,
            'category': category,
            'answerNeed': 'outcome',
            'desiredOutcome': desired_outcome.strip(),
            'knownContext': known_context,
        },
        'methods': {
            'liuyao': {
                '本卦': liuyao.get('本卦', ''),
                '变卦': liuyao.get('变卦', ''),
                '动爻': liuyao.get('动爻', []),
                '世爻': liuyao.get('世爻', {}),
                '应爻': liuyao.get('应爻', {}),
                'direction': ly['direction'],
                'level': ly['level'],
                'evidence': ly['evidence'].document,
            },
            'qimen': {
                '局数': qimen.get('局数', ''),
                '节气': qimen.get('节气', ''),
                '值符': qimen.get('值符', ''),
                '值使': qimen.get('值使', ''),
                '空亡': qimen.get('空亡', ''),
                'direction': qm['direction'],
                'level': qm['level'],
                'evidence': qm['evidence'].document,
            },
        },
        'evidence': ly['evidence'].evidence + qm['evidence'].evidence,
        'agreement': {
            'overall': status,
            'points': agree_points,
            'conflicts': conflict_points,
        },
        'conclusions': conclusions,
        'diagram': liuyao.get('diagram', ''),  # Legacy audit field, not the new display.
        'diagramData': build_diagram_data(liuyao['raw_output']),
        'soulNote': build_soul_note(question, ly['direction'], status == 'same', category),
    }
    if document['basisComparison']['diverges']:
        differences = '；'.join(document['basisComparison']['differences'])
        document['timeBasisDisclosure'] = (
            f'本次起卦按{time_basis}时基排盘；当地与北京四柱存在差异（{differences}），'
            '跨时区案例以当地时基为准，边界情形需另行核对。'
        )
    return document

def build_soul_note(question, tendency, overall_agree, category='general'):
    """生成 soulNote"""
    normalized = question.casefold()
    if any(keyword in normalized for keyword in ('丢', '找', '遗失', 'perdi', 'sumiu', 'encontrar')):
        return '有些东西不是丢了，是暂时藏起来，等你安静下来才能找到。'
    if category == 'career' or any(keyword in normalized for keyword in ('工作', '事业', '面试', 'trabalho', 'carreira', 'entrevista')):
        return '你要过的关不是有没有机会，而是愿不愿意离开已经不合身的位置。'
    if category == 'relationship' or any(keyword in normalized for keyword in ('感情', '恋爱', '分手', 'relacionamento', 'amor', 'separação', 'separacao')):
        return '人有时候也有意思，嘴上说随缘，心里那根绳攥得比谁都紧。'
    if tendency == '吉':
        return '天时在你这边，但地利靠做事，人和靠做人。'
    if tendency == '凶':
        return '难关不是惩罚，是让你知道什么才是真正重要的。'
    return '事在人为，卦只是映照。'


VALID_DELIVERIES = ('firm', 'probable', 'tentative')
VALID_LEVELS = ('none', 'low', 'medium', 'high')
VALID_STATUS = ('same', 'complementary', 'conflict')


def _resolve_pointer(document, pointer):
    """按 JSON pointer 取回融合文档里的真实字段，用于核对判据编号。"""
    if not isinstance(pointer, str) or not pointer.startswith('/'):
        return None
    value = document
    for raw in pointer[1:].split('/'):
        key = raw.replace('~1', '/').replace('~0', '~')
        if key in ('__proto__', 'prototype', 'constructor'):
            return None
        if isinstance(value, list):
            if not key.isdigit() or int(key) >= len(value):
                return None
            value = value[int(key)]
            continue
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def check_document(document):
    """把交付口径落成可执行校验：说死的档位必须真有两法各自的高强度依据。"""
    errors = []
    if document.get('schemaVersion') != 'aceworld-liuyao-qimen-fusion.v3':
        errors.append('schemaVersion 不匹配')
    if document.get('timeBasis') not in ('local', 'beijing'):
        errors.append('timeBasis 必须是 local 或 beijing')
    comparison = document.get('basisComparison')
    if not isinstance(comparison, dict):
        errors.append('basisComparison 缺失')
    elif comparison.get('diverges') and not str(document.get('timeBasisDisclosure') or '').strip():
        errors.append('时基存在差异时必须给出 timeBasisDisclosure')
    question = document.get('question')
    if not isinstance(question, dict):
        errors.append('question 缺失')
    else:
        for key in ('desiredOutcome', 'knownContext'):
            if key not in question:
                errors.append(f'question.{key} 缺失')

    registry = {}
    for item in document.get('evidence') or []:
        if not isinstance(item, dict):
            errors.append('evidence 条目必须是对象')
            continue
        evidence_id = item.get('id')
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            errors.append('evidence.id 必须非空')
            continue
        if evidence_id in registry:
            errors.append(f'evidence.id 重复：{evidence_id}')
        registry[evidence_id] = item
        if item.get('system') not in ('liuyao', 'qimen'):
            errors.append(f'{evidence_id} system 非法')
        for key in ('label', 'kind'):
            if not str(item.get(key) or '').strip():
                errors.append(f'{evidence_id} {key} 不能为空')
        actual = _resolve_pointer(document, item.get('sourcePath'))
        if actual is None:
            errors.append(f'{evidence_id} sourcePath 无法回指本次盘面')
        elif actual != item.get('value'):
            errors.append(f'{evidence_id} value 与盘面字段不一致')

    agreement = document.get('agreement')
    if not isinstance(agreement, dict) or agreement.get('overall') not in VALID_STATUS:
        errors.append('agreement.overall 非法')
        agreement = agreement if isinstance(agreement, dict) else {}
    points = agreement.get('points') or []
    if not points:
        errors.append('agreement.points 不能为空')
    for index, point in enumerate(points):
        if not str((point or {}).get('detail') or '').strip():
            errors.append(f'agreement.points[{index}].detail 不能为空')
    conflicts = agreement.get('conflicts') or []
    if agreement.get('overall') == 'same' and conflicts:
        errors.append('overall=same 但 conflicts 非空')

    conclusions = document.get('conclusions') or []
    if not 1 <= len(conclusions) <= 4:
        errors.append('conclusions 需 1..4 条')
    seen_ids = set()
    for index, conclusion in enumerate(conclusions):
        label = f'conclusions[{index}]'
        if not isinstance(conclusion, dict):
            errors.append(f'{label} 不是对象')
            continue
        if not str(conclusion.get('id') or '').strip() or not str(conclusion.get('verdict') or '').strip():
            errors.append(f'{label} 缺少 id 或 verdict')
        if conclusion.get('id') in seen_ids:
            errors.append('结论 id 重复')
        seen_ids.add(conclusion.get('id'))
        delivery = conclusion.get('delivery')
        if delivery not in VALID_DELIVERIES:
            errors.append(f'{label} delivery 非法')
        for key in ('liuyao_level', 'qimen_level'):
            if conclusion.get(key) not in VALID_LEVELS:
                errors.append(f'{label} {key} 非法')
        if conclusion.get('agreement') not in VALID_STATUS:
            errors.append(f'{label} agreement 非法')
        for key in ('conditions', 'guidance', 'liuyao_evidence_ids', 'qimen_evidence_ids', 'counter_evidence_ids'):
            value = conclusion.get(key)
            if not isinstance(value, list) or any(not isinstance(entry, str) for entry in value):
                errors.append(f'{label} {key} 必须是字符串数组')
        referenced = []
        for key in ('liuyao_evidence_ids', 'qimen_evidence_ids', 'counter_evidence_ids'):
            referenced.extend(conclusion.get(key) or [])
        for evidence_id in referenced:
            if evidence_id not in registry:
                errors.append(f'{label} 引用了不存在的判据：{evidence_id}')

        liuyao_ids = set(conclusion.get('liuyao_evidence_ids') or [])
        qimen_ids = set(conclusion.get('qimen_evidence_ids') or [])
        if liuyao_ids and liuyao_ids == qimen_ids:
            errors.append(f'{label} 两法引用同一组判据编号，等于没有分别取证')
        counter = bool(conclusion.get('counter_evidence_ids'))
        same = agreement.get('overall') == 'same' and conclusion.get('agreement') == 'same'
        both_high = conclusion.get('liuyao_level') == 'high' and conclusion.get('qimen_level') == 'high'
        if delivery == 'firm' and not (both_high and same and not counter):
            errors.append(f'{label} 说死（firm）需两法都 high、方向一致且无反证')
        if conclusion.get('id') == 'outcome' and both_high and same and not counter and delivery != 'firm':
            errors.append(f'{label} 双高同向且无反证时应给出 firm')
        if delivery != 'tentative' and (counter or conclusion.get('agreement') == 'conflict'):
            errors.append(f'{label} 存在反证或方向相左时应降为 tentative')
        if delivery == 'probable' and 'low' in (conclusion.get('liuyao_level'), conclusion.get('qimen_level')):
            errors.append(f'{label} 任一法为 low 时不得给出 probable')

        verdict = conclusion.get('verdict') or ''
        if delivery == 'firm' and _has_marker(verdict, HEDGE_WORDS):
            errors.append(f'{label} 说死档不得出现含糊措辞')
        if delivery == 'probable' and not _has_marker(verdict, RESIDUAL_WORDS):
            errors.append(f'{label} 留余地档必须写出余地或条件')
        if delivery == 'tentative' and '两种' not in verdict:
            errors.append(f'{label} 依据弱或相左时必须并列两种可能')
    return errors


def run_self_test():
    """固定输入回归：验证分级、交付门禁、判据回指与时基披露。"""
    cases = [
        {
            'question': '月底前甲方会不会签下这份合同', 'category': 'career',
            'method': 'numbers', 'numbers': [12, 35, 8], 'year': 2026, 'month': 8,
            'day': 29, 'hour': 15, 'minute': 0, 'time_zone': 8, 'time_basis': 'local',
            'desired_outcome': '确认月底前能否签约',
        },
        {
            'question': '这笔钱年内能不能回笼', 'category': 'wealth',
            'method': 'numbers', 'numbers': [3, 7, 9], 'year': 2026, 'month': 8,
            'day': 29, 'hour': 9, 'minute': 20, 'time_zone': -3, 'time_basis': 'local',
            'desired_outcome': '',
        },
        {
            'question': '这个月要不要换工作', 'category': 'career',
            'method': 'time', 'numbers': None, 'year': 2026, 'month': 9,
            'day': 20, 'hour': 10, 'minute': 30, 'time_zone': -3, 'time_basis': 'beijing',
            'desired_outcome': '',
        },
    ]
    failures = 0
    for case in cases:
        dt = datetime(case['year'], case['month'], case['day'], case['hour'], case['minute'])
        liuyao = paipan_liuyao(
            dt, method=case['method'], numbers=case['numbers'],
            time_zone=case['time_zone'], category=case['category'], question=case['question'],
        )
        qimen = paipan_qimen(
            case['year'], case['month'], case['day'], case['hour'], case['minute'],
            case['question'], time_zone=case['time_zone'], category=case['category'],
            time_basis=case['time_basis'],
        )
        document = fuse(
            case['question'], liuyao, qimen, category=case['category'],
            time_basis=case['time_basis'], desired_outcome=case['desired_outcome'],
        )
        errors = check_document(document)
        name = f"{case['category']}/{case['method']}/tz{case['time_zone']}/{case['time_basis']}"
        if errors:
            failures += 1
            print(f'[FAIL] {name}')
            for error in errors:
                print(f'       {error}')
        else:
            delivery = document['conclusions'][0]['delivery']
            ly_level = document['conclusions'][0]['liuyao_level']
            qm_level = document['conclusions'][0]['qimen_level']
            print(f'[PASS] {name} delivery={delivery} liuyao={ly_level} qimen={qm_level} '
                  f'evidence={len(document["evidence"])} conflicts={len(document["agreement"]["conflicts"])}')
    if failures:
        print(f'[FAIL] {failures}/{len(cases)} 个用例未通过')
    else:
        print(f'[PASS] {len(cases)}/{len(cases)} 个盘面用例通过')
    return failures + _rule_case_tests()


def _synthetic_document(liuyao_level, qimen_level, liuyao_direction, qimen_direction,
                        with_counter=False, force_delivery=None):
    """手搓一份最小但结构完整的融合文档，用来验证交付门禁本身。"""
    status = _overall_status(liuyao_direction, qimen_direction)
    counter_ids = ['ly-03'] if with_counter else []
    delivery = force_delivery or _decide_delivery(
        {'level': liuyao_level, 'direction': liuyao_direction},
        {'level': qimen_level, 'direction': qimen_direction},
        status, counter_ids,
    )
    verdict = _verdict_text(
        liuyao_direction if status != 'conflict' else '平', delivery,
        {'supportText': '用神临世得月建', 'limitText': '用神月破', 'direction': liuyao_direction},
        {'supportText': '开门临用神宫', 'limitText': '用神宫空亡', 'direction': qimen_direction},
        'career',
    )
    return {
        'schemaVersion': 'aceworld-liuyao-qimen-fusion.v3',
        'stage': 'reading',
        'timeBasis': 'local',
        'basisComparison': {'localPillars': '丙午 丁酉 丁酉 乙巳', 'beijingPillars': '丙午 丁酉 丁酉 辛亥',
                            'diverges': False, 'differences': []},
        'question': {'text': '月底前这份合同签得成吗', 'category': 'career', 'answerNeed': 'outcome',
                     'desiredOutcome': '', 'knownContext': []},
        'methods': {
            'liuyao': {'direction': liuyao_direction, 'level': liuyao_level,
                       'evidence': {'items': [{'kind': '用神', 'label': '用神', 'text': '用神临世得月建'},
                                              {'kind': '反证', 'label': '反证', 'text': '用神月破'}]}},
            'qimen': {'direction': qimen_direction, 'level': qimen_level,
                      'evidence': {'items': [{'kind': '格局', 'label': '格局', 'text': '开门临用神宫'}]}},
        },
        'evidence': [
            {'id': 'ly-01', 'system': 'liuyao', 'label': '用神', 'kind': '用神',
             'sourcePath': '/methods/liuyao/evidence/items/0/text', 'value': '用神临世得月建'},
            {'id': 'qm-01', 'system': 'qimen', 'label': '格局', 'kind': '格局',
             'sourcePath': '/methods/qimen/evidence/items/0/text', 'value': '开门临用神宫'},
            {'id': 'ly-03', 'system': 'liuyao', 'label': '反证', 'kind': '反证',
             'sourcePath': '/methods/liuyao/evidence/items/1/text', 'value': '用神月破'},
        ],
        'agreement': {
            'overall': status,
            'points': [{'dimension': '总体吉凶', 'verdict': f'六爻偏{liuyao_direction}，奇门偏{qimen_direction}',
                        'delivery': delivery, 'detail': '六爻：用神临世得月建；奇门：开门临用神宫'}],
            'conflicts': ([{'dimension': '总体吉凶', 'liuyao': '用神临世得月建', 'qimen': '用神宫空亡',
                            'resolution': '两法方向相反，如实说明两种可能'}]
                          if status == 'conflict' else []),
        },
        'conclusions': [{
            'id': 'outcome', 'appliesTo': '月底前这份合同签得成吗', 'verdict': verdict,
            'timing': '盘面没给明确应期；具体还要看条件是否出现',
            'conditions': ['把节点和交付物落成书面'], 'guidance': ['先把可控的那一步做扎实'],
            'delivery': delivery,
            'liuyao_evidence_ids': ['ly-01'], 'qimen_evidence_ids': ['qm-01'],
            'counter_evidence_ids': counter_ids,
            'liuyao_level': liuyao_level, 'qimen_level': qimen_level, 'agreement': status,
        }],
    }


def _rule_case_tests():
    """三档交付各自可达，且门禁能挡住不该说死的盘子。"""
    failures = 0

    def report(name, errors, expect_clean=True):
        nonlocal failures
        ok = (not errors) if expect_clean else bool(errors)
        print(f'[{"PASS" if ok else "FAIL"}] rule/{name}')
        if not ok:
            failures += 1
            for error in errors[:6]:
                print(f'       {error}')

    firm_doc = _synthetic_document('high', 'high', '吉', '吉')
    report('双高同向→说死', check_document(firm_doc))
    report('双高交付应为firm', [] if firm_doc['conclusions'][0]['delivery'] == 'firm'
           else ['双高同向却未给出 firm'], expect_clean=True)

    probable_doc = _synthetic_document('medium', 'medium', '吉', '吉')
    report('双中留余地', check_document(probable_doc))
    report('双中交付应为probable', [] if probable_doc['conclusions'][0]['delivery'] == 'probable'
           else ['双中未给出 probable'], expect_clean=True)

    conflict_doc = _synthetic_document('high', 'high', '吉', '凶')
    report('两法相左→并列两种可能', check_document(conflict_doc))
    report('相左交付应为tentative', [] if conflict_doc['conclusions'][0]['delivery'] == 'tentative'
           else ['相左未给出 tentative'], expect_clean=True)

    counter_doc = _synthetic_document('high', 'high', '吉', '吉', with_counter=True)
    report('有反证不得说死', check_document(counter_doc))

    bad_doc = _synthetic_document('medium', 'medium', '吉', '吉', force_delivery='firm')
    report('双中不得说死（应被拦下）', check_document(bad_doc), expect_clean=False)

    bad_voice = _synthetic_document('high', 'high', '吉', '吉')
    bad_voice['conclusions'][0]['verdict'] = '多半能成。用神临世得月建。'
    report('说死档不得含糊（应被拦下）', check_document(bad_voice), expect_clean=False)

    if not failures:
        print('[PASS] 交付档位回归全部通过')
    return failures


def main():
    parser = argparse.ArgumentParser(description='六爻+奇门双法融合算事')
    parser.add_argument('--question', help='所问之事')
    parser.add_argument('--category', default='general', choices=['general','relationship','career','wealth','health','legal','study','travel','property'], help='问事类别')
    parser.add_argument('--method', default='time', choices=['time', 'numbers'])
    parser.add_argument('--numbers', help='报数起卦的三个数，逗号分隔')
    parser.add_argument('--year', type=int)
    parser.add_argument('--month', type=int)
    parser.add_argument('--day', type=int)
    parser.add_argument('--hour', type=int)
    parser.add_argument('--minute', type=int, default=0)
    parser.add_argument('--timeZone', type=int, default=8)
    parser.add_argument('--timeBasis', dest='timeBasis', default='local', choices=['local', 'beijing'], help='起卦时基：local=用户所在地，beijing=北京时')
    parser.add_argument('--desiredOutcome', dest='desiredOutcome', default='', help='用户想确认的具体结果')
    parser.add_argument('--knownContext', dest='knownContext', action='append', default=[], help='用户明确说过的现实背景，可重复')
    parser.add_argument('--output', default='fusion.json')
    parser.add_argument('--self-test', dest='self_test', action='store_true', help='跑固定输入回归，验证分级与交付门禁')

    args = parser.parse_args()
    if args.self_test:
        sys.exit(run_self_test())
    if not args.question:
        parser.error('需要 --question，或用 --self-test 跑回归')
    for field in ('year', 'month', 'day', 'hour'):
        if getattr(args, field) is None:
            parser.error(f'缺少 --{field}')

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

    # 2. 奇门排盘+解盘（与六爻同一时基）
    qimen = paipan_qimen(args.year, args.month, args.day, args.hour, args.minute, args.question,
                         time_zone=args.timeZone, category=args.category, time_basis=args.timeBasis)

    # 3. 融合
    result = fuse(args.question, liuyao, qimen, category=args.category, time_basis=args.timeBasis,
                  desired_outcome=args.desiredOutcome, known_context=args.knownContext)

    errors = check_document(result)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}", file=sys.stderr)
        sys.exit(1)

    # 写入结果
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    primary = result['conclusions'][0]
    print(f"Fusion complete → {args.output}")
    print(f"  时基: {result['timeBasis']}（当地四柱 {result['basisComparison']['localPillars']} / 北京 {result['basisComparison']['beijingPillars']}）")
    print(f"  六爻: {result['methods']['liuyao']['direction']}/{result['methods']['liuyao']['level']}"
          f"  奇门: {result['methods']['qimen']['direction']}/{result['methods']['qimen']['level']}"
          f"  → {primary['delivery']}")
    print(f"  Agree points: {len(result['agreement']['points'])}")
    print(f"  Conflict points: {len(result['agreement']['conflicts'])}")
    print(f"  Conclusions: {len(result['conclusions'])}")


if __name__ == '__main__':
    main()
