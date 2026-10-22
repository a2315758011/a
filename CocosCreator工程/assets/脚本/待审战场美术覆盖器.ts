import { _decorator, Component, Node, Sprite, SpriteFrame, Color, UITransform, Layers, resources, profiler, view, Graphics, Label, HorizontalTextAlignment, VerticalTextAlignment, Button, EventHandler, JsonAsset } from 'cc';
import { 守城控制器 } from './守城控制器';
const { ccclass } = _decorator;

type TowerKind = 'rapid'|'heavy'|'frost';
type ShopId='coreShield'|'fireControl'|'viewerBoost';
type ShopRow={id:ShopId;info:Label;buttonSprite:Sprite;button:Button;buttonLabel:Label};
type TowerInstance = { node:Node; sprites:Sprite[]; fx:Sprite; kind:TowerKind|null; level:number; upgradeTimer:number; };
type ShotFxInstance = { root:Node; projectile:Sprite; muzzle:Sprite; impact:Sprite; };
type EnemyAnimState = 'walk'|'hurt'|'attack'|'death';
type EnemyKeyframeState = 'idle'|EnemyAnimState;
type LayerPose = { x:number;y:number;r:number;sx:number;sy:number;a:number; };
type EnemyPoseFrame = { root:LayerPose;layers:LayerPose[]; };
type EnemyKeyframeSet = { frameRate:number;frameDurationMs:number;frameCount:number;states:Record<EnemyKeyframeState,{loop:boolean;frames:EnemyPoseFrame[]}>; };
type EnemyInstance = { node:Node; master:Sprite; sprites:Sprite[]; frame:number; kind:'grunt'|'boss'|null; mobRef:object|null; lastHp:number; hurtTimer:number; attackTimer:number; deathTimer:number; ghost:boolean; animState:EnemyAnimState; lastX:number; lastY:number; lastScale:number; lastDistance:number; };

@ccclass('待审战场美术覆盖器')
export class 待审战场美术覆盖器 extends Component {
  private controller:守城控制器|null=null;
  private artRoot!:Node;
  private crystalRoot!:Node;
  private crystalSprites:Sprite[]=[];
  private towerFrames=new Map<TowerKind,SpriteFrame[]>();
  private crystalFrames:SpriteFrame[]=new Array<SpriteFrame>(3);
  private groundRoot!:Node;
  private groundSprite!:Sprite;
  private groundFrame:SpriteFrame|null=null;
  private runeRoot!:Node;
  private runeSprite!:Sprite;
  private runeFrame:SpriteFrame|null=null;
  private fxRoot!:Node;
  private fxFrames:SpriteFrame[]=new Array<SpriteFrame>(8);
  private shotFxPool:ShotFxInstance[]=[];
  private crystalHitFx!:Sprite;
  private readonly maxShotFx=160;
  private uiRoot!:Node;
  private uiFrames:SpriteFrame[]=new Array<SpriteFrame>(8);
  private uiSprites:Sprite[]=[];
  private settlementRoot!:Node;
  private settlementGraphics!:Graphics;
  private settlementPanel!:Sprite;
  private settlementHeader!:Sprite;
  private settlementCrystal!:Sprite;
  private infoPlate!:Graphics;
  private hintPlate!:Graphics;
  private settlementButtonSprite!:Sprite;
  private settlementButton!:Button;
  private settlementTitle!:Label;
  private settlementSubtitle!:Label;
  private settlementStats!:Label;
  private settlementButtonLabel!:Label;
  private settlementMenuSprite!:Sprite;
  private settlementMenuButton!:Button;
  private settlementMenuLabel!:Label;
  private settlementState='ready';
  private settlementLayoutKey='';
  private mainMenuRoot!:Node;
  private mainMenuGraphics!:Graphics;
  private mainMenuHeader!:Sprite;
  private mainMenuCrystal!:Sprite;
  private mainMenuStartSprite!:Sprite;
  private mainMenuStartButton!:Button;
  private mainMenuTitle!:Label;
  private mainMenuSubtitle!:Label;
  private mainMenuFeature!:Label;
  private mainMenuStartLabel!:Label;
  private mainMenuWallet!:Label;
  private mainMenuShopSprite!:Sprite;
  private mainMenuShopButton!:Button;
  private mainMenuShopLabel!:Label;
  private mainMenuLayoutKey='';
  private shopRoot!:Node;
  private shopGraphics!:Graphics;
  private shopTitle!:Label;
  private shopWallet!:Label;
  private shopMessage!:Label;
  private shopCloseSprite!:Sprite;
  private shopCloseButton!:Button;
  private shopCloseLabel!:Label;
  private shopRows:ShopRow[]=[];
  private shopLayoutKey='';
  private inMainMenu=true;
  private inShop=false;
  private enemyLayerFrames:Record<'grunt'|'boss',SpriteFrame[]>={grunt:new Array<SpriteFrame>(3),boss:new Array<SpriteFrame>(3)};
  private enemyMasterFrames:Record<'grunt'|'boss',SpriteFrame|null>={grunt:null,boss:null};
  private enemyKeyframes:Record<'grunt'|'boss',EnemyKeyframeSet|null>={grunt:null,boss:null};
  private ready=false;
  private failed=false;
  private towerPool:TowerInstance[]=[];
  private enemyPool:EnemyInstance[]=[];
  private previousTowers=0;
  private previousEnemies=0;
  private previousGiftEvents=0;
  private elapsed=0;
  private previousHealth=100;
  private previousGameState='ready';
  private coreHitTimer=0;
  private crystalDeathElapsed=0;
  private readonly normalTint=new Color(255,255,255,255);
  private readonly hurtTint=new Color(255,100,100,255);
  private readonly upgradeTint=new Color(255,220,120,255);
  private readonly deathTint=new Color(175,175,175,255);
  private readonly maxVisible=600;
  private readonly towerSources:Array<{id:TowerKind;names:[string,string,string]}>= [
    {id:'rapid',names:['连珠速射塔_底座','连珠速射塔_主体','连珠速射塔_双炮管']},
    {id:'heavy',names:['熔芯重炮塔_底座','熔芯重炮塔_主体','熔芯重炮塔_熔芯炮口']},
    {id:'frost',names:['寒霜喷射塔_底座','寒霜喷射塔_主体','寒霜喷射塔_寒霜喷射器']}
  ];
  private readonly crystalNames=['城防水晶_基座','城防水晶_晶体','城防水晶_能量符文'];

