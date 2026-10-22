# -*- coding: utf-8 -*-
"""WHOLE-GAME-FORMAL-SHOP-EFFECTS-20261022 effect QA. Only test fixture: seed 500 coins in fresh browser localStorage.
All upgrades are purchased through real Cocos shop buttons; upgrade levels are never written directly.
"""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from websockets.sync.client import connect
import requests,threading,subprocess,tempfile,time,json,traceback,sys,socket

ROOT=Path(r"C:\Users\ide0007\Desktop\deliverable\AI小游戏实战营\AI小游戏制作工程文件\直播炮塔守城")
BUILD=ROOT/"CocosCreator工程"/"build"/"web-mobile"
OUT=ROOT/"验收证据"/"WHOLE-GAME-FORMAL-SHOP-EFFECTS-20261022";OUT.mkdir(parents=True,exist_ok=True)
EDGE=Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe");W,H=360,780
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**k):super().__init__(*a,directory=str(BUILD),**k)
 def log_message(self,*a):pass
def port():
 for p in range(9237,9261):
  with socket.socket() as s:
   if s.connect_ex(("127.0.0.1",p))!=0:return p
 raise RuntimeError("no port")
def kill(profile):
 e=str(profile).replace("'","''");cmd="$p=Get-CimInstance Win32_Process|?{$_.Name -eq 'msedge.exe' -and $_.CommandLine -like '*"+e+"*'};$p|%{Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}"
 try:subprocess.run(["powershell","-NoProfile","-Command",cmd],timeout=10,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 except:pass
srv=ThreadingHTTPServer(("127.0.0.1",0),Handler);threading.Thread(target=srv.serve_forever,daemon=True).start()
rep={"task":"WHOLE-GAME-FORMAL-SHOP-EFFECTS-20261022","test":"synthetic wallet seed -> real UI purchase fireControl/viewerBoost -> reload -> effect","checks":{},"errors":[],"startedAt":time.strftime("%Y-%m-%dT%H:%M:%S")}
profile=tempfile.mkdtemp(prefix="turret-shop-effects-030-");p=port();proc=None;ws=None;seq=0
try:
 proc=subprocess.Popen([str(EDGE),"--headless","--remote-debugging-port="+str(p),"--remote-allow-origins=*","--no-first-run","--no-default-browser-check","--disable-features=msEdgeStartupBoost","--disable-background-timer-throttling","--user-data-dir="+profile,"about:blank"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 pages=None
 for _ in range(300):
  try:
   r=requests.get(f"http://127.0.0.1:{p}/json/list",timeout=.5)
   if r.ok:
    pages=r.json()
    if pages:break
  except:pass
  time.sleep(.1)
 if not pages:raise RuntimeError("CDP not ready")
 pg=next((x for x in pages if x.get("url")=="about:blank"),pages[0]);ws=connect(pg["webSocketDebuggerUrl"],open_timeout=8,max_size=24*1024*1024)
 def call(m,q=None,t=10):
  global seq
  seq+=1;i=seq;ws.send(json.dumps({"id":i,"method":m,"params":q or {}}));end=time.monotonic()+t
  while time.monotonic()<end:
   x=json.loads(ws.recv(timeout=max(.05,end-time.monotonic())))
   if x.get("id")==i:
    if "error" in x:raise RuntimeError(str(x["error"]))
    return x.get("result",{})
   pa=x.get("params",{})
   if x.get("method")=="Runtime.exceptionThrown":rep["errors"].append(pa.get("exceptionDetails",{}).get("text"))
   if x.get("method")=="Runtime.consoleAPICalled" and pa.get("type")=="error":rep["errors"].append("console.error")
  raise TimeoutError(m)
 def ev(e):
  x=call("Runtime.evaluate",{"expression":e,"returnByValue":True})
  if x.get("exceptionDetails"):raise RuntimeError(x["exceptionDetails"].get("text","eval"))
  return x.get("result",{}).get("value")
 def st():
  return ev("""(()=>{const n=cc.director.getScene().getChildByName('守城画布'),c=n&&n.getComponent('守城控制器'),a=n&&n.getComponent('待审战场美术覆盖器');if(!c||!a)return null;return {state:c.state,menu:a.mainMenuRoot.active,shop:a.shopRoot.active,profile:c.profileSnapshot(),catalog:c.shopCatalog(),fire:c.fireControlMultiplier,viewerStart:c.viewerStartLevel,towers:c.towers.map(t=>({id:t.ownerId,level:t.level})),inputBlocked:c.inputBlocked}})()""")
 def wait(pred,timeout=35):
  end=time.monotonic()+timeout;last=None
  while time.monotonic()<end:
   try:
    call("Page.bringToFront");last=st()
    if pred(last):return last
   except:pass
   time.sleep(.18)
  return last
 def pt(expr):
  q=ev(f"""(()=>{{const n=cc.director.getScene().getChildByName('守城画布'),a=n.getComponent('待审战场美术覆盖器'),v=cc.view.getVisibleSize(),p={expr}.position;return {{x:p.x,y:p.y,vw:v.width}}}})()""");sc=W/q["vw"];return round(W/2+q["x"]*sc),round(H/2-q["y"]*sc)
 def named(name):
  q=ev(f"""(()=>{{const n=cc.director.getScene().getChildByName('守城画布'),v=cc.view.getVisibleSize(),p=n.getChildByName('{name}').position;return {{x:p.x,y:p.y,vw:v.width}}}})()""");sc=W/q["vw"];return round(W/2+q["x"]*sc),round(H/2-q["y"]*sc)
 def click(x,y):
  call("Input.dispatchMouseEvent",{"type":"mousePressed","x":x,"y":y,"button":"left","clickCount":1});call("Input.dispatchMouseEvent",{"type":"mouseReleased","x":x,"y":y,"button":"left","clickCount":1});time.sleep(.3)
 for m in ("Page.enable","Runtime.enable","Network.enable"):call(m)
 call("Emulation.setDeviceMetricsOverride",{"width":W,"height":H,"deviceScaleFactor":1,"mobile":False})
 url=f"http://127.0.0.1:{srv.server_address[1]}/";call("Page.navigate",{"url":url})
 ready=wait(lambda q:q and q["menu"])
 if not ready:raise RuntimeError("menu not ready")
 seed={"version":1,"coins":500,"upgrades":{"coreShield":0,"fireControl":0,"viewerBoost":0},"stats":{"runs":0,"wins":0,"totalKills":0,"bestKills":0},"updatedAt":1}
 ev("localStorage.setItem('live-turret-defense.profile.v1',"+json.dumps(json.dumps(seed,ensure_ascii=False))+");true")
 call("Page.navigate",{"url":url})
 seeded=wait(lambda q:q and q["menu"] and q["profile"]["coins"]==500)
 if not seeded:raise RuntimeError("wallet fixture reload failed")
 sx,sy=pt("a.mainMenuShopSprite.node");click(sx,sy);opened=wait(lambda q:q and q["shop"])
 if not opened:raise RuntimeError("shop open failed")
 fx,fy=pt("a.shopRows.find(r=>r.id==='fireControl').buttonSprite.node");click(fx,fy)
 fireBought=wait(lambda q:q["profile"]["upgrades"]["fireControl"]==1)
 if not fireBought:raise RuntimeError("fireControl real purchase failed")
 vx,vy=pt("a.shopRows.find(r=>r.id==='viewerBoost').buttonSprite.node");click(vx,vy)
 viewerBought=wait(lambda q:q["profile"]["upgrades"]["viewerBoost"]==1)
 if not viewerBought:raise RuntimeError("viewerBoost real purchase failed")
 rep["afterPurchases"]=viewerBought
 rep["checks"]["realUiBoughtBoth"]=viewerBought["profile"]["coins"]==360 and viewerBought["profile"]["upgrades"]["fireControl"]==1 and viewerBought["profile"]["upgrades"]["viewerBoost"]==1
 cx,cy=pt("a.shopCloseSprite.node");click(cx,cy);wait(lambda q:q["menu"] and not q["shop"],8)
 call("Page.navigate",{"url":url});persist=wait(lambda q:q and q["menu"] and q["profile"]["upgrades"]["fireControl"]==1 and q["profile"]["upgrades"]["viewerBoost"]==1)
 if not persist:raise RuntimeError("upgrades not persistent")
 rep["afterReload"]=persist
 rep["checks"]["bothPersist"]=persist["profile"]["coins"]==360
 mx,my=pt("a.mainMenuStartSprite.node");click(mx,my);running=wait(lambda q:q["state"]=="running",8)
 if not running:raise RuntimeError("battle start failed")
 rep["afterStart"]=running
 rep["checks"]["fireControlMultiplierApplied"]=abs(running["fire"]-1.05)<0.0001
 rep["checks"]["viewerBaseLevelApplied"]=running["viewerStart"]==2
 jx,jy=named("按钮-观众+1");click(jx,jy);joined=wait(lambda q:any(not t["id"].startswith("base-") for t in q["towers"]),8)
 if not joined:raise RuntimeError("viewer join failed")
 live=next(t for t in joined["towers"] if not t["id"].startswith("base-"))
 rep["joined"]=joined
 rep["checks"]["newViewerTowerStartsLevel2"]=live["level"]==2
 rep["result"]="PASS" if all(rep["checks"].values()) and not rep["errors"] else "PARTIAL"
except Exception as e:
 rep["result"]="ERROR";rep["exception"]=repr(e);rep["stack"]=traceback.format_exc()[-3500:]
finally:
 if ws:
  try:ws.close()
  except:pass
 if proc:
  try:proc.terminate();proc.wait(timeout=2)
  except:
   try:proc.kill()
   except:pass
 kill(profile)
 try:srv.shutdown()
 except:pass
 rep["finishedAt"]=time.strftime("%Y-%m-%dT%H:%M:%S")
 dest=OUT/"火控与直播增幅效果回归.json";dest.write_text(json.dumps(rep,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"result":rep["result"],"checks":rep["checks"],"afterPurchases":rep.get("afterPurchases",{}).get("profile") if isinstance(rep.get("afterPurchases"),dict) else None,"afterStart":{"fire":rep.get("afterStart",{}).get("fire"),"viewerStart":rep.get("afterStart",{}).get("viewerStart")} if isinstance(rep.get("afterStart"),dict) else None,"joined":next((t for t in rep.get("joined",{}).get("towers",[]) if not t["id"].startswith("base-")),None) if isinstance(rep.get("joined"),dict) else None,"errors":rep["errors"],"exception":rep.get("exception"),"evidence":str(dest)},ensure_ascii=True))
sys.exit(0 if rep["result"]=="PASS" else 1)
