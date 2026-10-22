# -*- coding: utf-8 -*-
"""WHOLE-GAME-FORMAL-SHOP-PERSISTENCE-20261022 real mouse shop/persistence E2E.
Fresh browser profile -> natural loss reward -> shop purchase -> reload -> permanent effect.
No direct game/profile state mutation.
"""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from websockets.sync.client import connect
import requests,threading,subprocess,tempfile,time,json,base64,traceback,hashlib,sys,socket

ROOT=Path(r"C:\Users\ide0007\Desktop\deliverable\AI小游戏实战营\AI小游戏制作工程文件\直播炮塔守城")
BUILD=ROOT/"CocosCreator工程"/"build"/"web-mobile"
OUT=ROOT/"验收证据"/"WHOLE-GAME-FORMAL-SHOP-PERSISTENCE-20261022"
OUT.mkdir(parents=True,exist_ok=True)
EDGE=Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
W,H=360,780

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**k):super().__init__(*a,directory=str(BUILD),**k)
    def log_message(self,*a):pass

def free_port():
    for p in range(9237,9261):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1",p))!=0:return p
    raise RuntimeError("no free CDP port")

def kill_profile(profile):
    e=str(profile).replace("'","''")
    cmd=("$p=Get-CimInstance Win32_Process | Where-Object {"
         "$_.Name -eq 'msedge.exe' -and $_.CommandLine -like '*"+e+"*'};"
         "$p | ForEach-Object {Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}")
    try:subprocess.run(["powershell.exe","-NoProfile","-Command",cmd],timeout=10,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    except:pass

server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
report={"task":"WHOLE-GAME-FORMAL-SHOP-PERSISTENCE-20261022","test":"natural settlement -> shop purchase -> reload -> permanent upgrade effect",
        "actions":[],"checks":{},"consoleErrors":[],"consoleWarnings":[],"screenshots":[],
        "startedAt":time.strftime("%Y-%m-%dT%H:%M:%S"),"result":"NOT_RUN"}
profile=tempfile.mkdtemp(prefix="turret-shop-030-");port=free_port();proc=None;ws=None;seq=0;started=time.monotonic()
try:
    proc=subprocess.Popen([str(EDGE),"--headless","--remote-debugging-port="+str(port),
      "--remote-allow-origins=*","--no-first-run","--no-default-browser-check",
      "--disable-features=msEdgeStartupBoost","--disable-background-timer-throttling",
      "--disable-renderer-backgrounding","--disable-backgrounding-occluded-windows",
      "--enable-webgl","--enable-unsafe-swiftshader","--use-angle=swiftshader","--disable-gpu-sandbox",
      "--user-data-dir="+profile,"about:blank"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    pages=None
    for _ in range(300):
        try:
            r=requests.get(f"http://127.0.0.1:{port}/json/list",timeout=.5)
            if r.ok:
                pages=r.json()
                if pages:break
        except:pass
        time.sleep(.1)
    if not pages:raise RuntimeError("CDP not ready")
    pg=next((x for x in pages if x.get("url")=="about:blank"),pages[0])
    ws=connect(pg["webSocketDebuggerUrl"],open_timeout=8,max_size=32*1024*1024)

    def call(method,params=None,timeout=10):
        global seq
        seq+=1;i=seq
        ws.send(json.dumps({"id":i,"method":method,"params":params or {}}))
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            m=json.loads(ws.recv(timeout=max(.05,end-time.monotonic())))
            if m.get("id")==i:
                if "error" in m:raise RuntimeError(f"{method}: {m['error']}")
                return m.get("result",{})
            name=m.get("method");p=m.get("params",{})
            if name=="Runtime.exceptionThrown":
                report["consoleErrors"].append({"type":name,"text":p.get("exceptionDetails",{}).get("text")})
            if name=="Runtime.consoleAPICalled" and p.get("type") in ("error","warning"):
                item={"type":p["type"],"text":" ".join(str(a.get("value",a.get("description",""))) for a in p.get("args",[]))[:500]}
                (report["consoleErrors"] if p["type"]=="error" else report["consoleWarnings"]).append(item)
        raise TimeoutError(method)

    def ev(expr,timeout=9):
        r=call("Runtime.evaluate",{"expression":expr,"returnByValue":True},timeout)
        if r.get("exceptionDetails"):raise RuntimeError(r["exceptionDetails"].get("text","Runtime.evaluate failed"))
        return r.get("result",{}).get("value")

    state_expr="""(()=>{const sc=cc.director.getScene(),n=sc&&sc.getChildByName('守城画布'),c=n&&n.getComponent('守城控制器'),a=n&&n.getComponent('待审战场美术覆盖器');if(!c||!a)return null;const p=c.profileSnapshot(),cat=c.shopCatalog(),cloud=c.profileCloudStatus();return {game:{state:c.state,hp:c.hp,maxHP:c.maxHP,wave:c.wave,towers:c.towers.length,kills:c.kills,enemies:c.enemies.length,time:c.time,inputBlocked:c.inputBlocked,lastReward:c.lastReward},profile:p,catalog:cat,cloudConfigured:cloud.configured,menu:{active:a.mainMenuRoot&&a.mainMenuRoot.active,wallet:a.mainMenuWallet&&a.mainMenuWallet.string,start:a.mainMenuStartLabel&&a.mainMenuStartLabel.string},shop:{active:a.shopRoot&&a.shopRoot.active,wallet:a.shopWallet&&a.shopWallet.string,message:a.shopMessage&&a.shopMessage.string,rows:(a.shopRows||[]).map(r=>({id:r.id,info:r.info.string,button:r.buttonLabel.string,interactable:r.button.interactable}))},settlement:{active:a.settlementRoot&&a.settlementRoot.active,title:a.settlementTitle&&a.settlementTitle.string,stats:a.settlementStats&&a.settlementStats.string},localRaw:localStorage.getItem('live-turret-defense.profile.v1')}})()"""

    def state():return ev(state_expr)
    def wait_for(pred,timeout=40,interval=.2):
        end=time.monotonic()+timeout;last=None
        while time.monotonic()<end:
            try:
                call("Page.bringToFront",timeout=5);last=state()
                if pred(last):return last
            except Exception as e:
                report.setdefault("transientReadErrors",[]).append(str(e))
            time.sleep(interval)
        return last
    def point(expr):
        q=ev(f"""(()=>{{const sc=cc.director.getScene(),n=sc.getChildByName('守城画布'),a=n.getComponent('待审战场美术覆盖器'),v=cc.view.getVisibleSize(),p={expr}.position;return {{x:p.x,y:p.y,vw:v.width}}}})()""")
        scale=W/q["vw"];return round(W/2+q["x"]*scale),round(H/2-q["y"]*scale)
    def click(name,x,y,delay=.2):
        call("Input.dispatchMouseEvent",{"type":"mousePressed","x":x,"y":y,"button":"left","clickCount":1},8)
        call("Input.dispatchMouseEvent",{"type":"mouseReleased","x":x,"y":y,"button":"left","clickCount":1},8)
        report["actions"].append({"t":round(time.monotonic()-started,2),"name":name,"x":x,"y":y});time.sleep(delay)
    def shot(name):
        raw=base64.b64decode(call("Page.captureScreenshot",{"format":"png"},12)["data"])
        p=OUT/name;p.write_bytes(raw)
        report["screenshots"].append({"file":name,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest().upper()})

    for m in ("Page.enable","Runtime.enable","Log.enable","Network.enable"):call(m)
    call("Network.setCacheDisabled",{"cacheDisabled":True})
    call("Emulation.setDeviceMetricsOverride",{"width":W,"height":H,"deviceScaleFactor":1,"mobile":False})
    url=f"http://127.0.0.1:{server.server_address[1]}/"
    call("Page.navigate",{"url":url})

    initial=wait_for(lambda q:q and q["menu"]["active"] and q["menu"]["start"]=="开始守城",45,.25)
    if not initial:raise RuntimeError("initial menu not ready")
    report["initial"]=initial
    report["checks"]["freshProfile"]=bool(initial["profile"]["coins"]==0 and initial["profile"]["upgrades"]=={"coreShield":0,"fireControl":0,"viewerBoost":0} and initial["profile"]["stats"]["runs"]==0)
    report["checks"]["catalogHasThreeItems"]=bool(len(initial["catalog"])==3 and [x["id"] for x in initial["catalog"]]==["coreShield","fireControl","viewerBoost"] and initial["catalog"][0]["cost"]==40 and initial["catalog"][1]["cost"]==60 and initial["catalog"][2]["cost"]==80)
    report["checks"]["cloudAdapterNotFaked"]=initial["cloudConfigured"] is False
    report["checks"]["walletStartsZero"]=initial["menu"]["wallet"]=="守城币 0"
    shot("00-新档案主界面.png")

    mx,my=point("a.mainMenuStartSprite.node");click("开始守城",mx,my,.3)
    running=wait_for(lambda q:q and q["game"]["state"]=="running",10,.15)
    if not running:raise RuntimeError("battle did not start")
    report["checks"]["baselineStarts100HP"]=running["game"]["hp"]==100 and running["game"]["maxHP"]==100

    terminal=None;deadline=time.monotonic()+130
    while time.monotonic()<deadline:
        call("Page.bringToFront",timeout=5);q=state()
        if q["game"]["state"] in ("lose","win"):terminal=q;break
        time.sleep(.35)
    if not terminal:raise RuntimeError("natural baseline settlement timeout")
    time.sleep(.25);terminal=state();report["firstSettlement"]=terminal
    kills=terminal["game"]["kills"];won=terminal["game"]["state"]=="win";expected=kills+(50 if won else 0)
    report["checks"]["settlementRewardOnce"]=bool(terminal["game"]["lastReward"]==expected and terminal["profile"]["coins"]==expected and terminal["profile"]["stats"]["runs"]==1 and terminal["profile"]["stats"]["wins"]==(1 if won else 0))
    report["checks"]["settlementShowsReward"]=bool(terminal["settlement"]["active"] and ("奖励 +"+str(expected)+" 守城币") in terminal["settlement"]["stats"] and ("余额 "+str(expected)) in terminal["settlement"]["stats"])
    time.sleep(.5);again_state=state()
    report["checks"]["rewardNotDuplicatedAcrossFrames"]=again_state["profile"]["coins"]==expected and again_state["profile"]["stats"]["runs"]==1
    shot("01-自然结算发放守城币.png")
    if expected<40:raise RuntimeError("natural reward below coreShield first cost")

    rx,ry=point("a.settlementMenuSprite.node");click("返回主界面",rx,ry,.4)
    menu=wait_for(lambda q:q and q["menu"]["active"] and not q["settlement"]["active"],10,.15)
    if not menu:raise RuntimeError("return menu failed")
    report["afterReturnMenu"]=menu
    report["checks"]["menuWalletMatchesReward"]=menu["menu"]["wallet"]=="守城币 "+str(expected)

    sx,sy=point("a.mainMenuShopSprite.node");click("打开战备商店",sx,sy,.35)
    shop=wait_for(lambda q:q and q["shop"]["active"] and not q["menu"]["active"],8,.15)
    if not shop:raise RuntimeError("shop did not open")
    report["shopBeforePurchase"]=shop
    core=next(x for x in shop["catalog"] if x["id"]=="coreShield")
    report["checks"]["shopShowsBalanceAndCoreCost"]=bool(shop["shop"]["wallet"]=="守城币 "+str(expected) and core["cost"]==40 and core["level"]==0 and core["canBuy"])
    shot("02-战备商店购买前.png")

    cx,cy=point("a.shopRows.find(r=>r.id==='coreShield').buttonSprite.node");click("购买水晶护盾",cx,cy,.35)
    purchased=wait_for(lambda q:q and q["profile"]["upgrades"]["coreShield"]==1,8,.15)
    if not purchased:raise RuntimeError("coreShield purchase failed")
    report["afterCorePurchase"]=purchased
    expected_balance=expected-40
    report["checks"]["corePurchaseDeductsCoins"]=bool(purchased["profile"]["coins"]==expected_balance and purchased["shop"]["wallet"]=="守城币 "+str(expected_balance) and purchased["shop"]["message"].startswith("购买成功"))
    fire_before=purchased["profile"]["upgrades"]["fireControl"]
    fire_coins=purchased["profile"]["coins"]
    fire_row=next(r for r in purchased["shop"]["rows"] if r["id"]=="fireControl")
    if fire_coins<60:
        fx,fy=point("a.shopRows.find(r=>r.id==='fireControl').buttonSprite.node");click("余额不足时尝试火控芯片",fx,fy,.3)
        insufficient=state();report["afterInsufficientClick"]=insufficient
        report["checks"]["insufficientPurchaseBlocked"]=bool(insufficient["profile"]["coins"]==fire_coins and insufficient["profile"]["upgrades"]["fireControl"]==fire_before and fire_row["interactable"] is False)
    else:
        report["checks"]["insufficientPurchaseBlocked"]=True
    shot("03-购买护盾后.png")

    bx,by=point("a.shopCloseSprite.node");click("关闭商店",bx,by,.3)
    closed=wait_for(lambda q:q and q["menu"]["active"] and not q["shop"]["active"],8,.15)
    if not closed:raise RuntimeError("shop close failed")
    saved_raw=closed["localRaw"]
    report["checks"]["localStorageWritten"]=bool(saved_raw and '"coreShield":1' in saved_raw)

    # Reload the same origin/browser profile; only persistence is being tested.
    call("Page.navigate",{"url":url})
    reloaded=wait_for(lambda q:q and q["menu"]["active"] and q["profile"]["upgrades"]["coreShield"]==1,45,.25)
    if not reloaded:raise RuntimeError("profile did not survive page reload")
    report["afterReload"]=reloaded
    report["checks"]["profilePersistsAfterReload"]=bool(reloaded["profile"]["coins"]==expected_balance and reloaded["profile"]["upgrades"]["coreShield"]==1 and reloaded["profile"]["stats"]["runs"]==1)
    report["checks"]["cloudStillNotConfiguredAfterReload"]=reloaded["cloudConfigured"] is False
    shot("04-刷新后档案仍在.png")

    mx,my=point("a.mainMenuStartSprite.node");click("刷新后开始下一局",mx,my,.3)
    boosted=wait_for(lambda q:q and q["game"]["state"]=="running",10,.15)
    if not boosted:raise RuntimeError("second battle did not start")
    report["secondRun"]=boosted
    report["checks"]["coreShieldEffectAppliedNextRun"]=bool(boosted["game"]["maxHP"]==110 and boosted["game"]["hp"]==110)
    shot("05-护盾升级下一局110生命.png")

    report["result"]="PASS" if all(report["checks"].values()) and not report["consoleErrors"] else "PARTIAL"

except Exception as e:
    report["result"]="ERROR";report["exception"]=repr(e);report["stack"]=traceback.format_exc()[-5000:]
finally:
    if ws:
        try:ws.close()
        except:pass
    if proc:
        try:proc.terminate();proc.wait(timeout=2)
        except:
            try:proc.kill()
            except:pass
    kill_profile(profile)
    try:server.shutdown()
    except:pass
    report["durationSeconds"]=round(time.monotonic()-started,2)
    report["finishedAt"]=time.strftime("%Y-%m-%dT%H:%M:%S")
    report["summary"]={"result":report["result"],"checks":report.get("checks",{}),
      "firstSettlement":report.get("firstSettlement",{}).get("game") if isinstance(report.get("firstSettlement"),dict) else None,
      "profileAfterPurchase":report.get("afterCorePurchase",{}).get("profile") if isinstance(report.get("afterCorePurchase"),dict) else None,
      "profileAfterReload":report.get("afterReload",{}).get("profile") if isinstance(report.get("afterReload"),dict) else None,
      "secondRun":report.get("secondRun",{}).get("game") if isinstance(report.get("secondRun"),dict) else None,
      "consoleErrorCount":len(report.get("consoleErrors",[]))}
    target=OUT/"商店存档真实鼠标端到端回归.json"
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"result":report["result"],"durationSeconds":report["durationSeconds"],"summary":report["summary"],"exception":report.get("exception"),"evidence":str(target),"screenshots":report.get("screenshots",[])},ensure_ascii=True),flush=True)
sys.exit(0 if report["result"]=="PASS" else 1)
