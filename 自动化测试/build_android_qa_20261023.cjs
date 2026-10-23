// Cocos Creator 3.8.2 Android build gate; never treat "build success" without exit 36/0 as PASS.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),cp=require('child_process');
const root=path.resolve(__dirname,'..'),project=path.join(root,'CocosCreator工程');
const user=process.env.USERPROFILE||process.env.HOME;
const editor=path.join(user,'.CocosCreator','Creator','3.8.2','CocosCreator.exe');
const sdk=path.resolve(root,'..','..','..','_assistant-temp','android-sdk');
const ndk=path.join(sdk,'ndk','23.1.7779620'),cmake=path.join(sdk,'cmake','3.22.1');
const configPath=path.join(root,'_assistant-temp','android-build-config.json');
const config=JSON.parse(fs.readFileSync(configPath,'utf8')),buildPath=config.buildPath;
const evidence=path.join(root,'验收证据','ANDROID-APK-20261023');
fs.mkdirSync(evidence,{recursive:true});
const reportPath=path.join(evidence,'cocos-android-build.json');
const failureCache=path.join(root,'_assistant-temp','android-build-known-blocker.json');
const needed=[editor,path.join(sdk,'platforms','android-33','android.jar'),path.join(sdk,'build-tools','34.0.0','aapt.exe'),path.join(ndk,'ndk-build.cmd'),path.join(cmake,'bin','cmake.exe')];
for(const f of needed)if(!fs.existsSync(f))throw new Error('Android build prerequisite missing: '+f);
function fingerprint(){
 const files=[configPath,
  path.join(project,'profiles','v2','packages','program.json'),
  path.join(project,'profiles','v2','extensions','android.json'),
  path.join(user,'.CocosCreator','profiles','v2','extensions','android.json'),
  path.join(user,'.CocosCreator','profiles','v2','packages','program.json'),
  path.join(sdk,'platforms','android-33','source.properties'),
  path.join(sdk,'build-tools','34.0.0','source.properties'),
  path.join(ndk,'source.properties'),
  path.join(cmake,'source.properties')];
 const hash=crypto.createHash('sha256');
 hash.update(JSON.stringify({editor:fs.statSync(editor).size,version:'3.8.2',sdk,ndk,cmake,buildPath}));
 for(const f of files)hash.update(f+'='+(fs.existsSync(f)?fs.readFileSync(f):'MISSING'));
 return hash.digest('hex');
}
const fp=fingerprint();
function blocked(reason){
 const result={result:'BLOCKED_KNOWN_COCOS_PLUGIN_ERROR',reason,code:34,signature:'Cocos Creator 3.8.2 android hook onAfterInit rejects SDK/NDK paths',sdkReady:true,ndkReady:true,apk:false,toolchainFingerprint:fp,instruction:'Change the environment or Android build config, then use --force to re-test; identical failures are cached.'};
 console.log(JSON.stringify(result,null,2));process.exitCode=2;
}
if(process.argv.includes('--adopt-last-failure')){
 const old=JSON.parse(fs.readFileSync(reportPath,'utf8').replace(/\\n\s*$/,''));
 const last=old.steps?.[0];
 if(old.status!=='FAIL'||last?.exitCode!==34||!last.stderrTail?.includes('找不到 Android NDK/SDK 路径')||old.apk?.length)throw new Error('Cannot cache an unverified failure');
 fs.writeFileSync(failureCache,JSON.stringify({signature:'SDK_PATH_REJECTED',fingerprint:fp,createdAt:new Date().toISOString(),sourceReport:path.relative(root,reportPath)},null,2)+'\n','utf8');
 console.log(JSON.stringify({result:'FAILURE_SIGNATURE_CACHED',fingerprint:fp}));process.exit(0);
}
const known=fs.existsSync(failureCache)?JSON.parse(fs.readFileSync(failureCache,'utf8')):null;
if(process.argv.includes('--check-cache')){console.log(JSON.stringify({cached:!!(known&&known.signature==='SDK_PATH_REJECTED'&&known.fingerprint===fp),fingerprint:fp}));process.exit(0)}
if(known&&known.signature==='SDK_PATH_REJECTED'&&known.fingerprint===fp&&!process.argv.includes('--force')){
 blocked('Identical SDK-path rejection already verified; skipped an unnecessary Creator startup');
}else{
 const stage=process.argv.includes('--make')?'make':'build';
 const env={...process.env,ANDROID_SDK_ROOT:sdk,ANDROID_HOME:sdk,NDK_ROOT:ndk,NDK_HOME:ndk,ANDROID_NDK_HOME:ndk,CMAKE_HOME:cmake,JAVA_HOME:config.packages.android.javaHome};
 const args=['--project',project,'--build','configPath='+configPath+';stage='+stage];
 const t=Date.now(),r=cp.spawnSync(editor,args,{cwd:project,env,encoding:'utf8',timeout:270000,windowsHide:true,maxBuffer:32*1024*1024});
 const stdout=r.stdout||'',stderr=(r.stderr||'')+(r.error?'\nSPAWN_ERROR '+String(r.error):'');
 fs.writeFileSync(path.join(evidence,'cocos-android-'+stage+'.stdout.log'),stdout,'utf8');
 fs.writeFileSync(path.join(evidence,'cocos-android-'+stage+'.stderr.log'),stderr,'utf8');
 const files=[];function walk(d){if(!fs.existsSync(d))return;for(const x of fs.readdirSync(d,{withFileTypes:true})){const f=path.join(d,x.name);if(x.isDirectory())walk(f);else if(/\.apk$/i.test(x.name))files.push({path:f,size:fs.statSync(f).size});}}
 walk(buildPath);
 const step={stage,args,exitCode:r.status,seconds:Math.round((Date.now()-t)/10)/100,spawnError:r.error?String(r.error):null,
  successLogged:/build success/i.test(stdout),stderrTail:stderr.slice(-3000),stdoutTail:stdout.slice(-5000)};
 const ok=(r.status===0||r.status===36)&&step.successLogged&&(!process.argv.includes('--make')||files.length>0);
 const report={task:'ANDROID-APK-20261023',project,editor,sdk,ndk,cmake,configPath,buildPath,startedAt:new Date(t).toISOString(),
  steps:[step],apk:files,totalSeconds:step.seconds,status:ok?'PASS_BUILD_STAGE':'FAIL',
  reason:ok?null:stderr.includes('找不到 Android NDK/SDK 路径')?'COCOS_ANDROID_HOOK_SDK_PATH_REJECTED':'COCOS_ANDROID_BUILD_FAILED',
  fingerprint:fp};
 fs.writeFileSync(reportPath,JSON.stringify(report,null,2)+'\n','utf8');
 if(ok&&fs.existsSync(failureCache))fs.unlinkSync(failureCache);
 else if(report.reason==='COCOS_ANDROID_HOOK_SDK_PATH_REJECTED')
  fs.writeFileSync(failureCache,JSON.stringify({signature:'SDK_PATH_REJECTED',fingerprint:fp,createdAt:new Date().toISOString()},null,2)+'\n','utf8');
 console.log(JSON.stringify({status:report.status,reason:report.reason,exitCode:r.status,seconds:step.seconds,apk:files,stderrTail:stderr.slice(-900)},null,2));
 if(!ok)process.exitCode=1;
}
