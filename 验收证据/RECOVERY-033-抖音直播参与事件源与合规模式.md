# RECOVERY-033｜抖音直播小玩法参与事件源与合规模式

日期：2026-10-22  
项目：live-turret-defense  
范围：隔离候选 Cocos Creator 3.8.2 工程；正式 CocosCreator工程 未修改。

## 已完成

1. 新增 `直播参与事件源.ts`
   - WebSocket 直播参与事件源。
   - 支持开发者后端标准化事件。
   - 评论“加入”/“888”映射为玩法参与加入。
   - 评论“退出”映射为玩法参与退出。
   - 礼物映射为 gift。
   - 无关评论与点赞不会被误当作加入/礼物。
   - 无 URL 时不伪装已连接。
   - stop 后不继续重连。

2. 平台模式
   - `standard`：普通 Web / Android / 普通小游戏模式，保留商店与永久经济。
   - `douyin-live-play`：直播小玩法模式。
   - 直播模式不宣称拥有“全员直播间进房/退房”能力，只表达显式玩法参与。
   - 直播模式禁用商店、禁用永久战备加成、禁用守城币结算奖励。

3. 控制器公开入口
   - `setPlatformMode()`
   - `attachDouyinParticipationWebSocket(url)`
   - `liveParticipationSourceSnapshot()`
   - `attachLiveEventSource()`
   - `detachLiveEventSource()`

## 三平台构建

当前候选代码重新构建：

- Web-Mobile：exit 36 / build success / TS 0 / stderr 0 / 288 files
- WeChat Game：exit 36 / build success / TS 0 / stderr 0 / 293 files
- ByteDance Mini Game：exit 36 / build success / TS 0 / stderr 0 / 291 files

三个产物中均确认包含：
- WebSocket 直播参与事件源
- douyin-live-play 模式
- platform-disabled 商店保护

## 本地 WebSocket 端到端验证

测试链路：

本地 mock WebSocket 服务
→ Cocos `WebSocket直播参与事件源`
→ `直播事件桥`
→ 炮塔/在线人数/礼物等级
→ detach

结果：PASS。

验证项：
- standard 模式商店和永久经济保留
- 已有永久升级档案可读
- 无 URL 不伪连接
- douyin-live-play 模式正确启用
- 直播模式忽略永久战备加成
- 直播模式隐藏商城和守城币 UI
- 程序接口购买也被双重阻断，档案不发生变化
- WebSocket 连接成功
- 评论“加入”/“888”/“退出”映射正确
- 礼物升级进入直播事件桥
- 无关评论、点赞被忽略
- 直播模式结算不发放守城币
- detach 正确停止事件源
- JavaScript 错误 0

## 普通模式回归

重新执行 RECOVERY-030：

- 商店存档真实鼠标端到端：PASS
- 火控与直播增幅效果：PASS
- 商店五视口：5/5 PASS
- 普通模式永久经济和本地存档未被直播模式改动破坏

## 边界

本轮没有真实抖音账号、直播间、access_token 或平台后端回调，因此不能把本地 WebSocket mock 验收冒充成真实抖音平台验收。

真实抖音接入仍需要：
1. 真实小游戏/直播小玩法账号与对应能力审批。
2. 服务端接收/鉴权平台互动数据。
3. 服务端转换为本项目标准化 WSS 数据。
4. 真开发者工具/真机/真直播间验证。

正式 Cocos 工程仍未修改，继续遵守 V5 美术签收门禁。
