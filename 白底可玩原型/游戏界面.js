/* 独立白底 Canvas 示意渲染；画布逻辑 540×960，透明塔素材后续替换 */
(function(){
  "use strict";
  const E=window.守城规则;
  if(!E){document.body.textContent="缺少规则引擎.js";return;}
  const c=document.getElementById("battle"),g=c.getContext("2d");
  const s=E.make();
  const overview=new URLSearchParams(location.search).get("overview")==="1";
  if(overview)document.documentElement.classList.add("overview");
  let last=performance.now(),runTime=0;
  window.__GAME_STATE=s;
  const f=(x)=>Math.round(x);
  function rect(x,y,w,h,fill,stroke,width=1,r=0){
    g.beginPath();g.roundRect(x,y,w,h,r);g.fillStyle=fill;g.fill();
    if(stroke){g.strokeStyle=stroke;g.lineWidth=width;g.stroke();}
  }
  function text(t,x,y,size=14,color="#273548",align="left",weight="normal"){
    g.font=weight+" "+size+"px 'Microsoft YaHei','Noto Sans SC',sans-serif";
    g.fillStyle=color;g.textAlign=align;g.textBaseline="middle";g.fillText(String(t),x,y);
  }
  function line(points,color="#b4c0d0",width=2,dash=[]){
    g.beginPath();g.moveTo(points[0][0],points[0][1]);
    for(const p of points.slice(1))g.lineTo(p[0],p[1]);
    g.strokeStyle=color;g.lineWidth=width;g.setLineDash(dash);g.stroke();g.setLineDash([]);
  }
  function diamond(x,y,r,fill,stroke){
    g.beginPath();g.moveTo(x,y-r);g.lineTo(x+r,y);g.lineTo(x,y+r);g.lineTo(x-r,y);g.closePath();
    g.fillStyle=fill;g.fill();if(stroke){g.strokeStyle=stroke;g.lineWidth=2;g.stroke();}
  }
  function arrow(x,y,orientation){
    g.save();g.translate(x,y);g.rotate(orientation);line([[0,-6],[0,8]],"#a0acbc",2);
    line([[-5,2],[0,8],[5,2]],"#a0acbc",2);g.restore();
  }
  function hud(){
    rect(0,0,540,109,"#fff","#dde5ef",1);
    text("直播炮塔守城",24,24,19,"#254469","left","bold");
    rect(391,10,130,26,"#f1f6fb","#d7e5f3",1,8);
    text("白底玩法骨架 · 本地模拟",456,23,10,"#53708c","center");
    text("第 "+String(overview?3:s.wave).padStart(2,"0")+" / "+String(s.maxWave).padStart(2,"0")+" 波",24,61,15,"#52667f","left","bold");
    const core=s.coreHP;
    text("守护核心",247,61,15,"#42566b","left","bold");
    rect(334,53,176,18,"#edf1f5","#c5d2dd",1,4);
    rect(335,54,174*(core/100),16,core>25?"#65bddf":"#e36b66",null,1,3);
    text(core+" / 100",421,62,11,core>65?"#1d526b":"#3d3e48","center","bold");
    text("观众炮塔 "+s.towers.length+" 座  ·  击败 "+s.score+" 只",24,93,12,"#60768a");
    text("四面兽潮共同防守",512,93,12,"#60768a","right");
  }
  function map(){
    rect(0,110,540,714,"#fff");
    // 场景层与塔层分离：浅灰方向轨迹，不把草地纹理粘在方块上
    g.strokeStyle="#f0f2f5";g.lineWidth=1;
    for(let x=29;x<=511;x+=32)line([[x,117],[x,812]],"#edf0f4",1);
    for(let y=120;y<=810;y+=32)line([[22,y],[518,y]],"#edf0f4",1);
    // 四路清晰指向唯一水晶
    line([[270,133],[270,401]],"#c5d0dd",18);line([[270,510],[270,795]],"#c5d0dd",18);
    line([[40,455],[213,455]],"#c5d0dd",18);line([[326,455],[500,455]],"#c5d0dd",18);
    line([[270,132],[270,396]],"#f9fafb",14);
    line([[270,514],[270,791]],"#f9fafb",14);
    line([[43,455],[211,455]],"#f9fafb",14);
    line([[330,455],[496,455]],"#f9fafb",14);
    for(const p of [[270,201,0],[270,310,0],[270,696,Math.PI],[270,591,Math.PI],
      [104,455,-Math.PI/2],[172,455,-Math.PI/2],[445,455,Math.PI/2],[385,455,Math.PI/2]])arrow(...p);
    rect(18,116,504,698,"rgba(255,255,255,0)","#d8e0e8",1,12);
    [["北",244,118],["东",489,443],["南",244,790],["西",21,443]].forEach(([d,x,y])=>{
      rect(x,y,30,22,"#f7e9e6","#e4c7bd",1,5);text(d,x+15,y+11,13,"#99594b","center","bold");
    });
    // 目标区域的占地仅是可独立替换的线框，不是炮塔或地板PNG
    g.beginPath();g.arc(270,455,67,0,2*Math.PI);g.fillStyle="#eef8fb";g.fill();
    g.strokeStyle="#b5d6e1";g.lineWidth=2;g.setLineDash([5,5]);g.stroke();g.setLineDash([]);
    coreArt();
  }
  function coreArt(){
    // 中心固定主目标: 蓝晶体+机械支架两个几何部件；不可用作玩家炮塔
    rect(238,486,64,15,"#e2e8ef","#7d94a9",2,2);
    rect(247,472,46,14,"#b5c6d5","#7c94a9",2,3);
    diamond(270,446,34,s.coreHP<=0?"#abb8c2":"#81d0ed","#288dbd");
    diamond(259,439,12,"#ddf6ff","#a0dff5");
    line([[271,413],[277,441],[267,476]],"#eefaff",3);
    if(s.coreHP<=40){line([[277,424],[265,450],[277,460]],"#50788e",2);}
    text("城防能量水晶",270,518,15,"#286785","center","bold");
    text("全体共同守护目标",270,538,12,"#57869b","center");
    if(s.coreHP<=0){rect(205,417,130,77,"rgba(236,74,74,.20)");text("已摧毁",270,456,21,"#b52b2b","center","bold");}
  }
  function tower(t){
    const tp=E.TYPES[t.kind],selected=t.id===s.selectedTowerId;
    if(selected){rect(f(t.x)-23,f(t.y)-24,46,46,"rgba(255,255,255,.02)","#345f96",2,8);}
    // 方块是【塔本体的占位图形】；没有绿色草地、场景背景或假底座
    rect(f(t.x)-15,f(t.y)-15,30,30,tp.color,"#485768",2,4);
    if(t.kind==="tower_repeater"){
      rect(t.x-8,t.y-24,6,13,"#765b35",null,0,1);
      rect(t.x+3,t.y-24,6,13,"#765b35",null,0,1);
      text("速",t.x,t.y+2,13,"#313d4a","center","bold");
    }else if(t.kind==="tower_mortar"){
      rect(t.x-6,t.y-24,12,14,"#9f493e",null,0,2);
      text("炮",t.x,t.y+2,13,"#fff","center","bold");
    }else{
      rect(t.x-8,t.y-22,16,9,"#39758b",null,0,2);
      text("霜",t.x,t.y+2,13,"#233f52","center","bold");
    }
    const label=t.viewer+" Lv"+t.lv;
    rect(t.x-32,t.y+20,64,18,"#fff","#d9e0e8",1,4);
    text(label,t.x,t.y+29,11,"#2d4052","center","bold");
  }
  function beast(e){
    const size=e.boss?21:12;rect(f(e.x)-size/2,f(e.y)-size/2,size,size,e.boss?"#9b5369":"#b36b62","#654649",1,2);
    if(e.boss)text("B",e.x,e.y+1,11,"white","center","bold");
    rect(e.x-size/2-3,e.y-size/2-9,size+6,4,"#f6d4d4",null,0,1);
    rect(e.x-size/2-3,e.y-size/2-9,(size+6)*Math.max(0,e.hp/e.maxHP),4,"#cb5b64",null,0,1);
  }
  function previewOrcs(){
    const list=[
      [270,160,false],[267,224,false],[289,270,false],[270,728,false],[266,674,false],[253,610,false],
      [71,455,false],[139,450,false],[471,454,true],[415,470,false],
      [65,220,false],[470,740,false]
    ];
    for(const p of list)beast({x:p[0],y:p[1],boss:p[2],hp:100,maxHP:100});
    // 只在规划态展示示意弹道，开始运行后使用真正模拟的弹丸
    line([[176,300],[251,269]],"#d5a74b",3,[4,4]);
    line([[360,299],[413,383]],"#d87967",3,[4,4]);
    line([[431,384],[457,438]],"#7bc7e7",3,[4,4]);
  }
  function info(){
    rect(0,825,540,135,"#fff","#dce4ec",1);
    rect(18,839,504,28,"#f5f8fb","#dfe9f2",1,6);
    if(overview||s.status==="ready"){
      text("布局说明：四方向刷怪 → 九座观众炮塔 → 守护中央水晶",270,853,12,"#45647f","center","bold");
    }else{
      text(s.eventLog[0]||"防守进行中",270,853,12,"#47637e","center","bold");
    }
    text("炮塔阵营",20,892,13,"#374e63","left","bold");
    const legend=[
      {x:101,label:"速射",c:"#e8b044"},{x:213,label:"重炮",c:"#e57463"},{x:326,label:"寒霜",c:"#79c4de"}
    ];
    for(const a of legend){rect(a.x,882,18,18,a.c,"#718496",1,3);text(a.label,a.x+24,891,12,"#43596d");}
    const tower=s.towers.find(t=>t.id===s.selectedTowerId);
    text(tower?"当前选中："+tower.viewer+" · "+E.TYPES[tower.kind].name+" Lv"+tower.lv:"点击塔位选择",20,919,12,"#56687a");
    text("本地模拟 / 无直播接入 / 暂用白底占位方块",20,945,11,"#91a0ad");
  }
  function render(){
    g.clearRect(0,0,540,960);
    g.fillStyle="#fff";g.fillRect(0,0,540,960);
    hud();map();
    if(overview||s.status==="ready")previewOrcs();
    else for(const e of s.enemies)beast(e);
    for(const t of s.towers)tower(t);
    if(!overview){
      for(const p of s.projectiles){g.fillStyle=p.kind==="tower_frost"?"#56b5db":p.kind==="tower_mortar"?"#da6e5c":"#b58b36";g.fillRect(p.x-3,p.y-3,6,6);}
      for(const p of s.particles)text(p.text,p.x,p.y-12,14,p.color,"center","bold");
    }
    info();
    if(!overview&&["won","lost","paused"].includes(s.status)){
      rect(102,346,336,55,"rgba(255,255,255,.94)","#9eb3c8",2,10);
      const label=s.status==="won"?"成功守住核心！":s.status==="lost"?"核心已失守":"游戏已暂停";
      text(label,270,373,24,s.status==="lost"?"#aa4545":"#2d718e","center","bold");
    }
  }
  function setBtn(){const b=document.getElementById("start");b.textContent=s.status==="ready"?"开始战斗":s.status==="lost"||s.status==="won"?"重新开局":"继续战斗";}
  function clickStart(){if(s.status==="won"||s.status==="lost")E.reset(s);E.start(s);setBtn();render();}
  document.getElementById("start").onclick=clickStart;
  document.getElementById("pause").onclick=()=>{E.pause(s);render();};
  document.getElementById("upgrade").onclick=()=>{E.upgrade(s);render();};
  document.getElementById("reset").onclick=()=>{E.reset(s);setBtn();render();};
  document.getElementById("join").onclick=()=>{const name=document.getElementById("viewer").value;E.join(s,name);render();};
  document.getElementById("leave").onclick=()=>{E.leave(s);render();};
  c.addEventListener("pointerdown",ev=>{
    const b=c.getBoundingClientRect(),x=(ev.clientX-b.left)*540/b.width,y=(ev.clientY-b.top)*960/b.height;
    let best=null,distance=28;
    for(const t of s.towers){const d=Math.hypot(t.x-x,t.y-y);if(d<distance){best=t;distance=d;}}
    if(best){E.select(s,best.id);render();}
  });
  document.addEventListener("keydown",e=>{
    if(e.target?.tagName==="INPUT")return;
    if(e.key===" "){e.preventDefault();if(s.status==="ready")clickStart();else{E.pause(s);render();}}
    if(e.key.toLowerCase()==="r"){E.reset(s);setBtn();render();}
    if(e.key.toLowerCase()==="u"){E.upgrade(s);render();}
  });
  function loop(now){
    const dt=Math.min((now-last)/1000,.05);last=now;runTime+=dt;
    if(!overview)E.step(s,dt);
    if(s.status!=="ready"||!window.__APP_READY)render();
    requestAnimationFrame(loop);
  }
  render();window.__APP_READY=true;document.documentElement.dataset.appReady='yes';document.documentElement.dataset.appMode=overview?'overview':'playable';window.__APP_RENDER=render;
  window.__TEST_HOOKS={state:s,engine:E,render,clickStart};
  if(!overview)requestAnimationFrame(loop);
})();
