# 技能目录

本目录中的每个技能包必须遵循 [SKILL_UPDATE_PROTOCOL.md](./SKILL_UPDATE_PROTOCOL.md)。

## 更新原则

**先审定并修订权威指令源，完成规则验收并冻结版本，再更新对应 Skill。** 如果源指令存在缺陷，不得只修改技能描述掩盖问题。

## 技能包目录

- `storyboard-director-cn/`：中文剧本转分镜与独立质检技能。
- `ai-production-director-cn/`：跨任务 AI 制作总导演技能，按任务路由至游戏、影视资产/分镜或通用工程规则。

技能包的 `SOURCE_LOCK.json` 记录权威来源、版本、Git blob SHA 和打包文件；本地安装包是版本快照，不会自动跟随仓库更新。
