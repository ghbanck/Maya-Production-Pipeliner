import ast
import inspect
import json
import sys
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from maya_production_pipeliner import config, pipeline, reporter, ui


ARTIFACT_DIR = Path("C:/tmp/maya_test25_validation")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = ARTIFACT_DIR / "test25_result.json"


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


def _run_pipeline(fake_report_paths):
    with mock.patch.object(pipeline.scanner, "scan", return_value=OBJECT_RECORDS):
        with mock.patch.object(pipeline.classifier, "classify", return_value=ROUTE_DECISIONS):
            with mock.patch.object(
                pipeline.reporter,
                "write_reports",
                return_value=fake_report_paths,
            ) as mocked_write_reports:
                run_result = pipeline.run(config.ALL_SCENE, config.DRY_RUN)
    return run_result, mocked_write_reports.call_count


def _extract_module_imports(module):
    tree = ast.parse(inspect.getsource(module))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            for alias in node.names:
                if module_name:
                    imports.append("{0}.{1}".format(module_name, alias.name))
                else:
                    imports.append(alias.name)
    return sorted(imports)


def main():
    good_report_paths = {
        "txt": str(ARTIFACT_DIR / "maya_production_pipeliner_report.txt"),
        "json": str(ARTIFACT_DIR / "maya_production_pipeliner_report.json"),
    }
    failed_report_paths = {"txt": None, "json": None}

    direct_run_result, direct_report_calls = _run_pipeline(good_report_paths)
    failed_run_result, failed_report_calls = _run_pipeline(failed_report_paths)

    ui_source = inspect.getsource(ui)
    reporter_source = inspect.getsource(reporter)
    ui_imports = _extract_module_imports(ui)
    reporter_imports = _extract_module_imports(reporter)

    result = {
        "pipeline_direct_run": {
            "success": direct_run_result.get("success"),
            "message": direct_run_result.get("message"),
            "report_paths": direct_run_result.get("report_paths"),
            "reporter_write_calls": direct_report_calls,
        },
        "pipeline_report_failure_surface": {
            "success": failed_run_result.get("success"),
            "message": failed_run_result.get("message"),
            "report_paths": failed_run_result.get("report_paths"),
            "warnings": failed_run_result.get("warnings"),
            "warning_events": failed_run_result.get("warning_events"),
            "reporter_write_calls": failed_report_calls,
        },
        "ui_contract": {
            "imports": ui_imports,
            "mentions_runresult_only": "Read only RunResult fields" in ui_source,
            "mentions_no_report_parsing": "Never parse TXT or JSON report files" in ui_source,
            "show_is_stub": "NotImplementedError" in inspect.getsource(ui.show),
            "on_run_clicked_is_stub": "NotImplementedError" in inspect.getsource(ui._on_run_clicked),
            "update_result_display_is_stub": "NotImplementedError" in inspect.getsource(ui._update_result_display),
        },
        "reporter_contract": {
            "imports": reporter_imports,
            "mentions_never_drive_ui": "must never drive the UI" in reporter_source,
            "imports_ui_module": any(name.endswith(".ui") or name == "ui" for name in reporter_imports),
        },
        "checks": {
            "pipeline_runs_without_ui": direct_run_result.get("success") is True
            and direct_report_calls == 1,
            "pipeline_propagates_report_paths": direct_run_result.get("report_paths") == good_report_paths,
            "ui_does_not_import_reporter": not any(name.endswith(".reporter") for name in ui_imports),
            "ui_does_not_import_scanner_classifier_organizer": not any(
                name.endswith(".scanner") or name.endswith(".classifier") or name.endswith(".organizer")
                for name in ui_imports
            ),
            "ui_contract_explicitly_forbids_report_parsing": "Never parse TXT or JSON report files" in ui_source,
            "reporter_does_not_import_ui": not any(name.endswith(".ui") or name == "ui" for name in reporter_imports),
            "report_write_failure_has_clear_runresult_warning": bool(failed_run_result.get("warnings"))
            or bool(failed_run_result.get("warning_events")),
        },
    }

    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(RESULT_PATH)


if __name__ == "__main__":
    main()
