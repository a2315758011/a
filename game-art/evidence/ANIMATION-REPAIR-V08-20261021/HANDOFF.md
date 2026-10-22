# V08 动画重制恢复点
Owner: agent-codex-animation-20261021
Project: live-turret-defense / win-unpacked
状态：上传修复候选已完成，未正式部署；真实动画和覆盖替换尚未完成。

## 真实失败与恢复
- 唯一真实 Gateway 任务：e5ceea17-83bc-4b1c-b10c-0878458e8cd1。
- 引用当前 V07 兽人首领 96×96 RGBA 母版，快照 reference-boss.png。
- 真实返回 failed / stage=upload-reference / Could not find node with given id。
- submitted=false, submitLocked=false，未生成图片。不得把排队、文件数或本地测试冒充成功。
- 调用期间另一个 PID182804 在18131启动，覆盖共享 discovery；该实例退出后删除 discovery。原18130服务仍有原任务。不能以新实例404判断原任务未提交。
- recover-query.cjs 已真实找回原18130的失败记录；job-query.cjs 只做GET并校验任务身份，查不到不重发。
- 原 V06/V07 状态不明任务均未重发；本轮没有更新正式资源、Cocos绑定或其他 Agent 的代码。

## 上传修复
win-unpacked/_assistant-temp/reference-upload-v08-20261021/
- 从实时 ASAR 0f5c3a6eabbb40285ea2dc7d18997a725f099f5cc1ef713bd3f47c3ee84dc60e 提取当前 runtime，仅替换 _setFileInputFiles。
- 每次发现只取一个 pierced DOM tree，支持 shadow/iframe；优先 backendNodeId，解析成 objectId 后上传。
- 节点失效时最多3次重新定位，不重发提示词。
- 必须出现新增附件且不在上传中；旧图或仅 file input 有文件不放行。兼容网页上传后清空 input。
- 控件适配失败使用 UPLOAD_*，不宣称账号不支持 image_edit。
- 10项CDP状态回归通过（包括实时旧函数负向复现）；真实Edge本地DOM上传3项通过；任务查询恢复4项通过。仅3项为真实浏览器，本轮没有模型网页生成通过。
- candidate ASAR 50915b94f60158edcb9e59c010d0744b01d8a94d99de7e504378a760d5c2eb20。
- pack-report确认只改web-generation-runtime.cjs，其他entry元数据一致，main/preload/renderer/package字节一致。
- 候选未安装，不能报告“已从根本修复”。

## 发布阻塞
项目 docs/task-orchestrator-v1/FAILURE-REVIEW-AND-RELEASE-GATE.md 第7、8条要求：
“只能通过 LIVE_ASAR_受控部署.bat / live-asar-deploy.cjs 执行正式 ASAR 受控部署。”
release-prerequisites.json 是只读前置检查，不是 --release 全套测试：六项严重故障0项verified，缺真实图片入画布证据，故不具备发布条件。
另一个 Agent 正持有 recovery service 和对应测试锁；不要覆盖其调度修复，部署前重新检查锁和实际ASAR SHA。

## 下一步
1. 与现有发布/恢复修复整合，重新检查live hash并重建候选；不得覆盖较新ASAR。
2. 满足正式release gate后经受控脚本安装；受控退出/启动单实例，验证discovery指向真实owner，不修改共享MCP基础设施。
3. 安装修复后重试本任务前确认持久库仍显示明确未提交，并遵守项目重试规则；任务已提交或不明时仅原会话回收。
4. 先真实核查参考图附件与四姿态像素风/关节运动；合格后才批量攻击/行走/死亡/破坏，逐动作视觉审查。
5. 规范化透明/锚点、播放预览、Cocos真实播放及构建回归通过后再promotion，保留原UUID及版本备份。

其他原恢复点仍保留：win-unpacked场景缺图候选发布门禁；game RECOVERY-024结算面板设计及mode-prepare失败记录。
