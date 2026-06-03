import json
import os
import sys
from pathlib import Path

import maya.standalone


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ARTIFACT_DIR = Path("C:/tmp/maya_test10_12_13_validation")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = ARTIFACT_DIR / "test10_12_13_result.json"
REFERENCE_SCENE_PATH = ARTIFACT_DIR / "referenced_asset.ma"


def _decision_by_name(route_decisions, name):
    for decision in route_decisions:
        if decision.get("object_name") == name:
            return decision
    return None


def _source_record(decision):
    return (decision or {}).get("source_record") or {}


def _compact_decision(decision):
    if not decision:
        return None
    record = _source_record(decision)
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
        "source_flags": {
            "is_referenced": record.get("is_referenced"),
            "is_instanced": record.get("is_instanced"),
            "has_skin_cluster": record.get("has_skin_cluster"),
            "has_blendshape": record.get("has_blendshape"),
            "parent_is_joint": record.get("parent_is_joint"),
            "is_under_sensitive_hierarchy": record.get("is_under_sensitive_hierarchy"),
        },
    }


def _create_reference_asset(cmds):
    cmds.file(new=True, force=True)
    cmds.polyCube(name="RefMesh_A")
    cmds.file(rename=str(REFERENCE_SCENE_PATH))
    cmds.file(save=True, type="mayaAscii", force=True)


def _create_validation_scene(cmds):
    cmds.file(new=True, force=True)
    cmds.file(
        str(REFERENCE_SCENE_PATH),
        reference=True,
        namespace="refProtected",
    )

    cmds.polyCube(name="InstancedMesh_A")
    cmds.duplicate("InstancedMesh_A", instanceLeaf=True, name="InstancedMesh_A_Copy")

    cmds.select(clear=True)
    cmds.joint(name="SensitiveJoint_A", position=(0, 0, 0))
    cmds.polyCube(name="JointChildMesh_A")
    cmds.parent("JointChildMesh_A", "SensitiveJoint_A")

    cmds.select(clear=True)
    skin_joint = cmds.joint(name="SkinJoint_A", position=(3, 0, 0))
    cmds.polyCube(name="SkinClusterMesh_A")
    cmds.skinCluster(skin_joint, "SkinClusterMesh_A", toSelectedBones=True)

    cmds.polyCube(name="BlendShapeMesh_A")
    cmds.polyCube(name="BlendShapeTarget_A")
    cmds.blendShape("BlendShapeTarget_A", "BlendShapeMesh_A", name="BlendShapeNode_A")


def _protected_checks(config, decisions):
    reference = decisions["reference"]
    instance_source = decisions["instance_source"]
    instance_copy = decisions["instance_copy"]
    joint_child = decisions["joint_child"]
    skin_cluster = decisions["skin_cluster"]
    blend_shape = decisions["blend_shape"]

    return {
        "reference_preserved": (
            reference["source_flags"]["is_referenced"] is True
            and reference["route"] == config.ROUTE_REFERENCES
            and reference["can_move"] is False
            and reference["report_only"] is True
            and reference["operation_status"] == config.STATUS_SKIPPED_REFERENCE
        ),
        "instances_preserved": all((
            instance_source["source_flags"]["is_instanced"] is True,
            instance_copy["source_flags"]["is_instanced"] is True,
            instance_source["can_move"] is False,
            instance_copy["can_move"] is False,
            instance_source["operation_status"] == config.STATUS_SKIPPED_INSTANCE,
            instance_copy["operation_status"] == config.STATUS_SKIPPED_INSTANCE,
        )),
        "joint_child_preserved": (
            joint_child["source_flags"]["parent_is_joint"] is True
            and joint_child["source_flags"]["is_under_sensitive_hierarchy"] is True
            and joint_child["can_move"] is False
            and joint_child["operation_status"] == config.STATUS_SKIPPED_SENSITIVE_HIERARCHY
        ),
        "skin_cluster_preserved": (
            skin_cluster["source_flags"]["has_skin_cluster"] is True
            and skin_cluster["can_move"] is False
            and skin_cluster["operation_status"] == config.STATUS_SKIPPED_SENSITIVE_HIERARCHY
        ),
        "blend_shape_preserved": (
            blend_shape["source_flags"]["has_blendshape"] is True
            and blend_shape["can_move"] is False
            and blend_shape["operation_status"] == config.STATUS_SKIPPED_SENSITIVE_HIERARCHY
        ),
    }


