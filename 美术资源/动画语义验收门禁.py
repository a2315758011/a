# -*- coding: utf-8 -*-
"""离线动画验收：只生成已有帧播放证据，未确认语义与引擎导入时坚决拒绝发布。
用法：python "美术资源/动画语义验收门禁.py"
不触发 MCP，不修改原有生成记录或正式资源。
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw
from datetime import datetime, timezone
import hashlib, json, re, sys

PROJECT = Path(__file__).resolve().parents[1]
ASSETS = PROJECT / "美术资源"
CONTRACT = ASSETS / "资源与动作合同-v0.4.json"
CANDIDATE_RECORD = ASSETS / "动画候选验收-v0.5.json"
OUT = ASSETS / "验收证据" / "兽人首领与水晶-动画语义核验"
SCOPE = {"enemy_boss": ["行走", "攻击", "死亡"], "objective_energy_core": ["破碎"]}
SEMANTIC = {
    "enemy_boss": {
        "行走": ["支撑姿态", "左脚抬起", "左脚前摆", "左脚落地换重心", "右脚抬起", "右脚前摆", "右脚落地", "恢复循环起点"],
        "攻击": ["站稳预备", "向后蓄力", "战锤举过肩/头", "躯干转动开始挥击", "战锤击中明确目标点", "随挥惯性和重心前移", "战锤从目标点回收", "回归待机"],
        "死亡": ["受到致命冲击", "身体后仰失衡", "腿部无力/跪倒", "倒地进行中", "身体接触地面", "肢体与武器落地", "保持倒地", "死亡姿态稳定结束"],
    },
    "objective_energy_core": {
        "破碎": ["完好水晶", "产生清晰裂纹", "裂纹扩散", "局部碎片开始分离", "主体破裂", "碎片飞散并旋转", "较小碎片下落", "残骸落地与能量散去"]
    },
}
def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def render(frame: Image.Image, scale=4) -> Image.Image:
    c = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    step = 8
    for y in range(0, frame.height, step):
        for x in range(0, frame.width, step):
            d.rectangle((x,y,x+step-1,y+step-1),fill=(215,220,226,255) if (x//step+y//step)%2 else (246,248,250,255))
    c.alpha_composite(frame.convert("RGBA"))
    return c.convert("RGB").resize((frame.width*scale, frame.height*scale), Image.Resampling.NEAREST)

def gif_and_strip(frames, basename: Path, ms: int, loop: bool):
    drawn=[render(im) for im in frames]
    gif=basename.with_suffix(".gif")
    durations=[max(35,int(ms))]*len(drawn)
    if not loop: durations[-1]=min(1800,ms*6)
    drawn[0].save(gif,save_all=True,append_images=drawn[1:],duration=durations,loop=0 if loop else 1,optimize=False)
    margin=14
    width=max(1,len(drawn))*drawn[0].width+max(0,len(drawn)-1)*margin
    strip=Image.new("RGB",(width,drawn[0].height+26),"#f7f7f7")
    d=ImageDraw.Draw(strip)
    for index,im in enumerate(drawn):
        x=index*(im.width+margin)
        strip.paste(im,(x,26))
        d.text((x+6,7),f"F{index+1:02d}",fill="#202020")
    png=basename.with_suffix(".png")
    strip.save(png)
    return [str(gif.relative_to(PROJECT)),str(png.relative_to(PROJECT))]

def main():
    asset_contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
    candidate=json.loads(CANDIDATE_RECORD.read_text(encoding="utf-8"))
    indexed={a["id"]:a for a in candidate["assets"]}
    documented={a["id"]:a for a in asset_contract["assets"]}
    OUT.mkdir(parents=True,exist_ok=True)
    report={
        "schema":"animation-semantic-gate/0.1",
        "timeUTC":datetime.now(timezone.utc).isoformat(),
        "projectId":"live-turret-defense",
        "sourceContractSha256":sha(CONTRACT),
        "candidateRecordSha256":sha(CANDIDATE_RECORD),
        "policy":"fail-closed; pixel/frame checks cannot replace action semantics or Cocos playback",
        "publishApproved":False,
        "results":[],
    }
    for asset_id, actions in SCOPE.items():
        entry=documented[asset_id]
        prior=indexed[asset_id]
        previous={a["action"]:a for a in prior["actions"]}
        for action in actions:
            seq=entry["animations"][action]
            paths=[PROJECT / p for p in seq["frames"]]
            failures=[]
            if len(paths)!=len(SEMANTIC[asset_id][action]):
                failures.append("KEYPOSE_FRAME_COUNT_MISMATCH")
            missing=[str(p) for p in paths if not p.is_file()]
            if missing:
                failures.append("MISSING_FRAMES")
                frames=[]
            else:
                frames=[]
                for path in paths:
                    with Image.open(path) as src:
                        src.load()
                        frames.append(src.convert("RGBA"))
                if any(x.size != tuple(entry["canvas"]) for x in frames):
                    failures.append("FRAME_SIZE_MISMATCH")
                if any(x.getchannel("A").getextrema()[0] == 255 for x in frames):
                    failures.append("MISSING_TRANSPARENT_PIXELS")
            prior_action=previous.get(action,{})
            if prior_action.get("semanticReview") != "PASS":
                failures.append("SEMANTIC_REVIEW_NOT_PASSED")
            if prior_action.get("engineImport") != "PASS":
                failures.append("COCOS_IMPORT_NOT_VERIFIED")
            # 关键姿态必须独立存在、有审查记录。动作名字和帧数不能当作动作成立。
            failures.append("KEY_POSE_EVIDENCE_MISSING")
            previews=gif_and_strip(frames,OUT/(asset_id+"-"+action),seq["frameDurationMs"],seq.get("loop",False)) if frames else []
            record={
                "assetId":asset_id,"name":entry["name"],"action":action,
                "expectedFrames":len(paths),"actualFrames":len(frames),
                "size":entry["canvas"],"frameDurationMs":seq["frameDurationMs"],
                "targetKeyPoses":SEMANTIC[asset_id][action],
                "frameSha256":{p.name:sha(p) for p in paths if p.is_file()},
                "originalGenerationType":"single-master then procedural motion",
                "semanticReview":prior_action.get("semanticReview","MISSING"),
                "engineImport":prior_action.get("engineImport","MISSING"),
                "previewEvidence":previews,
                "gate":"BLOCKED" if failures else "PASS",
                "reasons":failures
            }
            report["results"].append(record)
    report_file=OUT/"动画验收结果.json"
    report_file.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"ok":True,"publishApproved":False,"examined":len(report["results"]),
                      "blocked":sum(a["gate"]=="BLOCKED" for a in report["results"]),
                      "report":str(report_file),"previews":sum(len(a["previewEvidence"]) for a in report["results"])},ensure_ascii=False))
    # --enforce 是打包/发布门禁：只要任一动作未通过，返回非零退出码。
    if "--enforce" in sys.argv and not report["publishApproved"]:
        return 2
    return 0

if __name__=="__main__":
    sys.exit(main())
