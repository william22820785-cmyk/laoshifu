'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'..');
const dir=path.join(__dirname,'fixtures','dual-review-runtime');
fs.mkdirSync(dir,{recursive:true});
const clone=x=>structuredClone(x);
const put=(name,x)=>{const p=path.join(dir,name);fs.writeFileSync(p,typeof x==='string'?x:JSON.stringify(x,null,2));return p;};
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const modulePath=path.join(root,'scripts/dual-review.cjs');
const evaluate=(...args)=>require(modulePath).evaluate(...args);
function dossier(kind='event'){
 const sourcePath=path.join(__dirname,'fixtures',`dual-review-${kind}.json`);
 const source=JSON.parse(fs.readFileSync(sourcePath,'utf8'));
 const names=kind==='event'?['liuyao','qimen']:['bazi','ziwei'];
 const originals=kind==='event'?source.conclusions:[{id:'career-2026',topic:'career',agreement:'complementary',bazi_level:'medium',ziwei_level:'medium',delivery:'probable',bazi_evidence_ids:['E005'],ziwei_evidence_ids:['E006'],counter_evidence_ids:[]}];
 const methods=names.map((method,n)=>({method,claims:originals.map((c,i)=>({id:`${method}-${i}`,proposition:n?'推进仍受对方节奏限制，需要等待确认':'已有推进基础，需先落实具体安排',evidence_ids:clone(c[`${method}_evidence_ids`]),counter_evidence_ids:n?[]:clone(c.counter_evidence_ids),scope:{subject:'本人',time:'本月底',aspect:i?'进展时间':'合同推进'},...(kind==='birth'?{source_paths:[{path:n?'/ziwei/gongs':'/bazi/dayMaster',value:clone(n?source.ziwei.gongs:source.bazi.dayMaster)}]}:{}),limits:['盘面不能保证现实结果']}))}));
 const resolutions=originals.map((c,i)=>({id:`r-${i}`,left_claim_ids:[methods[0].claims[i].id],right_claim_ids:[methods[1].claims[i].id],relation:i?'complementary':'conditional',rationale:'已有推进基础与节奏受阻可以同时成立，落实书面安排后再观察对方确认。',condition_evidence_ids:i?[]:[methods[0].claims[i].evidence_ids[0]],retained_counter_evidence_ids:clone(c.counter_evidence_ids),rounds:1}));
 const conclusions=originals.map((c,i)=>({...clone(c),verdict:i?'需等确认后再判断推进时间。':'先确认书面安排，才有望继续推进。',timing:'确认前不锁定日期。',conditions:['先落实书面安排。'],guidance:['拿到对方确认再推进。'],delivery:'probable',agreement:'complementary',counter_evidence_ids:[],resolution_ids:[`r-${i}`],uncertainty:i?'目前无法确定对方给出确认的具体日期。':'对方是否按期确认仍未确定。'}));
 const review={schemaVersion:'laoshifu-dual-review.v1',kind,sourceSha256:hash(sourcePath),mode:'sequential',focus:'月底前能否推进合同',methods,resolutions,conclusions};
 const response=conclusions.flatMap(c=>[c.verdict,c.uncertainty,c.timing,...c.conditions,...c.guidance]).join('\n');
 const plan={schemaVersion:'bazi-ziwei-consultation.v1',stage:'reading',conclusions:clone(conclusions)};
 return {source,review,options:{kind,sourcePath,response,...(kind==='birth'?{plan}:{})}};
}
function check(d){return evaluate(d.source,d.review,d.options);}
function good(d){const r=check(d);assert.deepEqual(r.errors,[]);assert.equal(r.reconciled,true);assert.deepEqual(r.conclusions,d.review.conclusions);return r;}
function bad(d,pattern){const r=check(d);assert.ok(r.errors.length, 'must fail closed');assert.equal(r.reconciled,false);assert.deepEqual(r.conclusions,[]);if(pattern)assert.match(r.errors.join('\n'),pattern);}
function rebind(d,name='rebound.json'){d.options.sourcePath=put(name,d.source);d.review.sourceSha256=hash(d.options.sourcePath);}
function syncPlan(d){if(d.options.plan)d.options.plan.conclusions=clone(d.review.conclusions);}
function run(script,args){return spawnSync(process.execPath,[path.join(root,script),...args],{encoding:'utf8',timeout:30000,windowsHide:true,env:{...process.env,PYTHONDONTWRITEBYTECODE:'1',PYTHONUTF8:'1'}});}
function cli(d,pkg,withReview=true){
 const sourceFlag=d.options.kind==='birth'?'chart':'fusion';
 const args=[`--${sourceFlag}=${d.options.sourcePath}`,`--response=${put('response.txt',d.options.response)}`];
 if(d.options.plan)args.push(`--plan=${put('plan.json',d.options.plan)}`);
 if(d.options.kind==='event'){
  const out=spawnSync('python',[path.join(root,pkg,'scripts/diagram_render.py'),`--fusion=${d.options.sourcePath}`,'--text'],{encoding:'utf8',env:{...process.env,PYTHONUTF8:'1',PYTHONDONTWRITEBYTECODE:'1'}});
  assert.equal(out.status,0,out.stderr);
  args[1]=`--response=${put('response.txt',out.stdout.trimEnd()+'\n'+d.options.response)}`;
  args.push('--diagramMode=text');
 }
 if(withReview)args.push(`--review=${put('review.json',d.review)}`);
 if(d.options.publicNotes)args.push(`--publicNotes=${put('notes.json',d.options.publicNotes)}`);
 return run(`${pkg}/scripts/validate-${d.options.kind==='birth'?'consultation':'liuyao-qimen-consultation'}.cjs`,args);
}
test('shared API exists before implementation',()=>assert.ok(fs.existsSync(modulePath)));
for(const kind of ['birth','event']){
 test(`${kind}: real engine fixture supports grounded probable with retained opposition`,()=>{const d=dossier(kind),before=fs.readFileSync(d.options.sourcePath);good(d);assert.deepEqual(fs.readFileSync(d.options.sourcePath),before);});
 test(`${kind}: unresolved gives specific uncertainty without mandatory 两种`,()=>{const d=dossier(kind);d.review.resolutions[0].relation='unresolved';d.review.conclusions[0].delivery='tentative';d.review.conclusions[0].agreement='conflict';syncPlan(d);const r=good(d);assert.equal(r.agreement.overall,'conflict');assert.ok(r.agreement.conflicts.length);});
 test(`${kind}: corrected requires linked claim and genuine method evidence`,()=>{const d=dossier(kind),r=d.review.resolutions[0];r.relation='corrected';r.correction={method:d.review.methods[0].method,claim_id:r.left_claim_ids[0],reason:'原读法把阶段阻力当成最终结果，需按同一问题范围修正。',evidence_ids:d.review.methods[0].claims[0].evidence_ids};good(d);});
 test(`${kind}: counters may be retained in conclusions instead`,()=>{const d=dossier(kind);d.review.conclusions[0].counter_evidence_ids=clone(d.review.resolutions[0].retained_counter_evidence_ids);d.review.resolutions[0].retained_counter_evidence_ids=[];syncPlan(d);good(d);});
 for(const [name,mutate] of [
  ['wrong hash',d=>d.review.sourceSha256='0'.repeat(64)],
  ['invalid mode',d=>d.review.mode='agents'],
  ['empty focus',d=>d.review.focus=' '],
  ['duplicate methods',d=>d.review.methods[1].method=d.review.methods[0].method],
  ['empty method claims',d=>d.review.methods[0].claims=[]],
  ['duplicate claim',d=>d.review.methods[1].claims[0].id=d.review.methods[0].claims[0].id],
  ['empty proposition',d=>d.review.methods[0].claims[0].proposition=''],
  ['missing scope',d=>delete d.review.methods[0].claims[0].scope],
  ['missing limits',d=>delete d.review.methods[0].claims[0].limits],
  ['wrong method evidence',d=>d.review.methods[0].claims[0].evidence_ids=d.review.methods[1].claims[0].evidence_ids],
  ['wrong counter ownership',d=>d.review.methods[1].claims[0].counter_evidence_ids=d.review.methods[0].claims[0].evidence_ids],
  ['unknown evidence',d=>d.review.methods[0].claims[0].evidence_ids=['unknown']],
  ['missing claim coverage',d=>d.review.methods[0].claims.push({...clone(d.review.methods[0].claims[0]),id:'uncovered'})],
  ['one sided resolution',d=>d.review.resolutions[0].right_claim_ids=[]],
  ['unknown resolution claim',d=>d.review.resolutions[0].left_claim_ids=['unknown']],
  ['missing condition evidence',d=>d.review.resolutions[0].condition_evidence_ids=[]],
  ['unknown condition evidence',d=>d.review.resolutions[0].condition_evidence_ids=['unknown']],
  ['lost claim counter',d=>{d.review.methods[0].claims[0].counter_evidence_ids=[d.review.methods[0].claims[0].evidence_ids[0]];d.review.resolutions[0].retained_counter_evidence_ids=[];}],
  ['unknown retained counter',d=>d.review.resolutions[0].retained_counter_evidence_ids.push('unknown')],
  ['round overflow',d=>d.review.resolutions[0].rounds=3],
  ['missing rounds',d=>delete d.review.resolutions[0].rounds],
  ['fractional rounds',d=>d.review.resolutions[0].rounds=0.5],
  ['unknown conclusion resolution',d=>d.review.conclusions[0].resolution_ids=['unknown']],
  ['empty uncertainty',d=>d.review.conclusions[0].uncertainty=''],
  ['unresolved probable',d=>d.review.resolutions[0].relation='unresolved'],
  ['missing verdict in response',d=>d.options.response=d.options.response.replace(d.review.conclusions[0].verdict,'')],
  ['missing uncertainty in response',d=>d.options.response=d.options.response.replace(d.review.conclusions[0].uncertainty,'')],
  ['missing method conclusion citation',d=>d.review.conclusions[0][`${d.review.methods[1].method}_evidence_ids`]=[]],
  ['wrong conclusion evidence ownership',d=>d.review.conclusions[0][`${d.review.methods[0].method}_evidence_ids`]=d.review.conclusions[0][`${d.review.methods[1].method}_evidence_ids`]],
  ['missing correction',d=>d.review.resolutions[0].relation='corrected'],
  ['wrong correction method',d=>{const r=d.review.resolutions[0];r.relation='corrected';r.correction={method:d.review.methods[1].method,claim_id:r.left_claim_ids[0],reason:'纠正范围',evidence_ids:d.review.methods[0].claims[0].evidence_ids};}],
 ])test(`${kind}: rejects ${name}`,()=>{const d=dossier(kind);mutate(d);syncPlan(d);bad(d);});
 for(const pkg of ['.','skill']){
  test(`${pkg} ${kind} CLI review path accepts supported synthesis`,()=>{const d=dossier(kind),r=cli(d,pkg);assert.equal(r.status,0,r.stdout+r.stderr);});
  test(`${pkg} ${kind} CLI fails invalid review without fallback`,()=>{const d=dossier(kind);d.review.sourceSha256='0'.repeat(64);const r=cli(d,pkg);assert.equal(r.status,1,r.stdout+r.stderr);});
 }
}
test('hash binds exact original bytes including BOM and CRLF',()=>{const d=dossier();d.options.sourcePath=put('bom-crlf.json','\uFEFF'+JSON.stringify(d.source,null,2).replace(/\n/g,'\r\n'));d.review.sourceSha256=hash(d.options.sourcePath);good(d);d.review.sourceSha256=crypto.createHash('sha256').update(JSON.stringify(d.source)).digest('hex');bad(d);});
test('hash also binds supplied source object to file',()=>{const d=dossier();d.source.conclusions[0].agreement='same';bad(d);});
test('missing source path fails closed',()=>{const d=dossier();delete d.options.sourcePath;bad(d);});
test('birth plan must exactly equal review conclusions',()=>{const d=dossier('birth');d.options.plan.conclusions[0].guidance=['篡改计划'];bad(d,/plan|计划/);});
test('birth plan required for review',()=>{const d=dossier('birth');delete d.options.plan;bad(d);});
test('all raw event conclusions must be covered',()=>{const d=dossier();d.review.conclusions.pop();bad(d);});
test('event conclusion IDs cannot be invented',()=>{const d=dossier();d.review.conclusions[0].id='new-outcome';bad(d);});
test('raw counter cannot be hidden by clearing claim counters',()=>{const d=dossier();d.review.methods[0].claims[0].counter_evidence_ids=[];d.review.resolutions[0].retained_counter_evidence_ids=[];bad(d);});
test('counter retained by unrelated conclusion does not cover original',()=>{const d=dossier();d.review.resolutions[1].retained_counter_evidence_ids=clone(d.review.resolutions[0].retained_counter_evidence_ids);d.review.resolutions[0].retained_counter_evidence_ids=[];bad(d);});
test('original event method levels cannot be raised',()=>{const d=dossier();d.review.conclusions[0].liuyao_level='high';bad(d);});
test('conflicted origin cannot become firm even with high labels and hidden counters',()=>{const d=dossier();d.source.agreement.overall='conflict';d.source.conclusions[0].agreement='conflict';d.source.conclusions[0].liuyao_level='high';d.source.conclusions[0].qimen_level='high';rebind(d);Object.assign(d.review.conclusions[0],{agreement:'same',delivery:'firm',liuyao_level:'high',qimen_level:'high'});bad(d);});
test('unknown legacy birth provenance is rejected',()=>{const d=dossier('birth');d.source.interpretation.evidence.find(e=>e.id==='E005').description='未知事实';delete d.review.methods[0].claims[0].source_paths;rebind(d);bad(d);});
test('explicit source metadata wins over description',()=>{const d=dossier('birth');const e=d.source.interpretation.evidence.find(e=>e.id==='E005');e.system='ziwei';rebind(d);bad(d);});
test('inconsistent ownership fields fail closed',()=>{const d=dossier();d.source.evidence[0].method='qimen';rebind(d);bad(d);});
for(const [name,mutate] of [
 ['null review',d=>d.review=null],['array review',d=>d.review=[]],['null claim',d=>d.review.methods[0].claims=[null]],['null resolution',d=>d.review.resolutions=[null]],['null conclusion',d=>d.review.conclusions=[null]],['malformed conclusion counters',d=>d.review.conclusions[0].counter_evidence_ids={}],['null source evidence',d=>{d.source.evidence.push(null);rebind(d);}],['duplicate source evidence',d=>{d.source.evidence.push(clone(d.source.evidence[0]));rebind(d);}],['malformed raw counter',d=>{d.source.conclusions[0].counter_evidence_ids={};rebind(d);}]
])test(`malformed input: ${name}`,()=>{const d=dossier();mutate(d);assert.doesNotThrow(()=>bad(d));});
for(const pkg of ['.','skill']){
 test(`${pkg}: legacy event path retains forced tentative and 两种 check`,()=>{const d=dossier();d.source.conclusions=d.review.conclusions.map(c=>{const x=clone(c);delete x.resolution_ids;delete x.uncertainty;return x;});rebind(d);const r=cli(d,pkg,false);assert.equal(r.status,1);assert.match(r.stdout,/tentative|两种/);});
 test(`${pkg}: original engine event passes legacy validation`,()=>{const d=dossier();d.options.response=d.source.conclusions.flatMap(c=>[c.verdict,c.timing,...c.conditions,...c.guidance]).join('\n');const r=cli(d,pkg,false);assert.equal(r.status,1);assert.match(r.stdout,/publicNotes/);});
 test(`${pkg}: legacy birth path remains available`,()=>{const d=dossier('birth');delete d.options.plan.conclusions[0].resolution_ids;delete d.options.plan.conclusions[0].uncertainty;const r=cli(d,pkg,false);assert.equal(r.status,0,r.stdout+r.stderr);});
}
test('root and skill mirror scripts remain identical',()=>{for(const name of ['dual-review.cjs','validate-consultation.cjs','validate-liuyao-qimen-consultation.cjs'])assert.deepEqual(fs.readFileSync(path.join(root,'scripts',name)),fs.readFileSync(path.join(root,'skill/scripts',name)));});

