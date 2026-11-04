'use strict';
/** Noun-occurrence audit. POS annotations require language review; no character-count fallback. */
const fs=require('node:fs'),crypto=require('node:crypto');
const lexicon=require('../references/terminology-lexicon.json');
const LIMIT_PERCENT=14;
const normalizeText=text=>text.replace(/\r\n?/g,'\n');
const key=text=>text.normalize('NFKD').replace(/\p{M}/gu,'').toLowerCase().replace(/\s+/gu,' ');
const aliases=[...new Set(lexicon.aliases.map(key))].sort((a,b)=>b.length-a.length);
const latinOrNumber=char=>!!char&&/[\p{Script=Latin}\p{N}]/u.test(char);
function recognizedTerms(value){
 const visible=value.replace(/!?\[([^\]]*)\]\([^)]*\)/g,'$1').replace(/https?:\/\/[^\s<>]+/g,'');
 const text=key(visible),marked=new Uint8Array(text.length),found=[];
 for(const term of aliases)for(let at=text.indexOf(term);at>=0;at=text.indexOf(term,at+term.length)){
  if(/[a-z]/.test(term)&&(latinOrNumber(text[at-1])||latinOrNumber(text[at+term.length])))continue;
  if(marked.subarray(at,at+term.length).some(Boolean))continue;
  marked.fill(1,at,at+term.length);found.push(term);
 }
 return found;
}
const counts=items=>{const m=new Map();for(const item of items)m.set(item,(m.get(item)||0)+1);return m;};
function measureTerminology(value,audit){
 if(typeof value!=='string')throw Error('Expected public prose as text');
 if(!audit||audit.schemaVersion!=='laoshifu-noun-audit.v1')throw Error('A reviewed noun audit is required; character ratios are not accepted');
 const text=normalizeText(value),chars=Array.from(text);
 const hash=crypto.createHash('sha256').update(text).digest('hex');
 if(audit.textSha256!==hash)throw Error('Noun audit text hash changed; review the current prose again');
 if(audit.coverage!=='all-noun-occurrences'||!['host-language-review','linguist-review','pos-tagger+review'].includes(audit.reviewedBy))throw Error('Noun annotation coverage and language-review provenance are required');
 if(typeof audit.language!=='string'||!audit.language.trim())throw Error('Noun audit language is required');
 if(!Array.isArray(audit.nouns)||audit.nouns.length>10000)throw Error('Noun annotations must be a bounded array');
 const annotatedTerms=[];let end=0,specialistNounCount=0;
 for(const noun of audit.nouns){
  if(!noun||!Number.isInteger(noun.start)||!Number.isInteger(noun.end)||noun.start<end||noun.start<0||noun.end<=noun.start||noun.end>chars.length)throw Error('Noun spans overlap or are out of order/range');
  if(!['NOUN','PROPN'].includes(noun.pos)||typeof noun.technical!=='boolean')throw Error('Each noun needs a NOUN/PROPN tag and technical classification');
  const surface=chars.slice(noun.start,noun.end).join('');
  if(!/[\p{L}\p{N}]/u.test(surface))throw Error('Punctuation or whitespace is not a noun');
  const known=recognizedTerms(surface);
  if(known.length&&!noun.technical)throw Error('Recognized specialist noun must be classified technical');
  if(known.length>1)throw Error('Separate technical noun occurrences must not be merged');
  annotatedTerms.push(...known);if(noun.technical)specialistNounCount++;end=noun.end;
 }
 const all=counts(recognizedTerms(text)),covered=counts(annotatedTerms);
 if(all.size!==covered.size||[...all].some(([term,n])=>covered.get(term)!==n))throw Error('Known specialist noun coverage is incomplete: unannotated term occurrence');
 const nounCount=audit.nouns.length;
 return {specialistNounCount,nounCount,percentage:nounCount?Number((100*specialistNounCount/nounCount).toFixed(4)):0,
  limitPercent:LIMIT_PERCENT,passes:!nounCount||specialistNounCount*100<nounCount*LIMIT_PERCENT,
  annotationSource:audit.reviewedBy,countingUnit:'noun occurrences; fixed multiword technical names count once'};
}
function nounAuditIssues(text,audit,language){
 if(!audit&&!language)return []; // Historical validator calls remain readable; current skill passes --language.
 try{
  if(language&&audit&&language.toLowerCase().split('-')[0]!==audit.language?.toLowerCase().split('-')[0])throw Error('Noun audit language does not match public language');
  const r=measureTerminology(text,audit);
  return r.passes?[]:['Specialist nouns '+r.specialistNounCount+'/'+r.nounCount+' = '+r.percentage+'%; required below 14% of nouns / 专业名词占全部名词须低于14%。'];
 }catch(error){return [error.message];}
}
module.exports={LIMIT_PERCENT,normalizeText,recognizedTerms,measureTerminology,nounAuditIssues};
if(require.main===module){
 try{
  const args=process.argv.slice(2),file=args.find(x=>x.startsWith('--file=')),audit=args.find(x=>x.startsWith('--audit='));
  if(!file||!audit||args.some(x=>x!==file&&x!==audit&&x!=='--json'))throw Error('Usage: node terminology-policy.cjs --file=prose.txt --audit=noun-audit.json [--json]');
  const r=measureTerminology(fs.readFileSync(file.slice(7),'utf8'),JSON.parse(fs.readFileSync(audit.slice(8),'utf8')));
  console.log(args.includes('--json')?JSON.stringify(r):(r.passes?'PASS':'FAIL')+' '+r.specialistNounCount+'/'+r.nounCount+' nouns ('+r.percentage+'%); required <14%');
  process.exitCode=r.passes?0:1;
 }catch(error){console.error(error.message);process.exitCode=2;}
}
