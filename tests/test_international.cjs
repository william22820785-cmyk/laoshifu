'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const path=require('node:path');
for(const folder of ['.', 'skill']){
 const policy=require(path.resolve(__dirname,'..',folder,'scripts/presentation-policy.cjs'));
 test(folder+': ordinary English discussion of evidence is allowed',()=>{
  assert.deepEqual(policy.textIssues('The evidence is limited, so the signing deadline remains uncertain.'),[]);
  assert.deepEqual(policy.textIssues('Evidence: the signing deadline remains uncertain.'),[]);
 });
 test(folder+': internal evidence identifiers remain private',()=>{
  assert.ok(policy.textIssues('liuyao_evidence_ids: ly-01').length);
  assert.ok(policy.textIssues('evidence: [ly-01]').length);
  assert.ok(policy.textIssues('sourcePath: /interpretation/evidence/0').length);
 });
}

const fs=require('node:fs');
const os=require('node:os');
const {spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'..');
for(const lang of ['en','es','pt']){
 for(const kind of ['birth','contract']){
  test(lang+': translated '+kind+' result passes the full delivery validator',()=>{
   const base=path.join(root,'examples',kind);
   const source=path.join(base,'source.json');
   const review=JSON.parse(fs.readFileSync(path.join(base,'review.json'),'utf8'));
   const text=fs.readFileSync(path.join(root,'examples/translations',lang,kind+'.txt'),'utf8');
   const parts=text.trim().split('\n\n');
   const verdict=kind==='birth'?parts[1]:parts[3].split('\n')[0];
   const uncertainty=kind==='birth'?parts[4]:parts[3].split('\n').slice(1).join(' ');
   review.conclusions=review.conclusions.map(c=>({...c,verdict,uncertainty,timing:'',conditions:[],guidance:[]}));
   const temp=fs.mkdtempSync(path.join(os.tmpdir(),'laoshifu-language-'));
   try{
    const reviewPath=path.join(temp,'review.json'),responsePath=path.join(temp,'response.txt');
    fs.writeFileSync(reviewPath,JSON.stringify(review));
    let response=text;
    const args=[];
    if(kind==='contract'){
     const diagram=spawnSync('python',[path.join(root,'scripts/diagram_render.py'),'--fusion='+source,'--text'],{encoding:'utf8',windowsHide:true});
     assert.equal(diagram.status,0,diagram.stderr);
     const disclosure=JSON.parse(fs.readFileSync(source,'utf8')).timeBasisDisclosure||'';
     response=diagram.stdout.trimEnd()+'\n'+response+'\n'+disclosure;
     args.push('--fusion='+source,'--diagramMode=text');
    }else{
     const plan=JSON.parse(fs.readFileSync(path.join(base,'plan.json'),'utf8'));
     plan.conclusions=review.conclusions;
     const planPath=path.join(temp,'plan.json');fs.writeFileSync(planPath,JSON.stringify(plan));
     args.push('--chart='+source,'--plan='+planPath);
    }
    fs.writeFileSync(responsePath,response);
    const validator=kind==='birth'?'validate-consultation.cjs':'validate-liuyao-qimen-consultation.cjs';
    const result=spawnSync(process.execPath,[path.join(root,'scripts',validator),...args,'--review='+reviewPath,'--response='+responsePath,'--detail=deep'],{encoding:'utf8',windowsHide:true});
    assert.equal(result.status,0,result.stdout+result.stderr);
   }finally{
    assert.equal(path.dirname(path.resolve(temp)),path.resolve(os.tmpdir()));
    fs.rmSync(temp,{recursive:true});
   }
  });
 }
}
