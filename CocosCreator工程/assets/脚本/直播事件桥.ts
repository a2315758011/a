export type 直播事件类型='viewer_join'|'viewer_leave'|'gift';
export type 直播事件来源='simulation'|'douyin'|'wechat'|'external';

export interface 直播事件 {
  readonly eventId:string;
  readonly type:直播事件类型;
  readonly viewerId:string;
  readonly viewerName?:string;
  readonly giftId?:string;
  readonly giftPower?:number;
  readonly timestamp?:number;
  readonly source?:直播事件来源;
}

export interface 观众记录 {
  viewerId:string;
  viewerName:string;
  online:boolean;
  joinedAt:number;
  lastSeenAt:number;
  giftCount:number;
  giftPower:number;
}

export interface 直播会话统计 {
  readonly onlineViewers:number;
  readonly knownViewers:number;
  readonly queueDepth:number;
  readonly processedEvents:number;
  readonly duplicateEvents:number;
  readonly rejectedEvents:number;
  readonly giftEvents:number;
  readonly giftPower:number;
  readonly lastEvent:string;
}

export interface 直播会话快照 extends 直播会话统计 {
  readonly viewers:ReadonlyArray<Readonly<观众记录>>;
}

export type 直播事件处理器=(event:Readonly<直播事件>,viewer:Readonly<观众记录>)=>void;

export class 直播事件桥 {
  private readonly maxQueue=4096;
  private readonly maxSeen=4096;
  private queue:直播事件[]=[];
  private viewers=new Map<string,观众记录>();
  private seen=new Set<string>();
  private seenOrder:string[]=[];
  private processedEvents=0;
  private duplicateEvents=0;
  private rejectedEvents=0;
  private giftEvents=0;
  private giftPower=0;
  private lastEvent='none';

  reset(seed:ReadonlyArray<{viewerId:string;viewerName:string}>):void {
    this.queue=[];
    this.viewers.clear();
    this.seen.clear();
    this.seenOrder=[];
    this.processedEvents=0;
    this.duplicateEvents=0;
    this.rejectedEvents=0;
    this.giftEvents=0;
    this.giftPower=0;
    this.lastEvent='none';
    const now=Date.now();
    for(const item of seed){
      const id=String(item.viewerId||'').trim();
      if(!id||this.viewers.has(id))continue;
      this.viewers.set(id,{
        viewerId:id,viewerName:String(item.viewerName||id),online:true,
        joinedAt:now,lastSeenAt:now,giftCount:0,giftPower:0
      });
    }
  }

  enqueue(input:直播事件):{accepted:boolean;reason:'accepted'|'duplicate'|'invalid'|'queue-full'} {
    const eventId=String(input?.eventId||'').trim();
    const viewerId=String(input?.viewerId||'').trim();
    if(!eventId||!viewerId||viewerId.startsWith('base-')||!['viewer_join','viewer_leave','gift'].includes(input?.type)){
      this.rejectedEvents++;
      return {accepted:false,reason:'invalid'};
    }
    if(this.seen.has(eventId)){
      this.duplicateEvents++;
      return {accepted:false,reason:'duplicate'};
    }
    if(this.queue.length>=this.maxQueue){
      this.rejectedEvents++;
      return {accepted:false,reason:'queue-full'};
    }
    const event:直播事件={
      eventId,
      type:input.type,
      viewerId,
      viewerName:String(input.viewerName||viewerId),
      giftId:input.giftId?String(input.giftId):undefined,
      giftPower:Math.max(1,Math.min(3,Math.floor(Number(input.giftPower)||1))),
      timestamp:Number.isFinite(input.timestamp)?Number(input.timestamp):Date.now(),
      source:input.source||'external'
    };
    this.queue.push(event);
    this.seen.add(eventId);
    this.seenOrder.push(eventId);
    while(this.seenOrder.length>this.maxSeen){
      const old=this.seenOrder.shift();
      if(old)this.seen.delete(old);
    }
    return {accepted:true,reason:'accepted'};
  }

  drain(handler:直播事件处理器,max:number=128):number {
    let count=0;
    const limit=Math.max(1,Math.min(512,Math.floor(max)||128));
    while(this.queue.length&&count<limit){
      const event=this.queue.shift()!;
      const now=Number(event.timestamp)||Date.now();
      let viewer=this.viewers.get(event.viewerId);
      if(!viewer){
        viewer={
          viewerId:event.viewerId,viewerName:event.viewerName||event.viewerId,online:false,
          joinedAt:now,lastSeenAt:now,giftCount:0,giftPower:0
        };
        this.viewers.set(event.viewerId,viewer);
      }
      if(event.viewerName)viewer.viewerName=event.viewerName;
      viewer.lastSeenAt=now;
      if(event.type==='viewer_join'){
        if(!viewer.online)viewer.joinedAt=now;
        viewer.online=true;
      }else if(event.type==='viewer_leave'){
        viewer.online=false;
      }else{
        // A gift implies an active participant even if the platform omitted a separate join callback.
        if(!viewer.online){viewer.online=true;viewer.joinedAt=now;}
        viewer.giftCount++;
        viewer.giftPower+=event.giftPower||1;
        this.giftEvents++;
        this.giftPower+=event.giftPower||1;
      }
      this.processedEvents++;
      this.lastEvent=event.type+':'+event.viewerId;
      handler(event,viewer);
      count++;
    }
    return count;
  }

  metrics():直播会话统计 {
    let online=0;
    for(const viewer of this.viewers.values())if(viewer.online)online++;
    return {
      onlineViewers:online,
      knownViewers:this.viewers.size,
      queueDepth:this.queue.length,
      processedEvents:this.processedEvents,
      duplicateEvents:this.duplicateEvents,
      rejectedEvents:this.rejectedEvents,
      giftEvents:this.giftEvents,
      giftPower:this.giftPower,
      lastEvent:this.lastEvent
    };
  }

  snapshot():直播会话快照 {
    const metrics=this.metrics();
    return {
      ...metrics,
      viewers:Array.from(this.viewers.values()).map(v=>({...v}))
    };
  }

  lastOnlineViewer():Readonly<观众记录>|null {
    const values=Array.from(this.viewers.values());
    for(let i=values.length-1;i>=0;i--)if(values[i].online)return values[i];
    return null;
  }

  getViewer(viewerId:string):Readonly<观众记录>|null {
    return this.viewers.get(viewerId)||null;
  }
}
