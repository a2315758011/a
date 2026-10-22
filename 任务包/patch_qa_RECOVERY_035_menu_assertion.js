const fs=require('fs'),crypto=require('crypto');
const p='C:/Users/ide0007/Desktop/deliverable/AI小游戏实战营/AI小游戏制作工程文件/直播炮塔守城/任务包/qa_RECOVERY_035_panel_e2e.py';
let s=fs.readFileSync(p,'utf8');
const from='and menu["game"]["towers"]==9 and menu["game"]["hp"]==100)';
const to='and menu["game"]["towers"]==24 and menu["game"]["onlineViewers"]==15 and menu["game"]["hp"]==100)';
if(!s.includes(from))throw new Error('stale menu tower-count assertion missing');
s=s.replace(from,to);
fs.writeFileSync(p,s,'utf8');
console.log(JSON.stringify({ok:true,sha256:crypto.createHash('sha256').update(s).digest('hex'),assertion:'main menu preserves room-level 15 live viewers and 24 logical towers while hiding battle art/HUD'}));