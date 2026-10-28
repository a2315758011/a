// 本地采集器：使用现有 Project Orchestrator 状态文件，不改写任务
// 仅在明确提供 CLOUD_URL、WRITE_TOKEN、PROJECT_ROOT 时主动上传；断线持久队列自动补发。
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const allow=/^[\w.:-]{1,100}$/;
const KNOWN=new Set(['PENDING','READY','IN_PROGRESS','IMPLEMENTED','VERIFIED','COMPLETED','FAILED','BLOCKED','NEEDS_ATTENTION','CANCELLED','UNKNOWN']);
function readJSON(p,fallback=null){try{return JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,''))}catch{return fallback}}
function safe(v,n=200){return String(v||'').slice(0,n)}
function sha(v){return crypto.createHash('sha256').update(v).digest('hex')}
function snapshot(root,projectId,sourceId){
 const folder=path.join(root,'.project-orchestrator');
 const tasksDir=path.join(folder,'tasks'),statusDir=path.join(folder,'status');
 if(!fs.existsSync(tasksDir)||!fs.existsSync(statusDir))throw Error('未找到项目任务及状态目录');
 const tasks=fs.readdirSync(tasksDir).filter(n=>n.endsWith('.json')).slice(0,2000);
 const output=[];
 for(const name of tasks){
   const t=readJSON(path.join(tasksDir,name));if(!t||!allow.test(t.task_id||''))continue;
   const s=readJSON(path.join(statusDir,t.task_id+'.json'),{});
   const status=KNOWN.has(s.status)?s.status:'UNKNOWN';
   const runId=s.run_id&&allow.test(s.run_id)?s.run_id:'project-state';
   const date=Number.isFinite(Date.parse(s.updated_at))?new Date(s.updated_at).toISOString():null;
   // 未知时间不伪称执行过。只有有可验证 status 文件时才上报。
   if(!date||!s.status)continue;
   const sourceKey=[projectId,sourceId,t.task_id,runId,status,date].join('|');
   const seq=Number.parseInt(sha(sourceKey).slice(0,12),16);
   output.push({eventId:sha(sourceKey).slice(0,40),projectId,sourceId,runId,taskId:t.task_id,
     seq,status,occurredAt:date,title:safe(t.title||t.task_id,150),owner:safe(s.owner||t.owner_hint,80),
     dependencies:Array.isArray(t.dependencies)?t.dependencies.filter(x=>allow.test(x)).slice(0,100):[],
     message:safe(s.last_successful_step||s.last_step||s.current_blocker||'',400),
     resumePoint:safe(s.resume_point,400),
     evidence:[] // 不上传原始日志及本机证据路径
   });
 }
 return output;
}
function writeAtomic(filename,data){
 fs.mkdirSync(path.dirname(filename),{recursive:true});
 const temp=filename+'.new-'+process.pid;
 fs.writeFileSync(temp,JSON.stringify(data,null,2),'utf8');
 fs.renameSync(temp,filename);
}
async function transmit(url,token,events,fetcher=fetch){
 const target=new URL('/api/events',url);
 if(target.protocol!=='https:' && target.hostname!=='127.0.0.1' && target.hostname!=='localhost')throw Error('仅允许 HTTPS 云端或本机测试接口');
 const res=await fetcher(target.toString(),{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+token},
  body:JSON.stringify({events}),signal:AbortSignal.timeout(12000)});
 if(!res.ok)throw Error('云端拒绝数据 HTTP '+res.status);
 return res.json();
}
async function tick(cfg,fetcher=fetch){
 const file=cfg.spoolFile, cache=readJSON(file,{version:1,queued:[],sent:[]});
 if(!Array.isArray(cache.queued)||!Array.isArray(cache.sent))throw Error('队列文件损坏，拒绝覆盖');
 const known=new Set([...cache.queued.map(x=>x.eventId),...cache.sent]);
 const current=snapshot(cfg.root,cfg.projectId,cfg.sourceId);
 for(const item of current)if(!known.has(item.eventId)){cache.queued.push(item);known.add(item.eventId)}
 if(cache.queued.length>10000)throw Error('离线队列超过10000条：需要检查连接，已保留原队列');
 writeAtomic(file,cache); // 先落盘后上传，避免崩溃丢失事件
 if(!cfg.url||!cfg.token)return {queued:cache.queued.length,sent:0,offline:true};
 let sent=0;
 while(cache.queued.length){
  const batch=cache.queued.slice(0,50);
  await transmit(cfg.url,cfg.token,batch,fetcher);
  cache.queued.splice(0,batch.length);
  cache.sent.push(...batch.map(x=>x.eventId));
  if(cache.sent.length>20000)cache.sent=cache.sent.slice(-20000);
  writeAtomic(file,cache);
  sent+=batch.length;
 }
 return {queued:cache.queued.length,sent,offline:false};
}
function config(env=process.env){
 const root=env.PROJECT_ROOT,projectId=env.PROJECT_ID,sourceId=env.SOURCE_ID||'win-agent';
 if(!root||!projectId||!allow.test(projectId)||!allow.test(sourceId))throw Error('必须配置 PROJECT_ROOT、PROJECT_ID 和合法 SOURCE_ID');
 return {root:path.resolve(root),projectId,sourceId,url:env.CLOUD_URL,token:env.WRITE_TOKEN,
 spoolFile:path.resolve(env.SPOOL_FILE||path.join(root,'.task-observatory','queue.json'))};
}
async function main(){
 const cfg=config();
 if(!process.argv.includes('--once')&&!process.argv.includes('--loop'))throw Error('使用 --once 或 --loop 明确启动');
 do{
  try{const result=await tick(cfg);console.log(new Date().toISOString(),'采集结果',JSON.stringify(result))}
  catch(e){console.error('采集/上报失败，保留队列：',e.message);if(process.argv.includes('--once'))process.exitCode=1}
  if(!process.argv.includes('--loop'))break;
  await sleep(15000);
 }while(true);
}
if(require.main===module)main().catch(e=>{console.error(e.message);process.exitCode=1});
module.exports={snapshot,tick,transmit,config,writeAtomic};
