#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Conservative semantic reviewer router v1.

This is not a full semantic understanding model.
It routes obvious cases and escalates ambiguous ones.

Usage:
  python 60_semantic_reviewer_reference.py candidate.json
  python 60_semantic_reviewer_reference.py --self-test
"""
import json
import sys
from pathlib import Path

BELIEF_PREFIXES = ["我觉得","我认为","我就知道","我知道你","你总是","你从来","肯定","一定是","我看你"]
EMOTION_CUES = ["我恨你","我烦死","我受够了","我讨厌你","气死我了","我再也不想见你"]
COMMITMENT_CUES = ["我会","我答应","我保证","明天我","下次我","以后我会","我一定会"]
STATE_CUES = {
    "boundary":["最多","不再","不能再","只负责","只承担","到此为止"],
    "identity":["我可以","我有权","我不是","我不需要再","我想要"],
    "competence":["我学会","我能处理","我已经会","我掌握"],
}
OBJECTIVE_ACTION_CUES = ["签字","转账","登记","报警","起诉","提交","离开","交给","拿回","删除","搬走"]

def review(candidate):
    text=(candidate.get("text") or "").strip()
    speaker=candidate.get("speaker")
    evidence=[f"{candidate.get('scene_id')}#L{candidate.get('line_no')}"]
    out={
        "candidate_id":candidate.get("candidate_id","UNKNOWN"),
        "classification":"ambiguous",
        "decision":"escalate",
        "confidence":0.5,
        "target_domain":None,
        "target_state_id":None,
        "owner":speaker,
        "before":None,
        "proposed_after":None,
        "transition_class":None,
        "evidence":evidence,
        "reason":"insufficient evidence",
        "canon_safe":False,
        "review_required":False
    }

    if any(x in text for x in EMOTION_CUES):
        out.update({
            "classification":"emotion_only",
            "decision":"reject",
            "confidence":0.9,
            "reason":"emotion expression alone does not establish persistent state"
        })
        return out

    if any(text.startswith(x) or x in text for x in BELIEF_PREFIXES):
        out.update({
            "classification":"character_belief",
            "decision":"approve" if speaker else "escalate",
            "confidence":0.86 if speaker else 0.6,
            "target_domain":"knowledge" if speaker else None,
            "proposed_after":{"belief":text},
            "transition_class":"retain" if speaker else None,
            "reason":"subjective statement; store as character belief, not world fact",
            "canon_safe":bool(speaker)
        })
        return out

    if any(x in text for x in COMMITMENT_CUES):
        out.update({
            "classification":"commitment",
            "decision":"approve" if speaker else "escalate",
            "confidence":0.84 if speaker else 0.6,
            "target_domain":"commitment" if speaker else None,
            "proposed_after":{"promise":text},
            "transition_class":"retain" if speaker else None,
            "reason":"future-oriented promise; does not prove completion",
            "canon_safe":bool(speaker)
        })
        return out

    for domain,cues in STATE_CUES.items():
        if any(x in text for x in cues):
            out.update({
                "classification":"actual_state_change",
                "decision":"escalate",
                "confidence":0.72,
                "target_domain":domain,
                "proposed_after":{"candidate_text":text},
                "transition_class":None,
                "reason":"state-change language detected, but persistence and prior state must be checked",
                "canon_safe":False
            })
            return out

    if not speaker and any(x in text for x in OBJECTIVE_ACTION_CUES):
        out.update({
            "classification":"objective_fact",
            "decision":"approve",
            "confidence":0.86,
            "target_domain":"world",
            "proposed_after":{"fact":text},
            "transition_class":"retain",
            "reason":"narrated observable action",
            "canon_safe":True
        })
        return out

    kind=candidate.get("kind")
    if kind=="knowledge" and speaker:
        out.update({
            "classification":"character_belief",
            "decision":"escalate",
            "confidence":0.64,
            "target_domain":"knowledge",
            "proposed_after":{"belief":text},
            "reason":"knowledge cue in dialogue may be belief, inference, or truth; needs context"
        })
        return out

    out["classification"]="no_state_change" if not text else "ambiguous"
    out["decision"]="reject" if not text else "escalate"
    return out

def self_test():
    cases=[
        {
            "candidate_id":"X1","scene_id":"E01S01","line_no":1,
            "speaker":"母亲","kind":"knowledge",
            "text":"我就知道，女儿嫁出去以后心就不在家了。"
        },
        {
            "candidate_id":"X2","scene_id":"E01S01","line_no":2,
            "speaker":"林晚","kind":"boundary",
            "text":"我最多陪两天，不能再全由我承担。"
        },
        {
            "candidate_id":"X3","scene_id":"E01S02","line_no":1,
            "speaker":None,"kind":"resource",
            "text":"林海在护士站登记三晚陪护。"
        }
    ]
    results=[review(x) for x in cases]
    assert results[0]["classification"]=="character_belief"
    assert results[0]["target_domain"]=="knowledge"
    assert results[1]["classification"]=="actual_state_change"
    assert results[1]["decision"]=="escalate"
    assert results[2]["classification"]=="objective_fact"
    assert results[2]["decision"]=="approve"
    print(json.dumps(results,ensure_ascii=False,indent=2))

def main():
    if len(sys.argv)==2 and sys.argv[1]=="--self-test":
        self_test(); return
    if len(sys.argv)!=2:
        print(__doc__.strip()); raise SystemExit(2)
    candidate=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps(review(candidate),ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
