# RECOVERY-027｜直播观众数据与事件桥回归

状态：CANDIDATE_QA_PASS / REAL_PLATFORM_PENDING

完成内容：
- 9座基础炮塔使用 base-* 内部身份，不再计入直播在线人数。
- base-* 为保留ID，外部直播事件无法离场或升级基础塔。
- 加入、离场、礼物统一经过直播事件桥，支持事件ID去重、队列与观众会话快照。
- 同一观众重复加入不会重复建塔；礼物升级对应观众炮塔；离线礼物可以恢复观众炮塔。
- 直播房间会话跨单局重开保留，在线人数和礼物累计不会被战斗 reset 清零。
- HUD显示在线人数与礼物累计。
- 现有观众+1、升级、离场真实按钮全部走同一事件桥。

验证：
- Cocos Web-Mobile：build success，Creator退出码36，TypeScript错误0，stderr0。
- 专项事件桥检查：19项全部通过，JS控制台错误0。
- 真实抖音/微信直播事件仍未接入，因此本任务不标记为真实平台完成。

证据：
- 验收证据/RECOVERY-027-直播事件桥/直播事件桥接口与真实按钮回归.json
- game-art/evidence/RECOVERY-027-live-event-build.json
