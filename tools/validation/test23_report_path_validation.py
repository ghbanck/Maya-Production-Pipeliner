import json
import os
import sys
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from maya_production_pipeliner import config, reporter


ARTIFACT_DIR = Path("C:/tmp/maya_test23_validation")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = ARTIFACT_DIR / "test23_result.json"


SAMPLE_RUN_RESULT = {
    "execution_mode": config.DRY_RUN,
    "scope_mode": config.ALL_SCENE,
    "ignore_string": "",
    "success": True,
    "message": "Dry Run completed without scene changes.",
    "summary": {
        "scanned": 1,
        "planned": 1,
        "would_move": 1,
        "moved": 0,
        "already_in_target": 0,
        "preserved": 0,
        "warnings": 0,
        "failed": 0,
    },
    "warnings": [],
    "warning_events": [],
    "report_paths": {"txt": None, "json": None},
    "route_decisions_count": 1,
    "preview_routes": [],
    "max_ui_preview_items": config.MAX_UI_PREVIEW_ITEMS,
}

SAMPLE_ROUTE_DECISIONS = [{
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


def write_case(name, fn):
    return {"case": name, **fn()}


def case_saved_scene_directory():
    target_dir = ARTIFACT_DIR / "saved_scene_dir"
    target_dir.mkdir(parents=True, exist_ok=True)
    scene_path = target_dir / "sample_scene.ma"
    scene_path.write_text("// maya ascii stub", encoding="utf-8")

    with mock.patch.object(reporter, "cmds") as fake_cmds:
        fake_cmds.file.return_value = str(scene_path)
        fake_cmds.workspace.return_value = str(ARTIFACT_DIR / "workspace_dir")
        paths = reporter.write_reports(dict(SAMPLE_RUN_RESULT), list(SAMPLE_ROUTE_DECISIONS))

    return {
        "expected_dir": str(target_dir),
        "report_paths": paths,
        "uses_saved_scene_dir": all(str(path).startswith(str(target_dir)) for path in paths.values()),
    }


def case_workspace_fallback():
    workspace_dir = ARTIFACT_DIR / "workspace_dir"
    workspace_dir.mkdir(parents=True, exist_ok=True)

    with mock.patch.object(reporter, "cmds") as fake_cmds:
        fake_cmds.file.return_value = ""
        fake_cmds.workspace.return_value = str(workspace_dir)
        paths = reporter.write_reports(dict(SAMPLE_RUN_RESULT), list(SAMPLE_ROUTE_DECISIONS))

    return {
        "expected_dir": str(workspace_dir),
        "report_paths": paths,
        "uses_workspace_dir": all(str(path).startswith(str(workspace_dir)) for path in paths.values()),
    }


def case_temp_fallback():
    with mock.patch.object(reporter, "cmds") as fake_cmds:
        fake_cmds.file.return_value = ""
        fake_cmds.workspace.return_value = ""
        paths = reporter.write_reports(dict(SAMPLE_RUN_RESULT), list(SAMPLE_ROUTE_DECISIONS))

    temp_dir = reporter.tempfile.gettempdir()
    return {
        "expected_dir": temp_dir,
        "report_paths": paths,
        "uses_temp_dir": all(str(path).startswith(temp_dir) for path in paths.values()),
    }


def case_unwritable_primary_dir():
    scene_dir = ARTIFACT_DIR / "blocked_scene_dir"
    scene_dir.mkdir(parents=True, exist_ok=True)
    scene_path = scene_dir / "sample_scene.ma"
    scene_path.write_text("// maya ascii stub", encoding="utf-8")
    workspace_dir = ARTIFACT_DIR / "workspace_fallback_after_block"
    workspace_dir.mkdir(parents=True, exist_ok=True)

    original_write = reporter._write_file

    def fake_write(directory, filename, content, mode="w"):
        if os.path.normcase(directory) == os.path.normcase(str(scene_dir)):
            return None
        return original_write(directory, filename, content, mode)

    with mock.patch.object(reporter, "cmds") as fake_cmds:
        fake_cmds.file.return_value = str(scene_path)
        fake_cmds.workspace.return_value = str(workspace_dir)
        with mock.patch.object(reporter, "_write_file", side_effect=fake_write):
            paths = reporter.write_reports(dict(SAMPLE_RUN_RESULT), list(SAMPLE_ROUTE_DECISIONS))

    return {
        "primary_dir": str(scene_dir),
        "workspace_dir": str(workspace_dir),
        "report_paths": paths,
        "uses_workspace_fallback": all(str(path).startswith(str(workspace_dir)) for path in paths.values()),
    }


def main():
    results = [
        write_case("saved_scene", case_saved_scene_directory),
        write_case("workspace_fallback", case_workspace_fallback),
        write_case("temp_fallback", case_temp_fallback),
        write_case("unwritable_primary_dir", case_unwritable_primary_dir),
    ]
    RESULT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(RESULT_PATH)


if __name__ == "__main__":
    main()
