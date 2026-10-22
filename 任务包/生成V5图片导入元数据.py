# -*- coding: utf-8 -*-
import hashlib, json, uuid
from pathlib import Path
from PIL import Image

ROOT = Path(r"C:\Users\ide0007\Desktop\deliverable\AI小游戏实战营\AI小游戏制作工程文件\直播炮塔守城")
ASSET_ROOT = ROOT / "CocosCreator工程" / "assets" / "resources" / "正式战斗美术-v5" / "战斗单位"
REPORT = ROOT / "game-art" / "evidence" / "ART-PIPELINE-V5-001" / "V5-Cocos-AssetMeta-QA.json"

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def make_meta(png):
    meta_path=png.with_suffix(png.suffix+".meta")
    with Image.open(png) as im:
        w,h=im.size
        has_alpha="A" in im.getbands()
    if not has_alpha:
        raise ValueError(f"Expected alpha channel: {png}")
    if w!=128 or h!=128:
        raise ValueError(f"Expected normalized 128x128 runtime sprite: {png} ({w}x{h})")
    if meta_path.exists():
        existing=json.loads(meta_path.read_text("utf-8"))
        tex=[v for v in existing.get("subMetas",{}).values() if v.get("importer")=="texture"]
        sf=[v for v in existing.get("subMetas",{}).values() if v.get("importer")=="sprite-frame"]
        if len(tex)==1 and len(sf)==1 and tex[0].get("userData",{}).get("minfilter")=="nearest" and tex[0].get("userData",{}).get("magfilter")=="nearest":
            return {"path":str(png),"meta":str(meta_path),"uuid":existing["uuid"],"sha256":sha(png),"width":w,"height":h,"reused":True}
    root_uuid=str(uuid.uuid4())
    stem=png.stem
    texture_id="6c48a"
    sprite_id="f9941"
    sprite_uuid=root_uuid+"@"+sprite_id
    meta={
        "ver":"1.0.26",
        "importer":"image",
        "imported":True,
        "uuid":root_uuid,
        "files":[".json",".png"],
        "subMetas":{
            texture_id:{
                "importer":"texture",
                "uuid":root_uuid+"@"+texture_id,
                "displayName":stem,
                "id":texture_id,
                "name":"texture",
                "userData":{
                    "wrapModeS":"clamp-to-edge",
                    "wrapModeT":"clamp-to-edge",
                    "imageUuidOrDatabaseUri":root_uuid,
                    "isUuid":True,
                    "visible":False,
                    "minfilter":"nearest",
                    "magfilter":"nearest",
                    "mipfilter":"none",
                    "anisotropy":0
                },
                "ver":"1.0.22",
                "imported":True,
                "files":[".json"],
                "subMetas":{}
            },
            sprite_id:{
                "importer":"sprite-frame",
                "uuid":sprite_uuid,
                "displayName":stem,
                "id":sprite_id,
                "name":"spriteFrame",
                "userData":{
                    "trimType":"auto",
                    "trimThreshold":1,
                    "rotated":False,
                    "offsetX":0,
                    "offsetY":0,
                    "trimX":0,
                    "trimY":0,
                    "width":w,
                    "height":h,
                    "rawWidth":w,
                    "rawHeight":h,
                    "borderTop":0,
                    "borderBottom":0,
                    "borderLeft":0,
                    "borderRight":0,
                    "packable":True,
                    "pixelsToUnit":100,
                    "pivotX":0.5,
                    "pivotY":0.5,
                    "meshType":0,
                    "vertices":{
                        "rawPosition":[-w/2,-h/2,0,w/2,-h/2,0,-w/2,h/2,0,w/2,h/2,0],
                        "indexes":[0,1,2,2,1,3],
                        "uv":[0,h,w,h,0,0,w,0],
                        "nuv":[0,0,1,0,0,1,1,1],
                        "minPos":[-w/2,-h/2,0],
                        "maxPos":[w/2,h/2,0]
                    },
                    "isUuid":True,
                    "imageUuidOrDatabaseUri":root_uuid+"@"+texture_id,
                    "atlasUuid":""
                },
                "ver":"1.0.12",
                "imported":True,
                "files":[".json"],
                "subMetas":{}
            }
        },
        "userData":{
            "type":"sprite-frame",
            "hasAlpha":True,
            "fixAlphaTransparencyArtifacts":False,
            "redirect":sprite_uuid
        }
    }
    meta_path.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {"path":str(png),"meta":str(meta_path),"uuid":root_uuid,"sha256":sha(png),"width":w,"height":h,"reused":False}

pngs=sorted(ASSET_ROOT.rglob("*.png"))
if len(pngs)!=16:
    raise SystemExit(f"Expected 16 V5 runtime PNGs, got {len(pngs)}")
items=[make_meta(p) for p in pngs]
uuids=[json.loads(Path(x["meta"]).read_text("utf-8"))["uuid"] for x in items]
if len(uuids)!=len(set(uuids)):
    raise SystemExit("Duplicate image UUID found")
REPORT.parent.mkdir(parents=True,exist_ok=True)
report={
    "taskId":"ART-PIPELINE-V5-001",
    "status":"PASS_V5_COCOS_IMAGE_META",
    "assetCount":len(items),
    "uniqueImageUUIDs":len(set(uuids)),
    "textureFilter":"nearest",
    "spriteCanvas":"128x128",
    "assets":items
}
REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"status":report["status"],"assetCount":len(items),"uniqueImageUUIDs":len(set(uuids)),"report":str(REPORT)},ensure_ascii=False,indent=2))
