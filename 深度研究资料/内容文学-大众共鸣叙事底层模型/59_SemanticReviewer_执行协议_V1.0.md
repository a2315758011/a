# Semantic Reviewer 执行协议 V1.0

日期：2026-10-26

## 一、职责

Semantic Reviewer 位于：

Parser
→ Semantic Reviewer
→ Narrative Auditor
→ Canon Commit

它不是创作Agent。

它只回答：

> **解析器抓到的这句话/动作，究竟代表什么？**

---

# 二、八类语义分类

## 1. objective_fact

客观发生且能进入世界事实。

例：

“护士把住院单递给林晚。”

可以形成：
WORLD / RESOURCE / EVENT 候选。

---

## 2. character_belief

只是某角色相信。

例：

母亲：
“女儿嫁出去以后心就不在家了。”

这不是World Fact。

应该写成：

mother believes:
daughter no longer prioritizes family.

---

## 3. misunderstanding

角色相信，
但当前Canon已有相反事实，
或后续将证明错误。

必须挂在：
CHARACTER_KNOWLEDGE / belief

禁止写入WORLD_STATE。

---

## 4. emotion_only

只是情绪表达。

例：

“我恨死你了。”

除非后续行为明确形成关系状态变化，
否则不能自动写成：

RELATIONSHIP = permanent hatred.

---

## 5. actual_state_change

确实改变：

- 边界
- 关系
- 能力
- 身份
- 资源
- 弧线

必须有可观察证据。

原则：

# Change Must Leave Evidence.

---

## 6. commitment

角色对未来作出明确承诺。

注意：

承诺 ≠ 已完成状态。

“我明天来陪护”
进入Commitment Ledger。

只有明天真的出现：
才能形成结果状态。

---

## 7. no_state_change

重复说明、气氛、装饰动作，
对Canon没有新的状态价值。

可以保留在剧本，
但不入State Ledger。

---

## 8. ambiguous

无法可靠裁决。

必须：

decision = escalate

不能为了自动化强行猜。

---

# 三、裁决顺序

每个candidate按顺序问：

### Q1
这是某人“说的”，还是实际“发生的”？

台词优先视为：
belief / commitment / emotion，
而不是objective_fact。

### Q2
是否有外部证据？

例如：
- 文件
- 录像
- 第三方确认
- 明确行为后果
- 已发生动作

有证据才提高objective_fact可信度。

### Q3
当前Canon是否已有同类状态？

如果有：
判断是：

retain
relapse
revision
strategy
reset

### Q4
这个候选是否改变未来可用状态？

如果不会：
no_state_change。

### Q5
是否存在冲突或信息不足？

有：
escalate。

---

# 四、对话事实安全规则

以下句式默认不得直接进入World State：

- 我觉得……
- 我知道你就是……
- 你从来……
- 你总是……
- 一定是……
- 肯定……
- 我恨你……
- 我不会原谅……
- 你根本不爱我……

这些首先是：

belief / emotion / commitment candidate。

---

# 五、边界识别规则

一句：

“我不管你了。”

不能自动升级稳定边界。

至少需要：

1. 明确对象；
2. 明确行为范围；
3. 后续实际执行；
4. 面对压力时是否保留。

首次出现可记录：

Boundary candidate / fragile

只有经历测试后才允许：

developing / stable。

---

# 六、关系变化规则

“拥抱”不自动等于：

关系完全修复。

“吵架”也不自动等于：

关系彻底破裂。

关系状态要看：

- 是否改变信任；
- 是否改变承诺；
- 是否改变资源/权力；
- 是否改变后续行为规则。

---

# 七、Knowledge规则

角色获得Knowledge必须标明来源：

- witnessed
- heard
- inferred
- disclosed
- document
- media
- mistaken

如果没有来源：

reject / escalate。

---

# 八、transition_class规则

## retain
已有状态被再次证明。

## relapse
人物知道旧状态，但在压力下退回。

必须保留：
memory + pressure + awareness。

## revision
新信息让人物合理修改判断。

## strategy
角色表面违背状态，但其实是有意识策略。

## reset
无解释撤销既有成长。

Semantic Reviewer如果判断reset：

decision必须：
reject 或 escalate。

不能approve。

---

# 九、输出合同

每个candidate必须输出：

- candidate_id
- classification
- decision
- confidence
- target_domain
- target_state_id
- owner
- before
- proposed_after
- transition_class
- evidence
- reason
- canon_safe
- review_required=false

只有：

decision=approve
且
canon_safe=true
且
transition_class != reset

才允许进入正式Delta。

---

# 十、置信度门槛

建议：

0.85以上：
可自动approve，但仍过Narrative Auditor。

0.65—0.84：
需要第二审查器复核。

低于0.65：
escalate。

这不是“真理概率”，
只是流程置信度。

---

# 十一、Semantic Reviewer禁止事项

禁止：

- 为了让剧情更顺而修改Canon；
- 把角色观点当事实；
- 把未来承诺当已发生；
- 把一次行为当稳定人格；
- 把一次退步当角色完全重置；
- 自动补写剧本里不存在的因果。

---

# 十二、最终目标

Parser回答：

> “这里可能有东西。”

Semantic Reviewer回答：

> “这东西究竟是什么。”

Narrative Auditor回答：

> “即使它是真的，这个变化合法吗？”

Canon Store只接受：

> **被识别、被裁决、被验证后的状态变化。**
