#!/usr/bin/env node
/**
 * validate-liuyao-qimen-consultation.cjs
 * =====================================
 * V2.0 六爻+奇门融合结果校验脚本
 * 
 * 用法:
 *   node scripts/validate-liuyao-qimen-consultation.cjs --fusion=fusion.json
 *   node scripts/validate-liuyao-qimen-consultation.cjs --fusion=fusion.json --response=response.txt
 */

const fs = require('fs');
const path = require('path');

// ─── 参数解析（支持 --flag=value 和 --flag value 两种格式）───
const args = process.argv.slice(2);
function getArg(name) {
  for (const a of args) {
    if (a.startsWith(name + '=')) return a.slice(name.length + 1);
  }
  const idx = args.indexOf(name);
  return idx >= 0 ? args[idx + 1] : null;
}

const fusionPath = getArg('--fusion');
const responsePath = getArg('--response');
const roundMetaPath = getArg('--roundMeta');

if (!fusionPath) {
  console.error('用法: node validate-liuyao-qimen-consultation.cjs --fusion=fusion.json --response=response.txt [--roundMeta=meta.json]');
  process.exit(2);
}

// V5: 强制要求 --response（词表要生效，答复必须被扫描；缺失即 FAIL，不再静默跳过）
if (!responsePath) {
  console.error('[FAIL] 缺少 --response 参数。V5 起强制扫描答复文本，请传入 response.txt');
  process.exit(1);
}

// ─── 加载数据 ───
let fusion;
try {
  fusion = JSON.parse(fs.readFileSync(fusionPath, 'utf-8'));
} catch (e) {
  console.error(`无法读取 fusion 文件: ${e.message}`);
  process.exit(1);
}

let response = '';
if (responsePath) {
  try {
    response = fs.readFileSync(responsePath, 'utf-8');
  } catch (e) {
    // 可选，忽略
  }
}

const errors = [];
const warnings = [];

// ─── 1. Schema 版本检查 ───
if (fusion.schemaVersion !== 'aceworld-liuyao-qimen-fusion.v2') {
  errors.push(`schemaVersion: 预期 aceworld-liuyao-qimen-fusion.v2, 实际 ${fusion.schemaVersion}`);
}

// ─── 2. 必需字段检查 ───
const required = ['schemaVersion', 'stage', 'question', 'methods', 'agreement', 'conclusions', 'diagram'];
for (const f of required) {
  if (!(f in fusion)) {
    errors.push(`缺少必需字段: ${f}`);
  }
}

if (fusion.question) {
  if (!fusion.question.text) errors.push('question.text 不能为空');
  if (!fusion.question.category) warnings.push('question.category 未填写');
}

if (fusion.methods) {
  if (!fusion.methods.liuyao) errors.push('缺少 methods.liuyao');
  if (!fusion.methods.qimen) errors.push('缺少 methods.qimen');
  
  if (fusion.methods.qimen) {
    // 检查奇门九宫格是否泄露
    const qmKeys = Object.keys(fusion.methods.qimen);
    const forbiddenQimen = ['九宫', '宫位', '天盘', '地盘', '八门', '九星', '八神', 'pan', '盘面', '格局详情'];
    for (const fk of forbiddenQimen) {
      if (qmKeys.some(k => k.includes(fk))) {
        errors.push(`奇门九宫格泄露: methods.qimen 包含 "${fk}" 相关字段`);
      }
    }
    const allowedQimen = ['局数', '节气', '值符', '值使', '空亡'];
    for (const k of qmKeys) {
      if (!allowedQimen.includes(k)) {
        warnings.push(`methods.qimen 包含非标准字段 "${k}"，可能泄露内部信息`);
      }
    }
  }
}

// ─── 3. 双高同断规则检查 ───
if (fusion.agreement && fusion.conclusions) {
  for (const c of fusion.conclusions) {
    const isSame = fusion.agreement.overall === 'same';
    const lyHigh = c.liuyao_level === 'high';
    const qmHigh = c.qimen_level === 'high';
    const hasCounter = c.counter_evidence_ids && c.counter_evidence_ids.length > 0;
    const deliveryShouldBeFirm = isSame && lyHigh && qmHigh && !hasCounter;
    
    if (deliveryShouldBeFirm && c.delivery !== 'firm') {
      errors.push(
        `${c.id}: agreement=same + liuyao=high + qimen=high + 无反证 → delivery 须为 firm, 实际 ${c.delivery}`
      );
    }
    
    // firm 时 verdict 不得含概率词
    if (c.delivery === 'firm') {
      const probWords = ['可能', '大概', '也许', '多半', '大概率', '有可能', '说不定', '差不多', '基本上', '应该是'];
      for (const w of probWords) {
        if (c.verdict && c.verdict.includes(w)) {
          errors.push(`${c.id}: delivery=firm 但 verdict 含概率词 "${w}"`);
          break;
        }
      }
    }
  }
}

