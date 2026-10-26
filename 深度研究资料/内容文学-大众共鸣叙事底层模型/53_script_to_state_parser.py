#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chinese screenplay -> narrative extraction candidates (reference v1).

This parser is intentionally conservative:
- it does NOT directly mutate Canon;
- every extracted fact/change is a candidate with confidence + review_required;
- compile mode compares candidates with an existing narrative_state.json.

Usage:
  python 53_script_to_state_parser.py extract script.md extracted.json
  python 53_script_to_state_parser.py compile state.json extracted.json out_dir
  python 53_script_to_state_parser.py --self-test
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple

EP_RE = re.compile(r"^(?:第\s*)?(\d+)\s*(?:集|话|章)\s*[:：]?(.*)$")
SCENE_RE = re.compile(r"^(?:场景|镜头|SCENE|Scene)\s*([A-Za-z0-9._-]+)?\s*[:：-]?\s*(.*)$")
DIALOGUE_RE = re.compile(r"^([\u4e00-\u9fffA-Za-z0-9_·]{1,20})\s*[:：]\s*(.+)$")
BRACKET_RE = re.compile(r"^[（(【\[].*[）)】\]]$")

CUES = {
    "knowledge": ["知道","发现","得知","听说","看见","看到","意识到","认出","揭开","真相"],
    "boundary": ["不再","拒绝","最多","只能","只负责","不会再","不能再","到此为止","不承担"],
    "relationship": ["和好","原谅","分手","离婚","结婚","决裂","复合","信任","疏远","站在","并肩","承诺"],
    "identity": ["我是","我不是","成为","不再是","做自己","我可以","我有权","我想要"],
    "competence": ["学会","掌握","做到","完成","解决","查清","识别","判断","独立处理"],
    "resource": ["工资卡","房产","公司","股权","存款","工作","职位","合同","证据","录音","录像","钱"],
    "commitment": ["我会","我答应","我保证","一定会","必须","明天","下次","以后会","等我"],
}

REWARD_CUES = {
    "C1_outcome":["赢了","赢下","追回","拿回","受罚","入狱","报警","起诉","成功","夺回","解决"],
    "C2_relationship":["和好","原谅","复合","分手","离婚","拥抱","信任","承诺","并肩","陪护","分工"],
    "C3_agency":["拒绝","坚持","决定","选择","不再","没有撤回","只承担","我来决定","不答应"],
    "C4_meaning":["原来","终于明白","意识到","才知道","理解","为什么","真相","误会"],
    "C5_competence":["学会","掌握","做到","独立","完成","解决","查清","识别","处理"],
}

RELATION_WORDS = ["母亲","妈妈","父亲","爸爸","丈夫","妻子","前夫","前妻","弟弟","姐姐","哥哥","妹妹","儿子","女儿","婆婆","公公","男友","女友","同事","老板"]

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())

def confidence_for(kind: str, text: str) -> float:
    base = 0.58
    if kind == "dialogue":
        base = 0.92
    elif kind in {"knowledge","boundary","relationship","commitment"}:
        base = 0.72
    elif kind in {"identity","competence","resource"}:
        base = 0.66
    if any(w in text for w in ["已经","明确","正式","亲眼","当场","签字","录音","录像"]):
        base += 0.08
    return min(base, 0.95)

def split_script(text: str) -> List[Dict[str, Any]]:
    episodes=[]
    current_ep={"episode":1,"title":"","scenes":[]}
    current_scene={"scene_id":"E01S01","heading":"","lines":[]}
    scene_no=1

    def flush_scene():
        nonlocal current_scene
        if current_scene["lines"] or current_scene["heading"]:
            current_ep["scenes"].append(current_scene)

    def flush_episode():
        nonlocal current_ep
        flush_scene()
        if current_ep["scenes"]:
            episodes.append(current_ep)

    for raw in text.splitlines():
        line=norm(raw)
        if not line:
            continue
        m=EP_RE.match(line)
        if m:
            if current_ep["scenes"] or current_scene["lines"]:
                flush_episode()
            ep=int(m.group(1))
            current_ep={"episode":ep,"title":norm(m.group(2)),"scenes":[]}
            scene_no=1
            current_scene={"scene_id":f"E{ep:02d}S{scene_no:02d}","heading":"","lines":[]}
            continue
        m=SCENE_RE.match(line)
        if m:
            flush_scene()
            scene_no += 1 if current_ep["scenes"] or current_scene["lines"] else 0
            sid=m.group(1) or f"{scene_no:02d}"
            current_scene={"scene_id":f"E{current_ep['episode']:02d}S{scene_no:02d}","heading":norm(m.group(2) or sid),"lines":[]}
            continue
        current_scene["lines"].append(line)

    flush_episode()
    if not episodes and current_scene["lines"]:
        episodes=[current_ep]
    return episodes

