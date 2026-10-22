# -*- coding: utf-8 -*-
"""v4 生产：真正部件动画重新导出160x144留白；斧刃宽化；死亡分层倒地。保留全部旧版本。"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
from xml.etree import ElementTree as ET
import types,math,zipfile,io,json,hashlib,shutil,os
ROOT=Path(__file__).resolve().parent
OLD=ROOT
NEW=ROOT/'__isolated_rebuild__'
CANVAS=(160,144);W,H=CANVAS;OX,OY=32,20
def empty():return Image.new('RGBA',CANVAS,(0,0,0,0))
def pad(img,xy=(OX,OY)):
 dst=empty()
 assert img.mode=='RGBA'
 dst.alpha_composite(img,xy)
 return dst
def composite(layers):
 dst=empty()
 for name,layer in layers:
  assert layer.size==CANVAS,(name,layer.size)
  dst.alpha_composite(layer)
 return dst
def ora(path,layers):
 merged=composite(layers)
 e=ET.Element('image',{'version':'0.0.3','w':str(W),'h':str(H),'name':path.stem})
 stack=ET.SubElement(e,'stack')
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
  buffer=io.BytesIO();merged.save(buffer,'PNG');z.writestr('mergedimage.png',buffer.getvalue())
  z.writestr('Thumbnails/thumbnail.png',buffer.getvalue())
  for i,(name,layer) in reversed(list(enumerate(layers))):
   b=io.BytesIO();layer.save(b,'PNG');src=f'data/layer{i:02}.png';z.writestr(src,b.getvalue())
   ET.SubElement(stack,'layer',{'name':name,'src':src,'x':'0','y':'0',
                               'opacity':'1.0','visibility':'visible','composite-op':'svg:src-over'})
  z.writestr('stack.xml',ET.tostring(e,encoding='utf-8',xml_declaration=True))
 return merged
def draw(fn):
 im=empty();fn(ImageDraw.Draw(im));return im
def thickAxe(pivot,tip):
 px,py=pivot;tx,ty=tip
 dx=tx-px;dy=ty-py
 d=math.hypot(dx,dy) or 1
 ux,uy=dx/d,dy/d;nx,ny=-uy,ux
 def pt(a,b):
  return (round(tx+a*ux+b*nx),round(ty+a*uy+b*ny))
 def paint(g):
  g.line([(px,py),(tx,ty)],fill='#1b303b',width=8)
  g.line([(px,py),(tx,ty)],fill='#735638',width=5)
  g.line([(px+ux*2,py+uy*2),(tx,ty)],fill='#af8052',width=2)
  # 斧头宽阔外凸刃，分明的凹形内缘与突出锋尖。
  wedge=[pt(-7,0),pt(-13,-9),pt(-23,-16),pt(-6,-22),pt(11,-19),pt(14,-11),pt(5,-6),pt(5,0)]
  g.polygon(wedge,fill='#a6bbc1')
  g.line(wedge+[wedge[0]],fill='#223945',width=3,joint='curve')
  g.polygon([pt(-17,-13),pt(-6,-19),pt(9,-16),pt(3,-10)],fill='#e0f5f3')
  g.line([pt(-23,-16),pt(-6,-22),pt(11,-19)],fill='#f7f6cf',width=2,joint='curve')
  g.ellipse((px-4,py-4,px+4,py+4),fill='#8f6c46',outline='#243b43',width=2)
 return draw(paint)
def load_v3_as_code():
 # Clean import: strip earlier module-level output directory initialization.
 filename=OLD/'可编辑动作生产配方-v3.py'
 s=filename.read_text('utf8')
 i=s.index('if V3.exists():');j=s.index('W=H=96',i)
 s=s[:i]+s[j:]
 m=types.ModuleType('v3_layer_read_only')
 m.__file__=str(filename)
 exec(compile(s,str(filename),'exec'),m.__dict__)
 return m
def orc_rebuilt(m,kind,index,base):
 if kind in ('walk','attack'):
  # 160px drawing buffer, 96px component origins: source-mother shapes stay same absolute display size.
  m.W=160;m.H=144
  m.axe=thickAxe
  original=m.orc(index,kind,base)
  # all independently rendered components positioned on unchanged character origin.
  out=[]
  for name,layer in original:
   out.append((name,pad(layer)))
  return out
 return orc_death(index,base)
def original_piece(base,key):
 return next(row['image'] for row in base if key in row['name'] and row['visible'])
def rotate_at(img,degrees,center):
 return img.rotate(degrees,Image.Resampling.NEAREST,center=center)
def move(img,x,y):
 dst=empty();dst.alpha_composite(img,(round(x),round(y)));return dst
def orc_death(i,base):
 """Stable floor line y=108. Torso pivots at hip; helmet follows torso; weapon detaches to ground."""
 body=pad(original_piece(base,'盔甲身体'))
 head=pad(original_piece(base,'头部'))
 larm=pad(original_piece(base,'左臂'))
 rarm=pad(original_piece(base,'右臂'))
 Lleg=pad(original_piece(base,'左腿'))
 Rleg=pad(original_piece(base,'右腿'))
 hip=(48+OX,68+OY)
 angles=[0,-3,-8,-16,-31,-54,-77,-86]
 tilt=angles[i]
 # body pivots around hip, not whole sprite. Head and armor rotate consistently into side-fall.
 body=rotate_at(body,tilt,hip)
 head=rotate_at(head,tilt,hip)
 larm=rotate_at(larm,tilt*.83,hip)
 rarm=rotate_at(rarm,tilt*.87,hip)
 if i<=2:
  Lleg=move(Lleg,-i,0)
  Rleg=move(Rleg,i,0)
 else:
  Lleg=rotate_at(Lleg,[-1,-1,-3,-12,-25,-30,-38,-42][i],(36+OX,60+OY))
  Rleg=rotate_at(Rleg,[0,1,4,7,14,18,21,24][i],(58+OX,60+OY))
 layers=[('01_左腿_支撑到折叠',Lleg),('02_右腿_失衡侧跨',Rleg),('03_盔甲_绕髋倒伏',body),
         ('04_左臂_撑地',larm),('05_右臂_脱力',rarm),('06_头部_跟随倒地',head)]
 # separate impact debris + weapon. Use ground horizontal axe in final state, no spear silhouette.
 grip=[(75,51),(77,52),(79,54),(88,58),(101,65),(113,80),(113,98),(110,103)][i]
 tip=[(83,14),(87,17),(94,25),(111,39),(119,55),(124,75),(131,97),(131,102)][i]
 # already padded coords must use offset for initial 96-world positions but later pose values converted explicitly.
 grip=(grip[0]+OX,grip[1]+OY) if i<4 else grip
 tip=(tip[0]+OX,tip[1]+OY) if i<4 else tip
 layers.append(('07_宽刃战斧_脱手',thickAxe(grip,tip)))
 if i>=4:
  def dirt(d):
   for j in range(max(2,i-2)):
    x=94+j*8+(i-4)*2;y=107+round(math.sin(j*2.5)*(i-3))
    d.ellipse((x,y,x+3,y+2),fill='#806c51')
  layers.append(('08_落地撞击土尘',draw(dirt)))
 return layers
def core_rebuilt(m,index,base):
 m.W=m.H=96
 return [(n,pad(lay)) for n,lay in m.core(index,base)]
def write_images(folder,frames,action,actor):
 d=folder/actor/action;d.mkdir(parents=True,exist_ok=True)
 frameHashes=[]
 for i,layers in enumerate(frames):
  im=composite(layers)
  q=d/f'帧{i+1:03}.png';im.save(q)
  ora(d/f'帧{i+1:03}-分层.ora',layers)
  frameHashes.append(hashlib.sha256(im.tobytes()).hexdigest())
 assert len(set(frameHashes))==8,(actor,action)
 sheet=Image.new('RGBA',(W*4,H*2))
 for i,layers in enumerate(frames):
  sheet.alpha_composite(composite(layers),((i%4)*W,(i//4)*H))
 sheet.save(folder/actor/(action+'-4列2行透明母图.png'))
 gifs=[composite(fr).resize((320,288),Image.Resampling.NEAREST) for fr in frames]
 gifs[0].save(folder/actor/(action+'-动作预览.gif'),save_all=True,append_images=gifs[1:],duration=110,loop=0,disposal=2)
 return frameHashes
def main():
 if NEW.exists():raise RuntimeError('REFUSE_TO_OVERWRITE_V4')
 NEW.mkdir(parents=True)
 m=load_v3_as_code()
 for subject in ('兽人小兵','城防水晶'):
  (NEW/subject).mkdir()
  shutil.copy2(OLD/subject/(subject+'-基础分层.ora'),NEW/subject/(subject+'-基础分层.ora'))
 for subject in ('连珠速射塔','熔芯重炮塔','寒霜喷射塔'):
  (NEW/subject).mkdir()
  shutil.copy2(OLD/subject/(subject+'-基础分层.ora'),NEW/subject/(subject+'-基础分层.ora'))
 transitions=[]
 for actor,action in [('兽人小兵','walk'),('兽人小兵','attack'),('兽人小兵','death'),('城防水晶','shatter')]:
  base=m.load(actor)
  frames=[orc_rebuilt(m,action,i,base) if actor=='兽人小兵' else core_rebuilt(m,i,base) for i in range(8)]
  f=write_images(NEW,frames,action,actor)
  transitions.append({'subject':actor,'action':action,'frames':8,'editableORA':8,'hashes':f})
 for actor in ('连珠速射塔','熔芯重炮塔','寒霜喷射塔'):
  d=NEW/actor/'attack';d.mkdir(parents=True)
  arr=[]
  for i in range(8):
   p=OLD/actor/'attack'/f'帧{i+1:03}.png'
   with Image.open(p) as src:im=src.convert('RGBA');im=im if im.size==CANVAS else pad(im)
   im.save(d/f'帧{i+1:03}.png')
   arr.append(im)
  sheet=Image.new('RGBA',(W*4,H*2))
  for i,im in enumerate(arr):sheet.alpha_composite(im,((i%4)*W,(i//4)*H))
  sheet.save(NEW/actor/'attack-4列2行透明母图.png')
  frames=[im.resize((320,288),Image.Resampling.NEAREST) for im in arr]
  frames[0].save(NEW/actor/'attack-动作预览.gif',save_all=True,append_images=frames[1:],duration=110,loop=0,disposal=2)
  transitions.append({'subject':actor,'action':'attack','frames':8,'editableORA':0,
                     'sourceORA':f'{actor}-基础分层.ora','derivedFrom':'v3 unchanged art, padded only'})
 (NEW/'V4分层生产契约.json').write_text(json.dumps({
  'version':'v4 candidate','projectId':'live-turret-defense','frame':[160,144],
  'visibleBodySize':'unchanged from source 96px','originOffset':[OX,OY],
  'pivot':[0.5,0.5],'groundLineYFromTop':105,'frameDurationMs':110,'sheet':{'columns':4,'rows':2,'size':[640,288]},
  'textureFilter':'nearest','approved':False,'artQuality':'PENDING',
  'sourceVersion':'v3 original editable ORA','sourceUnchanged':True,
  'renderingNotes':'sprites 160x144 UITransform to preserve native original 96 body actual size',
  'actions':transitions
 },ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'status':'V4_GENERATED','root':str(NEW),'animationGroups':7,'pngFrames':56,
                   'editableFrameORA':32,'sheetCount':7,'frameCanvas':[W,H]},ensure_ascii=True))
if __name__=='__main__':main()
