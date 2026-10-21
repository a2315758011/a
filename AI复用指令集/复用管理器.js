#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path'),cp=require('child_process');
const root=__dirname,index=path.join(root,'技能索引.json'),log=path.join(root,'执行记录.jsonl');
const read=()=>JSON.parse(fs.readFileSync(index,'utf8'));
const argv=process.argv.slice(2),action=argv.shift()||'help';
const opt=(name,def)=>{const n=argv.indexOf('--'+name);return n>=0?argv[n+1]:def};
const output=x=>console.log(JSON.stringify(x,null,2));
function safePath(relative){if(!relative||path.isAbsolute(relative))throw Error('只允许库内相对脚本路径');const full=path.resolve(root,relative);if(!full.startsWith(root+path.sep))throw Error('脚本越界');return full}
function record(obj){fs.appendFileSync(log,JSON.stringify({at:new Date().toISOString(),...obj})+'\n','utf8')}
try{
 const data=read(),skills=data.skills||[];
 if(action==='list'){output(skills);process.exit(0)}
 if(action==='find'){const q=argv.join(' ').toLowerCase();output(skills.filter(s=>[s.id,s.title,...(s.keywords||[])].join(' ').toLowerCase().includes(q)));process.exit(0)}
 if(action==='show'){const s=skills.find(x=>x.id===argv[0]);if(!s)throw Error('找不到技能');output(s);process.exit(0)}
 if(action==='check'){const errors=[];for(const s of skills){try{if(!fs.existsSync(safePath(s.script)))errors.push(s.id+': 缺失脚本')}catch(e){errors.push(s.id+': '+e.message)}}output({ok:!errors.length,count:skills.length,errors});process.exit(errors.length?2:0)}
 if(action==='run'){
  const id=argv.shift(),s=skills.find(x=>x.id===id);if(!s)throw Error('找不到技能 '+id);
  const target=safePath(s.script);if(!fs.existsSync(target))throw Error('脚本不存在');
  if(s.requiresApproval&&!argv.includes('--approved'))throw Error('此技能需授权参数 --approved');
  const args=[];for(let i=0;i<argv.length;i++){if(argv[i]==='--arg'){if(!argv[i+1])throw Error('--arg 缺少值');args.push(argv[++i])}}
  let binary; if(target.endsWith('.js'))binary=process.execPath;else if(target.endsWith('.ps1'))binary='powershell.exe';else throw Error('仅支持 .js/.ps1');
  const params=target.endsWith('.ps1')?['-NoProfile','-File',target,...args]:[target,...args];
  const r=cp.spawnSync(binary,params,{cwd:root,encoding:'utf8',timeout:Math.min(s.timeoutMs||30000,300000),maxBuffer:1024*1024});
  record({id,args,exitCode:r.status,error:r.error?.message||null,stdoutTail:(r.stdout||'').slice(-1000),stderrTail:(r.stderr||'').slice(-1000)});
  process.stdout.write(r.stdout||'');process.stderr.write(r.stderr||'');if(r.error)console.error(r.error.message);
  process.exit(r.status===null?2:r.status)
 }
 console.log('用法: node 复用管理器.js list | find <关键词> | show <ID> | check | run <ID> [--arg 参数] [--approved]');
}catch(e){console.error(e.message);process.exit(2)}
