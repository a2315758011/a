# -*- coding: utf-8 -*-
"""Finalize RECOVERY-035 evidence, task package, manifest and handoff."""
from pathlib import Path
import json,hashlib,time,sys

ROOT=Path(r"C:\Users\ide0007\Desktop\deliverable\AI小游戏实战营\AI小游戏制作工程文件\直播炮塔守城")
EVDIR=ROOT/"game-art"/"evidence"/"RECOVERY-035-UI-PANEL-MASTER-A"
QA_DIR=ROOT/"验收证据"/"RECOVERY-035-UI-PANEL"
TASK=ROOT/"任务包"/"RECOVERY-035.json"
BOARD=ROOT/"任务榜单.md"
ART_MANIFEST=ROOT/"game-art"/"manifest"/"art-manifest.json"
BRIEF=ROOT/"game-art"/"briefs"/"RECOVERY-035-UI-PANEL-MASTER-A-design-brief.json"
PROMPT=ROOT/"game-art"/"briefs"/"RECOVERY-035-UI-PANEL-MASTER-A-prompt.txt"
PROCESSOR=ROOT/"任务包"/"处理RECOVERY-035-结算面板.py"
BUILDER=ROOT/"任务包"/"build_candidate_v5_RECOVERY_035.py"
QA_SCRIPT=ROOT/"任务包"/"qa_RECOVERY_035_panel_e2e.py"
RUNTIME_SCRIPT=ROOT/"_assistant-temp"/"候选战场Cocos-V5隔离工程-20261020"/"assets"/"脚本"/"待审战场美术覆盖器.ts"
PROJECT=ROOT/"_assistant-temp"/"候选战场Cocos-V5隔离工程-20261020"
RUNTIME_PNG=PROJECT/"assets"/"resources"/"候选战斗美术-v5-RECOVERY-004"/"UI"/"面板"/"结算面板底板.png"
RUNTIME_META=Path(str(RUNTIME_PNG)+".meta")
ALPHA=EVDIR/"alpha-pixel-qa.json"
BUILD=EVDIR/"cocos-build-qa.json"
RUN=QA_DIR/"真实Cocos双结局与五视口回归.json"
OLD_RUN=QA_DIR/"真实Cocos双结局与五视口回归-before-assertion-correction.json"
REPORT=QA_DIR/"RECOVERY-035-结算面板集成与回归.md"
SNAPSHOT=EVDIR/"manifest.json"

