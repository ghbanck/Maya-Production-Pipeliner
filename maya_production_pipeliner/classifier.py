"""
classifier.py
=============
Route classification module for the Maya Production Pipeliner.

Responsibility
--------------
Consume a list of ObjectRecord dicts produced by scanner.py and return a
list of RouteDecision dicts.  This module must never modify the Maya scene.

Classification priority (highest to lowest)
--------------------------------------------
1. Internal tool structural groups  -> skipped_tool_structure
2. User ignore-string (Bypass)      -> Bypass / can_move=False
3. Referenced nodes                 -> References / can_move=False
4. Instanced geometry               -> preserved / can_move=False
5. Rig/deformer-sensitive content   -> preserved / can_move=False
6. Scene utilities                  -> Scene_Utilities
7. Material review                  -> Review_MissingMaterial or
                                        Review_MultiMaterial
8. Clean production meshes          -> Production_Meshes
9. Safe unclear cases               -> Review_UnclearCases

Dependencies
------------
- config  (route, group, and status constants)

Public API
----------
    classify(object_records, execution_mode, scope_mode, ignore_string="")
        -> list[dict]
        Return one RouteDecision dict per ObjectRecord.
"""

from maya_production_pipeliner import config  # noqa: F401  (used in Phase 5)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def classify(object_records, execution_mode, scope_mode, ignore_string=""):
    """Classify each ObjectRecord and return a list of RouteDecision dicts.

    Parameters
    ----------
    object_records : list[dict]
        Output of scanner.scan().
    execution_mode : str
        config.DRY_RUN or config.APPLY.
    scope_mode : str
        The scope mode used during scanning.
    ignore_string : str
        User-defined preservation pattern applied during scanning.

    Returns
    -------
    list[dict]
        One RouteDecision dict per input record.  The scene is never modified
        by this function.
    """
    if execution_mode not in config.EXECUTION_MODES:
        raise ValueError("Unsupported execution_mode: {0}".format(execution_mode))
    if scope_mode not in config.SCOPE_MODES:
        raise ValueError("Unsupported scope_mode: {0}".format(scope_mode))

    decisions = []
    for record in object_records:
        warnings = list(record.get("warnings") or [])

        if _is_tool_structural_group(record):
            decisions.append(_build_route_decision(
                record, config.ROUTE_REVIEW_UNCLEAR_CASES, None, False,
                config.OPERATION_REPORT_ONLY, config.STATUS_SKIPPED_TOOL_STRUCTURE,
                "internal tool structure", "tool structural group", warnings,
                execution_mode, scope_mode,
            ))
            continue

        if _is_bypass(record):
            decisions.append(_build_route_decision(
                record, config.ROUTE_BYPASS, config.BYPASS, False,
                config.OPERATION_REPORT_ONLY, config.STATUS_PRESERVED_REPORT_ONLY,
                "matches ignore string", "user ignore string", warnings,
                execution_mode, scope_mode,
            ))
            continue

        if _is_reference(record):
            decisions.append(_build_route_decision(
                record, config.ROUTE_REFERENCES, config.REFERENCES, False,
                config.OPERATION_REPORT_ONLY, config.STATUS_SKIPPED_REFERENCE,
                "referenced node", "referenced content", warnings,
                execution_mode, scope_mode,
            ))
            continue

        if _is_instance(record):
            decisions.append(_build_route_decision(
                record, config.ROUTE_REVIEW_UNCLEAR_CASES, None, False,
                config.OPERATION_REPORT_ONLY, config.STATUS_SKIPPED_INSTANCE,
                "instanced geometry", "instanced geometry", warnings,
                execution_mode, scope_mode,
            ))
            continue

        if _is_rig_sensitive(record):
            decisions.append(_build_route_decision(
                record, config.ROUTE_REVIEW_UNCLEAR_CASES, None, False,
                config.OPERATION_REPORT_ONLY,
                config.STATUS_SKIPPED_SENSITIVE_HIERARCHY,
                "rig or deformer sensitive content",
                "rig/deformer sensitive content", warnings,
                execution_mode, scope_mode,
            ))
            continue

        if _is_scene_utility(record):
            decisions.append(_build_route_decision(
                record, config.ROUTE_SCENE_UTILITIES, config.SCENE_UTILITIES,
                True, config.OPERATION_MOVE, config.STATUS_DRY_RUN_ONLY,
                "scene utility", "", warnings, execution_mode, scope_mode,
            ))
            continue

        material_route = _material_review_route(record)
        if material_route:
            decisions.append(_build_route_decision(
                record, material_route, material_route, True,
                config.OPERATION_MOVE, config.STATUS_DRY_RUN_ONLY,
                "material review required", "", warnings,
                execution_mode, scope_mode,
            ))
            continue

        if record.get("is_mesh"):
            decisions.append(_build_route_decision(
                record, config.ROUTE_PRODUCTION_MESHES,
                config.PRODUCTION_MESHES, True, config.OPERATION_MOVE,
                config.STATUS_DRY_RUN_ONLY, "production mesh candidate", "",
                warnings, execution_mode, scope_mode,
            ))
            continue

        decisions.append(_build_route_decision(
            record, config.ROUTE_REVIEW_UNCLEAR_CASES,
            config.REVIEW_UNCLEAR_CASES, False, config.OPERATION_REPORT_ONLY,
            config.STATUS_PRESERVED_REPORT_ONLY, "unclear object type",
            "unclear non-mesh content", warnings, execution_mode, scope_mode,
        ))

    return decisions


