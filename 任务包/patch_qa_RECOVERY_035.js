const fs=require('fs'),crypto=require('crypto');
const p='C:/Users/ide0007/Desktop/deliverable/AI小游戏实战营/AI小游戏制作工程文件/直播炮塔守城/任务包/qa_RECOVERY_035_panel_e2e.py';
let s=fs.readFileSync(p,'utf8');const before=crypto.createHash('sha256').update(s).digest('hex');
function rep(a,b,n){if(!s.includes(a))throw new Error('missing '+n);s=s.replace(a,b);}
rep('p&&p.node.getComponent(cc.UITransform)',"p&&p.node.getComponent('cc.UITransform')",'transform string type');
rep("n=sc.getChildByName('候选美术战场画布'),v=cc.view.getVisibleSize(),p={node_expr}.position","n=sc.getChildByName('候选美术战场画布'),a=n.getComponent('待审战场美术覆盖器'),v=cc.view.getVisibleSize(),p={node_expr}.position",'point helper component');
fs.writeFileSync(p,s,'utf8');console.log(JSON.stringify({ok:true,before,after:crypto.createHash('sha256').update(s).digest('hex'),size:Buffer.byteLength(s)}));