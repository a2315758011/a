const cp=require('child_process');
const edge='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const port=Number(process.argv[2]);
const profile=process.argv[3];
if(!port||!profile){console.error('usage: node edge_cdp_launcher_20261022.js <port> <profile> [keep]');process.exit(2);}
const args=['--headless=new','--remote-debugging-port='+port,'--remote-allow-origins=*','--no-first-run','--no-default-browser-check','--disable-features=msEdgeStartupBoost','--disable-background-timer-throttling','--disable-renderer-backgrounding','--disable-backgrounding-occluded-windows','--enable-webgl','--enable-unsafe-swiftshader','--use-angle=swiftshader','--disable-gpu-sandbox','--user-data-dir='+profile];
const p=cp.spawn(edge,args,{detached:true,stdio:'ignore',windowsHide:true});
p.unref();
console.log(JSON.stringify({ok:true,pid:p.pid,port,profile}));
if(process.argv[4]==='keep')setInterval(()=>{},1000);
