import { 直播事件 } from './直播事件桥';
import { 直播事件源接口 } from './平台适配器';

export interface 直播参与事件源配置 {
  url:string;
  id?:string;
  source?:'douyin'|'wechat'|'external';
  joinCommands?:ReadonlyArray<string>;
  leaveCommands?:ReadonlyArray<string>;
  reconnectBaseMs?:number;
  reconnectMaxMs?:number;
}

export interface 直播参与事件源快照 {
  id:string;
  url:string;
  source:'douyin'|'wechat'|'external';
  active:boolean;
  connected:boolean;
  received:number;
  mapped:number;
  ignored:number;
  reconnects:number;
  lastError:string|null;
}

/**
 * 接收“开发者后端 -> Cocos 客户端”的标准化 WebSocket 数据。
 *
 * 官方抖音直播数据应先由开发者服务器通过开放平台能力接收/验签，再转发到本事件源。
 * 本类不持有 access_token，不直连主播直播间，也不把“进入/离开直播间”伪装成平台能力。
 *
 * 支持的后端包：
 * - participation_join / participation_leave：玩法参与加入/退出
 * - live_comment：仅当评论内容精确匹配 joinCommands / leaveCommands 时映射
 * - live_gift / gift：映射到礼物事件
 * - live_like / live_fansclub：当前忽略，直到游戏为其定义确定的玩法效果
 */
export class WebSocket直播参与事件源 implements 直播事件源接口 {
  public readonly id:string;
  private readonly url:string;
  private readonly source:'douyin'|'wechat'|'external';
  private readonly joinCommands:Set<string>;
  private readonly leaveCommands:Set<string>;
  private readonly reconnectBaseMs:number;
  private readonly reconnectMaxMs:number;
  private socket:any=null;
  private emit:((event:直播事件)=>boolean)|null=null;
  private reconnectTimer:any=null;
  private generation=0;
  private active=false;
  private connected=false;
  private received=0;
  private mapped=0;
  private ignored=0;
  private reconnects=0;
  private lastError:string|null=null;
  private reconnectAttempt=0;

  constructor(config:直播参与事件源配置){
    this.url=String(config.url||'').trim();
    this.id=String(config.id||'douyin-live-participation-ws').trim()||'douyin-live-participation-ws';
    const inferred=this.id.toLowerCase().includes('wechat')?'wechat':this.id.toLowerCase().includes('douyin')?'douyin':'external';
    this.source=config.source||inferred;
    this.joinCommands=new Set((config.joinCommands||['加入','888']).map(x=>this.normalizeCommand(x)).filter(Boolean));
    this.leaveCommands=new Set((config.leaveCommands||['退出']).map(x=>this.normalizeCommand(x)).filter(Boolean));
    this.reconnectBaseMs=Math.max(200,Math.min(10000,Math.floor(Number(config.reconnectBaseMs)||500)));
    this.reconnectMaxMs=Math.max(this.reconnectBaseMs,Math.min(30000,Math.floor(Number(config.reconnectMaxMs)||8000)));
  }

  public start(emit:(event:直播事件)=>boolean):void {
    this.stop();
    this.emit=emit;
    this.active=true;
    this.lastError=null;
    this.reconnectAttempt=0;
    this.generation++;
    this.connect(this.generation);
  }

  public stop():void {
    this.active=false;
    this.connected=false;
    this.emit=null;
    this.generation++;
    if(this.reconnectTimer!==null){
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer=null;
    }
    const ws=this.socket;
    this.socket=null;
    if(ws){
      try{ws.onopen=null;ws.onmessage=null;ws.onerror=null;ws.onclose=null;ws.close();}catch{}
    }
  }

  public snapshot():直播参与事件源快照 {
    return {
      id:this.id,url:this.url,source:this.source,active:this.active,connected:this.connected,
      received:this.received,mapped:this.mapped,ignored:this.ignored,
      reconnects:this.reconnects,lastError:this.lastError
    };
  }

