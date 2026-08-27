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

function parseArgs() {
  const args = {};
  process.argv.slice(2).forEach(arg => {
    const m = arg.match(/^--(\w+)=(.+)$/);
    if (m) args[m[1]] = m[2];
  });
  return args;
}

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
  return fs.readFileSync(filepath, 'utf8');
}

// 黑盒禁止词（问询与答复都查）
const BLOCKED_TERMS = [
  // 后台体系名
  '六爻', '奇门', '八字', '紫微', '紫微斗数',
  // 推断术语
  '四柱', '十神', '格局', '旺衰', '星曜', '宫位', '四化',
  '用神', '忌神', '仇神', '闲神',
  '九宫', '空亡', '值符', '值使',
  // 内部流程
  'evidence', '权重', '分数', '内部等级', '算法版本',
  '两张盘', '两个系统', '双法同参', '交叉验证',
  '后台', '推断链', '推断结构',
  // SKILL配置泄露
  'skill-root', 'node <skill-root>', 'chart.cjs', 'validate',
  'consultation-plan', 'chart.json', 'fusion.json',
];

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
function checkResponse(text, meta) {
  const issues = [];

  // 基础黑盒/报告腔/权威（与原先一致）
  BLOCKED_TERMS.forEach(term => { if (text.includes(term)) issues.push(`泄露术语: "${term}"`); });
  REPORT_PATTERNS.forEach(pat => { if (text.includes(pat)) issues.push(`报告腔: "${pat}"`); });
  AUTHORITY_PATTERNS.forEach(pat => { if (text.includes(pat)) issues.push(`权威套话: "${pat}"`); });

  // 江湖黑话
  BLACKTALK_TERMS.forEach(term => { if (text.includes(term)) issues.push(`江湖黑话: "${term}"`); });

  // 假定现场
  SCENE_TERMS.forEach(term => { if (text.includes(term)) issues.push(`假定现场: "${term}"`); });

  // 拍胸脯变体
  BRAG_TERMS.forEach(term => { if (text.includes(term)) issues.push(`自报资历/拍胸脯: "${term}"`); });

  // 行规说破
  RULE_SPOKEN_PATTERNS.forEach(pat => { if (text.includes(pat)) issues.push(`行规说破: "${pat}"`); });

  // 退让/含糊：V7 降级为“双高轮断语行为准则”（reference 强约束）+ 盲评抽检，脚本不拦。
  // 意象堆砌：全部交离线盲评（脚本不掺和，避免误杀满分句 + 每轮噪音）。

  // V9：双高轮不变量（审官+验师V8一致修正）——弱化词反向否决 + 宽松正向（至少两项）
  // 建议句豁免：句中含建议标记词即豁免整句（不只测句首）
  if (meta && meta.isFirm === true && text) {
    const adviceMarks = ['你应该', '你要', '你最好', '我劝你', '建议你', '你得', '你先', '你该', '你千万', '你切记', '你别'];
    // 剔除建议句，只留断语正文做不变量检查
    const sentences = text.split(/[。！？；\n]/).map(s => s.trim()).filter(s => s.length > 0);
    const verdictText = sentences.filter(s => !adviceMarks.some(m => s.includes(m))).join(' ');
    if (verdictText) {
      // ① 弱化词反向否决：命中任何弱化/退让词即 FAIL（含糊即破功，无论 skeleton 多完整）
      const weaken = ['可能', '大概', '多半', '应该', '也许', '或许', '八成', '七成', '有戏', '稳了', '把握', '差不多', '十之八九', '悬', '难说', '不一定', '不好说', '保不齐', '没准儿', '问题不大', '八九不离十', '十拿九稳'];
      const hitWeak = weaken.filter(w => verdictText.includes(w));
      if (hitWeak.length > 0) {
        issues.push(`双高轮不变量: 断语含弱化词 "${hitWeak.join('/')}"，直断轮不得含糊`);
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
          issues.push(`双高轮不变量: 断语须含 明确断言+线索(时间/对象) 至少两项（当前缺 ${miss.join('/')}），含糊或线索不足`);
        }
      }
    }
  }

  // 字数（算人场景 ≤520）
  if (text.length > 600) {
    issues.push(`答复过长 (${text.length} 字符，建议 ≤520)`);
  }

  // 标题/项目符号
  if (/^#{1,3}\s/m.test(text)) issues.push('使用了 Markdown 标题');
  if (/^\s*[-*]\s/m.test(text) || /^\s*\d+[.)]\s/m.test(text)) issues.push('使用了项目符号/编号列表');

  return issues;
}

function validatePlan(chart, plan) {
  const issues = [];
  if (!plan.delivery) {
    issues.push('plan 缺少 delivery 字段');
  } else if (!['direct', 'tentative', 'deferred'].includes(plan.delivery)) {
    issues.push(`无效的 delivery 值: ${plan.delivery}`);
  }
  if (!chart.interpretation || !chart.interpretation.evidence) {
    issues.push('chart.json 缺少 interpretation.evidence');
    return issues;
  }
  const validEvidenceIds = new Set(chart.interpretation.evidence.map(e => e.id || e));
  if (plan.evidence && Array.isArray(plan.evidence)) {
    plan.evidence.forEach(id => {
      if (!validEvidenceIds.has(id)) issues.push(`plan 引用了不存在的 evidence ID: ${id}`);
    });
  }
  return issues;
}

function main() {
  const args = parseArgs();

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
  if (args.chart && args.plan) {
    const chart = loadJSON(args.chart);
    plan = loadJSON(args.plan);
    const issues = validatePlan(chart, plan);
    allIssues.push(...issues);
    if (issues.length === 0) console.log('[OK] plan validated against chart');
  }

  if (args.response) {
    const text = loadText(args.response);
    // V6：roundMeta 统一为 { isFirm:bool }；默认从 plan.delivery 自动推导（direct=firm）
    let meta = null;
    if (args.roundMeta) {
      try { meta = JSON.parse(fs.readFileSync(args.roundMeta, 'utf8')); }
      catch (e) { console.error(`[FAIL] 无法读取 roundMeta: ${e.message}`); process.exit(1); }
    } else if (plan) {
      meta = { isFirm: plan.delivery === 'direct' };
    }
    const issues = checkResponse(text, meta);
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

main();
