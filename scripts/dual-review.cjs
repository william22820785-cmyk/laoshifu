'use strict';
/** Structural/evidence reconciliation checks; this does not prove interpretive truth. */
const fs = require('node:fs');
const crypto = require('node:crypto');
const {isDeepStrictEqual} = require('node:util');
const P = require('./presentation-policy.cjs');
const METHODS = {birth: ['bazi', 'ziwei'], event: ['liuyao', 'qimen']};
const LEVELS = ['none', 'low', 'medium', 'high'];
const RELATIONS = ['same', 'complementary', 'conditional', 'unresolved', 'corrected'];
const list = value => Array.isArray(value) ? value : [];
const strings = value => Array.isArray(value) && value.every(P.nonempty);
const ownersIn = value => {
 if (typeof value !== 'string') return [];
 return Object.entries({bazi: /(?:\bbazi\b|八字)/i, ziwei: /(?:\bziwei\b|紫微)/i,
  liuyao: /(?:\bliuyao\b|^ly[-_]|六爻)/i, qimen: /(?:\bqimen\b|^qm[-_]|奇门)/i})
  .filter(([, pattern]) => pattern.test(value)).map(([method]) => method);
};
function provenance(item) {
 const explicit = new Set(['system', 'method', 'source', 'sourcePath', 'id'].flatMap(key => ownersIn(item[key])));
 // Published birth registries use E001-style IDs and no source metadata.
 // These recognizable legacy descriptions are only a cross-method guard; claims still need source_paths.
 let hint;
 if (/^紫微命宫/.test(item.description || '')) hint = 'ziwei';
 else if (/^(日主|命格|命带财星|官杀有气)/.test(item.description || '')) hint = 'bazi';
 return {explicit, hint};
}
function evaluate(source, review, options = {}) {
 const errors = [];
 const empty = () => ({errors, conclusions: [], agreement: {overall: 'conflict', points: [], conflicts: []}, reconciled: false});
 const fail = message => errors.push(message);
 try {
  if (!P.plain(options) || !METHODS[options.kind]) {fail('kind 必须为 birth|event'); return empty();}
  const {kind, sourcePath, response, plan} = options;
  const methods = METHODS[kind];
  if (!P.plain(source) || !P.plain(review)) {fail('source/review 必须为对象'); return empty();}
  if (review.schemaVersion !== 'laoshifu-dual-review.v1') fail('review.schemaVersion 不匹配');
  if (review.kind !== kind) fail('review.kind 与入口不匹配');
  if (!['parallel', 'sequential'].includes(review.mode)) fail('review.mode 必须为 parallel|sequential');
  if (!P.nonempty(review.focus)) fail('review.focus 必须非空');
  if (typeof review.sourceSha256 !== 'string' || !/^[a-f0-9]{64}$/.test(review.sourceSha256)) fail('sourceSha256 格式非法');
  if (!P.nonempty(sourcePath)) fail('必须提供原始 sourcePath');
  else {
   const bytes = fs.readFileSync(sourcePath);
   if (crypto.createHash('sha256').update(bytes).digest('hex') !== review.sourceSha256) fail('sourceSha256 与原始文件字节不匹配');
   const original = JSON.parse(bytes.toString('utf8').replace(/^\uFEFF/, ''));
   if (!isDeepStrictEqual(original, source)) fail('source 与 sourcePath 原始数据不匹配');
  }
  if (!P.nonempty(response)) fail('response 必须为非空正文');
  const registry = new Map();
  const evidence = kind === 'birth' ? source.interpretation?.evidence : source.evidence;
  if (!Array.isArray(evidence) || !evidence.length) fail('原始 evidence 必须为非空数组');
  for (const item of list(evidence)) {
   if (!P.plain(item) || !P.nonempty(item.id)) {fail('原始 evidence 必须有非空 id'); continue;}
   if (registry.has(item.id)) fail('原始 evidence id 重复: ' + item.id);
   const owner = provenance(item);
   if (owner.explicit.size > 1) fail('原始 evidence 方法归属矛盾: ' + item.id);
   for (const key of ['system', 'method']) {
    if (Object.hasOwn(item, key) && !methods.includes(item[key])) fail('原始 evidence.' + key + ' 非法: ' + item.id);
   }
   if (kind === 'event' && (owner.explicit.size !== 1 || !methods.includes([...owner.explicit][0]))) fail('事件 evidence 方法来源不明: ' + item.id);
   if (Object.hasOwn(item, 'sourcePath')) {
    const value = P.resolvePointer(source, item.sourcePath);
    if (value === undefined || !isDeepStrictEqual(value, item.value ?? item.sourceValue)) fail('原始 evidence sourcePath/value 不匹配: ' + item.id);
   }
   registry.set(item.id, {item, owner: [...owner.explicit][0], hint: owner.hint});
  }
  function refs(value, label, {method, nonempty = false, paths = false} = {}) {
   if (!strings(value) || (nonempty && !value.length)) {fail(label + ' 必须为' + (nonempty ? '非空' : '') + '字符串数组'); return [];}
   if (new Set(value).size !== value.length) fail(label + ' 引用重复');
   for (const id of value) {
    const entry = registry.get(id);
    if (!entry) {fail(label + ' 引用了不存在的 evidence: ' + id); continue;}
    if (method && ((entry.owner && entry.owner !== method) || (!entry.owner && entry.hint && entry.hint !== method))) fail(label + ' 方法归属错误: ' + id);
    if (method && !entry.owner && !paths) fail(label + ' 缺少可验证的方法来源/source_paths: ' + id);
   }
   return value;
  }
  const claims = new Map();
  if (!Array.isArray(review.methods) || review.methods.length !== 2) fail('methods 必须恰有两法');
  const seenMethods = new Set();
  for (const reader of list(review.methods)) {
   if (!P.plain(reader) || !methods.includes(reader.method)) {fail('methods.method 非法'); continue;}
   if (seenMethods.has(reader.method)) fail('methods.method 重复');
   seenMethods.add(reader.method);
   if (!Array.isArray(reader.claims) || !reader.claims.length) fail(reader.method + '.claims 必须非空');
   for (const claim of list(reader.claims)) {
    if (!P.plain(claim)) {fail('claim 必须是对象'); continue;}
    const label = 'claim ' + claim.id;
    if (!P.nonempty(claim.id) || claims.has(claim.id)) fail(label + ' id 缺失或重复');
    if (!P.nonempty(claim.proposition)) fail(label + ' proposition 必须非空');
    if (!P.plain(claim.scope) || ['subject', 'time', 'aspect'].some(key => !P.nonempty(claim.scope[key]))) fail(label + ' scope 缺失 subject/time/aspect');
    if (!strings(claim.limits)) fail(label + ' limits 必须是字符串数组');
    let hasPaths = false;
    if (Object.hasOwn(claim, 'source_paths')) {
     if (!Array.isArray(claim.source_paths) || !claim.source_paths.length) fail(label + ' source_paths 必须是非空数组');
     else {
      hasPaths = true;
      for (const ref of claim.source_paths) {
       if (!P.plain(ref) || typeof ref.path !== 'string' || !ref.path.startsWith('/' + reader.method + '/') || !Object.hasOwn(ref, 'value')) {
        fail(label + ' source_paths 必须指向本方法原盘 /' + reader.method + '/'); hasPaths = false; continue;
       }
       const actual = P.resolvePointer(source, ref.path);
       if (actual === undefined || !isDeepStrictEqual(actual, ref.value)) {fail(label + ' source_paths path/value 不匹配'); hasPaths = false;}
      }
     }
    }
    const evidenceIds = refs(claim.evidence_ids, label + '.evidence_ids', {method: reader.method, nonempty: true, paths: hasPaths});
    const counterIds = refs(claim.counter_evidence_ids, label + '.counter_evidence_ids', {method: reader.method, paths: hasPaths});
    claims.set(claim.id, {method: reader.method, claim, evidenceIds, counterIds, hasPaths});
   }
  }
  if (methods.some(method => !seenMethods.has(method))) fail('methods 缺少指定方法');
  const resolutions = new Map(), covered = new Set();
  if (!Array.isArray(review.resolutions) || !review.resolutions.length) fail('resolutions 必须非空');
  for (const r of list(review.resolutions)) {
   if (!P.plain(r)) {fail('resolution 必须是对象'); continue;}
   const label = 'resolution ' + r.id;
   if (!P.nonempty(r.id) || resolutions.has(r.id)) fail(label + ' id 缺失或重复');
   if (!RELATIONS.includes(r.relation)) fail(label + ' relation 非法');
   if (!P.nonempty(r.rationale)) fail(label + ' rationale 必须非空');
   if (!Number.isInteger(r.rounds) || r.rounds < 0 || r.rounds > 2) fail(label + ' rounds 必须为 0..2 整数');
   for (const [index, key] of ['left_claim_ids', 'right_claim_ids'].entries()) {
    if (!strings(r[key]) || !r[key].length) {fail(label + '.' + key + ' 必须非空'); continue;}
    if (new Set(r[key]).size !== r[key].length) fail(label + ' claim 引用重复');
    for (const id of r[key]) {
     const claim = claims.get(id);
     if (!claim || claim.method !== methods[index]) fail(label + ' claim 不存在或不属于 ' + methods[index] + ': ' + id);
     covered.add(id);
    }
   }
   refs(r.condition_evidence_ids, label + '.condition_evidence_ids', {nonempty: r.relation === 'conditional'});
   refs(r.retained_counter_evidence_ids, label + '.retained_counter_evidence_ids');
   if (r.relation === 'corrected') {
    const correction = r.correction;
    if (!P.plain(correction) || !methods.includes(correction.method) || !P.nonempty(correction.reason)) fail(label + ' correction 缺少 method/reason');
    else {
     const claim = claims.get(correction.claim_id);
     if (!claim || claim.method !== correction.method || ![...list(r.left_claim_ids), ...list(r.right_claim_ids)].includes(correction.claim_id)) fail(label + ' correction.claim_id 方法或关联错误');
     const ids = refs(correction.evidence_ids, label + '.correction.evidence_ids', {method: correction.method, nonempty: true, paths: claim?.hasPaths});
     if (claim && ids.some(id => ![...claim.evidenceIds, ...claim.counterIds].includes(id))) fail(label + ' correction evidence 未由被修正 claim 取证');
    }
   }
   resolutions.set(r.id, r);
  }
  for (const id of claims.keys()) if (!covered.has(id)) fail('claim 未被 resolutions 覆盖: ' + id);
  const originalConclusions = new Map();
  function conclusionShape(c, label, original = false) {
   if (!P.plain(c)) {fail(label + ' 必须为对象'); return false;}
   for (const key of ['id', 'verdict']) if (!P.nonempty(c[key])) fail(label + '.' + key + ' 必须非空');
   const deliveries = kind === 'birth' ? ['direct', 'firm', 'probable', 'tentative'] : ['firm', 'probable', 'tentative'];
   if (!deliveries.includes(c.delivery)) fail(label + '.delivery 非法');
   if (!['same', 'complementary', 'conflict', ...(kind === 'birth' ? ['single'] : [])].includes(c.agreement)) fail(label + '.agreement 非法');
   for (const method of methods) {
    if (!LEVELS.includes(c[method + '_level'])) fail(label + '.' + method + '_level 非法');
    // Claim-specific paths below establish ownership for legacy birth IDs.
    refs(c[method + '_evidence_ids'], label + '.' + method + '_evidence_ids', {method, nonempty: true, paths: kind === 'birth' && !original});
   }
   refs(c.counter_evidence_ids, label + '.counter_evidence_ids');
   for (const key of ['conditions', 'guidance']) if (!strings(c[key])) fail(label + '.' + key + ' 必须为字符串数组');
   if (typeof c.timing !== 'string') fail(label + '.timing 必须为字符串');
   return true;
  }
  if (kind === 'event') {
   if (!P.plain(source.agreement) || !['same', 'complementary', 'conflict'].includes(source.agreement.overall) || !Array.isArray(source.agreement.conflicts) || !Array.isArray(source.agreement.points)) fail('原始 agreement 结构非法');
   if (!Array.isArray(source.conclusions) || !source.conclusions.length) fail('原始 event conclusions 必须非空');
   for (const c of list(source.conclusions)) {
    if (!conclusionShape(c, '原始 conclusion', true)) continue;
    if (originalConclusions.has(c.id)) fail('原始 conclusion id 重复');
    originalConclusions.set(c.id, c);
   }
  }
  if (!Array.isArray(review.conclusions) || !review.conclusions.length || review.conclusions.length > 4) fail('review.conclusions 必须为 1..4 条');
  const seenConclusions = new Set(), usedResolutions = new Set();
  for (const c of list(review.conclusions)) {
   if (!conclusionShape(c, 'conclusion')) continue;
   const label = 'conclusion ' + c.id;
   if (seenConclusions.has(c.id)) fail(label + ' id 重复');
   seenConclusions.add(c.id);
   if (!P.nonempty(c.uncertainty)) fail(label + '.uncertainty 必须具体且非空');
   if (!strings(c.resolution_ids) || !c.resolution_ids.length) fail(label + '.resolution_ids 必须非空');
   const linked = list(c.resolution_ids).map(id => {
    usedResolutions.add(id);
    if (!resolutions.has(id)) fail(label + ' resolution 不存在: ' + id);
    return resolutions.get(id);
   }).filter(Boolean);
   const linkedClaims = linked.flatMap(r => [...list(r.left_claim_ids), ...list(r.right_claim_ids)]).map(id => claims.get(id)).filter(Boolean);
   for (const method of methods) {
    const taken = new Set(linkedClaims.filter(claim => claim.method === method).flatMap(claim => claim.evidenceIds));
    for (const id of list(c[method + '_evidence_ids'])) if (!taken.has(id)) fail(label + ' 证据未由关联的同方法 claim 取证: ' + id);
   }
   const raw = originalConclusions.get(c.id);
   if (kind === 'event') {
    if (!raw) fail(label + ' 不属于原始 event conclusion IDs');
    else for (const method of methods) if (c[method + '_level'] !== raw[method + '_level']) fail(label + ' 不得修改原始 ' + method + '_level');
   }
   const retained = new Set([...list(c.counter_evidence_ids), ...linked.flatMap(r => list(r.retained_counter_evidence_ids))]);
   for (const id of list(raw?.counter_evidence_ids)) if (!retained.has(id)) fail(label + ' 遗失原始 counter: ' + id);
   const counter = retained.size || linkedClaims.some(claim => claim.counterIds.length);
   const unresolved = linked.some(r => r.relation === 'unresolved');
   if (unresolved && /^(不确定|尚不确定|无法确定|存在不确定性|两种可能|unknown|uncertain|tbd)[。.!！\s]*$/i.test(String(c.uncertainty).trim())) fail(label + ' unresolved 需说明具体未确定事项');
   if (unresolved && c.delivery !== 'tentative') fail(label + ' unresolved 必须 tentative');
   if (unresolved && c.agreement !== 'conflict') fail(label + ' unresolved 必须保留 conflict');
   if (c.agreement === 'same' && (counter || unresolved)) fail(label + ' same 与保留反证/未解冲突矛盾');
   const firm = ['direct', 'firm'].includes(c.delivery);
   const weakOrigin = raw && (raw.agreement === 'conflict' || list(raw.counter_evidence_ids).length || methods.some(method => ['low', 'none'].includes(raw[method + '_level'])));
   if (firm && (weakOrigin || source.agreement?.overall === 'conflict' || list(source.agreement?.conflicts).length || counter || unresolved || c.agreement !== 'same' || methods.some(method => c[method + '_level'] !== 'high') || linked.some(r => !['same', 'corrected'].includes(r.relation)))) fail(label + ' 原始冲突/弱依据/反证不可提升为 firm/direct');
   if (firm && kind === 'birth' && methods.some(method => !list(c[method + '_evidence_ids']).some(id => registry.get(id)?.item.strength === 'high'))) fail(label + ' firm/direct 缺少两法 high 原证据');
   if (c.delivery === 'probable' && c.agreement === 'conflict') fail(label + ' conflict 不可 probable，需先记录有据调和');
   if (c.delivery === 'probable' && linked.some(r => ['conditional', 'complementary'].includes(r.relation)) && !list(c.conditions).length) fail(label + ' probable 调和必须说明条件');
   if (typeof response === 'string') {
    for (const text of [c.verdict, c.uncertainty]) {
     if (P.nonempty(text) && !P.normalize(response).includes(P.normalize(text))) fail(label + ' response 缺少最终 verdict/uncertainty: ' + text);
    }
   }
  }
  for (const id of originalConclusions.keys()) if (!seenConclusions.has(id)) fail('遗漏原始 event conclusion: ' + id);
  for (const [id, r] of resolutions) {
   if (!usedResolutions.has(id)) fail('resolution 未被最终 conclusions 使用: ' + id);
   const retained = new Set([...list(r.retained_counter_evidence_ids), ...list(review.conclusions).filter(c => P.plain(c) && list(c.resolution_ids).includes(id)).flatMap(c => list(c.counter_evidence_ids))]);
   for (const claimId of [...list(r.left_claim_ids), ...list(r.right_claim_ids)]) {
    for (const counterId of claims.get(claimId)?.counterIds || []) if (!retained.has(counterId)) fail('resolution ' + id + ' 遗失 claim counter: ' + counterId);
   }
   const grounded = new Set([...list(r.left_claim_ids), ...list(r.right_claim_ids)].flatMap(claimId => {
    const claim = claims.get(claimId); return claim ? [...claim.evidenceIds, ...claim.counterIds] : [];
   }));
   if (list(r.condition_evidence_ids).some(evidenceId => !grounded.has(evidenceId))) fail('resolution ' + id + ' condition 未由关联 claim 取证');
  }
  if (kind === 'birth' && (!P.plain(plan) || !isDeepStrictEqual(plan.conclusions, review.conclusions))) fail('birth plan.conclusions 必须与 review.conclusions 完全匹配');
  if (errors.length) return empty();
  const conclusions = structuredClone(review.conclusions);
  const conflicts = conclusions.filter(c => c.agreement === 'conflict').map(c => ({dimension: c.id, resolution: c.uncertainty}));
  const overall = conflicts.length ? 'conflict' : conclusions.every(c => c.agreement === 'same') ? 'same' : 'complementary';
  const agreement = {overall, points: conclusions.map(c => ({dimension: c.id, verdict: c.verdict, delivery: c.delivery, detail: c.verdict + ' ' + c.uncertainty})), conflicts};
  return {errors, conclusions, agreement, reconciled: true};
 } catch (error) {
  fail('复核输入/原始文件校验失败: ' + error.message);
  return empty();
 }
}
module.exports = {evaluate};
