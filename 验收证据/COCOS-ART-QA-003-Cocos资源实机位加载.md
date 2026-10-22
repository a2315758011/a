# COCOS-ART-QA-003｜Cocos 候选分层美术真实导入和浏览器运行验收

日期：2026-10-19；项目：直播炮塔守城 (live-turret-defense)。

## 实际修改（与正式主场景隔离）
- 新增 `CocosCreator工程/assets/场景/待审美术演示.scene`，UUID独立；正式 `守城主场景.scene` 未改，SHA256 `d42fc8b8f45e922f900e4bf68504b7df085051abf91dcd81966f5415aaff8fba`。
- 新增 `CocosCreator工程/assets/脚本/待审美术测试控制器.ts`，运行时加载 7 组、每组 8 帧，固定原画布尺寸、像素 nearest、关闭调试统计遮挡。
- 新增 `CocosCreator工程/assets/resources/待审核-分层动画测试/`：56 PNG与Cocos编辑器自动导入的56 .png.meta；meta含 SpriteFrame 子资产，nearest min/mag滤波。
- 正式 `守城控制器.ts` 不变，SHA256 `f55c7e638c7cba52b0c90736ec37533b39774a2d319c87ddefe987fafabc72ed`。
- 未写 `assets/Art` 正式素材，也未改正式主场景、直播接口、地图/战斗逻辑。
- 为避免覆盖正常构建，在 `_assistant-temp/美术候选Cocos隔离构建工程` 复制官方工程必要配置、候选测试场景/脚本和资源，单独构建。

## 验证证据（真实运行）
1. 编辑器：`Cocos Creator 3.8.2` 在工作站启动运行，并自动为56张候选PNG导入 Cocos `SpriteFrame` 子资产。
2. 逐文件复验：56/56 PNG与v2候选源字节相同；56/56 `.png.meta` 纹理过滤为nearest；两份正式主游戏文件SHA保持原值。
3. CLI构建：`--project <隔离工程> --build "platform=web-mobile;debug=true"` 的日志明确 `build success`，产出 `build/web-mobile/index.html` 和总计196个文件。**进程退出码36（非0）**，因此仅依据后续真实运行确认可用；不能把退出码宣称为零。
4. 本机 Edge 通过 `http://127.0.0.1` 开启隔离工程构建，CDP捕获 WebGL2 可用、Cocos Creator v3.8.2加载成功、`Success to load scene: db://assets/场景/待审美术演示.scene` 和日志 **`美术样例引擎加载完成 7 组56帧`**，JS异常0。
5. 网络记录中仅 `/favicon.ico` 404（非核心资源）；动态SpriteFrame加载来自 `assets/resources/native` 和 import manifest，无核心资源未加载证据。
6. Edge CDP 截图来自**真实 Cocos Web-Mobile 运行画布**，不是AI拼图或HTML替代游戏：`美术资源/分层源文件/动画引擎验收隔离/Cocos浏览器CDP场景运行图.png`。当前测试视口画面 **1056×1748**（由Edge实际 viewport 导致）；不是抖音真机1080×1920发布验证。
7. 结构化证据 `Cocos候选美术最终验收数据.json`、`Cocos浏览器CDP运行错误诊断.json`、`QA-Cocos构建结果.json`，复验脚本 `_assistant-temp/Cocos候选资源最终验收.py` 实际退出码0。

## 视觉审核结论：不通过最终美术质量门
- 兽人walk腿部交替存在，但脚部重心与方向不够可信；attack有斧头越过脸部与姿态跳帧；death仍像绕中心旋转而非真正身体塌落。
- 水晶shatter以近似六等分三角形割裂，缺乏自然不规则裂纹、主体崩解与残骸收束。
- 以上属于视觉真实动作的**待重画/待用户审核**，不是此轮技术运行错误。场景只作为隔离演示，**不得导入正式主场景并声明G2/G3通过**。
- 对标V0.3规范：兽人32×32、炮塔64×64、核心96×96的候选规格尚未统一；当前5种样板源画布均为96×96，且审美风格未经批准。
- 没有完成 Cocos 正式战斗替换、Prefab绑定及抖音/微信/Android真机性能验证。

## 交接下一步
1. 保留全部v1/v2和旧174帧历史证据不覆盖，按视觉审核结果为失效动作重绘关键姿态/骨骼分层，尤其兽人行走、挥斧、死亡、水晶破碎。
2. 核对像素规范、画布/角色本体与相机，打磨一致风格，再经美术及用户认可，才能转入正式Art目录/Prefab。
3. 使用已建独立 `待审美术演示.scene` 做相同规模Cocos运行回归，检查加载56/56、异常0、PNG/meta UUID、透明/画布、动作语义和性能。
