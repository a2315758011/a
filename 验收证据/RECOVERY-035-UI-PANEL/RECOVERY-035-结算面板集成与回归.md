# RECOVERY-035｜结算面板专用像素美术与候选运行时回归

## 完成内容

- 通过工作站共享 Generation Gateway 生成新的静态结算面板；Job ID：e5e90483-d544-4e55-a3c7-2463294afec6。
- Provider 原图保存在 game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/provider-output.png，未覆盖旧任务资产。
- 处理后 Master：game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/master.png，512×636、RGBA，SHA-256 AFC5887638F7F86E3D3AA28E0785BFD0AFE175478937FE79DC0CCF088B24E1DB。
- 已把面板作为真实 Sprite 接入隔离 Cocos V5 候选；结算暗幕、标题、统计文本、水晶图标、两个按钮和事件处理保持独立，未烘焙中文文字。

## 验证结果

| 验收项 | 实测结果 |
|---|---|
| Alpha / 像素QA | PASS；真透明背景、面板中心不透明、48色、残留不透明洋红 0 |
| Cocos Creator Web-Mobile 构建 | PASS；exit 36（官方成功码）、build success、TS错误0、stderr0、PNG 108、缺失Meta 0 |
| 自然胜利 | 第3波、96杀、HP100、24塔、15名在线观众；结算面板显示 |
| 自然失败 | 第3波、74杀、HP0、9座基础塔、0在线观众；结算面板显示 |
| 竖屏布局 | 胜利5/5 + 失败5/5，合计10/10 |
| 返回主界面 / 再次守城 | PASS；返回菜单隐藏结算面板和战斗HUD；房间级观众会话按设计保留；再次守城恢复ready、HP100、9基础塔 |
| JavaScript控制台错误 | 0 |

## 证据文件

- game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/gateway-job.json
- game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/alpha-pixel-qa.json
- game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/cocos-build-qa.json
- game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/manifest.json
- 验收证据/RECOVERY-035-UI-PANEL/真实Cocos双结局与五视口回归.json
- 验收证据/RECOVERY-035-UI-PANEL/01-natural-win-360x780.png
- 验收证据/RECOVERY-035-UI-PANEL/02-natural-loss-360x780.png

## 验收边界

- 本任务只修改隔离候选工程和美术候选资源；正式 Cocos 场景、Prefab、正式运行资源未修改。
- 资产状态为 candidate_runtime_qa_pass，approved=false、formalPresent=false。人工美术签收之前不得提升到正式资产。
- Android、微信小游戏、抖音小游戏真机和真实平台直播事件仍需独立验收。
- 第一次QA结果中有一条旧断言错误地要求返回主菜单后只剩9塔；真实记录证明房间级15名观众会跨菜单保留，正确状态是24塔、15在线、HP100、菜单显示、结算面板与战斗HUD隐藏。原始报告保留为 真实Cocos双结局与五视口回归-before-assertion-correction.json，修正后的断言和依据已写入最终JSON。
