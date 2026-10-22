# -*- coding: utf-8 -*-
from pathlib import Path
import subprocess,tempfile,time,requests,json,os
ROOT=Path(r"C:\Users\ide0007\Desktop\deliverable\AI小游戏实战营\AI小游戏制作工程文件\直播炮塔守城")
helper=ROOT/"自动化测试"/"edge_cdp_launcher_20261022.js"
profile=tempfile.mkdtemp(prefix="edge-python-probe-")
port=9250
p=subprocess.Popen(["node",str(helper),str(port),profile,"keep"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding="utf8",errors="replace",creationflags=0x01000000)
out={"pid":p.pid,"profile":profile,"helper":str(helper)}
time.sleep(1)
out["nodePoll"]=p.poll()
try:
    line=p.stdout.readline().strip()
    out["nodeStdout"]=line
except Exception as e: out["nodeStdoutError"]=repr(e)
try:
    r=requests.get(f"http://127.0.0.1:{port}/json/list",timeout=2)
    out["httpStatus"]=r.status_code
    out["body"]=r.text[:1000]
except Exception as e: out["httpError"]=repr(e)
try:
    ps=subprocess.run(["powershell","-NoProfile","-Command",f"Get-CimInstance Win32_Process | Where-Object {{$_.CommandLine -like '*{profile.replace(chr(39),chr(39)*2)}*'}} | Select-Object ProcessId,ParentProcessId,Name,CommandLine | ConvertTo-Json -Depth 3 -Compress"],capture_output=True,text=True,encoding="utf8",errors="replace",timeout=5)
    out["processes"]=ps.stdout.strip()
except Exception as e: out["psError"]=repr(e)
try:p.terminate()
except:pass
print(json.dumps(out,ensure_ascii=False,indent=2))
