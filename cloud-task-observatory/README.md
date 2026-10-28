# Cloud Task Observatory / 云端工程任务观察站

**状态：V0 GitHub 隔离分支原型（未正式部署）。** 本目录是公开安全的通用原型，`snapshot.json` 是**合成示例**，不是用户工作站的真实任务数据。

## 要解决的问题

用户不应因聊天网页崩溃或本机 MCP 失联就失去任务进度、责任人、错误、证据和恢复点。监控平台必须清楚区分：

- `VERIFIED/COMPLETED`：有真实证据的验收完成。
- `IN_PROGRESS`：最近有可信执行事件，并存在任务 ID。
- `FAILED/BLOCKED`：直接失败或明确阻塞。
- 下游受阻：沿完整祖先依赖追踪导致阻塞的根节点，不错误宣称下游自身失败。
- `STALE/OFFLINE`：超出心跳阈值；只能展示最后已知状态。
- `UNKNOWN`：未收到事件，不得伪造百分比。

## 数据契约（schemaVersion=1）

```json
{
  "schemaVersion": 1,
  "projectId": "example-project",
  "updatedAt": "2026-10-28T04:00:00Z",
  "tasks": [
    {
      "id": "BUILD-01",
      "title": "实现采集器",
      "status": "IN_PROGRESS",
      "dependencies": ["PLAN-01"],
      "owner": "AI engineer",
      "updatedAt": "2026-10-28T03:50:00Z",
      "lastSuccess": "单元测试",
      "resumePoint": "继续采集器接口与断线重传",
      "evidence": []
    }
  ],
  "events": [
    {"at":"2026-10-28T03:50:00Z","taskId":"BUILD-01","type":"heartbeat","message":"采集器开发中"}
  ]
}
```

实时正式版本应使用每条事件的 `eventId`、`taskId`、`runId`、`sourceId`、`sequence`、`occurredAt`、`receivedAt`、`evidenceRef`，写入云端持久存储。服务器验证 token/签名，按 `eventId` 去重，拒绝逆序状态覆盖，定期生成快照。网页只读取云端状态；工作站采集器只主动向云端推送，使用断线持久队列。禁止直接向公开 GitHub 仓库提交个人路径、密钥、完整私有日志、聊天历史或隐私材料。

## GitHub / 云端部署路线

1. 在**独立私有仓库**存放正式源码；当前分支仅用于无敏感数据的原型研发。
2. 前端：静态部署（Cloudflare Pages / GitHub Pages），不在页面暴露写入密钥。
3. 云端 API/持久化：Cloudflare Worker + D1（或同等的受控服务）保存事件、状态、心跳、恢复点和审计记录。
4. 本地采集：只读适配现有 `.project-orchestrator`，以本地 spool 队列补发，断线不会丢失最近记录；未来可增加 GitHub Actions、Codex、Claude 等适配器。
5. 安全：私有任务默认必须鉴权访问，匿名演示仅展示合成数据；不可将 D1/Worker 凭据写进公开源代码。
6. 验收门槛：真实 GitHub 独立私有仓库、真实云端 URL、双端刷新、浏览器崩溃恢复、MCP 断线续传、任务故障传播、数据访问控制、跨电脑打开。

## 本地预览

在此目录中运行 `python -m http.server 8080`，打开 `http://127.0.0.1:8080`。无需依赖安装；前端每 15 秒刷新 `snapshot.json`。示例时间戳固定，因此会明确提示快照过期。

**此版本不是正式的云端实时系统。** GitHub 目前只有隔离开发分支，尚未创建独立仓库、配置 Pages 或接通云端持久化。此文档不得当成已部署证据。
