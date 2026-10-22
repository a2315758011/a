# -*- coding: utf-8 -*-
"""分层原件 (ORA) + 可复现关键姿态/部件动作配方。全新v2候选，不改正式资产。"""
from PIL import Image, ImageDraw,ImageChops,ImageStat
from pathlib import Path
from xml.etree import ElementTree as ET
import hashlib,json,zipfile,io,math,shutil,os
HERE=Path(__file__).resolve().parent
ROOT=next((q for q in Path(__file__).resolve().parents if (q/'美术资源'/'分层源文件').is_dir()),HERE)
V1=ROOT/'美术资源'/'分层源文件'/'首批原创样板-v1'
V2=HERE if (HERE/'分层动作资源清单-v2.json').exists() else ROOT/'美术资源'/'分层源文件'/'动作与分层修订-v2'
assert V1.is_dir() or V2.is_dir()
if __name__ == '__main__':
    if V2.exists():
        raise RuntimeError('NO_OVERWRITE: '+str(V2))
    V2.mkdir()
W=H=96
transparent=(0,0,0,0)
def empty():return Image.new('RGBA',(W,H),transparent)
def shift(im,x,y):
    out=empty();out.alpha_composite(im,(int(round(x)),int(round(y))));return out
def rotate(im,deg,pivot):
    return im.rotate(deg,resample=Image.Resampling.NEAREST,expand=False,center=pivot)
def drawlayer(fn):
    a=empty();fn(ImageDraw.Draw(a));return a
def poly(d,pts,c):d.polygon(pts,fill=c)
def circ(d,x,y,r,fill,outline=None,width=1):d.ellipse((x-r,y-r,x+r,y+r),fill=fill,outline=outline,width=width)
def polyfracture(sprite,step):
    # 在同一块水晶上逐步绘制裂纹并真正分离六块实体，非对整图淡出/缩小。
    if step<4:
        out=sprite.copy()
        def cracks(d):
            if step>=1:
                d.line([(46,12),(51,26),(43,38),(46,48)],fill=(16,41,58,235),width=2)
            if step>=2:
                d.line([(51,26),(61,28),(65,38)],fill=(17,54,76,255),width=3)
                d.line([(43,38),(36,43),(32,53)],fill=(22,61,85,255),width=2)
            if step>=3:
                d.line([(46,48),(57,56),(53,69)],fill=(9,48,64,255),width=3)
                d.line([(46,48),(39,61)],fill=(15,50,67,255),width=3)
        cracks(ImageDraw.Draw(out))
        return out
    vertices=[(48,3),(72,27),(66,62),(48,77),(29,62),(24,27)]
    cx,cy=48,43
    spread={4:2,5:5,6:10,7:17}[step]
    out=empty()
    for i in range(6):
        mask=Image.new('L',(W,H),0)
        d=ImageDraw.Draw(mask)
        p1=vertices[i];p2=vertices[(i+1)%6]
        d.polygon([(cx,cy),p1,p2],fill=255)
        frag=empty();frag.paste(sprite,(0,0),mask)
        midx=(cx+p1[0]+p2[0])/3;midy=(cy+p1[1]+p2[1])/3
        dx=(midx-cx)/16*spread;dy=(midy-cy)/16*spread+(step-4)*2
        # 坐标固定:同一个三角裂片从中心分离，底座未动
        frag=shift(frag,dx,dy)
        out.alpha_composite(frag)
    return out
def loadsource(kind):
    folder=V2/kind if (V2/kind/(kind+'-可编辑分层.ora')).exists() else V1/kind
    src=folder/(kind+'-可编辑分层.ora')
    with zipfile.ZipFile(src) as z:
        root=ET.fromstring(z.read('stack.xml'))
        stack=root.find('stack')
        layers=[]
        for l in reversed(stack.findall('layer')):
            with Image.open(io.BytesIO(z.read(l.attrib['src']))) as img:
                assert img.mode=='RGBA' and img.size==(W,H)
                layers.append({'name':l.attrib['name'],'source':img.copy(),
                               'visible':l.attrib.get('visibility','visible')=='visible'})
    return src,layers
