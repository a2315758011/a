// Node 24 零依赖规则回归；全部断言是可复现的确定性规则，不冒充真人试玩
const assert=require("node:assert/strict");
const E=require("./规则引擎.js");
let passed=0;
function t(name,fn){try{fn();passed++;console.log("PASS",name);}catch(e){console.error("FAIL",name,e.stack);process.exitCode=1;}}
t("初始恰有9座塔+3种炮种+唯一核心满血",()=>{
 const s=E.make();assert.equal(s.towers.length,9);
 assert.deepEqual(new Set(s.towers.map(x=>x.kind)),new Set(Object.keys(E.TYPES)));
 assert.equal(s.coreHP,100);assert.equal(s.status,"ready");assert.equal(s.wave,0);
 assert.deepEqual(E.CORE,{x:270,y:455});
});
t("北东南西各有入口",()=>{assert.deepEqual(E.SPAWNS.map(x=>x.dir),["北","东","南","西"]);});
t("开始/暂停/恢复状态转换",()=>{const s=E.make();E.start(s);assert.equal(s.status,"playing");E.pause(s);assert.equal(s.status,"paused");const time=s.elapsed;E.step(s,1);assert.equal(time,s.elapsed);E.pause(s);assert.equal(s.status,"playing");});
t("升级只升级选中玩家且Lv5封顶",()=>{
 const s=E.make();const first=s.towers[0],other=s.towers[1],lvl=other.lv;
 assert.equal(E.upgrade(s,first.id),true);assert.equal(first.lv,4);assert.equal(other.lv,lvl);
 assert.equal(E.upgrade(s,first.id),true);assert.equal(first.lv,5);
 assert.equal(E.upgrade(s,first.id),false);assert.equal(first.lv,5);
});
t("加入不复制重复昵称, 离场只撤玩家塔不删水晶",()=>{
 const s=E.make();const first=E.join(s,"测试甲");
 assert(first);assert.equal(s.towers.length,10);
 const again=E.join(s,"测试甲");assert.equal(again.id,first.id);assert.equal(s.towers.length,10);
 assert.equal(E.leave(s,first.id),true);assert.equal(s.towers.length,9);assert.equal(s.coreHP,100);
});
t("种子生成额外炮种稳定",()=>{
 const a=E.make(42),b=E.make(42);assert.equal(E.join(a,"甲").kind,E.join(b,"甲").kind);
});
t("刷怪点朝唯一核心前进",()=>{
 const s=E.make();E.start(s);
 const monsters=E.SPAWNS.map((_,i)=>E.addEnemy(s,i,{speed:20,hp:1000}));
 const before=monsters.map(e=>Math.hypot(E.CORE.x-e.x,E.CORE.y-e.y));
 E.step(s,0.05);
 for(let i=0;i<monsters.length;i++)assert(Math.hypot(E.CORE.x-monsters[i].x,E.CORE.y-monsters[i].y)<before[i]);
});
t("四方怪物抵达中央并能使水晶归零失败",()=>{
 const s=E.make();E.start(s);s.towers.length=0;s.coreHP=9;
 E.addEnemy(s,0,{speed:2000,hp:1000,damage:10});
 E.simulate(s,2);assert.equal(s.status,"lost");assert.equal(s.coreHP,0);
});
t("防守三波可通关，并可以重开",()=>{
 const s=E.make(7);E.start(s);
 // 使用正常游戏的九塔；长时间模拟直到结束，若不能胜利则揭示数值平衡缺陷
 E.simulate(s,200);
 assert.equal(s.status,"won","默认九塔需要能守完三波才能真正可玩");
 assert(s.coreHP>0);E.reset(s);
 assert.equal(s.status,"ready");assert.equal(s.towers.length,9);assert.equal(s.coreHP,100);
});
t("怪物击杀不可无限重复结算",()=>{
 const s=E.make();E.start(s);const e=E.addEnemy(s,2,{hp:1,speed:1});
 e.hp=-5;const score=s.score;E.step(s,.05);assert.equal(s.score,score);assert(!s.enemies.some(x=>x.id===e.id));
});
console.log("PASS_COUNT",passed,"TOTAL",10);if(process.exitCode)process.exit(1);
