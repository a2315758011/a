#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply semantic reviews and build Canon-safe draft artifacts v1.

Usage:
  python 63_review_apply_reference.py state.json extracted.json review_bundle.json out_dir
  python 63_review_apply_reference.py --self-test
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

VALID_TRANSITIONS={"retain","relapse","revision","strategy"}
VALID_DOMAINS={"world","knowledge","boundary","relationship","competence","identity","resource","arc"}

def _idx(items, key):
    out={}
    for x in items:
        k=x.get(key)
        if k:
            out[k]=x
    return out

def apply_reviews(state, extracted, bundle):
    candidate_by_id=_idx(extracted.get("candidates",[]),"candidate_id")
    review_by_id=_idx(bundle.get("candidate_reviews",[]),"candidate_id")
    scene_by_id=_idx(extracted.get("scene_contracts",[]),"scene_id")
    scene_review_by_id=_idx(bundle.get("scene_reviews",[]),"scene_id")

    blockers=[]
    changes=[]
    rewards=[]
    opened=[]
    paid=[]
    approved_scene_contracts=[]

    # Every extracted semantic candidate must be reviewed.
    for cid in candidate_by_id:
        if cid not in review_by_id:
            blockers.append({"rule_id":"SR001","target":cid,"reason":"candidate has no semantic review"})

    for cid,review in review_by_id.items():
        cand=candidate_by_id.get(cid)
        if not cand:
            blockers.append({"rule_id":"SR002","target":cid,"reason":"review points to unknown candidate"})
            continue

        decision=review.get("decision")
        cls=review.get("classification")
        if decision=="escalate":
            blockers.append({"rule_id":"SR003","target":cid,"reason":"semantic review still unresolved"})
            continue
        if decision=="reject":
            continue
        if review.get("canon_safe") is not True:
            blockers.append({"rule_id":"SR004","target":cid,"reason":"approved candidate is not canon_safe"})
            continue
        if review.get("review_required") is not False:
            blockers.append({"rule_id":"SR005","target":cid,"reason":"review not finalized"})
            continue

        domain=review.get("target_domain")
        transition=review.get("transition_class")

        if cls=="commitment":
            owner=review.get("owner") or cand.get("speaker") or "UNKNOWN"
            promise=(review.get("proposed_after") or {}).get("promise") or cand.get("text")
            opened.append({
                "id":"K_"+cid,
                "promise":f"{owner}: {promise}",
                "expected_payoff_window":None,
                "review_required":False
            })
            continue

        if cls in {"emotion_only","no_state_change"}:
            continue

        if domain not in VALID_DOMAINS:
            blockers.append({"rule_id":"SR006","target":cid,"reason":f"unsupported target_domain={domain}"})
            continue
        if transition not in VALID_TRANSITIONS:
            blockers.append({"rule_id":"SR007","target":cid,"reason":f"invalid or unsafe transition={transition}"})
            continue

        target_state_id=review.get("target_state_id")
        owner=review.get("owner") or cand.get("speaker") or "WORLD"
        operation="update" if target_state_id else "create"
        target=f"{owner}:{domain}" if domain!="world" else (target_state_id or "WORLD:new_fact")

        changes.append({
            "change_id":"APPROVED_"+cid,
            "domain":domain,
            "target":target,
            "operation":operation,
            "before":review.get("before"),
            "after":review.get("proposed_after"),
            "transition_class":transition,
            "cause":review.get("reason"),
            "evidence":review.get("evidence") or [f"{cand.get('scene_id')}#L{cand.get('line_no')}"],
            "state_id":target_state_id,
            "irreversible":False,
            "review_required":False
        })

    # Scene contracts also require semantic approval.
    for sid,scene in scene_by_id.items():
        sr=scene_review_by_id.get(sid)
        if not sr:
            blockers.append({"rule_id":"SR101","target":sid,"reason":"scene has no semantic review"})
            continue
        if sr.get("decision")=="escalate":
            blockers.append({"rule_id":"SR102","target":sid,"reason":"scene review unresolved"})
            continue
        if sr.get("decision")=="reject":
            continue
        if sr.get("review_required") is not False:
            blockers.append({"rule_id":"SR103","target":sid,"reason":"scene review not finalized"})
            continue

        channels=sr.get("approved_reward_channels",[])
        descriptions=sr.get("reward_descriptions",{})
        magnitudes=sr.get("reward_magnitude",{})
        for ch in channels:
            rewards.append({
                "scene_id":sid,
                "channel":ch,
                "magnitude":magnitudes.get(ch,"L1"),
                "description":descriptions.get(ch, f"approved {ch} reward"),
                "persists":True,
                "review_required":False
            })

        paid.extend(sr.get("commitments_paid",[]))
        approved_scene_contracts.append({
            "scene_id":sid,
            "episode":scene.get("episode"),
            "before_state_refs":scene.get("before_state_refs",[]),
            "trigger":scene.get("trigger",""),
            "choice":scene.get("choice",""),
            "opposition":scene.get("opposition",""),
            "consequence":scene.get("consequence",""),
            "state_changes":[x for x in sr.get("state_change_candidate_ids",[]) if x in candidate_by_id],
            "reward_channels":channels,
            "after_state_refs":scene.get("after_state_refs",[]),
            "hook":{
                "present":bool(sr.get("hook_valid")),
                "question":sr.get("hook_question") if sr.get("hook_valid") else None
            },
            "commitments_opened":sr.get("commitments_opened",[]),
            "commitments_paid":sr.get("commitments_paid",[]),
            "risk_flags":[],
            "visual_state_delta":scene.get("visual_state_delta",[]),
            "review_required":False
        })

    if blockers:
        return {
            "VERDICT":"BLOCK",
            "BLOCKERS":blockers,
            "episode_delta":None,
            "scene_contracts":None
        }

    episode=max([e.get("episode",1) for e in extracted.get("episodes",[])], default=state.get("episode",0)+1)
    delta={
        "episode":episode,
        "from_canon_version":state.get("canon_version",1),
        "to_canon_version":state.get("canon_version",1)+1,
        "changes":changes,
        "rewards":rewards,
        "commitments":{
            "opened":opened,
            "paid":sorted(set(paid)),
            "abandoned":[]
        },
        "notes":["Built from finalized Semantic Review Bundle; still requires Narrative Auditor PASS."]
    }
    return {
        "VERDICT":"PASS",
        "BLOCKERS":[],
        "episode_delta":delta,
        "scene_contracts":approved_scene_contracts
    }

