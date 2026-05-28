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
    # TODO: Phase 5 — iterate object_records, apply priority ladder, and
    #       populate route, target_group, can_move, operation, operation_status,
    #       reason, preserve_reason, warnings, would_move, report_only,
    #       execution_mode, and scope_mode for each decision.
    raise NotImplementedError("classifier.classify() is not yet implemented.")


# ---------------------------------------------------------------------------
# Internal helpers (stubs)
# ---------------------------------------------------------------------------

def _is_tool_structural_group(record):
    """Return True when the object is a Pipeline_Organized structural group.

    TODO: Phase 5 — check is_tool_structural_group and is_inside_tool_output
    flags on the record.
    """
    raise NotImplementedError


def _is_bypass(record):
    """Return True when the object matches the user ignore-string.

    TODO: Phase 5 — check record['matches_ignore_string'].
    """
    raise NotImplementedError


def _is_reference(record):
    """Return True when the object is a referenced node.

    TODO: Phase 5 — check record['is_referenced'].
    """
    raise NotImplementedError


def _is_instance(record):
    """Return True when the object is instanced geometry.

    TODO: Phase 5 — check record['is_instanced'].
    """
    raise NotImplementedError


def _is_rig_sensitive(record):
    """Return True when the object is rig/deformer-sensitive.

    TODO: Phase 5 — check has_skin_cluster, has_blendshape,
    parent_is_joint, is_under_sensitive_hierarchy.
    """
    raise NotImplementedError


def _is_scene_utility(record):
    """Return True when the object is a scene utility (locator, camera, etc).

    TODO: Phase 5 — evaluate node_type/shape_type against utility criteria.
    """
    raise NotImplementedError


def _material_review_route(record):
    """Return the material-review route string or None if not applicable.

    TODO: Phase 5 — return REVIEW_MISSING_MATERIAL when uses_default_material
    or material_count == 0; return REVIEW_MULTI_MATERIAL when material_count
    > 1; return None otherwise.
    """
    raise NotImplementedError


def _build_route_decision(record, route, target_group, can_move,
                          operation, operation_status, reason,
                          preserve_reason, warnings,
                          execution_mode, scope_mode):
    """Assemble and return a RouteDecision dict.

    TODO: Phase 5 — fill all RouteDecision fields defined by the
    project data contracts.
    """
    raise NotImplementedError
