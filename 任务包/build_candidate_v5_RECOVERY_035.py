# -*- coding: utf-8 -*-
from pathlib import Path
import subprocess, json, time, re, sys, hashlib

ROOT=Path(r"C:\Users\ide0007\Desktop\deliverable\AI小游戏实战营\AI小游戏制作工程文件\直播炮塔守城")
PROJECT=ROOT/"_assistant-temp"/"候选战场Cocos-V5隔离工程-20261020"
EXE=Path(r"C:\Users\ide0007\.CocosCreator\Creator\3.8.2\CocosCreator.exe")
OUT=PROJECT/"V5-Cocos构建-输出-RECOVERY-035.log"
ERR=PROJECT/"V5-Cocos构建-错误-RECOVERY-035.log"
started=time.time()
panel=PROJECT/"assets"/"resources"/"候选战斗美术-v5-RECOVERY-004"/"UI"/"面板"/"结算面板底板.png"
script=PROJECT/"assets"/"脚本"/"待审战场美术覆盖器.ts"
if not panel.exists(): raise SystemExit("panel runtime PNG missing")
if not script.exists(): raise SystemExit("candidate controller missing")
panel_hash=hashlib.sha256(panel.read_bytes()).hexdigest().upper()
with OUT.open("w",encoding="utf-8",errors="replace") as stdout, ERR.open("w",encoding="utf-8",errors="replace") as stderr:
    result=subprocess.run([str(EXE),"--project",str(PROJECT),"--build","platform=web-mobile;debug=true"],
                          stdout=stdout,stderr=stderr,timeout=180)
out=OUT.read_text(encoding="utf-8",errors="replace")
err=ERR.read_text(encoding="utf-8",errors="replace")
build_dir=PROJECT/"build"/"web-mobile"
pngs=list((PROJECT/"assets"/"resources").rglob("*.png"))
metas=[Path(str(p)+".meta") for p in pngs]
ts_errors=re.findall(r"error TS\d+:[^\r\n]*",out+err)
markers=["结算专用面板底板","结算面板底板","returnToMainMenu","beginFromMainMenu","再次守城"]
marker_hits={m:[] for m in markers}
if build_dir.exists():
    for js in build_dir.rglob("*.js"):
        try: txt=js.read_text(encoding="utf-8",errors="ignore")
        except Exception: continue
        for m in markers:
            if m in txt: marker_hits[m].append(str(js.relative_to(build_dir)))
summary={
 "task":"RECOVERY-035 dedicated UI settlement panel",
 "startedAt":time.strftime("%Y-%m-%dT%H:%M:%S",time.localtime(started)),
 "durationSeconds":round(time.time()-started,2),
 "returnCode":result.returncode,
 "buildSuccessLogged":"build success" in out.lower(),
 "typescriptErrors":ts_errors[:40],
 "errorLogBytes":ERR.stat().st_size,
 "stdoutBytes":OUT.stat().st_size,
 "entryExists":(build_dir/"index.html").exists(),
 "entryMtime":time.strftime("%Y-%m-%dT%H:%M:%S",time.localtime((build_dir/"index.html").stat().st_mtime)) if (build_dir/"index.html").exists() else None,
 "panel":{"exists":panel.exists(),"sha256":panel_hash,"bytes":panel.stat().st_size,"metaExists":Path(str(panel)+".meta").exists()},
 "resourcePngCount":len(pngs),
 "missingMeta":[str(p) for p in metas if not p.exists()],
 "compiledMarkers":marker_hits,
 "lastLogLines":out.splitlines()[-18:],
 "stderrTail":err.splitlines()[-24:]
}
summary["effectiveSuccess"]=(result.returncode in (0,36) and summary["buildSuccessLogged"] and not ts_errors
    and summary["entryExists"] and not summary["missingMeta"] and summary["errorLogBytes"]==0
    and summary["panel"]["metaExists"] and bool(marker_hits["结算专用面板底板"]) and bool(marker_hits["returnToMainMenu"])
    and bool(marker_hits["beginFromMainMenu"]))
report=ROOT/"game-art"/"evidence"/"RECOVERY-035-UI-PANEL-MASTER-A"/"cocos-build-qa.json"
report.parent.mkdir(parents=True,exist_ok=True)
report.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(summary,ensure_ascii=True,indent=2))
sys.exit(0 if summary["effectiveSuccess"] else 1)
