# 剧本文本自动解析与Canon写入规则 V1.0

日期：2026-10-26

## 核心原则

自动解析器只负责**提出候选**，不拥有Canon写权限。

原因：
- 对话不等于事实；
- 人物说谎、误解、讽刺都会制造假事实；
- ‘我不会再管你’可能是情绪台词，不一定等于稳定边界；
- ‘我终于明白’可能只是一时判断；
- 同一句话在不同上下文可能属于不同Reward通道。

所以流程必须是：

Script → Extracted Candidates → Semantic Review → State Delta → Narrative Auditor → Commit

## 自动抽取内容

当前参考解析器支持：
- 分集标题；
- 场景边界；
- 角色台词；
- Knowledge候选；
- Boundary候选；
- Relationship候选；
- Identity候选；
- Competence候选；
- Resource候选；
- Commitment候选；
- C1—C5 Reward候选；
- Scene Contract草稿。

## 置信度规则

每个候选带 confidence 与 review_required。

无论置信度多高：
review_required 默认 true。

这是有意设计。

因为解析器任务是高召回发现，不是自动裁决事实。

## 写入门禁

只有候选被确认后才能：
1. 映射到已有state_id；
2. 填写真实before；
3. 选择 retain / relapse / revision / strategy；
4. 若疑似 reset，交给 Continuity Auditor；
5. 确认Reward是否persists；
6. 才能进入正式Episode Delta。

## 禁止自动完成的事情

- 自动把角色台词写成World Fact；
- 自动判断人物说的是真话；
- 自动把一句拒绝升级成永久边界；
- 自动把单次成功升级成能力形成；
- 自动把单次亲密动作升级成关系承诺；
- 自动把草稿分支写入Canon。

## 端到端目标

最终系统不是“文本抽实体”。

而是：

**把自由文本转换成可审计的叙事状态变化提案。**

这使现有剧本、分集脚本、分镜脚本都能逐步进入统一State Store。