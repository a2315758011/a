# -*- coding: utf-8 -*-
"""One-click incremental official Cocos build + fast runtime QA. Never substitutes HTML for Cocos."""
from __future__ import annotations
from pathlib import Path
import argparse, hashlib, json, subprocess, sys, time, traceback
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/"CocosCreator工程"
TEMP=ROOT/"自动化测试"
OUT=ROOT/"验收证据"/"WHOLE-GAME-FAST-REGRESSION-20261022"
OUT.mkdir(parents=True,exist_ok=True)
CACHE=OUT/"build-cache.json"
REPORT=OUT/"最后一次高速回归.json"
SCENE="db://assets/场景/守城主场景.scene"
BUILD=PROJECT/"build"/"web-mobile"

def current_fingerprint():
    roots=[PROJECT/"assets", PROJECT/"settings"/"v2"/"packages", PROJECT/"profiles"/"v2"/"packages"]
    files=[p for base in roots if base.exists() for p in base.rglob("*") if p.is_file()]
    files.extend([PROJECT/"package.json"])
    digest=hashlib.sha256()
    for p in sorted(files):
        if not p.exists():continue
        digest.update(p.relative_to(PROJECT).as_posix().encode("utf8"))
        with p.open("rb") as stream:
            while chunk:=stream.read(1024*1024):digest.update(chunk)
    return digest.hexdigest(),len(files)

def bundle_current():
    settings=BUILD/"src"/"settings.json"
    main=BUILD/"assets"/"main"/"config.json"
    if not all(p.is_file() for p in [BUILD/"index.html",settings,main]): return False
    try:return json.loads(settings.read_text("utf8"))["launch"]["launchScene"]==SCENE
    except Exception:return False

def run(argv,limit):
    start=time.perf_counter()
    r=subprocess.run(argv,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                     text=True,encoding="utf8",errors="replace",timeout=limit)
    return {
      "command":[str(x) for x in argv], "exitCode":r.returncode,
      "seconds":round(time.perf_counter()-start,3),
      "stdoutTail":r.stdout[-3000:], "stderrTail":r.stderr[-1000:],
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--all",action="store_true",help="include main menu, shop, live event and persistence checks")
    parser.add_argument("--rebuild",action="store_true",help="force a real Cocos CLI build")
    args=parser.parse_args()
    start=time.perf_counter()
    fingerprint,file_count=current_fingerprint()
    old=json.loads(CACHE.read_text("utf8")) if CACHE.is_file() else {}
    must_build=args.rebuild or old.get("sourceFingerprint")!=fingerprint or not bundle_current()
    report={"task":"WHOLE-GAME-FAST-REGRESSION-20261022",
            "timestamp":datetime.now(timezone.utc).isoformat(),
            "sourceFingerprint":fingerprint,"sourceFiles":file_count,
            "reusedBuild":not must_build,"build":None,"tests":[],"result":"IN_PROGRESS"}
    try:
        if must_build:
            report["build"]=run(["node",str(TEMP/"build-formal-integration-20261022.cjs")],210)
            builder_report=ROOT/"验收证据"/"WHOLE-GAME-COCOS-FORMAL-INTEGRATION-BUILD-20261022.json"
            if report["build"]["exitCode"]!=0 or not builder_report.is_file():
                raise RuntimeError("Cocos build failed, check report")
            builder=json.loads(builder_report.read_text("utf8"))
            if builder.get("status")!="PASS" or not bundle_current():
                raise RuntimeError("Cocos artifact/build launch scene not verified")
            # Creator can update imported .meta files during the build. Cache the
            # post-import fingerprint, not the stale pre-build value, to avoid a
            # redundant full build on the very next unchanged run.
            post_fingerprint,post_file_count=current_fingerprint()
            report["sourceFingerprintAfterBuild"]=post_fingerprint
            report["sourceFilesAfterBuild"]=post_file_count
            CACHE.write_text(json.dumps({"sourceFingerprint":post_fingerprint,"sourceFiles":post_file_count,
                                         "time":report["timestamp"],"buildEvidence":str(builder_report)},
                                         ensure_ascii=False,indent=2)+"\n","utf8")
        required=["qa_formal_fast_combat_20261022.py","qa_formal_platform_socket_fallback_20261022.py"]
        if args.all:required+=["qa_formal_shop_20261022.py","qa_formal_shop_effects_20261022.py",
                               "qa_formal_liveplay_20261022.py"]
        for script in required:
            item=run([sys.executable,str(TEMP/script)],70)
            item["script"]=script
            report["tests"].append(item)
            if item["exitCode"]!=0:raise RuntimeError(f"QA failed: {script}")
        report["result"]="PASS"
    except Exception as e:
        report["result"]="FAIL"
        report["error"]=str(e)
        report["stack"]=traceback.format_exc()[-1000:]
    report["totalSeconds"]=round(time.perf_counter()-start,3)
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n","utf8")
    run_report=OUT/("扩展回归.json" if args.all else "快速回归.json")
    run_report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n","utf8")
    print(json.dumps({"result":report["result"],"buildCacheHit":report["reusedBuild"],
       "buildSeconds":report["build"]["seconds"] if report["build"] else 0,
       "tests":[{"script":x["script"],"seconds":x["seconds"],"ok":x["exitCode"]==0} for x in report["tests"]],
       "totalSeconds":report["totalSeconds"],"evidence":str(run_report),"latestEvidence":str(REPORT),"error":report.get("error")},
       ensure_ascii=False))
    return 0 if report["result"]=="PASS" else 1
if __name__=="__main__":raise SystemExit(main())
