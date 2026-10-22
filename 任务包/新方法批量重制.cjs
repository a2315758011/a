
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..');
const run=path.join(root,'美术资源','重制批次-v0.6');
const ledger=path.join(run,'任务记录');
const raw=path.join(run,'原始生成');
fs.mkdirSync(ledger,{recursive:true});fs.mkdirSync(raw,{recursive:true});
const rt=JSON.parse(fs.readFileSync(path.resolve(root,'../../../.infra/GENERATION_GATEWAY_RUNTIME.json'),'utf8'));
const token=fs.readFileSync(rt.tokenFile,'utf8').trim();
const cfg=JSON.parse(fs.readFileSync(path.join(root,'美术资源/任务配置/批量美术计划.json'),'utf8'));
const ids=['tower_repeater','tower_mortar','tower_frost','objective_energy_core','enemy_orc_grunt','enemy_orc_boss'];
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const save=(f,d)=>{const tmp=f+'.part';fs.writeFileSync(tmp,JSON.stringify(d,null,2)+'\n');fs.renameSync(tmp,f)};
async function req(method,url,data){const r=await fetch(rt.baseUrl+url,{method,headers:{'x-moyin-gateway-token':token,'Content-Type':'application/json'},body:data?JSON.stringify(data):undefined,signal:AbortSignal.timeout(20000)});return {http:r.status,data:await r.json()}}
function prompt(a){
return '任务类型 MASTER，仅作为下一阶段真实动画的审定形象，不代表动画交付。游戏《直播炮塔守城》。重绘参考图的角色身份与配色，纠正参考图的错误视角和非原生像素风。'+
'统一镜头：俯视塔防，正交投影，镜头俯角约70度，朝屏幕下方，能看到头顶和肩顶；禁止正面人物海报，禁止等距斜视建筑插画。'+
'制作真正64×64逻辑像素画布的一张游戏精灵，以16倍最近邻整数放大显示为1024×1024，保持每个逻辑像素为方块，硬边、有限调色板、1逻辑像素轮廓，无抗锯齿、无渐变和模糊。单位脚底逻辑基线y=56，中心x=32，轮廓占画布约75%，长武器保留完整，不越界。'+
'资源名：'+a.name+'。保留参考图的主要外形、装备类别和主色，只改变镜头和像素表现。'+
(a.id.includes('enemy')?'绿色兽人，双腿双手可分辨，武器与手臂结构清楚，可用于后续真实挥击和步态。':a.id.includes('core')?'青蓝色独立水晶和金属能源支架，保留作为物体的支架，不附加地砖。':'机械炮塔，炮管与机构可分辨，与地面分开。')+
'单一单位、完整画布，纯白#FFFFFF背景便于精确去背景。不要地板草地投影、文字昵称、标题、装饰边框或额外角色；不照搬参考图中的水印。输出PNG。sourceProjectId=live-turret-defense；assetId='+a.id+'；sourceTaskId=ART-REMASTER-V06-'+a.id+'。';
}
async function submit(a,fresh=false){
const f=path.join(ledger,a.id+(fresh?'-新母版.json':'-母版.json'));
if(fs.existsSync(f)){console.log('SKIP',a.id,JSON.parse(fs.readFileSync(f)).jobId);return}
const ref=path.join(root,'美术资源/原始生成/批量母素材',a.id+'-母素材-原始.png');
if(!fs.existsSync(ref))throw Error('missing reference '+a.id);
const descriptions={tower_repeater:'青铜双管速射机械炮塔，圆形机械底座，朝下双炮管',tower_mortar:'暗铁重炮塔，粗大炮口与橙红熔芯，青铜基座',tower_frost:'青蓝冰霜机械塔，短喷口，青铜机构与冰晶',objective_energy_core:'青蓝六棱能源水晶，青铜金属支架，独立物件',enemy_orc_grunt:'小型绿色兽人，皮甲棕腰带，右手短铁斧，双腿明确',enemy_orc_boss:'巨大绿色兽人首领，两枚獠牙，红边暗铁尖刺肩甲，棕皮腰带，右手单柄铁战锤'};const full=fresh?prompt(a).replace('重绘参考图的角色身份与配色，纠正参考图的错误视角和非原生像素风。','创建纠错版本新母版。本任务没有图片参考，请按下列文字角色设定锁定身份。').replace('保留参考图的主要外形、装备类别和主色，只改变镜头和像素表现。',descriptions[a.id]+'。') :prompt(a),data={kind:'image',feature:'freedom_image',transport:'web',accountId:a.accountId,pool:false,providerId:'web:'+a.accountId+':freedom_image',prompt:full,referenceImages:fresh?[]:[ref],aspectRatio:'1:1',sourceProjectId:'live-turret-defense',sourceTaskId:(fresh?'ART-FRESHMASTER-V06-':'ART-REMASTER-V06-')+a.id,idempotencyKey:(fresh?'live-turret-defense-freshmaster-v06-':'live-turret-defense-remaster-v06-')+a.id,outputDir:raw};
const record={assetId:a.id,name:a.name,type:'MASTER',status:'SUBMISSION_UNKNOWN_NO_RETRY',prompt:full,promptSHA256:hash(full),reference:fresh?null:{path:ref,sha256:hash(fs.readFileSync(ref))},request:data,submittedAt:new Date().toISOString(),jobId:null,approved:false};
save(f,record);
try{const x=await req('POST','/v1/jobs',data);record.http=x.http;record.jobId=x.data.job?.id;record.response=x.data;record.status=record.jobId?'SUBMITTED':'REJECTED';}catch(e){record.error=e.message}
save(f,record);console.log(JSON.stringify({assetId:a.id,status:record.status,http:record.http,jobId:record.jobId,error:record.error}));
}
async function collect(f){
const d=JSON.parse(fs.readFileSync(f));
if(!d.jobId){console.log('UNKNOWN',d.assetId);return}
const x=await req('GET','/v1/jobs/'+d.jobId);
const j=x.data.job;d.lastJob=j;d.status=j.status;d.lastQueriedAt=new Date().toISOString();
if(j.status==='completed'){
d.outputs=[];
for(const [i,a] of (j.artifacts||[]).entries()){
if(!a.path||!fs.existsSync(a.path))continue;
const dest=path.join(raw,d.assetId+(d.reference?'-母版-':'-新母版-')+i+path.extname(a.path));
if(!fs.existsSync(dest))fs.copyFileSync(a.path,dest,fs.constants.COPYFILE_EXCL);
d.outputs.push({path:dest,sha256:hash(fs.readFileSync(dest))});
}
}
save(f,d);console.log(JSON.stringify({assetId:d.assetId,status:d.status,jobId:d.jobId,outputs:d.outputs?.map(x=>x.path),error:j.error}));
}
(async()=>{
const mode=process.argv[2];
if(mode==='submit-master')await Promise.all(ids.map(id=>submit(cfg.assets.find(a=>a.id===id))));
else if(mode==='submit-fresh-master')await Promise.all(ids.map(id=>submit(cfg.assets.find(a=>a.id===id),true)));
else if(mode==='collect')await Promise.all(fs.readdirSync(ledger).filter(f=>f.endsWith('.json')).map(f=>collect(path.join(ledger,f))));
else throw Error('Use submit-master or collect');
})().catch(e=>{console.error(e.message);process.exitCode=1});
