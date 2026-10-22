# -*- coding: utf-8 -*-
"""首张正式玩法图：使用现有共享生图网关，严格一次提交、固定账号、不重试未知状态。"""
import json,pathlib,urllib.request,urllib.error,datetime,hashlib
root=pathlib.Path(__file__).resolve().parents[1]
runtime=json.loads((pathlib.Path.home()/'Desktop/deliverable/.infra/GENERATION_GATEWAY_RUNTIME.json').read_text('utf-8'))
token=pathlib.Path(runtime['tokenFile']).read_text('utf-8').strip()
ledger=root/'任务包'/'正式玩法图网关任务-v0.4.json'
payload={
 'kind':'image','feature':'freedom_image','transport':'web',
 'providerId':'web:d3b71ce4-d61e-4adc-8f08-3c28262b6e48:freedom_image',
 'accountId':'d3b71ce4-d61e-4adc-8f08-3c28262b6e48',
 'pool':False,
 'sourceProjectId':'live-turret-defense','sourceTaskId':'GAME-OVERVIEW-002',
 'idempotencyKey':'live-turret-defense-GAME-OVERVIEW-002-original-native-pixel-art-v04-once',
 'outputDir':str(root/'美术资源'/'原始生成'),
 'prompt':"""请生成一张真正用于手机游戏内玩法审查的原创 2D 像素风局内截图，不是白底结构示意图！抖音直播互动塔防《直播炮塔守城》，单幅9:16竖屏完整游戏画面。严格正上方俯视正交镜头，原生逐像素轮廓，清楚的像素草地、碎石、断墙遗迹、独特原创建筑和战斗视觉，不使用高清三维渲染、等距45度斜视、写实模型或海报排版。可见视口只是远大于屏幕的完整地图中的一个相机窗口，镜头以中央独立能量水晶为中心，地面空间可持续容纳成百上千座观众炮塔，不把总地图限制成一屏。中间唯一被保护的蓝色晶体HP显示86/100，晶体不能是炮塔。环绕放置约九到十五座互不重叠的独立炮塔：黄色双短枪管连珠速射塔、红色单粗炮管熔芯重炮塔、青蓝色矮胖金属寒霜喷射炮塔；第三种绝不是水晶。每座塔方向、弹道各异，一颗黄色像素子弹、一朵橙色爆炸和一条蓝色减速冰雾。北、南、东、西四侧都有像素兽人兵向中心逼近，红色血条，视野外可继续来怪。顶部小型清晰HUD波次03/08、守护核心86/100，下方少量直播互动操作标签，昵称独立小字UI不绘在炮塔上。整体采用丰富游戏美术像素材质、色彩逻辑一致、场地清楚、对象边界清晰、玩家看得懂哪里可以自由布塔、哪里有敌人、核心被围攻。参考的是俯视像素塔防这一玩法类型，不模仿、复制《兽人领地》原始截图、UI、角色、炮塔或具体场景布局。禁止把整幅做成说明书/设计图/白底原型；禁止明显大面积空白页面，禁止3D。"""
}
def req(method,uri,data=None):
  headers={'X-Moyin-Gateway-Token':token}
  raw=None
  if data is not None:
    headers['Content-Type']='application/json;charset=utf-8'
    raw=json.dumps(data,ensure_ascii=False).encode('utf-8')
  request=urllib.request.Request(runtime['baseUrl']+uri,headers=headers,data=raw,method=method)
  with urllib.request.urlopen(request,timeout=20) as resp:
    return resp.status,json.load(resp)
def persist(state):
  ledger.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
  if ledger.exists():
    j=json.loads(ledger.read_text(encoding='utf-8'))
    print('EXISTING_RECORD_NO_RESUBMIT',j.get('jobId'),j.get('status'));return
  try:
    http,listing=req('GET','/v1/jobs')
  except Exception as ex:
    print('BLOCKED_PRE_SUBMIT_QUERY_FAILED',str(ex));return
  for j in listing.get('jobs',[]):
    if j.get('sourceProjectId')==payload['sourceProjectId'] and j.get('sourceTaskId')==payload['sourceTaskId']:
      persist({'status':'EXISTING_FOUND_NO_SUBMIT','jobId':j.get('id'),'idempotencyKey':payload['idempotencyKey']})
      print('EXISTING_FOUND',j.get('id'));return
  state={'status':'SUBMIT_UNKNOWN_NO_RETRY','jobId':None,'idempotencyKey':payload['idempotencyKey'],'providerId':payload['providerId'],'sourceTaskId':payload['sourceTaskId'],'promptSha256':hashlib.sha256(payload['prompt'].encode()).hexdigest(),'submittedAt':datetime.datetime.now(datetime.timezone.utc).isoformat()}
  persist(state) # 写入提交意图，阻断断网/超时重复生成
  try:
    http,r=req('POST','/v1/jobs',payload)
    state.update({'http':http,'response':r,'jobId':(r.get('job') or {}).get('id') or r.get('jobId'),'status':'SUBMITTED' if http in (200,201,202) else 'REJECTED'})
    persist(state)
    print('SUBMISSION',json.dumps({'http':http,'jobId':state['jobId'],'status':state['status']},ensure_ascii=False))
  except urllib.error.HTTPError as ex:
    state.update({'http':ex.code,'status':'REJECTED','reason':ex.read().decode('utf-8','replace')[:600]});persist(state);print('REJECTED',state['reason'])
  except Exception as ex:
    state.update({'status':'SUBMIT_UNKNOWN_NO_RETRY','error':str(ex)});persist(state);print('UNKNOWN_DO_NOT_RETRY',str(ex))
if __name__=='__main__':main()