  onLoad():void {
    this.controller=this.node.getComponent(守城控制器);
    if(!this.controller){console.error('候选V5美术未找到守城控制器');return;}
    this.controller.useCandidateArt=false;
    profiler.hideStats();
    this.scheduleOnce(()=>profiler.hideStats(),.35);
    this.groundRoot=new Node('V5地面纹理层');
    this.groundRoot.layer=Layers.Enum.UI_2D;
    this.node.addChild(this.groundRoot);
    this.groundRoot.setSiblingIndex(1);
    const groundNode=new Node('无缝战场地砖');
    groundNode.layer=Layers.Enum.UI_2D;
    this.groundRoot.addChild(groundNode);
    groundNode.addComponent(UITransform).setContentSize(3200,3200);
    this.groundSprite=groundNode.addComponent(Sprite);
    this.groundSprite.sizeMode=Sprite.SizeMode.CUSTOM;
    this.groundSprite.type=Sprite.Type.TILED;
    this.groundSprite.trim=false;
    this.artRoot=new Node('V5分层战场精灵层');
    this.artRoot.layer=Layers.Enum.UI_2D;
    this.node.addChild(this.artRoot);
    this.artRoot.setSiblingIndex(3);
    this.runeRoot=new Node('V5中心符文平台');
    this.runeRoot.layer=Layers.Enum.UI_2D;
    this.artRoot.addChild(this.runeRoot);
    this.runeSprite=this.createSpriteNode(this.runeRoot,'中心符文平台',128);
    this.uiRoot=new Node('V5战斗UI皮肤层');
    this.uiRoot.layer=Layers.Enum.UI_2D;
    this.node.addChild(this.uiRoot);
    this.uiRoot.setSiblingIndex(4);
    this.crystalRoot=new Node('V5城防水晶');
    this.artRoot.addChild(this.crystalRoot);
    this.crystalSprites=[
      this.createSpriteNode(this.crystalRoot,'水晶基座',128),
      this.createSpriteNode(this.crystalRoot,'水晶晶体',128),
      this.createSpriteNode(this.crystalRoot,'水晶能量符文',128)
    ];
    this.fxRoot=new Node('V5像素弹道特效层');
    this.fxRoot.layer=Layers.Enum.UI_2D;
    this.artRoot.addChild(this.fxRoot);
    this.crystalHitFx=this.createSpriteNode(this.fxRoot,'水晶受击碎片FX',96);
    this.crystalHitFx.node.active=false;
    const uiDefs:Array<[string,number,number]>=[
      ['HUD顶部底板',480,96],['生命值条外框',192,32],['波次徽章',44,44],['能量水晶图标',44,44],
      ['主操作按钮',100,42],['观众按钮',100,42],['升级按钮',100,42],['离场按钮',100,42],['重开按钮',100,42],['炮塔升级图标',28,28]
    ];
    this.uiSprites=uiDefs.map(([name,w,h])=>this.createSpriteNode(this.uiRoot,name,w,h));
    const createPlate=(name:string):Graphics=>{
      const node=new Node(name);
      node.layer=Layers.Enum.UI_2D;
      this.uiRoot.addChild(node);
      node.addComponent(UITransform).setContentSize(480,32);
      return node.addComponent(Graphics);
    };
    this.infoPlate=createPlate('战场数据高对比度底板');
    this.hintPlate=createPlate('观众指引高对比度底板');
    this.createSettlementUi();
    this.createMainMenuUi();
    this.createShopUi();
    // HUD artwork is drawn above legacy labels by default; move text to the top
    // of the combat render stack so icons/buttons cannot occlude it on phones.
    for(const item of [...this.node.children]){
      if(item.name==='游戏状态'||item.name==='战场说明'||item.name==='操作提示'
        ||item.name.startsWith('按钮-')||item.name.startsWith('镜头-')){
        item.setSiblingIndex(this.node.children.length-1);
      }
    }
    this.controller.setInputBlocked(true);
    this.setBattleHudVisible(false);

    for(const source of this.towerSources)this.towerFrames.set(source.id,new Array<SpriteFrame>(3));
    const expected=3*3+3+6+2+1+1+8+8+1;
    let loaded=0;
    const complete=(assetPath:string,err:Error|null,frame:SpriteFrame|null,assign:(value:SpriteFrame)=>void):void=>{
      if(!this.isValid)return;
      if(err||!frame){
        if(!this.failed)console.error('V5候选美术资源加载失败，保留灰盒：',assetPath,err);
        this.failed=true;
        return;
      }
      assign(frame);
      loaded++;
      if(loaded===expected&&!this.failed){
        this.applyUiFrames();
        this.controller!.setCandidateHudContrast(true);
        this.ready=true;
        this.controller!.useCandidateArt=true;
        console.log('候选V5战场：9个炮塔图层、3个水晶图层、6个兽人回退分层、2个顶视Master、无缝地面、中心符文平台、8款UI和8款像素FX已载入');
      }
    };

    for(const source of this.towerSources){
      const frames=this.towerFrames.get(source.id)!;
      source.names.forEach((name,index)=>{
        const assetPath='正式战斗美术-v5/战斗单位/炮塔/'+name+'/spriteFrame';
        resources.load(assetPath,SpriteFrame,(err,asset)=>complete(assetPath,err,asset,frame=>{frames[index]=frame;}));
      });
    }
    this.crystalNames.forEach((name,index)=>{
      const assetPath='正式战斗美术-v5/战斗单位/水晶/'+name+'/spriteFrame';
      resources.load(assetPath,SpriteFrame,(err,asset)=>complete(assetPath,err,asset,frame=>{this.crystalFrames[index]=frame;}));
    });
    const enemyLayerSources:Array<{kind:'grunt'|'boss';names:[string,string,string]}>= [
      {kind:'grunt',names:['兽人小兵_身体护甲_母图层','兽人小兵_头部双臂_母图层','兽人小兵_武器配件_母图层']},
      {kind:'boss',names:['兽人首领_身体护甲_母图层','兽人首领_头部双臂_母图层','兽人首领_武器配件_母图层']}
    ];
    for(const source of enemyLayerSources){
      const frames=this.enemyLayerFrames[source.kind];
      source.names.forEach((name,index)=>{
        const assetPath='候选战斗美术-v5-RECOVERY-004/战斗单位/兽人/'+name+'/spriteFrame';
        resources.load(assetPath,SpriteFrame,(err,asset)=>complete(assetPath,err,asset,frame=>{frames[index]=frame;}));
      });
    }
    const enemyMasterPaths:Array<{kind:'grunt'|'boss';path:string}>=[
      {kind:'grunt',path:'候选战斗美术-v5-RECOVERY-004/战斗单位/兽人/兽人小兵_顶视MasterA/spriteFrame'},
      {kind:'boss',path:'候选战斗美术-v5-RECOVERY-004/战斗单位/兽人/兽人首领_顶视MasterB/spriteFrame'}
    ];
    for(const source of enemyMasterPaths){
      resources.load(source.path,SpriteFrame,(err,asset)=>complete(source.path,err,asset,frame=>{this.enemyMasterFrames[source.kind]=frame;}));
    }
    const enemyKeyframePaths:Array<{kind:'grunt'|'boss';path:string}>=[
      {kind:'grunt',path:'候选战斗美术-v5-RECOVERY-004/战斗单位/兽人/动画/兽人小兵-layer-keyframes'},
      {kind:'boss',path:'候选战斗美术-v5-RECOVERY-004/战斗单位/兽人/动画/兽人首领-layer-keyframes'}
    ];
    for(const source of enemyKeyframePaths){
      resources.load(source.path,JsonAsset,(err,asset)=>{
        if(!this.isValid)return;
        const raw=asset?.json as EnemyKeyframeSet|null;
        const valid=!err&&!!raw&&raw.frameCount===8&&raw.frameDurationMs===110
          &&!!raw.states?.walk&&!!raw.states?.hurt&&!!raw.states?.attack&&!!raw.states?.death
          &&[raw.states.walk,raw.states.hurt,raw.states.attack,raw.states.death].every(state=>state.frames?.length===8);
        if(valid){
          this.enemyKeyframes[source.kind]=raw;
          console.log('V5兽人离散关键帧已载入：',source.kind,source.path);
        }else{
          console.warn('V5兽人关键帧未载入，继续使用分层程序动画回退：',source.path,err);
        }
      });
    }
    const groundPath='候选战斗美术-v5-RECOVERY-004/环境/战场地砖/spriteFrame';
    resources.load(groundPath,SpriteFrame,(err,asset)=>complete(groundPath,err,asset,frame=>{this.groundFrame=frame;}));
    const runePath='候选战斗美术-v5-RECOVERY-004/环境/中心符文平台/spriteFrame';
    resources.load(runePath,SpriteFrame,(err,asset)=>complete(runePath,err,asset,frame=>{this.runeFrame=frame;this.runeSprite.spriteFrame=frame;}));
    const uiPaths=[
      '候选战斗美术-v5-RECOVERY-004/UI/面板/HUD顶部底板',
      '候选战斗美术-v5-RECOVERY-004/UI/按钮/主操作按钮',
      '候选战斗美术-v5-RECOVERY-004/UI/按钮/次操作按钮',
      '候选战斗美术-v5-RECOVERY-004/UI/按钮/离场按钮',
      '候选战斗美术-v5-RECOVERY-004/UI/面板/生命值条外框',
      '候选战斗美术-v5-RECOVERY-004/UI/图标/波次徽章',
      '候选战斗美术-v5-RECOVERY-004/UI/图标/能量水晶图标',
      '候选战斗美术-v5-RECOVERY-004/UI/图标/炮塔升级图标'
    ];
    uiPaths.forEach((base,index)=>{
      const assetPath=base+'/spriteFrame';
      resources.load(assetPath,SpriteFrame,(err,asset)=>complete(assetPath,err,asset,frame=>{this.uiFrames[index]=frame;}));
    });
    const settlementPanelPath='候选战斗美术-v5-RECOVERY-004/UI/面板/结算面板底板/spriteFrame';
    resources.load(settlementPanelPath,SpriteFrame,(err,asset)=>complete(settlementPanelPath,err,asset,frame=>{this.settlementPanel.spriteFrame=frame;}));
    const fxPaths=[
      '候选战斗美术-v5-RECOVERY-004/FX/连珠弹道',
      '候选战斗美术-v5-RECOVERY-004/FX/连珠枪口闪光',
      '候选战斗美术-v5-RECOVERY-004/FX/重炮炮弹',
      '候选战斗美术-v5-RECOVERY-004/FX/重炮命中特效',
      '候选战斗美术-v5-RECOVERY-004/FX/寒霜弹道',
      '候选战斗美术-v5-RECOVERY-004/FX/寒霜命中特效',
      '候选战斗美术-v5-RECOVERY-004/FX/水晶受击碎片',
      '候选战斗美术-v5-RECOVERY-004/FX/炮塔升级闪光'
    ];
    fxPaths.forEach((base,index)=>{
      const assetPath=base+'/spriteFrame';
      resources.load(assetPath,SpriteFrame,(err,asset)=>complete(assetPath,err,asset,frame=>{this.fxFrames[index]=frame;}));
    });
  }

