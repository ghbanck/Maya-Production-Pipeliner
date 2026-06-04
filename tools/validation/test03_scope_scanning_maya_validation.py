import json
import os
import sys
from pathlib import Path

import maya.standalone


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ARTIFACT_DIR = Path("C:/tmp/maya_test03_validation")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH = ARTIFACT_DIR / "test03_result.json"
REFERENCE_SCENE_PATH = ARTIFACT_DIR / "scope_reference_asset.ma"


def _records_by_name(records):
    return {record.get("name"): record for record in records}


def _record_summary(record):
    if not record:
        return None
    return {
        "name": record.get("name"),
        "long_name": record.get("long_name"),
        "node_type": record.get("node_type"),
        "shape_type": record.get("shape_type"),
        "shape_types": record.get("shape_types"),
        "is_mesh": record.get("is_mesh"),
        "is_selected": record.get("is_selected"),
        "is_referenced": record.get("is_referenced"),
        "is_instanced": record.get("is_instanced"),
    }


def _create_reference_asset(cmds):
    cmds.file(new=True, force=True)
    cmds.polyCube(name="ScopeRefMesh_A")
    cmds.file(rename=str(REFERENCE_SCENE_PATH))
    cmds.file(save=True, type="mayaAscii", force=True)


def _create_validation_scene(cmds):
    cmds.file(new=True, force=True)
    cmds.polyCube(name="ScopeMesh_A")
    cmds.spaceLocator(name="ScopeLocator_A")
    camera_transform, _camera_shape = cmds.camera(name="ScopeCamera_A")
    cmds.directionalLight(name="ScopeLight_A")

    cmds.polyCube(name="ScopeInstancedMesh_A")
    cmds.duplicate("ScopeInstancedMesh_A", instanceLeaf=True, name="ScopeInstancedMesh_A_Copy")

    cmds.group(empty=True, name="ScopeParent_A")
    cmds.polyCube(name="ScopeChildMesh_A")
    cmds.parent("ScopeChildMesh_A", "ScopeParent_A")

    cmds.file(
        str(REFERENCE_SCENE_PATH),
        reference=True,
        namespace="scopeRef",
    )
    return {
        "camera_transform": camera_transform,
    }


def _scan_selected(cmds, scanner, config, selection):
    cmds.select(clear=True)
    cmds.select(selection, replace=True)
    records = scanner.scan(config.SELECTED)
    return records


def main():
    maya.standalone.initialize(name="python")

    import maya.cmds as cmds
    from maya_production_pipeliner import config, pipeline, scanner

    _create_reference_asset(cmds)
    scene_nodes = _create_validation_scene(cmds)

    all_records = scanner.scan(config.ALL_SCENE)
    all_by_name = _records_by_name(all_records)

    selected_records = _scan_selected(
        cmds,
        scanner,
        config,
        ["ScopeMesh_A", "ScopeLocator_A"],
    )
    selected_by_name = _records_by_name(selected_records)

    shape_node = cmds.listRelatives(
        "ScopeMesh_A",
        shapes=True,
        fullPath=True,
        noIntermediate=True,
    )[0]
    shape_selected_records = _scan_selected(cmds, scanner, config, [shape_node])
    shape_selected_by_name = _records_by_name(shape_selected_records)

    child_selected_records = _scan_selected(cmds, scanner, config, ["ScopeChildMesh_A"])
    child_selected_by_name = _records_by_name(child_selected_records)

    component_selected_records = _scan_selected(
        cmds,
        scanner,
        config,
        ["ScopeMesh_A.vtx[0]"],
    )
    component_selected_by_name = _records_by_name(component_selected_records)

    cmds.select(["ScopeMesh_A", "ScopeLocator_A"], replace=True)
    selected_pipeline_result = pipeline.run(config.SELECTED, config.DRY_RUN)

    relevant_names = [
        "ScopeMesh_A",
        "ScopeLocator_A",
        scene_nodes["camera_transform"],
        "ScopeLight_A",
        "ScopeInstancedMesh_A",
        "ScopeInstancedMesh_A_Copy",
        "ScopeParent_A",
        "ScopeChildMesh_A",
        "scopeRef:ScopeRefMesh_A",
    ]

    result = {
        "all_scene": {
            "scanned_count": len(all_records),
            "relevant_records": {
                name: _record_summary(all_by_name.get(name))
                for name in relevant_names
            },
        },
        "selected_scope": {
            "selected_names": [record.get("name") for record in selected_records],
            "records": {
                name: _record_summary(record)
                for name, record in selected_by_name.items()
            },
        },
        "shape_selection": {
            "selected_shape": shape_node,
            "selected_names": [record.get("name") for record in shape_selected_records],
            "scope_mesh_record": _record_summary(shape_selected_by_name.get("ScopeMesh_A")),
        },
        "child_selection": {
            "selected_names": [record.get("name") for record in child_selected_records],
            "child_record": _record_summary(child_selected_by_name.get("ScopeChildMesh_A")),
        },
        "component_selection": {
            "selected_component": "ScopeMesh_A.vtx[0]",
            "selected_names": [record.get("name") for record in component_selected_records],
            "scope_mesh_record": _record_summary(component_selected_by_name.get("ScopeMesh_A")),
        },
        "pipeline_selected_scope": {
            "success": selected_pipeline_result.get("success"),
            "message": selected_pipeline_result.get("message"),
            "summary": selected_pipeline_result.get("summary"),
            "route_decisions_count": selected_pipeline_result.get("route_decisions_count"),
            "route_decision_names": [
                decision.get("object_name")
                for decision in selected_pipeline_result.get("route_decisions") or []
            ],
            "report_paths": selected_pipeline_result.get("report_paths"),
            "report_paths_exist": {
                key: bool(path and os.path.exists(path))
                for key, path in (selected_pipeline_result.get("report_paths") or {}).items()
            },
        },
        "checks": {
            "all_scene_includes_relevant_transforms": all(
                all_by_name.get(name) is not None for name in relevant_names
            ),
            "all_scene_records_reference_and_instance_facts": (
                (all_by_name.get("scopeRef:ScopeRefMesh_A") or {}).get("is_referenced") is True
                and (all_by_name.get("ScopeInstancedMesh_A") or {}).get("is_instanced") is True
                and (all_by_name.get("ScopeInstancedMesh_A_Copy") or {}).get("is_instanced") is True
            ),
            "selected_scope_includes_only_selected_transforms": sorted(
                record.get("name") for record in selected_records
            ) == ["ScopeLocator_A", "ScopeMesh_A"],
            "selected_scope_marks_selected_records": all(
                record.get("is_selected") is True for record in selected_records
            ),
            "shape_selection_normalizes_to_transform": (
                len(shape_selected_records) == 1
                and shape_selected_records[0].get("name") == "ScopeMesh_A"
            ),
            "child_selection_records_child_transform": (
                len(child_selected_records) == 1
                and child_selected_records[0].get("name") == "ScopeChildMesh_A"
            ),
            "component_selection_normalizes_to_transform": (
                len(component_selected_records) == 1
                and component_selected_records[0].get("name") == "ScopeMesh_A"
            ),
            "run_result_selected_count_matches_scanner": (
                (selected_pipeline_result.get("summary") or {}).get("scanned")
                == len(selected_records)
                == selected_pipeline_result.get("route_decisions_count")
            ),
        },
    }

    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(RESULT_PATH)


if __name__ == "__main__":
    main()
