# 工程任务观察站｜中文维护手册

**当前状态：GitHub 代码已提交，云端后端和采集器已完成首轮本地测试；尚未部署为真正的 HTTPS 在线服务。**

本工程解决三个实际问题：聊天网页崩溃后找不回执行位置；本机 MCP 不稳定时看不到最后进度；不知道哪条任务依赖链发生故障。

## 你会看到什么

1. **任务进度百分比**：只把通过验收的任务计入完成数，不根据 AI 的口头承诺增加百分比。
2. **任务执行关系图**：金色表示验收通过；蓝色表示执行中；红色表示失败或受故障影响；黄色表示等待前置依赖。
3. **故障定位**：点击任务查看负责人、最后成功步骤、阻塞原因、恢复位置和证据。
4. **连接状态**：本机停止上报超过 90 秒后，云端显示最后已知记录和采集超时，而不是虚构实时执行。
5. **中文维护**：状态和操作说明使用中文；代码所需固定技术标识无需用户维护。

## 文件结构

| 目录或文件 | 作用 |
| --- | --- |
| `public/index.html` | 正式云端中文网页；只能读取云端受保护的真实状态或手动查看演示 |
| `public/snapshot.json` | 明确标注的模拟演示，不包含真实项目 |
| `cloudflare/worker.mjs` | 云端接口、读取和写入鉴权、状态快照、采集器心跳 |
| `cloudflare/schema.sql` | 数据库建表和查询索引 |
| `cloudflare/wrangler.toml` | 云端发布配置，数据库 ID 是占位符 |
| `collector/collector.cjs` | Windows 工程任务采集、离线排队、自动重试 |
| `tests/integration.test.cjs` | 权限、数据、断线恢复及乱序事件测试 |
| `index.html` | 旧版 GitHub 源码演示入口；生产部署使用 public 目录 |
| `.github/workflows/cloud-task-observatory-test.yml` | 自动检查代码和执行 Node.js 回归测试 |

## 工程如何工作

`Project Orchestrator任务文件 → 本地采集器 → HTTPS云端接口 → D1数据库 → 中文看板`

采集器不会修改原任务数据。它只读取 `.project-orchestrator/tasks` 和 `.project-orchestrator/status` 中有真实更新时间的任务，并使用事件唯一 ID 去重。状态文件没有更新时间时不会冒称正在执行。网络中断时，先将事件写入本地队列；恢复联网后按批次补发。心跳接口独立发送，避免任务无变化时误判采集器离线。

**隐私默认值**：任务标题会先做基础脱敏；恢复文字/错误细节默认不上传，必须显式启用 `ALLOW_RECOVERY_TEXT=true`。这仍不是绝对的个人信息识别器，项目名称和任务标题本身也应避免包含秘密。

**现阶段自动采集范围**：已接入 Project Orchestrator 的任务。未接入的 AI 聊天操作、浏览器点击或其他软件运行过程，不能自动完整监控。后续需要针对每一种执行器接入事件适配器，不能宣称已经捕获全部 AI 活动。

## GitHub 自动部署入口（已加入仓库）

仓库已加入手动触发的部署工作流：`.github/workflows/部署云端任务看板.yml`。它会先检查凭据，再运行数据库迁移、写入 Worker 密文、发布网页和接口。它不会自动在每次代码提交时发布生产版本。

部署前仅需在 GitHub 仓库的 **Settings → Environments → cloud-production** 配置以下项目：

| 类型 | 名称 | 作用 |
| --- | --- | --- |
| 环境机密 | `CLOUDFLARE_API_TOKEN` | 仅限本 Worker 与 D1 所需权限的 Cloudflare API 令牌 |
| 环境机密 | `CLOUDFLARE_ACCOUNT_ID` | Cloudflare 账户标识 |
| 环境机密 | `TASK_OBSERVATORY_WRITE_TOKEN` | 本地采集器上传事件使用的随机强口令 |
| 环境机密 | `TASK_OBSERVATORY_READ_TOKEN` | 看板读取状态使用的另一条随机强口令 |
| 云端资源 | 无需手动填数据库 ID | 部署流程会在 Cloudflare 账户中查找；不存在时自动创建 `zh-task-observatory`。令牌需有 D1 读取/写入权限。 |

