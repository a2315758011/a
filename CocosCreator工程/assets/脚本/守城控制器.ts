import { _decorator, Component, Node, UITransform, Graphics, Label, Color, Vec3, input, Input, EventTouch, EventMouse, EventKeyboard, KeyCode, HorizontalTextAlignment, VerticalTextAlignment, Layers, view } from 'cc';
import { 直播事件桥, 直播事件, 直播会话快照, 观众记录 } from './直播事件桥';
import { 玩家档案仓库, 商店商品Id, 商店条目, 购买结果, 玩家档案 } from './玩家档案';
import { 平台适配器, 平台快照, 平台运行模式, 直播事件源接口 } from './平台适配器';
import { WebSocket直播参与事件源, 直播参与事件源快照 } from './直播参与事件源';
const { ccclass, property } = _decorator;

type 炮种 = '连珠'|'重炮'|'寒霜';
interface 炮塔 {x:number; y:number; type:炮种; level:number; cd:number; owner:string; ownerId:string;}
interface 兽人 {x:number; y:number; hp:number; max:number; speed:number; r:number; slow:number; boss:boolean;}
interface 弹道 {x:number; y:number; tx:number; ty:number; age:number; type:炮种;}
type 局状态='ready'|'running'|'paused'|'win'|'lose';

@ccclass('守城控制器')
export class 守城控制器 extends Component {
  @property({tooltip:'仅供候选美术试玩场景打开'})
  public useCandidateArt=false;
  // 只读数据观察接口，不改变战斗计算，外部渲染器不得修改引用的实体。
  public candidateArtState(): {
    readonly towers: readonly 炮塔[];readonly enemies:readonly 兽人[];readonly shots:readonly 弹道[];
    readonly camX:number;readonly camY:number;readonly zoom:number;
    readonly health:number;readonly maxHealth:number;readonly wave:number;readonly kills:number;readonly gameState:局状态;readonly gameTime:number;
    readonly viewers:number;readonly giftEvents:number;readonly liveQueue:number;
    readonly coins:number;readonly lastReward:number;readonly profile:Readonly<玩家档案>;
    readonly duplicateLiveEvents:number;readonly rejectedLiveEvents:number;readonly lastLiveEvent:string;
  } {
    const live=this.liveBridge.metrics();
    const profile=this.profileRepo.snapshot();
    return {towers:this.towers,enemies:this.enemies,shots:this.shots,camX:this.camX,camY:this.camY,
      zoom:this.zoom,health:this.hp,maxHealth:this.maxHP,wave:this.wave,kills:this.kills,gameState:this.state,gameTime:this.time,
      viewers:live.onlineViewers,giftEvents:live.giftEvents,liveQueue:live.queueDepth,
      coins:profile.coins,lastReward:this.lastReward,profile,
      duplicateLiveEvents:live.duplicateEvents,rejectedLiveEvents:live.rejectedEvents,lastLiveEvent:live.lastEvent};
  }

  public receiveLiveEvent(event:直播事件):boolean {
    return this.liveBridge.enqueue(event).accepted;
  }

  public liveSessionSnapshot():直播会话快照 {
    return this.liveBridge.snapshot();
  }

  public platformSnapshot():平台快照 {
    return this.platformAdapter.snapshot();
  }

  public setPlatformMode(mode:平台运行模式):void {
    this.platformAdapter.setMode(mode);
    if(this.state==='ready')this.reset();
    else this.render();
  }

  public attachLiveEventSource(source:直播事件源接口):void {
    this.platformAdapter.attachLiveSource(source,(event)=>this.receiveLiveEvent(event));
  }

  public detachLiveEventSource():void {
    this.platformAdapter.detachLiveSource();
    this.liveParticipationSource=null;
  }

