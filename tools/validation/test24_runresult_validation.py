import json
import sys
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from maya_production_pipeliner import config, pipeline


ARTIFACT_DIR = Path("C:/tmp/maya_test24_validation")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = ARTIFACT_DIR / "test24_result.json"


def _object_record(index, ignore_match=False, warning_text=""):
    warnings = [warning_text] if warning_text else []
    return {
        "object_name": "Object_{0:02d}".format(index),
        "long_name": "|Object_{0:02d}".format(index),
        "matches_ignore_string": ignore_match,
        "warnings": warnings,
    }


def _route_decision(index, warning_text=""):
    warnings = [warning_text] if warning_text else []
    return {
        "object_name": "Object_{0:02d}".format(index),
        "long_name": "|Object_{0:02d}".format(index),
        "new_long_name": None,
        "route": config.ROUTE_PRODUCTION_MESHES,
        "target_group": config.PRODUCTION_MESHES,
        "reason": "production mesh candidate",
        "warnings": warnings,
        "execution_mode": config.DRY_RUN,
        "scope_mode": config.ALL_SCENE,
        "can_move": True,
        "operation": config.OPERATION_MOVE,
        "preserve_reason": "",
        "report_only": False,
        "would_move": True,
        "did_move": False,
        "operation_status": config.STATUS_DRY_RUN_ONLY,
    }


def main():
    object_records = []
    route_decisions = []

    for index in range(30):
        object_records.append(
            _object_record(
                index,
                ignore_match=index < 26,
                warning_text="scanner warning {0}".format(index) if index < 2 else "",
            )
        )
        route_decisions.append(
            _route_decision(
                index,
                warning_text="classifier warning {0}".format(index) if index < 3 else "",
            )
        )

    fake_report_paths = {
        "txt": str(ARTIFACT_DIR / "maya_production_pipeliner_report.txt"),
        "json": str(ARTIFACT_DIR / "maya_production_pipeliner_report.json"),
    }

    with mock.patch.object(pipeline.scanner, "scan", return_value=object_records):
        with mock.patch.object(pipeline.classifier, "classify", return_value=route_decisions):
            with mock.patch.object(
                pipeline.reporter,
                "write_reports",
                return_value=fake_report_paths,
            ):
                run_result = pipeline.run(config.ALL_SCENE, config.DRY_RUN, ignore_string="BYPASS")

    result = {
        "validation": {
            "execution_mode": run_result.get("execution_mode"),
            "scope_mode": run_result.get("scope_mode"),
            "success": run_result.get("success"),
            "message": run_result.get("message"),
            "route_decisions_count": run_result.get("route_decisions_count"),
            "preview_route_count": len(run_result.get("preview_routes") or []),
            "max_ui_preview_items": run_result.get("max_ui_preview_items"),
            "preview_is_capped": len(run_result.get("preview_routes") or []) <= run_result.get("max_ui_preview_items"),
            "preview_matches_expected_cap": len(run_result.get("preview_routes") or []) == config.MAX_UI_PREVIEW_ITEMS,
            "first_preview_object": (run_result.get("preview_routes") or [{}])[0].get("object_name"),
            "last_preview_object": (run_result.get("preview_routes") or [{}])[-1].get("object_name"),
            "summary": run_result.get("summary"),
            "warnings_count": len(run_result.get("warnings") or []),
            "warning_events_count": len(run_result.get("warning_events") or []),
            "warning_codes": [event.get("code") for event in run_result.get("warning_events") or []],
            "report_paths": run_result.get("report_paths"),
        },
        "checks": {
            "route_decisions_count_matches": run_result.get("route_decisions_count") == len(route_decisions),
            "preview_routes_capped": len(run_result.get("preview_routes") or []) == config.MAX_UI_PREVIEW_ITEMS,
            "summary_fields_present": sorted((run_result.get("summary") or {}).keys()),
            "summary_scanned_matches_records": (run_result.get("summary") or {}).get("scanned") == len(object_records),
            "summary_total_matches_routes": (run_result.get("summary") or {}).get("total") == len(route_decisions),
            "summary_warning_count_matches_visible_warnings": (
                (run_result.get("summary") or {}).get("warnings") == len(run_result.get("warnings") or [])
            ),
            "summary_warning_count_matches_warning_events": (
                (run_result.get("summary") or {}).get("warnings") == len(run_result.get("warning_events") or [])
            ),
            "warning_threshold_triggered": config.WARNING_IGNORE_MATCH_HIGH in [
                event.get("code") for event in run_result.get("warning_events") or []
            ],
            "report_paths_propagated": run_result.get("report_paths") == fake_report_paths,
            "message_matches_dry_run": run_result.get("message") == "Dry Run completed without scene changes.",
            "success_true": run_result.get("success") is True,
        },
    }

    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(RESULT_PATH)


if __name__ == "__main__":
    main()
