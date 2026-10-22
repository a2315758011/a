# -*- coding: utf-8 -*-
"""RECOVERY-035: real mouse-driven Cocos E2E for generated settlement panel."""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from websockets.sync.client import connect
import requests, threading, subprocess, tempfile, time, json, base64, traceback, hashlib, sys, socket

ROOT=Path(r"C:\Users\ide0007\Desktop\deliverable\AI小游戏实战营\AI小游戏制作工程文件\直播炮塔守城")
PROJECT=ROOT/"_assistant-temp"/"候选战场Cocos-V5隔离工程-20261020"
BUILD=PROJECT/"build"/"web-mobile"
OUT=ROOT/"验收证据"/"RECOVERY-035-UI-PANEL"
OUT.mkdir(parents=True,exist_ok=True)
EDGE=Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
VIEWPORTS=[(360,780),(393,852),(540,760),(540,960),(540,1108)]
W,H=360,780

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(BUILD),**kwargs)
    def log_message(self,fmt,*args): pass

def choose_port():
    for port in range(9237,9251):
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1",port))!=0: return port
    raise RuntimeError("no free CDP port")

def kill_profile(profile):
    esc=str(profile).replace("'","''")
    cmd=("$p=Get-CimInstance Win32_Process | Where-Object {"
         "$_.Name -eq 'msedge.exe' -and $_.CommandLine -like '*"+esc+"*'};"
         "$p | ForEach-Object {Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}")
    try: subprocess.run(["powershell.exe","-NoProfile","-Command",cmd],timeout=12,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    except Exception: pass

server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
report={"task":"RECOVERY-035","test":"real mouse E2E; natural win + return menu + natural loss + restart; both endings across five viewports",
        "startedAt":time.strftime("%Y-%m-%dT%H:%M:%S"),"viewports":[],"actions":[],"samples":[],
        "consoleErrors":[],"consoleWarnings":[],"screenshots":[],"checks":{},"result":"NOT_RUN"}
started=time.monotonic();proc=None;sock=None;profile=None;seq=0

try:
    assert (BUILD/"index.html").exists(),"built Cocos Web-Mobile entry missing"
    profile=tempfile.mkdtemp(prefix="turret-panel-035-")
    port=choose_port();report["debugPort"]=port
    proc=subprocess.Popen([
        str(EDGE),"--headless","--remote-debugging-port="+str(port),"--remote-allow-origins=*",
        "--no-first-run","--no-default-browser-check","--disable-features=msEdgeStartupBoost",
        "--disable-background-timer-throttling","--disable-renderer-backgrounding","--disable-backgrounding-occluded-windows",
        "--enable-webgl","--enable-unsafe-swiftshader","--use-angle=swiftshader","--disable-gpu-sandbox",
        "--user-data-dir="+profile,"about:blank"
    ],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

    pages=None
    for _ in range(150):
        try:
            r=requests.get(f"http://127.0.0.1:{port}/json/list",timeout=.5)
            if r.ok:
                pages=r.json()
                if any(x.get("type")=="page" for x in pages): break
        except Exception: pass
        time.sleep(.1)
    if not pages or not any(x.get("type")=="page" for x in pages): raise RuntimeError("Edge CDP not ready")
    page=next((x for x in pages if x.get("type")=="page" and x.get("url")=="about:blank"),next(x for x in pages if x.get("type")=="page"))
    sock=connect(page["webSocketDebuggerUrl"],open_timeout=8,max_size=32*1024*1024)

    def call(method,params=None,timeout=10):
        nonlocal_dummy=None
        global seq
        seq+=1; ident=seq
        sock.send(json.dumps({"id":ident,"method":method,"params":params or {}}))
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            msg=json.loads(sock.recv(timeout=max(.05,deadline-time.monotonic())))
            if msg.get("id")==ident:
                if "error" in msg: raise RuntimeError(f"CDP {method}: {msg['error']}")
                return msg.get("result",{})
            name=msg.get("method");p=msg.get("params",{})
            if name=="Runtime.exceptionThrown":
                report["consoleErrors"].append({"type":name,"text":p.get("exceptionDetails",{}).get("text")})
            if name=="Runtime.consoleAPICalled" and p.get("type") in ("error","warning"):
                item={"type":p["type"],"text":" ".join(str(a.get("value",a.get("description",""))) for a in p.get("args",[]))[:500]}
                (report["consoleErrors"] if p["type"]=="error" else report["consoleWarnings"]).append(item)
        raise TimeoutError("CDP "+method)

    def ev(expr,timeout=9):
        r=call("Runtime.evaluate",{"expression":expr,"returnByValue":True},timeout)
        if r.get("exceptionDetails"): raise RuntimeError(r["exceptionDetails"].get("text","Runtime.evaluate failed"))
        return r.get("result",{}).get("value")

    state_expr="""(()=>{const sc=cc.director.getScene(),n=sc&&sc.getChildByName('候选美术战场画布'),c=n&&n.getComponent('守城控制器'),a=n&&n.getComponent('待审战场美术覆盖器');if(!c||!a)return null;const p=a.settlementPanel,pt=p&&p.node.position,u=p&&p.node.getComponent('cc.UITransform'),v=cc.view.getVisibleSize(),live=c.liveSessionSnapshot();return {game:{state:c.state,hp:c.hp,wave:c.wave,towers:c.towers.length,kills:c.kills,enemies:c.enemies.length,time:c.time,inputBlocked:!!c.inputBlocked,onlineViewers:live.onlineViewers},art:{ready:!!a.ready,failed:!!a.failed,battleHudActive:!!(a.uiRoot&&a.uiRoot.active),artRootActive:!!(a.artRoot&&a.artRoot.active)},menu:{active:!!(a.mainMenuRoot&&a.mainMenuRoot.active),inMainMenu:!!a.inMainMenu,title:a.mainMenuTitle&&a.mainMenuTitle.string,start:a.mainMenuStartLabel&&a.mainMenuStartLabel.string},settlement:{active:!!(a.settlementRoot&&a.settlementRoot.active),title:a.settlementTitle&&a.settlementTitle.string,subtitle:a.settlementSubtitle&&a.settlementSubtitle.string,stats:a.settlementStats&&a.settlementStats.string,again:a.settlementButtonLabel&&a.settlementButtonLabel.string,menu:a.settlementMenuLabel&&a.settlementMenuLabel.string,panelLoaded:!!(p&&p.spriteFrame),panelActive:!!(p&&p.node.activeInHierarchy),panelSize:u?[u.width,u.height]:null,panelPosition:pt?[pt.x,pt.y]:null,visibleSize:[v.width,v.height]}}})()"""
    def state(): return ev(state_expr)

    def wait_for(pred,timeout=35,interval=.2):
        end=time.monotonic()+timeout;last=None
        while time.monotonic()<end:
            try:
                call("Page.bringToFront",timeout=5);last=state()
                if pred(last): return last
            except Exception as e:
                report.setdefault("transientReadErrors",[]).append(str(e))
            time.sleep(interval)
        return last

    def point(node_expr):
        q=ev(f"""(()=>{{const sc=cc.director.getScene(),n=sc.getChildByName('候选美术战场画布'),a=n.getComponent('待审战场美术覆盖器'),v=cc.view.getVisibleSize(),p={node_expr}.position;return {{x:p.x,y:p.y,vw:v.width}}}})()""")
        scale=W/q["vw"]
        return round(W/2+q["x"]*scale),round(H/2-q["y"]*scale)

    def named(name):
        q=ev(f"""(()=>{{const sc=cc.director.getScene(),n=sc.getChildByName('候选美术战场画布'),v=cc.view.getVisibleSize(),p=n.getChildByName('{name}').position;return {{x:p.x,y:p.y,vw:v.width}}}})()""")
        scale=W/q["vw"]
        return round(W/2+q["x"]*scale),round(H/2-q["y"]*scale)

    def click(name,x,y,delay=.14):
        call("Input.dispatchMouseEvent",{"type":"mousePressed","x":x,"y":y,"button":"left","clickCount":1},8)
        call("Input.dispatchMouseEvent",{"type":"mouseReleased","x":x,"y":y,"button":"left","clickCount":1},8)
        report["actions"].append({"t":round(time.monotonic()-started,2),"name":name,"x":x,"y":y,"viewport":[W,H]})
        time.sleep(delay)

    def shot(name):
        raw=base64.b64decode(call("Page.captureScreenshot",{"format":"png"},12)["data"])
        p=OUT/name;p.write_bytes(raw)
        report["screenshots"].append({"file":name,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest().upper()})

    def set_viewport(w,h):
        global W,H
        W,H=w,h
        call("Emulation.setDeviceMetricsOverride",{"width":w,"height":h,"deviceScaleFactor":1,"mobile":False})
        call("Page.bringToFront")
        time.sleep(.8)

    def viewport_sweep(ending):
        for w,h in VIEWPORTS:
            set_viewport(w,h)
            q=wait_for(lambda x:x and x["settlement"]["active"] and x["settlement"]["panelLoaded"],5,.1)
            if not q: raise RuntimeError(f"{ending}: settlement panel disappeared at {w}x{h}")
            p=q["settlement"]
            vw,vh=p["visibleSize"];pw,ph=p["panelSize"];px,py=p["panelPosition"]
            checks={
              "settlementVisible":p["active"],
              "panelLoaded":p["panelLoaded"],
              "panelVisible":p["panelActive"],
              "panelInsideVisibleRect":abs(px)+pw/2<=vw/2+1 and abs(py)+ph/2<=vh/2+1,
              "panelWidthWithinSafeArea":pw<=vw-28+1,
              "panelHeightWithinSafeArea":ph<=vh-54+1
            }
            row={"ending":ending,"viewport":[w,h],"visibleSize":[vw,vh],"panelSize":[pw,ph],"panelPosition":[px,py],"checks":checks,"pass":all(checks.values())}
            report["viewports"].append(row)
            shot(f"{ending}-{w}x{h}.png")
            if not row["pass"]: raise RuntimeError(f"{ending}: viewport QA failed {w}x{h}: {checks}")

    for m in ("Page.enable","Runtime.enable","Log.enable","Network.enable"): call(m)
    call("Network.setCacheDisabled",{"cacheDisabled":True})
    call("Emulation.setDeviceMetricsOverride",{"width":W,"height":H,"deviceScaleFactor":1,"mobile":False})
    call("Page.navigate",{"url":f"http://127.0.0.1:{server.server_address[1]}/"})

    initial=wait_for(lambda q:q and q["art"]["ready"] and not q["art"]["failed"] and q["menu"]["active"],45,.2)
    report["initial"]=initial
    if not initial: raise RuntimeError("main menu/art did not become ready")
    report["checks"]["initialPanelLoaded"]=bool(initial["settlement"]["panelLoaded"])
    report["checks"]["initialMenuBlocksInput"]=bool(initial["game"]["state"]=="ready" and initial["game"]["inputBlocked"] and initial["menu"]["active"] and not initial["art"]["battleHudActive"])
    shot("00-main-menu-360x780.png")

    mx,my=point("a.mainMenuStartSprite.node")
    click("main-menu-start",mx,my,.35)
    started1=wait_for(lambda q:q and q["game"]["state"]=="running" and not q["menu"]["active"] and q["art"]["battleHudActive"] and not q["game"]["inputBlocked"],12,.15)
    if not started1: raise RuntimeError("start button did not begin battle")
    report["checks"]["startBattle"]=started1["game"]["towers"]==9
    vx,vy=named("按钮-观众+1")
    for _ in range(15): click("viewer-join",vx,vy,.13)
    ux,uy=named("按钮-升级")
    click("gift-upgrade",ux,uy,.15);click("gift-upgrade",ux,uy,.15)
    setup=state();report["winSetup"]=setup
    if setup["game"]["towers"]!=24 or setup["game"]["onlineViewers"]!=15: raise RuntimeError("win setup not 24 towers/15 viewers")

    win=None;deadline=time.monotonic()+115;last_wave=1
    while time.monotonic()<deadline:
        call("Page.bringToFront",timeout=5);q=state()
        report["samples"].append({"phase":"win","t":round(time.monotonic()-started,2),"game":q["game"]})
        if q["game"]["wave"]!=last_wave:
            last_wave=q["game"]["wave"];report.setdefault("waveChanges",[]).append({"t":round(time.monotonic()-started,2),"wave":last_wave})
        if q["game"]["state"] in ("win","lose"):win=q;break
        time.sleep(.35)
    if not win:raise RuntimeError("natural win timeout")
    time.sleep(.25);win=state();report["winTerminal"]=win
    report["checks"]["naturalWinPanelVisible"]=bool(win["game"]["state"]=="win" and win["game"]["wave"]==3 and win["game"]["kills"]==96 and win["game"]["hp"]>0 and win["settlement"]["active"] and win["settlement"]["title"]=="守城成功" and win["settlement"]["again"]=="再次守城" and win["settlement"]["menu"]=="返回主界面" and win["settlement"]["panelLoaded"] and win["settlement"]["panelActive"] and not win["art"]["battleHudActive"])
    shot("01-natural-win-360x780.png")
    viewport_sweep("win")

    set_viewport(360,780)
    win_back=state()
    if not win_back["settlement"]["active"]:raise RuntimeError("win settlement lost after viewport sweep")
    rx,ry=point("a.settlementMenuSprite.node")
    click("win-return-main-menu",rx,ry,.4)
    menu=wait_for(lambda q:q and q["menu"]["active"] and q["game"]["state"]=="ready" and q["game"]["inputBlocked"],10,.15)
    report["afterReturnMenu"]=menu
    report["checks"]["returnMenuHidesPanel"]=bool(menu and not menu["settlement"]["active"] and not menu["settlement"]["panelActive"] and not menu["art"]["battleHudActive"] and menu["game"]["towers"]==24 and menu["game"]["onlineViewers"]==15 and menu["game"]["hp"]==100)
    mx,my=point("a.mainMenuStartSprite.node")
    click("second-run-start",mx,my,.35)
    second=wait_for(lambda q:q and q["game"]["state"]=="running" and not q["menu"]["active"],10,.15)
    if not second:raise RuntimeError("second run did not start")
    report["checks"]["secondRunStartedWithSession"]=second["game"]["onlineViewers"]==15 and second["game"]["towers"]==24

    lx,ly=named("按钮-离场")
    for _ in range(15):click("viewer-leave",lx,ly,.13)
    base=wait_for(lambda q:q and q["game"]["towers"]==9 and q["game"]["onlineViewers"]==0,8,.1)
    report["baseNineAfterViewerLeaves"]=base
    report["checks"]["viewerLeavesPreserveBaseTowers"]=bool(base and base["game"]["towers"]==9 and base["game"]["onlineViewers"]==0)
    if not report["checks"]["viewerLeavesPreserveBaseTowers"]:raise RuntimeError("viewer leave did not restore base-nine formation")

    loss=None;deadline=time.monotonic()+115
    while time.monotonic()<deadline:
        call("Page.bringToFront",timeout=5);q=state()
        report["samples"].append({"phase":"loss","t":round(time.monotonic()-started,2),"game":q["game"]})
        if q["game"]["state"] in ("lose","win"):loss=q;break
        time.sleep(.35)
    if not loss:raise RuntimeError("natural loss timeout")
    time.sleep(.25);loss=state();report["lossTerminal"]=loss
    report["checks"]["naturalLossPanelVisible"]=bool(loss["game"]["state"]=="lose" and loss["game"]["hp"]==0 and loss["settlement"]["active"] and loss["settlement"]["title"]=="守城失败" and loss["settlement"]["again"]=="再次守城" and loss["settlement"]["menu"]=="返回主界面" and loss["settlement"]["panelLoaded"] and loss["settlement"]["panelActive"] and not loss["art"]["battleHudActive"])
    shot("02-natural-loss-360x780.png")
    viewport_sweep("loss")

    set_viewport(360,780)
    ax,ay=point("a.settlementButtonSprite.node")
    click("loss-restart",ax,ay,.55)
    again=wait_for(lambda q:q and q["game"]["state"]=="ready" and not q["settlement"]["active"] and q["art"]["battleHudActive"],10,.15)
    report["afterAgain"]=again
    report["checks"]["restartRestoresReady"]=bool(again and again["game"]["hp"]==100 and again["game"]["wave"]==1 and again["game"]["towers"]==9 and again["game"]["kills"]==0 and again["game"]["enemies"]==0 and not again["game"]["inputBlocked"] and not again["menu"]["active"] and not again["settlement"]["panelActive"])
    shot("03-restart-ready-360x780.png")
    report["result"]="PASS" if all(report["checks"].values()) and not report["consoleErrors"] else "PARTIAL"

except Exception as e:
    report["result"]="ERROR";report["exception"]=repr(e);report["stack"]=traceback.format_exc()[-6000:]
finally:
    if sock:
        try:sock.close()
        except:pass
    if proc:
        try:proc.terminate();proc.wait(timeout=2)
        except:
            try:proc.kill()
            except:pass
    if profile:
        kill_profile(profile);time.sleep(.3)
    try:server.shutdown()
    except:pass
    report["durationSeconds"]=round(time.monotonic()-started,2)
    report["finishedAt"]=time.strftime("%Y-%m-%dT%H:%M:%S")
    report["summary"]={"result":report["result"],"checks":report.get("checks",{}),
      "win":report.get("winTerminal",{}).get("game") if isinstance(report.get("winTerminal"),dict) else None,
      "loss":report.get("lossTerminal",{}).get("game") if isinstance(report.get("lossTerminal"),dict) else None,
      "viewportsPass":sum(1 for x in report.get("viewports",[]) if x.get("pass")),
      "viewportsTotal":len(report.get("viewports",[])),"consoleErrorCount":len(report.get("consoleErrors",[]))}
    target=OUT/"真实Cocos双结局与五视口回归.json"
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"result":report["result"],"durationSeconds":report["durationSeconds"],"summary":report["summary"],"exception":report.get("exception"),"evidence":str(target),"screenshots":report.get("screenshots",[])},ensure_ascii=True),flush=True)
sys.exit(0 if report["result"]=="PASS" else 1)
