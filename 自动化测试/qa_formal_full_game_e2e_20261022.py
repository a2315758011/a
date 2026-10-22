# -*- coding: utf-8 -*-
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from websockets.sync.client import connect
import requests, threading, subprocess, tempfile, time, json, base64, traceback, hashlib, sys, socket

ROOT=Path(r"C:\Users\ide0007\Desktop\deliverable\AI小游戏实战营\AI小游戏制作工程文件\直播炮塔守城")
PROJECT=ROOT/"CocosCreator工程"
BUILD=PROJECT/"build"/"web-mobile"
OUT=ROOT/"验收证据"/"WHOLE-GAME-FORMAL-E2E-20261022"
OUT.mkdir(parents=True,exist_ok=True)
EDGE=Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
W,H=360,780

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(BUILD),**kwargs)
    def log_message(self,fmt,*args): pass

def choose_port():
    for p in range(9237,9251):
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1",p)) != 0:
                return p
    raise RuntimeError("no free CDP port")

def kill_profile(profile):
    esc=str(profile).replace("'","''")
    cmd=("$p=Get-CimInstance Win32_Process | Where-Object {"
         "$_.Name -eq 'msedge.exe' -and $_.CommandLine -like '*"+esc+"*'};"
         "$p | ForEach-Object {Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}")
    try:
        subprocess.run(["powershell.exe","-NoProfile","-Command",cmd],timeout=10,
                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    except Exception: pass

server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
report={"task":"WHOLE-GAME-FORMAL-E2E-20261022","test":"main-menu vertical slice double-ending E2E","viewport":[W,H],
        "startedAt":time.strftime("%Y-%m-%dT%H:%M:%S"),"actions":[],"samples":[],
        "consoleErrors":[],"consoleWarnings":[],"screenshots":[],"checks":{},"result":"NOT_RUN"}
started=time.monotonic();proc=None;sock=None;profile=None;seq=0

try:
    profile=tempfile.mkdtemp(prefix="turret-vertical-026-")
    port=choose_port(); report["debugPort"]=port
    proc=subprocess.Popen(["node",str(ROOT/"自动化测试"/"edge_cdp_launcher_20261022.js"),str(port),profile,"keep"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

    pages=None
    for _ in range(100):
        try:
            r=requests.get(f"http://127.0.0.1:{port}/json/list",timeout=.15)
            if r.ok:
                pages=r.json()
                if any(x.get("type")=="page" for x in pages): break
        except Exception: pass
        time.sleep(.1)
    if not pages: raise RuntimeError("Edge CDP not ready")
    page=next((x for x in pages if x.get("type")=="page"),pages[0])
    sock=connect(page["webSocketDebuggerUrl"],open_timeout=8,max_size=32*1024*1024)

    def call(method,params=None,timeout=10):
        global seq
        seq+=1; ident=seq
        sock.send(json.dumps({"id":ident,"method":method,"params":params or {}}))
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            m=json.loads(sock.recv(timeout=max(.05,deadline-time.monotonic())))
            if m.get("id")==ident:
                if "error" in m: raise RuntimeError(f"{method}: {m['error']}")
                return m.get("result",{})
            name=m.get("method"); p=m.get("params",{})
            if name=="Runtime.exceptionThrown":
                report["consoleErrors"].append({"type":name,"text":p.get("exceptionDetails",{}).get("text")})
            if name=="Runtime.consoleAPICalled" and p.get("type") in ("error","warning"):
                item={"type":p["type"],"text":" ".join(str(a.get("value",a.get("description",""))) for a in p.get("args",[]))[:500]}
                (report["consoleErrors"] if p["type"]=="error" else report["consoleWarnings"]).append(item)
        raise TimeoutError(method)

    def ev(expr,timeout=9):
        r=call("Runtime.evaluate",{"expression":expr,"returnByValue":True},timeout)
        if r.get("exceptionDetails"): raise RuntimeError(r["exceptionDetails"].get("text","Runtime.evaluate failed"))
        return r.get("result",{}).get("value")

    state_expr="""(()=>{const sc=cc.director.getScene(),n=sc&&sc.getChildByName('守城画布'),c=n&&n.getComponent('守城控制器'),a=n&&n.getComponent('待审战场美术覆盖器');if(!c||!a)return null;return {game:{state:c.state,hp:c.hp,wave:c.wave,towers:c.towers.length,kills:c.kills,enemies:c.enemies.length,time:c.time,inputBlocked:!!c.inputBlocked},art:{ready:!!a.ready,failed:!!a.failed,battleHudActive:!!(a.uiRoot&&a.uiRoot.active),artRootActive:!!(a.artRoot&&a.artRoot.active)},menu:{active:!!(a.mainMenuRoot&&a.mainMenuRoot.active),inMainMenu:!!a.inMainMenu,title:a.mainMenuTitle&&a.mainMenuTitle.string,start:a.mainMenuStartLabel&&a.mainMenuStartLabel.string},settlement:{active:!!(a.settlementRoot&&a.settlementRoot.active),title:a.settlementTitle&&a.settlementTitle.string,again:a.settlementButtonLabel&&a.settlementButtonLabel.string,menu:a.settlementMenuLabel&&a.settlementMenuLabel.string}}})()"""

    def state():
        return ev(state_expr)

    def wait_for(pred,timeout=35,interval=.2):
        deadline=time.monotonic()+timeout; last=None
        while time.monotonic()<deadline:
            try:
                call("Page.bringToFront",timeout=5)
                last=state()
                if pred(last): return last
            except Exception as e:
                report.setdefault("transientReadErrors",[]).append(str(e))
            time.sleep(interval)
        return last

    def point(expr):
        q=ev(f"""(()=>{{const sc=cc.director.getScene(),n=sc.getChildByName('守城画布'),a=n.getComponent('待审战场美术覆盖器'),v=cc.view.getVisibleSize(),p={expr}.position;return {{x:p.x,y:p.y,vw:v.width}}}})()""")
        scale=W/q["vw"]
        return round(W/2+q["x"]*scale),round(H/2-q["y"]*scale)

    def named(name):
        q=ev(f"""(()=>{{const sc=cc.director.getScene(),n=sc.getChildByName('守城画布'),v=cc.view.getVisibleSize(),p=n.getChildByName('{name}').position;return {{x:p.x,y:p.y,vw:v.width}}}})()""")
        scale=W/q["vw"]
        return round(W/2+q["x"]*scale),round(H/2-q["y"]*scale)

    def click(name,x,y,delay=.14):
        call("Input.dispatchMouseEvent",{"type":"mousePressed","x":x,"y":y,"button":"left","clickCount":1},8)
        call("Input.dispatchMouseEvent",{"type":"mouseReleased","x":x,"y":y,"button":"left","clickCount":1},8)
        report["actions"].append({"t":round(time.monotonic()-started,2),"name":name,"x":x,"y":y})
        time.sleep(delay)

    def shot(name):
        raw=base64.b64decode(call("Page.captureScreenshot",{"format":"png"},12)["data"])
        p=OUT/name; p.write_bytes(raw)
        report["screenshots"].append({"file":name,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest().upper()})

    for m in ("Page.enable","Runtime.enable","Log.enable","Network.enable"): call(m)
    call("Network.setCacheDisabled",{"cacheDisabled":True})
    call("Emulation.setDeviceMetricsOverride",{"width":W,"height":H,"deviceScaleFactor":1,"mobile":False})
    call("Page.navigate",{"url":f"http://127.0.0.1:{server.server_address[1]}/"})

    initial=wait_for(lambda q:q and q["art"]["ready"] and not q["art"]["failed"] and q["menu"]["active"],40,.25)
    if not initial: raise RuntimeError("main menu/art not ready")
    report["initial"]=initial
    report["checks"]["initialMenu"]=bool(initial["game"]["state"]=="ready" and initial["game"]["inputBlocked"] and initial["menu"]["active"] and initial["menu"]["title"]=="直播炮塔守城" and initial["menu"]["start"]=="开始守城" and not initial["art"]["battleHudActive"])
    shot("00-启动主界面.png")

    vx,vy=named("按钮-观众+1")
    click("主界面期间尝试观众+1",vx,vy,.2)
    blocked=state(); report["afterBlockedClick"]=blocked
    report["checks"]["menuBlocksBattleInput"]=bool(blocked["game"]["towers"]==9 and blocked["game"]["state"]=="ready")

    mx,my=point("a.mainMenuStartSprite.node")
    click("主界面-开始守城",mx,my,.3)
    started1=wait_for(lambda q:q and q["game"]["state"]=="running" and not q["menu"]["active"] and q["art"]["battleHudActive"] and not q["game"]["inputBlocked"],10,.15)
    if not started1: raise RuntimeError("main menu start did not enter battle")
    report["firstBattleStart"]=started1
    report["checks"]["menuStartsBattle"]=True
    shot("01-主界面进入战斗.png")

    vx,vy=named("按钮-观众+1")
    for _ in range(15): click("观众加入",vx,vy,.13)
    ux,uy=named("按钮-升级")
    click("升级",ux,uy,.14); click("升级",ux,uy,.14)
    setup=state(); report["winSetup"]=setup
    if setup["game"]["towers"]!=24: raise RuntimeError("win setup expected 24 towers")

    win=None; deadline=time.monotonic()+110; last_wave=1
    while time.monotonic()<deadline:
        call("Page.bringToFront",timeout=5); q=state()
        report["samples"].append({"phase":"win","t":round(time.monotonic()-started,2),"game":q["game"]})
        if q["game"]["wave"]!=last_wave:
            last_wave=q["game"]["wave"]; report.setdefault("waveChanges",[]).append({"t":round(time.monotonic()-started,2),"wave":last_wave})
        if q["game"]["state"] in ("win","lose"): win=q; break
        time.sleep(.28)
    if not win: raise RuntimeError("natural win timeout")
    time.sleep(.25); win=state(); report["winTerminal"]=win
    report["checks"]["naturalWinSettlement"]=bool(win["game"]["state"]=="win" and win["game"]["kills"]==96 and win["game"]["hp"]>0 and win["settlement"]["active"] and win["settlement"]["title"]=="守城成功" and win["settlement"]["again"]=="再次守城" and win["settlement"]["menu"]=="返回主界面" and not win["art"]["battleHudActive"])
    shot("02-自然胜利结算.png")

    rx,ry=point("a.settlementMenuSprite.node")
    click("胜利结算-返回主界面",rx,ry,.4)
    menu2=wait_for(lambda q:q and q["menu"]["active"] and q["game"]["state"]=="ready" and q["game"]["inputBlocked"],10,.15)
    if not menu2: raise RuntimeError("return-to-menu did not restore main menu")
    report["afterReturnMenu"]=menu2
    report["checks"]["returnToMenu"]=bool(menu2["game"]["hp"]==100 and menu2["game"]["towers"]==24 and menu2["game"]["kills"]==0 and not menu2["settlement"]["active"] and not menu2["art"]["battleHudActive"])
    shot("03-结算返回主界面.png")

    vx,vy=named("按钮-观众+1")
    click("返回主界面后尝试观众+1",vx,vy,.2)
    blocked2=state(); report["afterSecondBlockedClick"]=blocked2
    report["checks"]["menuStillBlocksBattleInput"]=bool(blocked2["game"]["towers"]==24 and blocked2["menu"]["active"])

    mx,my=point("a.mainMenuStartSprite.node")
    click("主界面-第二局开始",mx,my,.3)
    started2=wait_for(lambda q:q and q["game"]["state"]=="running" and not q["menu"]["active"],10,.15)
    if not started2: raise RuntimeError("second run did not start")
    report["checks"]["secondRunStarts"]=True

    lx,ly=named("按钮-离场")
    for _ in range(15): click("离场-移除在线观众塔",lx,ly,.13)
    loss_setup=state(); report["lossSetup"]=loss_setup
    if loss_setup["game"]["towers"]!=9: raise RuntimeError("loss setup expected 1 tower")

    loss=None; deadline=time.monotonic()+115
    while time.monotonic()<deadline:
        call("Page.bringToFront",timeout=5); q=state()
        report["samples"].append({"phase":"loss","t":round(time.monotonic()-started,2),"game":q["game"]})
        if q["game"]["state"] in ("lose","win"): loss=q; break
        time.sleep(.25)
    if not loss: raise RuntimeError("natural loss timeout")
    time.sleep(.25); loss=state(); report["lossTerminal"]=loss
    report["checks"]["naturalLossSettlement"]=bool(loss["game"]["state"]=="lose" and loss["game"]["hp"]==0 and loss["settlement"]["active"] and loss["settlement"]["title"]=="守城失败" and loss["settlement"]["again"]=="再次守城" and loss["settlement"]["menu"]=="返回主界面" and not loss["art"]["battleHudActive"])
    shot("04-自然失败结算.png")

    ax,ay=point("a.settlementButtonSprite.node")
    click("失败结算-再次守城",ax,ay,.6)
    again=wait_for(lambda q:q and q["game"]["state"]=="ready" and not q["settlement"]["active"] and q["art"]["battleHudActive"],10,.15)
    if not again: raise RuntimeError("again button did not reset battle")
    report["afterAgain"]=again
    report["checks"]["againResetsBattle"]=bool(again["game"]["hp"]==100 and again["game"]["wave"]==1 and again["game"]["towers"]==9 and again["game"]["kills"]==0 and again["game"]["enemies"]==0 and not again["game"]["inputBlocked"] and not again["menu"]["active"])
    shot("05-失败后再次守城.png")

    report["result"]="PASS" if all(report["checks"].values()) and not report["consoleErrors"] else "PARTIAL"

except Exception as e:
    report["result"]="ERROR"; report["exception"]=repr(e); report["stack"]=traceback.format_exc()[-5000:]
finally:
    if sock:
        try:sock.close()
        except:pass
    if proc:
        try:proc.terminate(); proc.wait(timeout=2)
        except:
            try:proc.kill()
            except:pass
    if profile:
        kill_profile(profile); time.sleep(.3)
    try:server.shutdown()
    except:pass
    report["durationSeconds"]=round(time.monotonic()-started,2)
    report["finishedAt"]=time.strftime("%Y-%m-%dT%H:%M:%S")
    report["summary"]={"result":report["result"],"checks":report.get("checks",{}),
      "win":report.get("winTerminal",{}).get("game") if isinstance(report.get("winTerminal"),dict) else None,
      "loss":report.get("lossTerminal",{}).get("game") if isinstance(report.get("lossTerminal"),dict) else None,
      "returnMenu":report.get("afterReturnMenu",{}).get("game") if isinstance(report.get("afterReturnMenu"),dict) else None,
      "again":report.get("afterAgain",{}).get("game") if isinstance(report.get("afterAgain"),dict) else None,
      "consoleErrorCount":len(report.get("consoleErrors",[]))}
    target=OUT/"正式整局双结局回归-房间会话修正.json"
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"result":report["result"],"durationSeconds":report["durationSeconds"],"summary":report["summary"],"exception":report.get("exception"),"evidence":str(target),"screenshots":report.get("screenshots",[])},ensure_ascii=True),flush=True)
sys.exit(0 if report["result"]=="PASS" else 1)
