# -*- coding: utf-8 -*-
"""对标布局G0静态探针：验证原生俯视、四周入口、玩家塔和守护核心的基础空间契约。"""
import json, math, pathlib, sys
root = pathlib.Path(__file__).resolve().parent
j = json.loads((root/"首图俯视战场布局候选-v0.3.json").read_text(encoding="utf-8"))
e=[]
sc=j["screen"]; o=j["objective"]; ts=j["sceneSamples"]; sp=j["enemySpawns"]
if sc["width"] != sc["designLogicalWidth"] * sc["scaleInteger"] or sc["height"] != sc["designLogicalHeight"] * sc["scaleInteger"]:e.append("NOT_INTEGER_SCALING")
if j["map"]["camera"]!="topdown":e.append("NOT_TOPDOWN")
if j["map"]["copyExistingOrcdomGraphics"]:e.append("COPYRIGHT_RISK")
if j["towerPlacement"]["towerGrassFloorAttached"]:e.append("SPRITE_GRASS_ATTACHED")
if o["playerAssigned"] or o["giftUpgradable"]:e.append("CORE_IS_NOT_OWNED_TOWER")
if {x["dir"] for x in sp}!={"north","south","east","west"}:e.append("MISSING_FOUR_DIRECTIONS")
if len({x["id"] for x in ts})!=len(ts):e.append("DUPLICATE_TOWER_ID")
if set(t["kind"] for t in ts)!={"tower_repeater","tower_mortar","tower_frost"}:e.append("WRONG_TOWER_POOL")
for t in ts:
 x,y=t["at"]
 if not (24<=x<=516 and 116<=y<=812):e.append(t["id"]+"_OUT_OF_PLAYFIELD")
 if math.dist(t["at"],o["center"]) < j["towerPlacement"]["minDistanceFromCoreCenter"]:e.append(t["id"]+"_OVERLAPS_CORE")
for i,t in enumerate(ts):
 for b in ts[i+1:]:
  if math.dist(t["at"],b["at"]) < j["towerPlacement"]["minTowerSpacingLogicalPx"]:e.append(t["id"]+"_"+b["id"]+"_TOO_CLOSE")
for p in sp:
 x,y=p["at"];vx,vy=p["vector"];cx,cy=o["center"]
 if (cx-x)*vx+(cy-y)*vy<=0:e.append("SPAWN_VECTOR_NOT_INWARD:"+p["dir"])
print(json.dumps({"status":"PASS_STATIC_ONLY" if not e else "FAIL","errors":e,"towerExamples":len(ts),"types":list(set(x["kind"] for x in ts)),"spawns":len(sp),"view":"540x960 native upsample x2 to 1080x1920","imageAssetGenerated":False,"engineValidated":False},ensure_ascii=False,indent=2))
sys.exit(0 if not e else 1)