读写口令必须是不同的随机字符串，至少 32 个字符。不要把口令发到聊天、源码或运行日志中。

首次部署时在 Actions → “部署云端任务看板” → Run workflow，勾选“首次部署时是否执行数据库建表”。正式地址只有工作流成功后才会出现在部署日志/Cloudflare Worker 列表中。在部署成功之前，不存在可供确认的正式在线地址。

## 正式部署步骤（仅需一次云端授权）

正式版使用 Cloudflare Workers + D1。官方配置说明：
https://developers.cloudflare.com/workers/static-assets/binding/

1. 在 GitHub 的 `cloud-production` 环境添加 Cloudflare API Token、账户 ID，以及两条不同的随机强口令。Cloudflare Token 至少需要账户级 D1 读取/写入与 Workers 脚本编辑权限。
2. 打开 Actions → “部署云端任务看板” → Run workflow。首次部署保留“执行远端数据库建表”选项。
3. 工作流会查找或创建 D1 数据库、生成仅存在于运行器的临时配置、迁移数据库、写入 Worker 加密口令并发布中文网页。数据库 ID 不会提交到 GitHub。
4. 记录 Cloudflare 返回的真实 HTTPS 地址，检查 `/api/health`，再用读取口令检查 `/api/status?project=solo-ai-company`；未通过这两项不能认为已上线。
5. 本地采集器运行前设置 `PROJECT_ROOT`、`PROJECT_ID`、`SOURCE_ID`、`CLOUD_URL`、`WRITE_TOKEN`。默认只上传最小任务元数据；如确需上传恢复文字，才显式设置 `ALLOW_RECOVERY_TEXT=true`，且必须先确认文本不含隐私。首次验证用 `node collector/collector.cjs --once`；长期采集使用 `--loop`，由现有受管进程管理机制监督，而不是额外新建公网隧道。
6. 在正式网址输入读取口令（仅保存在当前浏览器会话中），查看项目任务。模拟数据显示必须通过“查看演示”主动打开。
7. 进行断线恢复和另一台电脑查看的端到端验收，确认云端数据与真实本地状态一致。

**绝不能将 READ_TOKEN / WRITE_TOKEN 写入浏览器 HTML、GitHub 仓库或命令输出日志。** 正式运行建议使用经审核的凭据注入与访问控制。

## 已执行测试（2026-10-28）

Windows 工作站 Node.js 对 GitHub 上的源码副本运行：

- JavaScript 语法检查通过。
- Node.js 核心回归测试 **11/11 PASS**（包含默认隐私最小化和脱敏验证）。
- 未授权读、未授权写被正确拒绝。
- 重复事件提交不会重复记录。
- 后补的旧任务事件不会把已经验收的新状态倒退。
- 断线队列可以保存事件并在网络恢复时补发，第二次不上报重复事件。
- 非 HTTPS 公网地址的上报请求被拒绝。
- 使用 SQLite 实际执行 D1 建表 SQL，通过跨项目采集器心跳隔离检查。
- 中文网页脚本语法、中文操作按钮、仅公开 public 静态文件配置通过。

GitHub Actions 最近一次通过记录：
https://github.com/a2315758011/a/actions/runs/40636821484

以上是**本地开发测试与 GitHub 云端 CI 测试**，不是 Cloudflare 线上运行和真实浏览器交互验收。

## 还没有完成的验收

- [ ] Cloudflare 账户授权、远端 D1 创建和数据库迁移。
- [ ] 正式 HTTPS 地址部署、真实 Worker / D1 端到端写入和查询。
- [ ] Windows 实际长期运行采集及断开/恢复完整验证。
- [ ] 真实浏览器点击、动画显示和移动端视觉验证。
- [ ] 真实跨电脑访问与断线恢复。
- [ ] 将尚未接入 Project Orchestrator 的其他 AI 工具接入采集。
- [ ] 独立私有 GitHub 仓库。当前仅在已有公开仓库的隔离分支进行无敏感数据的代码研发。

## 当前 GitHub 地址

https://github.com/a2315758011/a/tree/feature/cloud-task-observatory-v0/cloud-task-observatory

你只需要继续用中文说明想添加或修改的功能，AI 负责修改、提交、测试和保留回滚记录。
