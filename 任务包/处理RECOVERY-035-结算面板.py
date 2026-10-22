# -*- coding: utf-8 -*-
"""RECOVERY-035 reproducible UI panel chroma-key, pixel normalization and QA."""
from pathlib import Path
from PIL import Image
import numpy as np, hashlib, json, time, sys

ROOT=Path(r"C:\Users\ide0007\Desktop\deliverable\AI小游戏实战营\AI小游戏制作工程文件\直播炮塔守城")
EVIDENCE=ROOT/"game-art"/"evidence"/"RECOVERY-035-UI-PANEL-MASTER-A"
SOURCE=EVIDENCE/"provider-output.png"
MASTER=EVIDENCE/"master.png"
RUNTIME=ROOT/"_assistant-temp"/"候选战场Cocos-V5隔离工程-20261020"/"assets"/"resources"/"候选战斗美术-v5-RECOVERY-004"/"UI"/"面板"/"结算面板底板.png"
REPORT=EVIDENCE/"alpha-pixel-qa.json"
EXPECTED_SOURCE_SHA256="7AD6A7F75B40D08C50BBCCA411104983F5D25A03F77B393DCD434797758E6022"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()

if not SOURCE.exists(): raise SystemExit("provider-output.png missing")
source_hash=sha(SOURCE)
if source_hash != EXPECTED_SOURCE_SHA256:
    raise SystemExit("Immutable provider-output hash mismatch; refuse to process a changed source")
im=Image.open(SOURCE).convert("RGB")
rgb=np.asarray(im,dtype=np.uint8)
r,g,b=rgb[:,:,0].astype(np.int16),rgb[:,:,1].astype(np.int16),rgb[:,:,2].astype(np.int16)
# Remove the magenta family globally; this asset's approved palette contains no magenta.
key=(r>125)&(b>125)&(g<145)&(np.abs(r-b)<130)
alpha=np.where(key,0,255).astype(np.uint8)
rgba=np.dstack((rgb,alpha))
keyed=Image.fromarray(rgba,"RGBA")
bbox=keyed.getchannel("A").getbbox()
if not bbox: raise SystemExit("Alpha QA failed: all pixels keyed out")
cropped=keyed.crop(bbox)
crop_rgba=np.asarray(cropped,dtype=np.uint8).copy()
crop_rgb=crop_rgba[:,:,:3]
crop_alpha=crop_rgba[:,:,3]
# Set hidden RGB on transparent pixels to neutral black before palette reduction.
crop_rgb[crop_alpha==0]=0
opaque=Image.fromarray(crop_rgb,"RGB")
quant=opaque.quantize(colors=48,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).convert("RGB")
quant_rgba=np.dstack((np.asarray(quant,dtype=np.uint8),crop_alpha))
normalized=Image.fromarray(quant_rgba,"RGBA")
# Keep pixel clusters crisp and avoid resampling blur in the mobile runtime master.
target=(512,636)
normalized=normalized.resize(target,Image.Resampling.NEAREST)
normalized.save(MASTER,optimize=True)
RUNTIME.parent.mkdir(parents=True,exist_ok=True)
normalized.save(RUNTIME,optimize=True)

out=np.asarray(normalized,dtype=np.uint8)
out_rgb=out[:,:,:3].astype(np.int16); out_a=out[:,:,3]
rr,gg,bb=out_rgb[:,:,0],out_rgb[:,:,1],out_rgb[:,:,2]
residual=((rr>125)&(bb>125)&(gg<145)&(np.abs(rr-bb)<130)&(out_a>0))
unique_colors=len(np.unique(out_rgb[out_a>0].reshape(-1,3),axis=0))
report={
 "taskId":"RECOVERY-035","assetId":"td-v5-ui-settlement-panel","status":"PASS" if (
   normalized.mode=="RGBA" and normalized.size==target and out_a.min()==0 and out_a.max()==255
   and int((out_a==0).sum())>0 and out_a[target[1]//2,target[0]//2]==255
   and int(residual.sum())==0 and unique_colors<=48
 ) else "FAIL",
 "source":{"path":str(SOURCE.relative_to(ROOT)).replace("\\","/"),"sha256":source_hash,"bytes":SOURCE.stat().st_size,"size":list(im.size),"mode":im.mode},
 "keying":{"rule":"R>125, B>125, G<145, abs(R-B)<130; no magenta is part of approved panel palette","keyPixels":int(key.sum()),"sourcePixels":int(rgb.shape[0]*rgb.shape[1]),"bbox":list(bbox),"cropSize":[cropped.width,cropped.height],"bboxAspectRatio":round(cropped.width/cropped.height,5)},
 "master":{"path":str(MASTER.relative_to(ROOT)).replace("\\","/"),"sha256":sha(MASTER),"bytes":MASTER.stat().st_size,"size":list(normalized.size),"mode":normalized.mode,"alphaMin":int(out_a.min()),"alphaMax":int(out_a.max()),"transparentPixels":int((out_a==0).sum()),"transparentRatio":round(float((out_a==0).mean()),5),"opaquePixels":int((out_a==255).sum()),"semiTransparentPixels":int(((out_a>0)&(out_a<255)).sum()),"uniqueOpaqueRgbColors":unique_colors,"paletteLimit":48,"residualMagentaOpaquePixels":int(residual.sum()),"centerPixelAlpha":int(out_a[target[1]//2,target[0]//2]),"cornerAlphas":[int(out_a[0,0]),int(out_a[0,-1]),int(out_a[-1,0]),int(out_a[-1,-1])]},
 "runtime":{"path":str(RUNTIME.relative_to(ROOT)).replace("\\","/"),"sha256":sha(RUNTIME),"bytes":RUNTIME.stat().st_size},
 "method":"immutable provider source -> magenta key -> crop silhouette -> 48-color no-dither palette reduction -> nearest-neighbor 512x636 RGBA master",
 "timestamp":time.strftime("%Y-%m-%dT%H:%M:%S"),
 "gates":{"realAlpha":bool(out_a.min()==0 and out_a.max()==255 and int((out_a==0).sum())>0),"panelInteriorOpaque":bool(out_a[target[1]//2,target[0]//2]==255),"noOpaqueMagentaFringe":bool(int(residual.sum())==0),"pixelPaletteBound":bool(unique_colors<=48),"runtimeCopyHashMatches":bool(sha(MASTER)==sha(RUNTIME))}
}
REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,ensure_ascii=True,indent=2))
sys.exit(0 if report["status"]=="PASS" and all(report["gates"].values()) else 1)
