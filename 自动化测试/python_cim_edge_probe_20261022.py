# -*- coding: utf-8 -*-
from pathlib import Path
import subprocess,tempfile,time,requests,json
ROOT=Path(r"C:\Users\ide0007\Desktop\deliverable\AI小游戏实战营\AI小游戏制作工程文件\直播炮塔守城")
launcher=ROOT/"自动化测试"/"edge_cdp_launcher_20261022.ps1"
profile=tempfile.mkdtemp(prefix="edge-cim-probe-")
port=9250
p=subprocess.run(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-File",str(launcher),str(port),profile],capture_output=True,text=True,encoding="utf8",errors="replace",timeout=10)
out={"launcherExit":p.returncode,"stdout":p.stdout.strip(),"stderr":p.stderr.strip(),"profile":profile,"port":port}
for i in range(30):
    try:
        r=requests.get(f"http://127.0.0.1:{port}/json/list",timeout=.2)
        if r.ok:
            out["httpStatus"]=r.status_code; out["targets"]=len(r.json()); break
    except Exception as e:
        out["lastHttpError"]=repr(e)
    time.sleep(.1)
ps=subprocess.run(["powershell","-NoProfile","-Command",f"Get-CimInstance Win32_Process | Where-Object {{$_.Name -eq 'msedge.exe' -and $_.CommandLine -like '*{profile.replace(chr(39),chr(39)*2)}*'}} | Select-Object ProcessId,ParentProcessId,Name,CommandLine | ConvertTo-Json -Depth 3 -Compress"],capture_output=True,text=True,encoding="utf8",errors="replace",timeout=5)
out["processes"]=ps.stdout.strip()
subprocess.run(["powershell","-NoProfile","-Command",f"Get-CimInstance Win32_Process | Where-Object {{$_.Name -eq 'msedge.exe' -and $_.CommandLine -like '*{profile.replace(chr(39),chr(39)*2)}*'}} | ForEach-Object {{Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}}"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5)
print(json.dumps(out,ensure_ascii=False,indent=2))
