# 多Agent编剧生产流水线 V1.0

日期：2026-10-26

## 一、目标

把“研究 → 策划 → 编剧 → 分镜 → 质检”改造成共享状态驱动的生产流水线。

核心原则：

> **所有Agent共享同一个叙事事实源，但拥有不同职责和写权限。**

不是让多个Agent各自读完整剧本后自由发挥。

---

# 二、为什么要共享状态而不是共享全文

2026 MAGNET/ATLAS 的长篇叙事研究使用：
- persona-grounded character agents
- shared structured world state
- evolving story goals
- critic refinement
- graph-based hallucination checking

并报告相较单模型与既有方法，在100页故事中显著减少编辑标注与幻觉。

来源：
https://arxiv.org/abs/2607.00918

2026 Agentsensus进一步指出：
多角色各自保存私有记忆会造成重复与不同步；共享事件记忆可以合并同一事件并标记见证者，从而减少重复存储并保持共享事实。

来源：
https://arxiv.org/abs/2609.32297

2026 NarraWorld则把长篇记忆拆为：
- world facts
- per-character beliefs
- open developments
- hypothetical branches

来源：
https://arxiv.org/abs/2609.32401

因此本项目采用：

# Shared World, Private Mind

世界事实共享；
角色认知分离；
未决剧情集中管理；
假设分支不直接污染正式状态。

---

# 三、Agent架构

## A0｜总导演 / Orchestrator

只负责：
- 接收项目目标
- 拆阶段
- 指派任务
- 检查门禁结果
- 决定是否进入下一阶段

禁止：
直接偷偷改世界事实。

---

## A1｜研究Agent

输入：
- 目标受众
- 价值洼地候选
- 真实需求语料
- 媒介供给

输出：
- Experience Structure
- Narrative Breakpoint
- 后遗层
- 目标回报通道
- 反例

写权限：
RESEARCH_STATE

无权限：
改变剧情正式Canon。

---

## A2｜故事架构Agent

负责：
- 总主题
- 核心冲突
- 主角弧线
- 季/幕/集目标
- Commitment Ledger 初始承诺

输出：
STORY_PLAN

必须声明：
- 这一季人物真正要学什么
- 哪些旧课题不能重复
- 最终状态是什么

---

## A3｜角色Agent群

每个主要角色独立一个Agent。

输入：
- 该角色persona
- 角色私有knowledge
- 当前relationship state
- 当前goal
- 当前fear / desire / shame
- 当前可见事件

输出只能是：
- candidate_action
- internal_reason
- expected_state_transition

角色Agent不能直接决定：
“世界上发生了什么”。

只能提出：
“这个角色在当前已知事实下会怎么做”。

---

## A4｜Scene Planner

把当前集目标转成场景。

每场必须包含：

1. Before State
2. Trigger
3. Character Choice
4. Opposition
5. Consequence
6. Reward Channel
7. After State
8. Hook / Open Development

如果场景结束后没有任何状态变化，
标记：
POSSIBLE_PADDING。

---

## A5｜Writer

只负责：
把已批准的Scene Plan写成可读剧本。

不得：
- 临时增加亲属关系
- 临时改变人物知识
- 临时发明关键资产
- 临时让人物完成未批准的弧线跳跃

如果需要新事实：
发起 CHANGE_REQUEST。

---

## A6｜Continuity Auditor

专门检查：

- Fact Gate
- Knowledge Gate
- State Gate
- Arc Gate
- Commitment Gate

任何 RESET / Canon Conflict：
FAIL CLOSED。

---

## A7｜Reward Auditor

检查：

- C1 Outcome
- C2 Relationship
- C3 Agency
- C4 Meaning
- C5 Competence

以及：
- Global Reward Gap
- Reward Fragmentation
- Reward Reversal
- Reward Debt

它不判断“文学性”，
只判断：

> 这一集是否让观众获得新的有效价值。

---

## A8｜Human-Likeness / Dialogue Auditor

检查：
- 角色声音是否区分
- 是否出现同义重复
- 是否过度解释心理
- 是否所有角色都像同一个AI
- 是否用台词代替行动
- 是否存在“为了给观众讲明白而说人不会说的话”

---

## A9｜Storyboard Agent

只在剧本通过A6/A7/A8后工作。

