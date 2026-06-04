import json
import os
import sys
from pathlib import Path

import maya.standalone


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ARTIFACT_DIR = Path("C:/tmp/maya_test14_validation")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = ARTIFACT_DIR / "test14_result.json"


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
        "reason": decision.get("reason"),
        "preserve_reason": decision.get("preserve_reason"),
        "did_move": decision.get("did_move"),
        "new_long_name": decision.get("new_long_name"),
        "apply_preflight": decision.get("apply_preflight"),
        "source_record": {
            "node_type": record.get("node_type"),
            "shape_type": record.get("shape_type"),
            "shape_types": record.get("shape_types"),
            "is_mesh": record.get("is_mesh"),
            "parent_is_joint": record.get("parent_is_joint"),
            "is_under_sensitive_hierarchy": record.get("is_under_sensitive_hierarchy"),
        },
    }


def _create_validation_scene(cmds):
    cmds.file(new=True, force=True)

    camera_transform, _ = cmds.camera(name="SceneCamera_A1")
    locator_transform = cmds.spaceLocator(name="SceneLocator_A")[0]
    light_shape = cmds.directionalLight(name="SceneDirectionalLightShape_A")
    light_transform = cmds.listRelatives(light_shape, parent=True, fullPath=False)[0]
    light_transform = cmds.rename(light_transform, "SceneLight_A")

    cmds.select(clear=True)
    joint_name = cmds.joint(name="SceneJoint_A", position=(0, 0, 0))

    cmds.select(clear=True)
    cmds.polyCube(name="JointChildMesh_A")
    cmds.parent("JointChildMesh_A", joint_name)

    return {
        "camera": camera_transform,
        "locator": locator_transform,
        "light": light_transform,
        "joint": joint_name,
        "joint_child": "JointChildMesh_A",
    }


def _load_json_report(report_path):
    if not report_path or not os.path.exists(report_path):
        return {}
    with open(report_path, encoding="utf-8") as handle:
        return json.load(handle)


def _txt_contains_utility_route_details(report_path, object_name, route, target):
    if not report_path or not os.path.exists(report_path):
        return False
    text = Path(report_path).read_text(encoding="utf-8")
    return (
        object_name in text
        and "route={0}".format(route) in text
        and "target={0}".format(target) in text
    )


def main():
    maya.standalone.initialize(name="python")

    import maya.cmds as cmds
    from maya_production_pipeliner import config, pipeline

    names = _create_validation_scene(cmds)

    dry_run_result = pipeline.run(config.ALL_SCENE, config.DRY_RUN)
    apply_result = pipeline.run(config.ALL_SCENE, config.APPLY)

    dry_decisions = dry_run_result.get("route_decisions") or []
    apply_decisions = apply_result.get("route_decisions") or []

    dry_targets = {
        key: _compact_decision(_decision_by_name(dry_decisions, object_name))
        for key, object_name in names.items()
    }
    apply_targets = {
        key: _compact_decision(_decision_by_name(apply_decisions, object_name))
        for key, object_name in names.items()
    }

    dry_json_path = (dry_run_result.get("report_paths") or {}).get("json")
    dry_txt_path = (dry_run_result.get("report_paths") or {}).get("txt")
    apply_json_path = (apply_result.get("report_paths") or {}).get("json")
    dry_json_report = _load_json_report(dry_json_path)
    apply_json_report = _load_json_report(apply_json_path)

    result = {
        "dry_run": {
            "success": dry_run_result.get("success"),
            "message": dry_run_result.get("message"),
            "summary": dry_run_result.get("summary"),
            "route_decisions_count": dry_run_result.get("route_decisions_count"),
            "targets": dry_targets,
        },
        "apply_preflight": {
            "success": apply_result.get("success"),
            "message": apply_result.get("message"),
            "summary": apply_result.get("summary"),
            "route_decisions_count": apply_result.get("route_decisions_count"),
            "targets": apply_targets,
        },
        "reports": {
            "dry_run_report_paths": dry_run_result.get("report_paths"),
            "apply_report_paths": apply_result.get("report_paths"),
            "dry_txt_camera_route_details": _txt_contains_utility_route_details(
                dry_txt_path,
                names["camera"],
                config.ROUTE_SCENE_UTILITIES,
                config.SCENE_UTILITIES,
            ),
            "dry_json_camera_source_record_shape_type": (
                (
                    _decision_by_name(
                        dry_json_report.get("route_decisions") or [],
                        names["camera"],
                    )
                    or {}
                ).get("source_record", {}).get("shape_type")
            ),
            "dry_json_locator_source_record_shape_type": (
                (
                    _decision_by_name(
                        dry_json_report.get("route_decisions") or [],
                        names["locator"],
                    )
                    or {}
                ).get("source_record", {}).get("shape_type")
            ),
            "apply_json_joint_child_preserve_reason": (
                (
                    _decision_by_name(
                        apply_json_report.get("route_decisions") or [],
                        names["joint_child"],
                    )
                    or {}
                ).get("preserve_reason")
            ),
        },
        "checks": {
            "utility_objects_route_scene_utilities": all(
                (dry_targets[key] or {}).get("route") == config.ROUTE_SCENE_UTILITIES
                and (dry_targets[key] or {}).get("target_group") == config.SCENE_UTILITIES
                and (dry_targets[key] or {}).get("can_move") is True
                for key in ("camera", "locator", "light")
            ),
            "joint_behavior_recorded_honestly": (
                dry_targets["joint"] is not None
                and apply_targets["joint"] is not None
                and dry_targets["joint"].get("route") == config.ROUTE_SCENE_UTILITIES
                and dry_targets["joint"].get("source_record", {}).get("node_type") == "joint"
                and apply_targets["joint"].get("operation_status") == "planned"
            ),
            "joint_child_remains_sensitive_not_utility": (
                dry_targets["joint_child"] is not None
                and dry_targets["joint_child"].get("route") == config.ROUTE_REVIEW_UNCLEAR_CASES
                and dry_targets["joint_child"].get("can_move") is False
                and dry_targets["joint_child"].get("operation_status") == config.STATUS_SKIPPED_SENSITIVE_HIERARCHY
                and dry_targets["joint_child"].get("source_record", {}).get("parent_is_joint") is True
            ),
            "apply_preflight_only_safe_utilities_move": all(
                (apply_targets[key] or {}).get("apply_preflight", {}).get("eligible") is True
                and (apply_targets[key] or {}).get("operation_status") == "planned"
                for key in ("camera", "locator", "light", "joint")
            ) and (
                (apply_targets["joint_child"] or {}).get("apply_preflight", {}).get("eligible") is False
            ),
            "report_fidelity_matches_runtime_contract": (
                _txt_contains_utility_route_details(
                    dry_txt_path,
                    names["camera"],
                    config.ROUTE_SCENE_UTILITIES,
                    config.SCENE_UTILITIES,
                )
                and (
                    (
                        _decision_by_name(
                            dry_json_report.get("route_decisions") or [],
                            names["camera"],
                        )
                        or {}
                    ).get("source_record", {}).get("shape_type")
                    == "camera"
                )
                and (
                    (
                        _decision_by_name(
                            dry_json_report.get("route_decisions") or [],
                            names["locator"],
                        )
                        or {}
                    ).get("source_record", {}).get("shape_type")
                    == "locator"
                )
                and (
                    (
                        _decision_by_name(
                            apply_json_report.get("route_decisions") or [],
                            names["joint_child"],
                        )
                        or {}
                    ).get("preserve_reason")
                    == "rig/deformer sensitive content"
                )
            ),
        },
    }

    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(RESULT_PATH)


if __name__ == "__main__":
    main()
