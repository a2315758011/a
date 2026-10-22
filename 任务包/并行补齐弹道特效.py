# -*- coding: utf-8 -*-
"""补齐发射物和特效母素材。和炮塔批次相同的全链路固定任务账本。"""
import pathlib,json,urllib.request,urllib.error,concurrent.futures,datetime,hashlib,os
root=pathlib.Path(__file__).resolve().parents[1]
ledger=root/'任务包'/'素材生成任务-v0.5';ledger.mkdir(exist_ok=True)
r=json.loads((pathlib.Path.home()/'Desktop/deliverable/.infra/GENERATION_GATEWAY_RUNTIME.json').read_text('utf-8'))
token=pathlib.Path(r['tokenFile']).read_text('utf-8').strip()
ids=[
('projectile_repeater','速射弹丸','tiny warm golden one-pixel-outline rapid turret bullet, short elongated yellow projectile seen directly from above, neat game pixel sprite'),
('projectile_mortar','重炮弹丸','single hefty red-bronze cannonball with ember orange core, overhead flat pixel sprite, one fireball projectile not an explosion'),
('projectile_frost','寒霜射流','single light cyan compressed ice magic blast travelling horizontally, blue short frozen wind streak, pixel art projectile'),
('fx_explosion','爆炸特效','one compact radial fiery explosion blast, orange and yellow ring of fire pixels, alpha-safe readable effects graphic, no environment'),
('fx_frost','冰雾特效','single ring-like translucent icy frost clouds with blue snow and tiny crystal pixels, flat overhead icy slow zone effect')
]
accs=['d3b71ce4-d61e-4adc-8f08-3c28262b6e48','b362bb9f-d46d-44cc-9a0c-811bd0afb728','3701a471-2d32-4cb2-aab6-8b9980015842','538465cc-e184-4e38-bdcd-684ab15a7bbf']
def run(t):
 i,name,desc=t; p=ledger/(i+'.json')
 if p.exists():
  d=json.loads(p.read_text('utf-8'));return (i,'SKIP_'+d.get('status','?'),d.get('jobId'))
 ix=ids.index(t);account=accs[ix%len(accs)];task='ART-MASTER-'+i.upper()+'-20261012'
 prompt='Generate ONE isolated original 2D top-down native pixel art sprite for a fantasy tower defense mobile game. Subject: '+desc+'. SINGLE graphic only, with crisp square jagged pixels, coarse limited-color palette, no smooth airbrush, no perspective, no 3D, no lettering, no logo, no shadows, no background tiles, no floor, no other sprites, no watermark. Pure uniform white RGB 255,255,255 blank background for clean segmentation. This is a game VFX component not a scene. Centered with wide blank margins.'
 body={'kind':'image','feature':'freedom_image','transport':'web','providerId':'web:'+account+':freedom_image','accountId':account,'pool':False,'sourceProjectId':'live-turret-defense','sourceTaskId':task,'idempotencyKey':'live-turret-defense-'+task+'-v05-once','prompt':prompt,'aspectRatio':'1:1','outputDir':str(root/'美术资源/原始生成/批量母素材')}
 rec={'id':i,'name':name,'sourceTaskId':task,'accountId':account,'promptSHA256':hashlib.sha256(prompt.encode()).hexdigest(),'status':'SUBMISSION_UNKNOWN_NO_RETRY','jobId':None,'submittedAt':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 def save(): 
  temp=p.with_suffix('.tmp');temp.write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n','utf-8');os.replace(temp,p)
 save()
 try:
  req=urllib.request.Request(r['baseUrl']+'/v1/jobs',data=json.dumps(body,ensure_ascii=False).encode('utf-8'),method='POST',headers={'X-Moyin-Gateway-Token':token,'Content-Type':'application/json;charset=utf-8'})
  with urllib.request.urlopen(req,timeout=30) as x:resp=json.load(x);status=x.status
  rec.update({'http':status,'status':'SUBMITTED' if status in (200,201,202) else 'REJECTED','jobId':(resp.get('job') or {}).get('id') or resp.get('jobId'),'response':resp})
 except urllib.error.HTTPError as e:
  rec.update({'status':'REJECTED','http':e.code,'error':e.read().decode('utf-8','replace')[:600]})
 except Exception as e:rec['error']=str(e)
 save();return (i,rec['status'],rec.get('jobId'))
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for result in pool.map(run,ids):print('RESULT',*result,flush=True)