def readj(p): return json.loads(p.read_text(encoding="utf-8"))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def rel(p): return p.relative_to(ROOT).as_posix()
def writej(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

alpha=readj(ALPHA); build=readj(BUILD); runtime=readj(RUN); task=readj(TASK); manifest=readj(ART_MANIFEST)
if alpha.get("status")!="PASS" or not all(alpha.get("gates",{}).values()):
    raise SystemExit("Alpha/pixel QA not PASS")
if build.get("effectiveSuccess") is not True or build.get("typescriptErrors") or build.get("errorLogBytes")!=0:
    raise SystemExit("Cocos build gates not PASS")
if runtime.get("result")!="PASS" or runtime.get("summary",{}).get("viewportsPass")!=10 or runtime.get("summary",{}).get("consoleErrorCount")!=0:
    raise SystemExit("Real runtime E2E gates not PASS")
if not RUNTIME_PNG.exists() or not RUNTIME_META.exists(): raise SystemExit("Cocos panel PNG/meta missing")
entry=next((x for x in manifest.get("assets",[]) if x.get("assetId")=="td-v5-ui-settlement-panel"),None)
if not entry or entry.get("approved") is not False or entry.get("formalPresent") is not False:
    raise SystemExit("Manifest entry missing or formal-promotion gate incorrect")
if sha(RUNTIME_PNG)!=alpha["master"]["sha256"]: raise SystemExit("Runtime panel hash does not match alpha-QA master")
if not all(p.exists() for p in [BRIEF,PROMPT,PROCESSOR,BUILDER,QA_SCRIPT,RUNTIME_SCRIPT,BOARD,TASK]):
    raise SystemExit("Required source/brief/task files missing")

task["status"]="CANDIDATE_QA_PASS_ART_APPROVAL_PENDING"
task["completed"]=[
 "Shared Generation Gateway job completed under unique RECOVERY-035 task ID; immutable provider output and gateway job record saved.",
 "Dedicated settlement panel master normalized to RGBA; chroma-key removal, crop, 48-color no-dither palette reduction and nearest-neighbor resize completed.",
 "Alpha/pixel QA PASS: 512x636 RGBA, true alpha, opaque interior, 48 unique opaque RGB colors, 0 opaque magenta fringe pixels.",
 "Panel imported and bound as a real Sprite in isolated Cocos V5 candidate; procedural settlement-card body replaced while separate dim backdrop, labels, crystal, buttons and handlers remain.",
 "Cocos Creator 3.8.2 Web-Mobile build PASS: exit 36 official success code, build success log, TypeScript errors 0, stderr 0, 108 PNG assets, missing Meta 0.",
 "Real mouse-driven Cocos E2E PASS: natural win, return to menu, natural loss, restart; JS errors 0.",
 "Both natural settlement states pass all five viewport sizes: 10/10 viewport checks; live-session persistence verified when returning to menu."
]
task["pending"]=[
 "Human V5 art sign-off before formal asset/Prefab promotion.",
 "Formal Cocos main scene/Prefab integration after art sign-off.",
 "Android real-device, WeChat DevTools/device, Douyin DevTools/device, real platform live event permissions/backend remain external gates."
]
task["evidence"]=[
 "game-art/briefs/RECOVERY-035-UI-PANEL-MASTER-A-prompt.txt",
 "game-art/briefs/RECOVERY-035-UI-PANEL-MASTER-A-design-brief.json",
 "game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/gateway-job.json",
 "game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/provider-output.png",
 "game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/master.png",
 "game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/alpha-pixel-qa.json",
 "game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/cocos-build-qa.json",
 "game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/manifest.json",
 "验收证据/RECOVERY-035-UI-PANEL/真实Cocos双结局与五视口回归.json",
 "验收证据/RECOVERY-035-UI-PANEL/真实Cocos双结局与五视口回归-before-assertion-correction.json",
 "验收证据/RECOVERY-035-UI-PANEL/RECOVERY-035-结算面板集成与回归.md"
]
task["verification"]={
 "generation":{"status":"completed","jobId":"e5e90483-d544-4e55-a3c7-2463294afec6","provider":"ChatGPT via shared Generation Gateway"},
 "alphaPixel":{"status":alpha["status"],"size":alpha["master"]["size"],"mode":alpha["master"]["mode"],"paletteColors":alpha["master"]["uniqueOpaqueRgbColors"],"residualMagentaOpaquePixels":alpha["master"]["residualMagentaOpaquePixels"],"sha256":alpha["master"]["sha256"]},
 "cocosBuild":{"status":"PASS","exitCode":build["returnCode"],"buildSuccessLogged":build["buildSuccessLogged"],"typescriptErrors":len(build["typescriptErrors"]),"stderrBytes":build["errorLogBytes"],"resourcePngCount":build["resourcePngCount"],"missingMetaCount":len(build["missingMeta"])},
 "realRuntime":{"status":runtime["result"],"naturalWin":runtime["summary"]["win"],"naturalLoss":runtime["summary"]["loss"],"viewportPasses":runtime["summary"]["viewportsPass"],"viewportTotal":runtime["summary"]["viewportsTotal"],"consoleErrors":runtime["summary"]["consoleErrorCount"]},
 "formalProjectModified":False,
 "humanArtApproval":"pending"
}
task["updatedAt"]=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
writej(TASK,task)

board=BOARD.read_text(encoding="utf-8")
section="""\n\n## 2026-10-22｜RECOVERY-035 结算面板专用像素美术与候选运行时接入\n\n| taskId | 产物/范围 | 状态与实测 |\n|---|---|---|\n| RECOVERY-035 | 独立结算面板RGBA Master；仅隔离候选Cocos接入，不覆盖正式场景/Prefab | **CANDIDATE_QA_PASS / ART_APPROVAL_PENDING**：Generation Gateway产物已保全；Alpha/像素QA PASS（512×636 RGBA、48色、残留不透明洋红0）；Cocos Web-Mobile构建exit36/build success/TS0/stderr0/Meta完整；真实鼠标自然胜利96杀HP100、自然失败74杀HP0、返回主界面与再次守城均PASS；胜/败各五视口10/10，JS错误0。正式资产提升仍需人工美术签收。 |\n\n证据：game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/manifest.json、验收证据/RECOVERY-035-UI-PANEL/RECOVERY-035-结算面板集成与回归.md。\n"""
if "## 2026-10-22｜RECOVERY-035 结算面板专用像素美术与候选运行时接入" not in board:
    BOARD.write_text(board.rstrip()+"\n"+section,encoding="utf-8")

report_text=f"""# RECOVERY-035｜结算面板专用像素美术与候选运行时回归

## 完成内容

- 通过工作站共享 Generation Gateway 生成新的静态结算面板；Job ID：e5e90483-d544-4e55-a3c7-2463294afec6。
- Provider 原图保存在 game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/provider-output.png，未覆盖旧任务资产。
- 处理后 Master：game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/master.png，512×636、RGBA，SHA-256 {alpha['master']['sha256']}。
- 已把面板作为真实 Sprite 接入隔离 Cocos V5 候选；结算暗幕、标题、统计文本、水晶图标、两个按钮和事件处理保持独立，未烘焙中文文字。

## 验证结果

| 验收项 | 实测结果 |
|---|---|
| Alpha / 像素QA | PASS；真透明背景、面板中心不透明、48色、残留不透明洋红 0 |
| Cocos Creator Web-Mobile 构建 | PASS；exit {build['returnCode']}（官方成功码）、build success、TS错误0、stderr0、PNG {build['resourcePngCount']}、缺失Meta {len(build['missingMeta'])} |
| 自然胜利 | 第3波、96杀、HP100、24塔、15名在线观众；结算面板显示 |
| 自然失败 | 第3波、74杀、HP0、9座基础塔、0在线观众；结算面板显示 |
| 竖屏布局 | 胜利5/5 + 失败5/5，合计10/10 |
| 返回主界面 / 再次守城 | PASS；返回菜单隐藏结算面板和战斗HUD；房间级观众会话按设计保留；再次守城恢复ready、HP100、9基础塔 |
| JavaScript控制台错误 | 0 |

## 证据文件

- game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/gateway-job.json
- game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/alpha-pixel-qa.json
- game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/cocos-build-qa.json
- game-art/evidence/RECOVERY-035-UI-PANEL-MASTER-A/manifest.json
- 验收证据/RECOVERY-035-UI-PANEL/真实Cocos双结局与五视口回归.json
- 验收证据/RECOVERY-035-UI-PANEL/01-natural-win-360x780.png
- 验收证据/RECOVERY-035-UI-PANEL/02-natural-loss-360x780.png

## 验收边界

- 本任务只修改隔离候选工程和美术候选资源；正式 Cocos 场景、Prefab、正式运行资源未修改。
- 资产状态为 candidate_runtime_qa_pass，approved=false、formalPresent=false。人工美术签收之前不得提升到正式资产。
- Android、微信小游戏、抖音小游戏真机和真实平台直播事件仍需独立验收。
- 第一次QA结果中有一条旧断言错误地要求返回主菜单后只剩9塔；真实记录证明房间级15名观众会跨菜单保留，正确状态是24塔、15在线、HP100、菜单显示、结算面板与战斗HUD隐藏。原始报告保留为 真实Cocos双结局与五视口回归-before-assertion-correction.json，修正后的断言和依据已写入最终JSON。
"""
REPORT.write_text(report_text,encoding="utf-8")

runtime_json=readj(RUN)
files=[
 EVDIR/"provider-output.png",EVDIR/"master.png",EVDIR/"provider-preview.jpg",EVDIR/"master-preview.jpg",
 EVDIR/"gateway-job.json",ALPHA,BUILD,PROMPT,BRIEF,ART_MANIFEST,TASK,BOARD,REPORT,PROCESSOR,BUILDER,QA_SCRIPT,
 ROOT/"任务包"/"patch_RECOVERY-035_UI_panel.js",ROOT/"任务包"/"patch_qa_RECOVERY_035.js",
 ROOT/"任务包"/"patch_qa_RECOVERY_035_menu_assertion.js",ROOT/"任务包"/"reconcile_RECOVERY_035_report.py",
 RUNTIME_PNG,RUNTIME_META,RUNTIME_SCRIPT,
 PROJECT/"V5-Cocos构建-输出-RECOVERY-035.log",PROJECT/"V5-Cocos构建-错误-RECOVERY-035.log",
 RUN,OLD_RUN
]
for shot in runtime_json.get("screenshots",[]): files.append(QA_DIR/shot["file"])
unique=[];seen=set()
for f in files:
    if f.exists() and str(f.resolve()).lower() not in seen:
        seen.add(str(f.resolve()).lower());unique.append(f)
snapshot={
 "taskId":"RECOVERY-035","projectId":"live-turret-defense","assetId":"td-v5-ui-settlement-panel",
 "createdAt":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
 "status":"PASS_WITH_ART_APPROVAL_PENDING",
 "immutabilityNote":"Provider output and final master are preserved as evidence snapshots with SHA-256; this is hash-based verification, not OS-enforced read-only storage.",
 "files":[{"path":rel(f),"bytes":f.stat().st_size,"sha256":sha(f)} for f in unique]
}
writej(SNAPSHOT,snapshot)
snap=readj(SNAPSHOT);mismatches=[]
for item in snap["files"]:
    f=ROOT/item["path"]
    if not f.exists() or f.stat().st_size!=item["bytes"] or sha(f)!=item["sha256"]: mismatches.append(item["path"])
if mismatches: raise SystemExit("Evidence snapshot verification failed: "+", ".join(mismatches))
snapshot["verification"]={"status":"PASS","verifiedAt":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"fileCount":len(unique),"mismatches":[]}
writej(SNAPSHOT,snapshot)
snap=readj(SNAPSHOT);mismatches=[]
for item in snap["files"]:
    f=ROOT/item["path"]
    if not f.exists() or f.stat().st_size!=item["bytes"] or sha(f)!=item["sha256"]: mismatches.append(item["path"])
if mismatches: raise SystemExit("Final evidence verification failed: "+", ".join(mismatches))
print(json.dumps({"ok":True,"taskStatus":task["status"],"assetCount":len(manifest.get("assets",[])),"snapshotStatus":snap.get("verification"),"snapshotFileCount":len(snap["files"]),"report":rel(REPORT),"manifest":rel(SNAPSHOT),"taskBoardUpdated":True},ensure_ascii=False,indent=2))
