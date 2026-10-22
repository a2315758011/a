# -*- coding:utf-8 -*-
import json,pathlib,urllib.request
root=pathlib.Path(__file__).resolve().parents[1]
rt=json.loads((pathlib.Path.home()/'Desktop/deliverable/.infra/GENERATION_GATEWAY_RUNTIME.json').read_text('utf-8'))
ledger=root/'任务包'/'正式玩法图网关任务-v0.4.json'
data=json.loads(ledger.read_text('utf-8'))
if not data.get('jobId'):
 print('NOT_SUBMITTED_OR_UNKNOWN',data['status']);raise SystemExit(0)
token=pathlib.Path(rt['tokenFile']).read_text('utf-8').strip()
req=urllib.request.Request(rt['baseUrl']+'/v1/jobs/'+data['jobId'],headers={'X-Moyin-Gateway-Token':token})
with urllib.request.urlopen(req,timeout=15) as r:obj=json.load(r)
job=obj.get('job') or obj
print(json.dumps({'id':job.get('id'),'status':job.get('status'),'error':job.get('error'),'artifacts':job.get('artifacts',[]),'request':job.get('request',{}).get('accountId')},ensure_ascii=False)[:2600])