读取：
- approved script
- scene spatial state
- character visual state
- prop state
- camera continuity

输出：
- 镜头
- 景别
- 机位
- 动作
- 画面状态变化

不得反向修改剧情Canon。

如发现无法视觉化：
提交 VISUALIZATION_BLOCKER，
返回Scene Planner修。

---

## A10｜Final QA

最终验收：

- Canon
- State
- Reward
- Arc
- Dialogue
- Visual continuity
- 未偿伏笔
- 下一集状态写回

只有PASS后：
该集才能成为正式Canon。

---

# 四、写权限模型

## 单一事实源
Narrative State Store

## Agent不得直接互相改状态

所有变化必须经过：

PROPOSE
→ VALIDATE
→ COMMIT

### PROPOSE
Agent提出候选状态转移。

### VALIDATE
Continuity + Reward + Arc 检查。

### COMMIT
Orchestrator批准后写入正式状态。

这可以防止：
两个Agent同时改同一人物关系造成状态分叉。

---

# 五、正式状态 vs 假设分支

必须分：

## CANON
已经发生的正式故事。

## DRAFT
正在生成、尚未批准。

## HYPOTHETICAL
用于比较的备选方案。

任何HYPOTHETICAL内容：
不得被角色Agent当成已发生事实。

---

# 六、角色知识必须独立

共享事件不等于所有角色都知道。

事件结构：

- event_id
- objective_fact
- witnesses
- heard_by
- inferred_by
- misunderstood_by

例：

母亲私下把钱转给弟弟。

世界事实：
发生。

母亲：
知道。

弟弟：
知道。

女主：
不知道。

观众：
可能知道。

这样才能避免：
角色突然“读到剧本”。

---

# 七、每集生产流水线

## Step 1｜Load
载入：
- Canon State
- Character Private Views
- Open Commitments
- Arc State
- Reward Debt

## Step 2｜Episode Goal
只定义1个主推进目标 + 最多2个次目标。

## Step 3｜Candidate Scenes
Scene Planner生成候选场景。

## Step 4｜Character Simulation
角色Agent根据自己的认知提出反应。

## Step 5｜Conflict Resolution
Planner合并冲突，不强迫所有角色服务剧情。

## Step 6｜Transition Validation
检查状态是否合法。

## Step 7｜Reward Validation
确保至少有一个有效回报通道，或明确记录合理延迟。

## Step 8｜Write
Writer写正式剧本。

## Step 9｜Audit
Continuity / Reward / Dialogue 三审。

## Step 10｜Local Repair
只修失败节点。

## Step 11｜Commit
更新正式Canon。

## Step 12｜Snapshot
保存：
- episode summary
- state delta
- unresolved commitments
- reward ledger
- next episode risks

---

# 八、失败关闭原则

以下情况禁止自动继续：

1. Canon冲突
2. 角色使用未知信息
3. 无解释Reset
4. 重复已完成弧线
5. 关键状态变化未更新账本
6. 未偿承诺持续累积超过阈值
7. 连续Global Reward Gap
8. 场景没有任何状态变化且无明确氛围/伏笔价值

这叫：

# Fail Closed Narrative Generation

不是：
“有问题也先写下去以后再修”。

---

# 九、与Google 2026长视频多Agent研究的连接

Google 2026 AI video co-director把长视频生成视为：
- global optimization
- world-state tracking
- multi-agent orchestration
- closed-loop refinement

并明确指出线性链式生成容易出现：
- semantic drift
- feature drift
- cascading failures

来源：
https://research.google/blog/coherent-long-form-video-generation/

这说明：
从剧本一路到分镜/视频，
共享状态不能在“文字剧本完成后”就停止。

角色外观、服装、场景、道具、镜头空间关系同样应该继续挂在同一个状态系统。

---

# 十、最终架构

Research
↓
Story Architecture
↓
Shared Narrative State
↓
Character Agents
↓
Scene Planner
↓
Transition Gate
↓
Reward Gate
↓
Writer
↓
Continuity / Dialogue Audit
↓
Storyboard
↓
Visual Continuity Gate
↓
Final QA
↓
Canon Commit

所有Agent围绕一个原则：

> **可以提出新故事，但不能各自拥有不同版本的现实。**
