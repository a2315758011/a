# 直播炮塔守城｜Cocos Creator 自动化验收

正式工程：CocosCreator工程（Cocos Creator 3.8.2）。禁止用独立 HTML 替代工程。

## 一键快速回归

运行：python 自动化测试/一键高速回归-正式Cocos.py

未修改的正式 Web-Mobile 构建走 SHA-256 缓存。默认快速回归使用已验收的 Node/CDP 直连启动器，在真实 Cocos 浏览器运行时检查主界面布局、三层敌人关键帧、观众会话保留、自然胜负双结局、重开与 JS 异常。2026-10-23 实测 7.213 秒（其中浏览器测试 5.232 秒），无需重复构建。默认快速回归**不包含**平台 SocketTask、五视口商店或官方直播数据验证。

## 扩展关联回归

运行：python 自动化测试/一键高速回归-正式Cocos.py --all

扩展模式额外调用既有 Python 平台 SocketTask、商店、效果和直播测试；当前旧 Python→Node→Edge 浏览器启动链路仍可能触发 CDP not ready，**未重新验收为 PASS**，不得拿默认快测结果替代。扩展报告保存在 验收证据/WHOLE-GAME-FAST-REGRESSION-20261022/扩展回归.json，快速报告为 快速回归.json，最新报告为 最后一次高速回归.json。

## 微信与抖音小游戏构建

运行：python 自动化测试/构建微信抖音-正式Cocos.py

分别构建 wechatgame 与 bytedance-mini-game，检查真实构建日志和导出产物。按 Cocos 源资产指纹缓存；源码变更后会重建对应目标。报告在 验收证据/COCOS-MINI-BUILD-20261022/微信抖音正式构建验收.json。

## Android 原生构建状态与高速失败缓存（2026-10-23）

工作站已复核并安装兼容工具链：共享 SDK 的 API 33/34（另有 35–37）、Build-Tools 34（另有 36/37）、NDK r23b、CMake 3.22.1、JDK 17。配置仅用于 Android 开发，不代表 APK 已生成。原生 Cocos Creator 3.8.2 的 Android 构建在 `android:onAfterInit` 返回“找不到 Android NDK/SDK 路径”，CLI 退出码 **34（失败）**；错误路径试过完整 configPath、Editor Profile 层级和版本兼容性检查。Creator 失败后仍可能输出 `build success` 字样，**不得单凭该字样判断成功**。

- `node 自动化测试/build_android_qa_20261023.cjs`：默认先检查构建环境指纹，相同签名的已复现插件错误直接返回 `BLOCKED_KNOWN_COCOS_PLUGIN_ERROR`（退出码 2），不会重复启动 Creator。
- `node 自动化测试/build_android_qa_20261023.cjs --check-cache`：只查看是否命中阻塞缓存（不启动 Creator）。
- `node 自动化测试/build_android_qa_20261023.cjs --force`：修复插件配置或工具链后才使用，强制重新启动真正的 Cocos Android 构建；不可把已有失败标记为通过。
- `python 自动化测试/qa_android_build_failure_cache_20261023.py`：测试“未变化命中、配置变化失效、还原后恢复”，不启动 Creator；`python 自动化测试/qa_android_sdk_detection_20261023.py` 检查 SDK 空目录假阳性。

本次原生结果为 **BLOCKED**：APK 0，真实 Android 安装及游戏流程未验收。完整失败调试日志留本机 `验收证据/ANDROID-APK-20261023/`；GitHub 只提交去除敏感运行参数的状态摘要。项目 GUI 的尝试性全局和工程 Profile 改动已按备份回滚，避免影响其他 Cocos 工程。

## 慢速发布验收（仅发布候选或交互核心修改后）

运行：python 自动化测试/qa_formal_full_game_e2e_20261022.py
运行：python 自动化测试/qa_formal_shop_persistence_20261022.py

高速固定步进回归不替代真人操作、真机或平台后端验证。Android 签名 APK、微信/抖音真实设备、官方直播事件后端和最终美术签收仍是独立发布门槛。

## 兽人三层资源

game-art/staging/RECOVERY-037-LOCAL-SEGMENTATION-001/ 存放从既有顶视母版派生的同画布三层 PNG、重组图和 manifest。两组重组均为零像素差；Cocos 实际运行验证小兵和首领都启用三层，母版作为兜底。当前仍是技术候选，非已签收美术，也不代表关键帧动画已经完成。
