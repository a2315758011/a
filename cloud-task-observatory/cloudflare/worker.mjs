// Cloudflare Worker：只接受具备权限的任务事件；网页和接口默认不公开私人信息
const STATUSES = new Set(['PENDING','READY','IN_PROGRESS','IMPLEMENTED','VERIFIED','COMPLETED','FAILED','BLOCKED','NEEDS_ATTENTION','CANCELLED','UNKNOWN']);
const IDs = /^[\w.:-]{1,100}$/;
const CORS = {'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'};
function reply(data,status=200){return new Response(JSON.stringify(data),{status,headers:{...CORS,'Content-Type':'application/json; charset=utf-8'}})}
function authorized(req,token){if(typeof token!=='string'||token.length<24)return false;const value=req.headers.get('authorization')||'';return value==='Bearer '+token}
function safeString(v,n=300){return typeof v==='string'?v.slice(0,n):''}
async function boundedJson(request,maxBytes){
 const reader=request.body?.getReader();
 if(!reader)throw Object.assign(new Error('缺少请求体'),{httpStatus:400});
 const decoder=new TextDecoder('utf-8',{fatal:true});
 let size=0,text='';
 try{
  while(true){
   const {done,value}=await reader.read();if(done)break;
   size+=value.byteLength;
   if(size>maxBytes)throw Object.assign(new Error('请求超过限制'),{httpStatus:413});
   text+=decoder.decode(value,{stream:true});
  }
  text+=decoder.decode();
  return JSON.parse(text);
 }catch(e){
  if(e?.httpStatus)throw e;
  throw Object.assign(new Error('无效JSON'),{httpStatus:400});
 }finally{try{await reader.cancel()}catch{}}
}
function validEvent(e){
 if(!e||typeof e!=='object'||Array.isArray(e))return '事件格式错误';
 for(const k of ['eventId','projectId','taskId','runId','sourceId'])if(!IDs.test(e[k]||''))return '无效字段 '+k;
 if(!Number.isSafeInteger(e.seq)||e.seq<0)return '事件序号必须是非负整数';
 if(!STATUSES.has(e.status))return '未知任务状态';
 if(!e.occurredAt||!Number.isFinite(Date.parse(e.occurredAt)))return '无效时间';
 if(e.dependencies!==undefined&&(!Array.isArray(e.dependencies)||e.dependencies.length>100||e.dependencies.some(x=>!IDs.test(x))))return '依赖字段错误';
 if(e.evidence!==undefined&&(!Array.isArray(e.evidence)||e.evidence.length>20))return '证据字段错误';
 return null;
}
function normalize(e){return {
 eventId:e.eventId,projectId:e.projectId,taskId:e.taskId,runId:e.runId,sourceId:e.sourceId,seq:e.seq,status:e.status,
 occurredAt:new Date(e.occurredAt).toISOString(),title:safeString(e.title,150),owner:safeString(e.owner,100),
 dependencies:(e.dependencies||[]),message:safeString(e.message,600),resumePoint:safeString(e.resumePoint,500),
 evidence:(e.evidence||[]).map(x=>safeString(x,180))
}}
async function store(db,e){
 const x=normalize(e),received=new Date().toISOString();
 // 唯一事件 ID + 来源/执行序号保证断线重放幂等；重放不能覆盖已有事件。
 await db.prepare(`INSERT OR IGNORE INTO events(event_id,project_id,task_id,run_id,source_id,seq,status,occurred_at,received_at,title,owner,dependencies_json,message,resume_point,evidence_json)
 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`).bind(x.eventId,x.projectId,x.taskId,x.runId,x.sourceId,x.seq,x.status,x.occurredAt,received,x.title,x.owner,JSON.stringify(x.dependencies),x.message,x.resumePoint,JSON.stringify(x.evidence)).run();
 await db.prepare(`INSERT INTO sources(source_id,project_id,last_seen_at) VALUES(?,?,?)
 ON CONFLICT(project_id,source_id) DO UPDATE SET project_id=excluded.project_id,last_seen_at=excluded.last_seen_at`).bind(x.sourceId,x.projectId,received).run();
 return x;
}
async function getSnapshot(db,projectId){
 const out=await db.prepare('SELECT * FROM events WHERE project_id=? ORDER BY occurred_at DESC, seq DESC, received_at DESC LIMIT 2000').bind(projectId).all();
 const rows=out.results||[]; const tasks=new Map();const seenSeq=new Map();
 // 以同一来源同一 run 的序号为主，跨 run 以收到时间排序（每条记录保留）。
 for(const r of rows){const key=r.task_id;if(!tasks.has(key))tasks.set(key,{
 id:r.task_id,title:r.title||r.task_id,status:r.status,owner:r.owner,dependencies:JSON.parse(r.dependencies_json||'[]'),
 updatedAt:r.received_at,occurredAt:r.occurred_at,resumePoint:r.resume_point,message:r.message,evidence:JSON.parse(r.evidence_json||'[]'),runId:r.run_id
 });}
 const sources=(await db.prepare('SELECT * FROM sources WHERE project_id=?').bind(projectId).all()).results||[];
 const latest=sources.map(x=>x.last_seen_at).sort().at(-1)||null;
 return {schemaVersion:1,projectId,updatedAt:latest,tasks:[...tasks.values()],
 events:rows.slice(0,40).map(r=>({eventId:r.event_id,at:r.received_at,taskId:r.task_id,type:r.status,message:r.message})).reverse(),
 sources:sources.map(s=>({sourceId:s.source_id,lastSeenAt:s.last_seen_at,online:Date.now()-Date.parse(s.last_seen_at)<90000})),
 truncated:rows.length>=2000};
}
export default {async fetch(request,env){
 const url=new URL(request.url);const pathname=url.pathname;
 if(pathname==='/api/health')return reply({ok:true,cloud:true});
 if(pathname==='/api/heartbeat'&&request.method==='POST'){
  if(!authorized(request,env.WRITE_TOKEN))return reply({error:'写入权限不足'},401);
  let body;try{body=await boundedJson(request,4096)}catch(e){return reply({error:e.message},e.httpStatus||400)}
  if(!body||!IDs.test(body.sourceId||'')||!IDs.test(body.projectId||''))return reply({error:'来源编号错误'},400);
  const now=new Date().toISOString();
  try{await env.DB.prepare(`INSERT INTO sources(source_id,project_id,last_seen_at) VALUES(?,?,?)
 ON CONFLICT(project_id,source_id) DO UPDATE SET project_id=excluded.project_id,last_seen_at=excluded.last_seen_at`).bind(body.sourceId,body.projectId,now).run();
  return reply({ok:true,receivedAt:now})}catch{return reply({error:'心跳保存失败'},500)}
 }
 if(pathname==='/api/events'&&request.method==='POST'){
  if(!authorized(request,env.WRITE_TOKEN))return reply({error:'写入权限不足'},401);
  if(Number(request.headers.get('content-length')||0)>100000)return reply({error:'请求过大'},413);
  let body;try{body=await boundedJson(request,100000)}catch(e){return reply({error:e.message},e.httpStatus||400)}
  if(!body||!Array.isArray(body.events)||body.events.length<1||body.events.length>50)return reply({error:'每批1至50个事件'},400);
  for(const e of body.events){const err=validEvent(e);if(err)return reply({error:err},400)}
  try{for(const e of body.events)await store(env.DB,e);return reply({ok:true,received:body.events.length})}
  catch(e){return reply({error:'云端写入失败'},500)}
 }
 if(pathname==='/api/status'&&request.method==='GET'){
  if(!authorized(request,env.READ_TOKEN))return reply({error:'读取权限不足'},401);
  const id=url.searchParams.get('project')||'';
  if(!IDs.test(id))return reply({error:'项目编号无效'},400);
  try{return reply(await getSnapshot(env.DB,id))}catch{return reply({error:'云端读取失败'},500)}
 }
 if(pathname.startsWith('/api/'))return reply({error:'没有该接口'},404);
 // 静态文件由 Cloudflare Assets 处理；不把读写令牌注入公开 HTML。
 return env.ASSETS.fetch(request);
}};
export {validEvent,normalize,getSnapshot};