  private createSpriteNode(parent:Node,name:string,size:number,height?:number):Sprite {
    const node=new Node(name);
    node.layer=Layers.Enum.UI_2D;
    parent.addChild(node);
    node.addComponent(UITransform).setContentSize(size,height===undefined?size:height);
    const sprite=node.addComponent(Sprite);
    sprite.sizeMode=Sprite.SizeMode.CUSTOM;
    sprite.trim=false;
    return sprite;
  }

  private applyUiFrames():void {
    if(this.groundFrame)this.groundSprite.spriteFrame=this.groundFrame;
    const map=[0,4,5,6,1,2,2,3,1,7];
    for(let i=0;i<this.uiSprites.length;i++){
      const frame=this.uiFrames[map[i]];
      if(frame)this.uiSprites[i].spriteFrame=frame;
    }
    if(this.uiFrames[0]){
      this.settlementHeader.spriteFrame=this.uiFrames[0];
      this.mainMenuHeader.spriteFrame=this.uiFrames[0];
    }
    if(this.uiFrames[6]){
      this.settlementCrystal.spriteFrame=this.uiFrames[6];
      this.mainMenuCrystal.spriteFrame=this.uiFrames[6];
    }
    if(this.uiFrames[1]){
      this.settlementButtonSprite.spriteFrame=this.uiFrames[1];
      this.mainMenuStartSprite.spriteFrame=this.uiFrames[1];
      this.mainMenuShopSprite.spriteFrame=this.uiFrames[1];
      for(const row of this.shopRows)row.buttonSprite.spriteFrame=this.uiFrames[1];
    }
    if(this.uiFrames[2]){
      this.settlementMenuSprite.spriteFrame=this.uiFrames[2];
      this.shopCloseSprite.spriteFrame=this.uiFrames[2];
    }
    this.layoutUi();
    this.layoutMainMenuUi();
    this.layoutShopUi();
  }

  private layoutUi():void {
    const half=view.getVisibleSize().height/2;
    const positions:Array<[number,number]>=[
      [0,half-53],[0,half-58],[-218,half-53],[218,half-53],
      [-205,-half+96],[-103,-half+96],[-1,-half+96],[101,-half+96],[203,-half+96],[-31,-half+96]
    ];
    const drawPlate=(plate:Graphics,y:number,width:number):void=>{
      plate.node.setPosition(0,y,0);
      plate.clear();
      plate.fillColor=new Color(11,28,44,239);
      plate.fillRect(-width/2,-16,width,32);
      plate.lineWidth=2;
      plate.strokeColor=new Color(205,151,74,255);
      plate.rect(-width/2,-16,width,32);
      plate.stroke();
    };
    drawPlate(this.infoPlate,half-115,480);
    drawPlate(this.hintPlate,-half+36,480);
    const upgradeLabel=this.node.getChildByName('按钮-升级');
    if(upgradeLabel)upgradeLabel.setPosition(12,-half+96,0);
    for(let i=0;i<this.uiSprites.length;i++){
      const p=positions[i];
      this.uiSprites[i].node.setPosition(p[0],p[1],0);
    }
  }


  private createSettlementUi():void {
    this.settlementRoot=new Node('V5结算弹层');
    this.settlementRoot.layer=Layers.Enum.UI_2D;
    this.node.addChild(this.settlementRoot);
    this.settlementRoot.setSiblingIndex(this.node.children.length-1);
    const size=view.getVisibleSize();
    this.settlementRoot.addComponent(UITransform).setContentSize(size.width,size.height);
    this.settlementGraphics=this.settlementRoot.addComponent(Graphics);
    this.settlementPanel=this.createSpriteNode(this.settlementRoot,'结算专用面板底板',440,540);
    this.settlementHeader=this.createSpriteNode(this.settlementRoot,'结算标题底板',320,104);
    this.settlementCrystal=this.createSpriteNode(this.settlementRoot,'结算水晶图标',56,56);
    this.settlementButtonSprite=this.createSpriteNode(this.settlementRoot,'再次守城按钮',220,72);
    this.settlementButton=this.settlementButtonSprite.node.addComponent(Button);
    this.settlementButton.transition=Button.Transition.SCALE;
    const handler=new EventHandler();
    handler.target=this.node;
    handler.component='守城控制器';
    handler.handler='restartFromSettlement';
    this.settlementButton.clickEvents=[handler];
    this.settlementMenuSprite=this.createSpriteNode(this.settlementRoot,'返回主界面按钮',190,54);
    this.settlementMenuButton=this.settlementMenuSprite.node.addComponent(Button);
    this.settlementMenuButton.transition=Button.Transition.SCALE;
    const menuHandler=new EventHandler();
    menuHandler.target=this.node;
    menuHandler.component='待审战场美术覆盖器';
    menuHandler.handler='returnToMainMenu';
    this.settlementMenuButton.clickEvents=[menuHandler];
    this.settlementTitle=this.createSettlementLabel(this.settlementHeader.node,'结算标题',280,60,32,new Color(239,247,255,255));
    this.settlementSubtitle=this.createSettlementLabel(this.settlementRoot,'结算说明',360,40,24,new Color(131,246,255,255));
    this.settlementStats=this.createSettlementLabel(this.settlementRoot,'结算统计',380,86,22,new Color(228,238,245,255));
    this.settlementButtonLabel=this.createSettlementLabel(this.settlementButtonSprite.node,'再次守城标签',200,48,24,new Color(255,255,255,255));
    this.settlementMenuLabel=this.createSettlementLabel(this.settlementMenuSprite.node,'返回主界面标签',170,40,20,new Color(224,236,244,255));
    this.settlementMenuLabel.string='返回主界面';
    this.settlementRoot.active=false;
  }

  private createMainMenuUi():void {
    this.mainMenuRoot=new Node('V5主界面');
    this.mainMenuRoot.layer=Layers.Enum.UI_2D;
    this.node.addChild(this.mainMenuRoot);
    this.mainMenuRoot.setSiblingIndex(this.node.children.length-1);
    const size=view.getVisibleSize();
    this.mainMenuRoot.addComponent(UITransform).setContentSize(size.width,size.height);
    this.mainMenuGraphics=this.mainMenuRoot.addComponent(Graphics);
    this.mainMenuHeader=this.createSpriteNode(this.mainMenuRoot,'主界面标题底板',360,118);
    this.mainMenuCrystal=this.createSpriteNode(this.mainMenuRoot,'主界面水晶图标',88,88);
    this.mainMenuStartSprite=this.createSpriteNode(this.mainMenuRoot,'开始守城按钮',240,76);
    this.mainMenuStartButton=this.mainMenuStartSprite.node.addComponent(Button);
    this.mainMenuStartButton.transition=Button.Transition.SCALE;
    const startHandler=new EventHandler();
    startHandler.target=this.node;
    startHandler.component='待审战场美术覆盖器';
    startHandler.handler='beginFromMainMenu';
    this.mainMenuStartButton.clickEvents=[startHandler];
    this.mainMenuTitle=this.createSettlementLabel(this.mainMenuHeader.node,'主界面标题',340,68,34,new Color(239,247,255,255));
    this.mainMenuSubtitle=this.createSettlementLabel(this.mainMenuRoot,'主界面副标题',420,52,23,new Color(131,246,255,255));
    this.mainMenuFeature=this.createSettlementLabel(this.mainMenuRoot,'主界面玩法说明',420,96,20,new Color(224,236,244,255));
    this.mainMenuStartLabel=this.createSettlementLabel(this.mainMenuStartSprite.node,'开始守城标签',220,52,25,new Color(255,255,255,255));
    this.mainMenuWallet=this.createSettlementLabel(this.mainMenuRoot,'主界面守城币',300,42,21,new Color(240,196,107,255));
    this.mainMenuShopSprite=this.createSpriteNode(this.mainMenuRoot,'商店入口按钮',220,58);
    this.mainMenuShopButton=this.mainMenuShopSprite.node.addComponent(Button);
    this.mainMenuShopButton.transition=Button.Transition.SCALE;
    const shopHandler=new EventHandler();
    shopHandler.target=this.node;
    shopHandler.component='待审战场美术覆盖器';
    shopHandler.handler='openShop';
    this.mainMenuShopButton.clickEvents=[shopHandler];
    this.mainMenuShopLabel=this.createSettlementLabel(this.mainMenuShopSprite.node,'商店入口标签',200,44,22,new Color(255,255,255,255));
    this.mainMenuTitle.string='直播炮塔守城';
    this.mainMenuSubtitle.string='守住中央水晶 · 击退三波兽人';
    this.mainMenuFeature.string='三系炮塔自动攻击\n观众加入增塔 · 礼物驱动升级';
    this.mainMenuStartLabel.string='开始守城';
    this.mainMenuShopLabel.string='战备商店';
    this.refreshEconomyUi();
    this.mainMenuRoot.active=true;
    this.layoutMainMenuUi();
  }

