# 直播炮塔守城｜Cocos Creator 自动化验收

正式工程：CocosCreator工程（Cocos Creator 3.8.2）。禁止用独立 HTML 替代工程。

## 一键快速回归

运行：python 自动化测试/一键高速回归-正式Cocos.py

未修改的正式 Web-Mobile 构建走 SHA-256 缓存；快测包含真实 Cocos 浏览器启动、固定步进双结局、观众加入/离场、重开、敌人三层运行时与平台 SocketTask。最近实测约 14.6 秒，包含启动浏览器和测试，不是单纯模拟循环时间。

## 扩展关联回归

运行：python 自动化测试/一键高速回归-正式Cocos.py --all

涵盖战斗、平台适配、五视口商店、商店效果和直播参与。最近实测约 56.5 秒。报告独立保存在 验收证据/WHOLE-GAME-FAST-REGRESSION-20261022/扩展回归.json，快速报告为 快速回归.json，最新报告为 最后一次高速回归.json。

## 微信与抖音小游戏构建

运行：python 自动化测试/构建微信抖音-正式Cocos.py

分别构建 wechatgame 与 bytedance-mini-game，检查真实构建日志和导出产物。按 Cocos 源资产指纹缓存；源码变更后会重建对应目标。报告在 验收证据/COCOS-MINI-BUILD-20261022/微信抖音正式构建验收.json。

## 慢速发布验收（仅发布候选或交互核心修改后）

运行：python 自动化测试/qa_formal_full_game_e2e_20261022.py
运行：python 自动化测试/qa_formal_shop_persistence_20261022.py

高速固定步进回归不替代真人操作、真机或平台后端验证。Android 签名 APK、微信/抖音真实设备、官方直播事件后端和最终美术签收仍是独立发布门槛。

## 兽人三层资源

game-art/staging/RECOVERY-037-LOCAL-SEGMENTATION-001/ 存放从既有顶视母版派生的同画布三层 PNG、重组图和 manifest。两组重组均为零像素差；Cocos 实际运行验证小兵和首领都启用三层，母版作为兜底。当前仍是技术候选，非已签收美术，也不代表关键帧动画已经完成。
