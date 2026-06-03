import json
import sys
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from maya_production_pipeliner import config, mel_bridge, pipeline, reporter


ARTIFACT_DIR = Path("C:/tmp/maya_test26_validation")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = ARTIFACT_DIR / "test26_result.json"


OBJECT_RECORDS = [{
    "object_name": "Cube_A",
    "long_name": "|Cube_A",
    "matches_ignore_string": False,
    "warnings": [],
}]

ROUTE_DECISIONS = [{
    "object_name": "Cube_A",
    "long_name": "|Cube_A",
    "new_long_name": None,
    "route": config.ROUTE_PRODUCTION_MESHES,
    "target_group": config.PRODUCTION_MESHES,
    "reason": "production mesh candidate",
    "warnings": [],
    "execution_mode": config.DRY_RUN,
    "scope_mode": config.ALL_SCENE,
    "can_move": True,
    "operation": config.OPERATION_MOVE,
    "preserve_reason": "",
    "report_only": False,
    "would_move": True,
    "did_move": False,
    "operation_status": config.STATUS_DRY_RUN_ONLY,
}]


def _run_pipeline(pre_hook="", post_hook=""):
    fake_report_paths = {
        "txt": str(ARTIFACT_DIR / "maya_production_pipeliner_report.txt"),
        "json": str(ARTIFACT_DIR / "maya_production_pipeliner_report.json"),
    }
    with mock.patch.object(pipeline.scanner, "scan", return_value=OBJECT_RECORDS):
        with mock.patch.object(pipeline.classifier, "classify", return_value=ROUTE_DECISIONS):
            with mock.patch.object(
                pipeline.reporter,
                "write_reports",
                return_value=fake_report_paths,
            ):
                return pipeline.run(
                    config.ALL_SCENE,
                    config.DRY_RUN,
                    pre_hook=pre_hook,
                    post_hook=post_hook,
                )


def main():
    no_hook_pre = mel_bridge.run_pre_hook("")
    no_hook_post = mel_bridge.run_post_hook("")

    unavailable_pre = mel_bridge.run_pre_hook("missingPreHook")
    unavailable_post = mel_bridge.run_post_hook("missingPostHook")

    with mock.patch.object(mel_bridge, "maya_mel") as fake_mel:
        fake_mel.eval.return_value = None
        valid_pre = mel_bridge.run_pre_hook("preHookOk")
        valid_post = mel_bridge.run_post_hook("postHookOk")

    with mock.patch.object(mel_bridge, "maya_mel") as fake_mel:
        fake_mel.eval.side_effect = RuntimeError("Stub MEL hook failure")
        failing_pre = mel_bridge.run_pre_hook("preHookFail")
        failing_post = mel_bridge.run_post_hook("postHookFail")

    run_result_disabled = _run_pipeline()
    run_result_named_hooks = _run_pipeline(pre_hook="preHookConfigured", post_hook="postHookConfigured")

    json_payload = reporter._format_json_payload(run_result_named_hooks, ROUTE_DECISIONS)
    txt_payload = reporter._format_txt_report(run_result_named_hooks, ROUTE_DECISIONS)

    result = {
        "isolated_module": {
            "no_hook_pre": no_hook_pre,
            "no_hook_post": no_hook_post,
            "unavailable_pre": unavailable_pre,
            "unavailable_post": unavailable_post,
            "valid_pre": valid_pre,
            "valid_post": valid_post,
            "failing_pre": failing_pre,
            "failing_post": failing_post,
        },
        "pipeline_disabled_runtime": {
            "no_hook_run_result": run_result_disabled.get("mel_hook_status"),
            "named_hook_run_result": run_result_named_hooks.get("mel_hook_status"),
            "success": run_result_named_hooks.get("success"),
            "message": run_result_named_hooks.get("message"),
            "report_paths": run_result_named_hooks.get("report_paths"),
        },
        "report_surfaces": {
            "json_has_mel_hook_status": "mel_hook_status" in (json_payload.get("run_result") or {}),
            "json_mel_hook_status": (json_payload.get("run_result") or {}).get("mel_hook_status"),
            "txt_mentions_mel_hook_status": "mel_hook_status" in txt_payload,
            "txt_mentions_disabled_error": "MEL hooks are disabled in the initial Dry Run runtime." in txt_payload,
        },
        "checks": {
            "module_no_hook_is_neutral": no_hook_pre == {"called": False, "success": True, "error": None}
            and no_hook_post == {"called": False, "success": True, "error": None},
            "module_unavailable_runtime_is_captured": unavailable_pre["called"] is True
            and unavailable_pre["success"] is False
            and unavailable_post["called"] is True
            and unavailable_post["success"] is False,
            "module_valid_hooks_record_success": valid_pre == {"called": True, "success": True, "error": None}
            and valid_post == {"called": True, "success": True, "error": None},
            "module_failing_hooks_record_error": failing_pre["called"] is True
            and failing_pre["success"] is False
            and "Stub MEL hook failure" in (failing_pre["error"] or "")
            and failing_post["called"] is True
            and failing_post["success"] is False
            and "Stub MEL hook failure" in (failing_post["error"] or ""),
            "pipeline_without_hooks_runs_normally": run_result_disabled.get("success") is True
            and run_result_disabled.get("mel_hook_status", {}).get("errors") == [],
            "pipeline_with_named_hooks_keeps_execution_disabled": run_result_named_hooks.get("success") is True
            and run_result_named_hooks.get("mel_hook_status", {}).get("pre", {}).get("called") is False
            and run_result_named_hooks.get("mel_hook_status", {}).get("post", {}).get("called") is False,
            "pipeline_disabled_errors_are_explicit": run_result_named_hooks.get("mel_hook_status", {}).get("errors") == [
                "MEL hooks are disabled in the initial Dry Run runtime.",
                "MEL hooks are disabled in the initial Dry Run runtime.",
            ],
            "json_report_surface_includes_hook_status": "mel_hook_status" in (json_payload.get("run_result") or {}),
            "txt_report_surface_omits_hook_status": "mel_hook_status" not in txt_payload,
        },
    }

    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(RESULT_PATH)


if __name__ == "__main__":
    main()
