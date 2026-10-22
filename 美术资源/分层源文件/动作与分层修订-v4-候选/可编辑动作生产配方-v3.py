# -*- coding: utf-8 -*-
"""原创可编辑关键姿态 v3：非伪图层。保留 v1/v2，四个失败动作真实部件变形。"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
from xml.etree import ElementTree as ET
import zipfile,io,hashlib,json,math,copy,shutil
R=Path(__file__).resolve().parent
V2=R
V3=R/'__rebuild_output__'
if V3.exists():
    # ONLY delete current generator's incomplete directory when manifest is absent.
    assert not (V3/'动作与源文件契约-v3.json').exists(), 'REFUSE_OVERWRITE_VALID_V3'
    shutil.rmtree(V3)
V3.mkdir(parents=True)
W=H=96
INK='#263947';GREEN='#639753';SHADE='#416c3c';ARMOR='#82664b'
def E():return Image.new('RGBA',(W,H))
def draw(fn):
 im=E();d=ImageDraw.Draw(im);fn(d);return im
def paste_shift(im,xy):
 out=E();out.alpha_composite(im,tuple(int(round(a)) for a in xy));return out
def rot(im,a,pt=(48,50)):
 return im.rotate(a,Image.Resampling.NEAREST,center=pt)
def load(kind):
 fn=V2/kind/(kind+'-基础分层.ora')
 with zipfile.ZipFile(fn) as z:
  l=ET.fromstring(z.read('stack.xml')).find('stack')
  layers=[]
  for node in reversed(l.findall('layer')):
   with Image.open(io.BytesIO(z.read(node.get('src')))) as im:
    layers.append({'name':node.get('name'),'image':im.convert('RGBA').copy(),
    'visible':node.get('visibility','visible')=='visible'})
  return layers
def alpha_line(d,points,fill,width):
 d.line(points,fill=fill,width=width,joint='curve')
 for x,y in (points[1:-1] if len(points)>2 else []):
  rr=width//2;d.ellipse((x-rr,y-rr,x+rr,y+rr),fill=fill)
def l_orc_legs(side,i,action):
 # 通过腰、膝、脚掌三段的重新绘制表现实际支撑/摆腿，而非整体图像平移。
 hipx=38 if side=='L' else 58
 stance=[0,1,2,3,4,5,6,7][i]
 if action=='walk':
  footsteps=[(-6,0),(-4,-2),(0,-5),(5,-2),(7,0),(4,-2),(0,-6),(-5,-2)]
  swing=footsteps[(i+(4 if side=='R' else 0))%8]
  x=hipx+swing[0];height=swing[1]
  # stance when opposite leg is airborne: foot remains planted at ground line 82.
  if side=='L' and i in (0,1,4,5):x=hipx-2;height=0
  if side=='R' and i in (2,3,6,7):x=hipx+2;height=0
  fy=81+height
 else:
  x=hipx+((-i//2) if side=='L' else (i//2))
  fy=81
 knee=(round((hipx+x)/2)+(-2 if side=='L' else 2),67-abs(x-hipx)//3)
 def paint(d):
  alpha_line(d,[(hipx,57),knee,(x,fy-5)],INK,13)
  alpha_line(d,[(hipx,57),knee,(x,fy-6)],'#567844',10)
  alpha_line(d,[(hipx,59),knee],GREEN,3)
  d.polygon([(x-8,fy-6),(x+6,fy-6),(x+10,fy),(x+7,fy+3),(x-9,fy+3)],fill=INK)
  d.polygon([(x-7,fy-5),(x+5,fy-5),(x+8,fy),(x-7,fy+1)],fill='#76603e')
  d.line([(x-6,fy-3),(x+4,fy-3)],fill='#cead61',width=2)
 return draw(paint)
def l_orc_arm(kind,i,action):
 isRight=(kind=='right')
 a=(69,34) if isRight else (28,34)
 if action=='walk':
  sw=[-7,-4,0,5,7,4,0,-5][i]*(1 if isRight else -1)
  f=(74+sw//2,50+abs(sw)//4) if isRight else (22+sw//2,50+abs(sw)//4)
 elif action=='attack':
  sw=[0,-2,-4,-5,6,5,2,0][i]
  f=(76+sw,48+[-1,-5,-8,-11,5,3,0,0][i]) if isRight else (23-sw//3,53+abs(sw)//3)
 else:
  f=(76,50) if isRight else (23,52)
 elbow=(round((a[0]+f[0])/2)+(3 if isRight else -3),round((a[1]+f[1])/2)+1)
 def paint(d):
  alpha_line(d,[a,elbow,f],INK,14)
  alpha_line(d,[a,elbow,f],GREEN,10)
  d.ellipse((a[0]-7,a[1]-6,a[0]+7,a[1]+6),fill='#a18a5b',outline=INK,width=2)
  d.ellipse((f[0]-6,f[1]-6,f[0]+6,f[1]+6),fill=GREEN,outline=INK,width=2)
 return draw(paint),f
def axe(pivot,tip,flash=False):
 # 不旋转整个原画，而是分层以稳定持握点绘制轴杆、斧刃及斩击光轨。
 px,py=pivot;tx,ty=tip
 dx=tx-px;dy=ty-py;norm=max(1,(dx*dx+dy*dy)**.5)
 nx,ny=-dy/norm,dx/norm
 def paint(d):
  alpha_line(d,[(px,py),(tx,ty)],INK,7)
  alpha_line(d,[(px,py),(tx,ty)],'#826847',4)
  # 在右外侧切削轮廓，锋刃不与头部重叠
  verts=[(int(tx+nx*3),int(ty+ny*3)),
         (int(tx+nx*11+dx/norm*5),int(ty+ny*11+dy/norm*5)),
         (int(tx+nx*10+dx/norm*15),int(ty+ny*10+dy/norm*15)),
         (int(tx+dx/norm*13),int(ty+dy/norm*13)),
         (int(tx-nx*2),int(ty-ny*2))]
  d.polygon(verts,fill='#aec9cf')
  d.line(verts+[verts[0]],fill=INK,width=2,joint='curve')
  d.line([verts[1],verts[2]],fill='#f2ffff',width=2)
  d.ellipse((px-3,py-3,px+3,py+3),fill='#7a5835',outline=INK)
 return draw(paint)
def orc(i,action,base):
 ls={v['name']:v['image'] for v in base if v['visible']}
 def find(s):return next(k for k in ls if s in k)
 head=ls[find('头部')]
 body=ls[find('盔甲身体')]
 le=ls[find('左腿')];ri=ls[find('右腿')]
 parts=[]
 phase=i
 if action=='walk':
  bodyBob=[0,1,2,1,0,1,2,1][i]
  bodySway=[0,1,1,0,0,-1,-1,0][i]
  parts.append(('01_左腿_逐步重绘',l_orc_legs('L',i,action)))
  parts.append(('02_右腿_逐步重绘',l_orc_legs('R',i,action)))
  parts.append(('03_胸甲_重心移动',paste_shift(body,(bodySway,bodyBob))))
  la,_=l_orc_arm('left',i,action);ra,grip=l_orc_arm('right',i,action)
  parts.append(('04_左臂_反向摆动',la));parts.append(('05_右臂_反向摆动',ra))
  parts.append(('06_头部_稳定目光',paste_shift(head,(bodySway,bodyBob))))
  parts.append(('07_武器_肩侧固定',axe(grip,(84+bodySway,12+bodyBob))))
 elif action=='attack':
  # 8个动作的视觉语义：就绪、预备、蓄力、举斧、下劈、接触、后摇、恢复
  bodyTilt=[0,1,2,2,-3,-2,-1,0][i]
  bodyShift=[(0,0),(0,0),(-1,0),(-1,0),(2,1),(1,1),(0,1),(0,0)][i]
  parts.extend([('01_左腿_定桩',l_orc_legs('L',i,action)),('02_右腿_前踏',l_orc_legs('R',i,action))])
  parts.append(('03_胸甲_出手前后重心',paste_shift(rot(body,bodyTilt,(48,60)),bodyShift)))
  larm,_=l_orc_arm('left',i,action);rarm,grip=l_orc_arm('right',i,action)
  parts.append(('04_左臂_护卫',larm));parts.append(('05_右臂_举斧',rarm))
  parts.append(('06_头部_不挡武器',paste_shift(head,(bodyShift[0],0))))
  # 斧刃始终保持在脸的外侧，挥击弧线在右侧下方
  tips=[(82,12),(86,7),(89,8),(92,17),(92,38),(90,51),(88,33),(83,12)]
  parts.append(('07_战斧_真实独立挥击路径',axe(grip,tips[i])))
  if i in (4,5):
   arc=draw(lambda d:d.arc((76,20,99,67),20,135,fill='#ffe299',width=3))
   parts.append(('08_斩击轨迹_只在命中阶段',arc))
 elif action=='death':
  # 肢体先失衡，随后身体向右侧跌倒，头部与躯干分层下坠，武器脱手。
  # 终帧不是整张像素图的旋转/淡出。
  fall=[0,1,4,9,15,20,23,25][i]
  tilt=[0,3,7,12,20,35,48,58][i]
  leftFoot=draw(lambda d:d.polygon([(26-i,73),(36-i,72),(36-i,84),(25-i,84)],fill='#68503a',outline=INK,width=2))
  rightFoot=draw(lambda d:d.polygon([(58+i,72),(71+i,74),(73+i,84),(58+i,84)],fill='#665038',outline=INK,width=2))
  parts.extend([('01_左腿_弯曲跪落',leftFoot),('02_右腿_向外崩塌',rightFoot)])
  torso=paste_shift(rot(body,-tilt,(47,60)),(int(fall*.45),int(fall*.5)))
  headPart=paste_shift(rot(head,-tilt*.75,(47,36)),(int(fall*.65),int(fall*.75)))
  parts.append(('03_胸甲_逐级倒地',torso))
  la= paste_shift(rot(ls[find('左臂')],-tilt*.6,(28,41)),(int(fall*.25),int(fall*.65)))
  ra= paste_shift(rot(ls[find('右臂')],-tilt*.5,(69,39)),(int(fall*.60),int(fall*.55)))
  parts.extend([('04_左臂_撑地',la),('05_右臂_脱力',ra),('06_头部_单独坠落',headPart)])
  dropped=[(83,13),(85,17),(89,25),(90,37),(88,54),(80,69),(75,76),(73,78)][i]
  pieces=axe((75+min(8,i),51+min(18,i*3)),dropped)
  parts.append(('07_战斧_脱手下坠',pieces))
  if i>=5:
   dust=draw(lambda d:[d.ellipse((27+j*11,78-(i-5),32+j*11,82+(i-5)),fill='#8c7451') for j in range(4)])
   parts.append(('08_着地尘土_碰撞帧',dust))
 else:raise ValueError(action)
 return parts
def core(i,base):
 layers={x['name']:x['image'] for x in base if x['visible']}
 crystal=next(im for n,im in layers.items() if '完整主晶体' in n)
 out=[(n,im.copy()) for n,im in layers.items() if '完整主晶体' not in n and '护爪' not in n]
 guard=next(im for n,im in layers.items() if '护爪' in n)
 # 使用不规则噪声Voronoi对原始水晶像素逐块归属，避免六个相同扇形。
 seeds=[(37,12),(61,13),(29,39),(49,33),(67,44),(40,61),(58,68)]
 masks=[Image.new('L',(W,H)) for s in seeds]
 mp=[x.load() for x in masks]
 cp=crystal.load()
 for y in range(H):
  for x in range(W):
   if cp[x,y][3]==0:continue
   jitter=math.sin(y*.56+x*.39)*3.3 + math.sin(y*.2-x*.71)*2.6
   distances=[(x-sx)**2+(y-sy)**2+(jitter*(k%3-1)*4) for k,(sx,sy) in enumerate(seeds)]
   index=min(range(len(seeds)),key=lambda n:distances[n])
   mp[index][x,y]=255
 frags=[]
 for k,m in enumerate(masks):
  im=E();im.paste(crystal,(0,0),m);frags.append(im)
 if i<3:
  out.append(('02_完整主晶体',crystal))
  if i:
   def crack(d):
    d.line([(47,14),(46,25),(43,31),(49,40)],fill='#17374d',width=2)
    if i>=2:
     d.line([(43,31),(34,39),(38,49),(32,56)],fill='#163c50',width=2)
     d.line([(49,40),(62,48),(59,57),(65,63)],fill='#163c50',width=2)
   out.append(('03_动态裂纹叠层',draw(crack)))
 elif i<7:
  velocities=[(-.45,-.65),(.7,-.8),(-.8,.05),(.1,-.35),(.9,.3),(-.25,.85),(.65,.75)]
  for k,frag in enumerate(frags):
   speed=i-2
   dx,dy=velocities[k]
   off=(int(dx*speed*4),int(dy*speed*4+speed*speed*.5))
   moved=paste_shift(rot(frag,(k-3)*1.7*speed,seeds[k]),off)
   out.append((f'02_独立不规则晶块_{k+1:02}',moved))
  dust=draw(lambda d:[d.ellipse((max(1,min(92,48+int(math.cos(j*1.45)*(9+7*(i-2))))),
                                   max(1,min(92,38+int(math.sin(j*.93)*(13+5*(i-2))))),
                                   max(2,min(95,49+int(math.cos(j*1.45)*(9+7*(i-2))))),
                                   max(2,min(95,39+int(math.sin(j*.93)*(13+5*(i-2)))))),
                                  fill='#79dcf4') for j in range(6)])
  out.append(('03_裂晶粒子',dust))
 else:
  # 残骸保留在底座上，主体已经破裂殆尽；结束状态持续可读。
  for k,frag in enumerate(frags):
   if k%2==0:
    moved=paste_shift(rot(frag,(-1 if k%3 else 1)*16,seeds[k]),((k-3)*7,23+k%3*3))
    out.append((f'02_残留晶块_{k+1}',moved))
  out.append(('03_底座残晶辉光',draw(lambda d:d.arc((26,67,72,79),0,180,fill='#4beeff',width=2))))
 out.append(('09_金属护爪_保护底座',guard))
 return out
def composite(ls):
 out=E()
 for _,im in ls:out.alpha_composite(im)
 return out
def zipora(dest,ls):
 st=ET.Element('image',{'version':'0.0.3','w':str(W),'h':str(H),'name':dest.stem})
 root=ET.SubElement(st,'stack')
 with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED) as z:
  z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
  merge=composite(ls);bf=io.BytesIO();merge.save(bf,'PNG')
  z.writestr('mergedimage.png',bf.getvalue())
  z.writestr('Thumbnails/thumbnail.png',bf.getvalue())
  for index,(name,im) in reversed(list(enumerate(ls))):
   data=io.BytesIO();im.save(data,'PNG')
   src=f'data/layer{index:02}.png'
   z.writestr(src,data.getvalue())
   ET.SubElement(root,'layer',{'name':name,'src':src,'x':'0','y':'0','opacity':'1.0',
                              'visibility':'visible','composite-op':'svg:src-over'})
  z.writestr('stack.xml',ET.tostring(st,encoding='utf-8',xml_declaration=True))
def main():
 actions={'兽人小兵':['walk','attack','death'],'城防水晶':['shatter']}
 manifest={'projectId':'live-turret-defense','version':'v3-art-candidate',
 'format':'editable OpenRaster each frame + independent per-frame components, not baked-only sheet',
 'camera':'2D_topdown','pixelCanvas':[W,H],'frameMs':110,
 'origin':'V2 editable original layers + new independent articulation and fracture paths',
 'approved':False,'actions':[]}
 for actor,acts in actions.items():
  base=load(actor)
  # Do not fake a master: keep editable master ORA unchanged in separate v3 version
  root=V3/actor;root.mkdir(parents=True)
  shutil.copy2(V2/actor/(actor+'-可编辑分层.ora'),root/(actor+'-基础分层.ora'))
  for action in acts:
   target=root/action;target.mkdir()
   frames=[]
   for i in range(8):
    layers=orc(i,action,base) if actor=='兽人小兵' else core(i,base)
    canvas=composite(layers)
    path=target/f'帧{i+1:03}.png';canvas.save(path)
    zipora(target/f'帧{i+1:03}-分层.ora',layers)
    frames.append(canvas)
   assert len(set(f.tobytes() for f in frames))==8
   sheet=Image.new('RGBA',(4*W,2*H))
   for i,im in enumerate(frames):sheet.alpha_composite(im,((i%4)*W,(i//4)*H))
   sheet.save(root/(action+'-关键姿态-4x2.png'))
   gifs=[im.resize((W*4,H*4),Image.Resampling.NEAREST) for im in frames]
   gifs[0].save(root/(action+'-动作预览.gif'),save_all=True,append_images=gifs[1:],duration=110,loop=0,disposal=2)
   manifest['actions'].append({'actor':actor,'name':action,'frames':8,'editableFrames':8,
                               'eventFrame':4 if action=='attack' else 5 if action=='shatter' else None,
                               'semanticReview':'CANDIDATE_VISUAL_REVIEW_PENDING','path':str(target.relative_to(V3))})
 # Unchanged three towers and source contract are included as separate reference, no needless frame regeneration.
 for tower in ('连珠速射塔','熔芯重炮塔','寒霜喷射塔'):
  d=V3/tower;d.mkdir()
  shutil.copy2(V2/tower/(tower+'-可编辑分层.ora'),d/(tower+'-可编辑分层.ora'))
  src=V2/tower/'动作帧候选'/'attack'
  dst=d/'attack';dst.mkdir()
  for p in sorted(src.glob('帧*.png')):shutil.copy2(p,dst/p.name)
  manifest['actions'].append({'actor':tower,'name':'attack','frames':8,
               'editableFrames':0,'sourceOra':tower+'-可编辑分层.ora',
               'sourceRecipe':'refer to V2 recipe file','semanticReview':'REUSED_V2_CANDIDATE',
               'path':str(dst.relative_to(V3))})
 manifest['rejectedV2Issues']=['orc walk unconvincing planting','orc axe crossing face',
             'orc death spinning rigid frame','crystal unnatural six equal sectors']
 (V3/'动作与源文件契约-v3.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 with zipfile.ZipFile(V3.parent/'分层关键姿态-v3-待审核.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
  for f in V3.rglob('*'):
   if f.is_file():z.write(f,f.relative_to(V3.parent))
 out={'version':'v3 candidate','root':str(V3),'totalActions':len(manifest['actions']),
      'totalFrames':sum(a['frames'] for a in manifest['actions']),
      'newEditableFrameOra':sum(a['editableFrames'] for a in manifest['actions']),
      'v2SourceUntouched':True}
 print(json.dumps(out,ensure_ascii=True))
if __name__=='__main__':main()
