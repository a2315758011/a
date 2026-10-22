# -*- coding: utf-8 -*-
"""只恢复已提交图片，从网关复制回工程；不执行任何生成提交。"""
import json,pathlib,urllib.request,urllib.error,hashlib,shutil,datetime,os,sys
from PIL import Image,ImageOps,ImageDraw
root=pathlib.Path(__file__).resolve().parents[1]
tasks=root/'任务包'/'素材生成任务-v0.5'
out=root/'美术资源'/'原始生成'/'批量母素材'
out.mkdir(parents=True,exist_ok=True)
rt=json.loads((pathlib.Path.home()/'Desktop/deliverable/.infra/GENERATION_GATEWAY_RUNTIME.json').read_text('utf-8'))
token=pathlib.Path(rt['tokenFile']).read_text('utf-8').strip()
def atomic(p,x):
 tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf-8');os.replace(tmp,p)
def get_job(jid):
 req=urllib.request.Request(rt['baseUrl']+'/v1/jobs/'+jid,headers={'X-Moyin-Gateway-Token':token})
 with urllib.request.urlopen(req,timeout=17) as r: j=json.load(r)
 return j.get('job') or j
summary=[]
for p in sorted(tasks.glob('*.json')):
 d=json.loads(p.read_text('utf-8'));jid=d.get('jobId')
 if not jid:
  summary.append((d.get('id'),'UNKNOWN_OR_NOT_SUBMITTED',None));continue
 try:
  j=get_job(jid)
  state=j.get('status');d['lastQueriedStatus']=state;d['lastQueriedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat()
  if state=='completed':
   art=j.get('artifacts') or (j.get('result') or {}).get('artifacts') or []
   if not art:raise ValueError('COMPLETED_BUT_NO_ARTIFACT')
   src=pathlib.Path(art[0].get('path') or '')
   if not src.is_file():raise ValueError('ARTIFACT_MISSING:'+str(src))
   dst=out/(d['id']+'-母素材-原始.png')
   digest=hashlib.sha256(src.read_bytes()).hexdigest()
   if dst.is_file() and hashlib.sha256(dst.read_bytes()).hexdigest()!=digest:raise ValueError('DEST_CONFLICT')
   if not dst.is_file():shutil.copy2(src,dst)
   with Image.open(dst) as im:im.load();dim=im.size;mode=im.mode
   d.update({'status':'MASTER_COPIED_PENDING_REVIEW','output':str(dst),'sha256':digest,'size':list(dim),'mode':mode,'artifacts':art})
  elif state in ('failed','cancelled'):
   d.update({'status':'FAILED_NO_RESUBMIT','error':j.get('error'),'providerAccount':j.get('request',{}).get('accountId')})
  else:d['status']='AWAITING_ORIGINAL_JOB'
  atomic(p,d)
  summary.append((d.get('id'),d.get('status'),state))
 except Exception as ex:
  d['inspectError']=str(ex);atomic(p,d);summary.append((d.get('id'),'QUERY_ERROR',str(ex)[:90]))
print('STATUS',json.dumps(summary,ensure_ascii=False))
pictures=[]
for p in sorted(out.glob('*-母素材-原始.png')):
 try:
  with Image.open(p) as im:
   im=im.convert('RGB');im.thumbnail((310,310))
   pictures.append((p.stem,im.copy()))
 except:pass
if pictures:
 cols=3;w,h=380,400;rows=(len(pictures)+cols-1)//cols
 sheet=Image.new('RGB',(w*cols,h*rows),'#c8c8c8');draw=ImageDraw.Draw(sheet)
 for i,(name,img) in enumerate(pictures):
  x=(i%cols)*w;y=(i//cols)*h
  sheet.paste(img,(x+(w-img.width)//2,y+20))
  draw.text((x+10,y+h-45),name,fill='black')
 preview=out/'母素材批次审图-非正式.jpg';sheet.save(preview,'JPEG',quality=83)
 print('PREVIEW',str(preview),'COUNT',len(pictures))