def self_test():
    state={"canon_version":1,"episode":1}
    extracted={
        "episodes":[{"episode":2}],
        "candidates":[
            {"candidate_id":"X1","scene_id":"E02S01","line_no":1,"speaker":"母亲","text":"我就知道，女儿心不在家。"},
            {"candidate_id":"X2","scene_id":"E02S01","line_no":2,"speaker":"林晚","text":"我最多陪两天。"}
        ],
        "scene_contracts":[
            {
                "scene_id":"E02S01","episode":2,
                "before_state_refs":[],"trigger":"母亲要求继续陪护",
                "choice":"林晚拒绝全天陪护","opposition":"母亲哭泣",
                "consequence":"林晚仍坚持两天","after_state_refs":[],
                "visual_state_delta":[]
            }
        ]
    }
    bundle={
        "candidate_reviews":[
            {
                "candidate_id":"X1","classification":"character_belief","decision":"approve",
                "confidence":0.9,"target_domain":"knowledge","target_state_id":None,
                "owner":"母亲","before":None,"proposed_after":{"belief":"女儿心不在家"},
                "transition_class":"retain","evidence":["E02S01#L1"],
                "reason":"subjective belief","canon_safe":True,"review_required":False
            },
            {
                "candidate_id":"X2","classification":"actual_state_change","decision":"approve",
                "confidence":0.9,"target_domain":"boundary","target_state_id":"B1",
                "owner":"林晚","before":{"strength":"developing"},
                "proposed_after":{"strength":"stable","rule":"最多陪两天"},
                "transition_class":"retain","evidence":["E02S01#L2"],
                "reason":"boundary survives pressure","canon_safe":True,"review_required":False
            }
        ],
        "scene_reviews":[
            {
                "scene_id":"E02S01","decision":"approve","confidence":0.9,
                "approved_reward_channels":["C3_agency"],
                "reward_descriptions":{"C3_agency":"林晚在压力下仍守住两天边界"},
                "reward_magnitude":{"C3_agency":"L2"},
                "hook_valid":True,"hook_question":"费用问题会不会再次测试边界？",
                "state_change_candidate_ids":["X2"],
                "commitments_opened":[],"commitments_paid":[],
                "reason":"scene changes boundary state","review_required":False
            }
        ]
    }
    result=apply_reviews(state,extracted,bundle)
    assert result["VERDICT"]=="PASS"
    assert result["episode_delta"]["to_canon_version"]==2
    assert result["episode_delta"]["changes"][1]["target"]=="林晚:boundary"
    assert result["scene_contracts"][0]["review_required"] is False

    bad=json.loads(json.dumps(bundle,ensure_ascii=False))
    bad["candidate_reviews"][1]["decision"]="escalate"
    blocked=apply_reviews(state,extracted,bad)
    assert blocked["VERDICT"]=="BLOCK"
    assert any(x["rule_id"]=="SR003" for x in blocked["BLOCKERS"])
    print(json.dumps({"pass_case":result,"blocked_case":blocked},ensure_ascii=False,indent=2))

def main():
    if len(sys.argv)==2 and sys.argv[1]=="--self-test":
        self_test(); return
    if len(sys.argv)!=5:
        print(__doc__.strip()); raise SystemExit(2)
    state=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    extracted=json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    bundle=json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
    outdir=Path(sys.argv[4]); outdir.mkdir(parents=True,exist_ok=True)
    result=apply_reviews(state,extracted,bundle)
    (outdir/"review_apply_result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    if result["VERDICT"]=="PASS":
        (outdir/"approved_episode_delta.json").write_text(json.dumps(result["episode_delta"],ensure_ascii=False,indent=2),encoding="utf-8")
        (outdir/"approved_scene_contracts.json").write_text(json.dumps(result["scene_contracts"],ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"VERDICT":result["VERDICT"],"BLOCKERS":result["BLOCKERS"]},ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
