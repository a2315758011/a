# -*- coding:utf-8 -*-
"""只能在旧任务明确未提交时换图像可用账号。禁止未知态自动重试。"""
import sys, json, pathlib, importlib.util
root=pathlib.Path(__file__).resolve().parent.parent
old=pathlib.Path(__file__).resolve().parent/"调用共享图片网关.py"
spec=importlib.util.spec_from_file_location("shared_gateway",old)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
led=mod.LEDGER
job=json.loads(led.read_text(encoding="utf-8"))
plan=job.get("retryPlan",{})
if plan.get("status") != "PREPARED_NOT_SUBMITTED":
    print("BLOCKED_NOT_PREPARED",plan.get("status"));sys.exit(2)
first=mod.fetch("GET","/v1/jobs/"+job["originalJobResult"]["jobId"])
item=(first.get("body") or {}).get("job") or {}
err=item.get("error") or {}
if first.get("http")!=200 or item.get("status")!="failed" or err.get("submitted") is not False or err.get("submitLocked") is not False:
    print("BLOCKED_ORIGINAL_SUBMISSION_NOT_PROVEN_FALSE",first.get("http"),item.get("status"),err.get("submitted"));sys.exit(2)
jobs=mod.fetch("GET","/v1/jobs")
if jobs.get("http")!=200:
    print("BLOCKED_CANNOT_INSPECT_JOBS");sys.exit(2)
for item in ((jobs.get("body") or {}).get("jobs") or []):
    if item.get("sourceTaskId")==job["sourceTaskId"] and item.get("id")!=job["originalJobResult"]["jobId"]:
        print("BLOCKED_EXISTING_SECOND_JOB",item.get("id"));sys.exit(2)
req={"kind":"image","feature":"freedom_image","prompt":job["prompt"],"transport":"web",
     "providerId":plan["requestedProviderId"],"accountId":plan["requestedAccountId"],"pool":False,
     "sourceProjectId":job["sourceProjectId"],"sourceTaskId":job["sourceTaskId"],
     "outputDir":str(root),"idempotencyKey":plan["idempotencyKey"],"aspectRatio":"9:16"}
r=mod.fetch("POST","/v1/jobs",req)
print("RETRY:",json.dumps(r,ensure_ascii=False)[:2600])
if r.get("uncertain"):
    plan["status"]="SUBMISSION_UNKNOWN_DO_NOT_REPEAT"
elif r.get("http") in (200,201,202):
    plan["status"]="SUBMITTED"
    data=r.get("body") or {}
    plan["jobId"]=data.get("jobId") or (data.get("job") or {}).get("id") or data.get("id")
else:
    plan["status"]="REJECTED_PRE_OR_VALIDATION"
    plan["lastError"]={"http":r.get("http"),"body":r.get("body")}
job["retryPlan"]=plan
mod.save(job)
