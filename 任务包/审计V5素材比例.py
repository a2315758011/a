# -*- coding: utf-8 -*-
import json, hashlib
from pathlib import Path
from PIL import Image, ImageChops, ImageStat

ROOT = Path(r"C:\Users\ide0007\Desktop\deliverable\AI小游戏实战营\AI小游戏制作工程文件\直播炮塔守城")
SRC = ROOT / "美术资源" / "重制批次-v0.7" / "分层源文件"
DST = ROOT / "CocosCreator工程" / "assets" / "resources" / "正式战斗美术-v5" / "战斗单位"
OUT = ROOT / "game-art" / "evidence" / "ART-PIPELINE-V5-001" / "V5素材尺寸与导入审计.json"

def digest(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()

def fit_canvas(im, size=(128,128)):
    w,h=im.size
    scale=min(size[0]/w,size[1]/h)
    nw,nh=max(1,round(w*scale)),max(1,round(h*scale))
    z=im.resize((nw,nh),Image.Resampling.NEAREST)
    c=Image.new("RGBA",size,(0,0,0,0))
    c.alpha_composite(z,((size[0]-nw)//2,(size[1]-nh)//2))
    return c

def err(a,b):
    return round(sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/4,4)

pairs = []
for unit, folder, layer_pairs in [
    ("连珠速射塔","炮塔",[("底座","连珠速射塔_底座_母图层.png","连珠速射塔_底座.png"),("主体","连珠速射塔_主体_母图层.png","连珠速射塔_主体.png"),("双炮管","连珠速射塔_双炮管_母图层.png","连珠速射塔_双炮管.png")]),
    ("熔芯重炮塔","炮塔",[("底座","熔芯重炮塔_底座_母图层.png","熔芯重炮塔_底座.png"),("主体","熔芯重炮塔_主体_母图层.png","熔芯重炮塔_主体.png"),("熔芯炮口","熔芯重炮塔_熔芯炮口_母图层.png","熔芯重炮塔_熔芯炮口.png")]),
    ("寒霜喷射塔","炮塔",[("底座","寒霜喷射塔_底座_母图层.png","寒霜喷射塔_底座.png"),("主体","寒霜喷射塔_主体_母图层.png","寒霜喷射塔_主体.png"),("寒霜喷射器","寒霜喷射塔_寒霜喷射器_母图层.png","寒霜喷射塔_寒霜喷射器.png")]),
    ("城防水晶","水晶",[("基座","城防水晶_基座_母图层.png","城防水晶_基座.png"),("晶体","城防水晶_晶体_母图层.png","城防水晶_晶体.png"),("能量符文","城防水晶_能量符文_母图层.png","城防水晶_能量符文.png")])
]:
    for layer, srcname, dstname in layer_pairs:
        src=SRC/folder/srcname
        dst=DST/folder/dstname
        if not src.exists() or not dst.exists():
            pairs.append({"unit":unit,"layer":layer,"sourceExists":src.exists(),"targetExists":dst.exists(),"pass":False})
            continue
        a=Image.open(src).convert("RGBA")
        b=Image.open(dst).convert("RGBA")
        direct=a.resize(b.size,Image.Resampling.NEAREST)
        fitted=fit_canvas(a,b.size)
        alpha=b.getchannel("A")
        pairs.append({
            "unit":unit,"layer":layer,"source":str(src),"target":str(dst),
            "sourceSize":list(a.size),"targetSize":list(b.size),
            "sourceAlphaBBox":list(a.getchannel("A").getbbox() or ()),
            "targetAlphaBBox":list(alpha.getbbox() or ()),
            "sourceSha256":digest(src),"targetSha256":digest(dst),
            "targetVsDirectResizeMAE":err(b,direct),
            "targetVsAspectFitMAE":err(b,fitted),
            "targetTransparentRatio":round(sum(1 for v in alpha.getdata() if v==0)/(b.width*b.height),5),
            "pass":b.size==(128,128) and alpha.getbbox() is not None
        })

report={"taskId":"ART-PIPELINE-V5-001","status":"AUDIT_ONLY","assetPairs":pairs,"summary":{"pairs":len(pairs),"missing":sum(1 for x in pairs if x.get("sourceExists") is False or x.get("targetExists") is False or not x.get("source") or not x.get("target")),"dimensionMismatch":sum(1 for x in pairs if x.get("targetSize") != [128,128]),"directResizeCloser":sum(1 for x in pairs if x.get("targetVsDirectResizeMAE",999)<x.get("targetVsAspectFitMAE",999)),"aspectFitCloser":sum(1 for x in pairs if x.get("targetVsAspectFitMAE",999)<x.get("targetVsDirectResizeMAE",999))}}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"report":str(OUT),"summary":report["summary"],"pairs":pairs},ensure_ascii=False,indent=2))