def compose(layers,action,index,kind):
    g=empty();changed=[];overlay=[]
    def put(img):g.alpha_composite(img)
    phase=index
    cfg={
      '连珠速射塔':[(0,0),(-1,-1),(-1,-3),(0,6),(0,4),(0,2),(0,1),(0,0)],
      '熔芯重炮塔':[(0,0),(0,-1),(0,-3),(0,9),(0,7),(0,4),(0,1),(0,0)],
      '寒霜喷射塔':[(0,0),(0,-1),(0,-2),(0,3),(0,4),(0,3),(0,1),(0,0)]
    }
    for d in layers:
        name=d['name'];o=d['source']
        if not d['visible']:continue
        frame=o
        if kind in cfg:
            dx,dy=cfg[kind][phase]
            if kind=='连珠速射塔' and '炮管' in name:
                frame=shift(o,dx,dy);changed.append(name)
            if kind=='熔芯重炮塔' and '粗炮管' in name:
                frame=shift(o,dx,dy);changed.append(name)
            if kind=='寒霜喷射塔' and '喷嘴' in name:
                frame=shift(o,dx,dy);changed.append(name)
        if kind=='城防水晶' and '完整主晶体' in name:
            if phase:frame=polyfracture(o,phase);changed.append(name)
        if kind=='兽人小兵':
            if action=='walk':
                stride=[-7,-5,-2,2,7,5,2,-2][phase]
                lift=[1,-2,-5,-1,2,0,-4,-1][phase]
                if '左腿' in name:frame=shift(rotate(o,stride*2.2,(37,56)),stride//2,lift);changed.append(name)
                elif '右腿' in name:frame=shift(rotate(o,-stride*2.2,(59,56)),-stride//2,-lift);changed.append(name)
                elif '左臂' in name:frame=rotate(o,-stride*2.0,(28,32));changed.append(name)
                elif '右臂' in name:frame=rotate(o,stride*2.0,(68,32));changed.append(name)
                elif '战斧' in name:frame=rotate(o,stride*1.5,(78,50));changed.append(name)
                elif '盔甲身体' in name or '头部' in name:frame=shift(o,0,abs(stride)//4);changed.append(name)
            elif action=='attack':
                # 起手 -> 举斧蓄力 -> 过顶挥砍 -> 冲击 -> 回收
                armAngles=[-10,-22,-38,-52,51,34,15,0]
                axeAngles=[-4,-22,-43,-66,73,51,24,0]
                sway=[0,-1,-2,-3,3,2,1,0]
                if '战斧' in name:frame=rotate(o,axeAngles[phase],(74,34));changed.append(name)
                elif '右臂' in name:frame=rotate(o,armAngles[phase],(67,33));changed.append(name)
                elif '头部' in name:frame=shift(o,sway[phase],0);changed.append(name)
                elif '盔甲身体' in name:frame=rotate(o,sway[phase]*1.7,(49,57));changed.append(name)
                elif '左腿' in name:frame=shift(o,-sway[phase],0);changed.append(name)
                elif '右腿' in name:frame=shift(o,sway[phase],0);changed.append(name)
            elif action=='death':
                # 失衡 -> 手臂下垂 -> 腿部折叠 -> 头部倾倒 -> 战斧脱手、倒地
                tilt=[0,4,10,17,29,43,59,77][phase]
                fall=[0,0,1,3,5,10,14,17][phase]
                if '战斧' in name:
                    frame=shift(rotate(o,-tilt*1.1,(79,44)),phase*2,phase*2);changed.append(name)
                elif '左腿' in name:
                    frame=shift(rotate(o,-tilt*.50,(37,57)),phase*1,phase//2);changed.append(name)
                elif '右腿' in name:
                    frame=shift(rotate(o,tilt*.42,(59,57)),-phase,phase//2);changed.append(name)
                elif '头部' in name:
                    frame=shift(rotate(o,-tilt*.8,(49,41)),phase//2,fall//2);changed.append(name)
                elif '盔甲身体' in name:
                    frame=shift(rotate(o,-tilt,(49,67)),phase//3,fall);changed.append(name)
                elif '左臂' in name:
                    frame=shift(rotate(o,-tilt*.8,(26,34)),phase//3,fall//2);changed.append(name)
                elif '右臂' in name:
                    frame=shift(rotate(o,tilt*.9,(69,34)),phase//3,fall//2);changed.append(name)
        put(frame)
    # 作用帧：独立、可重绘动态特效，不修改/替换其他图层。
    if kind=='连珠速射塔':
        if phase>=2 and phase<=5:
            s=[2,3,6,4,3,2,1,1][phase]
            x,y=39,9
            fire=drawlayer(lambda d:(
                poly(d,[(x-3,y),(x,y-s*3),(x+3,y)],'#f5ac2b'),
                poly(d,[(56,y),(59,y-s*3),(63,y)],'#ffee87')))
            overlay.append(('双口火焰',fire))
        if phase>=4:
            bullet=drawlayer(lambda d:(
                circ(d,36+(phase-4)*2,2,2,'#fdf09c'),
                circ(d,61+(phase-4)*2,2,2,'#fff4af')))
            overlay.append(('飞出弹丸',bullet))
    if kind=='熔芯重炮塔':
        if phase>=1:
            glow=drawlayer(lambda d:circ(d,48,17,3+min(phase,4),'#ffbc59'))
            overlay.append(('蓄能核心',glow))
        if phase>=3 and phase<=6:
            rr=[0,0,0,7,9,12,7,0][phase]
            flash=drawlayer(lambda d:(circ(d,48,17,rr,'#ffa72d','#d84d20',1),circ(d,48,17,max(2,rr//2),'#ffef9e')))
            overlay.append(('重炮炮口焰',flash))
    if kind=='寒霜喷射塔':
        if phase>=2:
            reach=[0,0,4,8,14,11,7,3][phase]
            wave=drawlayer(lambda d:(
                poly(d,[(43,17),(48,17-reach),(53,17)],'#7de6fd'),
                circ(d,48,max(5,17-reach),2,'#d5ffff')))
            overlay.append(('动态冰雾',wave))
    if kind=='城防水晶' and phase>=3:
        # 碎裂冲击晶尘:变化在独立图层
        dust=drawlayer(lambda d:[
            circ(d,round(48+math.cos(j*.77)*(5+phase*2.2)),round(41+math.sin(j*1.34)*(6+phase*2.6)),
                 max(1,4-phase//3),'#8cf8ff') for j in range(4+phase//2)])
        overlay.append(('独立晶尘',dust))
    if kind=='兽人小兵' and action=='attack' and phase in (3,4,5):
        slash=drawlayer(lambda d:d.arc((55-2*phase,12,100,63),start=285,end=90,fill='#ffd37c',width=3))
        overlay.append(('挥斧轨迹',slash))
    if kind=='兽人小兵' and action=='death' and phase>=4:
        dust=drawlayer(lambda d:[circ(d,34+7*j,82+(j%2)*3,1+(phase-4)//2,'#7b6d55') for j in range(5)])
        overlay.append(('倒地扬尘',dust))
    for name,im in overlay:put(im)
    return g,changed,[name for name,im in overlay]
def main():
    records=[]
    objects=[
        ('连珠速射塔',['attack']),
        ('熔芯重炮塔',['attack']),
        ('寒霜喷射塔',['attack']),
        ('城防水晶',['shatter']),
        ('兽人小兵',['walk','attack','death'])
    ]
    for name,actions in objects:
        p,layers=loadsource(name)
        d=V2/name;d.mkdir()
        # 保留完整可编辑的源文件和各组成部件，动作数据引用这些图层。
        shutil.copy2(p,d/(name+'-可编辑分层.ora'))
        for i,l in enumerate(layers):
            q=d/'可编辑PNG图层'/f"{i+1:02}_{l['name']}.png"
            q.parent.mkdir(exist_ok=True);l['source'].save(q)
        acts={}
        for action in actions:
            fdir=d/'动作帧候选'/action;fdir.mkdir(parents=True)
            imgs=[]; metadata=[]
            for i in range(8):
                image,parts,fx=compose(layers,action,i,name)
                fp=fdir/f'帧{i+1:03}.png';image.save(fp)
                imgs.append(image)
                metadata.append({'frame':i,'durationMs':110,'rigPartTransitions':parts,'dynamicEffects':fx,'sha256':hashlib.sha256(fp.read_bytes()).hexdigest()})
            unique=len({hashlib.sha256(im.tobytes()).hexdigest() for im in imgs})
            adjacent=sum(imgs[i].tobytes()==imgs[i-1].tobytes() for i in range(1,len(imgs)))
            sheet=Image.new('RGBA',(W*4,H*2))
            for i,im in enumerate(imgs):sheet.alpha_composite(im,((i%4)*W,(i//4)*H))
            sheet.save(d/f'{action}-关键姿态-4x2.png')
            gifs=[im.resize((W*3,H*3),Image.Resampling.NEAREST) for im in imgs]
            gifs[0].save(d/f'{action}-动作预览.gif',save_all=True,append_images=gifs[1:],duration=110,loop=0,disposal=2)
            acts[action]={'frameCount':8,'uniqueFrames':unique,'adjacentDuplicatePairs':adjacent,'frames':metadata,'status':'PENDING_SEMANTICS_REVIEW'}
        records.append({'object':name,'sourceOra':str((d/(name+'-可编辑分层.ora')).relative_to(ROOT)).replace('\\','/'),
                        'layerCount':len(layers),'motions':acts})
    manifest={'status':'CANDIDATE_QA_NOT_GAME_READY','projectId':'live-turret-defense',
            'source':'rebuild from independent layer PNG in verified v1 ORA, not fake whole-image transforms',
            'notes':'Frames are export cache; editable layers + transform recipe are source. Do not load formal Cocos assets without human art review.',
            'canvas':[W,H],'fps':9.09,'entries':records}
    (V2/'分层动作资源清单-v2.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    quick=Image.new('RGBA',(W*5,H),(29,38,48,255))
    for i,r in enumerate(records):
        n=r['object'];p=V2/n;ac=list(r['motions'])[0]
        with Image.open(p/f'动作帧候选/{ac}/帧001.png') as im:quick.alpha_composite(im,(i*W,0))
    quick.resize((960,192),Image.Resampling.NEAREST).save(V2/'五种分层源形象-修订样板.png')
    zpath=V2.parent/'分层源文件及动作关键姿态-v2-待审核.zip'
    if zpath.exists():raise RuntimeError('NO_OVERWRITE_ZIP')
    with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
        for x in sorted(V2.rglob('*')):
            if x.is_file():z.write(x,x.relative_to(V2.parent))
    print(json.dumps({'output':str(V2),'zip':str(zpath),'zipBytes':zpath.stat().st_size,
                      'objects':len(records),'animations':sum(len(x['motions']) for x in records),
                      'layers':sum(x['layerCount'] for x in records),
                      'allUnique':all(v['uniqueFrames']==8 for o in records for v in o['motions'].values()),
                      'stats':[{'object':o['object'],'motions':{k:(v['uniqueFrames'],v['adjacentDuplicatePairs']) for k,v in o['motions'].items()}} for o in records]},ensure_ascii=True))
if __name__=="__main__":main()