def _report_contains_preserved_targets(report_path):
    if not report_path or not os.path.exists(report_path):
        return False
    with open(report_path, encoding="utf-8") as handle:
        payload = json.load(handle)
    decisions = payload.get("route_decisions") or []
    by_name = {decision.get("object_name"): decision for decision in decisions}
    expected = {
        "refProtected:RefMesh_A": "skipped_reference",
        "InstancedMesh_A": "skipped_instance",
        "InstancedMesh_A_Copy": "skipped_instance",
        "JointChildMesh_A": "skipped_sensitive_hierarchy",
        "SkinClusterMesh_A": "skipped_sensitive_hierarchy",
        "BlendShapeMesh_A": "skipped_sensitive_hierarchy",
    }
    for name, status in expected.items():
        decision = by_name.get(name)
        if not decision:
            return False
        if decision.get("operation_status") != status:
            return False
        if decision.get("can_move") is not False:
            return False
        if decision.get("report_only") is not True:
            return False
    return True


def main():
    maya.standalone.initialize(name="python")

    import maya.cmds as cmds
    from maya_production_pipeliner import config, pipeline

    _create_reference_asset(cmds)
    _create_validation_scene(cmds)

    assemblies_before = cmds.ls(assemblies=True, long=True) or []

    dry_run_result = pipeline.run(config.ALL_SCENE, config.DRY_RUN)
    apply_result = pipeline.run(config.ALL_SCENE, config.APPLY)

    assemblies_after = cmds.ls(assemblies=True, long=True) or []

    dry_decisions = dry_run_result.get("route_decisions") or []
    apply_decisions = apply_result.get("route_decisions") or []

    dry_targets = {
        "reference": _compact_decision(_decision_by_name(dry_decisions, "refProtected:RefMesh_A")),
        "instance_source": _compact_decision(_decision_by_name(dry_decisions, "InstancedMesh_A")),
        "instance_copy": _compact_decision(_decision_by_name(dry_decisions, "InstancedMesh_A_Copy")),
        "joint_child": _compact_decision(_decision_by_name(dry_decisions, "JointChildMesh_A")),
        "skin_cluster": _compact_decision(_decision_by_name(dry_decisions, "SkinClusterMesh_A")),
        "blend_shape": _compact_decision(_decision_by_name(dry_decisions, "BlendShapeMesh_A")),
    }
    apply_targets = {
        "reference": _compact_decision(_decision_by_name(apply_decisions, "refProtected:RefMesh_A")),
        "instance_source": _compact_decision(_decision_by_name(apply_decisions, "InstancedMesh_A")),
        "instance_copy": _compact_decision(_decision_by_name(apply_decisions, "InstancedMesh_A_Copy")),
        "joint_child": _compact_decision(_decision_by_name(apply_decisions, "JointChildMesh_A")),
        "skin_cluster": _compact_decision(_decision_by_name(apply_decisions, "SkinClusterMesh_A")),
        "blend_shape": _compact_decision(_decision_by_name(apply_decisions, "BlendShapeMesh_A")),
    }

    dry_checks = _protected_checks(config, dry_targets)
    apply_checks = _protected_checks(config, apply_targets)

    result = {
        "reference_scene_path": str(REFERENCE_SCENE_PATH),
        "dry_run": {
            "success": dry_run_result.get("success"),
            "message": dry_run_result.get("message"),
            "route_decisions_count": dry_run_result.get("route_decisions_count"),
            "targets": dry_targets,
        },
        "apply_preflight": {
            "success": apply_result.get("success"),
            "message": apply_result.get("message"),
            "route_decisions_count": apply_result.get("route_decisions_count"),
            "targets": apply_targets,
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
            "apply_json_contains_preserved_targets": _report_contains_preserved_targets(
                (apply_result.get("report_paths") or {}).get("json")
            ),
        },
        "checks": {
            "dry_run": dry_checks,
            "apply_preflight": apply_checks,
            "apply_kept_protected_content_unmoved": all(
                item.get("did_move") is False and item.get("new_long_name") is None
                for item in apply_targets.values()
            ),
            "apply_preflight_blocked_protected_content": all(
                (item.get("apply_preflight") or {}).get("eligible") is False
                for item in apply_targets.values()
            ),
            "outliner_unchanged": assemblies_before == assemblies_after,
            "no_pipeline_group_created": cmds.objExists(config.ROOT_GROUP) is False,
            "apply_json_report_documents_preserved_targets": _report_contains_preserved_targets(
                (apply_result.get("report_paths") or {}).get("json")
            ),
        },
    }

    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(RESULT_PATH)


if __name__ == "__main__":
    main()
