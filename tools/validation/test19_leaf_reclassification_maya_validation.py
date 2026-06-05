import json
import sys
from pathlib import Path

import maya.standalone


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ARTIFACT_DIR = Path("C:/tmp/maya_test19_validation")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = ARTIFACT_DIR / "test19_result.json"


def _decision_by_name(route_decisions, object_name):
    for decision in route_decisions or []:
        if decision.get("object_name") == object_name:
            return decision
    return None


def _decision_by_long_name(route_decisions, long_name):
    for decision in route_decisions or []:
        if decision.get("long_name") == long_name:
            return decision
    return None


def _compact_decision(decision):
    if not decision:
        return None
    source = decision.get("source_record") or {}
    return {
        "object_name": decision.get("object_name"),
        "long_name": decision.get("long_name"),
        "new_long_name": decision.get("new_long_name"),
        "route": decision.get("route"),
        "target_group": decision.get("target_group"),
        "can_move": decision.get("can_move"),
        "operation": decision.get("operation"),
        "operation_status": decision.get("operation_status"),
        "did_move": decision.get("did_move"),
        "report_only": decision.get("report_only"),
        "reason": decision.get("reason"),
        "preserve_reason": decision.get("preserve_reason"),
        "apply_preflight": decision.get("apply_preflight"),
        "source_record": {
            "long_name": source.get("long_name"),
            "is_mesh": source.get("is_mesh"),
            "uses_default_material": source.get("uses_default_material"),
            "parent_is_joint": source.get("parent_is_joint"),
            "is_inside_tool_output": source.get("is_inside_tool_output"),
            "is_tool_structural_group": source.get("is_tool_structural_group"),
        },
    }


def _make_material(cmds, shader_name, shading_group_name):
    shader = cmds.shadingNode("lambert", asShader=True, name=shader_name)
    shading_group = cmds.sets(
        renderable=True,
        noSurfaceShader=True,
        empty=True,
        name=shading_group_name,
    )
    cmds.connectAttr(shader + ".outColor", shading_group + ".surfaceShader", force=True)
    return shader, shading_group


def _assign_material(cmds, transform, shading_group):
    cmds.sets(transform, edit=True, forceElement=shading_group)


def _create_scene(cmds):
    cmds.file(new=True, force=True)

    cmds.polyCube(name="ReclassMesh_A")
    _make_material(cmds, "ReclassLambert_A", "ReclassLambert_A_SG")
    _assign_material(cmds, "ReclassMesh_A", "ReclassLambert_A_SG")

    cmds.select(clear=True)
    protected_joint = cmds.joint(name="ProtectedJoint_A", position=(0, 0, 0))
    cmds.select(clear=True)
    cmds.polyCube(name="ProtectedLeafMesh_A")
    cmds.parent("ProtectedLeafMesh_A", protected_joint)

    return {
        "reclass_mesh": "ReclassMesh_A",
        "protected_joint": "ProtectedJoint_A",
        "protected_leaf": "ProtectedLeafMesh_A",
    }


def _structural_snapshot(route_decisions):
    structural_long_names = ["|Pipeline_Organized"] + [
        "|Pipeline_Organized|{0}".format(group_name)
        for group_name in (
            "Production_Meshes",
            "Scene_Utilities",
            "References",
            "Review_MissingMaterial",
            "Review_MultiMaterial",
            "Review_UnclearCases",
        )
    ]
    return {
        long_name: _compact_decision(_decision_by_long_name(route_decisions, long_name))
        for long_name in structural_long_names
    }


def _planned_route_objects(route_decisions):
    return [
        decision.get("object_name")
        for decision in (route_decisions or [])
        if decision.get("operation_status") == "planned"
    ]


