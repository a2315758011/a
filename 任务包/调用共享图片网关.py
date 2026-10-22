# -*- coding: utf-8 -*-
"""仅向工作站已存在的Generation Gateway提交已固化指纹的唯一任务。
不重试未知已提交请求；只允许明确失败前重配，保护账号配额。
"""
import argparse, json, pathlib, urllib.request, urllib.error
ROOT=pathlib.Path(__file__).resolve().parent.parent
RUNTIME=pathlib.Path.home()/"Desktop"/"deliverable"/".infra"/"GENERATION_GATEWAY_RUNTIME.json"
LEDGER=ROOT/"任务包"/"玩法总览图生成任务-v0.3.json"

def fetch(method,uri,body=None):
    rt=json.loads(RUNTIME.read_text(encoding="utf-8"))
    token=pathlib.Path(rt["tokenFile"]).read_text(encoding="utf-8").strip()
    headers={"X-Moyin-Gateway-Token":token}
    if body is not None:headers["Content-Type"]="application/json; charset=utf-8"
    b=json.dumps(body,ensure_ascii=False).encode("utf-8") if body is not None else None
    req=urllib.request.Request(rt["baseUrl"]+uri,data=b,method=method,headers=headers)
    try:
        with urllib.request.urlopen(req,timeout=24) as r:
            raw=r.read().decode("utf-8","replace")
            return {"http":r.status,"body":json.loads(raw) if raw else None}
    except urllib.error.HTTPError as e:
        raw=e.read().decode("utf-8","replace")
        try:err=json.loads(raw)
        except:err=raw[:1000]
        return {"http":e.code,"body":err}
    except Exception as e:
        return {"http":None,"uncertain":True,"error":str(e)}
def save(ledger):
    LEDGER.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--submit",action="store_true")
    p.add_argument("--inspect",action="store_true")
    p.add_argument("--probe",action="store_true")
    a=p.parse_args()
    ledger=json.loads(LEDGER.read_text(encoding="utf-8"))
    if a.probe:
        # 故意缺prompt/idempotencyKey，验证参数；绝不造成成功收费生成。
        answer=fetch("POST","/v1/jobs",{"kind":"INVALID","feature":"INVALID"})
        print(json.dumps(answer,ensure_ascii=False,indent=2));return
    jobs=fetch("GET","/v1/jobs")
    print("CURRENT_JOBS:",json.dumps(jobs,ensure_ascii=False)[:1000])
    if not a.submit:return
    if jobs.get("uncertain"):
        print("BLOCKED: cannot query existing jobs");return
    if ledger["jobStatus"] not in ["NOT_SUBMITTED","REJECTED"]:
        print("BLOCKED: job status already recorded",ledger["jobStatus"]);return
    oldjobs=(jobs.get("body") or {}).get("jobs",[])
    for job in oldjobs:
        if job.get("idempotencyKey")==ledger["idempotencyKey"] or (job.get("sourceProjectId")==ledger["sourceProjectId"] and job.get("sourceTaskId")==ledger["sourceTaskId"]):
            print("EXISTING_JOB_DO_NOT_RESUBMIT",job.get("id"),job.get("status"));ledger["jobStatus"]="EXISTING_FOUND";ledger["jobId"]=job.get("id");save(ledger);return
    body={"kind":"image","feature":"freedom_image","prompt":ledger["prompt"],"providerId":"web-pool:freedom_image","transport":"web","sourceProjectId":ledger["sourceProjectId"],"sourceTaskId":ledger["sourceTaskId"],"idempotencyKey":ledger["idempotencyKey"],"outputDir":str(ROOT)}
    response=fetch("POST","/v1/jobs",body)
    print("SUBMIT_RESULT:",json.dumps(response,ensure_ascii=False)[:3000])
    if response.get("uncertain"):
        ledger["jobStatus"]="SUBMISSION_UNCERTAIN_DO_NOT_RESUBMIT"
    elif response["http"] in (200,201,202):
        ledger["jobStatus"]="SUBMITTED"
        b=response.get("body") or {}
        ledger["jobId"]=b.get("jobId") or (b.get("job") or {}).get("id") or b.get("id")
        ledger["providerResponse"]=b
    else:
        ledger["jobStatus"]="REJECTED"
        ledger["rejectionHTTP"]=response["http"]
        ledger["rejectionBody"]=response.get("body")
    save(ledger)

if __name__=="__main__":main()
