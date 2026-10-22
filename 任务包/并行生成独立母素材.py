# -*- coding: utf-8 -*-
"""真实批量提交测试：固定账号，不重复提交；任务结果从原任务ID恢复。"""
import json,pathlib,urllib.request,urllib.error,concurrent.futures,threading,datetime,hashlib,sys,time,os
ROOT=pathlib.Path(__file__).resolve().parents[1]
CONFIG=ROOT/'美术资源/任务配置/批量美术计划.json'
LEDGER_DIR=ROOT/'任务包'/'素材生成任务-v0.5'
LEDGER_DIR.mkdir(parents=True,exist_ok=True)
RUNTIME=pathlib.Path.home()/'Desktop/deliverable/.infra/GENERATION_GATEWAY_RUNTIME.json'
rt=json.loads(RUNTIME.read_text('utf-8'))
token=pathlib.Path(rt['tokenFile']).read_text('utf-8').strip()
assets=json.loads(CONFIG.read_text('utf-8'))['assets']
lock=threading.Lock()
def log(*args):
 with lock:print(*args,flush=True)
def request(method,url,body=None,timeout=22):
 h={'X-Moyin-Gateway-Token':token}
 if body is not None:h['Content-Type']='application/json; charset=utf-8'
 b=json.dumps(body,ensure_ascii=False).encode('utf-8') if body is not None else None
 q=urllib.request.Request(rt['baseUrl']+url,headers=h,method=method,data=b)
 try:
  with urllib.request.urlopen(q,timeout=timeout) as resp:return resp.status,json.load(resp)
 except urllib.error.HTTPError as ex:
  data=ex.read().decode('utf-8','replace')
  try:data=json.loads(data)
  except:pass
  return ex.code,data
def write_atomic(path,data):
 tmp=path.with_suffix('.part')
 tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf-8')
 os.replace(tmp,path)
def run(asset):
 aid=asset['id'];p=LEDGER_DIR/(aid+'.json')
 if p.exists():
  d=json.loads(p.read_text('utf-8'))
  log('SKIP_EXISTING',aid,d.get('status'),d.get('jobId'))
  return
 account=asset['accountId'];stid='ART-MASTER-'+aid.upper().replace('-','_')+'-20261012'
 prompt=asset['prompt']+' Image is ONLY an individual master sprite, not a complete battle scene. Crisp legible silhouette. Leave 15 percent pure white margin, avoid shadows. PNG if supported.'
 data={'kind':'image','feature':'freedom_image','transport':'web','providerId':'web:'+account+':freedom_image','accountId':account,'pool':False,'prompt':prompt,
 'aspectRatio':'1:1','sourceProjectId':'live-turret-defense','sourceTaskId':stid,
 'idempotencyKey':'live-turret-defense-'+stid+'-v05-once','outputDir':str(ROOT/'美术资源/原始生成/批量母素材')}
 # Preserve pre-submit record before the network action; uncertain means never resubmit.
 record={'id':aid,'name':asset['name'],'stage':'MASTER_SAMPLE_NOT_FINAL','accountId':account,'sourceTaskId':stid,'idempotencyKey':data['idempotencyKey'],'promptSHA256':hashlib.sha256(prompt.encode()).hexdigest(),'status':'SUBMISSION_UNKNOWN_NO_RETRY','submittedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'jobId':None}
 write_atomic(p,record)
 try:
  status,reply=request('POST','/v1/jobs',data,timeout=28)
  job=(reply.get('job') or {}) if isinstance(reply,dict) else {}
  record.update({'http':status,'jobId':job.get('id') or (reply.get('jobId') if isinstance(reply,dict) else None),'status':'SUBMITTED' if status in (200,201,202) else 'REJECTED','response':reply})
 except Exception as ex:
  record.update({'status':'SUBMISSION_UNKNOWN_NO_RETRY','error':str(ex)})
 write_atomic(p,record)
 log('RESULT',aid,record['status'],record.get('http'),record.get('jobId'),str(record.get('error',''))[:140])
if __name__=='__main__':
 limit=int(sys.argv[1]) if len(sys.argv)>1 else 4
 batch=assets[:limit]
 log('BATCH_COUNT',len(batch),'GENERATE_GATEWAY',rt['baseUrl'])
 with concurrent.futures.ThreadPoolExecutor(max_workers=min(4,len(batch))) as pool:
  list(pool.map(run,batch))
