import json
import os
import sys
from pathlib import Path

import maya.standalone


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ARTIFACT_DIR = Path("C:/tmp/maya_test17_validation")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = ARTIFACT_DIR / "test17_result.json"


def _compact_record(record):
    if not record:
        return None
    return {
        "name": record.get("name"),
        "long_name": record.get("long_name"),
        "transform_node": record.get("transform_node"),
        "is_selected": record.get("is_selected"),
        "is_mesh": record.get("is_mesh"),
        "shape_nodes": record.get("shape_nodes"),
    }


def _compact_decision(decision):
    if not decision:
        return None
    return {
        "object_name": decision.get("object_name"),
        "long_name": decision.get("long_name"),
        "route": decision.get("route"),
        "target_group": decision.get("target_group"),
        "can_move": decision.get("can_move"),
        "operation_status": decision.get("operation_status"),
        "did_move": decision.get("did_move"),
        "new_long_name": decision.get("new_long_name"),
        "source_record": {
            "long_name": (decision.get("source_record") or {}).get("long_name"),
            "is_selected": (decision.get("source_record") or {}).get("is_selected"),
            "is_mesh": (decision.get("source_record") or {}).get("is_mesh"),
        },
        "apply_preflight": decision.get("apply_preflight"),
    }


def _find_record(records, long_name):
    for record in records:
        if record.get("long_name") == long_name:
            return record
    return None


def _find_decision(decisions, long_name):
    for decision in decisions:
        if decision.get("long_name") == long_name:
            return decision
    return None


def _json_report_has_long_names(report_path, expected_long_names):
    if not report_path or not os.path.exists(report_path):
        return False
    with open(report_path, encoding="utf-8") as handle:
        payload = json.load(handle)
    found = set()
    for decision in payload.get("route_decisions") or []:
        long_name = decision.get("long_name")
        if long_name in expected_long_names:
            found.add(long_name)
    return found == set(expected_long_names)


def _create_validation_scene(cmds):
    cmds.file(new=True, force=True)
    parent_transform, _ = cmds.polyCube(name="ConflictParent_A")
    child_transform, _ = cmds.polyCube(name="ConflictChild_A")
    cmds.parent(child_transform, parent_transform)

    parent_long = cmds.ls(parent_transform, long=True)[0]
    child_long = cmds.ls("|ConflictParent_A|ConflictChild_A", long=True)[0]
    return parent_long, child_long


def main():
    maya.standalone.initialize(name="python")

    import maya.cmds as cmds
    from maya_production_pipeliner import config, pipeline, scanner

    parent_long, child_long = _create_validation_scene(cmds)
    expected_long_names = [parent_long, child_long]

    cmds.select(parent_long, child_long, replace=True)
    selected_records = scanner.scan(config.SELECTED)
    dry_run_result = pipeline.run(config.SELECTED, config.DRY_RUN)
    apply_result = pipeline.run(config.SELECTED, config.APPLY)

    selected_targets = [
        _compact_record(_find_record(selected_records, long_name))
        for long_name in expected_long_names
    ]
    dry_targets = [
        _compact_decision(_find_decision(dry_run_result.get("route_decisions") or [], long_name))
        for long_name in expected_long_names
    ]
    apply_targets = [
        _compact_decision(_find_decision(apply_result.get("route_decisions") or [], long_name))
        for long_name in expected_long_names
    ]

    result = {
        "expected_long_names": expected_long_names,
        "selected_records": selected_targets,
        "dry_run": {
            "success": dry_run_result.get("success"),
            "message": dry_run_result.get("message"),
            "summary": dry_run_result.get("summary"),
            "route_decisions_count": dry_run_result.get("route_decisions_count"),
            "warnings": dry_run_result.get("warnings"),
            "targets": dry_targets,
        },
        "apply_preflight": {
            "success": apply_result.get("success"),
            "message": apply_result.get("message"),
            "summary": apply_result.get("summary"),
            "route_decisions_count": apply_result.get("route_decisions_count"),
            "warnings": apply_result.get("warnings"),
            "targets": apply_targets,
        },
        "reports": {
            "dry_run_report_paths": dry_run_result.get("report_paths"),
            "apply_report_paths": apply_result.get("report_paths"),
            "dry_json_has_both_long_names": _json_report_has_long_names(
                (dry_run_result.get("report_paths") or {}).get("json"),
                expected_long_names,
            ),
            "apply_json_has_both_long_names": _json_report_has_long_names(
                (apply_result.get("report_paths") or {}).get("json"),
                expected_long_names,
            ),
        },
        "checks": {
            "selected_scope_handled_both_inputs_safely": (
                len([record for record in selected_targets if record]) == 2
                and all(record.get("is_selected") is True for record in selected_targets if record)
                and (dry_run_result.get("summary") or {}).get("scanned") == 2
                and dry_run_result.get("route_decisions_count") == 2
            ),
            "route_plan_kept_parent_and_child_distinct": (
                len([decision for decision in dry_targets if decision]) == 2
                and len({decision["long_name"] for decision in dry_targets if decision}) == 2
            ),
            "apply_preflight_avoided_destructive_double_parenting": (
                len([decision for decision in apply_targets if decision]) == 2
                and all(decision.get("did_move") is False for decision in apply_targets if decision)
                and all(decision.get("new_long_name") is None for decision in apply_targets if decision)
            ),
            "warnings_or_clear_status_recorded": (
                all(decision.get("operation_status") for decision in apply_targets if decision)
                and isinstance(apply_result.get("warnings"), list)
            ),
            "reports_trace_both_long_names": (
                _json_report_has_long_names(
                    (dry_run_result.get("report_paths") or {}).get("json"),
                    expected_long_names,
                )
                and _json_report_has_long_names(
                    (apply_result.get("report_paths") or {}).get("json"),
                    expected_long_names,
                )
            ),
        },
    }

    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(RESULT_PATH)


if __name__ == "__main__":
    main()
