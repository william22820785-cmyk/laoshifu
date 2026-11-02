#!/usr/bin/env node
/** V4.1 event delivery validator: structured result, exact diagram, grounded public gloss. */
const P=require('./presentation-policy.cjs');
const {evaluate}=require('./dual-review.cjs');
const {spawnSync}=require('node:child_process');
const path=require('node:path');
const HEDGE_WORDS=['大概率','可能','也许','或许','多半','不一定','说不准','难说','未必','倾向于'];
const RESIDUAL_WORDS=['多半','可能','取决于','要看','不算板上钉钉','留有余地'];
function containsAny(text,words){return words.some(word=>text.includes(word));}
function evidenceIssues(f){
 const errors=[],registry=new Map();
 const items=Array.isArray(f.evidence)?f.evidence:[];
 if(!items.length)errors.push('evidence 判据清单为空，等于没有可回指的盘面依据');
 for(const [i,item] of items.entries()){
  const label=`evidence[${i}]`;
  if(!P.plain(item)){errors.push(label+' 不是对象');continue;}
  if(!P.nonempty(item.id)){errors.push(label+' 缺少 id');continue;}
  if(registry.has(item.id))errors.push('判据编号重复: '+item.id);
  registry.set(item.id,item);
  if(!['liuyao','qimen'].includes(item.system))errors.push(label+' system 非法');
  for(const key of ['label','kind'])if(!P.nonempty(item[key]))errors.push(label+'.'+key+' 缺失');
  const actual=P.resolvePointer(f,item.sourcePath);
  if(actual===undefined)errors.push(label+' sourcePath 无法回指本次盘面');
  else if(actual!==item.value)errors.push(label+' value 与盘面字段不一致');
 }
 return {errors,registry};
}
function timeBasisIssues(f){
 const errors=[];
 if(!['local','beijing'].includes(f.timeBasis))errors.push('timeBasis 必须是 local 或 beijing');
 if(!P.plain(f.basisComparison))errors.push('basisComparison 缺失');
 else if(f.basisComparison.diverges&&!P.nonempty(f.timeBasisDisclosure))
  errors.push('当地与北京四柱存在差异时必须给出 timeBasisDisclosure');
 return errors;
}
function verifiedDiagramProse(args) {
 const script=path.join(__dirname,'diagram_render.py');
 const command=[script,'--verify',`--fusion=${args.fusion}`,`--response=${args.response}`,`--mode=${args.diagramMode||'image'}`];
 if(args.diagramBundle)command.push(`--bundle=${args.diagramBundle}`);
 const configured=process.env.PYTHON||process.env.PYTHON3;
 const candidates=configured?[configured]:(process.platform==='win32'?['python','python3']:['python3','python']);
 for(const python of candidates){
  const result=spawnSync(python,command,{encoding:'utf8',timeout:30000,maxBuffer:2*1024*1024,
   env:{...process.env,PYTHONUTF8:'1',PYTHONIOENCODING:'utf-8'},windowsHide:true});
  if(result.error?.code==='ENOENT')continue;
  if(result.error)throw Error('卦图核验无法完成: '+result.error.message);
  if(result.status!==0)throw Error((result.stderr||result.stdout||'卦图核验失败').trim());
  const output=JSON.parse(result.stdout);
  if(typeof output.prose!=='string')throw Error('卦图核验未返回正文');
  return output.prose;
 }
 throw Error('未找到Python；请设置PYTHON为已有Python可执行文件路径');
}
function validate(f,response,notes,detail,args){
 const errors=[];
 if(!P.plain(f))return ['fusion 必须是对象'];
 const original=f;
 if(args.review){
  const result=evaluate(original,P.readJSON(args.review),{kind:'event',sourcePath:args.fusion,response});
  if(result.errors.length)return result.errors;
  f={...original,conclusions:result.conclusions,agreement:result.agreement};
 }
 const SUPPORTED_VERSIONS=['aceworld-liuyao-qimen-fusion.v2','aceworld-liuyao-qimen-fusion.v3'];
 const isCurrent=f.schemaVersion==='aceworld-liuyao-qimen-fusion.v3';
 if(!SUPPORTED_VERSIONS.includes(f.schemaVersion))errors.push('schemaVersion 不匹配');
 else if(!isCurrent)console.log('[NOTE] 旧版 v2 结果按历史规则复核；新结果应为 v3');
 const reading=['reading','calibration','deepening','closure','conclusion'];
 if(![...reading,'restricted','rejected'].includes(f.stage))errors.push('stage 非法');
 if(!P.plain(f.question)||!P.nonempty(f.question.text))errors.push('question.text 必须非空');
 if(!Array.isArray(f.conclusions))errors.push('conclusions 必须是数组');
 if(typeof f.diagram!=='string')errors.push('diagram 必须是字符串');
 if(errors.length)return errors;
 if(['restricted','rejected'].includes(f.stage)){
  if(f.conclusions.length||f.diagram)errors.push('拒答/受限不得附带结论或卦图');
  if(f.methods||f.agreement||Object.hasOwn(f,'diagramData')||args.diagramBundle)errors.push('拒答/受限不得附带盘面');
  if(!P.nonempty(f.message))errors.push('拒答/受限需 message');
  return errors.concat(P.textIssues(response,detail));
 }
 if(!P.plain(f.methods)||!P.plain(f.methods.liuyao)||!P.plain(f.methods.qimen))errors.push('methods.liuyao/qimen 必须是对象');
 const agreements=['same','complementary','conflict'];
 if(!P.plain(f.agreement)||!agreements.includes(f.agreement.overall))errors.push('agreement.overall 非法');
 if(!f.conclusions.length||f.conclusions.length>4)errors.push('reading 需1-4条结论');
 let registry=new Map();
 if(isCurrent){
  errors.push(...timeBasisIssues(f));
  const evidenceChecks=evidenceIssues(f);
  errors.push(...evidenceChecks.errors);
  registry=evidenceChecks.registry;
  if(!P.plain(f.question))errors.push('question 必须是对象');
  else for(const key of ['desiredOutcome','knownContext'])
   if(!Object.hasOwn(f.question,key))errors.push('question.'+key+' 缺失');
  const points=Array.isArray(f.agreement?.points)?f.agreement.points:[];
  if(!points.length)errors.push('agreement.points 不能为空');
  for(const [i,p] of points.entries())
   if(!P.nonempty(p?.detail))errors.push(`agreement.points[${i}].detail 不能为空`);
 }
 const ids=new Set();
 for(const [i,c] of f.conclusions.entries()){
  const label=`conclusions[${i}]`;
  if(!P.plain(c)){errors.push(label+' 不是对象');continue;}
  for(const k of ['id','verdict'])if(!P.nonempty(c[k]))errors.push(label+'.'+k+' 缺失');
  if(ids.has(c.id))errors.push('重复结论ID');ids.add(c.id);
  if(!['firm','probable','tentative'].includes(c.delivery))errors.push(label+' delivery非法');
  for(const k of ['liuyao_level','qimen_level'])if(!['high','medium','low','none'].includes(c[k]))errors.push(label+' '+k+'非法');
  if(!agreements.includes(c.agreement))errors.push(label+' agreement非法');
  for(const k of ['conditions','guidance','liuyao_evidence_ids','qimen_evidence_ids','counter_evidence_ids']){
   if(!Array.isArray(c[k])||c[k].some(x=>typeof x!=='string'))errors.push(label+' '+k+'必须是字符串数组');
  }
  if(typeof c.timing!=='string')errors.push(label+' timing必须是字符串');
 const counter=Array.isArray(c.counter_evidence_ids)&&c.counter_evidence_ids.length>0;
 if(c.agreement==='same'&&counter)errors.push(label+' same与反证矛盾');
 const same=f.agreement?.overall==='same'&&c.agreement==='same';
 const doubleHigh=same&&c.liuyao_level==='high'&&c.qimen_level==='high'&&!counter;
 const weak=c.liuyao_level==='low'||c.qimen_level==='low'||c.agreement==='conflict'||counter;
  if(isCurrent){
   if(!args.review&&doubleHigh&&c.id==='outcome'&&c.delivery!=='firm')errors.push(label+' 双高同向且无反证时应给出firm');
   if(c.delivery==='firm'&&!doubleHigh)errors.push(label+' 说死(firm)需两法都high、方向一致且无反证');
   if(!args.review&&c.delivery==='probable'&&weak)errors.push(label+' 依据偏弱或相左时应降为tentative');
   const referenced=[...(c.liuyao_evidence_ids||[]),...(c.qimen_evidence_ids||[]),...(c.counter_evidence_ids||[])];
   if(!referenced.length)errors.push(label+' 未引用任何盘面判据');
   for(const evidenceId of referenced)if(!registry.has(evidenceId))errors.push(label+' 引用了不存在的判据: '+evidenceId);
   const ly=new Set(c.liuyao_evidence_ids||[]),qm=new Set(c.qimen_evidence_ids||[]);
   if(ly.size&&qm.size&&[...ly].every(id=>qm.has(id))&&ly.size===qm.size)
    errors.push(label+' 两法引用同一组判据编号，等于没有分别取证');
   const verdict=P.normalize(String(c.verdict||''));
   if(c.delivery==='firm'&&containsAny(verdict,HEDGE_WORDS))errors.push(label+' 说死档不得出现含糊措辞');
   if(!args.review&&c.delivery==='probable'&&!containsAny(verdict,RESIDUAL_WORDS))errors.push(label+' 留余地档必须写出余地或条件');
   if(!args.review&&c.delivery==='tentative'&&!verdict.includes('两种'))errors.push(label+' 依据弱或相左时必须并列两种可能');
  }else{
   if(doubleHigh&&c.delivery!=='firm')errors.push(label+' 双高同向需firm');
   if(c.delivery==='firm'&&weak)errors.push(label+' 弱依据/冲突不能firm');
  }
}
 if(f.agreement?.overall==='same'&&Array.isArray(f.agreement.conflicts)&&f.agreement.conflicts.length)errors.push('overall=same但conflicts非空');
 let prose=response;
 if(Object.hasOwn(f,'diagramData')||args.diagramBundle||args.diagramMode){
  try{prose=verifiedDiagramProse(args);}catch(e){errors.push(e.message);return errors;}
 }else{
  // Historical v2 files remain verifiable; new engine output cannot use this branch.
  const diagram=P.normalize(f.diagram);
  if(!diagram.trim()||!response.includes(diagram))errors.push('答复缺少原样卦图（允许LF/CRLF差异）');
  prose=diagram?response.replace(diagram,''):response;
 }
errors.push(...P.textIssues(prose,detail),...P.noteIssues(prose,original,notes));
 if(P.nonempty(f.timeBasisDisclosure)&&!response.includes(P.normalize(f.timeBasisDisclosure)))
  errors.push('答复缺少时基披露原文: '+f.timeBasisDisclosure);
 return errors;
}
try{
 const args=P.args();
 if(!args.fusion||!args.response)throw Error('必须提供 --fusion 和 --response');
 const f=P.readJSON(args.fusion),response=P.readText(args.response);
 const notes=args.publicNotes?P.readJSON(args.publicNotes):null;
 const errors=validate(f,response,notes,args.detail||'standard',args);
 if(errors.length){console.log('[FAIL] '+errors.join('\n'));process.exitCode=1;}
 else console.log('[PASS] 六爻+奇门详解交付校验通过（来源匹配不等于解读正确或预测准确）');
}catch(e){console.error('[FAIL] '+e.message);process.exitCode=1;}