  private createShopUi():void {
    this.shopRoot=new Node('V5战备商店');
    this.shopRoot.layer=Layers.Enum.UI_2D;
    this.node.addChild(this.shopRoot);
    this.shopRoot.setSiblingIndex(this.node.children.length-1);
    const size=view.getVisibleSize();
    this.shopRoot.addComponent(UITransform).setContentSize(size.width,size.height);
    this.shopGraphics=this.shopRoot.addComponent(Graphics);
    this.shopTitle=this.createSettlementLabel(this.shopRoot,'商店标题',360,54,30,new Color(239,247,255,255));
    this.shopWallet=this.createSettlementLabel(this.shopRoot,'商店守城币',320,40,21,new Color(240,196,107,255));
    this.shopMessage=this.createSettlementLabel(this.shopRoot,'商店提示',360,42,18,new Color(131,246,255,255));
    const defs:Array<{id:ShopId;handler:string}>=[
      {id:'coreShield',handler:'buyCoreShield'},
      {id:'fireControl',handler:'buyFireControl'},
      {id:'viewerBoost',handler:'buyViewerBoost'}
    ];
    for(const def of defs){
      const info=this.createSettlementLabel(this.shopRoot,'商品-'+def.id,400,68,18,new Color(224,236,244,255));
      const buttonSprite=this.createSpriteNode(this.shopRoot,'购买-'+def.id,190,48);
      const button=buttonSprite.node.addComponent(Button);
      button.transition=Button.Transition.SCALE;
      const handler=new EventHandler();
      handler.target=this.node;handler.component='待审战场美术覆盖器';handler.handler=def.handler;
      button.clickEvents=[handler];
      const buttonLabel=this.createSettlementLabel(buttonSprite.node,'购买标签-'+def.id,174,38,18,new Color(255,255,255,255));
      this.shopRows.push({id:def.id,info,buttonSprite,button,buttonLabel});
    }
    this.shopCloseSprite=this.createSpriteNode(this.shopRoot,'关闭商店按钮',190,52);
    this.shopCloseButton=this.shopCloseSprite.node.addComponent(Button);
    this.shopCloseButton.transition=Button.Transition.SCALE;
    const closeHandler=new EventHandler();
    closeHandler.target=this.node;closeHandler.component='待审战场美术覆盖器';closeHandler.handler='closeShop';
    this.shopCloseButton.clickEvents=[closeHandler];
    this.shopCloseLabel=this.createSettlementLabel(this.shopCloseSprite.node,'关闭商店标签',170,38,20,new Color(224,236,244,255));
    this.shopTitle.string='战备商店';
    this.shopCloseLabel.string='返回主界面';
    this.shopMessage.string='永久战备在下一局生效';
    this.shopRoot.active=false;
    this.refreshShopUi();
    this.layoutShopUi();
  }

  private createSettlementLabel(parent:Node,name:string,width:number,height:number,fontSize:number,color:Color):Label {
    const node=new Node(name);
    node.layer=Layers.Enum.UI_2D;
    parent.addChild(node);
    node.addComponent(UITransform).setContentSize(width,height);
    const label=node.addComponent(Label);
    label.fontSize=fontSize;
    label.lineHeight=fontSize+10;
    label.horizontalAlign=HorizontalTextAlignment.CENTER;
    label.verticalAlign=VerticalTextAlignment.CENTER;
    label.color=color;
    return label;
  }

  public openShop():void {
    if(!this.controller||!this.inMainMenu||!this.controller.platformSnapshot().shopAllowed)return;
    this.inShop=true;
    this.mainMenuRoot.active=false;
    this.shopRoot.active=true;
    this.refreshShopUi();
    this.layoutShopUi();
  }

  public closeShop():void {
    if(!this.inMainMenu)return;
    this.inShop=false;
    this.shopRoot.active=false;
    this.mainMenuRoot.active=true;
    this.refreshEconomyUi();
    this.layoutMainMenuUi();
  }

  public buyCoreShield():void {this.buyShop('coreShield');}
  public buyFireControl():void {this.buyShop('fireControl');}
  public buyViewerBoost():void {this.buyShop('viewerBoost');}

  private buyShop(id:ShopId):void {
    if(!this.controller)return;
    const result=this.controller.buyShopItem(id);
    this.shopMessage.string=result.ok?'购买成功 · 下一局生效':result.reason==='platform-disabled'?'当前直播玩法模式禁用商店':result.reason==='insufficient-coins'?'守城币不足':result.reason==='max-level'?'已满级':'购买失败';
    this.refreshShopUi();
    this.refreshEconomyUi();
  }

  private refreshEconomyUi():void {
    if(!this.controller||!this.mainMenuWallet)return;
    const platform=this.controller.platformSnapshot();
    const allowed=platform.persistentEconomyAllowed;
    this.mainMenuWallet.node.active=allowed;
    this.mainMenuShopSprite.node.active=platform.shopAllowed;
    if(!platform.shopAllowed&&this.inShop){
      this.inShop=false;
      this.shopRoot.active=false;
      this.mainMenuRoot.active=true;
    }
    if(allowed){
      const profile=this.controller.profileSnapshot();
      this.mainMenuWallet.string='守城币 '+profile.coins;
      this.mainMenuFeature.string='三系炮塔自动攻击\n观众加入增塔 · 礼物驱动升级';
    }else{
      this.mainMenuFeature.string='评论“加入”参与守城\n礼物升级 · 直播玩法不设商城';
    }
  }

  private refreshShopUi():void {
    if(!this.controller||!this.shopWallet)return;
    const profile=this.controller.profileSnapshot();
    this.shopWallet.string='守城币 '+profile.coins;
    const catalog=this.controller.shopCatalog();
    for(const row of this.shopRows){
      const item=catalog.find(x=>x.id===row.id);
      if(!item)continue;
      row.info.string=item.name+'  Lv.'+item.level+'/'+item.maxLevel+'\n'+item.description;
      row.buttonLabel.string=item.cost===null?'已满级':'购买 '+item.cost;
      row.button.interactable=item.canBuy;
      row.buttonLabel.color=item.canBuy?new Color(255,255,255,255):new Color(145,158,168,255);
    }
  }

  public beginFromMainMenu():void {
    if(!this.controller)return;
    this.inMainMenu=false;
    this.inShop=false;
    this.shopRoot.active=false;
    this.mainMenuRoot.active=false;
    this.artRoot.active=true;
    this.controller.setInputBlocked(false);
    this.controller.startNewRunFromMenu();
    this.setBattleHudVisible(true);
  }

  public returnToMainMenu():void {
    if(!this.controller)return;
    this.controller.returnToMenuState();
    this.controller.setInputBlocked(true);
    this.inMainMenu=true;
    this.inShop=false;
    this.settlementRoot.active=false;
    this.shopRoot.active=false;
    this.mainMenuRoot.active=true;
    this.refreshEconomyUi();
    this.artRoot.active=false;
    this.setBattleHudVisible(false);
    this.layoutMainMenuUi();
  }