  public attachDouyinParticipationWebSocket(url:string):直播参与事件源快照 {
    this.setPlatformMode('douyin-live-play');
    const source=new WebSocket直播参与事件源({
      url,
      joinCommands:['加入','888'],
      leaveCommands:['退出']
    });
    this.liveParticipationSource=source;
    if(!/^wss?:\/\//i.test(String(url||'').trim())){
      source.start(()=>false);
      return source.snapshot();
    }
    this.attachLiveEventSource(source);
    return source.snapshot();
  }

  public liveParticipationSourceSnapshot():直播参与事件源快照|null {
    return this.liveParticipationSource?.snapshot()||null;
  }
  private attachConfiguredLiveSource():void {
    const runtime=this.platformAdapter.snapshot().runtime;
    const g=globalThis as unknown as {
      __LIVE_TURRET_LIVE_CONFIG__?:{websocketUrl?:string;url?:string};
    };
    const config=g.__LIVE_TURRET_LIVE_CONFIG__;
    const url=String(config?.websocketUrl||config?.url||'').trim();
    // The official platform event must be verified by the developer backend.
    // Without a configured endpoint the client never pretends to be connected.
    if(runtime==='douyin'&&url)this.attachDouyinParticipationWebSocket(url);
  }


  public profileSnapshot():玩家档案 {
    return this.profileRepo.snapshot();
  }

  public shopCatalog():商店条目[] {
    const catalog=this.profileRepo.catalog();
    if(this.platformAdapter.snapshot().shopAllowed)return catalog;
    return catalog.map(item=>({...item,canBuy:false}));
  }

  public buyShopItem(id:商店商品Id):购买结果 {
    if(!this.platformAdapter.snapshot().shopAllowed){
      const profile=this.profileRepo.snapshot();
      return {ok:false,reason:'platform-disabled',id,level:profile.upgrades[id],coins:profile.coins,cost:0};
    }
    const result=this.profileRepo.purchase(id);
    this.render();
    return result;
  }

  public profileCloudStatus():{configured:boolean;payload:玩家档案} {
    return {configured:this.profileRepo.cloudConfigured(),payload:this.profileRepo.exportCloudPayload()};
  }

  public restartFromSettlement():void {
    if(this.state==='win'||this.state==='lose')this.reset();
  }

  public setInputBlocked(blocked:boolean):void {
    this.inputBlocked=blocked;
    if(blocked)this.drag=false;
  }

  public startNewRunFromMenu():void {
    this.reset();
    this.state='running';
    this.render();
  }

  public returnToMenuState():void {
    this.reset();
    this.render();
  }

  public setCandidateHudContrast(enabled:boolean):void {
    if(this.title)this.title.color=enabled?new Color(239,247,255,255):new Color(28,44,53,255);
    if(this.sub)this.sub.color=enabled?new Color(199,226,241,255):new Color(28,44,53,255);
    if(this.help)this.help.color=enabled?new Color(215,236,245,255):new Color(28,44,53,255);
  }

