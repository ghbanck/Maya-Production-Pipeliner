"""Apply organizer for Maya Production Pipeliner.

Phase 8a runtime scope:
- Create or reuse Pipeline_Organized and all config.OUTPUT_GROUPS child groups
  when Apply is called (ensure_group_structure).
- Evaluate Apply preflight eligibility for each RouteDecision (apply_routes).
- No route decision objects are moved, parented, or renamed.
- Dry Run must never call ensure_group_structure.

Mutation boundary: only organizer.py may mutate scene hierarchy.
"""

try:
    import maya.cmds as cmds
except ImportError:
    cmds = None  # Running outside Maya; stubs will raise NotImplementedError.

from maya_production_pipeliner import config


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def ensure_group_structure():
    """Create or reuse Pipeline_Organized and all OUTPUT_GROUPS child groups.

    Called by pipeline.py in Apply mode before apply_routes().
    Never called during Dry Run.

    Returns
    -------
    dict
        Mapping of group name -> 'created' | 'reused' | 'error: <msg>'.
        Empty dict when cmds is unavailable (outside Maya).
    """
    if cmds is None:
        return {}

    status = {}
    root_full = "|" + config.ROOT_GROUP

    try:
        if not cmds.objExists(root_full):
            cmds.createNode("transform", name=config.ROOT_GROUP)
            status[config.ROOT_GROUP] = "created"
        else:
            status[config.ROOT_GROUP] = "reused"
    except Exception as exc:
        status[config.ROOT_GROUP] = "error: " + str(exc)
        return status

    for group_name in config.OUTPUT_GROUPS:
        child_full = root_full + "|" + group_name
        try:
            if not cmds.objExists(child_full):
                cmds.createNode("transform", name=group_name,
                                parent=config.ROOT_GROUP)
                status[group_name] = "created"
            else:
                status[group_name] = "reused"
        except Exception as exc:
            status[group_name] = "error: " + str(exc)

    return status


def apply_routes(route_decisions):
    """Return non-mutating Apply preflight results for route decisions.

    Parameters
    ----------
    route_decisions : list[dict]
        Output of classifier.classify().

    Returns
    -------
    list[dict]
        Route decisions annotated with apply preflight fields and
        operation status updates where applicable.
    """
    evaluated = []
    for decision in route_decisions or []:
        item = dict(decision)
        item["apply_preflight"] = _preflight_decision(item)
        preflight = item["apply_preflight"]
        if preflight["eligible"] and item.get("operation") == config.OPERATION_MOVE:
            item["operation_status"] = config.STATUS_PLANNED
        elif not preflight["eligible"] and preflight["status"]:
            item["operation_status"] = preflight["status"]
        item["did_move"] = False
        item["new_long_name"] = None
        evaluated.append(item)
    return evaluated


# ---------------------------------------------------------------------------
# Internal helpers (stubs)
# ---------------------------------------------------------------------------

def _preflight_decision(decision):
    """Return eligibility and block reasons without mutating scene state."""
    reasons = []
    status = None

    if decision.get("operation") != config.OPERATION_MOVE:
        reasons.append("operation is report_only")
        return {"eligible": False, "status": decision.get("operation_status"), "reasons": reasons}

    if not decision.get("can_move"):
        reasons.append("can_move is false")
        return {"eligible": False, "status": decision.get("operation_status"), "reasons": reasons}

    target_group = decision.get("target_group")
    if not target_group:
        reasons.append("missing target group")
        return {"eligible": False, "status": config.STATUS_PRESERVED_REPORT_ONLY, "reasons": reasons}

    long_name = decision.get("long_name")
    if not long_name:
        reasons.append("missing long_name")
        return {"eligible": False, "status": config.STATUS_SKIPPED_MISSING_NODE, "reasons": reasons}

    if cmds is not None:
        if not cmds.objExists(long_name):
            reasons.append("node missing at apply preflight")
            return {"eligible": False, "status": config.STATUS_SKIPPED_MISSING_NODE, "reasons": reasons}
    else:
        reasons.append("maya runtime unavailable; eligibility not verified")
        return {"eligible": False, "status": config.STATUS_PRESERVED_REPORT_ONLY, "reasons": reasons}

    if _is_already_in_target(long_name, target_group):
        reasons.append("already in target group")
        status = config.STATUS_ALREADY_IN_TARGET
        return {"eligible": False, "status": status, "reasons": reasons}

    return {"eligible": True, "status": config.STATUS_PLANNED, "reasons": reasons}


def _is_already_in_target(long_name, target_group):
    """Return True when long_name parent short name matches target_group."""
    if cmds is None:
        return False
    try:
        parents = cmds.listRelatives(long_name, parent=True, fullPath=True) or []
    except (RuntimeError, ValueError, TypeError):
        parents = []
    if not parents:
        return False
    parent_short = parents[0].split("|")[-1]
    return parent_short == target_group
