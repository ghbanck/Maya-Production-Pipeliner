import json
import os
import sys
from pathlib import Path

import maya.standalone


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ARTIFACT_DIR = Path("C:/tmp/maya_test20_validation")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = ARTIFACT_DIR / "test20_result.json"


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
        "report_only": decision.get("report_only"),
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
    safe_unclear = cmds.group(empty=True, name="AmbiguousGroup_A")

    cmds.select(clear=True)
    unsafe_joint = cmds.joint(name="AmbiguousJoint_A", position=(0, 0, 0))
    unsafe_unclear = cmds.group(empty=True, name="AmbiguousChildGroup_A")
    unsafe_unclear = cmds.parent(unsafe_unclear, unsafe_joint)[0]

    return {
        "safe_unclear": "AmbiguousGroup_A",
        "unsafe_unclear": "AmbiguousChildGroup_A",
    }


def _load_json_report(report_path):
    if not report_path or not os.path.exists(report_path):
        return {}
    with open(report_path, encoding="utf-8") as handle:
        return json.load(handle)


def _txt_contains_terms(report_path, object_name, expected_terms):
    if not report_path or not os.path.exists(report_path):
        return False
    text = Path(report_path).read_text(encoding="utf-8")
    if object_name not in text:
        return False
    return all(term in text for term in expected_terms)


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

    dry_txt_path = (dry_run_result.get("report_paths") or {}).get("txt")
    dry_json_path = (dry_run_result.get("report_paths") or {}).get("json")
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
            "dry_txt_safe_unclear_fidelity": _txt_contains_terms(
                dry_txt_path,
                names["safe_unclear"],
                [
                    "route={0}".format(config.ROUTE_REVIEW_UNCLEAR_CASES),
                    "reason=unclear object type",
                    "target={0}".format(config.REVIEW_UNCLEAR_CASES),
                    "can_move=True",
                ],
            ),
            "dry_txt_unsafe_unclear_fidelity": _txt_contains_terms(
                dry_txt_path,
                names["unsafe_unclear"],
                [
                    "status={0}".format(config.STATUS_SKIPPED_SENSITIVE_HIERARCHY),
                    "preserve_reason=rig/deformer sensitive content",
                ],
            ),
            "dry_json_safe_unclear_reason": (
                (_decision_by_name(dry_json_report.get("route_decisions") or [], names["safe_unclear"]) or {}).get("reason")
            ),
            "apply_json_unsafe_unclear_preserve_reason": (
                (_decision_by_name(apply_json_report.get("route_decisions") or [], names["unsafe_unclear"]) or {}).get("preserve_reason")
            ),
        },
        "checks": {
            "safe_unclear_receives_unclear_route": (
                dry_targets["safe_unclear"] is not None
                and dry_targets["safe_unclear"].get("route") == config.ROUTE_REVIEW_UNCLEAR_CASES
                and dry_targets["safe_unclear"].get("target_group") == config.REVIEW_UNCLEAR_CASES
            ),
            "safe_unclear_currently_movable_review": (
                dry_targets["safe_unclear"] is not None
                and dry_targets["safe_unclear"].get("can_move") is True
                and dry_targets["safe_unclear"].get("report_only") is False
                and dry_targets["safe_unclear"].get("operation_status") == config.STATUS_DRY_RUN_ONLY
                and dry_targets["safe_unclear"].get("target_group") == config.REVIEW_UNCLEAR_CASES
            ),
            "unsafe_unclear_preserved_as_sensitive": (
                dry_targets["unsafe_unclear"] is not None
                and dry_targets["unsafe_unclear"].get("can_move") is False
                and dry_targets["unsafe_unclear"].get("report_only") is True
                and dry_targets["unsafe_unclear"].get("operation_status") == config.STATUS_SKIPPED_SENSITIVE_HIERARCHY
                and dry_targets["unsafe_unclear"].get("source_record", {}).get("parent_is_joint") is True
            ),
            "apply_preflight_keeps_both_unmoved": all(
                target is not None
                and target.get("did_move") is False
                and target.get("new_long_name") is None
                for target in apply_targets.values()
            ) and (
                (apply_targets["safe_unclear"] or {}).get("apply_preflight", {}).get("eligible") is True
            ) and (
                (apply_targets["unsafe_unclear"] or {}).get("apply_preflight", {}).get("eligible") is False
            ),
            "report_fidelity_matches_unclear_contract": (
                _txt_contains_terms(
                    dry_txt_path,
                    names["safe_unclear"],
                    [
                        "route={0}".format(config.ROUTE_REVIEW_UNCLEAR_CASES),
                        "reason=unclear object type",
                        "target={0}".format(config.REVIEW_UNCLEAR_CASES),
                        "can_move=True",
                    ],
                )
                and _txt_contains_terms(
                    dry_txt_path,
                    names["unsafe_unclear"],
                    [
                        "status={0}".format(config.STATUS_SKIPPED_SENSITIVE_HIERARCHY),
                        "preserve_reason=rig/deformer sensitive content",
                    ],
                )
                and (
                    (_decision_by_name(dry_json_report.get("route_decisions") or [], names["safe_unclear"]) or {}).get("reason")
                    == "unclear object type"
                )
                and (
                    (_decision_by_name(apply_json_report.get("route_decisions") or [], names["safe_unclear"]) or {}).get("target_group")
                    == config.REVIEW_UNCLEAR_CASES
                )
                and (
                    (_decision_by_name(apply_json_report.get("route_decisions") or [], names["unsafe_unclear"]) or {}).get("preserve_reason")
                    == "rig/deformer sensitive content"
                )
            ),
        },
    }

    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(RESULT_PATH)


if __name__ == "__main__":
    main()
