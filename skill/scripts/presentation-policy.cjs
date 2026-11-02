/** V4.1 public explanation contract: source facts, plain-language gloss, no scoring dump. */
const fs = require('node:fs');
const INTERNAL_TERMS = ['evidence','sourcePath','sourceValue','schemaVersion','内部等级','算法版本','融合权重','加权评分','推断链','推断结构','skill-root','consultation-plan','chart.json','fusion.json','后台评分','九宫格'];
const UNSUPPORTED_PROMISES = ['保证准确','百分之百准确','保证应验','百算百准','稳赚不赔','包你发财','必有灾祸','不买就会倒霉'];
const GLOSSARY_TERMS = ['日主','十神','旺衰','用神','忌神','喜用','官禄宫','夫妻宫','命宫','四化','化禄','化忌','世爻','应爻','父母爻','官鬼爻','妻财爻','动爻','空亡','回头生','回头克','伏神','值符','值使','生门','开门'];
const LIMITS = {brief:650,standard:1800,deep:3600};
const plain = v => v !== null && typeof v === 'object' && !Array.isArray(v);
const nonempty = v => typeof v === 'string' && v.trim().length > 0;
const normalize = s => s.replace(/\r\n?/g,'\n');
function readText(file) { const text=normalize(fs.readFileSync(file,'utf8').replace(/^\uFEFF/,'')); if(!text.trim()) throw Error('文本为空'); return text; }
function readJSON(file) { return JSON.parse(readText(file)); }
function args(argv=process.argv.slice(2)) {
 const result={}; for(let i=0;i<argv.length;i++){const m=/^--([\w-]+)(?:=(.*))?$/.exec(argv[i]);if(!m)throw Error('非法参数');result[m[1]]=m[2]===undefined?argv[++i]:m[2];if(!result[m[1]]||result[m[1]].startsWith('--'))throw Error('参数缺少值: '+m[1]);}return result;
}
function textIssues(text,detail='standard') {
 const errors=[];
 if(!(detail in LIMITS))return ['detail 必须是 brief|standard|deep'];
 if(!text.trim())errors.push('答复不能为空');
 if([...text].length>LIMITS[detail])errors.push(`答复超过 ${detail} 上限 ${LIMITS[detail]} 字符`);
 for(const t of INTERNAL_TERMS)if(text.toLowerCase().includes(t.toLowerCase()))errors.push('泄露内部实现: '+t);
 for(const t of UNSUPPORTED_PROMISES){
  for(let at=text.indexOf(t);at>=0;at=text.indexOf(t,at+1)){
   const prefix=text.slice(Math.max(0,at-8),at);
   if(!/(不|不会|无法|不能|并非|不是|从不|绝不|不承诺|不得|不应)$/.test(prefix))errors.push('无依据的保证或恐吓: '+t);
  }
 }
 if(/准确率\s*(?:达到|高达|为|[:：])\s*\d+\s*%/.test(text))errors.push('不得捏造准确率');
 return errors;
}
function resolvePointer(source,pointer) {
 if(typeof pointer!=='string'||!pointer.startsWith('/'))return undefined;
 let value=source;
 for(const raw of pointer.slice(1).split('/')){
  const key=raw.replace(/~1/g,'/').replace(/~0/g,'~');
  if(['__proto__','prototype','constructor'].includes(key)||value===null||typeof value!=='object'||!Object.hasOwn(value,key))return undefined;
  value=value[key];
 }
 return value;
}
function noteIssues(text,source,notes) {
 const terminologyText=text.replaceAll('开门见山','直说');
 const found=GLOSSARY_TERMS.filter(t=>terminologyText.includes(t));
 if(!notes)return found.length?['正文有术语，需 --publicNotes 记录真实来源与解释: '+found.join('、')]:[];
 if(!plain(notes)||notes.schemaVersion!=='laoshifu-public-notes.v1'||!Array.isArray(notes.items)||notes.items.length>8)return ['publicNotes 结构非法'];
 const errors=[],seen=new Set();
 for(const [i,n] of notes.items.entries()){
  const label=`publicNotes.items[${i}]`;
  if(!plain(n)){errors.push(label+' 必须为对象');continue;}
  if(!nonempty(n.term)||!nonempty(n.explanation)||!nonempty(n.application)||!nonempty(n.sourcePath)){errors.push(label+' 缺少 term/explanation/application/sourcePath');continue;}
  if(seen.has(n.term))errors.push(label+' 术语重复');seen.add(n.term);
  if(!text.includes(n.term)||!text.includes(n.explanation)||!text.includes(n.application))errors.push(label+' 术语、解释或现实落点未出现在正文');
  if(n.explanation.trim().length<8)errors.push(label+' 口语解释过短');
  const actual=resolvePointer(source,n.sourcePath);
  const scalar=['string','number','boolean'];
  if(actual===undefined||!scalar.includes(typeof actual)||actual!==n.sourceValue)errors.push(label+' 来源路径不存在或 sourceValue 与实际盘面不一致');
  errors.push(...textIssues(n.explanation+' '+n.application,'deep'));
 }
 for(const t of found)if(!seen.has(t))errors.push('术语缺少对应解释记录: '+t);
 return errors;
}
module.exports={INTERNAL_TERMS,GLOSSARY_TERMS,LIMITS,plain,nonempty,normalize,readText,readJSON,args,textIssues,noteIssues,resolvePointer};
