'use strict';
const path=require('path'),cp=require('child_process');
const project=process.argv[2]||'win-unpacked';
if(!/^[\w\u3400-\u9fff-]+$/.test(project)){console.error('无效项目 ID');process.exit(2)}
const manager=path.resolve(__dirname,'../../.infra/context-manager.js');
const r=cp.spawnSync(process.execPath,[manager,'recover','--project',project],{encoding:'utf8',timeout:12000});
process.stdout.write(r.stdout||'');process.stderr.write(r.stderr||'');
if(r.error)console.error(r.error.message);process.exit(r.status===null?2:r.status);
