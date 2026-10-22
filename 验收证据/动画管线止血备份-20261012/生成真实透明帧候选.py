# -*- coding: utf-8 -*-
"""将真实MCP母素材加工为可加载的逐帧动画候选。不得将程序性动作冒充已审美术。"""
import pathlib,json,hashlib,math,os,sys
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageEnhance,ImageChops
root=pathlib.Path(__file__).resolve().parents[1]
contract=json.loads((root/'美术资源/资源与动作合同-v0.4.json').read_text('utf-8'))
originals=root/'美术资源/原始生成/批量母素材'
ledger=root/'任务包/素材生成任务-v0.5'
result=root/'美术资源/动画候选验收-v0.5.json'
mapping={'enemy_orc':'enemy_orc_grunt','enemy_boss':'enemy_orc_boss'}
def key_out(img):
 rgb=np.array(img.convert('RGB'))
 # near-white pixels connected to border are background; preserve white details disconnected from border
 white=((rgb.min(axis=2)>222)&(rgb.max(axis=2)-rgb.min(axis=2)<33)).astype('uint8')
 n,labels,stats,cent=cv2.connectedComponentsWithStats(white,8)
 borders=np.unique(np.concatenate([labels[0,:],labels[-1,:],labels[:,0],labels[:,-1]]))
 bg=np.isin(labels,borders)
 alpha=np.where(bg,0,255).astype('uint8')
 # discard small detached corner marks/artifacts; retain biggest central connected unit
 mask=(alpha>0).astype('uint8')
 count,lbs,areas,cs=cv2.connectedComponentsWithStats(mask,8)
 if count>1:
  sizes=areas[1:,cv2.CC_STAT_AREA]
  main=1+np.argmax(sizes)
  center=cs[main]
  keep=np.zeros_like(mask,dtype=bool)
  for idx in range(1,count):
   area=areas[idx,cv2.CC_STAT_AREA];cx,cy=cs[idx]
   # Keep main object and genuine detached large VFX pixels near image center
   if idx==main or (area>sizes.max()*0.035 and math.hypot(cx-center[0],cy-center[1])<min(rgb.shape[:2])*0.3):
    keep|=(lbs==idx)
  alpha=np.where(keep,alpha,0).astype('uint8')
 rgba=np.dstack([rgb,alpha])
 arr=Image.fromarray(rgba,'RGBA')
 bbox=arr.getbbox()
 if not bbox:raise ValueError('empty-after-alpha')
 return arr.crop(bbox)
def layout(item,crop):
 w,h=item['canvas']
 # Expand sprite with transparent pixels, preserve bottom pivot. 85% for projectiles/effects, 80% other.
 targetW=int(w*(0.74 if item['kind'] in ('tower','enemy','core') else 0.83))
 targetH=int(h*(0.78 if item['kind'] in ('tower','enemy','core') else 0.82))
 scale=min(targetW/crop.width,targetH/crop.height)
 outsz=(max(1,int(crop.width*scale)),max(1,int(crop.height*scale)))
 piece=crop.resize(outsz,Image.Resampling.NEAREST)
 base=Image.new('RGBA',(w,h),(0,0,0,0))
 x=(w-piece.width)//2
 y=int(h*0.86)-piece.height if item['kind'] in ('tower','enemy','core') else (h-piece.height)//2
 y=max(1,min(h-piece.height-1,y))
 base.alpha_composite(piece,(x,y))
 return base
def shifted(base,dx=0,dy=0,brightness=1.0):
 if brightness!=1.0:
  rgb=ImageEnhance.Brightness(base.convert('RGB')).enhance(brightness)
  rgb.putalpha(base.getchannel('A'));base=rgb
 canvas=Image.new('RGBA',base.size,(0,0,0,0))
 canvas.alpha_composite(base,(dx,dy))
 return canvas
