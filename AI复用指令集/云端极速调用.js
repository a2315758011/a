#!/usr/bin/env node
'use strict';
// Cloud-first launcher. Tiny persistent index; verified code in OS temp cache.
const fs=require('fs'),path=require('path'),os=require('os'),https=require('https'),crypto=require('crypto'),cp=require('child_process');
const root=__dirname;
const index=JSON.parse(fs.readFileSync(path.join(root,'技能索引.json'),'utf8')).skills;
const specs={
 'file-inventory':{remote:'脚本/目录清单.js',sha256:'394e073673d8e2f9af313a5f80654d883261b4ddeb038c1ae4a7d0af2cc4bb16'},
 'project-bootstrap':{remote:'脚本/项目恢复.js',sha256:'a259d7980cf784649b4f8ec7c599ccab909e7ffb06d315bce14c33884af7d042'}
};
const cache=path.join(os.tmpdir(),'ai-reuse-cloud-v1');
const base='https://raw.githubusercontent.com/a2315758011/a/main/AI%E5%A4%8D%E7%94%A8%E6%8C%87%E4%BB%A4%E9%9B%86/';
const [mode,id,...args]=process.argv.slice(2);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function fetch(url){return new Promise((resolve,reject)=>{https.get(url,{timeout:7000,headers:{'User-Agent':'AIReuseRunner/1'}},r=>{if(r.statusCode!==200){r.resume();reject(Error('HTTP '+r.statusCode));return}const parts=[];let n=0;r.on('data',c=>{n+=c.length;if(n>512*1024){r.destroy(Error('文件超出 512KB'));return}parts.push(c)});r.on('end',()=>resolve(Buffer.concat(parts)));r.on('error',reject)}).on('error',reject)})}
async function main(){
 if(mode==='find'){let q=[id,...args].filter(Boolean).join(' ').toLowerCase();console.log(JSON.stringify(index.filter(s=>[s.id,s.title,...(s.keywords||[])].join(' ').toLowerCase().includes(q)),null,2));return}
 if(mode==='list'){console.log(JSON.stringify(index,null,2));return}
 if(mode!=='run'&&mode!=='prefetch')throw Error('使用: node 云端极速调用.js find 关键词 | run 技能ID [参数...] | prefetch 技能ID');
 const s=index.find(x=>x.id===id),spec=specs[id];if(!s||!spec)throw Error('此技能尚未在云端白名单内');
 if(s.requiresApproval&&!args.includes('--approved'))throw Error('需要明确授权 --approved');
 const dest=path.join(cache,spec.sha256+'.js');let source='cache';
 if(!fs.existsSync(dest)||sha(fs.readFileSync(dest))!==spec.sha256){
  source='github';const data=await fetch(base+spec.remote.split('/').map(encodeURIComponent).join('/'));
  if(sha(data)!==spec.sha256)throw Error('云端脚本与已审核 SHA256 不一致，拒绝执行');
  fs.mkdirSync(cache,{recursive:true});fs.writeFileSync(dest,data,{flag:'w'});
 }
 if(mode==='prefetch'){console.log(JSON.stringify({id,source,verified:true}));return}
 const input=args.filter(x=>x!=='--approved');const started=process.hrtime.bigint();
 let execPath=dest;
 // Bootstrap script assumes its relative .infra location: use original copy only until portable cloud version is reviewed.
 if(id==='project-bootstrap'){execPath=path.join(root,s.script);if(!fs.existsSync(execPath)||sha(fs.readFileSync(execPath))!==spec.sha256)throw Error('本地 bootstrap 脚本缺失或校验失败');source='local-bootstrap'}
 const result=cp.spawnSync(process.execPath,[execPath,...input],{cwd:root,encoding:'utf8',timeout:Math.min(s.timeoutMs||30000,300000),maxBuffer:1024*1024});
 process.stdout.write(result.stdout||'');process.stderr.write(result.stderr||'');
 console.error(JSON.stringify({id,source,elapsedMs:Number(process.hrtime.bigint()-started)/1e6,exitCode:result.status}));
 if(result.error)throw result.error;process.exitCode=result.status===null?2:result.status;
}
main().catch(e=>{console.error(e.message);process.exitCode=2});