test('response may paraphrase timing, conditions and guidance while including final verdict and uncertainty',()=>{const d=dossier();d.options.response=d.review.conclusions.flatMap(c=>[c.verdict,c.uncertainty]).join('\n')+'\n先核对文本和对方确认进度。';good(d);});
for(const [name,mutate] of [
 ['wrong birth source path',d=>d.review.methods[0].claims[0].source_paths[0].path='/ziwei/gongs'],
 ['wrong birth source value',d=>d.review.methods[0].claims[0].source_paths[0].value='forged'],
 ['missing birth source paths',d=>delete d.review.methods[0].claims[0].source_paths],
 ['invalid birth source paths shape',d=>d.review.methods[0].claims[0].source_paths={}],
 ['unsafe birth source path',d=>d.review.methods[0].claims[0].source_paths[0].path='/bazi/__proto__/polluted'],
 ['conclusion citation not taken by linked method claim',d=>d.review.conclusions[0].bazi_evidence_ids=['E001']],
])test(`birth source binding: rejects ${name}`,()=>{const d=dossier('birth');mutate(d);syncPlan(d);bad(d);});
test('unclassified birth evidence is usable with exact own-method original source path',()=>{const d=dossier('birth');d.source.interpretation.evidence.find(e=>e.id==='E005').description='阶段结构';rebind(d);good(d);});
test('explicit birth ownership permits claims without extra source_paths',()=>{const d=dossier('birth');for(const reader of d.review.methods){const claim=reader.claims[0];delete claim.source_paths;for(const id of claim.evidence_ids)d.source.interpretation.evidence.find(e=>e.id===id).system=reader.method;}rebind(d);good(d);});
test('hash rejects whitespace-only rewrite of original file',()=>{const d=dossier();d.options.sourcePath=put('rewritten.json',JSON.stringify(d.source));bad(d);});
test('supported high same event can remain firm',()=>{const d=dossier();d.source.agreement={overall:'same',points:[],conflicts:[]};for(let i=0;i<d.source.conclusions.length;i++){Object.assign(d.source.conclusions[i],{agreement:'same',counter_evidence_ids:[],liuyao_level:'high',qimen_level:'high',delivery:'firm'});Object.assign(d.review.conclusions[i],{agreement:'same',counter_evidence_ids:[],liuyao_level:'high',qimen_level:'high',delivery:'firm'});Object.assign(d.review.resolutions[i],{relation:'same',retained_counter_evidence_ids:[],condition_evidence_ids:[]});for(const reader of d.review.methods)reader.claims[i].counter_evidence_ids=[];}rebind(d);good(d);});
test('unresolved cannot use a content-free uncertainty placeholder',()=>{const d=dossier();d.review.resolutions[0].relation='unresolved';Object.assign(d.review.conclusions[0],{delivery:'tentative',agreement:'conflict',uncertainty:'不确定'});d.options.response+='\n不确定';bad(d);});

