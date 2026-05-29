"""
scanner.py
==========
Scene scanning module for the Maya Production Pipeliner.

Responsibility
--------------
Collect facts about scene objects and return a list of ObjectRecord
instances.  This module must never classify objects, assign routes,
create groups, move objects, or write reports.

Dependencies
------------
- maya.cmds  (Maya runtime; guarded import — safe outside Maya)
- config     (scope mode constants)

Public API
----------
    scan(scope_mode, ignore_string="") -> list[dict]
        Return one ObjectRecord dict per object found within the given scope.
"""

try:
    import maya.cmds as cmds
except ImportError:
    cmds = None  # Running outside Maya; stubs will raise NotImplementedError.

from maya_production_pipeliner import config  # noqa: F401  (used in Phase 4)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def scan(scope_mode, ignore_string=""):
    """Scan the Maya scene and return a list of ObjectRecord dicts.

    Parameters
    ----------
    scope_mode : str
        One of config.ALL_SCENE, config.SELECTED, or config.VISIBLE.
    ignore_string : str
        User-defined preservation pattern.  Empty string disables matching.

    Returns
    -------
    list[dict]
        One ObjectRecord dict per scanned object.  Never contains route
        decisions, can_move flags, or target groups.
    """
    if scope_mode not in config.SCOPE_MODES:
        raise ValueError("Unsupported scope_mode: {0}".format(scope_mode))

    if cmds is None:
        return []

    selected_transforms = set(
        _normalize_to_transforms(cmds.ls(selection=True, long=True) or [])
    )
    records = []
    seen = set()
    for transform in _resolve_scope(scope_mode):
        long_name = _as_long_name(transform)
        if not long_name or long_name in seen:
            continue
        seen.add(long_name)
        records.append(
            _build_object_record(long_name, ignore_string, selected_transforms)
        )
    return sorted(records, key=lambda item: item.get("long_name") or "")


# ---------------------------------------------------------------------------
# Internal helpers (stubs)
# ---------------------------------------------------------------------------

def _resolve_scope(scope_mode):
    """Return the list of transform node names for the given scope mode.

    Visible scope currently uses Maya's native visible transform query as the
    first safe slice.  Display-layer and inherited visibility hardening belongs
    to a later scanner pass.
    """
    if cmds is None:
        return []

    if scope_mode == config.ALL_SCENE:
        return sorted(cmds.ls(type="transform", long=True) or [])

    if scope_mode == config.SELECTED:
        selected = cmds.ls(selection=True, long=True) or []
        return sorted(_normalize_to_transforms(selected))

    if scope_mode == config.VISIBLE:
        visible = cmds.ls(type="transform", visible=True, long=True) or []
        return sorted(visible)

    raise ValueError("Unsupported scope_mode: {0}".format(scope_mode))


def _build_object_record(transform, ignore_string="", selected_transforms=None):
    """Build and return a single ObjectRecord dict for *transform*.

    """
    long_name = _as_long_name(transform) or transform
    name = long_name.split("|")[-1]
    shape_nodes = cmds.listRelatives(
        long_name, shapes=True, fullPath=True, noIntermediate=True
    ) or []
    shape_types = [_safe_node_type(shape) for shape in shape_nodes]
    shape_type = shape_types[0] if shape_types else None
    selected_transforms = selected_transforms or set()
    (
        materials,
        material_node_count,
        shading_engines,
        shading_engine_count,
        uses_default_material,
    ) = _detect_materials(long_name)
    hierarchy_visible, native_visible, resolved_visible = _resolve_visibility(long_name)
    is_referenced = _safe_reference_query(long_name)
    is_instanced = _is_instanced(shape_nodes)
    has_skin_cluster, has_blendshape = _detect_rig_history(long_name, shape_nodes)
    parent_is_joint = _parent_is_joint(long_name)
    is_inside_tool_output = _is_inside_tool_output(long_name)
    is_tool_structural_group = name in config.STRUCTURAL_GROUPS

    return {
        "name": name,
        "long_name": long_name,
        "transform_node": long_name,
        "shape_nodes": shape_nodes,
        "node_type": _safe_node_type(long_name),
        "shape_type": shape_type,
        "shape_types": shape_types,
        "is_mesh": config.MESH_SHAPE_TYPE in shape_types,
        "is_visible": resolved_visible,
        "is_selected": long_name in selected_transforms,
        "namespace": _namespace_from_name(name),
        "materials": materials,
        "material_count": material_node_count,
        "material_node_count": material_node_count,
        "shading_engines": shading_engines,
        "shading_engine_count": shading_engine_count,
        "uses_default_material": uses_default_material,
        "matches_ignore_string": _matches_ignore_string(name, long_name, ignore_string),
        "is_referenced": is_referenced,
        "is_instanced": is_instanced,
        "has_skin_cluster": has_skin_cluster,
        "has_blendshape": has_blendshape,
        "parent_is_joint": parent_is_joint,
        "is_under_sensitive_hierarchy": parent_is_joint,
        "is_inside_tool_output": is_inside_tool_output,
        "is_tool_structural_group": is_tool_structural_group,
        "hierarchy_visible": hierarchy_visible,
        "display_layer_visible": None,
        "native_visible": native_visible,
        "resolved_visible": resolved_visible,
        "warnings": [],
    }


