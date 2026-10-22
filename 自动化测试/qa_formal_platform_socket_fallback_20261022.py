# -*- coding: utf-8 -*-
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from websockets.sync.client import connect
import requests,threading,subprocess,tempfile,time,json,traceback,sys,socket

ROOT=Path(r"C:\Users\ide0007\Desktop\deliverable\AI小游戏实战营\AI小游戏制作工程文件\直播炮塔守城")
BUILD=ROOT/"CocosCreator工程"/"build"/"web-mobile"
OUT=ROOT/"验收证据"/"WHOLE-GAME-FORMAL-PLATFORM-ADAPTER-20261022"
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
 proc=subprocess.Popen(["node",str(ROOT/"自动化测试"/"edge_cdp_launcher_20261022.js"),str(port),profile,"keep"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 pages=None
 for _ in range(100):
  try:
   r=requests.get(f"http://127.0.0.1:{port}/json/list",timeout=.15)
   if r.ok:
    pages=r.json()
    if pages:break
  except:pass
  time.sleep(.1)
 if not pages:raise RuntimeError("CDP not ready")
 pg=next((x for x in pages if x.get("type")=="page"),pages[0]);ws=connect(pg["webSocketDebuggerUrl"],open_timeout=8,max_size=24*1024*1024)
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
 rep["checks"]["webRuntime"]=base["platform"]["runtime"]=="web"
 rep["checks"]["storageAvailable"]=base["platform"]["storageAvailable"] is True
 rep["checks"]["sdkNotPretendedOnWeb"]=base["platform"]["platformSdkAvailable"] is False
 rep["checks"]["noSourceByDefault"]=base["platform"]["liveEventSourceAttached"] is False and base["platform"]["liveEventSourceId"] is None
 injected=ev("""(()=>{const n=cc.director.getScene().getChildByName('守城画布'),c=n.getComponent('守城控制器');globalThis.__platQaStop=0;const src={id:'qa-mock-source',start(emit){emit({eventId:'platform-qa-join',type:'viewer_join',viewerId:'platform-qa-user',viewerName:'平台测试观众',timestamp:Date.now(),source:'external'});},stop(){globalThis.__platQaStop++}};c.attachLiveEventSource(src);return c.platformSnapshot()})()""")
 rep["afterAttach"]=injected
 rep["checks"]["sourceAttached"]=injected["liveEventSourceAttached"] is True and injected["liveEventSourceId"]=="qa-mock-source"
 after=None
 for _ in range(50):
  time.sleep(.1)
  after=ev("""(()=>{const n=cc.director.getScene().getChildByName('守城画布'),c=n.getComponent('守城控制器'),l=c.liveSessionSnapshot();return {l,towers:c.towers.length,p:c.platformSnapshot()}})()""")
  if after["l"]["onlineViewers"]>=1 and after["towers"]>=10:break
 rep["afterEvent"]=after
 rep["checks"]["eventReachedBridge"]=after["l"]["onlineViewers"]==1 and after["l"]["knownViewers"]==1 and after["towers"]==10
 detached=ev("""(()=>{const n=cc.director.getScene().getChildByName('守城画布'),c=n.getComponent('守城控制器');c.detachLiveEventSource();return {p:c.platformSnapshot(),stops:globalThis.__platQaStop}})()""")
 rep["afterDetach"]=detached
 rep["checks"]["sourceDetached"]=detached["p"]["liveEventSourceAttached"] is False and detached["p"]["liveEventSourceId"] is None and detached["stops"]==1

 # Verify the Douyin/WeChat mini-game SocketTask path when browser WebSocket is unavailable.
 fallback_start=ev("""(()=>{const n=cc.director.getScene().getChildByName('守城画布'),c=n.getComponent('守城控制器');
 c.receiveLiveEvent({eventId:'qa-clear-platform-user',type:'viewer_leave',viewerId:'platform-qa-user',viewerName:'平台测试观众',timestamp:Date.now(),source:'external'});c.flushLiveEvents();
 const oldWS=globalThis.WebSocket,oldTT=globalThis.tt;try{Object.defineProperty(globalThis,'WebSocket',{configurable:true,writable:true,value:undefined})}catch(e){globalThis.WebSocket=undefined}
 const qa={url:'',closed:false,handlers:null,task:null,oldWS,oldTT};globalThis.__miniSocketQa=qa;
 globalThis.tt={connectSocket:({url})=>{qa.url=url;const h={};const task={onOpen(fn){h.open=fn},onMessage(fn){h.message=fn},onError(fn){h.error=fn},onClose(fn){h.close=fn},close(){qa.closed=true}};qa.handlers=h;qa.task=task;return task}};
 const snap=c.attachDouyinParticipationWebSocket('wss://qa.invalid/live');qa.handlers.open();qa.handlers.message({data:JSON.stringify({type:'participation_join',eventId:'qa-mini-join',viewerId:'qa-mini-viewer',viewerName:'小程序模拟观众',timestamp:Date.now()})});
 return {snap,url:qa.url,platform:c.platformSnapshot(),source:c.liveParticipationSourceSnapshot()}})()""")
 time.sleep(.25)
 fallback_state=ev("""(()=>{const n=cc.director.getScene().getChildByName('守城画布'),c=n.getComponent('守城控制器');return {p:c.platformSnapshot(),s:c.liveParticipationSourceSnapshot(),l:c.liveSessionSnapshot(),towers:c.towers.length}})()""")
 rep["miniGameSocketFallback"]=fallback_state
 rep["checks"]["miniGameSocketTaskUsed"]=fallback_state["p"]["runtime"]=="douyin" and fallback_state["p"]["liveEventSourceAttached"] is True and fallback_state["s"]["connected"] is True and fallback_state["s"]["received"]==1 and fallback_state["s"]["mapped"]==1 and fallback_state["l"]["onlineViewers"]==1 and fallback_state["towers"]==10
 detached_mini=ev("""(()=>{const n=cc.director.getScene().getChildByName('守城画布'),c=n.getComponent('守城控制器'),qa=globalThis.__miniSocketQa;c.detachLiveEventSource();const closed=qa.closed===true;try{Object.defineProperty(globalThis,'WebSocket',{configurable:true,writable:true,value:qa.oldWS})}catch(e){globalThis.WebSocket=qa.oldWS}if(qa.oldTT!==undefined)globalThis.tt=qa.oldTT;else delete globalThis.tt;delete globalThis.__miniSocketQa;return {closed,p:c.platformSnapshot(),source:c.liveParticipationSourceSnapshot()}})()""")
 rep["miniGameSocketDetached"]=detached_mini
 rep["checks"]["miniGameSocketTaskCloses"]=detached_mini["closed"] is True and detached_mini["p"]["liveEventSourceAttached"] is False and detached_mini["source"] is None

 rep["result"]="PASS" if all(rep["checks"].values()) and not rep["errors"] else "PARTIAL"
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
 dest=OUT/"平台适配层Web与小程序SocketTask回归.json";dest.write_text(json.dumps(rep,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"result":rep["result"],"checks":rep["checks"],"errors":rep["errors"],"exception":rep.get("exception"),"evidence":str(dest)},ensure_ascii=True))
sys.exit(0 if rep["result"]=="PASS" else 1)
