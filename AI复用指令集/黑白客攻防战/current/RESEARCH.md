# V8.0｜30轮联网研究与对抗升级摘要

日期：2026-10-22

这份文件只记录可审计的研究结论和设计变化，不记录私有思维链。

## 外部研究→设计变化

1. **OWASP GenAI Red Teaming Manual v1.0（2026-10-20）**  
   八阶段方法强调规划、侦察、攻击面映射、影响验证、可复现证据和修复闭环。V8要求每个研究结论必须落到规则变化、测试变化或可执行实验。  
   https://genai.owasp.org/resource/genai-red-teaming-manual-version-1-0/

2. **OWASP Agent Control Standard（2026-09-01）**  
   Agent需要可观察、可追踪并能在运行时施加控制。V8明确：自然语言规则不能冒充真正的运行时边界。  
   https://genai.owasp.org/resource/agent-control-standard-acs/

3. **OWASP Top 10 for Agentic Applications 2026**  
   风险覆盖Goal Hijack、Tool Misuse、Identity/Privilege Abuse、Memory/Context Poisoning等。V8从“单句输入”扩展到完整Agent链路。  
   https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/

4. **OWASP 2026 Exploit Roundups**  
   多个案例显示网页、日志、连接器和遥测数据可以影响Agent后续行为。V8把外部内容中的指令性文字默认视为不可信数据。  
   https://genai.owasp.org/2026/10/08/genai-and-agentic-ai-exploit-roundup-q3-2026/

5. **NIST AI 100-2e2025**  
   攻击应按目标、攻击者能力、知识和生命周期阶段分析。V8因此分离“对象标签”和“具体动作/能力路径”。  
   https://www.nist.gov/publications/adversarial-machine-learning-taxonomy-and-terminology-attacks-and-mitigations-0

6. **NIST ARIA Evaluation Planning Manual（2026-09-18）**  
   评估需要结合Model Testing、Red Teaming和User Testing。V8不再用单一静态分数声称能力提升。  
   https://www.nist.gov/publications/aria-evaluation-planning-manual-elements-aria-style-ai-evaluations

7. **AgentLAB（ICML 2026）**  
   长程攻击包括intent hijacking、tool chaining、task injection、objective drifting和memory poisoning；单轮防御不足。V8新增真正的跨轮自适应序列。  
   https://proceedings.mlr.press/v306/jiang26as.html

8. **Adaptive Adversaries（2026）**  
   攻击者观察防御者响应后持续调整，会发现静态攻击池遗漏的弱点。V8默认“对手会学习”。  
   https://arxiv.org/abs/2607.18063

9. **Agent Security Bench（ICLR 2025）**  
   Agent攻击面跨提示、工具和记忆，同时需要权衡安全与效用。V8把正常任务控制作为强制验收。  
   https://proceedings.iclr.cc/paper_files/paper/2025/hash/5750f91d8fb9d5c02bd8ad2c3b44456b-Abstract-Conference.html

10. **AgentDyn（2026）**  
    静态、简单基准容易低估真实复杂性，防御也容易产生过度防御。V8加入“有用但不可信”的第三方内容和部署式对照。  
    https://arxiv.org/abs/2602.03117

11. **ToolSafe / TS-Bench（ACL Findings 2026）**  
    步级动作判断可以同时减少不安全调用并提高正常任务完成。V8将动作判断放在具体工具行为层。  
    https://aclanthology.org/2026.findings-acl.1850/

12. **BackdoorAgent（ACL Findings 2026）**  
    影响可以在planning、memory、tool-use之间持续传播。V8增加跨阶段来源与持久范围记录。  
    https://aclanthology.org/2026.findings-acl.791/

13. **Mem2ActBench（ACL 2026）**  
    关键不只是记住事实，而是能否把记忆正确转成工具选择和参数。V8把“证据/记忆→行动转换”单独验收。  
    https://aclanthology.org/2026.acl-long.370/

14. **AgencyBench（ACL 2026）**  
    长程任务暴露资源效率、自我纠错和工具偏好差异。V8增加长程状态、重复动作和时间效率。  
    https://aclanthology.org/2026.acl-long.337/

15. **AuditBench（2026）**  
    某个工具单独有效，不代表Agent会正确使用它，存在tool-to-agent gap。V8把“工具证据是否改变正确下一步”单列。  
    https://alignment.anthropic.com/2026/auditbench/

16. **Training Alignment Auditors via Reinforcement Learning（2026-10）**  
    点式奖励会被reward hack；pairwise和benign目标校准更稳。V8使用最小差异配对与正常任务控制。  
    https://alignment.anthropic.com/2026/training-alignment-auditors/

17. **Coding Audit Realism（2026）**  
    使用真实系统提示、工具定义和代码库会显著改善审计现实度。V8把公开回归和deployment-like测试分开。  
    https://alignment.anthropic.com/2026/coding-audit-realism/

## 30轮审计对应关系

1 权威洗白 → 来源核验  
2 标签操纵 → ACTION级判断  
3 真伪混合 → 局部可信度而非全局信任  
4 局部限制扩散 → 依赖图传播  
5 自我证明循环 → SOURCE_GRAPH  
6 规则DoS → META_BUDGET  
7 矛盾洪泛 → 判别实验优先  
8 紧迫性 → 真实时间源  
9 情绪/激将 → 决策阈值不随语气变化  
10 目标漂移 → SUCCESS_ORACLE  
11 旧记忆污染 → currentness核验  
12 长期记忆污染 → provenance持久化  
13 工具输出污染 → 数据/指令分离  
14 工具链组合 → capability path  
15 跨阶段传播 → PLAN→MEMORY→TOOL→ACTION追踪  
16 有用但不可信内容 → 保留事实、隔离控制性文字  
17 自适应攻击者 → 后轮观察前轮结果  
18 多攻击者多样性 → 蓝方留出不由单一模板构造  
19 评测觉察 → explicit-eval vs deployment-like  
20 Reward hacking → 业务oracle优先  
21 单点评分偏差 → pairwise  
22 能力完整性 → reachable ≠ in-scope  
23 provenance → 独立来源组  
24 证据到行动转换 → TOOL_TO_AGENT_GAP  
25 高价值工具未充分使用 → 工具选择质量  
26 噪声证据误权重 → 强/弱证据对照  
27 正常任务误拦截 → benign controls  
28 长程状态与资源效率 → 重复动作/时间账本  
29 多Agent结论污染 → 他人结论同样检查来源  
30 业务oracle与代理冲突 → 真实状态决定胜负

## V8公开基准结构

- 30个稳定研究/攻击家族；
- 30轮审计映射；
- 60个公开案例；
- 15组最小差异配对；
- 5条自适应多轮序列；
- 22个正常任务控制（含配对中的正常对照）。

公开案例只用于回归。用户回来后的真正比赛仍应使用未写入仓库的蓝方留出攻击。

## 当前状态

已完成：联网研究、V8规则、V8公开回归结构、云端发布。  
尚未完成：当前模型在V8上的真实逐案执行、V7/V8同预算A/B、蓝方隐藏盲测。  
因此不能宣称“已经变强到能赢用户”；只能宣称“下一轮的对抗规则和评测设计更难被已知漏洞钻空子”。
