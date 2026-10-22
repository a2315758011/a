# -*- coding: utf-8 -*-
"""本项目真实资源验收：不把占位PNG或单张角色图冒充动态资源。"""
import argparse,json,pathlib,hashlib,sys
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parent.parent
MANIFEST=ROOT/'美术资源'/'资源与动作合同-v0.4.json'
def check_manifest(m):
 errors=[]
 ids=set()
 for item in m.get('assets',[]):
  aid=item.get('id')
  if not aid or aid in ids:errors.append('重复或空资源ID:'+str(aid))
  ids.add(aid)
  kind=item.get('kind')
  animations=item.get('animations') or {}
  if kind in ('tower','enemy','core') and not animations:errors.append(aid+' 无动态动作合同')
  for aname,anim in animations.items():
   frames=anim.get('frames',[])
   if not isinstance(frames,list) or not frames:errors.append(aid+'/'+aname+' 缺少逐帧定义');continue
   if len(set(frames))!=len(frames):errors.append(aid+'/'+aname+' 帧路径重复')
   if not anim.get('frameDurationMs',0)>0:errors.append(aid+'/'+aname+' 帧时长无效')
   anchor=anim.get('anchor')
   if not isinstance(anchor,list) or len(anchor)!=2 or any(not isinstance(n,(int,float)) or n<0 or n>1 for n in anchor):errors.append(aid+'/'+aname+' 锚点无效')
 return errors
def validate_images(m):
 errors=[],[]
 report=[]
 for item in m['assets']:
  for name,anim in (item.get('animations') or {}).items():
   dims=set();missing=0
   for rel in anim.get('frames',[]):
    p=ROOT/pathlib.Path(rel)
    if not p.is_file():missing+=1;continue
    try:
     im=Image.open(p);im.load();dims.add(im.size)
     if im.mode!='RGBA':errors[0].append(str(rel)+' 非RGBA')
     else:
      a=im.getchannel('A')
      if a.getextrema()==(255,255):errors[0].append(str(rel)+' alpha全不透明')
      if a.getbbox() is None:errors[0].append(str(rel)+' 全透明空图')
      w,h=im.size
      pts=[a.getpixel((0,0)),a.getpixel((w-1,0)),a.getpixel((0,h-1)),a.getpixel((w-1,h-1))]
      if any(v!=0 for v in pts):errors[0].append(str(rel)+' 边角不透明')
    except Exception as ex:errors[0].append(str(rel)+' PNG无法解码 '+str(ex))
   if len(dims)>1:errors[0].append(item['id']+'/'+name+' 各帧画布大小不同')
   report.append(dict(assetId=item['id'],action=name,expected=len(anim['frames']),missing=missing,dimensions=[list(z) for z in dims]))
 return errors[0],report
def main():
 m=json.loads(MANIFEST.read_text('utf-8'))
 structural=check_manifest(m)
 media,report=validate_images(m)
 status='BLOCKED_NO_MEDIA' if any(x['missing'] for x in report) else 'FAILED' if structural or media else 'VERIFIED'
 if structural or media:status='FAILED'
 out={'status':status,'manifestSha256':hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),'structuralErrors':structural,'mediaErrors':media,'assets':len(m['assets']),'actions':len(report),'details':report}
 path=ROOT/'验收证据'/'动态资产机器验收-v0.4.json';path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf-8')
 print(json.dumps({'status':status,'assets':len(m['assets']),'actions':len(report),'missingActions':sum(x['missing']>0 for x in report),'errors':len(structural)+len(media)},ensure_ascii=False))
 if structural or media:sys.exit(2)
if __name__=='__main__':main()
