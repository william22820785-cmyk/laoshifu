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

if (!fusionPath) {
  console.error('用法: node validate-liuyao-qimen-consultation.cjs --fusion=fusion.json [--response=response.txt]');
  process.exit(2);
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

// ─── 6. Response 额外检查 ───
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