def frame(item,act,i,n,base):
 w,h=base.size
 phase=2*math.pi*i/n
 # actual motion: body bobbing, recoil, hit feedback, VFX growth and fade
 if act in ('待机','行走'):
  dx=(int(round(math.sin(phase)*1.3)) if act=='行走' else 0)
  dy=int(round(math.cos(phase)*1.25))
  out=shifted(base,dx,dy,1.0+0.04*math.sin(phase))
 elif act in ('攻击','飞行'):
  recoil=2 if act=='攻击' else 1
  out=shifted(base,int(round(math.sin(phase)*recoil)),int(round(math.cos(phase)*recoil)))
  if act=='攻击':
   d=ImageDraw.Draw(out)
   x=w//2+int(3*math.sin(phase));y=max(4,int(h*.15))
   k=1+(i%3);d.polygon([(x,y-5-k),(x-2-k,y+2),(x+2+k,y+2)],fill=(255,205,65,205))
 elif act in ('升级','受击'):
  out=shifted(base,0,0,1.0+(0.12 if i%2==0 else 0))
  d=ImageDraw.Draw(out);rad=8+int(i/max(1,n-1)*min(w,h)*.45)
  color=(110,228,255,max(30,160-i*10)) if act=='升级' else (255,115,86,max(60,180-i*24))
  d.ellipse((w//2-rad,h//2-rad,w//2+rad,h//2+rad),outline=color,width=1)
 elif act in ('死亡','破碎'):
  scale=max(.25,1-i/max(1,n-1)*.72)
  piece=base.resize((max(1,int(w*scale)),max(1,int(h*scale))),Image.Resampling.NEAREST)
  faded=piece.copy(); faded.putalpha(piece.getchannel('A').point(lambda a:int(a*(1-i/n))))
  out=Image.new('RGBA',(w,h),(0,0,0,0));out.alpha_composite(faded,((w-piece.width)//2,(h-piece.height)//2+int(i*.4)))
 elif act in ('爆炸','减速'):
  out=shifted(base,0,0)
  d=ImageDraw.Draw(out)
  rad=3+int((i+1)/n*(min(w,h)*.42))
  color=(255,115+(i*9)%120,35,max(35,210-i*18)) if act=='爆炸' else (110,226,255,max(35,170-i*12))
  d.ellipse((w//2-rad,h//2-rad,w//2+rad,h//2+rad),outline=color,width=2)
 else:out=shifted(base,0,0)
 return out
report={'status':'CANDIDATE_NOT_FINAL','contractVersion':'0.4','source':'win-unpacked-mcp-generated-master, procedural sprite-motion processing','assets':[]}
for item in contract['assets']:
 sourceId=mapping.get(item['id'],item['id'])
 p=originals/(sourceId+'-母素材-原始.png')
 a={'id':item['id'],'name':item['name'],'sourceId':sourceId,'sourceExists':p.is_file(),'actions':[]}
 if not p.is_file():report['assets'].append(a);continue
 with Image.open(p) as raw:
  raw.load()
  crop=key_out(raw)
 base=layout(item,crop)
 master=root/'美术资源/透明母素材候选'/ (item['id']+'.png')
 master.parent.mkdir(parents=True,exist_ok=True)
 base.save(master)
 a['transparentMaster']=str(master.relative_to(root));a['sourceSha256']=hashlib.sha256(p.read_bytes()).hexdigest()
 for action,settings in item['animations'].items():
  files=[];digests=[]
  for i,rel in enumerate(settings['frames']):
   path=root/rel
   path.parent.mkdir(parents=True,exist_ok=True)
   rendered=frame(item,action,i,len(settings['frames']),base)
   # enforce corner alpha clear
   rendered.putpixel((0,0),(0,0,0,0));rendered.putpixel((item['canvas'][0]-1,0),(0,0,0,0))
   rendered.putpixel((0,item['canvas'][1]-1),(0,0,0,0));rendered.putpixel((item['canvas'][0]-1,item['canvas'][1]-1),(0,0,0,0))
   if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()!=hashlib.sha256(path.read_bytes()).hexdigest():raise ValueError('impossible')
   rendered.save(path)
   files.append(str(path.relative_to(root)));digests.append(hashlib.sha256(rendered.tobytes()).hexdigest())
  a['actions'].append({'action':action,'frameCount':len(files),'frameDurationMs':settings['frameDurationMs'],'anchor':settings['anchor'],'uniqueFramePayloads':len(set(digests)),'frameDir':str(path.parent.relative_to(root)),'semanticReview':'PENDING','engineImport':'PENDING'})
 report['assets'].append(a)
report['processedAssets']=sum(a['sourceExists'] for a in report['assets'])
report['actionsCreated']=sum(len(a['actions']) for a in report['assets'])
report['framesCreated']=sum(z['frameCount'] for a in report['assets'] for z in a['actions'])
report['warnings']=['Source angles and pixel style are not approved. Animation is procedurally derived, NOT individually web-generated frame art. Do not mark final/G2 passed until actual game import and visual review.']
result.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'status':report['status'],'processed':report['processedAssets'],'actions':report['actionsCreated'],'frames':report['framesCreated'],'missing':[a['id'] for a in report['assets'] if not a['sourceExists']]},ensure_ascii=False))
