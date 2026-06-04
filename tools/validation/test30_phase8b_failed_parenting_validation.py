"""
test30 — Phase 8b failed_parenting branch validation.

Validates outside Maya (mocked cmds) that when cmds.parent raises:
  1. operation_status = failed_parenting on the failing decision.
  2. did_move = False on the failing decision.
  3. new_long_name = None on the failing decision.
  4. warning contains "parenting failed" on the failing decision.
  5. Remaining eligible Production_Meshes decisions continue and succeed.
  6. Non-Production_Meshes eligible decisions remain STATUS_PLANNED (untouched).
  7. Ineligible decisions are unchanged.
"""
import json
import sys
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from maya_production_pipeliner import config, organizer

ARTIFACT_DIR = Path("C:/tmp/maya_test30_validation")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = ARTIFACT_DIR / "test30_failed_parenting_result.json"


def _make_decision(name, route, can_move, operation=None):
    op = operation or (
        config.OPERATION_MOVE if can_move else config.OPERATION_REPORT_ONLY
    )
    return {
        "object_name": name,
        "long_name": "|" + name,
        "new_long_name": None,
        "route": route,
        "target_group": route,
        "reason": "test",
        "warnings": [],
        "execution_mode": config.APPLY,
        "scope_mode": config.ALL_SCENE,
        "can_move": can_move,
        "operation": op,
        "preserve_reason": "",
        "report_only": not can_move,
        "would_move": can_move,
        "did_move": False,
        "operation_status": config.STATUS_PLANNED,
    }


DECISIONS = [
    # eligible PM — cmds.parent will raise (first call)
    _make_decision("ProdMesh_A", config.ROUTE_PRODUCTION_MESHES, True),
    # eligible PM — cmds.parent will succeed (second call)
    _make_decision("ProdMesh_B", config.ROUTE_PRODUCTION_MESHES, True),
    # eligible non-PM — must stay STATUS_PLANNED, untouched
    _make_decision("ReviewMesh_A", config.ROUTE_REVIEW_MISSING_MATERIAL, True),
    # ineligible — can_move=False
    _make_decision("RefMesh_A", config.ROUTE_REFERENCES, False),
]


def main():
    checks = {}
    errors = []

    mock_cmds = mock.MagicMock()
    mock_cmds.objExists.return_value = True
    mock_cmds.listRelatives.return_value = []   # not already in target
    mock_cmds.parent.side_effect = [
        RuntimeError("mock parenting failure"),  # ProdMesh_A fails
        ["ProdMesh_B"],                          # ProdMesh_B succeeds
    ]
    mock_cmds.ls.return_value = [
        "|{0}|{1}|ProdMesh_B".format(
            config.ROOT_GROUP, config.PRODUCTION_MESHES
        )
    ]

    original_cmds = organizer.cmds
    organizer.cmds = mock_cmds
    try:
        result = organizer.apply_routes(DECISIONS)
    finally:
        organizer.cmds = original_cmds

    by_name = {d["object_name"]: d for d in result}
    fail_dec  = by_name["ProdMesh_A"]
    succ_dec  = by_name["ProdMesh_B"]
    plan_dec  = by_name["ReviewMesh_A"]
    inelig    = by_name["RefMesh_A"]

    # 1 — operation_status = failed_parenting on failing decision
    checks["fail_status_failed_parenting"] = (
        fail_dec.get("operation_status") == config.STATUS_FAILED_PARENTING
    )

    # 2 — did_move = False on failing decision
    checks["fail_did_move_false"] = fail_dec.get("did_move") is False

    # 3 — new_long_name = None on failing decision
    checks["fail_new_long_name_none"] = fail_dec.get("new_long_name") is None

    # 4 — warning contains "parenting failed"
    fail_warnings = fail_dec.get("warnings") or []
    checks["fail_warning_contains_parenting_failed"] = any(
        "parenting failed" in w for w in fail_warnings
    )

    # 5 — remaining eligible PM decision was processed and succeeded
    checks["next_pm_did_move"] = succ_dec.get("did_move") is True
    checks["next_pm_status_moved"] = (
        succ_dec.get("operation_status") == config.STATUS_MOVED
    )
    checks["next_pm_new_long_name_set"] = bool(succ_dec.get("new_long_name"))

    # 6 — non-PM eligible stays STATUS_PLANNED, did_move False
    checks["non_pm_stays_planned"] = (
        plan_dec.get("operation_status") == config.STATUS_PLANNED
    )
    checks["non_pm_not_moved"] = plan_dec.get("did_move") is False

    # 7 — ineligible decision unchanged
    checks["ineligible_not_moved"] = inelig.get("did_move") is False

    all_pass = all(checks.values()) and not errors
    output = {"checks": checks, "errors": errors}
    RESULT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))
    print("ALL PASS" if all_pass else "FAIL")


if __name__ == "__main__":
    main()
