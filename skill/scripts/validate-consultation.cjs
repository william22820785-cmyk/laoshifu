/**
 * validate-consultation.cjs — 八字紫微会谈校验脚本
 * 
 * 校验算人场景下的会谈输出：
 * 1. 校验 consultation-plan.json 与 chart.json 的 evidence ID 一致性
 * 2. 校验 response.txt 的黑盒合规性
 * 
 * 用法:
 *   node validate-consultation.cjs --chart=chart.json --plan=consultation-plan.json
 *   node validate-consultation.cjs --chart=chart.json --plan=consultation-plan.json --response=response.txt
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

// 黑盒禁止词
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

// 不允许的报告腔
const REPORT_PATTERNS = [
  '综合来看', '综上所述', '值得注意的是', '建议如下',
  '说到底', '本质上', '真正的问题是', '归根结底',
  '最终取决于你',
];

// 不允许的权威式套话
const AUTHORITY_PATTERNS = [
  '天机不可泄露', '贫道', '小友', '破财消灾', '相信我',
  '坐下说吧', '请坐', '把手伸过来', '点炷香',
];

function validateResponse(text) {
  const issues = [];

  // 检查黑盒禁止词
  BLOCKED_TERMS.forEach(term => {
    if (text.includes(term)) {
      issues.push(`泄露术语: "${term}"`);
    }
  });

  // 检查报告腔
  REPORT_PATTERNS.forEach(pat => {
    if (text.includes(pat)) {
      issues.push(`报告腔: "${pat}"`);
    }
  });

  // 检查权威式套话
  AUTHORITY_PATTERNS.forEach(pat => {
    if (text.includes(pat)) {
      issues.push(`权威套话: "${pat}"`);
    }
  });

  // 检查字数（算人场景不超过 520 字）
  if (text.length > 600) {
    issues.push(`答复过长 (${text.length} 字符，建议 ≤520)`);
  }

  // 检查是否有标题/项目符号结构
  if (/^#{1,3}\s/m.test(text)) {
    issues.push('使用了 Markdown 标题');
  }
  if (/^\s*[-*]\s/m.test(text) || /^\s*\d+[.)]\s/m.test(text)) {
    issues.push('使用了项目符号/编号列表');
  }

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
  
  // 检查 plan 中的 evidence IDs 是否存在
  if (plan.evidence && Array.isArray(plan.evidence)) {
    plan.evidence.forEach(id => {
      if (!validEvidenceIds.has(id)) {
        issues.push(`plan 引用了不存在的 evidence ID: ${id}`);
      }
    });
  }

  return issues;
}

function main() {
  const args = parseArgs();

  // --inquiry 模式：只校验询问文本
  if (args.inquiry) {
    const text = loadText(args.inquiry);
    const issues = validateResponse(text);
    if (issues.length > 0) {
      console.log('[WARN]');
      issues.forEach(i => console.log(`  ${i}`));
    } else {
      console.log('[OK] inquiry passed');
    }
    process.exit(issues.length > 0 ? 1 : 0);
  }

  // --response 模式：校验完整答复
  let allIssues = [];

  if (args.chart && args.plan) {
    const chart = loadJSON(args.chart);
    const plan = loadJSON(args.plan);
    const issues = validatePlan(chart, plan);
    allIssues.push(...issues);
    
    if (issues.length === 0) {
      console.log('[OK] plan validated against chart');
    }
  }

  if (args.response) {
    const text = loadText(args.response);
    const issues = validateResponse(text);
    allIssues.push(...issues);
    
    if (issues.length === 0) {
      console.log('[OK] response validated');
    }
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
