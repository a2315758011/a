# AI 制作总导演技能（离线版）

目录：`skills/ai-production-director-cn/`

## 包含什么
- `SKILL.md`：标准 Agent Skills 格式的触发条件、路由和执行流程。
- `references/`：完整权威规则快照，包含游戏总指令、影视资产、分镜编写与自检、通用工程指令及统一入口。
- `SOURCE_LOCK.json`：源文件版本、Git blob SHA、字符数及包内目标路径，便于审计漂移。
- `README.md`：安装、使用与限制说明。

## 安装/使用
1. 如果 AI 客户端支持 Agent Skills 导入，将整个 `ai-production-director-cn` 文件夹作为一个技能导入；不要只上传 SKILL.md 而丢掉 references。
2. 如果客户端支持本地 Skills 目录，把整个文件夹复制到该客户端的 Skills 目录。
3. 如果使用 ChatGPT 的普通聊天且没有 Skills 安装入口，不能仅靠仓库链接自动加载。可以将 `SKILL.md` 与当前任务所需的 references 文件上传到对话；或者把 SKILL.md 内容放进自定义 GPT 的 Instructions，并将 references 作为 Knowledge 文件。是否能创建/分享自定义 GPT 取决于账号权限。
4. 每次新聊天都应确认客户端实际加载了该技能及所需引用。技能包不会自行安装，也不会自动获得电脑、GitHub、生成模型或终端权限。

## 验证
- 必须能够读取 SKILL.md 和所有引用文件。
- 触发后，模型应根据任务选择相应规则并指出实际读取的规则章节/标记。
- 文件可读不等于业务任务完成。实际成果仍须按相关规则验收。
- 当前包为 GitHub main 分支快照；下载/安装后的本地版本不会自动跟随仓库更新。

## 维护规则
更新顺序固定为：**权威指令源审查/修订 → 源指令验收 → 冻结来源 SHA → 更新 references 与 SKILL.md → 一致性检查 → 技能包测试 → 发布**。
详见 `../SKILL_UPDATE_PROTOCOL.md`。
