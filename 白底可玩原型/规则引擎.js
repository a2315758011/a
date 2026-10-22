/* 白底守城骨架 - 可离线复用的确定性规则内核（不含平台API和美术贴图） */
(function (g, factory) {
  const api = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  g.守城规则 = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  "use strict";
  const W=540,H=960,CORE={x:270,y:455},R=26;
  const TYPES={
    tower_repeater:{name:"连珠速射",label:"速射",color:"#e8b044",range:124,interval:0.43,damage:12,bulletSpeed:350,area:0,slow:0},
    tower_mortar:{name:"熔芯重炮",label:"重炮",color:"#e57463",range:144,interval:1.12,damage:29,bulletSpeed:245,area:38,slow:0},
    tower_frost:{name:"寒霜喷射",label:"寒霜",color:"#79c4de",range:116,interval:0.77,damage:7,bulletSpeed:310,area:0,slow:1.15}
  };
  const START=[
    [176,300,"tower_repeater","阿风",3],
    [360,299,"tower_mortar","小虎",2],
    [431,384,"tower_frost","阿宁",1],
    [395,552,"tower_repeater","青禾",1],
    [325,650,"tower_mortar","北北",4],
    [197,643,"tower_frost","小舟",1],
    [102,545,"tower_repeater","橘子",2],
    [98,387,"tower_mortar","禾苗",3],
    [274,250,"tower_frost","花生",1]
  ];
  const EXTRA=[
    [432,510],[146,627],[345,236],[114,289],[433,628],[274,720],
    [76,675],[468,304],[315,347],[175,755],[75,220],[452,751]
  ];
  const SPAWNS=[
    {dir:"北",x:270,y:126},{dir:"东",x:500,y:455},
    {dir:"南",x:270,y:791},{dir:"西",x:40,y:455}
  ];
  const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
  function make(seed=20261012){
    return {seed,status:"ready",paused:false,wave:0,maxWave:3,coreHP:100,maxHP:100,
      gold:0,score:0,elapsed:0,spawned:0,spawnClock:0,
      towers:START.map((t,i)=>({id:"t"+(i+1),x:t[0],y:t[1],kind:t[2],viewer:t[3],lv:t[4],cooldown:i*0.11,shots:0})),
      enemies:[],projectiles:[],particles:[],eventLog:["九座塔位就绪。点击开始迎接四方兽潮。"],
      nextId:1,selectedTowerId:"t1",rng:seed>>>0,joined:0};
  }
  function rand(s){s.rng=(1664525*s.rng+1013904223)>>>0;return s.rng/4294967296;}
  function log(s,t){s.eventLog.unshift(t);s.eventLog.length=Math.min(s.eventLog.length,5);}
  function reset(s){const clean=make(s.seed);Object.keys(s).forEach(k=>delete s[k]);Object.assign(s,clean);return s;}
  function start(s){if(s.status==="ready"){s.status="playing";s.wave=1;s.spawnClock=0;s.spawned=0;log(s,"第 1 波：四方向入侵开始。");}else if(s.status==="paused"){s.status="playing";s.paused=false;}return s.status;}
  function pause(s){if(s.status==="playing"){s.status="paused";s.paused=true;}else if(s.status==="paused"){s.status="playing";s.paused=false;}return s.status;}
  function select(s,id){if(s.towers.some(t=>t.id===id)){s.selectedTowerId=id;return true;}return false;}
  function upgrade(s,id=s.selectedTowerId){
    const t=s.towers.find(t=>t.id===id);if(!t)return false;
    if(t.lv>=5){log(s,t.viewer+" 的塔已满级");return false;}
    t.lv++;log(s,t.viewer+" 的"+TYPES[t.kind].label+"升至 Lv"+t.lv+"（模拟礼物）");return true;
  }
  function join(s,name){
    const text=String(name||"新观众").trim().slice(0,8);
    if(!text)return null;
    const existing=s.towers.find(t=>t.viewer===text);if(existing){s.selectedTowerId=existing.id;return existing;}
    const p=EXTRA.find(p=>!s.towers.some(t=>Math.hypot(t.x-p[0],t.y-p[1])<54));
    if(!p){log(s,"本版示意塔位已满，请稍后");return null;}
    const kinds=Object.keys(TYPES),kind=kinds[Math.floor(rand(s)*kinds.length)];
    const t={id:"extra"+(++s.nextId),x:p[0],y:p[1],kind,viewer:text,lv:1,cooldown:0,shots:0};
    s.towers.push(t);s.selectedTowerId=t.id;s.joined++;log(s,text+" 加入，获得"+TYPES[kind].label);return t;
  }
  function leave(s,id=s.selectedTowerId){
    const i=s.towers.findIndex(t=>t.id===id);if(i<0)return false;
    const t=s.towers.splice(i,1)[0];s.selectedTowerId=s.towers[0]?.id||null;log(s,t.viewer+" 离开，炮塔撤下（模拟）");return true;
  }
  function addEnemy(s,dirIndex=0,opt={}){
    const p=SPAWNS[((dirIndex%4)+4)%4];const boss=!!opt.boss;
    const wave=s.wave||1;
    const enemy={id:"e"+(++s.nextId),x:p.x,y:p.y,dir:p.dir,
      hp:opt.hp??(boss?110+wave*22:21+wave*9),maxHP:opt.hp??(boss?110+wave*22:21+wave*9),
      speed:opt.speed??(boss?23:31+wave*3),damage:opt.damage??(boss?20:9),boss,slowTimer:0,
      attackClock:0,alive:true,atCore:false};
    s.enemies.push(enemy);return enemy;
  }
  function step(s,dt){
    if(s.status!=="playing"||!Number.isFinite(dt)||dt<=0)return s;
    dt=Math.min(dt,0.05);s.elapsed+=dt;
    const counts=[0,14,19,24],need=counts[s.wave];
    s.spawnClock+=dt;
    while(s.spawned<need&&s.spawnClock>=(s.wave===1?0.78:0.6)){
      s.spawnClock-=s.wave===1?0.78:0.6;
      const boss=s.spawned===need-1;
      addEnemy(s,s.spawned%4,{boss});s.spawned++;
      if(boss)log(s,"第 "+s.wave+" 波首领出现！");
    }
    for(const e of s.enemies){
      if(e.hp<=0)continue;
      if(e.slowTimer>0)e.slowTimer=Math.max(0,e.slowTimer-dt);
      const d=Math.hypot(CORE.x-e.x,CORE.y-e.y);
      if(d>R+8){
        const v=e.speed*(e.slowTimer>0?.48:1)*dt;
        e.x+=(CORE.x-e.x)/d*Math.min(v,d-(R+8));
        e.y+=(CORE.y-e.y)/d*Math.min(v,d-(R+8));
      }else{
        e.attackClock+=dt;
        if(!e.atCore){e.atCore=true;e.attackClock=0.5;}
        if(e.attackClock>=0.8){
          e.attackClock-=0.8;s.coreHP=Math.max(0,s.coreHP-e.damage);
          s.particles.push({x:CORE.x,y:CORE.y,text:"-"+e.damage,color:"#db6262",ttl:.75});
          log(s,"核心受击 -" + e.damage+"，剩余 "+s.coreHP);
          if(s.coreHP<=0){s.status="lost";log(s,"核心被摧毁，本局失败。");break;}
          // after one core hit, enemy is consumed (keeps boss from permanent unbounded damage)
          e.hp=0;e.reached=true;
        }
      }
    }
    if(s.status!=="playing")return s;
    for(const t of s.towers){
      t.cooldown-=dt;
      if(t.cooldown>0)continue;
      const type=TYPES[t.kind];
      let target=null,best=Infinity;
      for(const e of s.enemies){
        if(e.hp<=0)continue;
        const d=dist(t,e);
        if(d<=type.range&&d<best){target=e;best=d;}
      }
      if(!target)continue;
      t.cooldown=Math.max(0.12,type.interval/(1+(t.lv-1)*0.13));
      t.shots++;
      s.projectiles.push({x:t.x,y:t.y,targetId:target.id,kind:t.kind,damage:Math.round(type.damage*(1+(t.lv-1)*0.25)),speed:type.bulletSpeed,area:type.area,slow:type.slow});
    }
    const remaining=[];
    for(const p of s.projectiles){
      const target=s.enemies.find(e=>e.id===p.targetId&&e.hp>0);
      if(!target)continue;
      const d=dist(p,target),move=p.speed*dt;
      if(d>move+2){p.x+=(target.x-p.x)/d*move;p.y+=(target.y-p.y)/d*move;remaining.push(p);continue;}
      const victims=p.area?s.enemies.filter(e=>e.hp>0&&dist(e,target)<=p.area):[target];
      for(const e of victims){
        e.hp-=p.damage;
        if(p.slow)e.slowTimer=Math.max(e.slowTimer,p.slow);
        if(e.hp<=0){s.score+=e.boss?10:1;s.gold+=e.boss?5:1;}
      }
      s.particles.push({x:target.x,y:target.y,text:p.area?"爆":"•",color:p.area?"#e57463":p.slow?"#6db5d6":"#d0a34e",ttl:.28});
    }
    s.projectiles=remaining;
    s.enemies=s.enemies.filter(e=>e.hp>0);
    s.particles=s.particles.filter(p=>(p.ttl-=dt)>0);
    if(s.spawned>=need&&s.enemies.length===0){
      if(s.wave===s.maxWave){s.status="won";log(s,"守住全部兽潮！城防核心安全。");}
      else{s.wave++;s.spawned=0;s.spawnClock=-1.15;log(s,"第 "+s.wave+" 波准备中");}
    }
    return s;
  }
  const simulate=(s,seconds)=>{for(let i=0;i<Math.ceil(seconds*60);i++)step(s,1/60);return s;};
  return {W,H,CORE,R,TYPES,START,SPAWNS,make,reset,start,pause,select,upgrade,join,leave,addEnemy,step,simulate};
});
