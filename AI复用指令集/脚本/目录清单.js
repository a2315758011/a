'use strict';
const fs=require('fs'),path=require('path');
const root=process.argv[2]||process.cwd();
if(!fs.existsSync(root)||!fs.statSync(root).isDirectory()){console.error('目录不存在');process.exit(2)}
let count=0,dirs=0,errors=[],samples=[];const pending=[root];
while(pending.length){const dir=pending.pop();let entries;try{entries=fs.readdirSync(dir,{withFileTypes:true})}catch(e){errors.push({dir,error:e.message});continue}
for(const e of entries){const p=path.join(dir,e.name);if(e.isDirectory()){dirs++;if(dirs<100000)pending.push(p)}
else if(e.isFile()){count++;if(samples.length<100)samples.push(path.relative(root,p))}}
if(count+dirs>200000)break}
console.log(JSON.stringify({root,files:count,directories:dirs,samples,errors,limited:count+dirs>200000},null,2));