  private pen!: Graphics;
  private title!: Label;
  private sub!: Label;
  private help!: Label;
  private towers: 炮塔[]=[];
  private readonly liveBridge=new 直播事件桥();
  private readonly profileRepo=new 玩家档案仓库();
  private readonly platformAdapter=new 平台适配器();
  private liveParticipationSource:WebSocket直播参与事件源|null=null;
  private fireControlMultiplier=1;
  private viewerStartLevel=1;
  private terminalRewarded=false;
  private lastReward=0;
  private enemies:兽人[]=[];
  private shots:弹道[]=[];
  private worldSize=3200;
  private hudHalfHeight=480;
  // Dynamic width-fixed viewport; Cocos project resolution policy is FIXED_WIDTH (4).
  // Larger aspect ratios reveal more world vertically instead of black bars.
  private updatePortraitLayout():number {
    const visible=view.getVisibleSize();
    const half=visible.height/2;
    if(Math.abs(half-this.hudHalfHeight) < .5) return half;
    this.hudHalfHeight=half;
    this.title.node.setPosition(0,half-31,0);
    this.sub.node.setPosition(0,half-115,0);
    this.help.node.setPosition(0,-half+36,0);
    for(const child of this.node.children){
      if(child.name.startsWith('按钮-'))child.setPosition(child.position.x,-half+96,0);
      if(child.name.startsWith('镜头-'))child.setPosition(child.position.x,half-106,0);
    }
    return half;
  }
  private camX=0;
  private camY=0;
  private zoom=1;
  private hp=100;
  private maxHP=100;
  private wave=1;
  private time=0;
  private nextSpawn=1;
  private totalSpawn=0;
  private kills=0;
  private serial=9;
  private state:局状态='ready';
  private inputBlocked=false;
  private drag=false;
  private lastClick='无';
  private lastTouch={x:0,y:0};
  private readonly palette=[
    new Color(231,172,41,255),
    new Color(189,87,55,255),
    new Color(78,173,198,255)
  ];
  onLoad():void{
    const penNode=new Node('战场画笔');
    this.node.addChild(penNode);
    penNode.layer=Layers.Enum.UI_2D;
    penNode.addComponent(UITransform).setContentSize(540,960);
    this.pen=penNode.addComponent(Graphics);
    this.title=this.makeLabel('游戏状态',0,452,510,32,22);
    this.sub=this.makeLabel('战场说明',0,393,516,28,18);
    this.help=this.makeLabel('操作提示',0,-444,510,26,17);
    for(const [i,label] of ['开始/暂停','观众+1','升级','离场','重开'].entries()){
      const b=this.makeLabel('按钮-'+label,-205+i*102,-384,100,42,16);
      b.string=label;b.color=new Color(255,255,255,255);
    }
    for(const item of [{n:'回核心',x:-170},{n:'缩小',x:140},{n:'放大',x:207}]){
      const b=this.makeLabel('镜头-'+item.n,item.x,374,item.n==='回核心'?115:54,26,14);b.string=item.n;
    }
    this.reset();
    input.on(Input.EventType.TOUCH_START,this.touchStart,this);
    input.on(Input.EventType.TOUCH_MOVE,this.touchMove,this);
    input.on(Input.EventType.TOUCH_END,this.touchEnd,this);
    input.on(Input.EventType.TOUCH_CANCEL,this.touchEnd,this);
    input.on(Input.EventType.MOUSE_DOWN,this.touchStart,this);
    input.on(Input.EventType.MOUSE_MOVE,this.touchMove,this);
    input.on(Input.EventType.MOUSE_UP,this.touchEnd,this);
    input.on(Input.EventType.KEY_DOWN,this.onKeyDown,this);
    this.attachConfiguredLiveSource();
  }
  protected onDestroy():void{
    this.platformAdapter.detachLiveSource();
    this.liveParticipationSource=null;
    input.off(Input.EventType.TOUCH_START,this.touchStart,this);
    input.off(Input.EventType.TOUCH_MOVE,this.touchMove,this);
    input.off(Input.EventType.TOUCH_END,this.touchEnd,this);
    input.off(Input.EventType.TOUCH_CANCEL,this.touchEnd,this);
    input.off(Input.EventType.MOUSE_DOWN,this.touchStart,this);
    input.off(Input.EventType.MOUSE_MOVE,this.touchMove,this);
    input.off(Input.EventType.MOUSE_UP,this.touchEnd,this);
    input.off(Input.EventType.KEY_DOWN,this.onKeyDown,this);
  }
  private makeLabel(name:string,_x:number,y:number,w:number,h:number,size:number):Label{
    const n=new Node(name);
    this.node.addChild(n);
    n.layer=Layers.Enum.UI_2D;
    n.setPosition(_x,y,0);
    const t=n.addComponent(UITransform);t.setContentSize(w,h);
    const lab=n.addComponent(Label);
    lab.fontSize=size;
    lab.lineHeight=Math.max(size+4,24);
    lab.horizontalAlign=HorizontalTextAlignment.CENTER;
    lab.verticalAlign=VerticalTextAlignment.CENTER;
    lab.color=new Color(28,44,53,255);
    return lab;
  }
  private reset():void{
    this.towers=[];this.enemies=[];this.shots=[];
    this.camX=0;this.camY=0;this.zoom=.9;
    const profile=this.profileRepo.snapshot();
    const economyAllowed=this.platformAdapter.snapshot().persistentEconomyAllowed;
    this.maxHP=economyAllowed?100+profile.upgrades.coreShield*10:100;
    this.hp=this.maxHP;this.wave=1;this.time=0;this.nextSpawn=0.9;
    this.fireControlMultiplier=economyAllowed?1+profile.upgrades.fireControl*.05:1;
    this.viewerStartLevel=economyAllowed?1+profile.upgrades.viewerBoost:1;
    this.lastReward=0;this.terminalRewarded=false;
    this.kills=0;this.totalSpawn=0;this.serial=9;this.state='ready';
    const names=['阿风','小虎','阿宁','小北','铁柱','小云','阿亮','糖糖','小鱼'];
    for(let i=0;i<9;i++){
      const a=i*Math.PI*2/9,rad=165+(i%3)*35;
      this.towers.push({x:Math.cos(a)*rad,y:Math.sin(a)*rad,type:(['连珠','重炮','寒霜'] as 炮种[])[i%3],level:1,cd:0,owner:names[i],ownerId:'base-'+(i+1)});
    }
    // 直播会话属于房间级状态，不应因单局重开/返回主界面而清零。
    this.restoreLiveViewerTowers();
    this.render();
  }

