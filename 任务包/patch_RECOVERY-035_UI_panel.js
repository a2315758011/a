const fs=require('fs'),crypto=require('crypto');
const file='C:/Users/ide0007/Desktop/deliverable/AI小游戏实战营/AI小游戏制作工程文件/直播炮塔守城/_assistant-temp/候选战场Cocos-V5隔离工程-20261020/assets/脚本/待审战场美术覆盖器.ts';
const expected='cf175eb2d17187761bcad046f2da7b33116ac684b729e3f09b1a30e058b7b16a';
let s=fs.readFileSync(file,'utf8');
const before=crypto.createHash('sha256').update(s).digest('hex');
if(before!==expected)throw new Error('Candidate controller changed unexpectedly; expected '+expected+' got '+before);
function replaceOnce(from,to,label){if(!s.includes(from))throw new Error('Patch target missing: '+label);s=s.replace(from,to);}
replaceOnce(
"  private settlementRoot!:Node;\n  private settlementGraphics!:Graphics;\n  private settlementHeader!:Sprite;",
"  private settlementRoot!:Node;\n  private settlementGraphics!:Graphics;\n  private settlementPanel!:Sprite;\n  private settlementHeader!:Sprite;",
'panel field');
replaceOnce(
"    this.settlementGraphics=this.settlementRoot.addComponent(Graphics);\n    this.settlementHeader=this.createSpriteNode(this.settlementRoot,'结算标题底板',320,104);",
"    this.settlementGraphics=this.settlementRoot.addComponent(Graphics);\n    this.settlementPanel=this.createSpriteNode(this.settlementRoot,'结算专用面板底板',440,540);\n    this.settlementHeader=this.createSpriteNode(this.settlementRoot,'结算标题底板',320,104);",
'create panel sprite');
replaceOnce(
"    const expected=3*3+3+6+2+1+1+8+8;",
"    const expected=3*3+3+6+2+1+1+8+8+1;",
'asset load count');
replaceOnce(
"    uiPaths.forEach((base,index)=>{\n      const assetPath=base+'/spriteFrame';\n      resources.load(assetPath,SpriteFrame,(err,asset)=>complete(assetPath,err,asset,frame=>{this.uiFrames[index]=frame;}));\n    });\n    const fxPaths=[",
"    uiPaths.forEach((base,index)=>{\n      const assetPath=base+'/spriteFrame';\n      resources.load(assetPath,SpriteFrame,(err,asset)=>complete(assetPath,err,asset,frame=>{this.uiFrames[index]=frame;}));\n    });\n    const settlementPanelPath='候选战斗美术-v5-RECOVERY-004/UI/面板/结算面板底板/spriteFrame';\n    resources.load(settlementPanelPath,SpriteFrame,(err,asset)=>complete(settlementPanelPath,err,asset,frame=>{this.settlementPanel.spriteFrame=frame;}));\n    const fxPaths=[",
'load panel asset');
replaceOnce(
"    this.settlementRoot.getComponent(UITransform)!.setContentSize(size.width,size.height);\n    this.settlementHeader.node.getComponent(UITransform)!.setContentSize(Math.min(320,panelWidth-36),104);",
"    this.settlementRoot.getComponent(UITransform)!.setContentSize(size.width,size.height);\n    this.settlementPanel.node.getComponent(UITransform)!.setContentSize(panelWidth,panelHeight);\n    this.settlementPanel.node.setPosition(0,0,0);\n    this.settlementHeader.node.getComponent(UITransform)!.setContentSize(Math.min(320,panelWidth-36),104);",
'layout panel');
const old="    const g=this.settlementGraphics;\n    g.clear();\n    g.fillColor=new Color(7,13,22,220);\n    g.fillRect(-size.width/2,-size.height/2,size.width,size.height);\n    const x=-panelWidth/2,y=-panelHeight/2;\n    g.fillColor=new Color(17,32,46,250);\n    g.fillRect(x,y,panelWidth,panelHeight);\n    g.lineWidth=10;g.strokeColor=new Color(52,61,74,255);g.rect(x,y,panelWidth,panelHeight);g.stroke();\n    g.lineWidth=4;g.strokeColor=new Color(199,141,59,255);g.rect(x+5,y+5,panelWidth-10,panelHeight-10);g.stroke();\n    g.lineWidth=2;g.strokeColor=new Color(240,196,107,255);g.rect(x+12,y+12,panelWidth-24,panelHeight-24);g.stroke();\n    g.fillColor=new Color(39,62,86,255);\n    g.fillRect(x+18,y+panelHeight-142,panelWidth-36,76);\n    const brass=new Color(199,141,59,255),cyan=new Color(66,216,238,255);\n    for(const [cx,cy,sx,sy] of [\n      [x+9,y+9,1,1],[x+panelWidth-14,y+9,-1,1],\n      [x+9,y+panelHeight-14,1,-1],[x+panelWidth-14,y+panelHeight-14,-1,-1]\n    ] as Array<[number,number,number,number]>){\n      g.fillColor=brass;g.fillRect(cx,cy,18,5);g.fillRect(cx,cy,5,18);\n      g.fillColor=new Color(240,196,107,255);g.fillRect(cx+sx*7,cy+sy*7,5,5);\n    }\n    g.fillColor=cyan;g.fillRect(x+12,-12,4,24);g.fillRect(x+panelWidth-16,-12,4,24);\n    this.settlementLayoutKey=size.width+'x'+size.height;";
const repl="    const g=this.settlementGraphics;\n    g.clear();\n    // Keep only the full-screen dim backdrop here; the dedicated transparent pixel panel is a real Sprite child.\n    g.fillColor=new Color(7,13,22,220);\n    g.fillRect(-size.width/2,-size.height/2,size.width,size.height);\n    this.settlementLayoutKey=size.width+'x'+size.height;";
replaceOnce(old,repl,'remove procedural card body');
fs.writeFileSync(file,s,'utf8');
const after=crypto.createHash('sha256').update(s).digest('hex');
console.log(JSON.stringify({ok:true,file,bytes:Buffer.byteLength(s),before,after,checks:{panelField:s.includes('private settlementPanel!:Sprite;'),panelLoaded:s.includes('结算面板底板/spriteFrame'),expectedCount:s.includes('3*3+3+6+2+1+1+8+8+1'),panelLayout:s.includes('this.settlementPanel.node.getComponent(UITransform)!.setContentSize(panelWidth,panelHeight)'),proceduralPanelRemoved:!s.includes('g.fillRect(x,y,panelWidth,panelHeight)')}},null,2));