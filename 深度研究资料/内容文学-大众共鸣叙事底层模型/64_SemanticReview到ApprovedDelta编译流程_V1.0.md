# Semantic Review → Approved Delta 编译流程 V1.0

日期：2026-10-26

## 一、为什么还需要Review Apply

Parser输出的是高召回候选。

Semantic Reviewer输出的是逐候选语义裁决。

但 Narrative Auditor需要的是：

- 最终 Episode Delta
- 最终 Scene Contract

所以中间必须有一个：

# Review Apply Compiler

职责只有一个：

> **把已经完成语义审查的候选，编译成可交给Narrative Auditor的正式提案。**

---

# 二、硬规则

如果存在任何：

decision=escalate

则：
整次编译BLOCK。

如果：

decision=approve
但 canon_safe != true

则：
BLOCK。

如果：

review_required != false

则：
BLOCK。

如果：

transition_class=reset

不会被编译为合法Delta。

---

# 三、场景层也必须审查

Parser对Reward/Hook的识别同样只是候选。

所以Scene Review必须确认：

- approved_reward_channels
- reward description
- reward magnitude
- hook_valid
- state_change_candidate_ids
- commitments opened/paid

未经Scene Review：
不能生成最终Scene Contract。

---

# 四、输出

PASS时：

approved_episode_delta.json
approved_scene_contracts.json

然后继续：

Narrative Auditor

只有Narrative Auditor也PASS：

才能Commit Canon。

---

# 五、完整链路

script.md
↓
53 Parser
↓
extracted.json
↓
59/60 Semantic Reviewer
↓
review_bundle.json
↓
63 Review Apply
↓
approved Episode Delta / Scene Contract
↓
48 Narrative Auditor
↓
PASS
↓
Canon Commit

这是当前第一版闭环。