  private restoreLiveViewerTowers():void {
    for(const viewer of this.liveBridge.snapshot().viewers){
      if(viewer.online)this.addLiveViewerTower(viewer);
    }
  }

  private addLiveViewerTower(viewer:Readonly<观众记录>):炮塔 {
    const existing=this.towers.find(t=>t.ownerId===viewer.viewerId);
    if(existing){
      existing.owner=viewer.viewerName;
      existing.level=Math.max(existing.level,Math.min(5,this.viewerStartLevel+viewer.giftPower));
      return existing;
    }
    this.serial++;
    const a=this.serial*2.399963229728653;
    const ring=155+(Math.sqrt(this.serial)*38);
    const tower:炮塔={
      x:Math.cos(a)*ring,y:Math.sin(a)*ring,
      type:(['连珠','重炮','寒霜'] as 炮种[])[this.serial%3],
      level:Math.min(5,this.viewerStartLevel+viewer.giftPower),cd:0,
      owner:viewer.viewerName,ownerId:viewer.viewerId
    };
    this.towers.push(tower);
    return tower;
  }

  private simulateViewerJoin():void{
    const next=this.serial+1;
    this.receiveLiveEvent({
      eventId:'sim-join-'+next+'-'+Date.now(),type:'viewer_join',
      viewerId:'sim-'+next,viewerName:'观众'+next,timestamp:Date.now(),source:'simulation'
    });
    this.flushLiveEvents();
  }

  private simulateViewerGift():void{
    let tower=[...this.towers].reverse().find(t=>!t.ownerId.startsWith('base-'));
    if(!tower){
      this.simulateViewerJoin();
      tower=[...this.towers].reverse().find(t=>!t.ownerId.startsWith('base-'));
    }
    if(!tower)return;
    this.receiveLiveEvent({
      eventId:'sim-gift-'+tower.ownerId+'-'+Date.now(),type:'gift',
      viewerId:tower.ownerId,viewerName:tower.owner,giftId:'ui-upgrade',giftPower:1,
      timestamp:Date.now(),source:'simulation'
    });
    this.flushLiveEvents();
  }

  private simulateViewerLeave():void{
    const tower=[...this.towers].reverse().find(t=>!t.ownerId.startsWith('base-'));
    if(!tower)return;
    this.receiveLiveEvent({
      eventId:'sim-leave-'+tower.ownerId+'-'+Date.now(),type:'viewer_leave',
      viewerId:tower.ownerId,viewerName:tower.owner,timestamp:Date.now(),source:'simulation'
    });
    this.flushLiveEvents();
  }