for(const pkg of ['.','skill']){
 test(`${pkg}: public notes still resolve against original event source after reconciliation`,()=>{const d=dossier();const explanation='用神是这里指代所问事项的盘面线索。',application='这次用于核对推进所受的限制。';d.options.response+='\n'+explanation+application;d.options.publicNotes={schemaVersion:'laoshifu-public-notes.v1',items:[{term:'用神',explanation,application,sourcePath:'/conclusions/0/verdict',sourceValue:d.source.conclusions[0].verdict}]};const r=cli(d,pkg);assert.equal(r.status,0,r.stdout+r.stderr);d.options.publicNotes.items[0].sourceValue=d.review.conclusions[0].verdict;const wrong=cli(d,pkg);assert.equal(wrong.status,1);assert.match(wrong.stdout,/sourceValue|来源/);});
 test(`${pkg}: unresolved final response does not need the literal word 两种`,()=>{const d=dossier();d.review.resolutions[0].relation='unresolved';Object.assign(d.review.conclusions[0],{delivery:'tentative',agreement:'conflict'});const r=cli(d,pkg);assert.equal(r.status,0,r.stdout+r.stderr);});
 test(`${pkg}: review path never accepts malformed resolution by falling back`,()=>{const d=dossier();d.review.resolutions[0]=null;const r=cli(d,pkg);assert.equal(r.status,1,r.stdout+r.stderr);assert.match(r.stdout,/resolution/);});
}
test('evaluate never mutates caller-owned source, review or plan',()=>{const d=dossier('birth'),before=clone(d);good(d);assert.deepEqual(d,before);});
