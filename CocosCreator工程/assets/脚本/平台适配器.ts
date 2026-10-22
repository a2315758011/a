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

/**
 * 平台差异只允许从这里向上暴露。
 * 微信/抖音真实直播 API 需由单独事件源实现后挂接；本类不伪造平台事件。
 */
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
      platformSdkAvailable:runtime==='wechat'||runtime==='douyin'||runtime==='android'||runtime==='native',
      storageAvailable:this.storageAvailable(),
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
    source.start(emit);
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

  private storageAvailable():boolean {
    try{
      const key='__live_turret_storage_probe__';
      sys.localStorage.setItem(key,'1');
      const ok=sys.localStorage.getItem(key)==='1';
      sys.localStorage.removeItem(key);
      return ok;
    }catch{
      return false;
    }
  }
}