// ─── 4. counter_evidence_ids 与 agreement 矛盾检查 ───
if (fusion.conclusions) {
  for (const c of fusion.conclusions) {
    if (c.agreement === 'same' && c.counter_evidence_ids && c.counter_evidence_ids.length > 0) {
      errors.push(`${c.id}: agreement=same 但 counter_evidence_ids 非空`);
    }
  }
}

// ─── 5. 证据泄露检查 ───
const forbiddenInUserFields = [
  '旺衰', '用神', '世应', '六亲', '六神', '伏神', '飞神',
  '天芮', '天蓬', '天心', '天冲', '天辅', '天禽', '天任', '天英', '天柱',
  '休门', '生门', '伤门', '杜门', '景门', '死门', '惊门', '开门',
  '值符', '螣蛇', '太阴', '六合', '勾陈', '朱雀', '九地', '九天', '白虎', '玄武',
  '九宫', '旺相', '休囚', '空亡宫', '生克', '格局',
  'evidence', '权重', '分数', '等级',
];

const userVisibleFields = [];
for (const c of (fusion.conclusions || [])) {
  userVisibleFields.push(c.verdict || '');
  userVisibleFields.push(c.timing || '');
  userVisibleFields.push((c.conditions || []).join(' '));
  userVisibleFields.push((c.guidance || []).join(' '));
}
userVisibleFields.push(fusion.soulNote || '');
// diagram 不纳入检查 — 六爻卦图（含六神、六亲）是用户合法可见内容

const visibleText = userVisibleFields.join(' ');
for (const term of forbiddenInUserFields) {
  const hardForbidden = ['旺衰', '用神', '伏神', '飞神', '格局', '权重', '分数', '等级', 'evidence'];
  if (visibleText.includes(term)) {
    if (hardForbidden.includes(term)) {
      errors.push(`推断术语泄露到用户可见字段: "${term}"`);
    } else {
      warnings.push(`可能泄露内部信息: "${term}" 出现在用户可见字段`);
    }
  }
}