def classify_line(line: str) -> Tuple[str, str | None, str]:
    m=DIALOGUE_RE.match(line)
    if m:
        return "dialogue", norm(m.group(1)), norm(m.group(2))
    if BRACKET_RE.match(line):
        return "direction", None, line
    return "action", None, line

def cue_hits(text: str, cue_map=CUES) -> List[str]:
    out=[]
    for kind, words in cue_map.items():
        if any(w in text for w in words):
            out.append(kind)
    return out

def extract(text: str) -> Dict[str, Any]:
    episodes=split_script(text)
    characters={}
    candidates=[]
    scene_contracts=[]
    commitments=[]
    cid=0
    kid=0

    for ep in episodes:
        for sc in ep["scenes"]:
            scene_changes=[]
            scene_rewards=set()
            before_refs=[]
            after_refs=[]
            trigger=""
            choice=""
            opposition=""
            consequence=""
            for idx,line in enumerate(sc["lines"],1):
                kind,speaker,body=classify_line(line)
                if speaker:
                    characters.setdefault(speaker, {"name":speaker,"dialogue_count":0})
                    characters[speaker]["dialogue_count"] += 1
                target_text=body
                hits=cue_hits(target_text)
                if not trigger and kind in {"action","direction"}:
                    trigger=target_text
                if speaker and not choice and any(w in target_text for w in CUES["boundary"]+["决定","选择"]):
                    choice=f"{speaker}: {target_text}"
                if any(w in target_text for w in ["但是","却","反对","指责","拒绝","阻止","逼","要求"]):
                    opposition=target_text
                if idx == len(sc["lines"]):
                    consequence=target_text

                for h in hits:
                    cid += 1
                    candidates.append({
                        "candidate_id":f"X{cid:04d}",
                        "episode":ep["episode"],
                        "scene_id":sc["scene_id"],
                        "line_no":idx,
                        "speaker":speaker,
                        "kind":h,
                        "text":target_text,
                        "confidence":confidence_for(h,target_text),
                        "review_required":True
                    })
                    scene_changes.append(f"X{cid:04d}")

                if "commitment" in hits:
                    kid += 1
                    commitments.append({
                        "id":f"K_CAND_{kid:03d}",
                        "episode":ep["episode"],
                        "scene_id":sc["scene_id"],
                        "speaker":speaker,
                        "promise":target_text,
                        "confidence":confidence_for("commitment",target_text),
                        "review_required":True
                    })

                for channel, words in REWARD_CUES.items():
                    if any(w in target_text for w in words):
                        scene_rewards.add(channel)

            scene_contracts.append({
                "scene_id":sc["scene_id"],
                "episode":ep["episode"],
                "heading":sc["heading"],
                "before_state_refs":before_refs,
                "trigger":trigger or (sc["lines"][0] if sc["lines"] else ""),
                "choice":choice or "",
                "opposition":opposition or "",
                "consequence":consequence or "",
                "state_changes":scene_changes,
                "reward_channels":sorted(scene_rewards),
                "after_state_refs":after_refs,
                "hook":{"present":False,"question":None},
                "commitments_opened":[c["id"] for c in commitments if c["scene_id"]==sc["scene_id"]],
                "commitments_paid":[],
                "risk_flags":[],
                "visual_state_delta":[],
                "review_required":True
            })

    return {
        "format":"script_extraction_v1",
        "episodes":episodes,
        "characters":[{"id":name,"name":name,**meta} for name,meta in characters.items()],
        "candidates":candidates,
        "commitments":commitments,
        "scene_contracts":scene_contracts,
        "warnings":[
            "所有语义抽取均为候选，不得直接写入Canon。",
            "关系、知识、边界和Reward候选必须经人工或LLM审查器确认。",
            "对话说出的内容不等于客观事实。"
        ]
    }

