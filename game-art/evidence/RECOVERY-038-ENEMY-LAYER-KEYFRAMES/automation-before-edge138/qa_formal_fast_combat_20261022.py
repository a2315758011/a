# -*- coding: utf-8 -*-
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from websockets.sync.client import connect
import base64,requests,threading,subprocess,tempfile,time,json,traceback,sys,socket

ROOT=Path(r"C:\Users\ide0007\Desktop\deliverable\AI小游戏实战营\AI小游戏制作工程文件\直播炮塔守城")
BUILD=ROOT/"CocosCreator工程"/"build"/"web-mobile"
OUT=ROOT/"验收证据"/"WHOLE-GAME-FAST-COMBAT-20261022"
OUT.mkdir(parents=True,exist_ok=True)
EDGE=Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
class H(SimpleHTTPRequestHandler):
 def __init__(self,*a,**k):super().__init__(*a,directory=str(BUILD),**k)
 def log_message(self,*a):pass
def free_port():
 for p in range(9237,9251):
  with socket.socket() as s:
   if s.connect_ex(("127.0.0.1",p))!=0:return p
 raise RuntimeError("no free port")
def kill(profile):
 e=str(profile).replace("'","''")
 cmd="$p=Get-CimInstance Win32_Process|?{$_.Name -eq 'msedge.exe' -and $_.CommandLine -like '*"+e+"*'};$p|%{Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}"
 try:subprocess.run(["powershell","-NoProfile","-Command",cmd],timeout=10,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 except:pass

srv=ThreadingHTTPServer(("127.0.0.1",0),H);threading.Thread(target=srv.serve_forever,daemon=True).start()
rep={"task":"WHOLE-GAME-FORMAL-PLATFORM-ADAPTER-20261022","test":"platform adapter web runtime and live-source contract","checks":{},"errors":[],"startedAt":time.strftime("%Y-%m-%dT%H:%M:%S")}
profile=tempfile.mkdtemp(prefix="turret-platform-031-");port=free_port();proc=None;ws=None;seq=0
try:
 proc=subprocess.Popen([str(EDGE),"--headless","--remote-debugging-port="+str(port),"--remote-allow-origins=*","--no-first-run","--no-default-browser-check","--disable-features=msEdgeStartupBoost","--disable-background-timer-throttling","--user-data-dir="+profile,"about:blank"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 pages=None
 for _ in range(120):
  try:
   r=requests.get(f"http://127.0.0.1:{port}/json/list",timeout=.5)
   if r.ok:
    pages=r.json()
    if pages:break
  except:pass
  time.sleep(.1)
 if not pages:raise RuntimeError("CDP not ready")
 pg=next((x for x in pages if x.get("url")=="about:blank"),pages[0]);ws=connect(pg["webSocketDebuggerUrl"],open_timeout=8,max_size=24*1024*1024)
 def call(m,p=None,t=10):
  global seq
  seq+=1;i=seq;ws.send(json.dumps({"id":i,"method":m,"params":p or {}}));end=time.monotonic()+t
  while time.monotonic()<end:
   x=json.loads(ws.recv(timeout=max(.05,end-time.monotonic())))
   if x.get("id")==i:
    if "error" in x:raise RuntimeError(str(x["error"]))
    return x.get("result",{})
   q=x.get("params",{})
   if x.get("method")=="Runtime.exceptionThrown":rep["errors"].append(q.get("exceptionDetails",{}).get("text"))
   if x.get("method")=="Runtime.consoleAPICalled" and q.get("type")=="error":
    rep["errors"].append(" ".join(str(a.get("value",a.get("description",""))) for a in q.get("args",[]))[:500] or "console.error")
  raise TimeoutError(m)
 def ev(e):
  x=call("Runtime.evaluate",{"expression":e,"returnByValue":True})
  if x.get("exceptionDetails"):raise RuntimeError(x["exceptionDetails"].get("text","eval"))
  return x.get("result",{}).get("value")
 for m in ("Page.enable","Runtime.enable","Network.enable"):call(m)
 call("Network.setCacheDisabled",{"cacheDisabled":True});call("Emulation.setDeviceMetricsOverride",{"width":360,"height":780,"deviceScaleFactor":1,"mobile":False})
 call("Page.navigate",{"url":f"http://127.0.0.1:{srv.server_address[1]}/"})
 base=None
 for _ in range(180):
  try:
   call("Page.bringToFront")
   base=ev("""(()=>{const n=cc.director.getScene()&&cc.director.getScene().getChildByName('守城画布'),c=n&&n.getComponent('守城控制器'),a=n&&n.getComponent('待审战场美术覆盖器');if(!c||!a||!a.ready)return null;return {platform:c.platformSnapshot(),live:c.liveSessionSnapshot(),towers:c.towers.length,menu:a.mainMenuRoot.active}})()""")
   if base:break
  except:pass
  time.sleep(.2)
 if not base:raise RuntimeError("candidate not ready")

 rep["baseline"]=base
 rep["checks"]["startupReady"]=bool(base["towers"]==9 and base["menu"] is True)
 # The whole engine's real Cocos UI/art start gate ran; accelerate only the
 # established fixed 30Hz combat tick, without changing the production game.
 js=r"""(()=>{
 const scene=cc.director.getScene(),root=scene.getChildByName('守城画布');
 const c=root.getComponent('守城控制器'),art=root.getComponent('待审战场美术覆盖器');
 const stats={loopTicks:0,elapsedJsMs:0,gameSeconds:0,terminal:null,errors:[],iterations:[]};
 const t0=performance.now();
 const seed=Array.from({length:15},(_,i)=>({
  type:'viewer_join',eventId:'qa-fast-win-'+i,
  viewerId:'fast-'+i,viewerName:'快速观众'+i,source:'simulation',
  timestamp:Date.now()
 }));
 c.startNewRunFromMenu();
 for(const e of seed)if(!c.receiveLiveEvent(e))stats.errors.push('join rejected '+e.viewerId);
 c.flushLiveEvents();
 const startedTowers=c.towers.length;
 const loop=(tag,limit=150*30)=>{
  const first=c.time;let i=0;
  while(c.state==='running'&&i<limit){c.tick(1/30);i++;}
  stats.loopTicks+=i;
  stats.iterations.push({tag,ticks:i,state:c.state,time:c.time,health:c.hp,
    wave:c.wave,kills:c.kills,towers:c.towers.length,simSeconds:c.time-first});
 };
 loop('win');
 const win={state:c.state,hp:c.hp,wave:c.wave,kills:c.kills,
  towers:c.towers.length,session:c.liveSessionSnapshot(),profile:c.profileSnapshot()};
 c.returnToMenuState();
 const menu={state:c.state,hp:c.hp,kills:c.kills,towers:c.towers.length,
  live:c.liveSessionSnapshot(),profile:c.profileSnapshot()};
 for(const e of seed)c.receiveLiveEvent({
  type:'viewer_leave',eventId:'qa-fast-leave-'+e.viewerId,
  viewerId:e.viewerId,viewerName:e.viewerName,timestamp:Date.now(),source:'simulation'});
 c.flushLiveEvents();
 c.startNewRunFromMenu();
 const startedLossTowers=c.towers.length;
 loop('loss');
 const loss={state:c.state,hp:c.hp,wave:c.wave,kills:c.kills,
  towers:c.towers.length,profile:c.profileSnapshot()};
 c.restartFromSettlement();
 const replay={state:c.state,hp:c.hp,wave:c.wave,kills:c.kills,towers:c.towers.length};
 stats.elapsedJsMs=performance.now()-t0;
 stats.gameSeconds=stats.iterations.reduce((a,x)=>a+x.simSeconds,0);
 return {stats,startedTowers,win,menu,startedLossTowers,loss,replay,
  artReady:art.ready,artFailed:art.failed};
})()"""
 # A single CDP call accelerates 2 complete natural combat endings.
 # Capture an actual Cocos frame after entering battle.
 layerProbe=ev("""(()=>{const n=cc.director.getScene().getChildByName('守城画布'),c=n.getComponent('守城控制器'),a=n.getComponent('待审战场美术覆盖器');a.beginFromMainMenu();for(let i=0;i<120&&c.state==='running';i++){c.tick(1/30);a.update(1/30)}if(c.enemies.length){c.camX=c.enemies[0].x;c.camY=c.enemies[0].y;a.update(1/30)}const syntheticBoss={x:c.camX,y:c.camY,hp:500,max:500,speed:0,r:30,slow:0,boss:true};c.enemies.push(syntheticBoss);a.update(1/30);const active=a.enemyPool.filter(e=>e.node.active&&e.mobRef);const bossEntry=active.find(e=>e.mobRef===syntheticBoss);return {state:c.state,time:c.time,wave:c.wave,controllerEnemies:c.enemies.length,ready:a.ready,failed:a.failed,enemyPool:a.enemyPool.length,activeEnemies:active.length,bossLayer:{present:!!bossEntry,masterActive:bossEntry?bossEntry.master.node.active:null,activeLayers:bossEntry?bossEntry.sprites.filter(s=>s.node.active&&s.spriteFrame).length:0},examples:active.slice(0,5).map(e=>({kind:e.kind,masterActive:e.master.node.active,activeLayers:e.sprites.filter(s=>s.node.active&&s.spriteFrame).length,layerNames:e.sprites.map(s=>s.node.name)}))}})()""")
 rep["enemyLayerRuntimeProbe"]=layerProbe
 time.sleep(.3)
 visual=OUT/"02-正式战斗HUD.png"
 visual.write_bytes(base64.b64decode(call("Page.captureScreenshot",{"format":"png","fromSurface":True},12)["data"]))
 rep["visualScreenshot"]={"path":str(visual),"bytes":visual.stat().st_size}
 start=time.perf_counter()
 accelerated=ev(js)
 rep["accelerated"]=accelerated
 rep["wallSeconds"]=round(time.perf_counter()-start,4)
 q=accelerated
 rep["checks"].update({
  "fifteenViewersJoined":q["startedTowers"]==24,
  "naturalWin96Kills":q["win"]["state"]=="win" and q["win"]["wave"]==3 and q["win"]["kills"]==96 and q["win"]["hp"]>0,
  "roomSessionRetained":q["menu"]["state"]=="ready" and q["menu"]["towers"]==24 and q["menu"]["live"]["onlineViewers"]==15,
  "roomObserversLeave":q["startedLossTowers"]==9,
  "naturalLoseZeroHp":q["loss"]["state"]=="lose" and q["loss"]["hp"]==0,
  "restartResets":q["replay"]["state"]=="ready" and q["replay"]["towers"]==9 and q["replay"]["hp"]==100,
  "artReady":q["artReady"] is True and q["artFailed"] is False,
  "enemyLayersRuntimeActive":bool(rep.get("enemyLayerRuntimeProbe",{}).get("activeEnemies",0)>0 and all(not x["masterActive"] and x["activeLayers"]==3 for x in rep["enemyLayerRuntimeProbe"].get("examples",[]))),
  "bossLayersRuntimeActive":bool(rep.get("enemyLayerRuntimeProbe",{}).get("bossLayer",{}).get("present") is True and rep["enemyLayerRuntimeProbe"]["bossLayer"].get("masterActive") is False and rep["enemyLayerRuntimeProbe"]["bossLayer"].get("activeLayers")==3),
  "simulationAcceleratedAtLeast30x":q["stats"]["gameSeconds"]>=100 and q["stats"]["elapsedJsMs"]<10000,
  "noQARunErrors":len(q["stats"]["errors"])==0,
  "noJsErrors":len(rep["errors"])==0
 })
 rep["result"]="PASS" if all(rep["checks"].values()) else "FAIL"

except Exception as e:
 rep["result"]="ERROR";rep["exception"]=repr(e);rep["stack"]=traceback.format_exc()[-3000:]
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
 dest=OUT/"正式Cocos自然双结局高速回归.json";dest.write_text(json.dumps(rep,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"result":rep["result"],"checks":rep["checks"],"errors":rep["errors"],"exception":rep.get("exception"),"timings":rep.get("accelerated",{}).get("stats",{}),"evidence":str(dest)},ensure_ascii=True))
sys.exit(0 if rep["result"]=="PASS" else 1)
