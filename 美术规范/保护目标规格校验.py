# -*- coding: utf-8 -*-
"""审查炮塔+主水晶设计结构。只验证文档，不冒充图片/引擎已通过。"""
import json
import sys
from pathlib import Path

def check_contract(path):
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = []
    towers = obj.get("towers", [])
    if len(towers) != 3:
        errors.append("TOWER_COUNT_MUST_BE_THREE")
    ids = [t.get("id") for t in towers]
    if len(set(ids)) != 3 or any(not i for i in ids):
        errors.append("TOWER_IDS_MUST_BE_UNIQUE")
    core = obj.get("protectedObjective", {})
    if not core:
        errors.append("MISSING_PROTECTED_OBJECTIVE")
    if core.get("assetId") in ids or core.get("isRandomTowerCandidate") is not False:
        errors.append("CORE_MUST_NOT_BE_TOWER_OR_RANDOM_ASSIGNED")
    if core.get("isViewerAssigned") is not False or core.get("isGiftUpgradable") is not False:
        errors.append("CORE_MUST_BE_SHARED_NOT_GIFT_TOWER")
    gp = core.get("gameplayCandidate", {})
    if not isinstance(gp.get("maxHP"), (int, float)) or gp.get("maxHP",0) <= 0:
        errors.append("CORE_MUST_HAVE_POSITIVE_HP")
    if gp.get("lossWhenHpEqualsZero") is not True:
        errors.append("MISSING_LOSS_WHEN_CORE_DESTROYED")
    if gp.get("winWhenAllWavesClearAndHpPositive") is not True:
        errors.append("MISSING_WIN_CONDITION")
    if gp.get("finalEnemyGoal") != "reach-and-attack-objective_energy_core":
        errors.append("ENEMY_MUST_TARGET_CORE")
    frost = next((t for t in towers if t.get("id") == "tower_frost"), None)
    if frost is None or "机械" not in frost.get("name", "") and "喷射" not in frost.get("name", ""):
        errors.append("FROST_TOWER_MUST_BE_MECHANICAL_NO_CRYSTAL_TOWER")
    if frost and "NO_TALL_CRYSTAL" not in frost.get("shape", ""):
        errors.append("FROST_TOWER_CRYSTAL_SILHOUETTE_FORBIDDEN")
    pose = core.get("design", {})
    if pose.get("terrainIsIndependent") is not True or pose.get("neverBakeUI") is not True:
        errors.append("CORE_MUST_NOT_BAKE_GROUND_OR_UI")
    result = {"file": str(path), "status": "PASS_STATIC_ONLY" if not errors else "FAIL",
        "towerCount": len(towers), "protectedObjective": core.get("assetId"),
        "g0": obj.get("gates",{}).get("G0"), "errors": errors, "engineQA":"NOT_RUN"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python 保护目标规格校验.py <合同json>", file=sys.stderr)
        sys.exit(2)
    sys.exit(check_contract(sys.argv[1]))