def _resolve_visibility(transform):
    """Derive resolved_visible from node, layer, shape, and hierarchy state.

    """
    if cmds is None:
        return None, None, None

    hierarchy_visible = True
    parts = transform.split("|")
    for index in range(1, len(parts) + 1):
        path = "|".join(parts[:index])
        if not path or not cmds.objExists(path):
            continue
        try:
            if cmds.attributeQuery("visibility", node=path, exists=True):
                if not bool(cmds.getAttr(path + ".visibility")):
                    hierarchy_visible = False
                    break
        except Exception:
            hierarchy_visible = None
            break

    try:
        native_visible = bool(cmds.ls(transform, visible=True))
    except Exception:
        native_visible = None

    if hierarchy_visible is False or native_visible is False:
        resolved_visible = False
    elif hierarchy_visible is None and native_visible is None:
        resolved_visible = None
    else:
        resolved_visible = True

    return hierarchy_visible, native_visible, resolved_visible


def _detect_materials(transform):
    """Return material and shadingEngine facts for one transform.

    """
    if cmds is None:
        return [], 0, [], 0, False

    materials = set()
    shading_engines = set()
    shapes = cmds.listRelatives(
        transform, shapes=True, fullPath=True, noIntermediate=True
    ) or []

    for shape in shapes:
        try:
            connections = cmds.listConnections(shape, type="shadingEngine") or []
        except Exception:
            connections = []
        shading_engines.update(connections)

    for shading_engine in shading_engines:
        try:
            connected_materials = cmds.listConnections(
                shading_engine + ".surfaceShader"
            ) or []
        except Exception:
            connected_materials = []
        materials.update(connected_materials)

    if not materials and config.DEFAULT_SHADING_GROUP in shading_engines:
        materials.add(config.DEFAULT_SHADING_GROUP)

    sorted_materials = sorted(materials)
    sorted_shading_engines = sorted(shading_engines)
    return (
        sorted_materials,
        len(sorted_materials),
        sorted_shading_engines,
        len(sorted_shading_engines),
        config.DEFAULT_SHADING_GROUP in shading_engines,
    )


def _matches_ignore_string(name, long_name, ignore_string):
    """Return True if *name* or *long_name* contains *ignore_string*.

    """
    if not ignore_string:
        return False
    needle = ignore_string.lower()
    if needle in (name or "").lower() or needle in (long_name or "").lower():
        return True
    return any(needle in part.lower() for part in (long_name or "").split("|"))


def _normalize_to_transforms(nodes):
    """Return unique transform long names for selected nodes/components."""
    transforms = []
    seen = set()
    for node in nodes:
        clean_node = node.split(".")[0]
        transform = _transform_from_node(clean_node)
        if transform and transform not in seen:
            seen.add(transform)
            transforms.append(transform)
    return transforms


def _transform_from_node(node):
    """Resolve a Maya node or component path to a transform long name."""
    if not node or cmds is None:
        return None
    if not cmds.objExists(node):
        return None
    node_type = _safe_node_type(node)
    if node_type == "transform":
        return _as_long_name(node)
    parents = cmds.listRelatives(node, parent=True, fullPath=True) or []
    for parent in parents:
        if _safe_node_type(parent) == "transform":
            return _as_long_name(parent)
    return None


def _as_long_name(node):
    """Return the full DAG path for *node* when possible."""
    if not node or cmds is None:
        return node
    try:
        matches = cmds.ls(node, long=True) or []
    except Exception:
        matches = []
    return matches[0] if matches else node


def _safe_node_type(node):
    """Return a Maya node type string, or None when unavailable."""
    try:
        return cmds.nodeType(node)
    except Exception:
        return None


def _namespace_from_name(name):
    """Return the namespace prefix for a short Maya name, if present."""
    if ":" not in name:
        return ""
    return name.rsplit(":", 1)[0]


def _safe_reference_query(node):
    """Return True when Maya reports *node* as referenced."""
    try:
        return bool(cmds.referenceQuery(node, isNodeReferenced=True))
    except Exception:
        return False


def _is_instanced(shape_nodes):
    """Return True when any shape has more than one parent transform."""
    for shape in shape_nodes:
        try:
            parents = cmds.listRelatives(shape, allParents=True, fullPath=True) or []
        except Exception:
            parents = []
        if len(parents) > 1:
            return True
    return False


def _detect_rig_history(transform, shape_nodes):
    """Return skinCluster/blendShape flags for a transform and its shapes."""
    history_nodes = set()
    for node in [transform] + list(shape_nodes):
        try:
            history_nodes.update(cmds.listHistory(node, pruneDagObjects=True) or [])
        except Exception:
            continue
    history_types = {_safe_node_type(node) for node in history_nodes}
    return (
        "skinCluster" in history_types,
        "blendShape" in history_types,
    )


def _parent_is_joint(transform):
    """Return True when the immediate parent is a joint."""
    try:
        parents = cmds.listRelatives(transform, parent=True, fullPath=True) or []
    except Exception:
        parents = []
    return bool(parents and _safe_node_type(parents[0]) == "joint")


def _is_inside_tool_output(long_name):
    """Return True when a node is inside the tool's output hierarchy."""
    parts = [part for part in long_name.split("|") if part]
    return config.ROOT_GROUP in parts
