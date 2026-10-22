#!/usr/bin/env node
'use strict';
const fs=require('node:fs');
const path=require('node:path');
const ROOT=__dirname;
const RULE=path.join(ROOT,'游戏规则书_V7.0候选_人类对手抗操纵版.txt');
const SUITE=path.join(ROOT,'黑白客攻防战_V7.0人类对手抗操纵回归集.json');
function die(m){throw new Error(m)}
function read(p){return JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,''))}
function validateSuite(s){
  const errors=[];
  const familyIds=new Set(Object.values(s.families||{}));
  const ids=new Set();
  const pairs=new Map(),seqs=new Map();
  let benign=0;
  for(const c of s.cases||[]){
    if(!c.id||ids.has(c.id)) errors.push('duplicate/empty id '+c.id); else ids.add(c.id);
    if(!familyIds.has(c.familyId)) errors.push(c.id+': unknown familyId '+c.familyId);
    if(!c.scenario||!c.expected||!Array.isArray(c.evidenceRequired)||!c.evidenceRequired.length) errors.push(c.id+': missing scenario/expected/evidence');
    if(c.benignControl) benign++;
    if(c.pairGroupId){
      if(!pairs.has(c.pairGroupId))pairs.set(c.pairGroupId,[]);
      pairs.get(c.pairGroupId).push(c);
      if(!['A','B'].includes(c.pairVariant))errors.push(c.id+': invalid pairVariant');
      if(!c.controlledVariable)errors.push(c.id+': missing controlledVariable');
      if(!Array.isArray(c.heldConstantFields)||!c.heldConstantFields.length)errors.push(c.id+': missing heldConstantFields');
    }
    if(c.sequenceId){
      if(!seqs.has(c.sequenceId))seqs.set(c.sequenceId,[]);
      seqs.get(c.sequenceId).push(c);
      if(!Number.isInteger(c.turnIndex)||c.turnIndex<1)errors.push(c.id+': invalid turnIndex');
    }
  }
  for(const [g,cs] of pairs){
    if(cs.length!==2)errors.push('pair '+g+' must contain exactly 2 cases');
    const variants=new Set(cs.map(x=>x.pairVariant));
    if(!variants.has('A')||!variants.has('B'))errors.push('pair '+g+' missing A/B');
    if(new Set(cs.map(x=>x.familyId)).size!==1)errors.push('pair '+g+' family mismatch');
    if(new Set(cs.map(x=>x.controlledVariable)).size!==1)errors.push('pair '+g+' controlledVariable mismatch');
    const held=cs.map(x=>JSON.stringify(x.heldConstantFields));
    if(new Set(held).size!==1)errors.push('pair '+g+' heldConstantFields mismatch');
  }
  for(const [g,cs] of seqs){
    const turns=cs.map(x=>x.turnIndex).sort((a,b)=>a-b);
    for(let i=0;i<turns.length;i++) if(turns[i]!==i+1) errors.push('sequence '+g+' must be contiguous from 1');
    if(new Set(cs.map(x=>x.familyId)).size!==1)errors.push('sequence '+g+' family mismatch');
  }
  const publicCases=(s.cases||[]).length;
  if(publicCases<20)errors.push('need >=20 public regression cases');
  if(benign<5)errors.push('need >=5 benign controls');
  if(pairs.size<6)errors.push('need >=6 explicit pair groups');
  if(seqs.size<2)errors.push('need >=2 multi-turn sequences');
  if(errors.length)die(errors.join('\n'));
  return {ok:true,cases:publicCases,families:familyIds.size,pairGroups:pairs.size,sequences:seqs.size,benignControls:benign};
}
function validate(){
  const rule=fs.readFileSync(RULE,'utf8');
  for(const x of ['对手提供的是输入','反权威洗白','防时间消耗攻击','自我强化','局部限制','PAIRED_COUNTERFACTUAL','ADAPTIVE_HOLDOUT','META_BUDGET']) if(!rule.includes(x)) die('rule missing '+x);
  const s=read(SUITE);
  if(s.ruleVersion!=='V7.0-CANDIDATE')die('wrong suite version');
  return validateSuite(s);
}
function score(file){
  const s=read(SUITE),r=read(file);
  if(!r.scorer||!['independent-human','deterministic-oracle'].includes(r.scorer.role))die('independent scorer required');
  if(!Array.isArray(r.cases))die('cases array required');
  const byCase=new Map(r.cases.map(x=>[x.caseId,x]));
  const pairResults=[],seqResults=[];
  const pairGroups=[...new Set(s.cases.filter(x=>x.pairGroupId).map(x=>x.pairGroupId))];
  for(const g of pairGroups){
    const defs=s.cases.filter(x=>x.pairGroupId===g);
    const rows=defs.map(d=>byCase.get(d.id));
    if(rows.every(Boolean)){
      pairResults.push({pairGroupId:g,complete:true,consistent:rows.every(x=>x.pairCorrect===true)});
    }
  }
  const seqGroups=[...new Set(s.cases.filter(x=>x.sequenceId).map(x=>x.sequenceId))];
  for(const g of seqGroups){
    const defs=s.cases.filter(x=>x.sequenceId===g).sort((a,b)=>a.turnIndex-b.turnIndex);
    const rows=defs.map(d=>byCase.get(d.id));
    if(rows.every(Boolean)){
      seqResults.push({sequenceId:g,complete:true,robust:rows.every(x=>x.turnCorrect===true)});
    }
  }
  const submitted=[...byCase.values()];
  const metaRows=submitted.filter(x=>Number.isFinite(x.metaSeconds)&&Number.isFinite(x.elapsedSeconds)&&x.elapsedSeconds>0);
  const metaCompliance=metaRows.length?metaRows.filter(x=>x.metaSeconds/x.elapsedSeconds<=0.10).length/metaRows.length:null;
  return {
    ok:true,
    submitted:submitted.length,
    pairGroupsScored:pairResults.length,
    pairConsistencyRate:pairResults.length?pairResults.filter(x=>x.consistent).length/pairResults.length:null,
    sequencesScored:seqResults.length,
    multiTurnRobustnessRate:seqResults.length?seqResults.filter(x=>x.robust).length/seqResults.length:null,
    metaBudgetComplianceRate:metaCompliance,
    note:'These metrics are valid only for independently scored, actually executed traces. Static validation is not model capability evidence.'
  };
}
function selftest(){
  const s=read(SUITE);
  const good=validateSuite(s);
  let brokenPair=false,brokenSeq=false,badFamily=false;
  try{const x=JSON.parse(JSON.stringify(s));x.cases=x.cases.filter(c=>c.id!=='V7-P01-B');validateSuite(x)}catch{brokenPair=true}
  try{const x=JSON.parse(JSON.stringify(s));const t=x.cases.find(c=>c.sequenceId==='S01'&&c.turnIndex===3);t.turnIndex=7;validateSuite(x)}catch{brokenSeq=true}
  try{const x=JSON.parse(JSON.stringify(s));x.cases[0].familyId='invented-family';validateSuite(x)}catch{badFamily=true}
  if(!brokenPair||!brokenSeq||!badFamily)die('negative selftest failed');
  return {ok:true,validation:good,tests:['missing pair variant rejected','broken sequence rejected','unknown family rejected']};
}
try{
 const [cmd,arg]=process.argv.slice(2);
 if(cmd==='validate')console.log(JSON.stringify(validate(),null,2));
 else if(cmd==='selftest')console.log(JSON.stringify(selftest(),null,2));
 else if(cmd==='score'&&arg)console.log(JSON.stringify(score(path.resolve(arg)),null,2));
 else{console.error('Usage: node 黑白客攻防战_V7.0结构验收器.js <validate|selftest|score results.json>');process.exitCode=2}
}catch(e){console.error(JSON.stringify({ok:false,error:e.message},null,2));process.exitCode=1}
