# Narrative Auditor 自动审计规则 V1.0

日期：2026-10-26

## 一、目标

把“下一集能不能写”从主观判断改成：结构校验 + 语义门禁 + 风险诊断。

JSON Schema负责结构合法性；Narrative Auditor负责跨集语义合法性。

JSON Schema Draft 2020-12：https://json-schema.org/draft/2020-12/
ConWriter：https://aclanthology.org/2026.findings-emnlp.359/
CANVAS：https://aclanthology.org/2026.findings-emnlp.92/

## 二、硬阻断规则

### R001 Canon Version
to_canon_version 必须等于 from_canon_version + 1，且 from 必须等于当前 Canon 版本。否则 BLOCK。

### R002 Reset
任何 change.transition_class == reset：BLOCK。若实际是 relapse / revision / strategy，必须补 cause 与 evidence 后重新提交。

### R003 Locked Canon
WORLD_STATE 中 mutable=false 的事实不得 update/remove。否则 BLOCK。

### R004 Knowledge Leak
角色新增知识必须有 witnessed / heard / inferred / disclosure 等来源证据。无来源 BLOCK。

### R005 Forbidden Reset
若 change 命中角色 forbidden_resets 且不属于 relapse/revision/strategy：BLOCK。

### R006 Completed Arc Reopen
已完成弧线的 forbidden_repetition 被重新当成从零课题开启：BLOCK。

## 三、高风险但不自动阻断

W101 Reward Reversal：此前 persists=true 的回报被无解释撤销，HIGH WARNING。
W102 Commitment Debt：旧承诺超过自己的 expected_payoff_window 仍未 paid/abandoned，WARNING。
W103 Global Reward Gap：Scene/Episode 中 C1—C5 为空且 state_changes 为空，标记 possible_padding/global_reward_gap。
W104 False Progress：Hook 存在但 After State 不变、无 Meaning 回报，WARNING。
W105 Reward Fragmentation：支线反复打开但没有持续状态沉淀，WARNING。
W106 Arc Exhaustion：主角没有新的 unresolved_learning，却不断追加同型外部冲突，WARNING。

## 四、State Retention

重要状态再次被测试时：retain=1.0；有因果的 relapse/revision/strategy=0.5；reset=0。
分维度输出 Knowledge / Boundary / Relationship / Competence / Identity / Resource / Canon，不合成伪精确总分。

## 五、Reward

五通道：C1 Outcome、C2 Relationship、C3 Agency、C4 Meaning、C5 Competence。
每个 reward 必须有 scene_id、magnitude、description、persists。

## 六、Scene Transition Contract

场景至少明确 Before State、Trigger、Choice、Opposition、Consequence、After State。
若 state_changes、reward_channels、commitments_opened/paid 均为空且 hook.present=false，则 POSSIBLE_PADDING。

## 七、自动审计输出

VERDICT: PASS | REPAIR | BLOCK
BLOCKERS: rule_id / target / evidence
WARNINGS: rule_id / target / explanation
REWARD: channels / global_gap
STATE_RETENTION: 分维度
COMMITMENT: opened / paid / oldest_open
NEXT_ACTION: commit | local_repair | return_to_planner

## 八、禁止伪精确

当前审计器不输出“剧本87.4分”。它首先判断状态转移是否自洽、是否推进、是否撤销既有回报。商业效果仍必须用留存、完播、评论、收藏和付费数据验证。