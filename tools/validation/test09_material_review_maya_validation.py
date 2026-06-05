import json
import os
import sys
from pathlib import Path

import maya.standalone


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ARTIFACT_DIR = Path("C:/tmp/maya_test09_validation")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = ARTIFACT_DIR / "test09_result.json"


def _decision_by_name(route_decisions, name):
    for decision in route_decisions or []:
        if decision.get("object_name") == name:
            return decision
    return None


def _compact(decision):
    if not decision:
        return None
    source = decision.get("source_record") or {}
    return {
        "object_name": decision.get("object_name"),
        "did_move": decision.get("did_move"),
        "new_long_name": decision.get("new_long_name"),
        "apply_preflight": decision.get("apply_preflight"),
        "route": decision.get("route"),
        "target_group": decision.get("target_group"),
        "can_move": decision.get("can_move"),
        "operation_status": decision.get("operation_status"),
        "reason": decision.get("reason"),
        "preserve_reason": decision.get("preserve_reason"),
        "report_only": decision.get("report_only"),
        "source_materials": source.get("materials"),
        "source_material_count": source.get("material_count"),
        "source_material_node_count": source.get("material_node_count"),
        "source_shading_engines": source.get("shading_engines"),
        "source_shading_engine_count": source.get("shading_engine_count"),
        "uses_default_material": source.get("uses_default_material"),
    }


def _load_report(report_path):
    if not report_path or not os.path.exists(report_path):
        return None
    with open(report_path, encoding="utf-8") as handle:
        return json.load(handle)


def _report_decision(report_payload, name):
    for decision in (report_payload or {}).get("route_decisions") or []:
        if decision.get("object_name") == name:
            return decision
    return None


def _create_scene(cmds):
    cmds.file(new=True, force=True)

    cmds.polyCube(name="DefaultMaterialMesh_A")

    cmds.polyCube(name="MultiMaterialMesh_A")
    shader_a = cmds.shadingNode("lambert", asShader=True, name="MultiLambert_A")
    shader_b = cmds.shadingNode("lambert", asShader=True, name="MultiLambert_B")
    sg_a = cmds.sets(
        renderable=True,
        noSurfaceShader=True,
        empty=True,
        name="MultiLambert_A_SG",
    )
    sg_b = cmds.sets(
        renderable=True,
        noSurfaceShader=True,
        empty=True,
        name="MultiLambert_B_SG",
    )
    cmds.connectAttr(shader_a + ".outColor", sg_a + ".surfaceShader", force=True)
    cmds.connectAttr(shader_b + ".outColor", sg_b + ".surfaceShader", force=True)
    cmds.sets("MultiMaterialMesh_A.f[0:2]", edit=True, forceElement=sg_a)
    cmds.sets("MultiMaterialMesh_A.f[3:5]", edit=True, forceElement=sg_b)


def main():
    maya.standalone.initialize(name="python")

    import maya.cmds as cmds
    from maya_production_pipeliner import config, pipeline

    _create_scene(cmds)
    dry_run_result = pipeline.run(config.ALL_SCENE, config.DRY_RUN)
    apply_result = pipeline.run(config.ALL_SCENE, config.APPLY)

    dry_route_decisions = dry_run_result.get("route_decisions") or []
    apply_route_decisions = apply_result.get("route_decisions") or []
    default_decision = _compact(_decision_by_name(dry_route_decisions, "DefaultMaterialMesh_A"))
    multi_decision = _compact(_decision_by_name(dry_route_decisions, "MultiMaterialMesh_A"))
    apply_default_decision = _compact(
        _decision_by_name(apply_route_decisions, "DefaultMaterialMesh_A")
    )
    apply_multi_decision = _compact(
        _decision_by_name(apply_route_decisions, "MultiMaterialMesh_A")
    )

    report_payload = _load_report((dry_run_result.get("report_paths") or {}).get("json"))
    report_default = _report_decision(report_payload, "DefaultMaterialMesh_A")
    report_multi = _report_decision(report_payload, "MultiMaterialMesh_A")

    result = {
        "dry_run": {
            "success": dry_run_result.get("success"),
            "message": dry_run_result.get("message"),
            "route_decisions_count": dry_run_result.get("route_decisions_count"),
            "report_paths": dry_run_result.get("report_paths"),
            "default_material_mesh": default_decision,
            "multi_material_mesh": multi_decision,
        },
        "apply": {
            "success": apply_result.get("success"),
            "message": apply_result.get("message"),
            "route_decisions_count": apply_result.get("route_decisions_count"),
            "report_paths": apply_result.get("report_paths"),
            "default_material_mesh": apply_default_decision,
            "multi_material_mesh": apply_multi_decision,
        },
        "report_payload": {
            "default_material_mesh": report_default,
            "multi_material_mesh": report_multi,
        },
        "checks": {
            "default_material_routed_to_missing_material": (
                default_decision is not None
                and default_decision["route"] == config.ROUTE_REVIEW_MISSING_MATERIAL
                and default_decision["target_group"] == config.REVIEW_MISSING_MATERIAL
                and default_decision["uses_default_material"] is True
                and default_decision["reason"] == "material review required"
            ),
            "multi_material_routed_to_multi_material": (
                multi_decision is not None
                and multi_decision["route"] == config.ROUTE_REVIEW_MULTI_MATERIAL
                and multi_decision["target_group"] == config.REVIEW_MULTI_MATERIAL
                and (multi_decision["source_material_node_count"] or 0) > 1
                and (multi_decision["source_shading_engine_count"] or 0) > 1
                and multi_decision["reason"] == "material review required"
            ),
            "material_review_routes_are_movable_in_dry_run": (
                default_decision["can_move"] is True
                and default_decision["operation_status"] == config.STATUS_DRY_RUN_ONLY
                and multi_decision["can_move"] is True
                and multi_decision["operation_status"] == config.STATUS_DRY_RUN_ONLY
            ),
            "apply_material_review_routes_do_not_stay_planned": (
                apply_default_decision is not None
                and apply_multi_decision is not None
                and (apply_default_decision.get("operation_status") in (
                    config.STATUS_MOVED,
                    config.STATUS_ALREADY_IN_TARGET,
                ))
                and (apply_multi_decision.get("operation_status") in (
                    config.STATUS_MOVED,
                    config.STATUS_ALREADY_IN_TARGET,
                ))
                and apply_default_decision.get("operation_status") != config.STATUS_PLANNED
                and apply_multi_decision.get("operation_status") != config.STATUS_PLANNED
            ),
            "report_documents_material_counts": (
                report_default is not None
                and report_multi is not None
                and ((report_default.get("source_record") or {}).get("material_node_count") is not None)
                and ((report_multi.get("source_record") or {}).get("material_node_count") or 0) > 1
                and ((report_multi.get("source_record") or {}).get("shading_engine_count") or 0) > 1
            ),
        },
    }

    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(RESULT_PATH)


if __name__ == "__main__":
    main()
