# -*- coding: utf-8 -*-
"""回归检查：旧程序性动作生产必须硬阻断，且不改动正式资源。"""
from pathlib import Path
import hashlib,json,subprocess,sys

root=Path(__file__).resolve().parents[2]
formal=root/"美术资源/正式资产"
candidate=root/"美术资源/程序性动画候选"
source=root/"美术资源/生成真实透明帧候选.py"

def tree_hash(folder):
    if not folder.exists():return {}
    return {p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in folder.rglob("*.png") if p.is_file()}

before=tree_hash(formal)
previous=tree_hash(candidate)
assert before, "no existing formal frames to protect"
for n in (1,2):
    run=subprocess.run([sys.executable,str(source)],cwd=root,
                       capture_output=True,text=True,encoding="utf-8",errors="replace")
    assert run.returncode==2, "FAIL: old procedural animation generator not blocked"
    result=json.loads(run.stdout.strip())
    assert result.get("status")=="FAIL_ANIMATION_SEMANTICS" and result.get("blockedActions"), "FAIL: missing action semantic failure"
    assert tree_hash(formal)==before, "FAIL: formal resources were overwritten"
    assert tree_hash(candidate)==previous, "FAIL: candidate files changed despite blocked semantics"
print(json.dumps({"ok":True,"semanticFailClosed":True,"repeatRunsBlocked":2,
                  "formalFramesProtected":len(before),"candidatesProtected":len(previous)},ensure_ascii=False))