  private setBattleHudVisible(visible:boolean):void {
    this.uiRoot.active=visible;
    for(const child of this.node.children){
      const name=child.name;
      if(name==='游戏状态'||name==='战场说明'||name==='操作提示'||name.startsWith('按钮-')||name.startsWith('镜头-'))child.active=visible;
    }
  }

  private layoutMainMenuUi():void {
    if(!this.mainMenuRoot)return;
    const size=view.getVisibleSize();
    const panelWidth=Math.min(460,size.width-28);
    const panelHeight=Math.min(620,size.height-80);
    this.mainMenuRoot.getComponent(UITransform)!.setContentSize(size.width,size.height);
    this.mainMenuHeader.node.getComponent(UITransform)!.setContentSize(Math.min(360,panelWidth-36),118);
    this.mainMenuHeader.node.setPosition(0,panelHeight/2-78,0);
    this.mainMenuTitle.node.getComponent(UITransform)!.setContentSize(Math.min(340,panelWidth-50),68);
    this.mainMenuTitle.node.setPosition(0,0,0);
    this.mainMenuCrystal.node.setPosition(0,panelHeight/2-196,0);
    this.mainMenuSubtitle.node.setPosition(0,42,0);
    this.mainMenuFeature.node.getComponent(UITransform)!.setContentSize(Math.min(420,panelWidth-44),80);
    this.mainMenuFeature.node.setPosition(0,-30,0);
    this.mainMenuWallet.node.getComponent(UITransform)!.setContentSize(Math.min(300,panelWidth-70),36);
    this.mainMenuWallet.node.setPosition(0,-100,0);
    this.mainMenuShopSprite.node.getComponent(UITransform)!.setContentSize(210,52);
    this.mainMenuShopSprite.node.setPosition(0,-panelHeight/2+158,0);
    this.mainMenuShopLabel.node.getComponent(UITransform)!.setContentSize(190,36);
    this.mainMenuShopLabel.node.setPosition(0,0,0);
    this.mainMenuStartSprite.node.getComponent(UITransform)!.setContentSize(230,68);
    this.mainMenuStartSprite.node.setPosition(0,-panelHeight/2+96,0);
    this.mainMenuStartLabel.node.getComponent(UITransform)!.setContentSize(210,44);
    this.mainMenuStartLabel.node.setPosition(0,0,0);
    const g=this.mainMenuGraphics;
    g.clear();
    g.fillColor=new Color(7,13,22,242);
    g.fillRect(-size.width/2,-size.height/2,size.width,size.height);
    const x=-panelWidth/2,y=-panelHeight/2;
    g.fillColor=new Color(17,32,46,252);
    g.fillRect(x,y,panelWidth,panelHeight);
    g.lineWidth=10;g.strokeColor=new Color(52,61,74,255);g.rect(x,y,panelWidth,panelHeight);g.stroke();
    g.lineWidth=4;g.strokeColor=new Color(199,141,59,255);g.rect(x+5,y+5,panelWidth-10,panelHeight-10);g.stroke();
    g.lineWidth=2;g.strokeColor=new Color(240,196,107,255);g.rect(x+12,y+12,panelWidth-24,panelHeight-24);g.stroke();
    g.fillColor=new Color(39,62,86,255);
    g.fillRect(x+18,y+panelHeight-160,panelWidth-36,94);
    g.fillColor=new Color(66,216,238,255);
    g.fillRect(x+18,-3,5,42);
    g.fillRect(x+panelWidth-23,-3,5,42);
    g.fillColor=new Color(199,141,59,255);
    g.fillRect(x+34,y+46,56,4);
    g.fillRect(x+panelWidth-90,y+46,56,4);
    this.mainMenuLayoutKey=size.width+'x'+size.height;
  }

  private layoutShopUi():void {
    if(!this.shopRoot)return;
    const size=view.getVisibleSize();
    const panelWidth=Math.min(470,size.width-28);
    const panelHeight=Math.min(690,size.height-54);
    this.shopRoot.getComponent(UITransform)!.setContentSize(size.width,size.height);
    this.shopTitle.node.setPosition(0,panelHeight/2-58,0);
    this.shopWallet.node.setPosition(0,panelHeight/2-108,0);
    this.shopMessage.node.setPosition(0,panelHeight/2-150,0);
    const rowY=[104,-18,-140];
    for(let i=0;i<this.shopRows.length;i++){
      const row=this.shopRows[i];
      row.info.node.getComponent(UITransform)!.setContentSize(Math.min(400,panelWidth-36),68);
      row.info.node.setPosition(0,rowY[i]+22,0);
      row.buttonSprite.node.getComponent(UITransform)!.setContentSize(190,48);
      row.buttonSprite.node.setPosition(0,rowY[i]-32,0);
      row.buttonLabel.node.setPosition(0,0,0);
    }
    this.shopCloseSprite.node.getComponent(UITransform)!.setContentSize(190,52);
    this.shopCloseSprite.node.setPosition(0,-panelHeight/2+50,0);
    this.shopCloseLabel.node.setPosition(0,0,0);
    const g=this.shopGraphics;g.clear();
    g.fillColor=new Color(7,13,22,245);g.fillRect(-size.width/2,-size.height/2,size.width,size.height);
    const x=-panelWidth/2,y=-panelHeight/2;
    g.fillColor=new Color(17,32,46,252);g.fillRect(x,y,panelWidth,panelHeight);
    g.lineWidth=10;g.strokeColor=new Color(52,61,74,255);g.rect(x,y,panelWidth,panelHeight);g.stroke();
    g.lineWidth=4;g.strokeColor=new Color(199,141,59,255);g.rect(x+5,y+5,panelWidth-10,panelHeight-10);g.stroke();
    g.lineWidth=2;g.strokeColor=new Color(240,196,107,255);g.rect(x+12,y+12,panelWidth-24,panelHeight-24);g.stroke();
    g.fillColor=new Color(39,62,86,255);g.fillRect(x+18,y+panelHeight-176,panelWidth-36,116);
    this.shopLayoutKey=size.width+'x'+size.height;
  }

  private syncSettlementUi(gameState:string,wave:number,kills:number,health:number,maxHealth:number,coins:number,lastReward:number):void {
    if(this.inMainMenu){
      this.setBattleHudVisible(false);
      this.artRoot.active=false;
      if(this.settlementRoot.active)this.settlementRoot.active=false;
      this.refreshEconomyUi();
      const menuSize=view.getVisibleSize();
      const menuKey=menuSize.width+'x'+menuSize.height;
      if(this.inShop){
        this.mainMenuRoot.active=false;this.shopRoot.active=true;this.refreshShopUi();
        if(this.shopLayoutKey!==menuKey)this.layoutShopUi();
      }else{
        this.shopRoot.active=false;if(!this.mainMenuRoot.active)this.mainMenuRoot.active=true;
        if(this.mainMenuLayoutKey!==menuKey)this.layoutMainMenuUi();
      }
      return;
    }
    this.shopRoot.active=false;
    this.mainMenuRoot.active=false;
    this.artRoot.active=true;
    const terminal=gameState==='win'||gameState==='lose';
    if(!terminal){
      this.setBattleHudVisible(true);
      if(this.settlementRoot.active){
        this.settlementRoot.active=false;
        this.settlementState=gameState;
      }
      return;
    }
    this.setBattleHudVisible(false);
    const size=view.getVisibleSize();
    const layoutKey=size.width+'x'+size.height;
    if(!this.settlementRoot.active||this.settlementState!==gameState||this.settlementLayoutKey!==layoutKey){
      this.settlementRoot.active=true;
      this.settlementState=gameState;
      this.layoutSettlementUi();
    }
    this.settlementTitle.string=gameState==='lose'?'守城失败':'守城成功';
    this.settlementSubtitle.string=gameState==='lose'?'城防水晶已被突破':'三波兽人已被击退';
    const economyAllowed=this.controller.platformSnapshot().persistentEconomyAllowed;
    this.settlementStats.string=economyAllowed
      ? (gameState==='lose'
        ? '本局击退 '+kills+' 只兽人\n抵达第 '+wave+' 波 · 水晶 0/'+maxHealth+'\n奖励 +'+lastReward+' 守城币 · 余额 '+coins
        : '本局击退 '+kills+' 只兽人\n水晶剩余 '+health+'/'+maxHealth+'\n奖励 +'+lastReward+' 守城币 · 余额 '+coins)
      : (gameState==='lose'
        ? '本局击退 '+kills+' 只兽人\n抵达第 '+wave+' 波 · 水晶 0/'+maxHealth
        : '本局击退 '+kills+' 只兽人\n水晶剩余 '+health+'/'+maxHealth);
    this.settlementButtonLabel.string='再次守城';
  }

