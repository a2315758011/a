import { _decorator, Component, Node, Sprite, SpriteFrame, UITransform, Graphics, Label, Color, Layers, resources, HorizontalTextAlignment, VerticalTextAlignment, profiler } from 'cc';
const { ccclass } = _decorator;
type Group = { title: string, dir: string, frames: SpriteFrame[], sprite: Sprite, loaded: number };
@ccclass('待审美术测试控制器')
export class 待审美术测试控制器 extends Component {
  private groups: Group[] = [];
  private elapsed = 0;
  private step = -1;
  private failures = 0;
  private status!: Label;
  private readonly subjects: Array<{ title: string, dir: string }> = [
    { title:'连珠·攻击', dir:'待审核-分层动画测试/连珠速射塔/attack' },
    { title:'重炮·攻击', dir:'待审核-分层动画测试/熔芯重炮塔/attack' },
    { title:'寒霜·攻击', dir:'待审核-分层动画测试/寒霜喷射塔/attack' },
    { title:'核心·破碎', dir:'待审核-分层动画测试/城防水晶/shatter' },
    { title:'兽人·行走', dir:'待审核-分层动画测试/兽人小兵/walk' },
    { title:'兽人·攻击', dir:'待审核-分层动画测试/兽人小兵/attack' },
    { title:'兽人·死亡', dir:'待审核-分层动画测试/兽人小兵/death' }
  ];
  onLoad(): void {
    this.scheduleOnce(() => profiler.hideStats(), .2);
    this.drawBackground();
    this.makeLabel('待审核美术样例｜仅Cocos资源导入测试',0,439,495,35,18,new Color(245,247,250));
    this.makeLabel('56帧候选｜双列7组｜不会影响守城主游戏',0,403,495,27,12,new Color(162,192,205));
    this.status=this.makeLabel('正在读取本地 SpriteFrame ...',0,-439,495,38,13,new Color(219,232,240));
    this.subjects.forEach((a,i)=>{
      const x=(i%2)===0?-132:132;
      const y=300-Math.floor(i/2)*200;
      const n=new Node('候选精灵-'+a.title);
      this.node.addChild(n);n.layer=Layers.Enum.UI_2D;n.setPosition(x,y,0);
      n.addComponent(UITransform).setContentSize(96,96);
      const spr=n.addComponent(Sprite);
      spr.sizeMode=Sprite.SizeMode.CUSTOM;
      spr.trim=false;
      this.makeLabel(a.title,x,y-68,250,28,15,new Color(255,214,155));
      const group:Group={title:a.title,dir:a.dir,frames:new Array<SpriteFrame>(8),sprite:spr,loaded:0};
      this.groups.push(group);
      for(let frame=1;frame<=8;frame++){
        const idx=frame-1;
        const source=a.dir+'/帧'+String(frame).padStart(3,'0')+'/spriteFrame';
        resources.load(source,SpriteFrame,(error,asset)=>{
          if(error || !asset){
            this.failures++;
            this.status.string='资源加载失败：'+this.failures+'，检查 Cocos 导入记录';
            console.error('候选美术载入失败',source,error);return;
          }
          group.frames[idx]=asset;group.loaded++;
          if(idx===0)group.sprite.spriteFrame=asset;
          if(this.groups.every(g=>g.loaded===8)){
            this.status.string='56 / 56 SpriteFrame 就绪：循环播放，仍待审美';
            console.log('美术样例引擎加载完成',this.groups.length,'组56帧');
          }
        });
      }
    });
  }
  update(dt:number):void {
    this.elapsed+=Math.min(Math.max(dt,0),.1);
    const next=Math.floor(this.elapsed/.11)%8;
    if(this.step===next)return;
    this.step=next;
    for(const group of this.groups){
      if(group.loaded===8 && group.frames[next]) group.sprite.spriteFrame=group.frames[next];
    }
  }
  private drawBackground():void{
    const n=new Node('浅色基准棋盘');n.layer=Layers.Enum.UI_2D;this.node.addChild(n);
    n.setSiblingIndex(0);
    n.addComponent(UITransform).setContentSize(540,960);
    const g=n.addComponent(Graphics);
    g.fillColor=new Color(30,43,54,255);g.rect(-270,-480,540,960);g.fill();
    for(let y=-408;y<389;y+=200){for(let x=-258;x<270;x+=264){
      g.fillColor=new Color(45,61,73,255);g.roundRect(x,y,252,181,14);g.fill();
      g.strokeColor=new Color(75,99,108,255);g.lineWidth=1;g.roundRect(x,y,252,181,14);g.stroke();
    }}
  }
  private makeLabel(value:string,x:number,y:number,w:number,h:number,size:number,color:Color):Label{
    const n=new Node('说明-'+value.slice(0,6));
    this.node.addChild(n);n.layer=Layers.Enum.UI_2D;n.setPosition(x,y,0);
    n.addComponent(UITransform).setContentSize(w,h);
    const l=n.addComponent(Label);l.string=value;l.fontSize=size;l.lineHeight=size+6;
    l.horizontalAlign=HorizontalTextAlignment.CENTER;l.verticalAlign=VerticalTextAlignment.CENTER;l.color=color;
    return l;
  }
}
