# Semantic Review闭环代码级验收 V0.1

日期：2026-10-26

## 一、验收链路

Parser Candidate
→ Semantic Review
→ Review Bundle
→ Review Apply Compiler
→ Approved Episode Delta / Scene Contract
→ Narrative Auditor
→ Canon Commit

本轮重点验证：

1. 完整审查后是否能生成正式APPROVED变化；
2. 任一候选仍未解决时，是否能Fail Closed。

---

# 二、PASS案例

输入：

X1：
“母亲：我就知道，女儿心不在家。”

语义审查：
- classification = character_belief
- target_domain = knowledge
- owner = 母亲
- canon_safe = true
- review_required = false

注意：
它进入的是“母亲的belief”，不是World Fact。

X2：
“林晚：我最多陪两天。”

在结合已有B1边界与当前压力情境后：

- classification = actual_state_change
- target_domain = boundary
- target_state_id = B1
- transition_class = retain
- canon_safe = true

场景审查：

- approved_reward_channels = C3_agency
- reward magnitude = L2
- hook_valid = true

---

## 实际代码级结果

VERDICT:
PASS

生成正式变化ID：

- APPROVED_X1
- APPROVED_X2

Scene Contract引用：

- APPROVED_X2

Canon：

1 → 2

这说明：

候选ID不会直接成为正式状态ID引用；
经过语义审查后才进入APPROVED层。

---

# 三、BLOCK案例

将X2改为：

decision = escalate

其余不变。

实际结果：

VERDICT:
BLOCK

命中：

SR003
semantic review still unresolved

没有生成：
- episode_delta
- scene_contracts

符合Fail Closed设计。

---

# 四、Semantic Reviewer规则回归

此前示例把：

“我就知道……”

定义为character_belief。

参考路由器初版没有覆盖“我就知道”句式，
实际会降级为escalate。

已修复：

BELIEF_PREFIXES新增：
“我就知道”

保证：
示例、协议、代码一致。

---

# 五、Schema修复

62_semantic_review_bundle_schema_v1.json
初版通过外部$ref引用semantic_review_v1。

这会要求运行环境配置Schema Registry/Resolver。

为减少离线部署依赖，
已改为：

$defs.semantic_review
+ 本地 #/$defs/semantic_review 引用。

即：
Bundle Schema自包含。

---

# 六、当前闭环已具备

1. script.md解析
2. episode / scene切分
3. 候选人物与状态抽取
4. Reward / Commitment候选
5. Semantic Review
6. 候选分类
7. objective fact / belief / misunderstanding / emotion / state change分离
8. 未决项Fail Closed
9. Approved Delta编译
10. Approved Scene Contract编译
11. R000—R006 Narrative Auditor门禁
12. PASS后才允许Canon Commit

---

# 七、当前还没有伪装成“已解决”的部分

Semantic Reviewer目前的Python实现只是：

**保守规则路由器**

它能自动处理：
- 明显情绪
- 明显主观信念
- 明显未来承诺
- 明显可观察动作

但对于：

- 人物是否真的形成稳定边界
- 是否属于relapse而非reset
- 一段关系是否真正重组
- 同一句台词在复杂上下文中的真实含义
- 是否存在反讽、撒谎、策略性表达

仍必须：

escalate

生产版应由：
LLM Semantic Reviewer + 当前状态切片 + 场景上下文

完成语义裁决，
再由规则Auditor负责硬门禁。

---

# 八、当前生产架构

规则层负责：
“不能错”。

语义层负责：
“它到底是什么意思”。

创作层负责：
“下一步写什么更有价值”。

三层必须分离。

否则让同一个生成模型：

发明剧情
→ 解释剧情
→ 批准剧情

等于没有真正的质检。