  private layoutSettlementUi():void {
    const size=view.getVisibleSize();
    const panelWidth=Math.min(440,size.width-32);
    const panelHeight=Math.min(540,size.height-180);
    this.settlementRoot.getComponent(UITransform)!.setContentSize(size.width,size.height);
    this.settlementPanel.node.getComponent(UITransform)!.setContentSize(panelWidth,panelHeight);
    this.settlementPanel.node.setPosition(0,0,0);
    this.settlementHeader.node.getComponent(UITransform)!.setContentSize(Math.min(320,panelWidth-36),104);
    this.settlementHeader.node.setPosition(0,panelHeight/2-60,0);
    this.settlementCrystal.node.setPosition(0,panelHeight/2-150,0);
    this.settlementSubtitle.node.setPosition(0,48,0);
    this.settlementStats.node.getComponent(UITransform)!.setContentSize(400,112);
    this.settlementStats.fontSize=20;this.settlementStats.lineHeight=30;
    this.settlementStats.node.setPosition(0,-18,0);
    this.settlementButtonSprite.node.getComponent(UITransform)!.setContentSize(220,68);
    this.settlementButtonSprite.node.setPosition(0,-panelHeight/2+126,0);
    this.settlementMenuSprite.node.getComponent(UITransform)!.setContentSize(190,52);
    this.settlementMenuSprite.node.setPosition(0,-panelHeight/2+54,0);
    this.settlementTitle.node.getComponent(UITransform)!.setContentSize(280,60);
    this.settlementTitle.node.setPosition(0,0,0);
    this.settlementButtonLabel.node.getComponent(UITransform)!.setContentSize(200,46);
    this.settlementButtonLabel.node.setPosition(0,0,0);
    this.settlementMenuLabel.node.getComponent(UITransform)!.setContentSize(170,38);
    this.settlementMenuLabel.node.setPosition(0,0,0);
    const g=this.settlementGraphics;
    g.clear();
    // Keep only the full-screen dim backdrop here; the dedicated transparent pixel panel is a real Sprite child.
    g.fillColor=new Color(7,13,22,220);
    g.fillRect(-size.width/2,-size.height/2,size.width,size.height);
    this.settlementLayoutKey=size.width+'x'+size.height;
  }

  private createTower():TowerInstance {
    const node=new Node('V5炮塔分层实例');
    node.layer=Layers.Enum.UI_2D;
    this.artRoot.addChild(node);
    const sprites=[
      this.createSpriteNode(node,'底座',128),
      this.createSpriteNode(node,'主体',128),
      this.createSpriteNode(node,'武器',128)
    ];
    const fx=this.createSpriteNode(node,'升级闪光FX',96);
    fx.spriteFrame=this.fxFrames[7]||null;
    fx.node.active=false;
    return {node,sprites,fx,kind:null,level:1,upgradeTimer:0};
  }

  private createEnemy():EnemyInstance {
    const node=new Node('兽人分层实例');
    node.layer=Layers.Enum.UI_2D;
    this.artRoot.addChild(node);
    node.addComponent(UITransform).setContentSize(128,128);
    const master=this.createSpriteNode(node,'顶视Master',128);
    const sprites=[
      this.createSpriteNode(node,'身体护甲',128),
      this.createSpriteNode(node,'头部双臂',128),
      this.createSpriteNode(node,'武器配件',128)
    ];
    master.node.active=false;
    return {node,master,sprites,frame:-1,kind:null,mobRef:null,lastHp:0,hurtTimer:0,attackTimer:0,deathTimer:0,ghost:false,animState:'walk',lastX:0,lastY:0,lastScale:1,lastDistance:Infinity};
  }

  private applyEnemy(instance:EnemyInstance,kind:'grunt'|'boss'):void {
    if(instance.kind===kind)return;
    const master=this.enemyMasterFrames[kind];
    const frames=this.enemyLayerFrames[kind];
    // Prefer reference-locked same-canvas layers. Composite Master is fallback only;
    // it must not silently disable the editable runtime layers.
    const layersReady=!!frames&&frames.length===3&&frames.every(frame=>!!frame);
    if(layersReady){
      instance.master.node.active=false;
      for(let i=0;i<3;i++){instance.sprites[i].spriteFrame=frames[i];instance.sprites[i].node.active=true;}
    }else if(master){
      instance.master.spriteFrame=master;instance.master.node.active=true;
      for(const sprite of instance.sprites)sprite.node.active=false;
    }else{
      instance.node.active=false;return;
    }
    instance.kind=kind;
  }

  private applyEnemyKeyframe(instance:EnemyInstance,state:EnemyAnimState,frameIndex:number,x:number,y:number,scale:number):boolean {
    if(!instance.kind||!instance.sprites.every(sprite=>sprite.node.active))return false;
    const set=this.enemyKeyframes[instance.kind];
    const frames=set?.states?.[state]?.frames;
    if(!frames||frames.length!==8)return false;
    const pose=frames[Math.max(0,Math.min(7,frameIndex|0))];
    if(!pose||!pose.root||!pose.layers||pose.layers.length<3)return false;
    instance.node.setPosition(x+pose.root.x*scale,y+pose.root.y*scale,0);
    instance.node.setScale(scale*pose.root.sx,scale*pose.root.sy,1);
    instance.node.setRotationFromEuler(0,0,pose.root.r);
    const tint=state==='hurt'?this.hurtTint:state==='death'?this.deathTint:this.normalTint;
    for(let i=0;i<3;i++){
      const layer=pose.layers[i];
      const sprite=instance.sprites[i];
      sprite.color=tint;
      sprite.node.setPosition(layer.x,layer.y,0);
      sprite.node.setRotationFromEuler(0,0,layer.r);
      sprite.node.setScale(layer.sx,layer.sy,1);
    }
    instance.master.color=tint;
    instance.master.node.setPosition(0,0,0);
    instance.master.node.setRotationFromEuler(0,0,0);
    instance.master.node.setScale(1,1,1);
    return true;
  }

  private enemyStateFrame(entry:EnemyInstance,state:EnemyAnimState,phase:number):number {
    if(state==='hurt')return Math.max(0,Math.min(7,Math.floor((1-entry.hurtTimer/.18)*8)));
    if(state==='death')return Math.max(0,Math.min(7,Math.floor((1-entry.deathTimer/.32)*8)));
    if(state==='attack'&&entry.ghost&&entry.attackTimer>0)return Math.max(0,Math.min(7,Math.floor((1-entry.attackTimer/.16)*8)));
    return phase&7;
  }

  private applyTower(instance:TowerInstance,kind:TowerKind):void {
    if(instance.kind===kind)return;
    const frames=this.towerFrames.get(kind);
    if(!frames||frames.length!==3||frames.some(frame=>!frame)){instance.node.active=false;return;}
    for(let i=0;i<3;i++)instance.sprites[i].spriteFrame=frames[i];
    instance.fx.spriteFrame=this.fxFrames[7]||null;
    instance.kind=kind;
  }

  private createShotFx():ShotFxInstance {
    const root=new Node('V5弹道FX实例');
    root.layer=Layers.Enum.UI_2D;
    this.fxRoot.addChild(root);
    const projectile=this.createSpriteNode(root,'弹体',64);
    const muzzle=this.createSpriteNode(root,'枪口闪光',64);
    const impact=this.createSpriteNode(root,'命中特效',64);
    root.active=false;
    return {root,projectile,muzzle,impact};
  }

