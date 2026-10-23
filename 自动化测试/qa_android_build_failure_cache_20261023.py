# -*- coding: utf-8 -*-
"""Validates the 3.8.2 Android build negative cache without launching Cocos."""
import json
import subprocess
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
config = root / "_assistant-temp" / "android-build-config.json"
script = root / "自动化测试" / "build_android_qa_20261023.cjs"

def check():
    p = subprocess.run(["node", str(script), "--check-cache"], cwd=root, capture_output=True, text=True, encoding="utf-8", check=True, timeout=12)
    return json.loads(p.stdout)

before = check()
assert before["cached"], "verified blocker cache not found"
original = config.read_bytes()
try:
    obj = json.loads(original)
    obj["packages"]["android"]["apiLevel"] = 34 if obj["packages"]["android"]["apiLevel"] != 34 else 33
    config.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    changed = check()
    assert not changed["cached"] and changed["fingerprint"] != before["fingerprint"], "config change failed to invalidate negative cache"
finally:
    config.write_bytes(original)
after = check()
assert after["cached"] and after["fingerprint"] == before["fingerprint"], "cache not recovered on restore"
print(json.dumps({"unchanged": "CACHE_HIT", "changed": "INVALIDATED", "restored": "CACHE_HIT", "result": "PASS", "cocosLaunches": 0}))
