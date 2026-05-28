"""
config.py
=========
Central store for all constants, group names, scope values, execution modes,
material identifiers, visibility settings, report defaults, and UI preview
limits used across the Maya Production Pipeliner.

Rules
-----
- This module must not import maya.cmds or any Maya runtime.
- It must not contain logic; only constant definitions.
- All other modules import their settings from here; they do not hard-code
  their own defaults.
"""

# ---------------------------------------------------------------------------
# Execution modes
# ---------------------------------------------------------------------------
# TODO: Phase 2 — define DRY_RUN and APPLY string constants.

# ---------------------------------------------------------------------------
# Scope modes
# ---------------------------------------------------------------------------
# TODO: Phase 2 — define ALL_SCENE, SELECTED, VISIBLE string constants.

# ---------------------------------------------------------------------------
# Output group names
# ---------------------------------------------------------------------------
# TODO: Phase 2 — define ROOT_GROUP, PRODUCTION_MESHES, SCENE_UTILITIES,
#       REFERENCES, REVIEW_MISSING_MATERIAL, REVIEW_MULTI_MATERIAL,
#       REVIEW_UNCLEAR_CASES, BYPASS string constants.

# ---------------------------------------------------------------------------
# Route names (mirror group names where applicable)
# ---------------------------------------------------------------------------
# TODO: Phase 2 — define ROUTE_* constants mirroring the group structure.

# ---------------------------------------------------------------------------
# Operation status values
# ---------------------------------------------------------------------------
# TODO: Phase 2 — define STATUS_* constants (planned, dry_run_only, moved,
#       already_in_target, preserved_report_only, skipped_reference,
#       skipped_instance, skipped_sensitive_hierarchy, skipped_tool_structure,
#       skipped_missing_node, failed_parenting).

# ---------------------------------------------------------------------------
# Material identifiers
# ---------------------------------------------------------------------------
# TODO: Phase 2 — define DEFAULT_SHADING_GROUP constant (initialShadingGroup).

# ---------------------------------------------------------------------------
# Report defaults
# ---------------------------------------------------------------------------
# TODO: Phase 2 — define REPORT_TXT_NAME and REPORT_JSON_NAME defaults.

# ---------------------------------------------------------------------------
# UI preview limits
# ---------------------------------------------------------------------------
# TODO: Phase 2 — define MAX_UI_PREVIEW_ITEMS integer constant.

# ---------------------------------------------------------------------------
# Ignore-string warning threshold
# ---------------------------------------------------------------------------
# TODO: Phase 2 — define IGNORE_MATCH_WARNING_THRESHOLD integer constant.