  private renderShotFx(shots:readonly {x:number;y:number;tx:number;ty:number;age:number;type:'连珠'|'重炮'|'寒霜'}[],camX:number,camY:number,zoom:number,maxX:number,maxY:number):void {
    let used=0;
    for(const shot of shots){
      if(used>=this.maxShotFx)break;
      const progress=Math.max(0,Math.min(1,shot.age/.13));
      const wx=shot.x+(shot.tx-shot.x)*progress;
      const wy=shot.y+(shot.ty-shot.y)*progress;
      const x=(wx-camX)*zoom,y=(wy-camY)*zoom;
      const sx=(shot.x-camX)*zoom,sy=(shot.y-camY)*zoom;
      const tx=(shot.tx-camX)*zoom,ty=(shot.ty-camY)*zoom;
      if(Math.abs(x)>maxX+80||Math.abs(y)>maxY+80)continue;
      if(used===this.shotFxPool.length)this.shotFxPool.push(this.createShotFx());
      const entry=this.shotFxPool[used++];
      entry.root.active=true;
      const rapid=shot.type==='连珠',heavy=shot.type==='重炮';
      const projectileIndex=rapid?0:heavy?2:4;
      const impactIndex=rapid?1:heavy?3:5;
      entry.projectile.spriteFrame=this.fxFrames[projectileIndex];
      entry.muzzle.spriteFrame=this.fxFrames[impactIndex];
      entry.impact.spriteFrame=this.fxFrames[impactIndex];
      entry.projectile.node.active=shot.age<.145;
      entry.muzzle.node.active=shot.age<.045;
      entry.impact.node.active=shot.age>=.115;
      entry.projectile.node.setPosition(x,y,0);
      entry.muzzle.node.setPosition(sx,sy,0);
      entry.impact.node.setPosition(tx,ty,0);
      const angle=Math.atan2(shot.ty-shot.y,shot.tx-shot.x)*180/Math.PI;
      entry.projectile.node.setRotationFromEuler(0,0,angle);
      const ps=(rapid?.34:heavy?.46:.40)*zoom;
      const ms=(rapid?.28:heavy?.22:.24)*zoom;
      const is=(rapid?.30:heavy?.58:.48)*zoom;
      entry.projectile.node.setScale(ps,ps,1);
      entry.muzzle.node.setScale(ms,ms,1);
      entry.impact.node.setScale(is,is,1);
    }
    for(let i=used;i<this.shotFxPool.length;i++)this.shotFxPool[i].root.active=false;
  }

