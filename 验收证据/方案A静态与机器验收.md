# 方案A静态与机器验收（2026-10-12）
项目：live-turret-defense；执行者：agent-gpt6-turret-art-spec-20261012；仅单Agent自审。

## 真实测试
- 命令：python "美术规范\\透明资源验收.py" --self-test
- 当前电脑 Python + Pillow 11.3.0 已确认。
- 结果：EXIT_CODE 0；selfTest PASS。
- 阳性用例：256×256 RGBA真实透明图，透明率0.7601，边缘透明，判PASS_MACHINE_ONLY。
- 阴性用例：256×256纯白RGB无透明通道，检出NOT_RGBA、ALPHA_ALL_OPAQUE、TOO_LITTLE_TRANSPARENT_AREA、BORDER_NOT_CLEAN，判FAIL。
- 人工绿草/地砖污染语义检测：UNVERIFIED（工具不能单独证明；需五种背景叠图和美术审查）。
- 真实3塔图、升级、序列帧：NOT_PRODUCED；Cocos引擎引用/实际运行：UNVERIFIED。
- 参考TapTap实际镜头尚无法从短链核实：BEN-001 BLOCKED。V5.3强制首张玩法总览图尚未落盘：GAME-OVERVIEW-001 BLOCKED。
- 表明状态：方案A规格为DOCUMENTED，Alpha工具有可重复selftest证据；不等于炮塔资源已量产。
