param([int]$Port,[string]$Profile)
$ErrorActionPreference='Stop'
$edge='C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
$args=@(
  '--headless=new',
  ('--remote-debugging-port='+$Port),
  '--remote-allow-origins=*',
  '--no-first-run',
  '--no-default-browser-check',
  '--disable-features=msEdgeStartupBoost',
  '--disable-background-timer-throttling',
  '--disable-renderer-backgrounding',
  '--disable-backgrounding-occluded-windows',
  '--enable-webgl',
  '--enable-unsafe-swiftshader',
  '--use-angle=swiftshader',
  '--disable-gpu-sandbox',
  ('--user-data-dir='+$Profile)
)
$quoted=$args | ForEach-Object { '"' + ($_ -replace '"','\"') + '"' }
$cmd='"'+$edge+'" '+($quoted -join ' ')
$r=Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine=$cmd}
if($r.ReturnValue -ne 0){ throw ('Win32_Process.Create failed: '+$r.ReturnValue) }
[pscustomobject]@{ok=$true;pid=$r.ProcessId;port=$Port;profile=$Profile;commandLine=$cmd}|ConvertTo-Json -Compress
