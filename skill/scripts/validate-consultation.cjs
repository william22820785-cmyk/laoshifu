/**
 * validate-consultation.cjs — 八字紫微会谈校验脚本（V5 升级版）
 * 
 * 校验算人场景下的会谈输出：
 * 1. 校验 consultation-plan.json 与 chart.json 的 evidence ID 一致性
 * 2. 校验 response.txt 的黑盒合规性 + 江湖化负向红线
 * 
 * V5 变更（依据审官、验师第4轮对抗性审查）：
 * - 拆分 checkInquiry() / checkResponse()：问询文本只查黑盒，答复文本查全量
 *   （避免用户问句里的"大概/应该"被误判为老师退让）
 * - responseChecks 支持 roundMeta：双高轮才查退让词、断语体才查意象堆砌
 * - 退让词改为"无落点退让结构"判据（比单字表更准，少误杀建议句）
 * - 意象堆砌需要人工预标（isJoke/isVerdict 标记），脚本只查有标记的断语体
 * 
 * 用法:
 *   node validate-consultation.cjs --chart=chart.json --plan=consultation-plan.json
 *   node validate-consultation.cjs --chart=chart.json --plan=consultation-plan.json --response=response.txt [--roundMeta=response-meta.json]
 *   node validate-consultation.cjs --inquiry=response.txt
 */

const fs = require('fs');
const path = require('path');
const P = require('./presentation-policy.cjs');
const {evaluate} = require('./dual-review.cjs');

function parseArgs() { return P.args(); }

function loadJSON(filepath) {
  if (!fs.existsSync(filepath)) {
    console.error(`[FAIL] File not found: ${filepath}`);
    process.exit(1);
  }
  return JSON.parse(fs.readFileSync(filepath, 'utf8'));
}

function loadText(filepath) {
  if (!fs.existsSync(filepath)) {
    console.error(`[FAIL] File not found: ${filepath}`);
    process.exit(1);
  }
  return fs.readFileSync(filepath, 'utf8').replace(/\r\n?/g, '\n');
}

// 黑盒禁止词（问询与答复都查）
const BLOCKED_TERMS = P.INTERNAL_TERMS;

// 不允许的报告腔（问询与答复都查）
const REPORT_PATTERNS = [
  '综合来看', '综上所述', '值得注意的是', '建议如下',
  '说到底', '本质上', '真正的问题是', '归根结底',
  '最终取决于你',
];

// 不允许的权威式套话（问询与答复都查）
const AUTHORITY_PATTERNS = [
  '天机不可泄露', '贫道', '小友', '破财消灾', '相信我',
  '坐下说吧', '请坐', '把手伸过来', '点炷香',
];

// ─── V7 新增：江湖化负向红线（仅保留机器能可靠判定的高置信查杀项，仅答复文本查）───

// 江湖黑话 / 切口（多字词；单字“尖/腥”不单独收，避免误伤“针尖对麦芒”等）
const BLACKTALK_TERMS = ['金点', '空子', '攒尖儿', '戗盘', '春点', '切口', '尖头儿', '腥盘'];

// 假定现场（收窄为精确现场动作短语，避免“坐我这趟船”比喻、“他进我门”叙事误杀）
const SCENE_TERMS = [
  '坐下吧', '坐下来吧', '来我这坐', '坐我这来了', '进我这屋', '伸过手', '点炷香',
  '看你脸上', '观你', '摊前', '摊上', '坐下来了',
];

// 拍胸脯 / 自报资历变体（“我看了几十年”与官方正例冲突，从词表删除，交给 reference 校准）
const BRAG_TERMS = [
  '相信我', '我见得多了', '我只会看盘说话',
  '我从来不骗人', '我这半辈子见过', '我跟那些不一样',
];

// 行规说破（整句逻辑——不拆散词，避免误伤情感承接语境）
const RULE_SPOKEN_PATTERNS = [
  '卦不二起', '心不诚，我不给你乱断', '义不占财',
  '我不给你乱断', '耍嘴皮子，我不干那事',
];

// 戏谑/哲理句豁免白名单（与 master-identity.md 逐字一致；攥 非 攒）
const WIT_EXEMPT = [
  '财这东西认路，不认嗓门', '嘴上说随缘，心里那根绳攥得比谁都紧',
  '命里八尺，难求一丈', '强扭的瓜不甜',
];

