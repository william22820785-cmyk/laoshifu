'use strict';
const {test}=require('node:test');const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),crypto=require('node:crypto');
const {spawnSync}=require('node:child_process');const root=path.resolve(__dirname,'..');
const terms=require('../scripts/terminology-policy.cjs');
function audit(text,items){const chars=Array.from(text),surface=chars.join('');let next=0;return {
 schemaVersion:'laoshifu-noun-audit.v1',language:'en',coverage:'all-noun-occurrences',reviewedBy:'host-language-review',
 textSha256:crypto.createHash('sha256').update(text).digest('hex'),nouns:items.map(([word,technical=false])=>{
  const at=surface.indexOf(word,next);assert.ok(at>=0);next=at+word.length;
  return {start:Array.from(surface.slice(0,at)).length,end:Array.from(surface.slice(0,next)).length,pos:technical?'PROPN':'NOUN',technical};
 })};}
test('14 specialist noun occurrences among 100 nouns is rejected; 14 among 101 passes',()=>{
 const words=[...Array(14).fill('BaZi'),...Array(86).fill('garden')],text=words.join(' ');
 const a=audit(text,words.map(w=>[w,w==='BaZi']));const r=terms.measureTerminology(text,a);
 assert.equal(r.specialistNounCount,14);assert.equal(r.nounCount,100);assert.equal(r.percentage,14);assert.equal(r.passes,false);
 const longer=text+' garden';assert.equal(terms.measureTerminology(longer,audit(longer,[...words,'garden'].map(w=>[w,w==='BaZi']))).passes,true);
});
test('adjectives, verbs, adverbs, spaces and punctuation do not dilute the noun denominator',()=>{
 const text='BaZi '+('beautiful gently quickly changing! '.repeat(100));
 const r=terms.measureTerminology(text,audit(text,[['BaZi',true]]));
 assert.equal(r.nounCount,1);assert.equal(r.percentage,100);assert.equal(r.passes,false);
});
test('a fixed multiword technical name is one noun occurrence, not its character or word count',()=>{
 const text='Zi Wei Dou Shu garden river season friend home story question culture';
 const a=audit(text,[['Zi Wei Dou Shu',true],...['garden','river','season','friend','home','story','question','culture'].map(w=>[w])]);
 const r=terms.measureTerminology(text,a);assert.equal(r.nounCount,9);assert.equal(r.specialistNounCount,1);assert.equal(r.passes,true);
});
test('missing annotations, stale text, overlap and concealed known jargon fail closed',()=>{
 const text='BaZi garden';const good=audit(text,[['BaZi',true],['garden']]);
 assert.throws(()=>terms.measureTerminology(text),/noun/i);
 assert.throws(()=>terms.measureTerminology(text+' beautiful',good),/hash|changed/i);
 const falseLabel=structuredClone(good);falseLabel.nouns[0].technical=false;
 assert.throws(()=>terms.measureTerminology(text,falseLabel),/specialist|technical/i);
 const overlapping=structuredClone(good);overlapping.nouns[1].start=0;
 assert.throws(()=>terms.measureTerminology(text,overlapping),/overlap|order/i);
 const missing=structuredClone(good);missing.nouns.shift();
 assert.throws(()=>terms.measureTerminology(text,missing),/unannotated|coverage/i);
});
for(const folder of ['.','skill']){
 const policy=require(path.join(root,folder,'scripts/presentation-policy.cjs'));
 test(folder+': language-aware delivery requires a noun audit and never falls back to character ratios',()=>{
  assert.match(policy.nounAuditIssues('A garden.',null,'en').join(' '),/noun/i);
  const text='The garden has a tree.';assert.deepEqual(policy.nounAuditIssues(text,audit(text,[['garden'],['tree']]),'en'),[]);
 });
 test(folder+': shipped welcomes have reviewed noun ledgers below 14 percent',()=>{
  for(const lang of ['zh','en','es','pt']){
   const text=fs.readFileSync(path.join(root,folder,'references','CULTURAL-WELCOME.'+lang+'.md'),'utf8');
   const ledger=JSON.parse(fs.readFileSync(path.join(root,folder,'references','cultural-noun-audits',lang+'.json'),'utf8'));
   const score=terms.measureTerminology(text,ledger);assert.equal(score.passes,true);assert.ok(score.nounCount>15);
  }
 });
}
test('standalone checker requires noun annotations and does not change the source',()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'laoshifu-nouns-')),file=path.join(dir,'response.txt'),a=path.join(dir,'nouns.json');
 try{const text='BaZi garden';fs.writeFileSync(file,text);fs.writeFileSync(a,JSON.stringify(audit(text,[['BaZi',true],['garden']])));
  const r=spawnSync(process.execPath,[path.join(root,'scripts/terminology-policy.cjs'),'--file='+file,'--audit='+a,'--json'],{encoding:'utf8',windowsHide:true});
  assert.equal(r.status,1,r.stderr);assert.equal(JSON.parse(r.stdout).nounCount,2);assert.equal(fs.readFileSync(file,'utf8'),text);
 }finally{assert.equal(path.dirname(path.resolve(dir)),path.resolve(os.tmpdir()));fs.rmSync(dir,{recursive:true});}
});

for(const folder of ['.','skill'])for(const mode of ['birth','event']){
 test(folder+': '+mode+' CLI enforces the noun audit when the public language is set',()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'laoshifu-noun-cli-'));
  try{
   const response=path.join(dir,'response.txt'),ledger=path.join(dir,'noun-audit.json');
   const text='The garden has a tree.';fs.writeFileSync(response,text);fs.writeFileSync(ledger,JSON.stringify(audit(text,[['garden'],['tree']])));
   const script=mode==='birth'?'validate-consultation.cjs':'validate-liuyao-qimen-consultation.cjs';
   const args=[path.join(root,folder,'scripts',script),'--response='+response,'--language=en'];
   if(mode==='event'){
    const fusion=path.join(dir,'fusion.json');fs.writeFileSync(fusion,JSON.stringify({schemaVersion:'aceworld-liuyao-qimen-fusion.v3',stage:'restricted',question:{text:'synthetic'},conclusions:[],diagram:'',message:text}));args.push('--fusion='+fusion);
   }
   const missing=spawnSync(process.execPath,args,{encoding:'utf8',windowsHide:true});
   assert.equal(missing.status,1,missing.stdout+missing.stderr);assert.match(missing.stdout+missing.stderr,/noun audit/i);
   const complete=spawnSync(process.execPath,[...args,'--nounAudit='+ledger],{encoding:'utf8',windowsHide:true});
   assert.equal(complete.status,0,complete.stdout+complete.stderr);
  }finally{assert.equal(path.dirname(path.resolve(dir)),path.resolve(os.tmpdir()));fs.rmSync(dir,{recursive:true});}
 });
}
