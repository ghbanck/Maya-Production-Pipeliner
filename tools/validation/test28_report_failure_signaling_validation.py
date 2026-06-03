import json
import sys
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from maya_production_pipeliner import config, pipeline


ARTIFACT_DIR = Path("C:/tmp/maya_test28_validation")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = ARTIFACT_DIR / "test28_result.json"


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


def _run_with_report_paths(report_paths):
    with mock.patch.object(pipeline.scanner, "scan", return_value=OBJECT_RECORDS):
        with mock.patch.object(pipeline.classifier, "classify", return_value=ROUTE_DECISIONS):
            with mock.patch.object(
                pipeline.reporter,
                "write_reports",
                return_value=report_paths,
            ):
                return pipeline.run(config.ALL_SCENE, config.DRY_RUN)


def main():
    good_paths = {
        "txt": str(ARTIFACT_DIR / "maya_production_pipeliner_report.txt"),
        "json": str(ARTIFACT_DIR / "maya_production_pipeliner_report.json"),
    }
    failed_paths = {"txt": None, "json": None}

    success_result = _run_with_report_paths(good_paths)
    failed_result = _run_with_report_paths(failed_paths)

    failed_events = failed_result.get("warning_events") or []
    result = {
        "success_case": {
            "success": success_result.get("success"),
            "report_paths": success_result.get("report_paths"),
            "warnings": success_result.get("warnings"),
            "warning_events": success_result.get("warning_events"),
        },
        "failed_case": {
            "success": failed_result.get("success"),
            "message": failed_result.get("message"),
            "report_paths": failed_result.get("report_paths"),
            "warnings": failed_result.get("warnings"),
            "warning_events": failed_events,
        },
        "checks": {
            "success_case_has_no_report_failure_warning": config.WARNING_REPORT_WRITE_FAILED not in [
                event.get("code") for event in success_result.get("warning_events") or []
            ],
            "failed_case_preserves_success_semantics": failed_result.get("success") is True,
            "failed_case_preserves_empty_report_paths": failed_result.get("report_paths") == failed_paths,
            "failed_case_adds_warning_text": "Report write failed for: json, txt." in (
                failed_result.get("warnings") or []
            ),
            "failed_case_adds_warning_event": any(
                event.get("code") == config.WARNING_REPORT_WRITE_FAILED
                and event.get("source") == "pipeline"
                and event.get("message") == "Report write failed for: json, txt."
                for event in failed_events
            ),
        },
    }

    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(RESULT_PATH)


if __name__ == "__main__":
    main()
