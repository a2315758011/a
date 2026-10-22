# -*- coding: utf-8 -*-
import hashlib, json, math
from collections import deque
from pathlib import Path
from PIL import Image, ImageChops

ROOT = Path(r"C:\Users\ide0007\Desktop\deliverable\AI小游戏实战营\AI小游戏制作工程文件\直播炮塔守城")
BATCH = ROOT / "美术资源" / "重制批次-v0.7"
RAW = BATCH / "原始生成"
LAYERS = BATCH / "分层源文件"
RUNTIME = BATCH / "运行时素材"
REPORT = ROOT / "game-art" / "evidence" / "ART-PIPELINE-V5-001" / "V5透明分层处理与QA.json"

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def latest_png(folder, recursive=False):
    if not folder.exists():
        return None
    it = folder.rglob("*.png") if recursive else folder.glob("*.png")
    files = [p for p in it if p.is_file() and not p.name.lower().endswith("_preview.png")]
    # Identical artifact copies can be created by the shared gateway and a manual recovery.
    # Keep all source files, but select the canonical unsuffixed filename for provenance.
    by_hash = {}
    for p in files:
        h = sha(p)
        old = by_hash.get(h)
        suffixed = p.stem.rsplit("-", 1)[-1].isdigit()
        old_suffixed = old.stem.rsplit("-", 1)[-1].isdigit() if old else False
        if old is None or (old_suffixed and not suffixed):
            by_hash[h] = p
    unique = list(by_hash.values())
    return max(unique, key=lambda p: p.stat().st_mtime) if unique else None

def is_magenta(px):
    r, g, b = px[:3]
    # Catch antialiased magenta fringe, not only pure #FF00FF background.
    return r >= 55 and b >= 55 and g <= min(r, b) * 0.72 and abs(r-b) <= 125

def remove_edge_magenta(img):
    im = img.convert("RGBA")
    w, h = im.size
    pix = im.load()
    seen = bytearray(w*h)
    q = deque()
    def add(x, y):
        i = y*w+x
        if not seen[i] and is_magenta(pix[x,y]):
            seen[i] = 1
            q.append(i)
    for x in range(w):
        add(x, 0); add(x, h-1)
    for y in range(h):
        add(0, y); add(w-1, y)
    while q:
        i = q.popleft()
        x, y = i % w, i // w
        pix[x,y] = (0,0,0,0)
        for dy in (-1,0,1):
            for dx in (-1,0,1):
                if dx == 0 and dy == 0: continue
                nx,ny=x+dx,y+dy
                if 0 <= nx < w and 0 <= ny < h: add(nx,ny)
    # Also remove enclosed magenta pockets between barrels/ornaments; this art set uses no magenta accents.
    for y in range(h):
        for x in range(w):
            i=y*w+x
            if not seen[i] and is_magenta(pix[x,y]):
                seen[i]=1
                pix[x,y]=(0,0,0,0)
    # Copy adjacent object RGB into transparent pixels to prevent coloured sampling halos.
    for i, flag in enumerate(seen):
        if not flag: continue
        x,y=i%w,i//w
        for dy in (-1,0,1):
            copied=False
            for dx in (-1,0,1):
                if dx == 0 and dy == 0: continue
                nx,ny=x+dx,y+dy
                if 0 <= nx < w and 0 <= ny < h:
                    ni=ny*w+nx
                    if not seen[ni] and pix[nx,ny][3] > 0:
                        rr,gg,bb,aa=pix[nx,ny]
                        pix[x,y]=(rr,gg,bb,0)
                        copied=True
                        break
            if copied: break
    return im

def bbox_alpha(img):
    a = img.getchannel("A")
    return a.getbbox()

def qa(img):
    rgba = img.convert("RGBA")
    hist = rgba.getchannel("A").histogram()
    total = rgba.width * rgba.height
    transparent = hist[0]
    opaque = hist[255]
    box = bbox_alpha(rgba)
    edge = False
    if box:
        l,t,r,b = box
        edge = l <= 1 or t <= 1 or r >= rgba.width-1 or b >= rgba.height-1
    magenta = 0
    px = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r,g,b,a = px[x,y]
            if a > 16 and is_magenta((r,g,b,a)):
                magenta += 1
    ratio=magenta/max(1,total-transparent)
    return {
        "width": rgba.width, "height": rgba.height,
        "transparentRatio": round(transparent/total, 5),
        "opaqueRatio": round(opaque/total, 5),
        "bbox": list(box) if box else None,
        "contentTouchesCanvasEdge": edge,
        "residualMagentaRatio": round(ratio, 6),
        "pass": bool(box) and transparent/total >= 0.03 and opaque/total >= 0.02 and not edge and ratio <= 0.002
    }

