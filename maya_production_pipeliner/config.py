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

DRY_RUN = "dry_run"
APPLY = "apply"
EXECUTION_MODES = (DRY_RUN, APPLY)

# ---------------------------------------------------------------------------
# Scope modes
# ---------------------------------------------------------------------------

ALL_SCENE = "all_scene"
SELECTED = "selected"
VISIBLE = "visible"
SCOPE_MODES = (ALL_SCENE, SELECTED, VISIBLE)

# ---------------------------------------------------------------------------
# Output group names
# ---------------------------------------------------------------------------

ROOT_GROUP = "Pipeline_Organized"
PRODUCTION_MESHES = "Production_Meshes"
SCENE_UTILITIES = "Scene_Utilities"
REFERENCES = "References"
REVIEW_MISSING_MATERIAL = "Review_MissingMaterial"
REVIEW_MULTI_MATERIAL = "Review_MultiMaterial"
REVIEW_UNCLEAR_CASES = "Review_UnclearCases"
BYPASS = "Bypass"

OUTPUT_GROUPS = (
    PRODUCTION_MESHES,
    SCENE_UTILITIES,
    REFERENCES,
    REVIEW_MISSING_MATERIAL,
    REVIEW_MULTI_MATERIAL,
    REVIEW_UNCLEAR_CASES,
    BYPASS,
)

STRUCTURAL_GROUPS = (ROOT_GROUP,) + OUTPUT_GROUPS

# ---------------------------------------------------------------------------
# Route names (mirror group names where applicable)
# ---------------------------------------------------------------------------

ROUTE_PRODUCTION_MESHES = PRODUCTION_MESHES
ROUTE_SCENE_UTILITIES = SCENE_UTILITIES
ROUTE_REFERENCES = REFERENCES
ROUTE_REVIEW_MISSING_MATERIAL = REVIEW_MISSING_MATERIAL
ROUTE_REVIEW_MULTI_MATERIAL = REVIEW_MULTI_MATERIAL
ROUTE_REVIEW_UNCLEAR_CASES = REVIEW_UNCLEAR_CASES
ROUTE_BYPASS = BYPASS

# ---------------------------------------------------------------------------
# Operation names and status values
# ---------------------------------------------------------------------------

OPERATION_MOVE = "move"
OPERATION_REPORT_ONLY = "report_only"

STATUS_PLANNED = "planned"
STATUS_DRY_RUN_ONLY = "dry_run_only"
STATUS_MOVED = "moved"
STATUS_ALREADY_IN_TARGET = "already_in_target"
STATUS_PRESERVED_REPORT_ONLY = "preserved_report_only"
STATUS_SKIPPED_REFERENCE = "skipped_reference"
STATUS_SKIPPED_INSTANCE = "skipped_instance"
STATUS_SKIPPED_SENSITIVE_HIERARCHY = "skipped_sensitive_hierarchy"
STATUS_SKIPPED_TOOL_STRUCTURE = "skipped_tool_structure"
STATUS_SKIPPED_MISSING_NODE = "skipped_missing_node"
STATUS_FAILED_PARENTING = "failed_parenting"

OPERATION_STATUSES = (
    STATUS_PLANNED,
    STATUS_DRY_RUN_ONLY,
    STATUS_MOVED,
    STATUS_ALREADY_IN_TARGET,
    STATUS_PRESERVED_REPORT_ONLY,
    STATUS_SKIPPED_REFERENCE,
    STATUS_SKIPPED_INSTANCE,
    STATUS_SKIPPED_SENSITIVE_HIERARCHY,
    STATUS_SKIPPED_TOOL_STRUCTURE,
    STATUS_SKIPPED_MISSING_NODE,
    STATUS_FAILED_PARENTING,
)

# ---------------------------------------------------------------------------
# Maya type and material identifiers
# ---------------------------------------------------------------------------

DEFAULT_SHADING_GROUP = "initialShadingGroup"
MESH_SHAPE_TYPE = "mesh"
UTILITY_SHAPE_TYPES = ("camera", "locator", "light", "nurbsCurve")
UTILITY_NODE_TYPES = ("camera", "locator", "light", "joint")
RIG_HISTORY_TYPES = ("skinCluster", "blendShape")

# ---------------------------------------------------------------------------
# Report defaults
# ---------------------------------------------------------------------------

TOOL_NAME = "Maya Production Pipeliner"
REPORT_TXT_NAME = "maya_production_pipeliner_report.txt"
REPORT_JSON_NAME = "maya_production_pipeliner_report.json"
REPORT_SCHEMA_VERSION = "0.1"

# ---------------------------------------------------------------------------
# UI preview limits
# ---------------------------------------------------------------------------

MAX_UI_PREVIEW_ITEMS = 25

# ---------------------------------------------------------------------------
# Ignore-string warning threshold
# ---------------------------------------------------------------------------

IGNORE_MATCH_WARNING_THRESHOLD = 25

# ---------------------------------------------------------------------------
# Warning codes
# ---------------------------------------------------------------------------

WARNING_IGNORE_MATCH_HIGH = "IGNORE_MATCH_HIGH"
