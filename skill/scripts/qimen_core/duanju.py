#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
奇门遁甲解盘引擎 v1.0
输入：盘面 JSON + 问事类型 → 输出：自然语言解盘报告
"""
import json, os, sys
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).parents[2] / "references" / "qimen"

def load_knowledge(name):
    with open(KNOWLEDGE_DIR / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)

class DuanjuEngine:
    """解盘主引擎"""

    def __init__(self):
        self.jiuxing = load_knowledge("jiuxing")
        self.bamen = load_knowledge("bamen")
        self.bashen = load_knowledge("bashen")
        self.geju = load_knowledge("geju")
        self.yongshen = load_knowledge("yongshen")
        self.shengke = load_knowledge("shengke_rules")
        self.xiangyi = load_knowledge("xiangyi_rules")

    def _get_yougshen_info(self, question_type):
        """智能用神定位 — 支持自由文本输入 + 别名映射"""
        yt = self.yongshen.get("问事类型", {})
        if not yt:
            yt = self.yongshen.get("问事用神表", {})
        
        # yongshen.json 的 key 别名映射表
        ALIAS_MAP = {
            "婚姻": "婚姻（男问女）",  # 默认男问
            "感情": "婚姻（男问女）",
            "恋爱": "婚姻（男问女）",
            "合作": "合作签约",
            "合伙": "合作签约",
            "投资": "投资置业",
            "身体": "疾病",
            "健康": "疾病",
            "不适": "疾病",
            "面试": "事业",
            "工作": "事业",
            "跳槽": "事业",
            "offer": "事业",
            "考研": "考试",
            "考公": "考试",
            "考证": "考试",
        }
        
        # 关键词匹配规则（自由文本智能识别）
        KEYWORD_MAP = {
            "寻物": ["丢", "找不到", "遗失", "哪", "方向", "找", "卡", "物", "证件"],
            "婚姻": ["感情", "恋爱", "结婚", "对象", "分手", "相亲", "老公", "老婆", "男女", "男朋友", "女朋友", "在一起", "吵架", "冷战"],
            "事业": ["工作", "职场", "升职", "面试", "offer", "老板", "同事", "跳槽", "职业", "转行"],
            "考试": ["考试", "考", "成绩", "复习", "学习", "考研", "考公", "证书"],
            "求财": ["钱", "财", "赚", "收入", "工资", "奖金", "股票", "基金", "理财", "发财"],
            "出行": ["出行", "旅游", "出差", "旅行", "飞机", "火车", "交通"],
            "合作": ["合作", "合伙", "签约", "合同", "协议", "搭档", "开店", "创业", "一起"],
            "投资": ["投资", "项目", "收益", "回报", "风险", "买", "炒股"],
            "疾病": ["病", "健康", "身体", "不适", "医院", "手术", "恢复", "疼"],
            "官司": ["官司", "法律", "诉讼", "纠纷", "仲裁", "起诉"],
        }
        
        # 先尝试精确匹配
        info = yt.get(question_type, {})
        if info:
            if "：" in question_type:
                parts = question_type.split("：", 1)
                type_name = parts[0]
                actual_key = ALIAS_MAP.get(type_name, type_name)
                info = yt.get(actual_key, info)
            return info
        
        # 关键词匹配
        best_type = None
        best_score = 0
        for type_name, keywords in KEYWORD_MAP.items():
            score = sum(1 for kw in keywords if kw in question_type)
            if score > best_score:
                best_score = score
                best_type = type_name
        
        # 有"："分隔的格式，优先取前缀
        if "：" in question_type:
            parts = question_type.split("：", 1)
            type_name = parts[0]
            kw_score = sum(1 for kw in KEYWORD_MAP.get(type_name, []) if kw in question_type)
            if kw_score > 0:
                best_type = type_name
        
        # 别名映射到 yongshen.json 实际 key
        if best_type:
            actual_key = ALIAS_MAP.get(best_type, best_type)
            info = yt.get(actual_key, yt.get(best_type, {}))
        
        return info

    def _find_gong_by_gan(self, pan, gan):
        """根据天干找宫位"""
        for gong_id, gong in pan["gongs"].items():
            if gong["天盘干"] == gan or gong["天盘干"] == gan:
                return gong_id, gong
            if gong["地盘干"] == gan:
                return gong_id, gong
        return None, None

    def _find_gong_by_men(self, pan, men_name):
        """根据八门找宫位"""
        for gong_id, gong in pan["gongs"].items():
            if gong["八门"] == men_name:
                return gong_id, gong
        return None, None

    def _find_gong_by_star(self, pan, star_name):
        """根据九星找宫位"""
        for gong_id, gong in pan["gongs"].items():
            if gong["九星"] == star_name:
                return gong_id, gong
        return None, None

    def _check_menpo(self, gong):
        """门迫检测"""
        if not gong.get("门迫"):
            return None
        men = gong["八门"]
        men_wx = self.bamen.get("八门五行", {}).get(men, "")
        gong_wx = gong["五行"]
        wx_ke = self.shengke.get("五行相克", {}).get("关系", self.shengke.get("五行相克", {}))
        if men_wx and gong_wx and gong_wx in wx_ke.get(men_wx, []):
            return f"{men}({men_wx})受宫({gong_wx})克，门迫——能量受压制"
        return None

    def _check_kongwang(self, gong):
        """空亡检查"""
        if gong.get("空亡"):
            return "空亡——事有虚象，宜待填实"
        return None

    def _analyze_geju(self, pan):
        """格局分析——十干克应"""
        results = []
        shigan_ke = self.geju.get("十干克应", {})
        for gong_id, gong in pan["gongs"].items():
            if gong_id == "5":
                continue
            tgan = gong.get("天盘干", "")
            dgan = gong.get("地盘干", "")
            if not tgan or not dgan:
                continue
            key = f"{tgan}+{dgan}"
            geju_info = shigan_ke.get(key, {})
            if geju_info:
                results.append({
                    "宫位": gong["宫名"],
                    "宫号": int(gong_id),
                    "组合": key,
                    "格局名": geju_info.get("格局名", ""),
                    "吉凶": geju_info.get("吉凶", "中"),
                    "含义": geju_info.get("含义", ""),
                    "天盘干": tgan,
                    "地盘干": dgan,
                    "八门": gong["八门"],
                    "九星": gong["九星"],
                    "八神": gong["八神"],
                })
        return results

    def _check_classic_dun(self, pan):
        """检查经典遁格"""
        results = []
        dun_jing = self.geju.get("经典遁格", {})
        for dun_name, dun_info in dun_jing.items():
            cond = dun_info.get("条件表达式", {})
            # 简单匹配
            found = False
            for gong_id, gong in pan["gongs"].items():
                if gong_id == "5":
                    continue
                matches = 0
                total = 0
                if "天盘干" in cond:
                    total += 1
                    if gong["天盘干"] == cond["天盘干"]:
                        matches += 1
                if "地盘干" in cond:
                    total += 1
                    if gong["地盘干"] == cond["地盘干"]:
                        matches += 1
                if "八门" in cond:
                    total += 1
                    if gong["八门"] == cond["八门"]:
                        matches += 1
                if total > 0 and matches == total:
                    results.append({
                        "遁格": dun_name,
                        "宫位": f"{gong['宫名']}({gong['八门']})",
                        "含义": dun_info.get("含义", ""),
                        "适用": dun_info.get("适用", ""),
                        "吉凶": dun_info.get("吉凶", "吉"),
                    })
                    found = True
                    break
        return results

    def _analyze_special_state(self, pan):
        """特殊状态分析"""
        states = []
        for gong_id, gong in pan["gongs"].items():
            if gong_id == "5":
                continue
            issues = []
            mp = self._check_menpo(gong)
            kw = self._check_kongwang(gong)
            if mp:
                issues.append(mp)
            if kw:
                issues.append(kw)
            if gong.get("反吟"):
                issues.append("反吟——事态反复，宜静不宜动")
            if gong.get("伏吟"):
                issues.append("伏吟——事态停滞，待时而动")
            if issues:
                states.append({
                    "宫位": gong["宫名"],
                    "宫号": int(gong_id),
                    "问题": issues,
                })
        return states

    def _shengke_analysis(self, pan, yongshen_info):
        """五行生克关系分析"""
        wx_sheng = self.shengke.get("五行相生", {}).get("关系", self.shengke.get("五行相生", {}))
        wx_ke = self.shengke.get("五行相克", {}).get("关系", self.shengke.get("五行相克", {}))
        gong_wx_map = self.shengke.get("宫位五行", {})

        analysis = []
        # 日干落宫 vs 时干落宫 关系
        ri_gan = pan["sizhu"]["日柱"]
        shi_zhu = pan["sizhu"]["时柱"]

        ri_gong = None
        shi_gong = None
        for gong_id, gong in pan["gongs"].items():
            if gong_id == "5":
                continue
            if gong["天盘干"] == ri_gan[0] or gong["地盘干"] == ri_gan[0]:
                ri_gong = (gong_id, gong)
            if gong["天盘干"] == shi_zhu[0] or gong["地盘干"] == shi_zhu[0]:
                shi_gong = (gong_id, gong)

        if ri_gong and shi_gong:
            _, ri = ri_gong
            _, shi = shi_gong
            ri_wx_info = gong_wx_map.get(str(ri_gong[0]), ri["五行"])
            shi_wx_info = gong_wx_map.get(str(shi_gong[0]), shi["五行"])
            ri_wx = ri_wx_info.get("五行", ri["五行"]) if isinstance(ri_wx_info, dict) else ri_wx_info
            shi_wx = shi_wx_info.get("五行", shi["五行"]) if isinstance(shi_wx_info, dict) else shi_wx_info

            if wx_sheng.get(shi_wx) == ri_wx:
                analysis.append(f"日干落{ri['宫名']}({ri_wx})，时干落{shi['宫名']}({shi_wx})，时干生日干——所问之事对己有利")
            elif wx_ke.get(shi_wx) == ri_wx:
                analysis.append(f"日干落{ri['宫名']}({ri_wx})，时干落{shi['宫名']}({shi_wx})，时干克日干——所问之事对己不利⚠️")
            elif wx_sheng.get(ri_wx) == shi_wx:
                analysis.append(f"日干落{ri['宫名']}({ri_wx})，时干落{shi['宫名']}({shi_wx})，日干生时干——需耗力付出")
            elif wx_ke.get(ri_wx) == shi_wx:
                analysis.append(f"日干落{ri['宫名']}({ri_wx})，时干落{shi['宫名']}({shi_wx})，日干克时干——能掌控局势")
            else:
                analysis.append(f"日干落{ri['宫名']}({ri_wx})，时干落{shi['宫名']}({shi_wx})，比和——事态平稳")

        return analysis

    def _xiangyi_deep_analysis(self, pan, yongshen_gong_ids):
        """象意深层解析"""
        results = []
        for gong_id in yongshen_gong_ids:
            gong = pan["gongs"].get(str(gong_id))
            if not gong or gong_id == 5:
                continue

            info = {
                "宫位": gong["宫名"],
                "方位": gong["方位"],
                "五行": gong["五行"],
                "八门": gong["八门"],
                "九星": gong["九星"],
                "八神": gong["八神"],
                "天盘干": gong["天盘干"],
                "地盘干": gong["地盘干"],
            }

            # 门象意
            men_data = self.bamen.get("八门", {}).get(gong["八门"], {})
            info["门象意"] = men_data.get("象意", [])[:5]

            # 星象意
            star_data = self.jiuxing.get("九星", {}).get(gong["九星"], {})
            info["星象意"] = star_data.get("象意", [])[:5]

            # 神象意
            shen_data = self.bashen.get("八神", {}).get(gong["八神"], {})
            info["神象意"] = shen_data.get("象意", [])[:5]

            # 格局提示
            t_d = f"{gong['天盘干']}+{gong['地盘干']}"
            info["格局提示"] = self.geju.get("十干克应", {}).get(t_d, {}).get("含义", "")

            # 门迫/空亡 状态
            info["状态"] = []
            if gong.get("门迫"):
                info["状态"].append("门迫")
            if gong.get("空亡"):
                info["状态"].append("空亡")
            if gong.get("反吟"):
                info["状态"].append("反吟")

            results.append(info)
        return results

    def _generate_conclusion(self, pan, question_type, geju_list, dun_list, shengke_list, special_states):
        """综合结论生成"""
        conclusions = []

        # 1. 总体吉凶倾向
        ji_count = sum(1 for g in geju_list if g["吉凶"] in ["吉", "大吉", "中上"])
        xiong_count = sum(1 for g in geju_list if g["吉凶"] in ["凶", "大凶", "中下"])
        total_geju = len(geju_list)

        if dun_list:
            conclusions.append(f"盘见**{', '.join(d['遁格'] for d in dun_list)}**，为经典吉格。")

        if ji_count > xiong_count:
            conclusions.append(f"整体格局偏吉（{ji_count}吉/{xiong_count}凶），事有可为之机。")
        elif xiong_count > ji_count:
            conclusions.append(f"整体格局偏凶（{xiong_count}凶/{ji_count}吉），需审慎行事。")
        else:
            conclusions.append("格局吉凶参半，需看具体宫位定夺。")

        # 2. 空亡警告
        kong_gongs = [s for s in special_states if any("空亡" in issue for issue in s.get("问题", []))]
        if kong_gongs:
            conclusions.append(f"⚠️ {', '.join(s['宫位'] for s in kong_gongs)}逢空亡，相关事宜有虚象、推迟之兆。")

        # 3. 门迫警告
        menpo_gongs = [s for s in special_states if any("门迫" in issue for issue in s.get("问题", []))]
        if menpo_gongs:
            conclusions.append(f"⚠️ {', '.join(s['宫位'] for s in menpo_gongs)}门迫，能量受制，需调方向或待时机。")

        # 4. 特殊状态
        for s in special_states:
            if any("反吟" in issue for issue in s.get("问题", [])):
                conclusions.append(f"⚠️ {s['宫位']}反吟，事态反复，不宜激进。")
            if any("伏吟" in issue for issue in s.get("问题", [])):
                conclusions.append(f"⚠️ {s['宫位']}伏吟，事态停滞，需外力推动。")

        # 5. 生克
        if shengke_list:
            conclusions.append("\n".join(shengke_list))

        # 6. 值符值使
        zfz = pan.get("zhifu_zhishi", {})
        zf_xing = zfz.get('zhifu_xing', '')
        zs_men = zfz.get('zhishi_men', '')
        conclusions.append(f"值符{zf_xing}临，主事有主导之势。值使{zs_men}临，行动方向已显。")

        # 7. 针对具体问题的个性化建议
        q_lower = question_type
        if "：" in question_type:
            q_lower = question_type.split("：", 1)[1] if question_type.split("：", 1)[0] in ("寻物", "事业", "求财", "婚姻", "考试", "出行", "合作", "投资", "健康", "官司") else question_type
        
        if "寻物" in question_type or "丢" in question_type or "找" in question_type or "遗失" in question_type:
            # 寻物专项分析
            shi_gan_gong = None
            for gong_id, gong in pan['gongs'].items():
                if gong['天盘干'] == pan['sizhu']['时柱'][0] or gong['地盘干'] == pan['sizhu']['时柱'][0]:
                    shi_gan_gong = (gong_id, gong)
                    break
            if shi_gan_gong:
                gid, gong = shi_gan_gong
                fw = gong['方位']
                conclusions.append(f"时干落{gong['宫名']}({fw})，物品可能在{gong['宫名']}方向。")
                if gong['空亡']:
                    conclusions.append(f"时干宫逢空亡，物品暂时难以寻回，待空亡填实（相关月份）或有转机。")
                elif gong['八门'] in ("死门", "惊门"):
                    conclusions.append(f"时干宫逢{gong['八门']}，寻回难度较大，可能已被转移或深度隐藏。")
                elif gong['八门'] in ("生门", "开门", "休门"):
                    conclusions.append(f"时干宫逢{gong['八门']}吉门，物品尚在，有寻回希望，宜抓紧查找。")
        
        elif "事业" in question_type or "工作" in question_type or "面试" in question_type or "offer" in question_type.lower():
            kaimen_gong = None
            for gong_id, gong in pan['gongs'].items():
                if gong['八门'] == '开门':
                    kaimen_gong = (gong_id, gong)
                    break
            if kaimen_gong:
                gid, gong = kaimen_gong
                if gong['空亡']:
                    conclusions.append(f"开门（事业）落{gong['宫名']}逢空亡，当前时机未到，宜等待。")
                elif gong['九星'] in ("天辅", "天心", "天禽"):
                    conclusions.append(f"开门临{gong['九星']}吉星，事业有贵人相助，发展向好。")
                else:
                    conclusions.append(f"开门落{gong['宫名']}临{gong['九星']}，事业需主动争取，不宜守株待兔。")
        
        elif "求财" in question_type or "钱" in question_type or "财" in question_type:
            shengmen_gong = None
            for gong_id, gong in pan['gongs'].items():
                if gong['八门'] == '生门':
                    shengmen_gong = (gong_id, gong)
                    break
            if shengmen_gong:
                gid, gong = shengmen_gong
                if gong['空亡']:
                    conclusions.append(f"生门（财运）落{gong['宫名']}逢空亡，财来财去，宜守不宜攻。")
                elif gong['八神'] in ("值符", "太阴", "六合"):
                    conclusions.append(f"生门临{gong['八神']}吉神，财运有护，可适当进取。")
                else:
                    conclusions.append(f"生门落{gong['宫名']}，财运平稳，注意开源节流。")
        elif "婚姻" in question_type or "感情" in question_type or "恋爱" in question_type:
            liuhe_gong = None
            for gong_id, gong in pan['gongs'].items():
                if gong['八神'] == '六合':
                    liuhe_gong = (gong_id, gong)
                    break
            if liuhe_gong:
                gid, gong = liuhe_gong
                if gong['空亡']:
                    conclusions.append(f"六合（姻缘）落{gong['宫名']}逢空亡，感情关系可能有虚象，需更多沟通。")
                elif gong['八门'] in ("休门", "开门", "生门"):
                    conclusions.append(f"六合临{gong['八门']}吉门，感情和睦，关系稳定。")
                else:
                    conclusions.append(f"六合落{gong['宫名']}，感情需用心经营，不宜急躁。")
        elif "考试" in question_type or "考" in question_type or "成绩" in question_type:
            jingmen_gong = None
            for gong_id, gong in pan['gongs'].items():
                if gong['八门'] == '景门':
                    jingmen_gong = (gong_id, gong)
                    break
            if jingmen_gong:
                gid, gong = jingmen_gong
                if gong['空亡']:
                    conclusions.append(f"景门（考试）落{gong['宫名']}逢空亡，成绩可能不如预期，或放榜时间推迟。")
                elif gong['九星'] in ("天辅", "天心", "天禽"):
                    conclusions.append(f"景门临{gong['九星']}文昌星，学业运佳，考试有望取得好成绩。")
                else:
                    conclusions.append(f"景门落{gong['宫名']}，考试结果与付出相当，稳扎稳打方有收获。")
        elif "健康" in question_type or "病" in question_type or "身体" in question_type:
            simen_gong = None
            for gong_id, gong in pan['gongs'].items():
                if gong['八门'] == '死门':
                    simen_gong = (gong_id, gong)
                    break
            if simen_gong:
                gid, gong = simen_gong
                if gong['空亡']:
                    conclusions.append(f"死门空亡则病象减轻，是好转之兆。")
                elif gong['九星'] in ("天芮", "天柱"):
                    conclusions.append(f"病星临{gong['九星']}重要，健康需重视，建议及时就医检查。")
                else:
                    conclusions.append(f"死门落{gong['宫名']}，健康状况总体可控，但勿掉以轻心。")
        elif "官司" in question_type or "法律" in question_type or "诉讼" in question_type:
            jingmen_gong = None
            for gong_id, gong in pan['gongs'].items():
                if gong['八门'] == '惊门':
                    jingmen_gong = (gong_id, gong)
                    break
            if jingmen_gong:
                gid, gong = jingmen_gong
                if gong['空亡']:
                    conclusions.append(f"惊门（官司）落{gong['宫名']}逢空亡，诉讼可能有转机或和解。")
                elif gong['八神'] in ("值符", "六合", "太阴"):
                    conclusions.append(f"惊门临{gong['八神']}，官司有望得到公正裁决或贵人相助。")
                else:
                    conclusions.append(f"惊门落{gong['宫名']}临{gong['九星']}，官司宜从速处理，不宜久拖。")
        elif "出行" in question_type or "旅游" in question_type or "旅行" in question_type:
            zhishimen = zfz.get('zhishi_men', '')
            zhishi_luo = zfz.get('zhishi_luo_gong', 0)
            if zhishi_luo:
                gong = pan['gongs'].get(str(zhishi_luo), {})
                if gong:
                    if gong.get('空亡'):
                        conclusions.append(f"值使{zhishimen}落空亡，出行可能有变数或延期，宜计划周密。")
                    elif gong['八门'] in ("开门", "休门", "生门"):
                        conclusions.append(f"值使{zhishimen}临{gong['八门']}吉门，出行顺利，旅途愉快。")
                    else:
                        conclusions.append(f"值使{zhishimen}落{gong['宫名']}，出行需注意安全，做好准备。")
        elif "合作" in question_type or "合伙" in question_type or "签约" in question_type:
            liuhe_gong = None
            for gong_id, gong in pan['gongs'].items():
                if gong['八神'] == '六合':
                    liuhe_gong = (gong_id, gong)
                    break
            if liuhe_gong:
                gid, gong = liuhe_gong
                if gong['空亡']:
                    conclusions.append(f"六合（合作）落{gong['宫名']}逢空亡，合作可能有变数或不实之约，需审慎判断。")
                elif gong['八门'] in ("开门", "休门", "生门"):
                    conclusions.append(f"六合临{gong['八门']}吉门，合作前景良好，可放心推进。")
                else:
                    conclusions.append(f"六合落{gong['宫名']}，合作协议宜白纸黑字，忌口头约定。")

        return "\n\n".join(f"• {c}" if not c.startswith("⚠️") else f"🔴 {c}" for c in conclusions)

    @staticmethod
    def _ensure_dict(pan):
        """兼容 dataclass 和 dict"""
        if hasattr(pan, 'gongs'):
            from dataclasses import asdict
            raw = asdict(pan)
        else:
            raw = pan
            # 已经是 dict，看看是不是需要映射
            if 'sizhu' in raw and '年柱' in raw.get('sizhu', {}):
                return raw  # 已映射过
        
        # 映射到中文键名
        s = raw.get('sizhu', {})
        z = raw.get('zhifu_zhishi', {})
        x = raw.get('xunshou', {})
        j = raw.get('jushu', {})
        
        return {
            'meta': {'input_time': raw.get('input_time', '').isoformat() if hasattr(raw.get('input_time', ''), 'isoformat') else raw.get('input_time', '')},
            'sizhu': {
                '年柱': s['year_gan'] + s['year_zhi'],
                '月柱': s['month_gan'] + s['month_zhi'],
                '日柱': s['day_gan'] + s['day_zhi'],
                '时柱': s['hour_gan'] + s['hour_zhi'],
            },
            'jushu': {
                '局数': j.get('ju_num', 0),
                '阴阳遁': j.get('yin_yang', ''),
                '节气': j.get('jieqi', ''),
                '计算方法': j.get('method', '拆补'),
                '元': j.get('yuan', ''),
            },
            'zhifu_zhishi': z,
            'xunshou': {
                '旬首': x.get('xunshou', ''),
                '隐仪': x.get('yinyi', ''),
                '空亡地支': x.get('kong_zhi', []),
                '空亡宫位': x.get('kong_gong', []),
                '马星': x.get('masa', ''),
            },
            'gongs': {
                str(k): {
                    '宫名': v['gong_name'],
                    '方位': v['fangwei'],
                    '五行': v['wuxing'],
                    '天盘干': v['tianpan_gan'],
                    '地盘干': v['dipan_gan'],
                    '九星': v['jiuxing'],
                    '八门': v['bamen'],
                    '八神': v['bashen'],
                    '空亡': v['is_kong'],
                    '门迫': v['men_po'],
                    '反吟': v['fan_yin'],
                    '伏吟': v['fu_yin'],
                    '格局': v['geju'],
                } for k, v in raw.get('gongs', {}).items() if k != 5
            },
        }

    def duanju(self, pan, question="综合", birth_year=None) -> dict:
        """
        主解盘方法
        
        Args:
            pan: 排盘 JSON（PanResult dataclass 或 dict）
            question: 所问之事
            birth_year: 出生年份（可选）
        
        Returns:
            解盘报告 dict
        """
        pan = self._ensure_dict(pan)
        # 统一 gongs key 为 string
        if pan.get('gongs'):
            pan['gongs'] = {str(k): v for k, v in pan['gongs'].items()}
        
        # Step 1: 用神定位
        yongshen = self._get_yougshen_info(question)
        main_men = yongshen.get("主用神", [])
        aux_men = yongshen.get("辅助用神", [])
        kan_gong_wei = yongshen.get("看宫位", "")
        judge_points = yongshen.get("判断要点", "")

        # Step 2: 格局分析
        geju_list = self._analyze_geju(pan)

        # Step 3: 经典遁格检测
        dun_list = self._check_classic_dun(pan)

        # Step 4: 五行生克
        shengke_list = self._shengke_analysis(pan, yongshen)

        # Step 5: 特殊状态
        special_states = self._analyze_special_state(pan)

        # Step 6: 用神宫位象意
        yongshen_gong_ids = []
        for gong_id, gong in pan["gongs"].items():
            if gong_id == "5":
                continue
            # 主用神宫位
            if main_men and gong["八门"] in main_men:
                yongshen_gong_ids.append(int(gong_id))
            if str(gong_id) == kan_gong_wei:
                if int(gong_id) not in yongshen_gong_ids:
                    yongshen_gong_ids.append(int(gong_id))

        if yongshen_gong_ids:
            xiangyi_result = self._xiangyi_deep_analysis(pan, yongshen_gong_ids)
        else:
            xiangyi_result = []

        # Step 7: 综合结论
        conclusion = self._generate_conclusion(pan, question, geju_list, dun_list, shengke_list, special_states)

        report = {
            "meta": {
                "engine": "qimen-duanju",
                "version": "2.0.0",
                "question": question,
                "birth_year": birth_year,
            },
            "盘面摘要": {
                "时间": pan["meta"]["input_time"],
                "局数": f"{pan['jushu']['阴阳遁']}{pan['jushu']['局数']}局 · {pan['jushu']['节气']}{pan['jushu']['元']}",
                "四柱": f"{pan['sizhu']['年柱']} {pan['sizhu']['月柱']} {pan['sizhu']['日柱']} {pan['sizhu']['时柱']}",
                "值符值使": f"{pan['zhifu_zhishi'].get('zhifu_xing','')} / {pan['zhifu_zhishi'].get('zhishi_men','')}",
                "空亡": f"{'、'.join(pan['xunshou']['空亡地支'])}",
            },
            "用神定位": {
                "问事类型": question,
                "主用神": main_men,
                "辅助用神": aux_men,
                "看宫位": kan_gong_wei,
                "判断要点": judge_points,
            },
            "格局分析": geju_list,
            "经典遁格": dun_list,
            "五行生克": shengke_list,
            "特殊状态": special_states,
            "用神宫位象意": xiangyi_result,
            "综合结论": conclusion,
        }

        return report

    def duanju_text(self, pan, question="综合", birth_year=None):
        """返回自然语言解盘报告"""
        pan = self._ensure_dict(pan)
        if pan.get('gongs'):
            pan['gongs'] = {str(k): v for k, v in pan['gongs'].items()}
        report = self.duanju(pan, question, birth_year)

        lines = []
        lines.append("═" * 50)
        lines.append("   🔮 奇门遁甲解盘报告")
        lines.append("═" * 50)
        lines.append("")

        # 盘面摘要
        s = report["盘面摘要"]
        lines.append(f"📅 {s['时间']}")
        lines.append(f"🏛️ {s['局数']} · 四柱：{s['四柱']}")
        lines.append(f"🎯 值符：{s['值符值使']} · 空亡：{s['空亡']}")
        lines.append("")

        # 用神
        y = report["用神定位"]
        lines.append("─" * 40)
        lines.append(f"📍 用神定位 | 问：{y['问事类型']}")
        lines.append(f"   主用神：{', '.join(y['主用神']) if y['主用神'] else '日干(综合)'}")
        if y.get('辅助用神'):
            lines.append(f"   辅助：{', '.join(y['辅助用神'])}")
        lines.append(f"   关注宫位：{y.get('看宫位','全盘')}")
        lines.append(f"   判断要点：{y.get('判断要点','综合判断')}")
        lines.append("")

        # 经典遁格
        if report["经典遁格"]:
            lines.append("─" * 40)
            lines.append("🌟 经典遁格")
            for d in report["经典遁格"]:
                lines.append(f"   {d['宫位']} {d['遁格']}（{d['吉凶']}）{d['含义']}")
            lines.append("")

        # 格局分析摘要
        if report["格局分析"]:
            lines.append("─" * 40)
            lines.append("📊 主要格局")
            for g in report["格局分析"][:8]:
                ji_xiong = "🟢" if g["吉凶"] in ["吉", "大吉"] else "🔴" if g["吉凶"] in ["凶", "大凶"] else "🟡"
                lines.append(f"   {ji_xiong} {g['宫位']} {g['组合']} {g['格局名']}")
            lines.append("")

        # 象意
        if report["用神宫位象意"]:
            lines.append("─" * 40)
            lines.append("🔍 关键宫位象意")
            for x in report["用神宫位象意"]:
                lines.append(f"  【{x['宫位']}】{x['八门']}·{x['九星']}·{x['八神']}")
                if x.get("门象意"):
                    lines.append(f"    门：{', '.join(x['门象意'][:3])}")
                if x.get("星象意"):
                    lines.append(f"    星：{', '.join(x['星象意'][:3])}")
                if x.get("神象意"):
                    lines.append(f"    神：{', '.join(x['神象意'][:3])}")
                if x.get("格局提示"):
                    lines.append(f"    格局：{x['格局提示']}")
                if x.get("状态"):
                    lines.append(f"    状态：{', '.join(x['状态'])}")
                lines.append("")

        # 特殊状态
        if report["特殊状态"]:
            lines.append("─" * 40)
            lines.append("⚠️ 特殊状态")
            for s in report["特殊状态"]:
                for issue in s["问题"]:
                    prefix = "🔴 " if "空亡" in issue or "门迫" in issue or "大凶" in issue else "🟡 "
                    lines.append(f"   {prefix}{s['宫位']}: {issue}")
            lines.append("")

        # 生克
        if report["五行生克"]:
            lines.append("─" * 40)
            lines.append("🔥 五行生克")
            for sk in report["五行生克"]:
                lines.append(f"   {sk}")
            lines.append("")

        # 综合结论
        lines.append("─" * 40)
        lines.append("📝 综合结论")
        lines.append(report["综合结论"])
        lines.append("")
        lines.append("─" * 40)
        lines.append("⚠️ 以上分析仅供研究和娱乐参考，重大决策请综合现实信息。")

        return "\n".join(lines)


# CLI
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="奇门遁甲解盘引擎")
    parser.add_argument("--json", type=str, help="盘面 JSON 文件路径")
    parser.add_argument("--question", type=str, default="综合", help="所问之事")
    parser.add_argument("--birth", type=int, help="出生年份")
    args = parser.parse_args()

    if args.json:
        with open(args.json) as f:
            pan = json.load(f)
    else:
        # 用当前时间排盘
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from engine import QimenEngine
        from datetime import datetime
        now = datetime.now()
        pan = QimenEngine().paipan(now.year, now.month, now.day, now.hour, now.minute)

    engine = DuanjuEngine()
    print(engine.duanju_text(pan, args.question, args.birth))