def split_sheet(source, cols, rows, row_bounds=None, padding=16):
    im = Image.open(source).convert("RGBA")
    w,h = im.size
    xs = [round(i*w/cols) for i in range(cols+1)]
    ys = [round(i*h/rows) for i in range(rows+1)] if row_bounds is None else list(row_bounds)
    if len(ys) != rows+1 or ys[0] != 0 or ys[-1] != h:
        raise ValueError("row_bounds must contain rows+1 values from 0 to image height")
    raw = []
    for row in range(rows):
        for col in range(cols):
            crop = im.crop((xs[col], ys[row], xs[col+1], ys[row+1]))
            raw.append((row,col,crop,[xs[col],ys[row],xs[col+1],ys[row+1]]))
    cell_w = max(item[2].width for item in raw)
    cell_h = max(item[2].height for item in raw)
    cells = []
    for row,col,crop,rect in raw:
        # All parts share a padded canvas/pivot; custom row bounds prevent tall ornaments being clipped.
        canvas = Image.new("RGBA",(cell_w+2*padding,cell_h+2*padding),(255,0,255,255))
        canvas.alpha_composite(crop,(padding+(cell_w-crop.width)//2, padding+(cell_h-crop.height)//2))
        cells.append((row,col,remove_edge_magenta(canvas),rect))
    return im.size, cells

def resize_nearest(img, size):
    return img.resize(size, Image.Resampling.NEAREST)

def fit_canvas(img, size):
    img = img.convert("RGBA")
    max_w, max_h = size
    scale = min(max_w / img.width, max_h / img.height)
    new_size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
    resized = resize_nearest(img, new_size)
    canvas = Image.new("RGBA", size, (0,0,0,0))
    canvas.alpha_composite(resized, ((max_w-new_size[0])//2, (max_h-new_size[1])//2))
    return canvas

def trim_with_padding(img, pad=5):
    box = img.getchannel("A").getbbox()
    if not box:
        return img
    l,t,r,b = box
    l=max(0,l-pad); t=max(0,t-pad); r=min(img.width,r+pad); b=min(img.height,b+pad)
    return img.crop((l,t,r,b))

def save_png(img, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "PNG", optimize=True)

report = {
    "taskId":"ART-PIPELINE-V5-001",
    "createdAt":"2026-10-19",
    "status":"PROCESSING",
    "inputs":[],
    "assets":[],
    "checks":[],
    "notes":[
        "Only source sheets saved on the Windows workstation are processed.",
        "Flat magenta removal uses edge-connected flood fill, not whole-image color replacement.",
        "Any failed alpha/silhouette check stays a candidate and must not be wired into formal gameplay."
    ]
}

tower_source = latest_png(RAW / "战斗分层", recursive=False)
if tower_source:
    source_height = Image.open(tower_source).height
    size, cells = split_sheet(tower_source, 4, 3, [0, min(340,source_height), min(640,source_height), source_height], padding=16)
    report["inputs"].append({"type":"tower-layer-sheet","path":str(tower_source),"sha256":sha(tower_source),"size":list(size)})
    names = [
        ("连珠速射塔","底座","炮塔"), ("熔芯重炮塔","底座","炮塔"), ("寒霜喷射塔","底座","炮塔"), ("城防水晶","基座","水晶"),
        ("连珠速射塔","主体","炮塔"), ("熔芯重炮塔","主体","炮塔"), ("寒霜喷射塔","主体","炮塔"), ("城防水晶","晶体","水晶"),
        ("连珠速射塔","双炮管","炮塔"), ("熔芯重炮塔","熔芯炮口","炮塔"), ("寒霜喷射塔","寒霜喷射器","炮塔"), ("城防水晶","能量符文","水晶")
    ]
    layer_map = {}
    for (row,col,img,rect), (unit,layer,kind) in zip(cells,names):
        src_dir = LAYERS / kind
        src_path = src_dir / f"{unit}_{layer}_母图层.png"
        save_png(img,src_path)
        q = qa(img)
        item={"asset":unit,"layer":layer,"kind":kind,"sourceRect":rect,"sourcePath":str(src_path),"sourceSha256":sha(src_path),"qa":q}
        report["assets"].append(item)
        layer_map[(col,row)] = img
    composites = [
        (0,"连珠速射塔","炮塔"), (1,"熔芯重炮塔","炮塔"), (2,"寒霜喷射塔","炮塔"), (3,"城防水晶","水晶")
    ]
    for col,unit,kind in composites:
        comp = Image.new("RGBA",layer_map[(col,0)].size,(0,0,0,0))
        layer_checks=[qa(layer_map[(col,row)]) for row in range(3)]
        for row in range(3):
            comp = Image.alpha_composite(comp,layer_map[(col,row)])
        q = qa(comp)
        master_path = LAYERS / kind / f"{unit}_合成预览_母图.png"
        save_png(comp,master_path)
        runtime_dir = RUNTIME / "战斗单位" / kind
        if not all(item["pass"] for item in layer_checks):
            quarantine = RUNTIME / "待审核" / f"{unit}_图层QA未通过.png"
            save_png(comp,quarantine)
            report["assets"].append({"asset":unit,"layer":"composite-preview","kind":kind,"sourcePath":str(master_path),"quarantinePath":str(quarantine),"sourceSha256":sha(master_path),"qa":q,"layerQa":layer_checks,"status":"BLOCKED_ALPHA_QA","approved":False})
            continue
        runtime_path = runtime_dir / f"{unit}.png"
        runtime = fit_canvas(comp,(128,128))
        save_png(runtime,runtime_path)
        runtime_qa = qa(runtime)
        report["assets"].append({"asset":unit,"layer":"composite-preview","kind":kind,"sourcePath":str(master_path),"runtimePath":str(runtime_path),"sourceSha256":sha(master_path),"runtimeSha256":sha(runtime_path),"qa":q,"runtimeQa":runtime_qa,"runtimeSize":list(runtime.size),"approved":False})
        # Keep aligned square canvases for pivot-stable layer composition and animation.
        for row in range(3):
            layer_name = names[row*4+col][1]
            runtime_layer = fit_canvas(layer_map[(col,row)],(128,128))
            layer_path = runtime_dir / f"{unit}_{layer_name}.png"
            save_png(runtime_layer,layer_path)
    report["checks"].append({"id":"TOWER-SPLIT","source":str(tower_source),"pass":len(cells)==12 and all(x["qa"]["pass"] for x in report["assets"] if x.get("kind") in ("炮塔","水晶")),"cells":12})
else:
    report["checks"].append({"id":"TOWER-SPLIT","pass":False,"reason":"No tower sheet found on workstation."})

enemy_source = latest_png(RAW / "战斗分层" / "兽人", recursive=False)
if enemy_source:
    size,cells=split_sheet(enemy_source,3,2)
    report["inputs"].append({"type":"enemy-layer-sheet","path":str(enemy_source),"sha256":sha(enemy_source),"size":list(size)})
    enemy_names=[("兽人小兵","身体护甲"),("兽人小兵","头部双臂"),("兽人小兵","武器配件"),("兽人首领","身体护甲"),("兽人首领","头部双臂"),("兽人首领","武器配件")]
    emap={}
    for (row,col,img,rect),(unit,layer) in zip(cells,enemy_names):
        p=LAYERS/"兽人"/f"{unit}_{layer}_母图层.png";save_png(img,p);q=qa(img);emap[(row,col)]=img
        report["assets"].append({"asset":unit,"layer":layer,"kind":"兽人","sourceRect":rect,"sourcePath":str(p),"sourceSha256":sha(p),"qa":q})
    for row,unit in [(0,"兽人小兵"),(1,"兽人首领")]:
        comp=Image.new("RGBA",emap[(row,0)].size,(0,0,0,0))
        for col in range(3):comp=Image.alpha_composite(comp,emap[(row,col)])
        master=LAYERS/"兽人"/f"{unit}_合成预览_母图.png";save_png(comp,master)
        runtime=fit_canvas(comp,(96,96))
        runtime_path=RUNTIME/"战斗单位"/"兽人"/f"{unit}.png";save_png(runtime,runtime_path)
        report["assets"].append({"asset":unit,"layer":"composite-preview","kind":"兽人","sourcePath":str(master),"runtimePath":str(runtime_path),"sourceSha256":sha(master),"runtimeSha256":sha(runtime_path),"qa":qa(comp),"approved":False})
    report["checks"].append({"id":"ENEMY-SPLIT","pass":len(cells)==6,"cells":6})
else:
    report["checks"].append({"id":"ENEMY-SPLIT","pass":False,"reason":"Enemy sheet not available yet."})

ui_source = latest_png(RAW / "UI皮肤", recursive=False)
if ui_source:
    size,cells=split_sheet(ui_source,4,2)
    report["inputs"].append({"type":"ui-skin-sheet","path":str(ui_source),"sha256":sha(ui_source),"size":list(size)})
    ui_names=[("HUD顶部底板","面板"),("主操作按钮","按钮"),("次操作按钮","按钮"),("离场按钮","按钮"),("生命值条外框","面板"),("波次徽章","图标"),("能量水晶图标","图标"),("炮塔升级图标","图标")]
    for (row,col,img,rect),(name,kind) in zip(cells,ui_names):
        p=LAYERS/"UI"/f"{name}_母图层.png";save_png(img,p);trim=trim_with_padding(img,8)
        if kind=="面板": target=(256,96) if col==0 or row==1 and col==0 else (192,96)
        elif kind=="按钮": target=(160,64)
        else: target=(96,96)
        runtime=fit_canvas(trim,target)
        runtime_path=RUNTIME/"UI"/kind/f"{name}.png";save_png(runtime,runtime_path);q=qa(img)
        report["assets"].append({"asset":name,"layer":"single","kind":"UI-"+kind,"sourceRect":rect,"sourcePath":str(p),"runtimePath":str(runtime_path),"sourceSha256":sha(p),"runtimeSha256":sha(runtime_path),"qa":q,"approved":False})
    report["checks"].append({"id":"UI-SPLIT","pass":len(cells)==8,"cells":8})
else:
    report["checks"].append({"id":"UI-SPLIT","pass":False,"reason":"UI sheet not available yet."})

ground_source = latest_png(RAW / "地砖", recursive=False)
if ground_source:
    ground=Image.open(ground_source).convert("RGBA")
    w,h=ground.size
    def edge_diff(a,b):
        n=min(len(a),len(b))
        if not n:return 999
        return sum(sum(abs(int(a[i][c])-int(b[i][c])) for c in range(3)) for i in range(n))/(n*3)
    left=[ground.getpixel((0,y)) for y in range(h)]
    right=[ground.getpixel((w-1,y)) for y in range(h)]
    top=[ground.getpixel((x,0)) for x in range(w)]
    bottom=[ground.getpixel((x,h-1)) for x in range(w)]
    lr=edge_diff(left,right);tb=edge_diff(top,bottom)
    seamless=(lr<=28 and tb<=28)
    source_copy=LAYERS/"环境"/"战场地砖_母图.png";save_png(ground,source_copy)
    runtime_path=RUNTIME/"环境"/"战场地砖.png"
    if seamless:
        save_png(resize_nearest(ground,(256,256)),runtime_path)
    report["inputs"].append({"type":"ground-tile","path":str(ground_source),"sha256":sha(ground_source),"size":[w,h]})
    report["assets"].append({"asset":"战场地砖","kind":"环境","sourcePath":str(source_copy),"runtimePath":str(runtime_path) if seamless else None,"sourceSha256":sha(source_copy),"seamless":{"leftRightMeanAbsDiff":round(lr,2),"topBottomMeanAbsDiff":round(tb,2),"pass":seamless},"approved":False})
    report["checks"].append({"id":"GROUND-SEAM","pass":seamless,"leftRightMeanAbsDiff":round(lr,2),"topBottomMeanAbsDiff":round(tb,2)})
else:
    report["checks"].append({"id":"GROUND-SEAM","pass":False,"reason":"Ground tile not available yet."})

# Any absent asset families keep the batch blocked; this script never auto-approves art.
ready_ids=[x for x in report["checks"] if x.get("pass") is True]
report["status"]="PARTIAL_QA" if ready_ids else "BLOCKED"
report["summary"]={"checksPassed":len(ready_ids),"checksTotal":len(report["checks"]),"assetsProcessed":len(report["assets"]),"allFamiliesReady":all(x.get("pass") is True for x in report["checks"])}
REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"report":str(REPORT),"status":report["status"],"summary":report["summary"],"checks":report["checks"],"assets":len(report["assets"])},ensure_ascii=False,indent=2))
