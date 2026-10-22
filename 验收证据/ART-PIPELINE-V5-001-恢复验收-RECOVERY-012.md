# ART-PIPELINE-V5-001｜V5 恢复验收与交接 RECOVERY-012

日期：2026-10-20
owner：agent-gpt6-art-recovery-20261020
projectId：live-turret-defense
状态：**CANDIDATE_RUNTIME_QA_PASS / ART_APPROVAL_PENDING**

## 完成内容

- 继续使用隔离 Cocos Creator 3.8.2 候选工程，没有替换正式主场景。
- 修正候选 HUD：标题/副标题改为高对比文字色，并重新安排标题、血条框、副标题的垂直位置。
- 候选美术目录内 17 张 PNG 与 17 份 Meta 已存在：8 张 UI、8 张敌人分层/合成图、1 张地面纹理。
- 候选工程总计 89 张 PNG、89 份 Meta；元数据可解析，89/89 图片 UUID 唯一，无缺失 Meta。
- 修正构建验收脚本：Cocos Creator 3.8.2 的 CLI 退出码 36 是官方定义的构建成功，不再误判为构建故障。

## 构建证据

- 构建入口：`_assistant-temp/候选战场Cocos-V5隔离工程-20261020/build/web-mobile/index.html`
- 最新报告：`game-art/evidence/ART-PIPELINE-V5-001/V5-Cocos-Build-QA-RECOVERY-010.json`
- 结果：build success；CLI exit code 36（官方成功码）；TypeScript 错误 0；stderr 0 字节；89 PNG/89 Meta；UUID 89/89 唯一。
- 官方参考：`https://docs.cocos.com/creator/3.8/manual/zh/editor/publish/publish-in-command-line.html`

## 完整对局回归

| 精确视口 | 结果 | 波次 | 击杀 | 水晶生命 | 加观众后炮塔 | 重开结果 | JS 异常 |
|---|---|---:|---:|---:|---:|---|---:|
| 540×760 | PASS | 3/3 | 96 | 100/100 | 24 | ready，9 座炮塔 | 0 |
| 540×960 | PASS | 3/3 | 96 | 100/100 | 24 | ready，9 座炮塔 | 0 |

测试使用真实鼠标输入，不直接修改游戏状态；状态读取仅用于只读 QA。每个视口都执行开始、观众加入、缩放/拖动、完整战斗、结算与重新开始。

证据：
- `验收证据/候选战场美术联调-V5-短屏RECOVERY-011/真人操作完整一局.json`
- `验收证据/候选战场美术联调-V5-短屏RECOVERY-011/00-开局.png`
- `验收证据/候选战场美术联调-V5-短屏RECOVERY-011/01-玩家进场布塔.png`
- `验收证据/候选战场美术联调-V5-短屏RECOVERY-011/99-结局.png`
- `验收证据/候选战场美术联调-V5-短屏RECOVERY-011/100-重新开始.png`
- `验收证据/候选战场美术联调-V5-540x960-RECOVERY-011/真人操作完整一局.json`
- `验收证据/候选战场美术联调-V5-540x960-RECOVERY-011/01-玩家进场布塔.png`
- `验收证据/候选战场美术联调-V5-540x960-RECOVERY-011/99-结局.png`
- `验收证据/候选战场美术联调-V5-540x960-RECOVERY-011/100-重新开始.png`

## 未完成 / 不得越级

- V5 仍是隔离候选；正式主场景与 Prefab 未替换。
- 用户美术签收仍待完成。早期炮塔母图生成时没有上传锁定玩法参考图，风格一致性不能宣称已获批准。
- 敌人现有 3 层是静态部件，仅有轻微呼吸/武器摆动；完整待机、攻击、受击、死亡与升级动画尚未完成。
- V5 专项视口 360×780、393×852、540×1108 尚未验收；本轮五视口 smoke harness 未到达 ready，记录为测试工具启动失败，没有将其计为产品失败或 PASS。
- Android 真机、微信/抖音小游戏构建、直播观众进退场平台事件、1000 塔性能未验证。
- 早期供应商生成 jobId 仍不可查询（404）；本轮使用本地资源完成候选集成，没有重复提交旧 jobId。

## 资源范围与基础设施

- 本轮只修改 `_assistant-temp/候选战场Cocos-V5隔离工程-20261020/` 下的候选脚本、构建/测试脚本及任务记录。
- 正式 `CocosCreator工程` 主场景未修改。
- 未触碰 4173、4174、4175、4180、4181、Serveo 或 17778；未创建隧道。
- 本次资源锁：`project:live-turret-defense:candidate-art-overlay-v5`、`project:live-turret-defense:cocos-v5-qa`、`project:live-turret-defense:task-board`。结束时须确认 checkpoint/operation 已写入并释放这三把锁。
