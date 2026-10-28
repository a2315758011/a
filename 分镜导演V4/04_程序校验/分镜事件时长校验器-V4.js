#!/usr/bin/env node
'use strict';
// AI 分镜 V4：镜头时码 + 人物/道具事件区间的可执行审计。
// 输入是人工/AI从已确认分镜提取的结构化事件，不对普通中文稿假装“自动理解”。
const fs=require('fs');
function validate(data) {
  const errors=[], warnings=[];
  const fail=(code,at,detail)=>errors.push({code,at,detail});
  const warn=(code,at,detail)=>warnings.push({code,at,detail});
  const num=(v)=>Number.isFinite(v);
  const episodes=data.episodes||[];
  if (!Array.isArray(episodes)||episodes.length===0) fail('T00','root','缺 episodes[]');
  for (const ep of episodes) {
    const id=ep.id||'?';const start=ep.start_ms,end=ep.end_ms;
    if (!num(start)||!num(end)||end<=start){fail('T01',id,'集时间区间非法');continue;}
    const shots=ep.shots||[], events=ep.events||[];
    if (!Array.isArray(shots)||!Array.isArray(events)){fail('T00',id,'shots/events 应为数组');continue;}
    const seenShot=new Set(),seenEvent=new Set();
    let cursor=start;
    for (const s of shots) {
      const tag=id+'/'+s.id;
      if(seenShot.has(s.id))fail('T02',tag,'重复镜号');seenShot.add(s.id);
      if(!num(s.start_ms)||!num(s.end_ms)||s.end_ms<=s.start_ms) {fail('T01',tag,'镜头时间无效');continue;}
      if(s.start_ms!==cursor)fail('T03',tag,'镜头有空档/重叠，预计起点 '+cursor+' 实际 '+s.start_ms);
      if(s.start_ms<start||s.end_ms>end)fail('T04',tag,'镜头超出集范围');
      cursor=s.end_ms;
    }
    if(cursor!==end)fail('T03',id,'末镜时间 '+cursor+' 不等于集结束 '+end);
    const byId=new Map();
    for(const e of events){
      const tag=id+'/'+e.id;
      if(!e.id||seenEvent.has(e.id))fail('T02',tag,'事件ID缺失/重复');
      seenEvent.add(e.id);byId.set(e.id,e);
      if(!num(e.start_ms)||!num(e.end_ms)||e.end_ms<=e.start_ms){fail('T01',tag,'事件区间非法');continue;}
      if(e.start_ms<start||e.end_ms>end)fail('T04',tag,'事件超出集范围');
      if(num(e.min_duration_ms)&&e.end_ms-e.start_ms<e.min_duration_ms){
        if(e.duration_status==='measured'||e.duration_status==='hard_constraint')fail('T05',tag,'事件'+(e.end_ms-e.start_ms)+'ms 小于已测量/硬约束最小时长 '+e.min_duration_ms+'ms');
        else warn('W04',tag,'事件短于估算阈值；转 NEEDS_REVIEW，不把估算冒充硬性实测失败');
      }
      if(e.duration_status!=='measured'&&e.duration_status!=='hard_constraint'&&e.min_duration_ms!==undefined)warn('W01',tag,'最小时长未标 measured；此数值只能用于候选预估，不能视为实测');
      if(e.requires_visible===true){
        const covers=shots.some(s=>s.events_visible?.includes(e.id)&&s.start_ms<e.end_ms&&s.end_ms>e.start_ms);
        if(!covers)fail('T06',tag,'关键事件未有可观察镜头证据');
      }
      if(num(e.shown_count)&&num(e.min_per_person_ms)&&e.presentation==='sequential_visible'){
        const required=e.shown_count*e.min_per_person_ms;
        if(e.end_ms-e.start_ms<required){
          if(e.duration_status==='measured'||e.duration_status==='hard_constraint')fail('T07',tag,'逐人可见动作需要至少 '+required+'ms；当前 '+(e.end_ms-e.start_ms)+'ms');
          else warn('W05',tag,'逐人可见展示负载超过估算窗口；转 NEEDS_REVIEW，需实测/导演改为蒙太奇或群像锚点');
        }
      }
      if(e.presentation==='montage'&&e.shown_count>1 && !e.montage_explanation)warn('W02',tag,'蒙太奇需说明其是省略展示，不代表逐人完整拍摄');
    }
    for(const e of events){
      for(const dep of e.requires||[]){
        const prior=byId.get(dep);
        if(!prior){fail('T08',id+'/'+e.id,'缺依赖事件 '+dep);continue;}
        if(num(prior.end_ms)&&num(e.start_ms)&&prior.end_ms>e.start_ms)fail('T09',id+'/'+e.id,'前置事件 '+dep+' 未完成；结束 '+prior.end_ms+'，本事件开始 '+e.start_ms);
      }
    }
    const overlaps=(a,b)=>a.start_ms<b.end_ms&&b.start_ms<a.end_ms;
    for(let i=0;i<events.length;i++)for(let j=i+1;j<events.length;j++){
      const a=events[i],b=events[j];
      if(!num(a.start_ms)||!num(a.end_ms)||!num(b.start_ms)||!num(b.end_ms)||!overlaps(a,b))continue;
      const common=(a.actor_ids||[]).filter(x=>(b.actor_ids||[]).includes(x));
      if(common.length && (a.exclusive===true||b.exclusive===true) &&
         !(a.compatible_with||[]).includes(b.id) && !(b.compatible_with||[]).includes(a.id)){
        fail('T10',id+'/'+a.id+'+'+b.id,'人物 '+common.join(',')+' 的排他事件重叠');
      }
      const shared=(a.exclusive_resources||[]).filter(x=>(b.exclusive_resources||[]).includes(x));
      if(shared.length)fail('T11',id+'/'+a.id+'+'+b.id,'独占道具/机构 '+shared.join(',')+' 同时被占用');
    }
    for(const e of events.filter(e=>e.continuous_hold===true)){
      if(!(e.exclusive===true||e.hold_can_coexist===true))warn('W03',id+'/'+e.id,'持续操作应声明是否排他，不能默认可同时战斗');
      if(e.engagement_event_id){
        const latch=byId.get(e.engagement_event_id);
        if(!latch)fail('T08',id+'/'+e.id,'未找到机关接合事件');
        else if(num(latch.end_ms)&&latch.end_ms>e.start_ms)fail('T12',id+'/'+e.id,'持续压闸开始早于接合完成');
      }
    }
  }
  return {ok:errors.length===0,errors,warnings,episodes_checked:episodes.length};
}
if(require.main===module){
  const file=process.argv[2];if(!file){console.error('用法: node 分镜事件时长校验器-V4.js <事件账本.json>');process.exit(2);}
  try {const x=JSON.parse(fs.readFileSync(file,'utf8'));const tests=Array.isArray(x.cases)?x.cases:[{id:'input',data:x}];let mismatch=0;
    for(const t of tests){const got=validate(t.data||t),codes=[...new Set(got.errors.map(e=>e.code))].sort();
      const expected=(t.expected_errors||[]).slice().sort();
      const warningCodes=[...new Set(got.warnings.map(w=>w.code))].sort();
      const expectedWarnings=(t.expected_warnings||[]).slice().sort();
      // Assert warning expectations too; previously expected_warnings in fixtures were silently ignored.
      const errorsMatch=(!('expected_errors' in t)||JSON.stringify(codes)===JSON.stringify(expected));
      const warningsMatch=(!('expected_warnings' in t)||JSON.stringify(warningCodes)===JSON.stringify(expectedWarnings));
      const pass=errorsMatch&&warningsMatch;
      if(!pass || (!('expected_errors' in t) && !got.ok)) mismatch++;
      console.log(JSON.stringify({case:t.id||'input',pass,ok:got.ok,codes,expected:('expected_errors' in t)?expected:undefined,warningCodes,expectedWarnings:('expected_warnings' in t)?expectedWarnings:undefined,errors:got.errors,warnings:got.warnings},null,2));
    }process.exit(mismatch?1:0);
  }catch(e){console.error('校验异常: '+e.message);process.exit(2);}
}
module.exports={validate};