  private connect(generation:number):void {
    if(!this.active||generation!==this.generation)return;
    if(!/^wss?:\/\//i.test(this.url)){
      this.lastError='invalid-websocket-url';
      this.active=false;
      return;
    }
    const g=globalThis as unknown as {
      WebSocket?:new(url:string)=>any;
      tt?:{connectSocket?:(options:{url:string})=>any};
      wx?:{connectSocket?:(options:{url:string})=>any};
    };
    let ws:any=null;
    const onOpen=()=>{
      if(generation!==this.generation)return;
      this.connected=true;
      this.reconnectAttempt=0;
      this.lastError=null;
    };
    const onMessage=(input:any)=>{
      if(generation!==this.generation)return;
      this.received++;
      const raw=input&&typeof input==='object'&&'data' in input?input.data:input;
      const event=this.mapMessage(raw);
      if(!event){this.ignored++;return;}
      const emit=this.emit;
      if(!emit){this.ignored++;return;}
      if(emit(event))this.mapped++;
      else this.ignored++;
    };
    const onError=()=>{
      if(generation!==this.generation)return;
      this.lastError='websocket-error';
    };
    const onClose=()=>{
      if(generation!==this.generation)return;
      this.connected=false;
      if(this.socket===ws)this.socket=null;
      this.scheduleReconnect(generation);
    };
    try{
      // Prefer the mini-game SocketTask API where available.
      const platformApi=this.source==='wechat'?g.wx:this.source==='douyin'?g.tt:
        ((g.tt&&typeof g.tt.connectSocket==='function')?g.tt:g.wx);
      const socketApi=platformApi&&typeof platformApi.connectSocket==='function'?platformApi:null;
      if(socketApi){
        ws=socketApi.connectSocket!({url:this.url});
        if(!ws||typeof ws.onOpen!=='function'||typeof ws.onMessage!=='function'||
           typeof ws.onError!=='function'||typeof ws.onClose!=='function'){
          throw new Error('platform-socket-task-unavailable');
        }
        this.socket=ws;
        ws.onOpen(onOpen);
        ws.onMessage(onMessage);
        ws.onError(onError);
        ws.onClose(onClose);
        return;
      }
      if(typeof g.WebSocket==='function'){
        ws=new g.WebSocket(this.url);
        this.socket=ws;
        ws.onopen=onOpen;
        ws.onmessage=onMessage;
        ws.onerror=onError;
        ws.onclose=onClose;
        return;
      }
      this.lastError='websocket-unavailable';
      this.active=false;
    }catch(error){
      this.connected=false;
      this.lastError='connect-failed:'+String(error);
      if(this.socket===ws)this.socket=null;
      this.scheduleReconnect(generation);
    }
  }
  private mapMessage(raw:unknown):直播事件|null {
    if(typeof raw!=='string')return null;
    let root:any;
    try{root=JSON.parse(raw);}catch{return null;}
    if(!root||typeof root!=='object')return null;
    const data=root.data&&typeof root.data==='object'?root.data:root;
    const type=String(data.type||data.msgType||data.messageType||root.type||'').trim();
    const eventId=this.firstString(data,root,['eventId','event_id','msgId','msg_id','id']);
    const user=data.user&&typeof data.user==='object'?data.user:{};
    const viewerId=this.firstString(data,user,['viewerId','viewer_id','openId','open_id','userId','user_id','secUid','sec_uid']);
    const viewerName=this.firstString(data,user,['viewerName','viewer_name','nickname','nickName','userName','user_name'])||viewerId;
    if(!eventId||!viewerId)return null;
    const base={
      eventId,viewerId,viewerName,
      timestamp:this.firstNumber(data,root,['timestamp','ts','time'])||Date.now(),
      source:this.source
    };
    if(type==='participation_join'){
      return {...base,type:'viewer_join'};
    }
    if(type==='participation_leave'){
      return {...base,type:'viewer_leave'};
    }
    if(type==='live_comment'){
      const text=this.normalizeCommand(this.firstString(data,root,['content','comment','text','message']));
      if(this.joinCommands.has(text))return {...base,type:'viewer_join'};
      if(this.leaveCommands.has(text))return {...base,type:'viewer_leave'};
      return null;
    }
    if(type==='live_gift'||type==='gift'){
      const giftId=this.firstString(data,root,['giftId','gift_id','giftName','gift_name'])||'live-gift';
      const rawPower=this.firstNumber(data,root,['giftPower','gift_power','power']);
      const giftPower=Math.max(1,Math.min(3,Math.floor(rawPower||1)));
      return {...base,type:'gift',giftId,giftPower};
    }
    // 点赞/粉丝团只有在游戏定义确定玩法效果后才能接入，不能无效果地消费平台事件。
    return null;
  }

  private normalizeCommand(value:unknown):string {
    return String(value||'').trim().toLowerCase();
  }

  private firstString(primary:any,secondary:any,keys:string[]):string {
    for(const obj of [primary,secondary]){
      if(!obj||typeof obj!=='object')continue;
      for(const key of keys){
        const value=obj[key];
        if(value!==undefined&&value!==null&&String(value).trim())return String(value).trim();
      }
    }
    return '';
  }

  private firstNumber(primary:any,secondary:any,keys:string[]):number {
    for(const obj of [primary,secondary]){
      if(!obj||typeof obj!=='object')continue;
      for(const key of keys){
        const value=Number(obj[key]);
        if(Number.isFinite(value)&&value>0)return value;
      }
    }
    return 0;
  }
}
