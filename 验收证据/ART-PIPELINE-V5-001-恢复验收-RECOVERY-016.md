# ART-PIPELINE-V5-001｜V5 候选单位比例迭代 RECOVERY-016

日期：2026-10-20
owner：agent-gpt6-art-recovery-20261020
projectId：live-turret-defense
状态：**CANDIDATE_SCALE_ITERATION / POST_SCALE_QA_PARTIAL / ART_APPROVAL_PENDING**

## 本轮修改

- 仅修改隔离候选工程脚本：`_assistant-temp/候选战场Cocos-V5隔离工程-20261020/assets/脚本/待审战场美术覆盖器.ts`
- 炮塔缩放由基础 0.255、每级增量 0.014 调整为基础 0.40、每级增量 0.018。
- 普通敌人缩放由 0.30 调整为 0.42，首领由 0.48 调整为 0.58。
- 修改前备份：`_assistant-temp/backup-overlay-v5-RECOVERY-016.ts`
- 对比图：`验收证据/候选战场美术联调-V5-RECOVERY-016/炮塔敌人比例调整前后对比.jpg`
- 正式 CocosCreator 工程和主场景未修改。

## 构建验证

- 构建脚本：`_assistant-temp/build_candidate_v5_recovery_016.py`
- 构建报告：`game-art/evidence/ART-PIPELINE-V5-001/V5-Cocos-Build-QA-RECOVERY-016.json`
- 结果：build success；Cocos Creator 3.8.2 CLI exit code 36（官方定义为构建成功）；TypeScript 错误 0；stderr 0 字节；89 PNG / 89 Meta；缺失 Meta 0；UUID 仍需按现有审计结论保持唯一。
- 构建耗时约 36.8 秒，构建产物入口存在。

## 修改后实测

- 360×780 隔离候选真实鼠标完整对局：PASS。
- 结果：第 3 波胜利，96 击杀，水晶 HP 100，24 座炮塔；重新开始恢复 ready、第 1 波、HP 100、9 座炮塔、0 击杀；JavaScript 异常 0。
- 证据：`验收证据/候选战场美术联调-V5-360x780-RECOVERY-016/真人操作完整一局.json`，截图包括 `01-玩家进场布塔.png`、`99-结局.png` 和 `100-重新开始.png`。
- 比例调整前后截图已检查：炮塔与敌人辨识度有所提高；画面仍偏稀疏，美术签收尚未通过。

## 尚未通过 / 受阻

- 修改后五视口 smoke 首次运行未进入 ready：CDP WebSocket 提前关闭（`ConnectionClosedError`），没有采集到游戏 JS 异常，也没有任何视口进入测试，因此该次记为测试工具启动失败，不记为产品失败或 PASS。
- 保存首次失败记录：`验收证据/候选战场美术联调-V5-五视口RECOVERY-016/五视口V5输入回归-首次运行失败.json`。
- 再次执行相同 smoke 测试的 PC MCP 命令调用被安全检查拦截；未尝试绕过。修改后 360×780 完整对局已独立通过，但修改后的 393×852、540×760、540×960、540×1108 尚未重新验证。
- RECOVERY-013 中五视口 5/5 的完整对局和输入 smoke 是比例修改前的基线证据，不能代替本轮比例修改后的回归。
- 不得把本轮称为五视口全部通过；正式 Prefab/主场景未替换。

## 后续恢复点

恢复可用的正常 PC MCP 测试执行后，先复跑五视口 smoke，再补齐修改后的其余视口回归。通过后继续候选美术比例/密度审查，待用户审美签收后才考虑提升正式 Prefab。Android、微信/抖音真机、直播进退场接口和 1000 塔性能仍未验收。
