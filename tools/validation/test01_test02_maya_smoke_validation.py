import json
import os
import sys
from pathlib import Path

import maya.standalone


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ARTIFACT_DIR = Path("C:/tmp/maya_test01_test02_validation")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = ARTIFACT_DIR / "test01_test02_result.json"


def _safe_exists(path_value):
    return bool(path_value) and os.path.exists(path_value)


def main():
    maya.standalone.initialize(name="python")

    import maya.cmds as cmds
    from maya_production_pipeliner import launcher, pipeline
    from maya_production_pipeliner import config as repo_config

    cmds.file(new=True, force=True)

    assemblies_before = cmds.ls(assemblies=True, long=True) or []
    pipeline_group_before = cmds.objExists(repo_config.ROOT_GROUP)

    package_import_ok = "maya_production_pipeliner" in sys.modules
    launcher_import_ok = "maya_production_pipeliner.launcher" in sys.modules
    pipeline_import_ok = "maya_production_pipeliner.pipeline" in sys.modules

    all_scene_result = pipeline.run(repo_config.ALL_SCENE, repo_config.DRY_RUN)
    cmds.select(clear=True)
    selected_result = pipeline.run(repo_config.SELECTED, repo_config.DRY_RUN)
    visible_result = pipeline.run(repo_config.VISIBLE, repo_config.DRY_RUN)

    assemblies_after = cmds.ls(assemblies=True, long=True) or []
    pipeline_group_after = cmds.objExists(repo_config.ROOT_GROUP)

    result = {
        "import_smoke": {
            "package_import_ok": package_import_ok,
            "launcher_import_ok": launcher_import_ok,
            "pipeline_import_ok": pipeline_import_ok,
            "launcher_launch_callable": callable(getattr(launcher, "launch", None)),
            "pipeline_run_callable": callable(getattr(pipeline, "run", None)),
            "pipeline_run_pipeline_callable": callable(getattr(pipeline, "run_pipeline", None)),
            "pipeline_group_before_import": pipeline_group_before,
            "pipeline_group_after_runs": pipeline_group_after,
            "assemblies_before": assemblies_before,
            "assemblies_after": assemblies_after,
        },
        "empty_scene_behavior": {
            "all_scene": {
                "success": all_scene_result.get("success"),
                "message": all_scene_result.get("message"),
                "route_decisions_count": all_scene_result.get("route_decisions_count"),
                "summary": all_scene_result.get("summary"),
                "report_paths": all_scene_result.get("report_paths"),
                "report_paths_exist": {
                    "txt": _safe_exists((all_scene_result.get("report_paths") or {}).get("txt")),
                    "json": _safe_exists((all_scene_result.get("report_paths") or {}).get("json")),
                },
            },
            "selected": {
                "success": selected_result.get("success"),
                "message": selected_result.get("message"),
                "route_decisions_count": selected_result.get("route_decisions_count"),
                "summary": selected_result.get("summary"),
                "report_paths": selected_result.get("report_paths"),
                "report_paths_exist": {
                    "txt": _safe_exists((selected_result.get("report_paths") or {}).get("txt")),
                    "json": _safe_exists((selected_result.get("report_paths") or {}).get("json")),
                },
            },
            "visible": {
                "success": visible_result.get("success"),
                "message": visible_result.get("message"),
                "route_decisions_count": visible_result.get("route_decisions_count"),
                "summary": visible_result.get("summary"),
                "report_paths": visible_result.get("report_paths"),
                "report_paths_exist": {
                    "txt": _safe_exists((visible_result.get("report_paths") or {}).get("txt")),
                    "json": _safe_exists((visible_result.get("report_paths") or {}).get("json")),
                },
            },
            "outliner_unchanged": assemblies_before == assemblies_after,
            "pipeline_group_created": pipeline_group_after,
        },
        "checks": {
            "imports_cleanly": package_import_ok and launcher_import_ok and pipeline_import_ok,
            "launcher_callable_exists": callable(getattr(launcher, "launch", None)),
            "pipeline_run_exists": callable(getattr(pipeline, "run", None)),
            "pipeline_run_pipeline_missing": not callable(getattr(pipeline, "run_pipeline", None)),
            "no_import_time_pipeline_group": pipeline_group_before is False,
            "no_dry_run_pipeline_group": pipeline_group_after is False,
            "outliner_unchanged_after_dry_runs": assemblies_before == assemblies_after,
        },
    }

    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(RESULT_PATH)


if __name__ == "__main__":
    main()
