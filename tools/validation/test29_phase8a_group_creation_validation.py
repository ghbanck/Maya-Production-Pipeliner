"""
test29 — Phase 8a group creation validation.

Validates outside Maya (mocked cmds) that:
  1. ensure_group_structure() returns {} when cmds is None.
  2. Creates ROOT_GROUP when not present.
  3. Creates all OUTPUT_GROUPS child groups when not present.
  4. Reuses existing groups without calling createNode.
  5. pipeline.run() Apply path calls ensure_group_structure().
  6. pipeline.run() Dry Run path does NOT call ensure_group_structure().
  7. RunResult contains group_structure_status key in Apply mode.
  8. Apply RunResult message no longer says "preflight completed without scene changes".

Maya runtime validation (group creation in a real scene, idempotency,
child group list) must be performed manually per the test checklist.
"""
import json
import sys
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from maya_production_pipeliner import config, organizer, pipeline

ARTIFACT_DIR = Path("C:/tmp/maya_test29_validation")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = ARTIFACT_DIR / "test29_result.json"

OBJECT_RECORDS = [{
    "object_name": "Cube_A",
    "long_name": "|Cube_A",
    "matches_ignore_string": False,
    "warnings": [],
}]

ROUTE_DECISIONS = [{
    "object_name": "Cube_A",
    "long_name": "|Cube_A",
    "new_long_name": None,
    "route": config.ROUTE_PRODUCTION_MESHES,
    "target_group": config.PRODUCTION_MESHES,
    "reason": "production mesh candidate",
    "warnings": [],
    "execution_mode": config.APPLY,
    "scope_mode": config.ALL_SCENE,
    "can_move": True,
    "operation": config.OPERATION_MOVE,
    "preserve_reason": "",
    "report_only": False,
    "would_move": True,
    "did_move": False,
    "operation_status": config.STATUS_PLANNED,
}]

FAKE_REPORT_PATHS = {
    "txt": str(ARTIFACT_DIR / "maya_production_pipeliner_report.txt"),
    "json": str(ARTIFACT_DIR / "maya_production_pipeliner_report.json"),
}


def _mock_cmds_empty():
    """Simulate a scene with no groups present."""
    m = mock.MagicMock()
    m.objExists.return_value = False
    m.createNode.return_value = "new_node"
    return m


def _mock_cmds_full():
    """Simulate a scene where all groups already exist."""
    m = mock.MagicMock()
    m.objExists.return_value = True
    return m


def main():
    checks = {}
    errors = []

    # 1 — ensure_group_structure returns {} when cmds is None
    original_cmds = organizer.cmds
    organizer.cmds = None
    result_no_cmds = organizer.ensure_group_structure()
    organizer.cmds = original_cmds
    checks["returns_empty_outside_maya"] = result_no_cmds == {}

    # 2 — creates ROOT_GROUP when not present
    mock_cmds = _mock_cmds_empty()
    organizer.cmds = mock_cmds
    status_empty = organizer.ensure_group_structure()
    organizer.cmds = original_cmds
    checks["root_group_created"] = status_empty.get(config.ROOT_GROUP) == "created"

    # 3 — creates all OUTPUT_GROUPS child groups when not present
    all_children_created = all(
        status_empty.get(g) == "created" for g in config.OUTPUT_GROUPS
    )
    checks["all_output_groups_created"] = all_children_created
    checks["output_groups_count"] = len(config.OUTPUT_GROUPS)

    # 4 — reuses existing groups without calling createNode
    mock_cmds_full = _mock_cmds_full()
    organizer.cmds = mock_cmds_full
    status_full = organizer.ensure_group_structure()
    organizer.cmds = original_cmds
    all_reused = all(
        v == "reused" for v in status_full.values()
    )
    checks["existing_groups_reused"] = all_reused
    checks["createNode_not_called_when_all_present"] = (
        mock_cmds_full.createNode.call_count == 0
    )

    # 5 — pipeline Apply path calls ensure_group_structure
    with mock.patch.object(pipeline.scanner, "scan", return_value=OBJECT_RECORDS):
        with mock.patch.object(pipeline.classifier, "classify",
                               return_value=ROUTE_DECISIONS):
            with mock.patch.object(pipeline.organizer, "apply_routes",
                                   return_value=ROUTE_DECISIONS):
                with mock.patch.object(pipeline.reporter, "write_reports",
                                       return_value=FAKE_REPORT_PATHS):
                    with mock.patch.object(
                        pipeline.organizer, "ensure_group_structure",
                        return_value={config.ROOT_GROUP: "created"}
                    ) as mock_ensure:
                        apply_result = pipeline.run(
                            config.ALL_SCENE, config.APPLY
                        )
    checks["apply_calls_ensure_group_structure"] = mock_ensure.called

    # 6 — pipeline Dry Run path does NOT call ensure_group_structure
    with mock.patch.object(pipeline.scanner, "scan", return_value=OBJECT_RECORDS):
        with mock.patch.object(pipeline.classifier, "classify",
                               return_value=ROUTE_DECISIONS):
            with mock.patch.object(pipeline.reporter, "write_reports",
                                   return_value=FAKE_REPORT_PATHS):
                with mock.patch.object(
                    pipeline.organizer, "ensure_group_structure",
                    return_value={}
                ) as mock_ensure_dry:
                    dry_result = pipeline.run(
                        config.ALL_SCENE, config.DRY_RUN
                    )
    checks["dry_run_does_not_call_ensure_group_structure"] = (
        not mock_ensure_dry.called
    )

    # 7 — RunResult has group_structure_status key in Apply mode
    checks["apply_runresult_has_group_structure_status"] = (
        "group_structure_status" in apply_result
    )

    # 8 — Apply message no longer says "preflight completed without scene changes"
    apply_message = apply_result.get("message", "")
    checks["apply_message_updated"] = (
        "preflight completed without scene changes" not in apply_message
        and "group structure ready" in apply_message
    )

    # 9 — Dry Run message unchanged
    dry_message = dry_result.get("message", "")
    checks["dry_run_message_unchanged"] = (
        dry_message == "Dry Run completed without scene changes."
    )

    all_pass = all(
        v is True for k, v in checks.items()
        if k != "output_groups_count"
    ) and not errors

    result = {"checks": checks, "errors": errors}
    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print("ALL PASS" if all_pass else "FAIL")


if __name__ == "__main__":
    main()
