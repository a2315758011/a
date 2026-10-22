# RECOVERY-034｜V5美术资源审计与缺口补全

日期：2026-10-22  
项目：live-turret-defense  
范围：game-art + 隔离候选 Cocos Creator 3.8.2 工程；正式 CocosCreator工程未覆盖。

## 验收结论

状态：**CANDIDATE_QA_PASS_WITH_EXTERNAL_GATES**

RECOVERY-034 已把“缺什么、哪些能用、哪些必须拒绝、哪些已经真实接入 Cocos”收敛到可追溯状态。候选运行时已经替换掉旧的错误透视敌人，并补齐中心符文平台与 8 款像素 FX。当前仍不满足正式美术发布门槛，因为敌人可编辑分层生产链受参考图上传自动化阻塞，同时 V5 整体美术尚未取得人工签收。

## 已完成

- 盘点 V4/V5/正式资源尺寸、Alpha、哈希、Cocos Meta，更新 `game-art/manifest/art-manifest.json`。
- 三款炮塔、水晶、UI、地砖继续复用当前 V5 候选。
- AI 网关生成并拆分 8 款弹道/命中/受击/升级 FX；Alpha、Cocos 导入、构建、真实战斗均通过。
- 补出独立中心符文平台 128×128；透明与像素硬门通过并已在隔离候选运行时绑定。
- 旧兽人小兵/首领合成图因斜视/侧视被拒绝，不再作为 V5 正式候选。
- 兽人小兵 Master A：96×96，真顶视候选，技术 QA 通过。
- Boss Master A：人工视觉门禁拒绝，原因是正面/高 3/4 读法；失败证据保留。
- Boss Master B：重新生成，128×128 归一化；Alpha 0/255、28 色、品红残留 0，进入候选。
- Cocos 候选运行时优先加载小兵 Master A / Boss Master B，旧三层仅保留回退；自然对局中两者均实际激活，旧层在 Master 激活时关闭，JS 错误 0。
- 顶视 Master 绑定后的 9 基础塔三波自然长局：自然失败，第三波、74 杀、JS 错误 0。
- 强化胜利长局：真实主界面开始 → 15 观众加入 → 升级 → 三波胜利；96 杀、HP100、24 塔，结算通过；点击“再次守城”后 15 名在线观众会话保留、24 塔恢复，JS 错误 0。
- Web-Mobile Cocos 构建：Creator exit 36（官方成功码）、build success、TS 错误 0、stderr 0、入口存在；新 Master PNG Meta 均已生成。

## 分层源审计

项目中实际存在 84 个 ORA，可确认是真分层文件，而非纯平图容器；旧炮塔/水晶/兽人也存在源层 PNG。

但当前 V5 Runtime 不能仅靠现有源文件精确重建：
- 84 个 ORA 的 `mergedimage.png` 与当前抽查 V5 Runtime 合成图无字节级完全匹配。
- 12 个炮塔/水晶源层 PNG 直接按最近邻归一化到 Runtime 层后，0/12 完全一致；像素一致率约 65.8%–88.5%，Alpha 一致率约 94.0%–97.5%。

因此当前准确结论是：**源文件存在，但 V5 当前 Runtime 的精确转换/裁剪/调色配方未被完整记录，资产追溯链尚未闭合。**

## 参考图分层生成阻塞

为了把 Boss Master B 继续拆成可编辑三层，已实际尝试两个独立 ChatGPT 网页账号：

- `RECOVERY-034-TOPDOWN-BOSS-LAYERS-B1`
- `RECOVERY-034-TOPDOWN-BOSS-LAYERS-B2`

两次都在 `upload-reference` 阶段失败，错误 `Could not find node with given id`，且均为 `submitted=false`、无产物。已停止第三次盲目账号轮换，没有把失败任务重复提交或伪装成分层已完成。

## 当前候选资产状态

- 炮塔三款：候选 QA 通过。
- 城防水晶：候选 QA 通过。
- 中心符文平台：候选 QA 通过并运行时绑定。
- UI/地砖：候选 QA 通过。
- 8 款 FX：候选运行时 QA 通过。
- 兽人小兵 Master A：顶视 Master 运行时 QA 通过；可编辑三层待补。
- 兽人首领 Master B：顶视 Master 运行时 QA 通过；可编辑三层待补。
- 2048 Runtime Atlas：候选已生成并通过布局 QA，但未在人工签收前强行替换当前稳定 loose-resource 绑定。
- 正式 Prefab/AnimationClip：未提升，等待美术签收。

## 门禁

以下事项没有宣称完成：

1. V5 整体人工美术签收。
2. 敌人 Master A/B 对应的参考锁定可编辑分层生产板。
3. V5 源文件到 Runtime 的精确转换配方归档。
4. Runtime Atlas 正式绑定。
5. 正式 Cocos 主场景/Prefab/AnimationClip 提升。
6. Android 真机、微信/抖音真实平台与真实直播后台验收。

## 关键证据

- `验收证据/RECOVERY-034-V5美术资源审计/V5美术缺口矩阵.json`
- `验收证据/RECOVERY-034-V5美术资源审计/V5-FX-Cocos构建回归.json`
- `验收证据/RECOVERY-034-V5美术资源审计/V5像素FX真实战斗回归.json`
- `验收证据/RECOVERY-034-V5美术资源审计/中心符文平台离线生成QA.json`
- `验收证据/RECOVERY-034-V5美术资源审计/顶视敌人Master运行时回归/顶视敌人Master运行时回归.json`
- `验收证据/RECOVERY-034-V5美术资源审计/顶视敌人Master强化胜利回归/顶视Master强化胜利完整回归.json`
- `验收证据/RECOVERY-034-V5美术资源审计/顶视敌人Master三波自然失败回归.json`
- `game-art/evidence/RECOVERY-034-TOPDOWN-ENEMY-MASTER-A/normalize-qa.json`
- `game-art/evidence/RECOVERY-034-TOPDOWN-BOSS-MASTER-B/normalize-qa.json`
- `game-art/evidence/RECOVERY-034-TOPDOWN-BOSS-LAYERS-B1/generation-failure.json`
- `game-art/evidence/RECOVERY-034-TOPDOWN-BOSS-LAYERS-B2/generation-failure.json`