  update(dt:number):void {
    if(!this.ready||!this.controller)return;
    const s=this.controller.candidateArtState();
    const giftIncreased=s.giftEvents>this.previousGiftEvents;
    this.syncSettlementUi(s.gameState,s.wave,s.kills,s.health,s.maxHealth,s.coins,s.lastReward);
    const previousState=this.previousGameState;
    if(s.gameState==='ready'&&previousState!=='ready'){
      for(const entry of this.enemyPool){
        entry.mobRef=null;entry.ghost=false;entry.hurtTimer=0;entry.attackTimer=0;entry.deathTimer=0;entry.animState='walk';
        entry.node.active=false;entry.node.setPosition(0,0,0);entry.node.setRotationFromEuler(0,0,0);entry.node.setScale(1,1,1);
        for(const sprite of entry.sprites){sprite.color=this.normalTint;sprite.node.setPosition(0,0,0);sprite.node.setRotationFromEuler(0,0,0);sprite.node.setScale(1,1,1);}
      }
      this.crystalDeathElapsed=0;
    }
    if(s.gameState==='lose'&&previousState!=='lose')this.crystalDeathElapsed=0;
    const healthDropped=s.health<this.previousHealth;
    if(healthDropped)this.coreHitTimer=.24;
    this.coreHitTimer=Math.max(0,this.coreHitTimer-dt);
    if(s.gameState==='lose')this.crystalDeathElapsed+=dt;
    this.previousHealth=s.health;
    this.previousGameState=s.gameState;
    this.layoutUi();
    this.groundRoot.setPosition(-s.camX*s.zoom,-s.camY*s.zoom,0);
    this.groundRoot.setScale(s.zoom,s.zoom,1);
    this.runeRoot.active=!!this.runeFrame;
    this.runeRoot.setPosition(-s.camX*s.zoom,-s.camY*s.zoom,0);
    this.runeRoot.setScale(.72*s.zoom,.72*s.zoom,1);
    this.elapsed+=Math.min(.1,Math.max(0,dt));
    const phase=Math.floor(this.elapsed/.11)%8;
    for(let i=0;i<3;i++)if(this.crystalSprites[i].spriteFrame!==this.crystalFrames[i])this.crystalSprites[i].spriteFrame=this.crystalFrames[i];
    this.crystalRoot.active=true;
    this.crystalRoot.setPosition(-s.camX*s.zoom,-s.camY*s.zoom,0);
    const coreDestroyed=s.gameState==='lose';
    const collapse=coreDestroyed?Math.max(.25,1-Math.min(.75,this.crystalDeathElapsed*1.1)):1;
    this.crystalRoot.setScale(.66*s.zoom*collapse,.66*s.zoom*collapse,1);
    const glow=this.coreHitTimer>0?1.15:1+Math.sin(this.elapsed*4)*.025;
    this.crystalSprites[2].node.setScale(glow,glow,1);
    this.crystalSprites[1].color=coreDestroyed?this.deathTint:this.coreHitTimer>0?this.hurtTint:this.normalTint;
    this.crystalHitFx.spriteFrame=this.fxFrames[6]||null;
    this.crystalHitFx.node.active=this.coreHitTimer>0&&!coreDestroyed;
    this.crystalHitFx.node.setPosition(-s.camX*s.zoom,-s.camY*s.zoom,0);
    const hitScale=.42*s.zoom*(1+this.coreHitTimer*1.8);
    this.crystalHitFx.node.setScale(hitScale,hitScale,1);

    const maxX=255;
    const maxY=Math.max(0,view.getVisibleSize().height/2-145);
    let usedTowers=0;
    for(const tower of s.towers){
      const x=(tower.x-s.camX)*s.zoom,y=(tower.y-s.camY)*s.zoom;
      if(Math.abs(x)>maxX||Math.abs(y)>maxY)continue;
      if(usedTowers>=this.maxVisible)break;
      if(usedTowers===this.towerPool.length)this.towerPool.push(this.createTower());
      const entry=this.towerPool[usedTowers++];
      const kind:TowerKind=tower.type==='连珠'?'rapid':tower.type==='重炮'?'heavy':'frost';
      const kindChanged=entry.kind!==kind;
      this.applyTower(entry,kind);
      if(kindChanged){entry.level=tower.level;entry.upgradeTimer=giftIncreased&&!tower.ownerId.startsWith('base-')?.62:0;}
      else if(entry.level!==tower.level){entry.level=tower.level;entry.upgradeTimer=.62;}
      entry.upgradeTimer=Math.max(0,entry.upgradeTimer-dt);
      entry.node.active=true;
      entry.node.setPosition(x,y,0);
      const scale=(.40+Math.min(4,tower.level-1)*.018)*s.zoom;
      entry.node.setScale(scale,scale,1);
      const firing=tower.cd>0&&phase%2===0;
      const upgrade=entry.upgradeTimer>0;
      const idlePulse=1+Math.sin(this.elapsed*2.5+tower.x*.012)*.012;
      entry.sprites[1].node.setScale(idlePulse,idlePulse*(upgrade?1.07:1),1);
      entry.sprites[1].color=upgrade?this.upgradeTint:this.normalTint;
      entry.sprites[0].color=this.normalTint;
      const weaponPulse=(firing?1.055:1)*(upgrade?1.08:1);
      entry.sprites[2].node.setScale(weaponPulse,weaponPulse,1);
      entry.sprites[2].node.setPosition(0,firing?2:0,0);
      entry.fx.node.active=upgrade;
      if(upgrade){
        const fxScale=(.58+Math.sin(this.elapsed*22)*.06)*s.zoom;
        entry.fx.node.setScale(fxScale,fxScale,1);
        entry.fx.node.setRotationFromEuler(0,0,this.elapsed*36%360);
      }
    }
    for(let i=usedTowers;i<this.previousTowers;i++)this.towerPool[i].node.active=false;
    this.previousTowers=usedTowers;
    this.renderShotFx(s.shots,s.camX,s.camY,s.zoom,maxX,maxY);
    this.fxRoot.setSiblingIndex(this.artRoot.children.length-1);

    const liveRefs=new Set<object>(s.enemies as readonly object[]);
    let lostForAttack:EnemyInstance|null=null;
    for(const entry of this.enemyPool){
      if(entry.mobRef&&!liveRefs.has(entry.mobRef)){
        if(!lostForAttack||entry.lastDistance<lostForAttack.lastDistance)lostForAttack=entry;
        entry.mobRef=null;entry.ghost=true;entry.animState='death';entry.attackTimer=0;entry.deathTimer=.32;
      }
    }
    if(healthDropped&&lostForAttack){
      lostForAttack.animState='attack';lostForAttack.attackTimer=.16;lostForAttack.deathTimer=.48;
    }
    for(const mob of s.enemies){
      const x=(mob.x-s.camX)*s.zoom,y=(mob.y-s.camY)*s.zoom;
      const distance=Math.hypot(mob.x,mob.y);
      const mobRef=mob as object;
      let entry=this.enemyPool.find(item=>item.mobRef===mobRef);
      const scale=(mob.boss ? 0.58 : 0.42)*s.zoom;
      const visible=Math.abs(x)<=maxX&&Math.abs(y)<=maxY;
      if(!visible){if(entry){entry.lastX=x;entry.lastY=y;entry.lastDistance=distance;entry.lastScale=scale;entry.node.active=false;}continue;}
      if(!entry){
        entry=this.enemyPool.find(item=>item.mobRef===null&&!item.ghost);
        if(!entry){if(this.enemyPool.length>=this.maxVisible+24)continue;entry=this.createEnemy();this.enemyPool.push(entry);}
        entry.mobRef=mobRef;entry.lastHp=mob.hp;entry.hurtTimer=0;entry.attackTimer=0;entry.deathTimer=0;entry.ghost=false;entry.animState='walk';entry.frame=-1;entry.kind=null;
        entry.node.setRotationFromEuler(0,0,0);
        for(const sprite of entry.sprites){sprite.color=this.normalTint;sprite.node.setRotationFromEuler(0,0,0);}
      }else if(mob.hp<entry.lastHp&&mob.hp>0){
        entry.hurtTimer=.18;
      }
      entry.lastHp=mob.hp;entry.lastX=x;entry.lastY=y;entry.lastDistance=distance;entry.lastScale=scale;
      const enemyKind:'grunt'|'boss'=mob.boss?'boss':'grunt';
      this.applyEnemy(entry,enemyKind);
      entry.node.active=true;entry.node.setPosition(x,y,0);entry.node.setScale(scale,scale,1);
      entry.hurtTimer=Math.max(0,entry.hurtTimer-dt);
      if(entry.hurtTimer>0)entry.animState='hurt';
      else if(distance<78)entry.animState='attack';
      else entry.animState='walk';
      const authoredFrame=this.enemyStateFrame(entry,entry.animState,phase);
      const authored=this.applyEnemyKeyframe(entry,entry.animState,authoredFrame,x,y,scale);
      if(!authored){
        for(const sprite of entry.sprites){
          sprite.color=this.normalTint;sprite.node.setPosition(0,0,0);sprite.node.setRotationFromEuler(0,0,0);sprite.node.setScale(1,1,1);
        }
        entry.node.setRotationFromEuler(0,0,0);
        const breathing=1+Math.sin(this.elapsed*5+mob.x*.01)*.02;
        if(entry.animState==='walk'){
          entry.sprites[0].node.setScale(1,breathing,1);
          entry.sprites[1].node.setRotationFromEuler(0,0,Math.sin(this.elapsed*3+mob.x*.01)*1.4);
          entry.sprites[2].node.setRotationFromEuler(0,0,Math.sin(this.elapsed*7+mob.y*.01)*1.8);
        }else if(entry.animState==='hurt'){
          for(const sprite of entry.sprites)sprite.color=this.hurtTint;
          entry.node.setPosition(x+Math.sin(this.elapsed*90)*2.5,y,0);
          entry.sprites[0].node.setScale(1.06,.94,1);
          entry.sprites[1].node.setRotationFromEuler(0,0,Math.sin(this.elapsed*75)*6);
          entry.sprites[2].node.setRotationFromEuler(0,0,-10);
        }else if(entry.animState==='attack'){
          entry.sprites[1].node.setRotationFromEuler(0,0,Math.sin(this.elapsed*20)*9);
          entry.sprites[2].node.setRotationFromEuler(0,0,Math.sin(this.elapsed*24)*25);
        }
        if(entry.master.node.active){
          entry.master.color=entry.animState==='hurt'?this.hurtTint:this.normalTint;
          entry.master.node.setRotationFromEuler(0,0,entry.animState==='attack'?Math.sin(this.elapsed*24)*6:entry.animState==='hurt'?Math.sin(this.elapsed*75)*4:0);
          if(entry.animState==='walk')entry.master.node.setScale(1,breathing,1);
          else if(entry.animState==='hurt')entry.master.node.setScale(1.06,.94,1);
          else if(entry.animState==='attack')entry.master.node.setScale(1.04,.97,1);
          else entry.master.node.setScale(1,1,1);
        }
      }
      entry.frame=authoredFrame;
    }
    for(const entry of this.enemyPool){
      if(!entry.ghost)continue;
      entry.deathTimer=Math.max(0,entry.deathTimer-dt);
      const onScreen=Math.abs(entry.lastX)<=maxX&&Math.abs(entry.lastY)<=maxY;
      if(!onScreen){
        entry.node.active=false;
        if(entry.deathTimer<=0){entry.ghost=false;entry.mobRef=null;entry.animState='walk';}
        continue;
      }
      entry.node.active=true;
      if(entry.attackTimer>0){
        entry.attackTimer=Math.max(0,entry.attackTimer-dt);
        entry.animState='attack';
        const authoredFrame=this.enemyStateFrame(entry,'attack',phase);
        const authored=this.applyEnemyKeyframe(entry,'attack',authoredFrame,entry.lastX,entry.lastY,entry.lastScale);
        if(!authored){
          entry.node.setPosition(entry.lastX,entry.lastY,0);entry.node.setScale(entry.lastScale,entry.lastScale,1);
          entry.master.color=this.normalTint;
          if(entry.master.node.active){entry.master.node.setRotationFromEuler(0,0,Math.sin(this.elapsed*24)*7);entry.master.node.setScale(1.04,.97,1);}
          for(const sprite of entry.sprites)sprite.color=this.normalTint;
          entry.sprites[1].node.setRotationFromEuler(0,0,Math.sin(this.elapsed*20)*10);
          entry.sprites[2].node.setRotationFromEuler(0,0,Math.sin(this.elapsed*24)*28);
        }
        entry.frame=authoredFrame;
      }else{
        entry.animState='death';
        const authoredFrame=this.enemyStateFrame(entry,'death',phase);
        const authored=this.applyEnemyKeyframe(entry,'death',authoredFrame,entry.lastX,entry.lastY,entry.lastScale);
        if(!authored){
          const progress=Math.max(0,Math.min(1,1-entry.deathTimer/.32));
          const collapse=Math.max(.05,1-progress*.8);
          entry.node.setPosition(entry.lastX,entry.lastY,0);
          entry.node.setScale(entry.lastScale*(1+progress*.2),entry.lastScale*collapse,1);
          entry.node.setRotationFromEuler(0,0,-progress*70);
          entry.master.color=this.deathTint;
          for(const sprite of entry.sprites)sprite.color=this.deathTint;
        }
        entry.frame=authoredFrame;
      }
      if(entry.deathTimer<=0){
        entry.ghost=false;entry.mobRef=null;entry.node.active=false;entry.animState='walk';entry.hurtTimer=0;entry.attackTimer=0;entry.lastHp=0;
        entry.node.setRotationFromEuler(0,0,0);
        for(const sprite of entry.sprites){sprite.color=this.normalTint;sprite.node.setPosition(0,0,0);sprite.node.setRotationFromEuler(0,0,0);sprite.node.setScale(1,1,1);}
      }
    }
    this.previousGiftEvents=s.giftEvents;
  }

  onDestroy():void {
    if(this.controller){this.controller.useCandidateArt=false;this.controller.setCandidateHudContrast(false);}
    this.towerFrames.clear();
    this.towerPool.length=0;
    this.enemyPool.length=0;
    this.shotFxPool.length=0;
    this.fxFrames.length=0;
    this.crystalSprites.length=0;
    this.uiSprites.length=0;
    this.uiFrames.length=0;
    this.enemyLayerFrames.grunt.length=0;
    this.enemyLayerFrames.boss.length=0;
    this.enemyMasterFrames.grunt=null;
    this.enemyMasterFrames.boss=null;
    this.groundFrame=null;
    this.runeFrame=null;
  }
}