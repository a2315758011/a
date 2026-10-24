import { sys } from 'cc';
import { 直播事件 } from './直播事件桥';

export type 运行平台='wechat'|'douyin'|'android'|'native'|'web';
export type 平台运行模式='standard'|'douyin-live-play';

export interface 平台快照 {
  runtime:运行平台;
  mode:平台运行模式;
  platformSdkAvailable:boolean;
  storageAvailable:boolean;
  liveEventSourceAttached:boolean;
  liveEventSourceId:string|null;
  shopAllowed:boolean;
  persistentEconomyAllowed:boolean;
  generalRoomPresenceAvailable:boolean;
  participationModel:'standard'|'explicit-interaction';
}

export interface 直播事件源接口 {
  readonly id:string;
  start(emit:(event:直播事件)=>boolean):void;
  stop():void;
}

/** 平台差异统一入口；不会把缺失的原生 SDK 误报成已接入的直播平台能力。 */
export class 平台适配器 {
  private source:直播事件源接口|null=null;
  private mode:平台运行模式='standard';

  public setMode(mode:平台运行模式):void {
    this.mode=mode==='douyin-live-play'?'douyin-live-play':'standard';
  }

  public snapshot():平台快照 {
    const runtime=this.detectRuntime();
    const livePlay=this.mode==='douyin-live-play';
    return {
      runtime,
      mode:this.mode,
      platformSdkAvailable:this.platformSdkAvailable(runtime),
      storageAvailable:this.storageAvailable(runtime),
      liveEventSourceAttached:this.source!==null,
      liveEventSourceId:this.source?.id||null,
      shopAllowed:!livePlay,
      persistentEconomyAllowed:!livePlay,
      generalRoomPresenceAvailable:false,
      participationModel:livePlay?'explicit-interaction':'standard'
    };
  }

  public attachLiveSource(source:直播事件源接口,emit:(event:直播事件)=>boolean):void {
    this.detachLiveSource();
    this.source=source;
    try{source.start(emit);}
    catch(error){this.source=null;throw error;}
  }

  public detachLiveSource():void {
    if(!this.source)return;
    try{this.source.stop();}catch(error){console.warn('直播事件源停止失败',error);}
    this.source=null;
  }

  private detectRuntime():运行平台 {
    const g=globalThis as unknown as {wx?:unknown;tt?:unknown};
    if(g.wx)return 'wechat';
    if(g.tt)return 'douyin';
    if(sys.isNative){
      const os=String(sys.os||'').toLowerCase();
      if(os.includes('android'))return 'android';
      return 'native';
    }
    return 'web';
  }

  private platformSdkAvailable(runtime:运行平台):boolean {
    const g=globalThis as unknown as {wx?:{getSystemInfoSync?:unknown};tt?:{getSystemInfoSync?:unknown}};
    if(runtime==='wechat')return typeof g.wx?.getSystemInfoSync==='function';
    if(runtime==='douyin')return typeof g.tt?.getSystemInfoSync==='function';
    return false;
  }

  private storageAvailable(runtime:运行平台):boolean {
    try{
      const key='__live_turret_storage_probe__';
      const g=globalThis as unknown as {
        wx?:{setStorageSync?:(key:string,value:string)=>void;getStorageSync?:(key:string)=>unknown;removeStorageSync?:(key:string)=>void};
        tt?:{setStorageSync?:(key:string,value:string)=>void;getStorageSync?:(key:string)=>unknown;removeStorageSync?:(key:string)=>void};
      };
      const platform=runtime==='wechat'?g.wx:runtime==='douyin'?g.tt:null;
      if(platform){
        if(typeof platform.setStorageSync!=='function'||typeof platform.getStorageSync!=='function'||typeof platform.removeStorageSync!=='function')return false;
        platform.setStorageSync(key,'1');
        const ok=platform.getStorageSync(key)==='1';
        platform.removeStorageSync(key);
        return ok;
      }
      sys.localStorage.setItem(key,'1');
      const ok=sys.localStorage.getItem(key)==='1';
      sys.localStorage.removeItem(key);
      return ok;
    }catch{return false;}
  }
}
