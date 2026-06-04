import json
import os
import sys
from pathlib import Path

import maya.standalone


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ARTIFACT_DIR = Path("C:/tmp/maya_test08_validation")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = ARTIFACT_DIR / "test08_result.json"


def _decision_by_name(route_decisions, name):
    for decision in route_decisions or []:
        if decision.get("object_name") == name:
            return decision
    return None


def _compact_decision(decision):
    if not decision:
        return None
    return {
        "object_name": decision.get("object_name"),
        "route": decision.get("route"),
        "target_group": decision.get("target_group"),
        "can_move": decision.get("can_move"),
        "operation": decision.get("operation"),
        "operation_status": decision.get("operation_status"),
        "report_only": decision.get("report_only"),
        "preserve_reason": decision.get("preserve_reason"),
        "reason": decision.get("reason"),
        "did_move": decision.get("did_move"),
        "new_long_name": decision.get("new_long_name"),
        "apply_preflight": decision.get("apply_preflight"),
        "matches_ignore_string": ((decision.get("source_record") or {}).get("matches_ignore_string")),
    }


def _report_contains_bypass(report_path, expected_names):
    if not report_path or not os.path.exists(report_path):
        return False
    with open(report_path, encoding="utf-8") as handle:
        payload = json.load(handle)
    decisions = payload.get("route_decisions") or []
    by_name = {item.get("object_name"): item for item in decisions}
    for name in expected_names:
        item = by_name.get(name)
        if not item:
            return False
        if item.get("route") != "Bypass":
            return False
        if item.get("preserve_reason") != "user ignore string":
            return False
    return True


def _create_scene(cmds):
    cmds.file(new=True, force=True)
    bypass_names = []
    normal_names = []

    for index in range(2):
        name = "ProdMesh_BYPASS_{0}".format(index)
        cmds.polyCube(name=name)
        bypass_names.append(name)

    cmds.polyCube(name="ProdMesh_Normal_A")
    normal_names.append("ProdMesh_Normal_A")

    for index in range(26):
        name = "HighMatch_BYPASS_{0:02d}".format(index)
        cmds.polyCube(name=name)
        bypass_names.append(name)

    return bypass_names, normal_names


def _warning_codes(run_result):
    return [event.get("code") for event in (run_result.get("warning_events") or [])]


def main():
    maya.standalone.initialize(name="python")

    import maya.cmds as cmds
    from maya_production_pipeliner import config, pipeline

    bypass_names, normal_names = _create_scene(cmds)
    focus_bypass_names = bypass_names[:2]

    dry_run = pipeline.run(config.ALL_SCENE, config.DRY_RUN, ignore_string="BYPASS")
    apply_preflight = pipeline.run(config.ALL_SCENE, config.APPLY, ignore_string="BYPASS")
    apply_report_contains_bypass = _report_contains_bypass(
        (apply_preflight.get("report_paths") or {}).get("json"),
        focus_bypass_names,
    )
    empty_ignore = pipeline.run(config.ALL_SCENE, config.DRY_RUN, ignore_string="")

    dry_decisions = dry_run.get("route_decisions") or []
    apply_decisions = apply_preflight.get("route_decisions") or []
    empty_decisions = empty_ignore.get("route_decisions") or []

    dry_targets = {
        name: _compact_decision(_decision_by_name(dry_decisions, name))
        for name in focus_bypass_names + normal_names
    }
    apply_targets = {
        name: _compact_decision(_decision_by_name(apply_decisions, name))
        for name in focus_bypass_names + normal_names
    }
    empty_targets = {
        name: _compact_decision(_decision_by_name(empty_decisions, name))
        for name in focus_bypass_names + normal_names
    }

    result = {
        "dry_run": {
            "success": dry_run.get("success"),
            "message": dry_run.get("message"),
            "warning_codes": _warning_codes(dry_run),
            "warnings": dry_run.get("warnings"),
            "targets": dry_targets,
            "report_paths": dry_run.get("report_paths"),
        },
        "apply_preflight": {
            "success": apply_preflight.get("success"),
            "message": apply_preflight.get("message"),
            "warning_codes": _warning_codes(apply_preflight),
            "warnings": apply_preflight.get("warnings"),
            "targets": apply_targets,
            "report_paths": apply_preflight.get("report_paths"),
        },
        "empty_ignore": {
            "success": empty_ignore.get("success"),
            "targets": empty_targets,
        },
        "checks": {
            "dry_run_bypass_preserved": all(
                dry_targets[name]["route"] == config.ROUTE_BYPASS
                and dry_targets[name]["can_move"] is False
                and dry_targets[name]["report_only"] is True
                and dry_targets[name]["operation_status"] == config.STATUS_PRESERVED_REPORT_ONLY
                and dry_targets[name]["preserve_reason"] == "user ignore string"
                and dry_targets[name]["matches_ignore_string"] is True
                for name in focus_bypass_names
            ),
            "apply_preflight_bypass_preserved": all(
                apply_targets[name]["route"] == config.ROUTE_BYPASS
                and apply_targets[name]["did_move"] is False
                and apply_targets[name]["new_long_name"] is None
                and (apply_targets[name]["apply_preflight"] or {}).get("eligible") is False
                for name in focus_bypass_names
            ),
            "normal_mesh_not_bypassed": (
                dry_targets["ProdMesh_Normal_A"]["route"] != config.ROUTE_BYPASS
                and dry_targets["ProdMesh_Normal_A"]["matches_ignore_string"] is False
            ),
            "empty_ignore_disables_bypass": all(
                empty_targets[name]["route"] != config.ROUTE_BYPASS
                and empty_targets[name]["matches_ignore_string"] is False
                for name in focus_bypass_names
            ),
            "warning_threshold_triggered": config.WARNING_IGNORE_MATCH_HIGH in _warning_codes(dry_run),
            "report_documents_bypass": apply_report_contains_bypass,
        },
    }

    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(RESULT_PATH)


if __name__ == "__main__":
    main()
