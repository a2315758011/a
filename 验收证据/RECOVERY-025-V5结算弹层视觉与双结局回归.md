# RECOVERY-025｜V5结算弹层视觉收敛与双结局回归

日期：2026-10-21
范围：隔离候选 Cocos Creator 3.8.2 工程；正式 `CocosCreator工程` 未并入本轮候选改动。

## 完成与验收

- Cocos Web-Mobile 构建通过：Creator CLI 退出码 36（项目已确认 36 为官方构建成功码），日志包含 `build success`，TypeScript 错误 0，stderr 0，89 张 PNG 元数据完整。
- 构建产物 `assets/main/index.js` 实际包含 `V5结算弹层`、`守城成功`、`守城失败`、`再次守城`、`setBattleHudVisible`。
- 当前 Web-Mobile 构建目录中 Spine/WASM 文件数量为 0；候选工程未使用 Spine，隔离候选 engine modules 已关闭未使用的 Spine 模块。
- 胜利自然对局 PASS：第 3 波、96 击杀、HP 100、24 塔；结算显示“守城成功”，战斗 HUD 隐藏；真实点击“再次守城”后恢复 ready / HP100 / 第1波 / 9塔 / 0击杀，HUD 恢复；控制台错误 0。
- 失败自然对局 PASS：第 1 波、HP 0、23 击杀、1 个敌人剩余；结算显示“守城失败”，战斗 HUD 隐藏；真实点击“再次守城”后恢复 ready / HP100 / 第1波 / 9塔 / 0击杀，HUD 恢复；控制台错误 0。
- 五视口 smoke 5/5 PASS：360×780、393×852、540×760、540×960、540×1108；资源加载、HUD 可视、开始、观众+1、重开、结算隐藏状态均通过，控制台错误 0。
- 之前出现的 `[Spine] wasm load failed` 已定位为复用旧 Edge DevTools Page 的历史控制台事件。改为创建全新 Page target 并禁用缓存后，当前构建的胜负回归控制台错误均为 0。

## 视觉复核

实际截图已人工复核。结算态现在隐藏顶部状态条、底部战斗按钮和镜头按钮，背景仅保留压暗后的战场；面板使用现有 V5 深蓝/黄铜/青色资产与 Cocos Graphics，胜负标题、统计、按钮文本使用 Cocos Label。

- 胜利截图：`验收证据/候选战场美术联调-V5-RECOVERY-025-胜利结算新目标回归/06-胜利结算弹层-精简HUD.png`
- 失败截图：`验收证据/候选战场美术联调-V5-RECOVERY-025-失败结算新目标回归/06-失败结算弹层-精简HUD.png`

## 关键证据

- `game-art/evidence/RECOVERY-025-settlement-ui-build.json`
- `game-art/evidence/RECOVERY-025-settlement-ui-runtime-audit.json`
- `验收证据/候选战场美术联调-V5-RECOVERY-025-胜利结算新目标回归/新目标胜利结算回归.json`
- `验收证据/候选战场美术联调-V5-RECOVERY-025-失败结算新目标回归/新目标失败结算回归.json`
- `验收证据/候选战场美术联调-V5-五视口RECOVERY-025/五视口V5输入与HUD结算状态回归.json`

## 门禁仍保留

- V5 候选整体美术仍未获得用户正式审美签收，因此本轮不将候选结算覆盖器合入正式主场景/Prefab。
- Android、微信小游戏、抖音小游戏真机未验收。
- 直播观众真实进退场/礼物网络接口未完成。
- 1000 塔低端真机性能未验收。