# ---------------------------------------------------------------------------
# Internal helpers (stubs)
# ---------------------------------------------------------------------------

def _is_tool_structural_group(record):
    """Return True when the object is a Pipeline_Organized structural group.

    """
    return bool(record.get("is_tool_structural_group"))


def _is_bypass(record):
    """Return True when the object matches the user ignore-string.

    """
    return bool(record.get("matches_ignore_string"))


def _is_reference(record):
    """Return True when the object is a referenced node.

    """
    return bool(record.get("is_referenced"))


def _is_instance(record):
    """Return True when the object is instanced geometry.

    """
    return bool(record.get("is_instanced"))


def _is_rig_sensitive(record):
    """Return True when the object is rig/deformer-sensitive.

    """
    return any((
        record.get("has_skin_cluster"),
        record.get("has_blendshape"),
        record.get("parent_is_joint"),
        record.get("is_under_sensitive_hierarchy"),
    ))


def _is_scene_utility(record):
    """Return True when the object is a scene utility (locator, camera, etc).

    """
    node_type = record.get("node_type")
    shape_type = record.get("shape_type")
    shape_types = record.get("shape_types") or []
    return (
        node_type in config.UTILITY_NODE_TYPES
        or shape_type in config.UTILITY_SHAPE_TYPES
        or any(item in config.UTILITY_SHAPE_TYPES for item in shape_types)
    )


def _material_review_route(record):
    """Return the material-review route string or None if not applicable.

    """
    if not record.get("is_mesh"):
        return None
    material_count = record.get("material_count")
    if record.get("uses_default_material") or material_count == 0:
        return config.ROUTE_REVIEW_MISSING_MATERIAL
    if material_count and material_count > 1:
        return config.ROUTE_REVIEW_MULTI_MATERIAL
    return None


def _build_route_decision(record, route, target_group, can_move,
                          operation, operation_status, reason,
                          preserve_reason, warnings,
                          execution_mode, scope_mode):
    """Assemble and return a RouteDecision dict.

    """
    report_only = operation == config.OPERATION_REPORT_ONLY or not can_move
    would_move = (
        execution_mode == config.DRY_RUN
        and operation == config.OPERATION_MOVE
        and can_move
    )
    return {
        "object_name": record.get("name"),
        "long_name": record.get("long_name"),
        "new_long_name": None,
        "route": route,
        "target_group": target_group,
        "reason": reason,
        "warnings": warnings,
        "execution_mode": execution_mode,
        "scope_mode": scope_mode,
        "can_move": bool(can_move),
        "operation": operation,
        "preserve_reason": preserve_reason,
        "report_only": report_only,
        "would_move": would_move,
        "did_move": False,
        "operation_status": operation_status,
        "source_record": record,
    }
