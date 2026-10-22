# -*- coding: utf-8 -*-
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from websockets.sync.client import connect
import requests,threading,subprocess,tempfile,time,json,traceback,sys,socket

ROOT=Path(r"C:\Users\ide0007\Desktop\deliverable\AI小游戏实战营\AI小游戏制作工程文件\直播炮塔守城")
BUILD=ROOT/"CocosCreator工程"/"build"/"web-mobile"
OUT=ROOT/"验收证据"/"WHOLE-GAME-FORMAL-SHOP-20261022"
OUT.mkdir(parents=True,exist_ok=True)
EDGE=Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
VIEWPORTS=[(360,780),(393,852),(540,760),(540,960),(540,1108)]

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**k):super().__init__(*a,directory=str(BUILD),**k)
    def log_message(self,*a):pass
def free_port():
    for p in range(9237,9261):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1",p))!=0:return p
    raise RuntimeError("no free port")
def kill(profile):
    e=str(profile).replace("'","''")
    cmd="$p=Get-CimInstance Win32_Process|?{$_.Name -eq 'msedge.exe' -and $_.CommandLine -like '*"+e+"*'};$p|%{Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}"
    try:subprocess.run(["powershell","-NoProfile","-Command",cmd],timeout=10,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    except:pass

srv=ThreadingHTTPServer(("127.0.0.1",0),Handler);threading.Thread(target=srv.serve_forever,daemon=True).start()
rep={"task":"WHOLE-GAME-FORMAL-SHOP-20261022","test":"five viewport real shop open/close/layout","viewports":[],"errors":[],"startedAt":time.strftime("%Y-%m-%dT%H:%M:%S")}
profile=tempfile.mkdtemp(prefix="turret-shop-5vp-030-");port=free_port();proc=None;ws=None;seq=0
try:
    proc=subprocess.Popen([str(EDGE),"--headless","--remote-debugging-port="+str(port),"--remote-allow-origins=*",
      "--no-first-run","--no-default-browser-check","--disable-features=msEdgeStartupBoost","--disable-background-timer-throttling",
      "--user-data-dir="+profile,"about:blank"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    pages=None
    for _ in range(130):
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
    def wait(pred,timeout=35):
        end=time.monotonic()+timeout;last=None
        while time.monotonic()<end:
            try:
                call("Page.bringToFront");last=ev("""(()=>{const n=cc.director.getScene().getChildByName('守城画布'),a=n&&n.getComponent('待审战场美术覆盖器'),c=n&&n.getComponent('守城控制器');if(!a||!c)return null;return {ready:a.ready,failed:a.failed,menu:a.mainMenuRoot&&a.mainMenuRoot.active,shop:a.shopRoot&&a.shopRoot.active,state:c.state,inputBlocked:c.inputBlocked}})()""")
                if pred(last):return last
            except:pass
            time.sleep(.18)
        return last
    def screen(expr,w,h):
        q=ev(f"""(()=>{{const n=cc.director.getScene().getChildByName('守城画布'),a=n.getComponent('待审战场美术覆盖器'),v=cc.view.getVisibleSize(),p={expr}.position;return {{x:p.x,y:p.y,vw:v.width}}}})()""")
        sc=w/q["vw"];return round(w/2+q["x"]*sc),round(h/2-q["y"]*sc)
    def click(x,y):
        call("Input.dispatchMouseEvent",{"type":"mousePressed","x":x,"y":y,"button":"left","clickCount":1});call("Input.dispatchMouseEvent",{"type":"mouseReleased","x":x,"y":y,"button":"left","clickCount":1});time.sleep(.25)
    for m in ("Page.enable","Runtime.enable","Network.enable"):call(m)
    call("Network.setCacheDisabled",{"cacheDisabled":True})
    url=f"http://127.0.0.1:{srv.server_address[1]}/"
    for w,h in VIEWPORTS:
        call("Emulation.setDeviceMetricsOverride",{"width":w,"height":h,"deviceScaleFactor":1,"mobile":False})
        call("Page.navigate",{"url":url})
        ready=wait(lambda q:q and q["ready"] and not q["failed"] and q["menu"])
        if not ready:raise RuntimeError(f"menu not ready {w}x{h}")
        sx,sy=screen("a.mainMenuShopSprite.node",w,h)
        startx,starty=screen("a.mainMenuStartSprite.node",w,h)
        row={"target":[w,h],"shopPoint":[sx,sy],"startPoint":[startx,starty],"checks":{}}
        row["checks"]["shopEntryInBounds"]=0<sx<w and 0<sy<h
        row["checks"]["startInBounds"]=0<startx<w and 0<starty<h
        before=ev("""(()=>{const n=cc.director.getScene().getChildByName('守城画布'),a=n.getComponent('待审战场美术覆盖器'),c=n.getComponent('守城控制器');return {wallet:a.mainMenuWallet.string,shopLabel:a.mainMenuShopLabel.string,profile:c.profileSnapshot()}})()""")
        row["before"]=before
        row["checks"]["mainMenuEconomyLabels"]=before["wallet"].startswith("守城币 ") and before["shopLabel"]=="战备商店"
        click(sx,sy)
        opened=wait(lambda q:q and q["shop"] and not q["menu"],8)
        row["checks"]["realOpen"]=bool(opened and opened["inputBlocked"])
        shop=ev("""(()=>{const n=cc.director.getScene().getChildByName('守城画布'),a=n.getComponent('待审战场美术覆盖器');return {title:a.shopTitle.string,wallet:a.shopWallet.string,message:a.shopMessage.string,rows:a.shopRows.map(r=>({id:r.id,info:r.info.string,button:r.buttonLabel.string,interactable:r.button.interactable}))}})()""")
        row["shop"]=shop
        row["checks"]["threeProducts"]=len(shop["rows"])==3 and [x["id"] for x in shop["rows"]]==["coreShield","fireControl","viewerBoost"]
        points=[]
        for ident in ("coreShield","fireControl","viewerBoost"):
            x,y=screen("a.shopRows.find(r=>r.id==='"+ident+"').buttonSprite.node",w,h);points.append([x,y]);row["checks"]["row_"+ident+"_inBounds"]=0<x<w and 0<y<h
        row["productPoints"]=points
        cx,cy=screen("a.shopCloseSprite.node",w,h);row["closePoint"]=[cx,cy];row["checks"]["closeInBounds"]=0<cx<w and 0<cy<h
        click(cx,cy)
        closed=wait(lambda q:q and q["menu"] and not q["shop"],8)
        row["checks"]["realClose"]=bool(closed and closed["inputBlocked"])
        row["pass"]=all(row["checks"].values());rep["viewports"].append(row)
except Exception as e:
    rep["exception"]=repr(e);rep["stack"]=traceback.format_exc()[-4000:]
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
    rep["overallPass"]=len(rep["viewports"])==5 and all(x["pass"] for x in rep["viewports"]) and not rep["errors"] and "exception" not in rep
    rep["finishedAt"]=time.strftime("%Y-%m-%dT%H:%M:%S")
    dest=OUT/"商店五视口真实输入回归.json";dest.write_text(json.dumps(rep,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"overallPass":rep["overallPass"],"viewports":[{"target":x["target"],"pass":x["pass"],"checks":x["checks"]} for x in rep["viewports"]],"errors":rep["errors"],"exception":rep.get("exception"),"evidence":str(dest)},ensure_ascii=True))
sys.exit(0 if rep["overallPass"] else 1)
