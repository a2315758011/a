# -*- coding: utf-8 -*-
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from websockets.sync.client import connect
from websockets.sync.server import serve as ws_serve
import requests,threading,subprocess,tempfile,time,json,traceback,sys,socket,base64

ROOT=Path(r"C:\Users\ide0007\Desktop\deliverable\AI小游戏实战营\AI小游戏制作工程文件\直播炮塔守城")
BUILD=ROOT/"CocosCreator工程"/"build"/"web-mobile"
OUT=ROOT/"验收证据"/"WHOLE-GAME-FORMAL-LIVEPLAY-20261022"
OUT.mkdir(parents=True,exist_ok=True)
EDGE=Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")

class H(SimpleHTTPRequestHandler):
 def __init__(self,*a,**k):super().__init__(*a,directory=str(BUILD),**k)
 def log_message(self,*a):pass

def free_port(start=9237,end=9299):
 for p in range(start,end+1):
  with socket.socket() as s:
   if s.connect_ex(("127.0.0.1",p))!=0:return p
 raise RuntimeError("no free port")

def kill(profile):
 e=str(profile).replace("'","''")
 cmd="$p=Get-CimInstance Win32_Process|?{$_.Name -eq 'msedge.exe' -and $_.CommandLine -like '*"+e+"*'};$p|%{Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}"
 try:subprocess.run(["powershell","-NoProfile","-Command",cmd],timeout=10,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 except:pass

ws_port=free_port(9301,9350)
stop_ws=threading.Event()
ws_stats={"connections":0,"sent":0}
packets=[
 {"type":"live_comment","event_id":"qa-c1","user":{"user_id":"qa-a","nickname":"甲观众"},"content":"加入","timestamp":1},
 {"type":"live_comment","event_id":"qa-c2","user":{"user_id":"qa-b","nickname":"乙观众"},"content":"888","timestamp":2},
 {"type":"live_comment","event_id":"qa-c3","user":{"user_id":"qa-c","nickname":"丙观众"},"content":"你好","timestamp":3},
 {"type":"live_like","event_id":"qa-like","user":{"user_id":"qa-a","nickname":"甲观众"},"count":12,"timestamp":4},
 {"type":"live_gift","event_id":"qa-g1","user":{"user_id":"qa-a","nickname":"甲观众"},"gift_id":"rose","gift_power":2,"timestamp":5},
 {"type":"live_comment","event_id":"qa-c4","user":{"user_id":"qa-b","nickname":"乙观众"},"content":"退出","timestamp":6}
]
def ws_handler(ws):
 ws_stats["connections"]+=1
 for item in packets:
  ws.send(json.dumps(item,ensure_ascii=False))
  ws_stats["sent"]+=1
  time.sleep(.08)
 while not stop_ws.is_set():
  try:
   time.sleep(.05)
  except:break

ws_server=ws_serve(ws_handler,"127.0.0.1",ws_port)
ws_thread=threading.Thread(target=ws_server.serve_forever,daemon=True);ws_thread.start()
srv=ThreadingHTTPServer(("127.0.0.1",0),H);threading.Thread(target=srv.serve_forever,daemon=True).start()

rep={"task":"WHOLE-GAME-FORMAL-LIVEPLAY-20261022","test":"Douyin live-play local WebSocket participation E2E","checks":{},"errors":[],"wsPort":ws_port,"startedAt":time.strftime("%Y-%m-%dT%H:%M:%S")}
profile=tempfile.mkdtemp(prefix="turret-liveplay-033-");port=free_port();proc=None;cdp=None;seq=0
try:
 proc=subprocess.Popen([str(EDGE),"--headless","--remote-debugging-port="+str(port),"--remote-allow-origins=*","--no-first-run","--no-default-browser-check","--disable-features=msEdgeStartupBoost","--disable-background-timer-throttling","--disable-renderer-backgrounding","--user-data-dir="+profile,"about:blank"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 pages=None
 for _ in range(140):
  try:
   r=requests.get(f"http://127.0.0.1:{port}/json/list",timeout=.5)
   if r.ok:
    pages=r.json()
    if pages:break
  except:pass
  time.sleep(.1)
 if not pages:raise RuntimeError("CDP not ready")
 pg=next((x for x in pages if x.get("url")=="about:blank"),pages[0])
 cdp=connect(pg["webSocketDebuggerUrl"],open_timeout=8,max_size=24*1024*1024)
 def call(m,p=None,t=12):
  global seq
  seq+=1;i=seq;cdp.send(json.dumps({"id":i,"method":m,"params":p or {}}));end=time.monotonic()+t
  while time.monotonic()<end:
   x=json.loads(cdp.recv(timeout=max(.05,end-time.monotonic())))
   if x.get("id")==i:
    if "error" in x:raise RuntimeError(str(x["error"]))
    return x.get("result",{})
   q=x.get("params",{})
   if x.get("method")=="Runtime.exceptionThrown":rep["errors"].append(q.get("exceptionDetails",{}).get("text","exception"))
   if x.get("method")=="Runtime.consoleAPICalled" and q.get("type")=="error":
    rep["errors"].append(" ".join(str(a.get("value",a.get("description",""))) for a in q.get("args",[]))[:800] or "console.error")
  raise TimeoutError(m)
 def ev(e):
  x=call("Runtime.evaluate",{"expression":e,"returnByValue":True})
  if x.get("exceptionDetails"):raise RuntimeError(x["exceptionDetails"].get("text","eval"))
  return x.get("result",{}).get("value")
 for m in ("Page.enable","Runtime.enable","Network.enable"):call(m)
 call("Network.setCacheDisabled",{"cacheDisabled":True})
 call("Emulation.setDeviceMetricsOverride",{"width":360,"height":780,"deviceScaleFactor":1,"mobile":False})
 fixture={"version":1,"coins":500,"upgrades":{"coreShield":3,"fireControl":3,"viewerBoost":2},"stats":{"runs":4,"wins":2,"totalKills":150,"bestKills":96},"updatedAt":1}
 call("Page.addScriptToEvaluateOnNewDocument",{"source":"try{localStorage.setItem('live-turret-defense.profile.v1',"+json.dumps(json.dumps(fixture,ensure_ascii=False))+")}catch(e){}"})
 call("Page.navigate",{"url":f"http://127.0.0.1:{srv.server_address[1]}/"})
 def state():
  return ev("""(()=>{const n=cc.director.getScene()&&cc.director.getScene().getChildByName('守城画布'),c=n&&n.getComponent('守城控制器'),a=n&&n.getComponent('待审战场美术覆盖器');if(!c||!a||!a.ready)return null;return {platform:c.platformSnapshot(),source:c.liveParticipationSourceSnapshot(),live:c.liveSessionSnapshot(),profile:c.profileSnapshot(),game:{state:c.state,hp:c.hp,maxHP:c.maxHP,fire:c.fireControlMultiplier,viewerStart:c.viewerStartLevel,lastReward:c.lastReward,towers:c.towers.map(t=>({ownerId:t.ownerId,owner:t.owner,level:t.level}))},ui:{menu:a.mainMenuRoot.active,shopButton:a.mainMenuShopSprite.node.active,wallet:a.mainMenuWallet.node.active,feature:a.mainMenuFeature.string,shop:a.shopRoot.active}}})()""")
 base=None
 for _ in range(180):
  try:
   call("Page.bringToFront");base=state()
   if base:break
  except:pass
  time.sleep(.2)
 if not base:raise RuntimeError("candidate not ready")
 rep["baseline"]=base
 rep["checks"]["standardModeKeepsShop"]=base["platform"]["mode"]=="standard" and base["platform"]["shopAllowed"] is True and base["ui"]["shopButton"] is True and base["ui"]["wallet"] is True
 rep["checks"]["fixtureUpgradesLoaded"]=base["profile"]["coins"]==500 and base["game"]["maxHP"]==130 and abs(base["game"]["fire"]-1.15)<0.001 and base["game"]["viewerStart"]==3

 bad=ev("""(()=>{const n=cc.director.getScene().getChildByName('守城画布'),c=n.getComponent('守城控制器');const bad=c.attachDouyinParticipationWebSocket('');return {bad,p:c.platformSnapshot()}})()""")
 time.sleep(.25);live_mode=state();rep["invalidUrl"]=bad;rep["liveMode"]=live_mode
 rep["checks"]["invalidUrlDoesNotPretendAttached"]=bad["bad"]["lastError"]=="invalid-websocket-url" and bad["p"]["liveEventSourceAttached"] is False
 rep["checks"]["livePlayPolicy"]=live_mode["platform"]["mode"]=="douyin-live-play" and live_mode["platform"]["shopAllowed"] is False and live_mode["platform"]["persistentEconomyAllowed"] is False and live_mode["platform"]["generalRoomPresenceAvailable"] is False and live_mode["platform"]["participationModel"]=="explicit-interaction"
 rep["checks"]["livePlayIgnoresPermanentUpgrades"]=live_mode["game"]["maxHP"]==100 and abs(live_mode["game"]["fire"]-1.0)<0.001 and live_mode["game"]["viewerStart"]==1
 rep["checks"]["livePlayHidesEconomyUi"]=live_mode["ui"]["shopButton"] is False and live_mode["ui"]["wallet"] is False and "不设商城" in live_mode["ui"]["feature"]
 buy=ev("""(()=>{const n=cc.director.getScene().getChildByName('守城画布'),c=n.getComponent('守城控制器'),before=c.profileSnapshot();const r=c.buyShopItem('coreShield'),after=c.profileSnapshot();return {before,r,after}})()""")
 rep["buyBlocked"]=buy
 rep["checks"]["purchaseBlockedWithoutMutation"]=buy["r"]["ok"] is False and buy["r"]["reason"]=="platform-disabled" and buy["before"]["coins"]==buy["after"]["coins"]==500 and buy["before"]["upgrades"]["coreShield"]==buy["after"]["upgrades"]["coreShield"]==3

 ws_url=f"ws://127.0.0.1:{ws_port}"
 attached=ev("(()=>{const n=cc.director.getScene().getChildByName('守城画布'),c=n.getComponent('守城控制器');return c.attachDouyinParticipationWebSocket("+json.dumps(ws_url)+")})()")
 rep["attachReturn"]=attached
 after=None
 for _ in range(100):
  time.sleep(.1);after=state()
  src=after.get("source") if after else None
  if src and src.get("connected") and src.get("received",0)>=6 and after["live"]["processedEvents"]>=4:break
 rep["afterPackets"]=after;rep["wsStatsBeforeDetach"]=dict(ws_stats)
 live=after["live"];src=after["source"];towers=after["game"]["towers"]
 qa_a=next((t for t in towers if t["ownerId"]=="qa-a"),None)
 qa_b=next((t for t in towers if t["ownerId"]=="qa-b"),None)
 rep["checks"]["webSocketConnected"]=src["connected"] is True and ws_stats["connections"]==1
 rep["checks"]["commentCommandsMapped"]=src["received"]==6 and src["mapped"]==4 and src["ignored"]==2
 rep["checks"]["participationReachedGame"]=live["knownViewers"]==2 and live["onlineViewers"]==1 and live["giftEvents"]==1 and live["giftPower"]==2 and len(towers)==10 and qa_a is not None and qa_a["level"]==3 and qa_b is None
 rep["checks"]["likeAndUnrelatedCommentIgnored"]=src["ignored"]==2 and live["processedEvents"]==4

 # 直播模式结算不能产生守城币/永久经济奖励。
 ev("""(()=>{const n=cc.director.getScene().getChildByName('守城画布'),c=n.getComponent('守城控制器');c.kills=25;c.hp=0;c.state='running';return true})()""")
 settled=None
 for _ in range(50):
  time.sleep(.1);settled=state()
  if settled and settled["game"]["state"]=="lose":break
 rep["settled"]=settled
 rep["checks"]["livePlaySettlementNoCurrency"]=settled["game"]["state"]=="lose" and settled["game"]["lastReward"]==0 and settled["profile"]["coins"]==500 and settled["profile"]["stats"]["runs"]==4

 ev("""(()=>{const n=cc.director.getScene().getChildByName('守城画布'),c=n.getComponent('守城控制器');c.detachLiveEventSource();return true})()""")
 time.sleep(1.2);detached=state();rep["detached"]=detached;rep["wsStatsAfterDetach"]=dict(ws_stats)
 rep["checks"]["detachStopsSource"]=detached["platform"]["liveEventSourceAttached"] is False and detached["source"] is None and ws_stats["connections"]==1

 shot=call("Page.captureScreenshot",{"format":"png","fromSurface":True})
 (OUT/"直播玩法模式主界面.png").write_bytes(base64.b64decode(shot["data"]))
 rep["checks"]["noJsErrors"]=len(rep["errors"])==0
 rep["result"]="PASS" if all(rep["checks"].values()) else "PARTIAL"
except Exception as e:
 rep["result"]="ERROR";rep["exception"]=repr(e);rep["stack"]=traceback.format_exc()[-5000:]
finally:
 stop_ws.set()
 try:ws_server.shutdown()
 except:pass
 try:srv.shutdown()
 except:pass
 if cdp:
  try:cdp.close()
  except:pass
 if proc:
  try:proc.terminate();proc.wait(timeout=2)
  except:
   try:proc.kill()
   except:pass
 kill(profile)
 rep["finishedAt"]=time.strftime("%Y-%m-%dT%H:%M:%S")
 dest=OUT/"本地WebSocket直播参与链路回归.json";dest.write_text(json.dumps(rep,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"result":rep["result"],"checks":rep["checks"],"errors":rep["errors"],"exception":rep.get("exception"),"wsStats":rep.get("wsStatsAfterDetach"),"evidence":str(dest)},ensure_ascii=True,indent=2))
sys.exit(0 if rep["result"]=="PASS" else 1)
