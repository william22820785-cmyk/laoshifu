#!/usr/bin/env python3
"""
黑箱融合引擎 — 六爻 + 奇门遁甲 双算法对比，输出融合解盘结果
完全黑箱：内部两种算法独立跑，外部只看到融合后的结果

路径依赖已适配 laoshifu-v2 skill 目录结构。
"""
import sys, os, json
from datetime import datetime

# 六爻引擎
sys.path.insert(0, '/root/.openclaw/workspace/skills/yxf_yixue')
from yxf_yixue.liuyao.liuyao_api import LiuyaoApi

# 奇门引擎
sys.path.insert(0, '/root/.openclaw/workspace/skills/qimen-dunjia/scripts')
from engine import QimenEngine
from duanju import DuanjuEngine


class HeixiangFusion:
    """黑箱融合引擎——调用六爻+奇门，内部推理，外部只输出融合结果"""
    
    def __init__(self):
        self.liuyao_api = LiuyaoApi()
        self.qimen_engine = QimenEngine()
        self.duanju_engine = DuanjuEngine()
        self._last_raw = {}  # 内部存储原始结果（不对外暴露）
    
    def divine(self, question: str, dt: datetime = None) -> dict:
        """
        融合算事入口
        
        返回 dict:
          - question: 原始问题
          - agree: 两算法一致点（可靠）
          - differ: 两算法差异点（两种可能）
          - conclusion: 融合判词
          - raw_liuyao: 六爻原始数据（隐藏，仅开发模式可见）
          - raw_qimen: 奇门原始数据（隐藏，仅开发模式可见）
        """
        if dt is None:
            dt = datetime.now()
        
        self._dt = dt
        
        # 1. 六爻排盘
        liuyao = self._divine_liuyao(dt, question)
        
        # 2. 奇门排盘+解盘
        qimen = self._divine_qimen(dt.year, dt.month, dt.day, dt.hour, dt.minute, question)
        
        # 3. 融合推理
        fusion = self._fuse(question, liuyao, qimen)
        
        self._last_raw = {
            "question": question,
            "datetime": dt.isoformat(),
            "liuyao": liuyao,
            "qimen": qimen,
        }
        
        return fusion
    
    def _divine_liuyao(self, dt, question):
        """六爻排盘"""
        try:
            pan = self.liuyao_api.paipan(dt, qiguafangfa='标准时间起卦')
            # 传统分析
            from yxf_yixue.liuyao._fenxi import Chuantongfenxi
            cf = Chuantongfenxi()
            pan = cf.fenxi(pan)
            
            output = self.liuyao_api.P.output()
            
            # 提取卦象关键信息
            bengua_name = pan['盘']['10']['六十四卦']
            biangua_name = pan['盘'].get('20', {}).get('六十四卦', '')
            bengua_gong = pan['盘']['10']['卦宫']
            biangua_gong = pan['盘'].get('20', {}).get('卦宫', '')
            
            # 动爻
            dongyao_indices = pan.get('动爻', [])
            dongyao_info = []
            for idx in dongyao_indices:
                yi_key = f'1{idx}'
                if yi_key in pan['盘']:
                    d = pan['盘'][yi_key]
                    dongyao_info.append({
                        '爻位': idx,
                        '六亲': d.get('六亲', ''),
                        '纳支': d.get('纳支', ''),
                        '五行': d.get('五行', ''),
                    })
            
            # 世应
            shi_yao = ying_yao = None
            for k in pan['盘']:
                v = pan['盘'][k]
                if k.startswith('1') and v.get('世应') == '世':
                    shi_yao = {'爻位': k[1:], '六亲': v.get('六亲', ''), '纳支': v.get('纳支', ''), '五行': v.get('五行', '')}
                if k.startswith('1') and v.get('世应') == '应':
                    ying_yao = {'爻位': k[1:], '六亲': v.get('六亲', ''), '纳支': v.get('纳支', ''), '五行': v.get('五行', '')}
            
            # 四柱
            ganzhi = pan.get('干支', {})
            ri_zhu = ganzhi.get('日柱', '')
            ri_gan = ri_zhu[0] if ri_zhu else ''
            ri_zhi = ri_zhu[1] if ri_zhu else ''
            
            # 日空亡
            ri_kong = ganzhi.get('四柱空亡', [])[2] if len(ganzhi.get('四柱空亡', [])) > 2 else ''
            
            return {
                '本卦': bengua_name,
                '变卦': biangua_name,
                '本卦宫': bengua_gong,
                '变卦宫': biangua_gong,
                '动爻': dongyao_info,
                '世爻': shi_yao,
                '应爻': ying_yao,
                '日柱': ri_zhu,
                '日空亡': ri_kong,
                '输出': output,
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _divine_qimen(self, y, m, d, h, mi, question):
        """奇门排盘+解盘"""
        try:
            pan = self.qimen_engine.paipan(y, m, d, h, mi)
            report = self.duanju_engine.duanju(pan, question)
            
            # 提取关键信息
            jushu = pan.jushu
            sizhu = pan.sizhu
            zhifu = pan.zhifu_zhishi
            xunshou = pan.xunshou
            
            key = {
                '局数': f"{'阳' if jushu.yin_yang == '阳' else '阴'}遁{jushu.ju_num}局",
                '节气': f"{jushu.jieqi}{jushu.yuan}",
                '四柱': f"{sizhu.year_gan}{sizhu.year_zhi} {sizhu.month_gan}{sizhu.month_zhi} {sizhu.day_gan}{sizhu.day_zhi} {sizhu.hour_gan}{sizhu.hour_zhi}",
                '值符': f"{zhifu.zhifu_xing}(落{zhifu.zhifu_luo_gong}宫)",
                '值使': f"{zhifu.zhishi_men}(落{zhifu.zhishi_luo_gong}宫)",
                '空亡': '、'.join(xunshou.kong_zhi) if xunshou.kong_zhi else '',
                '用神定位': report.get('用神定位', {}),
                '格局分析': report.get('格局分析', []),
                '特殊状态': report.get('特殊状态', []),
                '综合结论': report.get('综合结论', ''),
            }
            return key
        except Exception as e:
            return {'error': str(e)}
    
    def _fuse(self, question, liuyao, qimen):
        """融合两种算法的结果"""
        agree = []
        differ = []
        
        # 1. 综合吉凶
        ly_ji = self._liuyao_ji_xiong(liuyao)
        qm_ji = self._qimen_ji_xiong(qimen)
        
        if ly_ji and qm_ji and ly_ji['倾向'] == qm_ji['倾向']:
            agree.append({
                '维度': '总体吉凶',
                '结论': f"两法一致：{ly_ji['倾向']}。{ly_ji['理由']}",
                '置信度': '高',
            })
        elif ly_ji and qm_ji:
            differ.append({
                '维度': '总体吉凶',
                '六爻': ly_ji['倾向'],
                '奇门': qm_ji['倾向'],
                '说明': '两法各有侧重，需结合具体问事类型综合判断',
            })
        
        # 2. 问事专项融合
        spec = self._fuse_by_type(question, liuyao, qimen)
        agree.extend(spec.get('agree', []))
        differ.extend(spec.get('differ', []))
        
        return {
            'question': question,
            'agree': agree,
            'differ': differ,
            'conclusion': self._generate_conclusion(question, agree, differ, liuyao, qimen),
        }
    
    def _liuyao_ji_xiong(self, liuyao):
        """六爻吉凶判断"""
        if 'error' in liuyao:
            return None
        
        try:
            dongyao = liuyao.get('动爻', [])
            shi = liuyao.get('世爻', {})
            ying = liuyao.get('应爻', {})
            
            reasons = []
            ji_tendency = 0
            
            for d in dongyao:
                if d.get('六亲') in ('妻财', '子孙', '父母'):
                    ji_tendency += 1
                    reasons.append(f"{d['六亲']}发动")
                elif d.get('六亲') in ('兄弟', '官鬼'):
                    ji_tendency -= 1
                    reasons.append(f"{d['六亲']}动以克")
            
            if shi:
                if shi.get('六亲') in ('妻财', '子孙'):
                    ji_tendency += 0.5
                    reasons.append(f"世持{shi['六亲']}为吉")
                elif shi.get('六亲') in ('兄弟', '官鬼'):
                    ji_tendency -= 0.5
                    reasons.append(f"世持{shi['六亲']}不利")
            
            tendency = '吉' if ji_tendency > 0 else ('凶' if ji_tendency < 0 else '平')
            return {
                '倾向': tendency,
                '理由': '; '.join(reasons[:3]) if reasons else '卦象平稳',
                '分数': ji_tendency,
            }
        except:
            return None
    
    def _qimen_ji_xiong(self, qimen):
        """奇门吉凶判断"""
        if 'error' in qimen:
            return None
        
        try:
            gejus = qimen.get('格局分析', [])
            ji_count = sum(1 for g in gejus if g.get('吉凶', '') in ['吉', '大吉', '中上'])
            xiong_count = sum(1 for g in gejus if g.get('吉凶', '') in ['凶', '大凶', '中下'])
            
            tendency = '吉' if ji_count > xiong_count else ('凶' if xiong_count > ji_count else '平')
            return {
                '倾向': tendency,
                '理由': f"{ji_count}吉/{xiong_count}凶格局",
            }
        except:
            return None
    
    def _fuse_by_type(self, question, liuyao, qimen):
        """根据问事类型做专项融合"""
        agree = []
        differ = []
        
        # 寻物
        if any(kw in question for kw in ['丢', '寻物', '遗失']) or \
           (any(kw in question for kw in ['找不到', '不见了', '哪里', '在哪']) and 
            not any(kw in question for kw in ['工作', '面试', 'offer'])):
            
            qm_dir = self._qimen_find_direction(qimen)
            ly_dir = self._liuyao_find_direction(liuyao)
            
            if qm_dir and ly_dir and qm_dir == ly_dir:
                agree.append({
                    '维度': '物品寻找方向',
                    '结论': f"两法一致指向**{qm_dir}方**，建议优先在该方向搜寻",
                    '置信度': '高',
                })
            elif qm_dir or ly_dir:
                dirs = []
                if ly_dir: dirs.append(f"六爻指**{ly_dir}方**")
                if qm_dir: dirs.append(f"奇门指**{qm_dir}方**")
                differ.append({
                    '维度': '物品寻找方向',
                    '六爻': ly_dir or '未明确',
                    '奇门': qm_dir or '未明确',
                    '说明': '两个方向都建议查看，可先查六爻所指方向',
                })
            
            qm_kezhao = self._qimen_can_find(qimen)
            ly_kezhao = self._liuyao_can_find(liuyao)
            if qm_kezhao == ly_kezhao:
                if qm_kezhao is not None:
                    agree.append({
                        '维度': '能否找回',
                        '结论': '两法一致：**' + ('有希望找回' if qm_kezhao else '找回难度较大') + '**',
                        '置信度': '高',
                    })
            elif qm_kezhao is not None and ly_kezhao is not None:
                differ.append({
                    '维度': '能否找回',
                    '六爻': '希望较大' if ly_kezhao else '难度较大',
                    '奇门': '希望较大' if qm_kezhao else '难度较大',
                    '说明': '一法示有寻回之机，一法示阻力较大，综合判断存在可能但需克服困难',
                })
        
        return {'agree': agree, 'differ': differ}
    
    def _qimen_find_direction(self, qimen):
        if 'error' in qimen:
            return None
        import re
        conclusion = qimen.get('综合结论', '')
        for line in conclusion.split('\n'):
            m = re.search(r'(巽四|离九|坤二|震三|兑七|艮八|坎一|乾六)(?:宫)?.*?(\([^\)]*\))', line)
            if m:
                return m.group(0)
        for line in conclusion.split('\n'):
            m = re.search(r'落.*?(巽四|离九|坤二|震三|兑七|艮八|坎一|乾六)', line)
            if m:
                return m.group(0)
    
    def _liuyao_find_direction(self, liuyao):
        if 'error' in liuyao:
            return None
        ying = liuyao.get('应爻', {})
        if ying:
            zhi_to_dir = {
                '子': '北', '午': '南', '卯': '东', '酉': '西',
                '丑': '东北', '寅': '东北', '辰': '东南', '巳': '东南',
                '未': '西南', '申': '西南', '戌': '西北', '亥': '西北',
            }
            return zhi_to_dir.get(ying.get('纳支', '')[:1], None)
        return None
    
    def _qimen_can_find(self, qimen):
        if 'error' in qimen:
            return None
        conclusion = qimen.get('综合结论', '')
        if '寻回希望' in conclusion or '吉门' in conclusion:
            return True
        if '难寻' in conclusion or '凶' in conclusion:
            return False
        return None
    
    def _liuyao_can_find(self, liuyao):
        if 'error' in liuyao:
            return None
        shi = liuyao.get('世爻', {})
        ying = liuyao.get('应爻', {})
        if shi and ying:
            wuxing = shi.get('五行', '')
            ying_wx = ying.get('五行', '')
            if isinstance(wuxing, str) and isinstance(ying_wx, str):
                wuxing_ke = {'金': '木', '木': '土', '土': '水', '水': '火', '火': '金'}
                if wuxing and wuxing[0] in wuxing_ke:
                    ke = wuxing_ke[wuxing[0]]
                    if ke == ying_wx[0]:
                        return True
                return False
        return None
    
    def _generate_conclusion(self, question, agree, differ, liuyao, qimen):
        """生成融合结论"""
        conclusion = []
        
        if agree:
            conclusion.append("\n### 🎯 两法一致的判断")
            for a in agree:
                conclusion.append(f"- {a['维度']}：{a['结论']}")
        
        if differ:
            conclusion.append("\n### ⚖️ 两种算法各有侧重")
            for d in differ:
                conclusion.append(f"- **{d['维度']}**：")
                conclusion.append(f"  - 六爻显示：{d.get('六爻', '')}")
                conclusion.append(f"  - 奇门显示：{d.get('奇门', '')}")
                conclusion.append(f"  - 综合说明：{d.get('说明', '')}")
        
        if not agree and not differ:
            qm_conclusion = qimen.get('综合结论', '') if not isinstance(qimen.get('综合结论'), str) else qimen.get('综合结论', '')
            conclusion.append(qm_conclusion)
        
        return '\n'.join(conclusion)


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "寻物：我的钱包丢了能找到吗"
    dt = datetime.now()
    fusion = HeixiangFusion()
    result = fusion.divine(q, dt)
    print(json.dumps(result, ensure_ascii=False, indent=2))
