'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {createRequire}=require('node:module');
const {snapshot,tick,transmit}=require('../collector/collector.cjs');
async function worker(){return import('../cloudflare/worker.mjs')}
function fixture(){const root=fs.mkdtempSync(path.join(__dirname,'..','_assistant-temp-test-'));const base=path.join(root,'.project-orchestrator');fs.mkdirSync(path.join(base,'tasks'),{recursive:true});fs.mkdirSync(path.join(base,'status'));fs.writeFileSync(path.join(base,'tasks','A.json'),JSON.stringify({task_id:'A',title:'工作任务',dependencies:[]}));fs.writeFileSync(path.join(base,'status','A.json'),JSON.stringify({task_id:'A',status:'IN_PROGRESS',updated_at:'2026-10-28T00:00:00Z',resume_point:'继续测试'}));return root}
function fakeServer(){
 const rows=[],sources=new Map();
 const db={async batch(statements){
   // 原子模拟：先保存快照，失败时回滚；测试事务语义。
   const before=rows.slice(),beforeSources=new Map(sources);
   try{for(const statement of statements)await statement.run()}
   catch(e){rows.splice(0,rows.length,...before);sources.clear();for(const [k,v] of beforeSources)sources.set(k,v);throw e}
   return statements.map(()=>({success:true}));
 },prepare(sql){let args=[];return {bind(...vals){args=vals;return this},async run(){
 if(sql.includes('INSERT OR IGNORE INTO events')){if(!rows.some(r=>r.event_id===args[0]||(r.project_id===args[1]&&r.source_id===args[4]&&r.run_id===args[3]&&r.seq===args[5])))rows.push({event_id:args[0],project_id:args[1],task_id:args[2],run_id:args[3],source_id:args[4],seq:args[5],status:args[6],occurred_at:args[7],received_at:args[8],title:args[9],owner:args[10],dependencies_json:args[11],message:args[12],resume_point:args[13],evidence_json:args[14]})}
 if(sql.includes('INSERT INTO sources'))sources.set(args[1]+'|'+args[0],{source_id:args[0],project_id:args[1],last_seen_at:args[2]});return {success:true};
 },async all(){if(sql.includes('FROM sources'))return {results:[...sources.values()].filter(s=>s.project_id===args[0])};return {results:rows.filter(r=>r.project_id===args[0]).slice().sort((a,b)=>b.occurred_at.localeCompare(a.occurred_at)||b.seq-a.seq||b.received_at.localeCompare(a.received_at))}}}}};
 return {DB:db,WRITE_TOKEN:'w'.repeat(32),READ_TOKEN:'r'.repeat(32),ASSETS:{fetch:async()=>new Response('网页内容')} ,rows,sources};
}
function evt(){return {eventId:'ev-1',projectId:'demo',taskId:'A',runId:'run-1',sourceId:'win-agent',seq:1,status:'IN_PROGRESS',occurredAt:'2026-10-28T00:00:00Z',title:'工作任务',dependencies:[]}}
test('事件必须具备合法任务编号与状态',async()=>{const {validEvent}=await worker();assert.equal(validEvent(evt()),null);assert.match(validEvent({...evt(),status:'FAKE_SUCCESS'}),/未知任务状态/);assert.match(validEvent({...evt(),taskId:'../secret'}),/无效字段/)});
test('未经授权禁止读取私人任务',async()=>{const {default:w}=await worker(),env=fakeServer();const r=await w.fetch(new Request('https://unit.test/api/status?project=demo'),env);assert.equal(r.status,401)});
test('未经授权禁止写入任务',async()=>{const {default:w}=await worker(),env=fakeServer();const r=await w.fetch(new Request('https://unit.test/api/events',{method:'POST',body:JSON.stringify({events:[evt()]})}),env);assert.equal(r.status,401)});
test('合法事件可查询；重复上报幂等',async()=>{const {default:w}=await worker(),env=fakeServer();for(let i=0;i<2;i++){const r=await w.fetch(new Request('https://unit.test/api/events',{method:'POST',headers:{Authorization:'Bearer '+env.WRITE_TOKEN,'Content-Type':'application/json'},body:JSON.stringify({events:[evt()]})}),env);assert.equal(r.status,200)}assert.equal(env.rows.length,1);const r=await w.fetch(new Request('https://unit.test/api/status?project=demo',{headers:{Authorization:'Bearer '+env.READ_TOKEN}}),env);const d=await r.json();assert.equal(d.tasks[0].id,'A');assert.equal(d.tasks[0].status,'IN_PROGRESS')});
test('断线后补发旧事件，不得覆盖较新的任务状态',async()=>{const {default:w}=await worker(),env=fakeServer();
 const newer={...evt(),eventId:'newer',seq:2,status:'VERIFIED',occurredAt:'2026-10-28T02:00:00Z'};
 const older={...evt(),eventId:'older',seq:1,status:'IN_PROGRESS',occurredAt:'2026-10-28T01:00:00Z'};
 for(const event of [newer,older]){const res=await w.fetch(new Request('https://unit.test/api/events',{method:'POST',headers:{Authorization:'Bearer '+env.WRITE_TOKEN,'Content-Type':'application/json'},body:JSON.stringify({events:[event]})}),env);assert.equal(res.status,200)}
 const res=await w.fetch(new Request('https://unit.test/api/status?project=demo',{headers:{Authorization:'Bearer '+env.READ_TOKEN}}),env);
 const data=await res.json();assert.equal(data.tasks[0].status,'VERIFIED');
});
test('云端数据库中途失败必须拒绝整批确认',async()=>{
 const {default:w}=await worker(),env=fakeServer();
 const original=env.DB.batch.bind(env.DB);
 env.DB.batch=async(statements)=>{throw new Error('数据库故障')};
 const r=await w.fetch(new Request('https://unit.test/api/events',{method:'POST',headers:{Authorization:'Bearer '+env.WRITE_TOKEN},body:JSON.stringify({events:[evt()]})}),env);
 assert.equal(r.status,500);assert.equal(env.rows.length,0);
 env.DB.batch=original;
});
test('多个采集源同一批次只写各自心跳',async()=>{
 const {default:w}=await worker(),env=fakeServer();
 const e1=evt(),e2={...evt(),eventId:'ev-2',sourceId:'second-agent',seq:2};
 const r=await w.fetch(new Request('https://unit.test/api/events',{method:'POST',headers:{Authorization:'Bearer '+env.WRITE_TOKEN},body:JSON.stringify({events:[e1,e2]})}),env);
 assert.equal(r.status,200);assert.equal(env.sources.size,2);assert.equal(env.rows.length,2);
});
test('无效事件必须完整拒绝',async()=>{const {default:w}=await worker(),env=fakeServer();const r=await w.fetch(new Request('https://unit.test/api/events',{method:'POST',headers:{Authorization:'Bearer '+env.WRITE_TOKEN,'Content-Type':'application/json'},body:JSON.stringify({events:[evt(),{...evt(),eventId:'bad2',status:'WRONG'}]})}),env);assert.equal(r.status,400);assert.equal(env.rows.length,0)});
test('无状态改变时仍更新心跳',async()=>{const {default:w}=await worker(),env=fakeServer();const r=await w.fetch(new Request('https://unit.test/api/heartbeat',{method:'POST',headers:{Authorization:'Bearer '+env.WRITE_TOKEN,'Content-Type':'application/json'},body:JSON.stringify({projectId:'demo',sourceId:'win-agent'})}),env);assert.equal(r.status,200);assert.equal(env.sources.size,1)});
test('采集器读取真实状态而非虚构验收',()=>{const root=fixture();try{const arr=snapshot(root,'demo','win-agent');assert.equal(arr.length,1);assert.equal(arr[0].status,'IN_PROGRESS');assert.deepEqual(arr[0].evidence,[])}finally{fs.rmSync(root,{recursive:true,force:true})}});
test('默认不上传恢复详情，并对任务文本进行脱敏',()=>{const root=fixture();try{
 const taskPath=path.join(root,'.project-orchestrator','tasks','A.json');
 const task=JSON.parse(fs.readFileSync(taskPath,'utf8'));
 task.title='检查 token=superSecretValue 联系 person@example.com 路径 C:\\Users\\private\\note.txt';
 fs.writeFileSync(taskPath,JSON.stringify(task));
 const normal=snapshot(root,'demo','win-agent');
 assert.equal(normal[0].message,'');assert.equal(normal[0].resumePoint,'');
 assert.ok(!normal[0].title.includes('superSecretValue'));
 assert.ok(!normal[0].title.includes('person@example.com'));
 assert.ok(!normal[0].title.includes('C:\\Users\\private'));
 const detailed=snapshot(root,'demo','win-agent',{includeRecoveryText:true});
 assert.equal(detailed[0].resumePoint,'继续测试');
 }finally{fs.rmSync(root,{recursive:true,force:true})}});
