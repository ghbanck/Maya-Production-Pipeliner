import json
import os
import sys
from pathlib import Path

import maya.standalone


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ARTIFACT_DIR = Path("C:/tmp/maya_test06_validation")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = ARTIFACT_DIR / "test06_result.json"


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
        "reason": decision.get("reason"),
        "can_move": decision.get("can_move"),
        "operation": decision.get("operation"),
        "operation_status": decision.get("operation_status"),
        "report_only": decision.get("report_only"),
        "would_move": decision.get("would_move"),
        "did_move": decision.get("did_move"),
        "new_long_name": decision.get("new_long_name"),
        "apply_preflight": decision.get("apply_preflight"),
        "source_record": {
            "is_mesh": record.get("is_mesh"),
            "material_node_count": record.get("material_node_count"),
            "shading_engine_count": record.get("shading_engine_count"),
            "uses_default_material": record.get("uses_default_material"),
            "materials": record.get("materials"),
            "shading_engines": record.get("shading_engines"),
        },
    }


def _create_scene(cmds):
    cmds.file(new=True, force=True)

    mesh_transform, _ = cmds.polyCube(name="ProdMesh_A")

    shader = cmds.shadingNode("lambert", asShader=True, name="ProdLambert_A")
    sg = cmds.sets(
        renderable=True,
        noSurfaceShader=True,
        empty=True,
        name="ProdLambert_A_SG",
    )
    cmds.connectAttr(shader + ".outColor", sg + ".surfaceShader", force=True)
    cmds.sets(mesh_transform, edit=True, forceElement=sg)

    return mesh_transform


def _load_json_report(report_path):
    if not report_path or not os.path.exists(report_path):
        return {}
    with open(report_path, encoding="utf-8") as handle:
        return json.load(handle)


def _txt_contains_production_mesh_route(report_path, object_name):
    if not report_path or not os.path.exists(report_path):
        return False
    text = Path(report_path).read_text(encoding="utf-8")
    return (
        object_name in text
        and "route=Production_Meshes" in text
        and "target=Production_Meshes" in text
        and "can_move=True" in text
    )


