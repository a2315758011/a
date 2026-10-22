# RECOVERY-031｜平台构建与适配层回归

日期：2026-10-22  
项目：`live-turret-defense`  
范围：隔离候选 Cocos Creator 3.8.2 工程。正式 `CocosCreator工程` 未修改。

## 结论

RECOVERY-031 的目标是“平台构建探测与平台差异收口”，不是宣称真机发布完成。当前结果：

| 平台 | 构建 | 运行/设备 | 当前结论 |
|---|---|---|---|
| Web-Mobile | exit 36 + build success，288 文件 | 五视口真实浏览器回归 5/5 PASS | **BUILD_PASS / BROWSER_QA_PASS**；stderr 只有 Cocos 登录服务器 timeout |
| 微信小游戏 | exit 36 + build success，TS 0，stderr 0，293 文件 | 未进微信开发者工具/真机 | **BUILD_PASS / DEVICE_PENDING** |
| 抖音小游戏 | exit 36 + build success，TS 0，stderr 0，291 文件 | 生成配置仍是 `testappId`，未进抖音开发者工具/真机 | **BUILD_PASS / DEVICE_ACCOUNT_PENDING** |
| Android | 规范 `packages.android` 配置已生效 | 本机缺 Android SDK/NDK | **PLATFORM_SDK_BLOCKED / DEVICE_PENDING** |

## 当前代码平台适配层

新增/已有候选文件：
- `assets/脚本/平台适配器.ts`
- 控制器统一暴露 `platformSnapshot()`
- 控制器统一暴露 `attachLiveEventSource()`
- 控制器统一暴露 `detachLiveEventSource()`

平台判断、存储能力和直播事件源挂接没有散落进战斗逻辑。真实微信/抖音直播事件源仍需单独实现，本适配层不会伪造官方平台事件。

## Web 运行时验证

`平台适配层Web运行时回归.json` 实测：

- runtime = `web`
- storageAvailable = true
- Web 环境不会错误宣称平台 SDK 可用
- 默认没有直播事件源
- mock 事件源真实挂接后，事件经过公开接口进入 `直播事件桥`
- 事件源 detach 后 stop 被调用一次且快照恢复未挂接
- JavaScript error = 0

同时复用当前 Web 构建重跑商店/主界面五视口：
- 360×780
- 393×852
- 540×760
- 540×960
- 540×1108

结果 5/5 PASS，商店入口、开始按钮、三项商品、关闭按钮均在屏内，真实打开/关闭通过。

## 微信小游戏

当前代码重新构建：

- CLI platform：`wechatgame`
- returnCode：36
- build success：true
- TypeScript errors：0
- stderr：0
- 文件数：293
- `platformSnapshot` 与 `attachLiveEventSource` 已进入构建脚本

生成 `project.config.json` 含一个微信 AppID，但本轮没有验证该 AppID 的账号归属、审核权限、开发者工具登录或真机。因此只能标记 BUILD_PASS，不能标记可发布或真机完成。

## 抖音小游戏

当前代码重新构建：

- CLI platform：`bytedance-mini-game`
- returnCode：36
- build success：true
- TypeScript errors：0
- stderr：0
- 文件数：291
- 平台适配层已进入构建脚本
- 生成 `project.config.json` 中 appid = `testappId`

因此构建层通过，但账号与真机必须保持 DEVICE_ACCOUNT_PENDING。

## Android

第一次旧式 CLI 仅传 `packageName` 时停在 Creator 必填参数校验。

本轮改为 Cocos 3.8 官方推荐的 `configPath + packages.android` 结构，提供：
- packageName
- portrait orientation
- API level
- arm64-v8a
- debug keystore
- GLES3
- JDK 17 路径

结果已经越过原先 required 参数错误，明确进入 Android builder，并返回：

`找不到 Android NDK/SDK 路径，请到 偏好设置 -> 外部程序 中设置`

本机实际环境检查：
- `JAVA_HOME=C:\Users\ide0007\.jdks\jdk-17.0.20.1+1`，存在
- `ANDROID_HOME`：空
- `ANDROID_SDK_ROOT`：空
- `NDK_HOME`：空
- `sdkmanager`：不存在
- `ndk-build`：不存在
- 仅有 `C:\platform-tools\adb.exe`

所以 Android 当前不是游戏 TypeScript/平台适配代码错误，而是明确的 **PLATFORM_SDK_BLOCKED**。

## 正式工程隔离

实测：
- 正式 `CocosCreator工程/assets/脚本/平台适配器.ts`：不存在
- 候选隔离工程 `assets/脚本/平台适配器.ts`：存在

因此 RECOVERY-031 没有绕过美术签收门禁把候选代码直接并入正式工程。

## 后续

RECOVERY-032 应单独处理 Android 构建环境：安装/配置 SDK + NDK，生成 Android 原生工程/APK 并做真实安装运行；微信/抖音则需要各自开发者工具、真实账号权限与设备测试，仍不能拿 CLI BUILD_PASS 代替。