  private flushLiveEvents():number {
    return this.liveBridge.drain((event,viewer)=>{
      if(event.type==='viewer_join'){
        this.addLiveViewerTower(viewer);
      }else if(event.type==='viewer_leave'){
        const index=this.towers.findIndex(t=>t.ownerId===event.viewerId);
        if(index>=0)this.towers.splice(index,1);
      }else{
        const tower=this.addLiveViewerTower(viewer);
        // 礼物成长按房间会话累计，重开后仍能从 viewer.giftPower 重建等级。
        tower.level=Math.min(5,this.viewerStartLevel+viewer.giftPower);
      }
    },128);
  }
  private evPos(e:EventTouch|EventMouse):{x:number,y:number}{
    const p=e.getUILocation();
    const u=this.node.getComponent(UITransform)!;
    const v=u.convertToNodeSpaceAR(new Vec3(p.x,p.y,0));
    // Canvas UI input arrives from the lower-left in this 540×960 project.
    // Gameplay controls and camera coordinates are centered on (0,0).
    // FIXED_WIDTH expands visible height on tall phones while the serialized
    // Canvas UITransform remains 540x960. Align input with the extended drawing area.
    const extraY=(view.getVisibleSize().height-u.height)*0.5;
    return {x:v.x-u.width*0.5,y:v.y-u.height*0.5-extraY};
  }
  private lastPointerAt=0;
  private lastPointerPos={x:Number.POSITIVE_INFINITY,y:Number.POSITIVE_INFINITY};
  private touchStart(e:EventTouch|EventMouse):void{
    if(this.inputBlocked)return;
    const p=this.evPos(e);
    // Browser mouse may synthesize a Cocos touch event. Suppress only duplicate
    // same-coordinate starts within 100ms; separate/normal clicks still work.
    const now=Date.now();
    if(now-this.lastPointerAt<100 &&
       Math.abs(p.x-this.lastPointerPos.x)<3 &&
       Math.abs(p.y-this.lastPointerPos.y)<3)return;
    this.lastPointerAt=now;this.lastPointerPos={x:p.x,y:p.y};
    if(this.state==='win'||this.state==='lose'){
      this.drag=false;
      if(p.y < -this.hudHalfHeight+130 && p.x>160)this.reset();
      this.render();
      return;
    }
    this.lastClick=Math.round(p.x)+','+Math.round(p.y);
    this.lastTouch={x:p.x,y:p.y};this.drag=true;
    if(p.y < -this.hudHalfHeight+130){
      this.drag=false;
      if(p.x<-160) {
        if(this.state==='ready'||this.state==='paused')this.state='running';
        else if(this.state==='running')this.state='paused';
      }else if(p.x<-55){
        this.simulateViewerJoin();
      }else if(p.x<55){
        this.simulateViewerGift();
      }else if(p.x<160){
        this.simulateViewerLeave();
      }else this.reset();
    }else if(p.y>this.hudHalfHeight-136 && p.x>80){
      this.zoom=Math.max(.48,Math.min(2.4,this.zoom+(p.x>190?.22:-.22)));
      this.drag=false;
    }else if(p.y>this.hudHalfHeight-136 && p.x<-100){
      this.camX=0;this.camY=0;this.drag=false;
    }
    this.render();
  }
  private touchMove(e:EventTouch|EventMouse):void{
    if(this.inputBlocked||!this.drag)return;
    const p=this.evPos(e);
    const dx=(p.x-this.lastTouch.x)/this.zoom,dy=(p.y-this.lastTouch.y)/this.zoom;
    this.camX=Math.max(-1300,Math.min(1300,this.camX-dx));
    this.camY=Math.max(-1300,Math.min(1300,this.camY-dy));
    this.lastTouch=p;this.render();
  }
  private touchEnd():void{this.drag=false;}
  private onKeyDown(e:EventKeyboard):void{
    if(this.inputBlocked)return;
    if(this.state==='win'||this.state==='lose'){
      if(e.keyCode===KeyCode.KEY_R)this.reset();
      this.render();
      return;
    }
    switch(e.keyCode){
      case KeyCode.SPACE:
        if(this.state==='ready'||this.state==='paused')this.state='running';
        else if(this.state==='running')this.state='paused';
        break;
      case KeyCode.KEY_J:this.simulateViewerJoin();break;
      case KeyCode.KEY_G:this.simulateViewerGift();break;
      case KeyCode.KEY_L:this.simulateViewerLeave();break;
      case KeyCode.KEY_R:this.reset();break;
      case KeyCode.EQUAL:this.zoom=Math.min(2.4,this.zoom+.2);break;
      case KeyCode.MINUS:this.zoom=Math.max(.48,this.zoom-.2);break;
    }
    this.render();
  }
  private simulationDebt=0;
  private drawDebt=0;
  update(dt:number):void{
    this.flushLiveEvents();
    const elapsed=Math.min(.16,Math.max(0,dt));
    this.drawDebt+=elapsed;
    if(this.state==='running'){
      this.simulationDebt=Math.min(.25,this.simulationDebt+elapsed);
      const fixed=1/30;
      let steps=0;
      while(this.simulationDebt>=fixed && steps<5 && this.state==='running'){
        this.tick(fixed);
        this.simulationDebt-=fixed;
        steps++;
      }
    }else{
      this.simulationDebt=0;
    }
    if(this.drawDebt>=1/20){
      this.drawDebt=0;
      this.render();
    }
  }
  private tick(dt:number):void{
    this.time+=dt;
    if(this.nextSpawn<=this.time && this.totalSpawn<16+this.wave*8){
      const i=this.totalSpawn++,a=(i*2.39996323+this.wave*.17)%(Math.PI*2);
      const rad=750+Math.random()*60;
      const boss=i===15+this.wave*8;
      const hp=(boss?155:22)+this.wave*(boss?40:12);
      this.enemies.push({x:Math.cos(a)*rad,y:Math.sin(a)*rad,hp,max:hp,speed:(boss?30:55)+this.wave*3,r:boss?23:12,slow:0,boss});
      this.nextSpawn=this.time+(.55-.08*Math.min(3,this.wave));
    }
    for(const t of this.towers){
      t.cd=Math.max(0,t.cd-dt);
      if(t.cd>0)continue;
      const range=(t.type==='重炮'?235:210)+t.level*13;
      const range2=range*range;
      let hit:兽人|undefined,closest=Infinity;
      for(const m of this.enemies){
        const dx=t.x-m.x,dy=t.y-m.y,dis=dx*dx+dy*dy;
        if(dis<range2&&dis<closest){hit=m;closest=dis;}
      }
      if(!hit)continue;
      const damage=((t.type==='重炮'?16:7)+(t.level-1)*(t.type==='重炮'?8:3))*this.fireControlMultiplier;
      if(t.type==='重炮'){
        for(const e of this.enemies){const d=(e.x-hit.x)**2+(e.y-hit.y)**2;if(d<62*62)e.hp-=damage;}
      }else hit.hp-=damage;
      if(t.type==='寒霜')hit.slow=Math.max(hit.slow,1.5);
      this.shots.push({x:t.x,y:t.y,tx:hit.x,ty:hit.y,age:0,type:t.type});
      t.cd=(t.type==='重炮'?1.65:t.type==='寒霜'?0.8:0.6)/(1+(t.level-1)*.13);
    }
    for(const m of this.enemies){
      if(m.hp<=0)continue;
      const d=Math.hypot(m.x,m.y);
      if(d<35){this.hp=Math.max(0,this.hp-(m.boss?22:6));m.hp=0;continue;}
      const speed=m.speed*(m.slow>0?.53:1);
      m.x-=m.x/d*speed*dt;m.y-=m.y/d*speed*dt;
      m.slow=Math.max(0,m.slow-dt);
    }
    const alive=this.enemies.filter(m=>m.hp>0);
    this.kills+=this.enemies.length-alive.length;
    this.enemies=alive;
    this.shots=this.shots.filter(s=>(s.age+=dt)<.19);
    if(this.hp<=0){this.settleRun(false);this.state='lose';return;}
    if(this.totalSpawn>=16+this.wave*8&&this.enemies.length===0){
      if(this.wave===3){this.settleRun(true);this.state='win';return;}
      this.wave++;this.totalSpawn=0;this.nextSpawn=this.time+2;
    }
  }
  private settleRun(won:boolean):void {
    if(this.terminalRewarded)return;
    this.lastReward=this.platformAdapter.snapshot().persistentEconomyAllowed
      ? this.profileRepo.recordSettlement(this.kills,won)
      : 0;
    this.terminalRewarded=true;
  }

