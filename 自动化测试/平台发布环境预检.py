# -*- coding: utf-8 -*-
from pathlib import Path
import json, os, shutil, subprocess, time

ROOT=Path(__file__).resolve().parents[1]
COCOS=ROOT/"CocosCreator工程"
USER=Path.home()

def run(args, timeout=8):
    try:
        p=subprocess.run(args,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=timeout)
        return {"code":p.returncode,"stdout":p.stdout.strip(),"stderr":p.stderr.strip()}
    except Exception as e:
        return {"code":None,"stdout":"","stderr":repr(e)}

def count_files(p):
    return sum(1 for x in p.rglob("*") if x.is_file()) if p.exists() else 0

def first_existing(paths):
    for p in paths:
        p=Path(p)
        if p.exists(): return str(p)
    return None

creator=first_existing([USER/".CocosCreator/Creator/3.8.2/CocosCreator.exe"])
java_home=os.environ.get("JAVA_HOME")
java=first_existing([
    Path(java_home)/"bin/java.exe" if java_home else USER/"__missing__",
    USER/".jdks/jdk-17.0.20.1+1/bin/java.exe",
])
sdk=first_existing([
    Path(os.environ["ANDROID_SDK_ROOT"]) if os.environ.get("ANDROID_SDK_ROOT") else USER/"__missing__",
    Path(os.environ["ANDROID_HOME"]) if os.environ.get("ANDROID_HOME") else USER/"__missing__",
    USER/"AppData/Local/Android/Sdk",
    USER/"Android/Sdk",
])
sdk_components={"cmdlineTools":False,"platforms":[],"buildTools":[],"licensesPresent":False}
if sdk:
    base=Path(sdk)
    managers=list((base/"cmdline-tools").glob("*/bin/sdkmanager.bat")) if (base/"cmdline-tools").is_dir() else []
    sdk_components["cmdlineTools"]=bool(managers or (base/"tools/bin/sdkmanager.bat").is_file())
    sdk_components["platforms"]=sorted(x.name for x in (base/"platforms").iterdir() if x.is_dir() and (x/"android.jar").is_file()) if (base/"platforms").is_dir() else []
    sdk_components["buildTools"]=sorted(x.name for x in (base/"build-tools").iterdir() if x.is_dir() and (x/"aapt.exe").is_file() and (x/"zipalign.exe").is_file()) if (base/"build-tools").is_dir() else []
    sdk_components["licensesPresent"]=(base/"licenses"/"android-sdk-license").is_file()
ndk=None
if sdk:
    base=Path(sdk)
    candidates=[]
    if os.environ.get("NDK_ROOT"): candidates.append(Path(os.environ["NDK_ROOT"]))
    if os.environ.get("NDK_HOME"): candidates.append(Path(os.environ["NDK_HOME"]))
    ndks=base/"ndk"
    if ndks.exists(): candidates.extend(sorted([x for x in ndks.iterdir() if x.is_dir()],reverse=True))
    candidates.append(base/"ndk-bundle")
    ndk=first_existing(candidates)

adb=first_existing([
    Path(shutil.which("adb")) if shutil.which("adb") else USER/"__missing__",
    Path(r"C:\platform-tools\adb.exe"),
])
devices=[]
selected=None
if adb:
    d=run([adb,"devices","-l"])
    for line in d["stdout"].splitlines()[1:]:
        parts=line.strip().split()
        if len(parts)>=2:
            devices.append({"serial":parts[0],"state":parts[1],"raw":line.strip()})
            if parts[1]=="device" and selected is None: selected=parts[0]

def adb_shell(*parts):
    if not selected:return None
    q=run([adb,"-s",selected,"shell",*parts])
    return q["stdout"] if q["code"]==0 else None

builds={}
for name in ("web-mobile","wechatgame","bytedance-mini-game","android"):
    p=COCOS/"build"/name
    builds[name]={"exists":p.exists(),"files":count_files(p),"path":str(p)}

wechat_tool=first_existing([
    USER/"AppData/Local/微信开发者工具",
    USER/"AppData/Local/Programs/微信开发者工具",
    USER/"AppData/Roaming/Tencent/微信开发者工具",
])
douyin_tool=first_existing([
    USER/"AppData/Local/抖音开发者工具",
    USER/"AppData/Local/Programs/抖音开发者工具",
    USER/"AppData/Roaming/抖音开发者工具",
])

result={
    "checkedAt":time.strftime("%Y-%m-%dT%H:%M:%S"),
    "projectRoot":str(ROOT),
    "formalCocosProject":COCOS.exists(),
    "creatorPath":creator,
    "javaHome":java_home,
    "javaPath":java,
    "androidSdkPath":sdk,
    "androidSdkComponents":sdk_components,
    "androidNdkPath":ndk,
    "adbPath":adb,
    "devices":devices,
    "selectedDevice":{
        "serial":selected,
        "api":adb_shell("getprop","ro.build.version.sdk"),
        "abi":adb_shell("getprop","ro.product.cpu.abi"),
        "model":adb_shell("getprop","ro.product.model"),
        "size":adb_shell("wm","size"),
        "density":adb_shell("wm","density"),
    } if selected else None,
    "builds":builds,
    "wechatDeveloperToolUserPath":wechat_tool,
    "douyinDeveloperToolUserPath":douyin_tool,
}
result["gates"]={
    "androidDeviceConnected":bool(selected),
    "androidJdkReady":bool(java),
    "androidSdkReady":bool(sdk_components["platforms"] and sdk_components["buildTools"]),
    "androidNdkReady":bool(ndk and (Path(ndk)/"ndk-build.cmd").is_file() and (Path(ndk)/"source.properties").is_file()),
    "androidBuildArtifact":builds["android"]["exists"] and builds["android"]["files"]>5,
    "wechatBuildArtifact":builds["wechatgame"]["exists"] and builds["wechatgame"]["files"]>0,
    "douyinBuildArtifact":builds["bytedance-mini-game"]["exists"] and builds["bytedance-mini-game"]["files"]>0,
    "wechatDevToolsUserInstallDetected":bool(wechat_tool),
    "douyinDevToolsUserInstallDetected":bool(douyin_tool),
}
print(json.dumps(result,ensure_ascii=False,indent=2))
