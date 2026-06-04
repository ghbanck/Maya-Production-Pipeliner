import json
import os
import sys
from pathlib import Path

import maya.standalone


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ARTIFACT_DIR = Path("C:/tmp/maya_test11_validation")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = ARTIFACT_DIR / "test11_result.json"
REFERENCE_SCENE_PATH = ARTIFACT_DIR / "selected_child_reference_asset.ma"


def _decision_by_name(route_decisions, object_name):
    for decision in route_decisions:
        if decision.get("object_name") == object_name:
            return decision
    return None


def _compact_decision(decision):
    if not decision:
        return None
    record = decision.get("source_record") or {}
    return {
        "object_name": decision.get("object_name"),
        "long_name": decision.get("long_name"),
        "route": decision.get("route"),
        "target_group": decision.get("target_group"),
        "can_move": decision.get("can_move"),
        "operation": decision.get("operation"),
        "operation_status": decision.get("operation_status"),
        "report_only": decision.get("report_only"),
        "preserve_reason": decision.get("preserve_reason"),
        "did_move": decision.get("did_move"),
        "new_long_name": decision.get("new_long_name"),
        "apply_preflight": decision.get("apply_preflight"),
        "source_record": {
            "long_name": record.get("long_name"),
            "transform_node": record.get("transform_node"),
            "is_selected": record.get("is_selected"),
            "is_referenced": record.get("is_referenced"),
            "namespace": record.get("namespace"),
        },
    }


def _create_reference_asset(cmds):
    cmds.file(new=True, force=True)
    parent = cmds.group(empty=True, name="RefParent_A")
    child_transform, _ = cmds.polyCube(name="RefChildMesh_A")
    cmds.parent(child_transform, parent)
    cmds.file(rename=str(REFERENCE_SCENE_PATH))
    cmds.file(save=True, type="mayaAscii", force=True)


def _create_validation_scene(cmds):
    cmds.file(new=True, force=True)
    cmds.file(
        str(REFERENCE_SCENE_PATH),
        reference=True,
        namespace="refChild",
    )
    child_matches = cmds.ls("*:RefChildMesh_A", long=True) or []
    if not child_matches:
        raise RuntimeError("Referenced child transform was not found.")
    child_long_name = child_matches[0]
    cmds.select(child_long_name, replace=True)
    return child_long_name


def _report_has_preserved_reference(report_path, object_name):
    if not report_path or not os.path.exists(report_path):
        return False
    with open(report_path, encoding="utf-8") as handle:
        payload = json.load(handle)
    for decision in payload.get("route_decisions") or []:
        if decision.get("object_name") != object_name:
            continue
        return (
            decision.get("can_move") is False
            and decision.get("report_only") is True
            and decision.get("operation_status") == "skipped_reference"
            and decision.get("preserve_reason") == "referenced content"
        )
    return False


def main():
    maya.standalone.initialize(name="python")

    import maya.cmds as cmds
    from maya_production_pipeliner import config, pipeline

    _create_reference_asset(cmds)
    selected_child_long_name = _create_validation_scene(cmds)
    assemblies_before = cmds.ls(assemblies=True, long=True) or []

    dry_run_result = pipeline.run(config.SELECTED, config.DRY_RUN)
    apply_result = pipeline.run(config.SELECTED, config.APPLY)

    assemblies_after = cmds.ls(assemblies=True, long=True) or []
    expected_object_name = "refChild:RefChildMesh_A"

    dry_decision = _compact_decision(
        _decision_by_name(dry_run_result.get("route_decisions") or [], expected_object_name)
    )
    apply_decision = _compact_decision(
        _decision_by_name(apply_result.get("route_decisions") or [], expected_object_name)
    )

    result = {
        "reference_scene_path": str(REFERENCE_SCENE_PATH),
        "selected_child_long_name": selected_child_long_name,
        "dry_run": {
            "success": dry_run_result.get("success"),
            "message": dry_run_result.get("message"),
            "route_decisions_count": dry_run_result.get("route_decisions_count"),
            "summary": dry_run_result.get("summary"),
            "target": dry_decision,
        },
        "apply_preflight": {
            "success": apply_result.get("success"),
            "message": apply_result.get("message"),
            "route_decisions_count": apply_result.get("route_decisions_count"),
            "summary": apply_result.get("summary"),
            "target": apply_decision,
        },
        "scene_state": {
            "assemblies_before": assemblies_before,
            "assemblies_after": assemblies_after,
            "outliner_unchanged": assemblies_before == assemblies_after,
            "pipeline_group_created": cmds.objExists(config.ROOT_GROUP),
        },
        "reports": {
            "dry_run_report_paths": dry_run_result.get("report_paths"),
            "apply_report_paths": apply_result.get("report_paths"),
            "apply_json_documents_preservation": _report_has_preserved_reference(
                (apply_result.get("report_paths") or {}).get("json"),
                expected_object_name,
            ),
        },
        "checks": {
            "selected_scope_detected_child_safely": (
                dry_decision is not None
                and dry_run_result.get("route_decisions_count") == 1
                and (dry_run_result.get("summary") or {}).get("scanned") == 1
                and dry_decision.get("long_name") == selected_child_long_name
                and (dry_decision.get("source_record") or {}).get("is_selected") is True
            ),
            "classified_as_referenced_report_only": (
                dry_decision is not None
                and dry_decision.get("route") == config.ROUTE_REFERENCES
                and dry_decision.get("can_move") is False
                and dry_decision.get("report_only") is True
                and dry_decision.get("preserve_reason") == "referenced content"
                and (dry_decision.get("source_record") or {}).get("is_referenced") is True
            ),
            "apply_did_not_parent_selected_reference_child": (
                apply_decision is not None
                and apply_decision.get("did_move") is False
                and apply_decision.get("new_long_name") is None
            ),
            "apply_status_skipped_reference": (
                apply_decision is not None
                and apply_decision.get("operation_status") == config.STATUS_SKIPPED_REFERENCE
                and ((apply_decision.get("apply_preflight") or {}).get("eligible") is False)
            ),
            "outliner_unchanged": assemblies_before == assemblies_after,
            "no_pipeline_group_created": cmds.objExists(config.ROOT_GROUP) is False,
            "apply_json_report_documents_preservation": _report_has_preserved_reference(
                (apply_result.get("report_paths") or {}).get("json"),
                expected_object_name,
            ),
        },
    }

    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(RESULT_PATH)


if __name__ == "__main__":
    main()