function splitSentences(text) {
  // 按中文句号/感叹/问号/分句分隔
  return text.split(/[。！？；\n]/).map(s => s.trim()).filter(s => s.length > 0);
}

// 戏谑/哲理句豁免（供盲评参考；脚本当前不拦退让，保留供未来语义级检查）
function isWitExempt(sentence) {
  return WIT_EXEMPT.some(w => sentence.includes(w));
}

// ─── checkInquiry：只查问询文本（用户的话），不查现场/黑话（避免误伤用户原话）───
function checkInquiry(text) {
  const issues = [];
  BLOCKED_TERMS.forEach(term => { if (text.includes(term)) issues.push(`泄露术语: "${term}"`); });
  REPORT_PATTERNS.forEach(pat => { if (text.includes(pat)) issues.push(`报告腔: "${pat}"`); });
  AUTHORITY_PATTERNS.forEach(pat => { if (text.includes(pat)) issues.push(`权威套话: "${pat}"`); });
  return issues;
}

// ─── checkResponse：查全量（黑盒 + 报告腔 + 权威 + 江湖负向红线）───
function checkResponse(text, meta, detail='standard') {
  const issues = P.textIssues(text, detail);
  for (const term of [...BLACKTALK_TERMS, ...SCENE_TERMS, ...BRAG_TERMS, ...RULE_SPOKEN_PATTERNS]) {
    if (text.includes(term)) issues.push('不合适的角色表述: ' + term);
  }
  return issues;
}

function validatePlan(chart, plan, reviewed = false) {
  const issues = [];
  if (!plan || typeof plan !== 'object' || Array.isArray(plan)) {
    issues.push('plan 必须是对象');
    return issues;
  }
  if (!P.plain(chart) || !chart.interpretation || !Array.isArray(chart.interpretation.evidence)) {
    issues.push('chart.json 缺少 interpretation.evidence');
    return issues;
  }
  const validEvidenceIds = new Set(chart.interpretation.evidence.map(e => e.id || e));
  const validDeliveries = ['direct', 'firm', 'probable', 'tentative'];
  const validLevels = ['high', 'medium', 'low', 'none'];

  // delivery 按 schema 位于 conclusions[] 内；不再读取不存在的顶层 plan.delivery。
  if ('delivery' in plan) {
    issues.push('plan.delivery 已废弃；请把 delivery 放入 conclusions[]');
  }
  if (!Array.isArray(plan.conclusions) || plan.conclusions.length < 1 || plan.conclusions.length > 4) {
    issues.push('plan.conclusions 必须是 1-4 条数组');
    return issues;
  }

  plan.conclusions.forEach((conclusion, index) => {
    const label = `conclusions[${index}]`;
    if (!conclusion || typeof conclusion !== 'object' || Array.isArray(conclusion)) {
      issues.push(`${label} 必须是对象`);
      return;
    }
    for (const key of ['id', 'verdict', 'agreement', 'bazi_level', 'ziwei_level', 'delivery']) {
      if (typeof conclusion[key] !== 'string' || !conclusion[key].trim()) {
        issues.push(`${label}.${key} 缺失或不是非空字符串`);
      }
    }
    if (!validDeliveries.includes(conclusion.delivery)) {
      issues.push(`${label}.delivery 无效: ${conclusion.delivery}`);
    }
    if (!validLevels.includes(conclusion.bazi_level)) {
      issues.push(`${label}.bazi_level 无效: ${conclusion.bazi_level}`);
    }
    if (!validLevels.includes(conclusion.ziwei_level)) {
      issues.push(`${label}.ziwei_level 无效: ${conclusion.ziwei_level}`);
    }
    if (!Array.isArray(conclusion.bazi_evidence_ids) || conclusion.bazi_evidence_ids.length < 1) {
      issues.push(`${label}.bazi_evidence_ids 必须至少包含一个 evidence ID`);
    } else {
      conclusion.bazi_evidence_ids.forEach(id => {
        if (!validEvidenceIds.has(id)) issues.push(`${label} 引用了不存在的 bazi evidence ID: ${id}`);
      });
    }
    if (!Array.isArray(conclusion.ziwei_evidence_ids) || conclusion.ziwei_evidence_ids.length < 1) {
      issues.push(`${label}.ziwei_evidence_ids 必须至少包含一个 evidence ID`);
    } else {
      conclusion.ziwei_evidence_ids.forEach(id => {
        if (!validEvidenceIds.has(id)) issues.push(`${label} 引用了不存在的 ziwei evidence ID: ${id}`);
      });
    }
    const counters = Array.isArray(conclusion.counter_evidence_ids) ? conclusion.counter_evidence_ids : [];
    counters.forEach(id => {
      if (!validEvidenceIds.has(id)) issues.push(`${label} 引用了不存在的 counter evidence ID: ${id}`);
    });
    const isDoubleHigh = conclusion.agreement === 'same'
      && conclusion.bazi_level === 'high'
      && conclusion.ziwei_level === 'high'
      && counters.length === 0;
    if (!reviewed && isDoubleHigh && conclusion.delivery !== 'direct') {
      issues.push(`${label}: 双高同断且无反证时 delivery 必须为 direct`);
    }
    if (conclusion.delivery === 'direct') {
      if (!isDoubleHigh) issues.push(`${label}: direct 只允许用于双高同断且无反证的结论`);
      // direct 描述主判断表达方式，不是对现实结果的保证。

    }
  });
  return issues;
}

