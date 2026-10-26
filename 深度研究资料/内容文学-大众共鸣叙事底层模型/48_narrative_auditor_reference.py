#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Narrative Auditor reference implementation v1.

Standard-library-only semantic checks.
Use a Draft 2020-12 JSON Schema validator separately for structural checks.

Usage:
  python 48_narrative_auditor_reference.py state.json delta.json [scene.json]
  python 48_narrative_auditor_reference.py --self-test
"""
import json
import sys
from pathlib import Path

CHANNELS = {"C1_outcome","C2_relationship","C3_agency","C4_meaning","C5_competence"}

def _chars(state):
    return {c.get("id"): c for c in state.get("characters", [])}

def _world(state):
    return {e.get("event_id"): e for e in state.get("timeline", []) if e.get("event_id")}

def audit(state, delta, scene=None):
    blockers, warnings = [], []
    frm = delta.get("from_canon_version")
    to = delta.get("to_canon_version")
    current = state.get("canon_version")

    if frm != current or to != (frm + 1 if isinstance(frm, int) else None):
        blockers.append({"rule_id":"R001","target":"canon_version","evidence":f"state={current}, from={frm}, to={to}"})

    chars = _chars(state)
    world = _world(state)

    # Parser/extractor output is draft material. It must never commit directly.
    for ch in delta.get("changes", []):
        if ch.get("review_required") is True:
            blockers.append({"rule_id":"R000","target":ch.get("change_id"),"evidence":"unreviewed change candidate"})
    for r in delta.get("rewards", []):
        if r.get("review_required") is True:
            blockers.append({"rule_id":"R000","target":r.get("scene_id"),"evidence":"unreviewed reward candidate"})
    for item in delta.get("commitments", {}).get("opened", []):
        if item.get("review_required") is True:
            blockers.append({"rule_id":"R000","target":item.get("id"),"evidence":"unreviewed commitment candidate"})
    if scene and scene.get("review_required") is True:
        blockers.append({"rule_id":"R000","target":scene.get("scene_id"),"evidence":"unreviewed scene contract"})

    for ch in delta.get("changes", []):
        cls = ch.get("transition_class")
        domain = ch.get("domain")
        target = ch.get("target", "")

        if cls == "reset":
            blockers.append({"rule_id":"R002","target":target,"evidence":"transition_class=reset"})

        if domain == "world":
            sid = ch.get("state_id")
            prev = world.get(sid)
            if prev and prev.get("mutable") is False and ch.get("operation") in {"update","remove"}:
                blockers.append({"rule_id":"R003","target":sid or target,"evidence":"locked canon is immutable"})

        if domain == "knowledge" and not (ch.get("evidence") or []):
            blockers.append({"rule_id":"R004","target":target,"evidence":"knowledge change has no source evidence"})

        cid = target.split(":", 1)[0] if ":" in target else None
        if cid and cid in chars:
            forbidden = chars[cid].get("forbidden_resets", [])
            blob = json.dumps(ch.get("after"), ensure_ascii=False)
            for phrase in forbidden:
                if phrase and phrase in blob and cls not in {"relapse","revision","strategy"}:
                    blockers.append({"rule_id":"R005","target":target,"evidence":f"matches forbidden reset: {phrase}"})

    rewards = delta.get("rewards", [])
    for r in rewards:
        if r.get("channel") not in CHANNELS:
            blockers.append({"rule_id":"SCHEMA","target":r.get("scene_id"),"evidence":"unknown reward channel"})

    if scene:
        changes = scene.get("state_changes") or []
        channels = set(scene.get("reward_channels") or [])
        opened = scene.get("commitments_opened") or []
        paid = scene.get("commitments_paid") or []
        hook = (scene.get("hook") or {}).get("present", False)

        if not changes and not channels and not opened and not paid and not hook:
            warnings.append({"rule_id":"W103","target":scene.get("scene_id"),"explanation":"possible_padding/global_reward_gap"})

        if hook and not changes and not channels and not paid:
            warnings.append({"rule_id":"W104","target":scene.get("scene_id"),"explanation":"hook without persistent progress may be false progress"})

    open_commitments = {
        c.get("id"): c for c in state.get("open_commitments", [])
        if c.get("status") in {"open","partially_paid"}
    }
    paid_ids = set(delta.get("commitments", {}).get("paid", []))
    for cid, item in open_commitments.items():
        if cid not in paid_ids and item.get("overdue") is True:
            warnings.append({"rule_id":"W102","target":cid,"explanation":"open commitment marked overdue"})

    verdict = "BLOCK" if blockers else ("REPAIR" if warnings else "PASS")
    return {
        "VERDICT": verdict,
        "BLOCKERS": blockers,
        "WARNINGS": warnings,
        "REWARD": {
            "channels": sorted({r.get("channel") for r in rewards if r.get("channel")}),
            "count": len(rewards)
        },
        "NEXT_ACTION": "return_to_planner" if blockers else ("local_repair" if warnings else "commit")
    }

def self_test():
    state = {
        "canon_version": 3,
        "timeline": [{"event_id":"W1","fact":"父亲已死亡","mutable":False}],
        "characters": [{"id":"linwan","forbidden_resets":["替弟弟还私人债务"]}],
        "open_commitments": [{"id":"K1","status":"open","overdue":True}]
    }
    good = {
        "from_canon_version":3,
        "to_canon_version":4,
        "changes":[{
            "change_id":"C1","domain":"boundary","target":"linwan:boundary",
            "operation":"update","before":"fragile","after":"stable",
            "transition_class":"retain","evidence":["E18S2"],"state_id":"B1"
        }],
        "rewards":[{
            "scene_id":"E19S3","channel":"C3_agency","magnitude":"L1",
            "description":"守住边界","persists":True
        }],
        "commitments":{"opened":[],"paid":["K1"],"abandoned":[]}
    }
    bad = {
        "from_canon_version":3,
        "to_canon_version":5,
        "changes":[{
            "change_id":"C2","domain":"world","target":"W1",
            "operation":"update","before":"死亡","after":"复活",
            "transition_class":"reset","evidence":["无解释"],"state_id":"W1"
        }],
        "rewards":[],
        "commitments":{"opened":[],"paid":[],"abandoned":[]}
    }
    good_result = audit(state, good)
    bad_result = audit(state, bad)
    assert good_result["VERDICT"] in {"PASS","REPAIR"}
    assert bad_result["VERDICT"] == "BLOCK"
    assert any(x["rule_id"] == "R001" for x in bad_result["BLOCKERS"])
    assert any(x["rule_id"] == "R002" for x in bad_result["BLOCKERS"])
    assert any(x["rule_id"] == "R003" for x in bad_result["BLOCKERS"])
    print(json.dumps({"good":good_result,"bad":bad_result}, ensure_ascii=False, indent=2))

def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        self_test()
        return
    if len(sys.argv) not in (3,4):
        print(__doc__.strip())
        raise SystemExit(2)
    state = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    delta = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    scene = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8")) if len(sys.argv) == 4 else None
    print(json.dumps(audit(state, delta, scene), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
