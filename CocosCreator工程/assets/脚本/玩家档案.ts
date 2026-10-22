import { sys } from 'cc';

export type 商店商品Id='coreShield'|'fireControl'|'viewerBoost';

export interface 永久升级 {
  coreShield:number;
  fireControl:number;
  viewerBoost:number;
}

export interface 玩家统计 {
  runs:number;
  wins:number;
  totalKills:number;
  bestKills:number;
}

export interface 玩家档案 {
  version:1;
  coins:number;
  upgrades:永久升级;
  stats:玩家统计;
  updatedAt:number;
}

export interface 商店条目 {
  id:商店商品Id;
  name:string;
  description:string;
  level:number;
  maxLevel:number;
  cost:number|null;
  canBuy:boolean;
}

export interface 购买结果 {
  ok:boolean;
  reason:'purchased'|'insufficient-coins'|'max-level'|'invalid-item'|'platform-disabled';
  id:商店商品Id;
  level:number;
  coins:number;
  cost:number;
}

export interface 档案云同步接口 {
  pull():Promise<Partial<玩家档案>|null>;
  push(profile:Readonly<玩家档案>):Promise<void>;
}

const DEFAULT_PROFILE=():玩家档案=>({
  version:1,
  coins:0,
  upgrades:{coreShield:0,fireControl:0,viewerBoost:0},
  stats:{runs:0,wins:0,totalKills:0,bestKills:0},
  updatedAt:Date.now()
});

const MAX_LEVEL:Record<商店商品Id,number>={
  coreShield:3,
  fireControl:3,
  viewerBoost:2
};

const BASE_COST:Record<商店商品Id,number>={
  coreShield:40,
  fireControl:60,
  viewerBoost:80
};

const ITEM_TEXT:Record<商店商品Id,{name:string;description:string}>={
  coreShield:{name:'水晶护盾',description:'每级开局水晶 +10 生命'},
  fireControl:{name:'火控芯片',description:'每级全塔伤害 +5%'},
  viewerBoost:{name:'直播增幅',description:'每级观众塔起始等级 +1'}
};

export class 玩家档案仓库 {
  public static readonly STORAGE_KEY='live-turret-defense.profile.v1';
  private profile:玩家档案;
  private cloudAdapter:档案云同步接口|null=null;

  constructor(){
    this.profile=this.load();
  }

  public snapshot():玩家档案 {
    return JSON.parse(JSON.stringify(this.profile)) as 玩家档案;
  }

  public catalog():商店条目[] {
    return (['coreShield','fireControl','viewerBoost'] as 商店商品Id[]).map(id=>{
      const level=this.profile.upgrades[id];
      const maxLevel=MAX_LEVEL[id];
      const cost=level>=maxLevel?null:BASE_COST[id]*(level+1);
      return {
        id,name:ITEM_TEXT[id].name,description:ITEM_TEXT[id].description,
        level,maxLevel,cost,canBuy:cost!==null&&this.profile.coins>=cost
      };
    });
  }

  public purchase(id:商店商品Id):购买结果 {
    if(!(id in MAX_LEVEL)){
      return {ok:false,reason:'invalid-item',id,level:0,coins:this.profile.coins,cost:0};
    }
    const level=this.profile.upgrades[id];
    const maxLevel=MAX_LEVEL[id];
    if(level>=maxLevel){
      return {ok:false,reason:'max-level',id,level,coins:this.profile.coins,cost:0};
    }
    const cost=BASE_COST[id]*(level+1);
    if(this.profile.coins<cost){
      return {ok:false,reason:'insufficient-coins',id,level,coins:this.profile.coins,cost};
    }
    this.profile.coins-=cost;
    this.profile.upgrades[id]=level+1;
    this.touchAndSave();
    return {ok:true,reason:'purchased',id,level:level+1,coins:this.profile.coins,cost};
  }

  public recordSettlement(kills:number,won:boolean):number {
    const safeKills=Math.max(0,Math.floor(Number(kills)||0));
    const reward=safeKills+(won?50:0);
    this.profile.coins+=reward;
    this.profile.stats.runs++;
    if(won)this.profile.stats.wins++;
    this.profile.stats.totalKills+=safeKills;
    this.profile.stats.bestKills=Math.max(this.profile.stats.bestKills,safeKills);
    this.touchAndSave();
    return reward;
  }

  public setCloudAdapter(adapter:档案云同步接口|null):void {
    this.cloudAdapter=adapter;
  }

  public cloudConfigured():boolean {
    return this.cloudAdapter!==null;
  }

  public async pushCloud():Promise<boolean> {
    if(!this.cloudAdapter)return false;
    await this.cloudAdapter.push(this.snapshot());
    return true;
  }

  public async pullCloud():Promise<boolean> {
    if(!this.cloudAdapter)return false;
    const remote=await this.cloudAdapter.pull();
    if(!remote)return false;
    this.profile=this.normalize(remote);
    this.touchAndSave();
    return true;
  }

  public exportCloudPayload():玩家档案 {
    return this.snapshot();
  }

  private load():玩家档案 {
    try{
      const raw=sys.localStorage.getItem(玩家档案仓库.STORAGE_KEY);
      if(!raw)return DEFAULT_PROFILE();
      return this.normalize(JSON.parse(raw));
    }catch{
      return DEFAULT_PROFILE();
    }
  }

  private normalize(input:Partial<玩家档案>|null|undefined):玩家档案 {
    const base=DEFAULT_PROFILE();
    const src=input||{};
    const upgrades=(src.upgrades||{}) as Partial<永久升级>;
    const stats=(src.stats||{}) as Partial<玩家统计>;
    base.coins=Math.max(0,Math.floor(Number(src.coins)||0));
    base.upgrades.coreShield=this.clampLevel(upgrades.coreShield,MAX_LEVEL.coreShield);
    base.upgrades.fireControl=this.clampLevel(upgrades.fireControl,MAX_LEVEL.fireControl);
    base.upgrades.viewerBoost=this.clampLevel(upgrades.viewerBoost,MAX_LEVEL.viewerBoost);
    base.stats.runs=Math.max(0,Math.floor(Number(stats.runs)||0));
    base.stats.wins=Math.min(base.stats.runs,Math.max(0,Math.floor(Number(stats.wins)||0)));
    base.stats.totalKills=Math.max(0,Math.floor(Number(stats.totalKills)||0));
    base.stats.bestKills=Math.max(0,Math.floor(Number(stats.bestKills)||0));
    base.updatedAt=Math.max(0,Math.floor(Number(src.updatedAt)||Date.now()));
    return base;
  }

  private clampLevel(value:unknown,max:number):number {
    return Math.max(0,Math.min(max,Math.floor(Number(value)||0)));
  }

  private touchAndSave():void {
    this.profile.updatedAt=Date.now();
    try{
      sys.localStorage.setItem(玩家档案仓库.STORAGE_KEY,JSON.stringify(this.profile));
    }catch(error){
      console.warn('玩家档案本地保存失败',error);
    }
  }
}