// ─── 6. Response 额外检查（V5 升级版）───
if (response) {
  for (const term of forbiddenInUserFields) {
    if (response.includes(term)) {
      if (['旺衰', '用神', '格局'].includes(term)) {
        errors.push(`response.txt 泄露推断术语: "${term}"`);
      } else {
        warnings.push(`response.txt 含可疑术语: "${term}"`);
      }
    }
  }

  // V7 新增：江湖化负向红线（仅保留机器能可靠判定的高置信查杀项）
  const blackTalk = ['金点', '空子', '攒尖儿', '戗盘', '春点', '切口', '尖头儿', '腥盘'];
  // 假定现场：收窄为精确的现场动作短语（避免“坐我这趟船”比喻、“他进我门”叙事误杀）
  const sceneWords = ['坐下吧', '坐下来吧', '来我这坐', '坐我这来了', '进我这屋', '伸过手', '点炷香', '看你脸上', '观你', '摊前', '摊上', '坐下来了'];
  const brag = ['相信我', '我见得多了', '我只会看盘说话', '我从来不骗人', '我这半辈子见过', '我跟那些不一样'];
  const ruleSpoken = ['卦不二起', '心不诚，我不给你乱断', '义不占财', '我不给你乱断', '耍嘴皮子，我不干那事'];

  // 读取 roundMeta：{ isFirm:bool }（可选覆盖）
  let rmeta = null;
  if (roundMetaPath) {
    try { rmeta = JSON.parse(fs.readFileSync(roundMetaPath, 'utf-8')); }
    catch (e) { errors.push(`无法读取 roundMeta: ${e.message}`); }
  }
  // V7 修 autoFirm：复用真双高校验（same + 双 high + 无反证），不再裸读 delivery==='firm'
  const autoFirm = (fusion.conclusions || []).some(c =>
    fusion.agreement?.overall === 'same' &&
    c.liuyao_level === 'high' && c.qimen_level === 'high' &&
    (!c.counter_evidence_ids || c.counter_evidence_ids.length === 0)
  );
  const isFirm = rmeta ? (rmeta.isFirm === true) : autoFirm;

  blackTalk.forEach(t => { if (response.includes(t)) errors.push(`江湖黑话: "${t}"`); });
  sceneWords.forEach(t => { if (response.includes(t)) errors.push(`假定现场: "${t}"`); });
  brag.forEach(t => { if (response.includes(t)) errors.push(`自报资历/拍胸脯: "${t}"`); });
  ruleSpoken.forEach(t => { if (response.includes(t)) errors.push(`行规说破: "${t}"`); });

  // V9：双高轮不变量（审官+验师V8一致修正）——从“正向凑三件套”改为“弱化词反向否决 + 宽松正向”
  // 建议句豁免：句中含建议标记词即豁免整句（不只测句首）
  if (isFirm && response) {
    const adviceMarks = ['你应该', '你要', '你最好', '我劝你', '建议你', '你得', '你先', '你该', '你千万', '你切记', '你别'];
    const sentences = response.split(/[。！？；\n]/).map(s => s.trim()).filter(s => s.length > 0);
    const verdictText = sentences.filter(s => !adviceMarks.some(m => s.includes(m))).join(' ');
    if (verdictText) {
      // ① 弱化词反向否决：命中任何弱化/退让词即 FAIL（含糊即破功，无论 skeleton 多完整）
      const weaken = ['可能', '大概', '多半', '应该', '也许', '或许', '八成', '七成', '有戏', '稳了', '把握', '差不多', '十之八九', '悬', '难说', '不一定', '不好说', '保不齐', '没准儿', '问题不大', '八九不离十', '十拿九稳'];
      const hitWeak = weaken.filter(w => verdictText.includes(w));
      if (hitWeak.length > 0) {
        errors.push(`双高轮不变量: 断语含弱化词 "${hitWeak.join('/')}"，双高轮不得含糊`);
      } else {
        // ② 宽松正向：断言 + 线索（时间/对象）至少两类命中，允许隐含（对象可从问询上下文推断）
        const firmVerbs = ['一定', '必', '能', '会', '可定', '必然', '稳', '准成', '成定了', '板上钉钉', '成', '签', '点头', '走', '调', '遇', '定'];
        const firmTime = ['今年', '明年', '月底', '下月', '这月', '秋天', '春天', '年底', '三月', '六月', '九月', '十月', '开春', '入秋', '立冬', '这周', '下周', '三个月', '半年', '三天内', '月底前'];
        const firmObject = ['合同', '款', '那桩事', '这门亲', '这个项目', '这笔生意', '这份差事', '那个位置', '你那位', '这份工作', '这单', '这个坎', '这份运', '对方', '甲方', '他', '她', '那边', '这件事', '那件事', '这事', '这桩'];
        const hasVerb = firmVerbs.some(w => verdictText.includes(w));
        const hasTime = firmTime.some(w => verdictText.includes(w));
        const hasObject = firmObject.some(w => verdictText.includes(w));
        const hitCnt = [hasVerb, hasTime, hasObject].filter(Boolean).length;
        if (hitCnt < 2) {
          const miss = [];
          if (!hasVerb) miss.push('明确断言');
          if (!hasTime) miss.push('时间');
          if (!hasObject) miss.push('对象');
          errors.push(`双高轮不变量: 断语须含 明确断言+线索(时间/对象) 至少两项（当前缺 ${miss.join('/')}），含糊或线索不足`);
        }
      }
    }
  }

  // 意象堆砌：全部交离线盲评（脚本不掺和，避免误杀满分句 + 每轮噪音）
}

// ─── 7. evidence_ids 存在性检查 ───
if (fusion.conclusions) {
  for (const c of fusion.conclusions) {
    if (!c.liuyao_evidence_ids || c.liuyao_evidence_ids.length === 0) {
      warnings.push(`${c.id}: liuyao_evidence_ids 为空`);
    }
    if (!c.qimen_evidence_ids || c.qimen_evidence_ids.length === 0) {
      warnings.push(`${c.id}: qimen_evidence_ids 为空`);
    }
  }
}

// ─── 输出 ───
console.log('');
console.log('═══════════════════════════════════════════');
console.log('  六爻+奇门融合校验 (V2.0)');
console.log('═══════════════════════════════════════════');
console.log(`  schema:  ${fusion.schemaVersion}`);
console.log(`  question: ${fusion.question?.text || '(无)'}`);
console.log(`  agreement: ${fusion.agreement?.overall || '(无)'}`);
console.log(`  conclusions: ${(fusion.conclusions || []).length}`);
console.log('───────────────────────────────────────────');

if (errors.length === 0 && warnings.length === 0) {
  console.log('  PASS 校验通过');
} else {
  if (errors.length > 0) {
    console.log(`  FAIL ${errors.length} 个错误:`);
    for (const e of errors) console.log(`     ✗ ${e}`);
  }
  if (warnings.length > 0) {
    console.log(`  WARN ${warnings.length} 个警告:`);
    for (const w of warnings) console.log(`     ⚠ ${w}`);
  }
}

console.log('═══════════════════════════════════════════');
console.log('');

process.exit(errors.length > 0 ? 1 : 0);