function derivePlanFirm(plan) {
  return Array.isArray(plan?.conclusions)
    && plan.conclusions.some(conclusion => conclusion && conclusion.delivery === 'direct');
}
function main() {
  const args = parseArgs();
  if (args.review && (!args.chart || !args.plan || !args.response || args.inquiry)) {
    throw Error('--review 必须同时提供 --chart、--plan、--response，且不能用于 inquiry');
  }

  // --inquiry 模式：只校验询问文本（只查黑盒，不查退让/意象/现场）
  if (args.inquiry) {
    const text = loadText(args.inquiry);
    const issues = checkInquiry(text);
    if (issues.length > 0) {
      console.log('[WARN]');
      issues.forEach(i => console.log(`  ${i}`));
    } else {
      console.log('[OK] inquiry passed');
    }
    process.exit(issues.length > 0 ? 1 : 0);
  }

  // --response 模式
  let allIssues = [];

  // V6 坑B补：算人主流程若校验证件盘面，必须同时提供 --response（否则词表静默失效）
  if (args.chart && args.plan && !args.response) {
    console.error('[FAIL] 缺少 --response 参数。V6 起强制扫描答复文本，请传入 response.txt');
    process.exit(1);
  }

  let plan = null;
  let chart = null;
  if (args.chart && args.plan) {
    chart = loadJSON(args.chart);
    plan = loadJSON(args.plan);
    if (args.review) {
      const result = evaluate(chart, loadJSON(args.review), {kind:'birth', sourcePath:args.chart, response:loadText(args.response), plan});
      if (result.errors.length) {
        console.error('[FAIL] ' + result.errors.join('\n'));
        process.exitCode = 1;
        return;
      }
    }
    const issues = validatePlan(chart, plan, Boolean(args.review));
    allIssues.push(...issues);
    if (issues.length === 0) console.log('[OK] plan validated against chart');
  }

  if (args.response) {
    const text = loadText(args.response);
    // V6：roundMeta 统一为 { isFirm:bool }；默认从 conclusions[].delivery 自动推导（direct=firm）
    let meta = null;
    if (args.roundMeta) {
      try { meta = JSON.parse(fs.readFileSync(args.roundMeta, 'utf8')); }
      catch (e) { console.error(`[FAIL] 无法读取 roundMeta: ${e.message}`); process.exit(1); }
    } else if (plan) {
      meta = { isFirm: derivePlanFirm(plan) };
    }
    if (plan && derivePlanFirm(plan) && meta && meta.isFirm !== true) {
      console.error('[FAIL] roundMeta 不得把 schema 中的 direct 结论降级为非直断');
      process.exit(1);
    }
    if (plan && meta) {
      meta = { ...meta, isFirm: derivePlanFirm(plan) || meta.isFirm === true };
    }
    const issues = checkResponse(text, meta, args.detail || 'standard');
    const notes = args.publicNotes ? P.readJSON(args.publicNotes) : null;
    issues.push(...P.noteIssues(text, chart, notes));
    allIssues.push(...issues);
    if (issues.length === 0) console.log('[OK] response validated');
  }

  if (allIssues.length > 0) {
    console.log('[WARN]');
    allIssues.forEach(i => console.log(`  ${i}`));
    process.exit(1);
  }
  if (allIssues.length === 0 && (args.chart || args.response || args.inquiry)) {
    console.log('[PASS] All checks passed');
  }
}

try { main(); } catch (e) { console.error('[FAIL] ' + e.message); process.exitCode = 1; }
