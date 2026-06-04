import json
import os
import sys
from pathlib import Path

import maya.standalone


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ARTIFACT_DIR = Path("C:/tmp/maya_test15_validation")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = ARTIFACT_DIR / "test15_result.json"


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
        "operation_status": decision.get("operation_status"),
        "did_move": decision.get("did_move"),
        "new_long_name": decision.get("new_long_name"),
        "source_record_long_name": (decision.get("source_record") or {}).get("long_name"),
        "source_record_selected": (decision.get("source_record") or {}).get("is_selected"),
    }


def _create_validation_scene(cmds):
    cmds.file(new=True, force=True)

    parent_a = cmds.group(empty=True, name="DupParent_A")
    parent_b = cmds.group(empty=True, name="DupParent_B")

    mesh_a, _ = cmds.polyCube(name="DupMesh_A")
    mesh_b, _ = cmds.polyCube(name="DupMesh_B")

    mesh_a = cmds.rename(mesh_a, "SameNameMesh_A")
    mesh_b = cmds.rename(mesh_b, "SameNameMesh_B")

    mesh_a = cmds.parent(mesh_a, parent_a)[0]
    mesh_b = cmds.parent(mesh_b, parent_b)[0]

    cmds.rename(mesh_a, "SharedMesh")
    cmds.rename(mesh_b, "SharedMesh")

    mesh_a_long = cmds.ls("|{0}|SharedMesh".format(parent_a), long=True)[0]
    mesh_b_long = cmds.ls("|{0}|SharedMesh".format(parent_b), long=True)[0]
    return mesh_a_long, mesh_b_long


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


def main():
    maya.standalone.initialize(name="python")

    import maya.cmds as cmds
    from maya_production_pipeliner import config, pipeline, scanner

    mesh_a_long, mesh_b_long = _create_validation_scene(cmds)
    expected_long_names = [mesh_a_long, mesh_b_long]

    all_scene_records = scanner.scan(config.ALL_SCENE)

    cmds.select(mesh_a_long, mesh_b_long, replace=True)
    selected_records = scanner.scan(config.SELECTED)
    dry_run_result = pipeline.run(config.SELECTED, config.DRY_RUN)

    all_scene_target_records = [
        _compact_record(_find_record(all_scene_records, long_name))
        for long_name in expected_long_names
    ]
    selected_target_records = [
        _compact_record(_find_record(selected_records, long_name))
        for long_name in expected_long_names
    ]
    dry_target_decisions = [
        _compact_decision(_find_decision(dry_run_result.get("route_decisions") or [], long_name))
        for long_name in expected_long_names
    ]

    result = {
        "expected_long_names": expected_long_names,
        "all_scene_records": all_scene_target_records,
        "selected_records": selected_target_records,
        "dry_run": {
            "success": dry_run_result.get("success"),
            "message": dry_run_result.get("message"),
            "summary": dry_run_result.get("summary"),
            "route_decisions_count": dry_run_result.get("route_decisions_count"),
            "targets": dry_target_decisions,
        },
        "reports": {
            "report_paths": dry_run_result.get("report_paths"),
            "json_report_has_both_long_names": _json_report_has_long_names(
                (dry_run_result.get("report_paths") or {}).get("json"),
                expected_long_names,
            ),
        },
        "checks": {
            "all_scene_kept_duplicate_records_distinct": (
                len([record for record in all_scene_target_records if record]) == 2
                and len({record["long_name"] for record in all_scene_target_records if record}) == 2
                and all(record.get("name") == "SharedMesh" for record in all_scene_target_records if record)
            ),
            "selected_scope_kept_both_inputs": (
                len([record for record in selected_target_records if record]) == 2
                and all(record.get("is_selected") is True for record in selected_target_records if record)
            ),
            "dry_run_kept_both_route_decisions_distinct": (
                dry_run_result.get("route_decisions_count") == 2
                and (dry_run_result.get("summary") or {}).get("scanned") == 2
                and len([decision for decision in dry_target_decisions if decision]) == 2
                and len({decision["long_name"] for decision in dry_target_decisions if decision}) == 2
            ),
            "json_report_preserved_original_long_names": _json_report_has_long_names(
                (dry_run_result.get("report_paths") or {}).get("json"),
                expected_long_names,
            ),
        },
    }

    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(RESULT_PATH)


if __name__ == "__main__":
    main()
