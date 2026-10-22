const fs=require('fs'),path=require('path'),cp=require('child_process'),crypto=require('crypto');
const root=path.resolve(__dirname,'..');
const project=path.join(root,'CocosCreator工程');
const editor=path.join(process.env.USERPROFILE,'.CocosCreator','Creator','3.8.2','CocosCreator.exe');
const outDir=path.join(project,'build','web-mobile');
if(!fs.existsSync(editor)) throw new Error('Cocos Creator 3.8.2 executable missing: '+editor);
if(!fs.existsSync(path.join(project,'assets','场景','守城主场景.scene'))) throw new Error('formal main scene missing');
const t=Date.now();
let code=-999,stdout='',stderr='';
try { const r=cp.spawnSync(editor,['--project',project,'--build','platform=web-mobile;debug=true;startScene=d640f6d0-03c5-4a07-a81a-7fbe6dad1af4'],{cwd:project,encoding:'utf8',timeout:240000,windowsHide:true,maxBuffer:20*1024*1024}); code=r.status===null?-999:r.status; stdout=r.stdout||''; stderr=r.stderr||''; if(r.error) stderr+='\nSPAWN_ERROR '+String(r.error); }
catch(e){stderr+=String(e);}
fs.writeFileSync(path.join(__dirname,'formal-integration-build.stdout.log'),stdout,'utf8');
fs.writeFileSync(path.join(__dirname,'formal-integration-build.stderr.log'),stderr,'utf8');
const files=fs.existsSync(outDir)?(()=>{let n=0;function walk(d){for(const x of fs.readdirSync(d,{withFileTypes:true})){const f=path.join(d,x.name);if(x.isDirectory())walk(f);else n++;}}walk(outDir);return n;})():0;
const entry=path.join(outDir,'index.html');
const report={task:'WHOLE-GAME-FORMAL-INTEGRATION',project,editor,startedAt:new Date(t).toISOString(),durationMs:Date.now()-t,exitCode:code,buildSuccessLogged:/build success/i.test(stdout),entryExists:fs.existsSync(entry),fileCount:files,typescriptErrors:(stdout+'\n'+stderr).match(/typescript[^\n]*(?:error|failed)|error TS\d+/gi)||[],stderrBytes:Buffer.byteLength(stderr),stdoutTail:stdout.slice(-5000),stderrTail:stderr.slice(-3000)};
report.status=(code===0||code===36)&&report.buildSuccessLogged&&report.entryExists&&report.typescriptErrors.length===0?'PASS':'FAIL';
fs.writeFileSync(path.join(root,'验收证据','WHOLE-GAME-COCOS-FORMAL-INTEGRATION-BUILD-20261022.json'),JSON.stringify(report,null,2)+'\n','utf8');
console.log(JSON.stringify({...report,stdoutTail:report.stdoutTail.slice(-1200),stderrTail:report.stderrTail.slice(-1200)},null,2));
if(report.status!=='PASS') process.exitCode=1;