test('采集事件序号必须由真实更新时间决定',()=>{const root=fixture();try{
 const items=snapshot(root,'demo','agent');
 assert.equal(items.length,1);
 assert.equal(items[0].seq,Date.parse('2026-10-28T00:00:00Z'));
 const statusPath=path.join(root,'.project-orchestrator','status','A.json');
 fs.writeFileSync(statusPath,JSON.stringify({task_id:'A',status:'VERIFIED',updated_at:'2026-10-28T01:00:00Z'}));
 const newer=snapshot(root,'demo','agent')[0];
 assert.ok(newer.seq>items[0].seq);
 }finally{fs.rmSync(root,{recursive:true,force:true})}});
test('断线先保存队列，下次联网再补发，不能重复',async()=>{const root=fixture();try{const cfg={root,projectId:'demo',sourceId:'win-agent',spoolFile:path.join(root,'spool.json')};const offline=await tick(cfg);assert.equal(offline.queued,1);const calls=[];const fake=async(url,opts)=>{calls.push(url);return {ok:true,status:200,json:async()=>({ok:true})}};const online=await tick({...cfg,url:'https://unit.test',token:'w'.repeat(32)},fake);assert.equal(online.sent,1);assert.equal(online.queued,0);const again=await tick({...cfg,url:'https://unit.test',token:'w'.repeat(32)},fake);assert.equal(again.sent,0);assert.equal(calls.filter(x=>x.endsWith('/api/events')).length,1)}finally{fs.rmSync(root,{recursive:true,force:true})}});
test('无Content-Length的超大JSON应被流式拒绝',async()=>{
 const {default:w}=await worker(),env=fakeServer();
 const oversized=JSON.stringify({events:[{...evt(),message:'x'.repeat(105000)}]});
 const r=await w.fetch(new Request('https://unit.test/api/events',{method:'POST',headers:{Authorization:'Bearer '+env.WRITE_TOKEN},body:oversized}),env);
 assert.equal(r.status,413);assert.equal(env.rows.length,0);
});
test('不接受空事件批次',async()=>{
 const {default:w}=await worker(),env=fakeServer();
 const r=await w.fetch(new Request('https://unit.test/api/events',{method:'POST',headers:{Authorization:'Bearer '+env.WRITE_TOKEN},body:JSON.stringify({events:[]})}),env);
 assert.equal(r.status,400);
});
test('心跳不得向公网HTTP发送上传口令',async()=>{
 const root=fixture();try{
 let calls=0;const cfg={root,projectId:'demo',sourceId:'win-agent',spoolFile:path.join(root,'spool.json'),url:'http://example.org',token:'some-private-write-token'};
 await assert.rejects(tick(cfg,async()=>{calls++;return {ok:true}}),/HTTPS/);
 assert.equal(calls,0);assert.equal(JSON.parse(fs.readFileSync(cfg.spoolFile,'utf8')).queued.length,1);
 }finally{fs.rmSync(root,{recursive:true,force:true})}
});
test('前端来源离线判定、动画暂停逻辑可加载',()=>{
 const vm=require('node:vm');
 const html=fs.readFileSync(path.join(__dirname,'..','public','index.html'),'utf8');
 const source=html.split('<script>')[1]?.split('</script>')[0];
 assert.ok(source,'中文网页脚本存在');new vm.Script(source);
 const sandbox={snapshot:{sources:[{sourceId:'agent-A',lastSeenAt:new Date().toISOString()}]},Date,translate:s=>s};
 vm.runInNewContext(source.slice(source.indexOf('function sourceOnline('),source.indexOf('function draw(data){')),sandbox);
 assert.equal(sandbox.sourceOnline({sourceId:'agent-A'}),true);
 assert.equal(sandbox.sourceOnline({sourceId:'agent-missing'}),false);
 assert.equal(sandbox.visibleStatus({status:'IN_PROGRESS',sourceId:'agent-missing'}),'最后记录：执行中（采集已断开）');
 assert.ok(source.includes("sourceOnline(t,data)?'active':''"),'动态线必须根据来源心跳控制');
});
test('公网HTTP明文上报必须拒绝',async()=>{await assert.rejects(transmit('http://example.org','secret',[evt()],async()=>({ok:true})),/HTTPS/)});