def main():
    maya.standalone.initialize(name="python")

    import maya.cmds as cmds
    from maya_production_pipeliner import config, pipeline

    names = _create_scene(cmds)

    first_apply = pipeline.run(config.ALL_SCENE, config.APPLY)
    first_decisions = first_apply.get("route_decisions") or []
    first_reclass = _compact_decision(
        _decision_by_name(first_decisions, names["reclass_mesh"])
    )
    first_protected_leaf = _compact_decision(
        _decision_by_name(first_decisions, names["protected_leaf"])
    )

    reclass_after_first = first_reclass.get("new_long_name")
    _assign_material(
        cmds,
        reclass_after_first or names["reclass_mesh"],
        config.DEFAULT_SHADING_GROUP,
    )

    second_apply = pipeline.run(config.ALL_SCENE, config.APPLY)
    second_decisions = second_apply.get("route_decisions") or []
    second_reclass = _compact_decision(
        _decision_by_name(second_decisions, names["reclass_mesh"])
    )
    second_protected_leaf = _compact_decision(
        _decision_by_name(second_decisions, names["protected_leaf"])
    )
    second_structural = _structural_snapshot(second_decisions)

    third_apply = pipeline.run(config.ALL_SCENE, config.APPLY)
    third_decisions = third_apply.get("route_decisions") or []
    third_reclass = _compact_decision(
        _decision_by_name(third_decisions, names["reclass_mesh"])
    )

    result = {
        "first_apply": {
            "message": first_apply.get("message"),
            "summary": first_apply.get("summary"),
            "route_decisions_count": first_apply.get("route_decisions_count"),
            "reclass_mesh": first_reclass,
            "protected_leaf": first_protected_leaf,
        },
        "second_apply": {
            "message": second_apply.get("message"),
            "summary": second_apply.get("summary"),
            "route_decisions_count": second_apply.get("route_decisions_count"),
            "reclass_mesh": second_reclass,
            "protected_leaf": second_protected_leaf,
            "structural_groups": second_structural,
            "planned_route_objects": _planned_route_objects(second_decisions),
        },
        "third_apply": {
            "message": third_apply.get("message"),
            "summary": third_apply.get("summary"),
            "route_decisions_count": third_apply.get("route_decisions_count"),
            "reclass_mesh": third_reclass,
            "planned_route_objects": _planned_route_objects(third_decisions),
        },
        "checks": {
            "first_apply_moves_safe_mesh_to_production_meshes": (
                first_reclass is not None
                and first_reclass.get("route") == config.ROUTE_PRODUCTION_MESHES
                and first_reclass.get("target_group") == config.PRODUCTION_MESHES
                and first_reclass.get("did_move") is True
                and first_reclass.get("operation_status") == config.STATUS_MOVED
                and "|Pipeline_Organized|Production_Meshes|" in (first_reclass.get("new_long_name") or "")
            ),
            "second_apply_rescans_leaf_inside_tool_output_as_content": (
                second_reclass is not None
                and second_reclass.get("source_record", {}).get("is_inside_tool_output") is True
                and second_reclass.get("source_record", {}).get("is_tool_structural_group") is False
                and second_reclass.get("long_name") == reclass_after_first
            ),
            "second_apply_reclassifies_and_moves_to_new_target": (
                second_reclass is not None
                and second_reclass.get("route") == config.ROUTE_REVIEW_MISSING_MATERIAL
                and second_reclass.get("target_group") == config.REVIEW_MISSING_MATERIAL
                and second_reclass.get("source_record", {}).get("uses_default_material") is True
                and second_reclass.get("apply_preflight", {}).get("eligible") is True
                and second_reclass.get("operation_status") == config.STATUS_MOVED
                and second_reclass.get("did_move") is True
                and "|Pipeline_Organized|Review_MissingMaterial|" in (second_reclass.get("new_long_name") or "")
            ),
            "third_apply_marks_already_in_target": (
                third_reclass is not None
                and third_reclass.get("route") == config.ROUTE_REVIEW_MISSING_MATERIAL
                and third_reclass.get("target_group") == config.REVIEW_MISSING_MATERIAL
                and third_reclass.get("long_name") == second_reclass.get("new_long_name")
                and third_reclass.get("operation_status") == config.STATUS_ALREADY_IN_TARGET
                and third_reclass.get("did_move") is False
                and third_reclass.get("apply_preflight", {}).get("eligible") is False
            ),
            "structural_groups_remain_skipped_tool_structure": all(
                decision is not None
                and decision.get("operation_status") == config.STATUS_SKIPPED_TOOL_STRUCTURE
                and decision.get("can_move") is False
                for decision in second_structural.values()
            ),
            "protected_leaf_remains_preserved_after_rescan": (
                second_protected_leaf is not None
                and second_protected_leaf.get("source_record", {}).get("is_inside_tool_output") is True
                and second_protected_leaf.get("source_record", {}).get("is_tool_structural_group") is False
                and second_protected_leaf.get("can_move") is False
                and second_protected_leaf.get("did_move") is False
                and second_protected_leaf.get("operation_status") == config.STATUS_SKIPPED_SENSITIVE_HIERARCHY
                and second_protected_leaf.get("preserve_reason") == "rig/deformer sensitive content"
            ),
            "no_eligible_final_route_remains_planned_after_apply": (
                not _planned_route_objects(second_decisions)
                and not _planned_route_objects(third_decisions)
            ),
            "report_fields_reflect_original_and_new_long_names": (
                first_reclass is not None
                and second_reclass is not None
                and third_reclass is not None
                and first_reclass.get("long_name") == "|ReclassMesh_A"
                and bool(first_reclass.get("new_long_name"))
                and second_reclass.get("long_name") == first_reclass.get("new_long_name")
                and bool(second_reclass.get("new_long_name"))
            ),
        },
    }

    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(RESULT_PATH)


if __name__ == "__main__":
    main()