  private sx(x:number):number{return (x-this.camX)*this.zoom;}
  private sy(y:number):number{return (y-this.camY)*this.zoom;}
  private box(x:number,y:number,w:number,h:number,c:Color):void{
    this.pen.fillColor=c;this.pen.fillRect(x,y,w,h);
  }
  private disc(x:number,y:number,r:number,c:Color):void{
    const g=this.pen;g.fillColor=c;g.circle(x,y,r);g.fill();
  }
  private labelAt(x:number,y:number,value:string,size:number=13,color:Color=new Color(30,48,62,255)):void{
    // Graphics-only glyphs are avoided: names/HUD are actual Cocos Label components.
    // Per-unit names will be separately pooled as Cocos labels in the art integration phase.
    void x;void y;void value;void size;void color;
  }
  private render():void{
    if(!this.pen)return;
    const g=this.pen;g.clear();
    const half=this.updatePortraitLayout();
    if(!this.useCandidateArt)this.box(-270,-half,540,2*half,new Color(235,243,239,255));
    g.lineWidth=1;g.strokeColor=new Color(216,225,219,255);
    for(let x=-1600;x<=1600;x+=80){
      const p=this.sx(x);if(p < -265||p>265)continue;
      g.moveTo(p,-half+135);g.lineTo(p,half-140);g.stroke();
    }
    for(let y=-1600;y<=1600;y+=80){
      const p=this.sy(y);if(p<-half+135||p>half-140)continue;
      g.moveTo(-270,p);g.lineTo(270,p);g.stroke();
    }
    // Visible scene is only a camera viewport into 3200x3200 world.
    g.strokeColor=new Color(153,178,165,255);g.lineWidth=3;
    const edge=this.worldSize/2;
    const ex1=this.sx(-edge),ex2=this.sx(edge),ey1=this.sy(-edge),ey2=this.sy(edge);
    g.rect(ex1,ey1,ex2-ex1,ey2-ey1);g.stroke();
    for(let k=0;k<12;k++){
      const t=(k+1)/13;
      this.disc(this.sx(Math.cos(k*1.3)*650),this.sy(Math.sin(k*1.3)*650),Math.max(1.5,2*this.zoom),new Color(200,213,204,255));
    }
    // Only central energy crystal can take damage: tower beams terminate at incoming orcs.
    const cx=this.sx(0),cy=this.sy(0);
    if(!this.useCandidateArt){
    this.disc(cx,cy,Math.max(6,34*this.zoom),new Color(210,226,217,255));
    this.box(cx-24*this.zoom,cy-15*this.zoom,48*this.zoom,31*this.zoom,new Color(111,129,139,255));
    g.fillColor=new Color(41,170,222,255);
    g.moveTo(cx,cy+36*this.zoom);g.lineTo(cx+20*this.zoom,cy);
    g.lineTo(cx,cy-36*this.zoom);g.lineTo(cx-20*this.zoom,cy);g.close();g.fill();
    g.strokeColor=new Color(16,111,154,255);g.lineWidth=2;g.stroke();
    } // 原核心绘制分支
    if(!this.useCandidateArt){
    for(const t of this.towers){
      const x=this.sx(t.x),y=this.sy(t.y);
      if(Math.abs(x)>280||Math.abs(y)>half-125)continue;
      const size=Math.max(4,13*this.zoom);
      const c=this.palette[t.type==='连珠'?0:t.type==='重炮'?1:2];
      this.box(x-size,y-size,2*size,2*size,new Color(50,62,66,255));
      this.box(x-size+2,y-size+2,2*size-4,2*size-4,c);
      if(this.zoom>.8){
        this.box(x-3*this.zoom,y-19*this.zoom,6*this.zoom,19*this.zoom,new Color(61,80,82,255));
      }
    }
    for(const m of this.enemies){
      const x=this.sx(m.x),y=this.sy(m.y);
      if(Math.abs(x)>290||Math.abs(y)>half-115)continue;
      const r=Math.max(3,m.r*this.zoom);
      this.disc(x,y,r,m.boss?new Color(157,58,57,255):new Color(107,161,84,255));
      this.box(x-r,y+r+2,2*r,3,new Color(96,43,43,255));
      this.box(x-r,y+r+2,2*r*(m.hp/m.max),3,new Color(83,190,97,255));
    }
    } // 原炮塔与怪物绘制分支
    // Off-screen enemies are still advancing in the 3200x3200 world.
    // Small edge pips provide direction feedback while keeping the HUD uncluttered.
    let arrows=0;
    for(const e of this.enemies){
      if(arrows>=8)break;
      const x=this.sx(e.x),y=this.sy(e.y);
      if(Math.abs(x)<255 && Math.abs(y)<half-153)continue;
      const k=Math.min(245/Math.max(1,Math.abs(x)),(half-160)/Math.max(1,Math.abs(y)));
      const dx=x*k,dy=y*k;
      this.disc(dx,dy,4,new Color(231,118,68,255));
      arrows++;
    }
    if(!this.useCandidateArt){
      for(const s of this.shots){
        const fromX=this.sx(s.x),fromY=this.sy(s.y),toX=this.sx(s.tx),toY=this.sy(s.ty);
        g.strokeColor=s.type==='寒霜'?new Color(39,185,244,255):s.type==='重炮'?new Color(232,92,35,255):new Color(228,198,61,255);
        g.lineWidth=Math.max(1,(s.type==='重炮'?4:2)*this.zoom);
        g.moveTo(fromX,fromY);g.lineTo(toX,toY);g.stroke();
      }
    }
    if(!this.useCandidateArt){
    this.box(-270,half-126,540,126,new Color(231,242,247,255));
    this.box(-270,-half,540,121,new Color(230,238,243,255));
    const btn=[
      {x:-254,w:98,text:'开始/暂停',c:new Color(88,140,181,255)},
      {x:-151,w:96,text:'观众+1',c:new Color(108,160,113,255)},
      {x:-50,w:96,text:'升级',c:new Color(180,135,58,255)},
      {x:51,w:96,text:'离场',c:new Color(158,113,118,255)},
      {x:152,w:101,text:'重开',c:new Color(103,120,150,255)}
    ];
    for(const b of btn)this.box(b.x,-half+71,b.w,50,b.c);
    this.box(-230,half-121,120,29,new Color(199,216,226,255));
    this.box(112,half-121,54,29,new Color(197,219,227,255));
    this.box(177,half-121,58,29,new Color(197,219,227,255));
    }
    this.title.string='第 '+this.wave+'/3 波 · '+(this.state==='ready'?'准备开战':this.state==='running'?'守城中':this.state==='paused'?'已暂停':this.state==='win'?'守城成功':'守城失败');
    const live=this.liveBridge.metrics();
    this.sub.string='水晶 '+this.hp+'/'+this.maxHP+' · 炮塔 '+this.towers.length+' · 击杀 '+this.kills;
    this.help.string='在线 '+live.onlineViewers+' · 礼物 '+live.giftPower+'  | 进场增塔 · 礼物升级';
  }
}
