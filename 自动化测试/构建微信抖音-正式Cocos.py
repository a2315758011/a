# -*- coding: utf-8 -*-
"""Incremental Cocos Creator 3.8.2 builds for WeChat and Douyin mini-games."""
from pathlib import Path
import hashlib,json,subprocess,time,re,sys,os
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/"CocosCreator工程"
EDITOR=Path.home()/".CocosCreator"/"Creator"/"3.8.2"/"CocosCreator.exe"
OUT=ROOT/"验收证据"/"COCOS-MINI-BUILD-20261022"
OUT.mkdir(parents=True,exist_ok=True)
SCENE="d640f6d0-03c5-4a07-a81a-7fbe6dad1af4"
TARGETS=[
 {"id":"wechatgame","label":"微信小游戏","platform":"wechatgame","required":["game.js","game.json","application.js"]},
 {"id":"bytedance-mini-game","label":"抖音小游戏","platform":"bytedance-mini-game","required":["game.js","game.json","application.js"]},
]
def fingerprint():
 h=hashlib.sha256();count=0
 roots=[PROJECT/"assets",PROJECT/"settings"/"v2"/"packages",PROJECT/"profiles"/"v2"/"packages"]
 files=[p for d in roots if d.exists() for p in d.rglob("*") if p.is_file()]
 files += [PROJECT/"package.json"]
 for p in sorted(set(files)):
  if not p.is_file():continue
  count+=1;h.update(p.relative_to(PROJECT).as_posix().encode("utf-8"))
  with p.open("rb") as f:
   while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest(),count
def output_valid(t):
 d=PROJECT/"build"/t["id"]
 if not all((d/n).is_file() for n in t["required"]):return False,0
 count=sum(1 for p in d.rglob("*") if p.is_file())
 if count<100:return False,count
 if not (d/"assets").is_dir():return False,count
 return True,count
def latest_source_mtime():
 roots=[PROJECT/"assets",PROJECT/"settings"/"v2"/"packages",PROJECT/"profiles"/"v2"/"packages"]
 files=[p for d in roots if d.exists() for p in d.rglob("*") if p.is_file()]
 files += [PROJECT/"package.json"]
 return max((p.stat().st_mtime_ns for p in files if p.is_file()),default=0)
def output_fresh(t):
 d=PROJECT/"build"/t["id"]
 files=[p for p in d.rglob("*") if p.is_file()] if d.exists() else []
 return bool(files) and max(p.stat().st_mtime_ns for p in files)>=latest_source_mtime()
def build(t,force,fp,count):
 out=PROJECT/"build"/t["id"]
 cache=OUT/(t["id"]+".cache.json")
 old={}
 if cache.is_file():
  try:old=json.loads(cache.read_text("utf-8"))
  except:pass
 valid,n=output_valid(t)
 fresh=output_fresh(t)
 if not force and valid and fresh and old.get("sourceFingerprint")==fp:
  return {"platform":t["platform"],"label":t["label"],"result":"PASS_CACHED","seconds":0,
          "fileCount":n,"fingerprint":fp,"fresh":True,"output":str(out)}
 started=time.perf_counter()
 args=[str(EDITOR),"--project",str(PROJECT),"--build",
       f"platform={t['platform']};debug=true;startScene={SCENE}"]
 try:
  p=subprocess.run(args,cwd=PROJECT,capture_output=True,text=True,encoding="utf-8",
                   errors="replace",timeout=240)
  stdout=p.stdout or "";stderr=p.stderr or "";code=p.returncode
 except Exception as e:
  stdout="";stderr=repr(e);code=-999
 secs=round(time.perf_counter()-started,3)
 (OUT/(t["id"]+".stdout.log")).write_text(stdout,"utf-8")
 (OUT/(t["id"]+".stderr.log")).write_text(stderr,"utf-8")
 valid,n=output_valid(t)
 ts_errors=re.findall(r"(?:error TS\d+|typescript[^\r\n]*(?:error|failed))",(stdout+"\n"+stderr),re.I)
 success=bool(re.search(r"build success",stdout,re.I))
 ok=code in (0,36) and success and valid and not ts_errors
 result={"platform":t["platform"],"label":t["label"],"exitCode":code,
         "result":"PASS" if ok else "FAIL","seconds":secs,"buildSuccessLogged":success,
         "artifactValid":valid,"fileCount":n,"typescriptErrors":ts_errors,
         "stdoutTail":stdout[-1800:],"stderrTail":stderr[-1000:],
         "fingerprint":fp,"fresh":output_fresh(t),"output":str(out)}
 if ok:cache.write_text(json.dumps({"sourceFingerprint":fp,"time":datetime.now(timezone.utc).isoformat(),
                                    "fileCount":n,"output":str(out)},ensure_ascii=False,indent=2)+"\n","utf-8")
 return result
def main():
 force="--rebuild" in sys.argv
 fp,count=fingerprint();start=time.perf_counter()
 report={"task":"COCOS-WECHAT-DOUYIN-MINI-BUILD-20261022",
         "timestamp":datetime.now(timezone.utc).isoformat(),"sourceFingerprint":fp,
         "sourceFiles":count,"targets":[],"result":"IN_PROGRESS"}
 for t in TARGETS:
  r=build(t,force,fp,count);report["targets"].append(r)
  if r["result"]=="FAIL":report["result"]="FAIL";break
 else:report["result"]="PASS"
 # Creator may rewrite .meta files during target import. Persist the final
 # post-import source fingerprint for both target caches to avoid repeat builds.
 post_fp,post_count=fingerprint()
 report["sourceFingerprintAfterBuild"]=post_fp
 report["sourceFilesAfterBuild"]=post_count
 if report["result"]=="PASS":
  for t in TARGETS:
   valid,n=output_valid(t)
   if valid:
    cache=OUT/(t["id"]+".cache.json")
    cache.write_text(json.dumps({"sourceFingerprint":post_fp,"time":datetime.now(timezone.utc).isoformat(),
      "fileCount":n,"output":str(PROJECT/"build"/t["id"])},ensure_ascii=False,indent=2)+"\n","utf-8")
 report["totalSeconds"]=round(time.perf_counter()-start,3)
 dest=OUT/"微信抖音正式构建验收.json"
 dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n","utf-8")
 print(json.dumps({"result":report["result"],"totalSeconds":report["totalSeconds"],
                   "targets":[{"platform":x["platform"],"result":x["result"],"seconds":x["seconds"],"fileCount":x["fileCount"]} for x in report["targets"]],
                   "evidence":str(dest),"error":[x for x in report["targets"] if x["result"]=="FAIL"]},ensure_ascii=False))
 return 0 if report["result"]=="PASS" else 1
if __name__=="__main__":raise SystemExit(main())
