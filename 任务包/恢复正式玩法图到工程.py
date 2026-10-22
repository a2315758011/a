# -*- coding:utf-8 -*-
import json,pathlib,urllib.request,hashlib,shutil
from PIL import Image
root=pathlib.Path(__file__).resolve().parents[1]
runtime=json.loads((pathlib.Path.home()/'Desktop/deliverable/.infra/GENERATION_GATEWAY_RUNTIME.json').read_text('utf-8'))
ledger=root/'任务包'/'正式玩法图网关任务-v0.4.json'
state=json.loads(ledger.read_text('utf-8'))
token=pathlib.Path(runtime['tokenFile']).read_text('utf-8').strip()
req=urllib.request.Request(runtime['baseUrl']+'/v1/jobs/'+state['jobId'],headers={'X-Moyin-Gateway-Token':token})
with urllib.request.urlopen(req,timeout=12) as r:x=json.load(r)
job=x.get('job') or x
if job.get('status')!='completed':raise SystemExit('NOT_COMPLETED '+str(job.get('status')))
files=job.get('artifacts') or (job.get('result') or {}).get('artifacts') or []
if not files:raise SystemExit('NO_ARTIFACT')
source=pathlib.Path(files[0]['path'])
if not source.is_file():raise SystemExit('ARTIFACT_NOT_ON_DISK')
dst_dir=root/'美术资源'/'原始生成';dst_dir.mkdir(parents=True,exist_ok=True)
dest=dst_dir/'玩法总览图-真实网页生成-v0.4.png'
if dest.exists() and hashlib.sha256(dest.read_bytes()).digest()!=hashlib.sha256(source.read_bytes()).digest():raise SystemExit('DEST_CONFLICT')
if not dest.exists():shutil.copy2(source,dest)
with Image.open(dest) as im:
 im.load()
 meta={'format':im.format,'mode':im.mode,'size':im.size,'fileBytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
 preview=dst_dir/'玩法总览图-审图缩略.jpg'
 thumb=im.convert('RGB');thumb.thumbnail((800,1400));thumb.save(preview,'JPEG',quality=82,optimize=True)
state.update({'status':'OUTPUT_COPIED_PENDING_VISUAL_REVIEW','output':str(dest),'preview':str(preview),'result':meta,'jobFinalStatus':'completed','accountId':job.get('request',{}).get('accountId'),'originalFile':str(source),'artifacts':files})
ledger.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'output':str(dest),'preview':str(preview),'result':meta},ensure_ascii=False))