def compile_against_state(state: Dict[str,Any], extracted: Dict[str,Any]) -> Dict[str,Any]:
    current_version=state.get("canon_version",1)
    episode=max([x.get("episode",1) for x in extracted.get("episodes",[])], default=state.get("episode",0)+1)
    changes=[]
    rewards=[]
    for c in extracted.get("candidates",[]):
        domain=c["kind"]
        if domain not in {"knowledge","boundary","relationship","competence","identity","resource"}:
            continue
        speaker=c.get("speaker") or "UNKNOWN"
        changes.append({
            "change_id":"DRAFT_"+c["candidate_id"],
            "domain":domain,
            "target":f"{speaker}:{domain}",
            "operation":"update",
            "before":None,
            "after":{"text":c["text"]},
            "transition_class":"retain",
            "cause":"auto-extracted candidate; requires semantic review",
            "evidence":[f"{c['scene_id']}#L{c['line_no']}"],
            "state_id":None,
            "irreversible":False,
            "review_required":True
        })
    for sc in extracted.get("scene_contracts",[]):
        for ch in sc.get("reward_channels",[]):
            rewards.append({
                "scene_id":sc["scene_id"],
                "channel":ch,
                "magnitude":"L1",
                "description":"auto-extracted reward candidate; requires review",
                "persists":False,
                "review_required":True
            })
    return {
        "episode":episode,
        "from_canon_version":current_version,
        "to_canon_version":current_version+1,
        "changes":changes,
        "rewards":rewards,
        "commitments":{
            "opened":[{"id":c["id"],"promise":c["promise"],"expected_payoff_window":None,"review_required":True} for c in extracted.get("commitments",[])],
            "paid":[],
            "abandoned":[]
        },
        "notes":[
            "DRAFT ONLY: compile输出不可直接Commit。",
            "必须先通过语义审查，把review_required候选确认/删除/重分类。",
            "transition_class默认retain只是占位，不代表已验证。"
        ]
    }

def self_test():
    sample="""# 第2集：边界测试
场景1 医院
护士：今晚需要一位家属陪护。
母亲：你弟弟工作忙，你就多陪几天吧。
林晚：我今天留下，但我最多陪两天，明天让林海来。
林海：姐，你就不能再帮一次吗？
林晚：不能再全由我承担。
场景2 走廊
林晚终于意识到，拒绝不等于不爱。
她决定明天照常去上班。
场景3 电梯口
母亲给林晚发来一条语音：“医药费你弟弟最近手头紧，你先垫一下吧。”
林晚没有回复。
"""
    out=extract(sample)
    assert out["episodes"][0]["episode"] == 2
    assert len(out["scene_contracts"]) == 3
    assert any(x["name"]=="林晚" for x in out["characters"])
    assert "母亲给林晚发来一条语音" not in [x["name"] for x in out["characters"]]
    assert any(x["kind"]=="boundary" for x in out["candidates"])
    assert any("C3_agency" in x["reward_channels"] for x in out["scene_contracts"])
    compiled=compile_against_state({"canon_version":1,"episode":1},out)
    assert compiled["episode"] == 2
    assert compiled["to_canon_version"]==2
    assert compiled["changes"]
    print(json.dumps({
        "episode":out["episodes"][0]["episode"],
        "characters":[x["name"] for x in out["characters"]],
        "candidate_count":len(out["candidates"]),
        "scene_count":len(out["scene_contracts"]),
        "compiled_change_count":len(compiled["changes"])
    },ensure_ascii=False,indent=2))

def main():
    if len(sys.argv)==2 and sys.argv[1]=="--self-test":
        self_test(); return
    if len(sys.argv)<2:
        print(__doc__.strip()); raise SystemExit(2)
    mode=sys.argv[1]
    if mode=="extract" and len(sys.argv)==4:
        text=Path(sys.argv[2]).read_text(encoding="utf-8")
        out=extract(text)
        Path(sys.argv[3]).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
        print(sys.argv[3]); return
    if mode=="compile" and len(sys.argv)==5:
        state=json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        extracted=json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
        outdir=Path(sys.argv[4]); outdir.mkdir(parents=True,exist_ok=True)
        delta=compile_against_state(state,extracted)
        (outdir/"episode_delta_draft.json").write_text(json.dumps(delta,ensure_ascii=False,indent=2),encoding="utf-8")
        (outdir/"scene_contracts_draft.json").write_text(json.dumps(extracted.get("scene_contracts",[]),ensure_ascii=False,indent=2),encoding="utf-8")
        print(str(outdir)); return
    print(__doc__.strip()); raise SystemExit(2)

if __name__=="__main__":
    main()
