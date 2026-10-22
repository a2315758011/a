const fs=require('fs'),path=require('path');
const dir='C:/Users/ide0007/Desktop/deliverable/AI小游戏实战营/AI小游戏制作工程文件/直播炮塔守城/自动化测试';
const out=[];
for(const n of fs.readdirSync(dir).filter(n=>/^qa_formal_.*_20261022\.py$/.test(n))){
 const p=path.join(dir,n); const lines=fs.readFileSync(p,'utf8').split(/\r?\n/); let changed=false;
 for(let i=0;i<lines.length-1;i++){ if(lines[i].includes('edge_cdp_launcher_20261022.js') && lines[i+1].trim()==='proc=None'){ const lead=(lines[i].match(/^\s*/)||[''])[0]; if(lines[i+1]!==lead+'proc=None'){lines[i+1]=lead+'proc=None';changed=true;} } }
 if(changed) fs.writeFileSync(p,lines.join('\n'),'utf8'); out.push({file:n,changed});
}
console.log(JSON.stringify(out));