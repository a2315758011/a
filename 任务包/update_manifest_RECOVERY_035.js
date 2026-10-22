const fs=require('fs'),path=require('path');
const root='C:/Users/ide0007/Desktop/deliverable/AI小游戏实战营/AI小游戏制作工程文件/直播炮塔守城';
const file=path.join(root,'game-art/manifest/art-manifest.json');
const manifest=JSON.parse(fs.readFileSync(file,'utf8'));
manifest.assets=manifest.assets||[];
const id='td-v5-ui-settlement-panel';
if(manifest.assets.some(x=>x.assetId===id))throw new Error('Asset id already exists; refusing duplicate insertion');
const entry={
 assetId:id,name:'结算弹层专用像素面板底板',mode:'static',status:'candidate_runtime_qa_pass',
 sourceSheet:'game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/master.png',
 sourceHash:'AFC5887638F7F86E3D3AA28E0785BFD0AFE175478937FE79DC0CCF088B24E1DB',
 providerOutput:'game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/provider-output.png',
 alphaQa:'game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/alpha-pixel-qa.json',
 enginePath:'_assistant-temp/候选战场Cocos-V5隔离工程-20261020/assets/resources/候选战斗美术-v5-RECOVERY-004/UI/面板/结算面板底板.png',
 runtimeHash:'AFC5887638F7F86E3D3AA28E0785BFD0AFE175478937FE79DC0CCF088B24E1DB',
 approved:false,formalPresent:false,layerability:'not_applicable_static',
 review:'New RECOVERY-035 static settlement panel; shared Generation Gateway output preserved, magenta removed, 48-color no-dither palette and nearest-neighbor normalization. Alpha/pixel QA PASS; Cocos Web-Mobile build and real win/loss runtime QA PASS across five viewports. Human V5 art sign-off pending.',
 replacementTask:'RECOVERY-035-UI-PANEL-MASTER-A',
 runtimeQa:'验收证据/RECOVERY-035-UI-PANEL/真实Cocos双结局与五视口回归.json',
 buildQa:'game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/cocos-build-qa.json'
};
manifest.assets.push(entry);
manifest.lastAudit='RECOVERY-035';
manifest.auditEvidence=Array.from(new Set([...(manifest.auditEvidence||[]),
 'game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/alpha-pixel-qa.json',
 'game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/cocos-build-qa.json',
 '验收证据/RECOVERY-035-UI-PANEL/真实Cocos双结局与五视口回归.json'
]));
manifest.updatedAt=new Date().toISOString();
fs.writeFileSync(file,JSON.stringify(manifest,null,2)+'\n','utf8');
console.log(JSON.stringify({ok:true,file,assetCount:manifest.assets.length,entry,updatedAt:manifest.updatedAt},null,2));