def main():
    maya.standalone.initialize(name="python")

    import maya.cmds as cmds
    from maya_production_pipeliner import config, pipeline

    mesh_name = _create_scene(cmds)

    assemblies_before = cmds.ls(assemblies=True, long=True) or []
    pipeline_group_before = cmds.objExists(config.ROOT_GROUP)

    dry_run_result = pipeline.run(config.ALL_SCENE, config.DRY_RUN)
    apply_result = pipeline.run(config.ALL_SCENE, config.APPLY)

    assemblies_after = cmds.ls(assemblies=True, long=True) or []
    pipeline_group_after = cmds.objExists(config.ROOT_GROUP)

    dry_decisions = dry_run_result.get("route_decisions") or []
    apply_decisions = apply_result.get("route_decisions") or []

    dry_target = _compact_decision(_decision_by_name(dry_decisions, mesh_name))
    apply_target = _compact_decision(_decision_by_name(apply_decisions, mesh_name))

    dry_txt_path = (dry_run_result.get("report_paths") or {}).get("txt")
    dry_json_path = (dry_run_result.get("report_paths") or {}).get("json")
    apply_json_path = (apply_result.get("report_paths") or {}).get("json")

    dry_json_report = _load_json_report(dry_json_path)
    apply_json_report = _load_json_report(apply_json_path)

    dry_json_decision = _decision_by_name(
        dry_json_report.get("route_decisions") or [], mesh_name
    )
    apply_json_decision = _decision_by_name(
        apply_json_report.get("route_decisions") or [], mesh_name
    )

    result = {
        "scene_setup": {
            "mesh_name": mesh_name,
            "assemblies_before": assemblies_before,
        },
        "dry_run": {
            "success": dry_run_result.get("success"),
            "message": dry_run_result.get("message"),
            "summary": dry_run_result.get("summary"),
            "route_decisions_count": dry_run_result.get("route_decisions_count"),
            "report_paths": dry_run_result.get("report_paths"),
            "report_paths_exist": {
                "txt": bool(dry_txt_path and os.path.exists(dry_txt_path)),
                "json": bool(dry_json_path and os.path.exists(dry_json_path)),
            },
            "target": dry_target,
        },
        "apply_preflight": {
            "success": apply_result.get("success"),
            "message": apply_result.get("message"),
            "summary": apply_result.get("summary"),
            "route_decisions_count": apply_result.get("route_decisions_count"),
            "report_paths": apply_result.get("report_paths"),
            "target": apply_target,
        },
        "scene_state": {
            "assemblies_after": assemblies_after,
            "outliner_unchanged": assemblies_before == assemblies_after,
            "pipeline_group_before": pipeline_group_before,
            "pipeline_group_after": pipeline_group_after,
        },
        "reports": {
            "dry_txt_contains_production_mesh_route": _txt_contains_production_mesh_route(
                dry_txt_path, mesh_name
            ),
            "dry_json_route": (dry_json_decision or {}).get("route"),
            "dry_json_target_group": (dry_json_decision or {}).get("target_group"),
            "dry_json_operation_status": (dry_json_decision or {}).get("operation_status"),
            "apply_json_route": (apply_json_decision or {}).get("route"),
            "apply_json_eligible": (
                (apply_json_decision or {}).get("apply_preflight") or {}
            ).get("eligible"),
            "apply_json_operation_status": (apply_json_decision or {}).get("operation_status"),
        },
        "checks": {
            "dry_run_routes_to_production_meshes": (
                dry_target is not None
                and dry_target.get("route") == config.ROUTE_PRODUCTION_MESHES
                and dry_target.get("target_group") == config.PRODUCTION_MESHES
                and dry_target.get("reason") == "production mesh candidate"
            ),
            "dry_run_material_facts_confirm_production_path": (
                dry_target is not None
                and (dry_target.get("source_record") or {}).get("is_mesh") is True
                and (dry_target.get("source_record") or {}).get("uses_default_material") is False
                and (dry_target.get("source_record") or {}).get("material_node_count") == 1
                and (dry_target.get("source_record") or {}).get("shading_engine_count") == 1
            ),
            "dry_run_can_move_and_not_report_only": (
                dry_target is not None
                and dry_target.get("can_move") is True
                and dry_target.get("report_only") is False
                and dry_target.get("would_move") is True
            ),
            "dry_run_status_is_dry_run_only": (
                dry_target is not None
                and dry_target.get("operation_status") == config.STATUS_DRY_RUN_ONLY
            ),
            "dry_run_no_name_or_path_changes": (
                dry_target is not None
                and dry_target.get("did_move") is False
                and dry_target.get("new_long_name") is None
            ),
            "dry_run_did_not_create_pipeline_group": (
                pipeline_group_before is False
                and pipeline_group_after is False
            ),
            "dry_run_outliner_unchanged": assemblies_before == assemblies_after,
            "apply_preflight_marks_mesh_eligible_and_planned": (
                apply_target is not None
                and (apply_target.get("apply_preflight") or {}).get("eligible") is True
                and apply_target.get("operation_status") == config.STATUS_PLANNED
            ),
            "apply_preflight_no_scene_mutation": (
                apply_target is not None
                and apply_target.get("did_move") is False
                and apply_target.get("new_long_name") is None
                and pipeline_group_after is False
            ),
            "apply_preflight_message_confirms_no_changes": (
                "without scene changes" in (apply_result.get("message") or "")
            ),
            "reports_written_and_json_contains_decision": (
                bool(dry_txt_path and os.path.exists(dry_txt_path))
                and bool(dry_json_path and os.path.exists(dry_json_path))
                and dry_json_decision is not None
                and dry_json_decision.get("route") == config.ROUTE_PRODUCTION_MESHES
            ),
            "txt_report_surfaces_production_mesh_route": _txt_contains_production_mesh_route(
                dry_txt_path, mesh_name
            ),
        },
    }

    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(RESULT_PATH)


if __name__ == "__main__":
    main()
