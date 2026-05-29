"""
pipeline.py
===========
Pipeline coordinator for the Maya Production Pipeliner.

Responsibility
--------------
Coordinate configuration loading, MEL pre-hook, scanning, classification,
optional Apply organisation, report writing, MEL post-hook, and RunResult
construction.  Return a RunResult dict to the caller (UI or launcher).

This module does not modify the Maya scene directly; it delegates to the
appropriate module for each step.

Execution flow
--------------
1. Load user options and call MEL pre-hook (if configured).
2. Scan the scene with scanner.scan().
3. Classify records with classifier.classify().
4. If Dry Run: write reports and build RunResult without touching the scene.
5. If Apply:   run non-mutating apply preflight, write reports, build RunResult.
6. Call MEL post-hook (if configured) and return RunResult.

Dependencies
------------
- config       (mode constants)
- scanner      (scan)
- classifier   (classify)
- organizer    (apply_routes)  — Apply mode only
- reporter     (write_reports)
- mel_bridge   (run_pre_hook, run_post_hook)

Public API
----------
    run(scope_mode, execution_mode, ignore_string="",
        pre_hook="", post_hook="") -> dict
        Execute the full pipeline and return a RunResult dict.
"""

from maya_production_pipeliner import (  # noqa: F401  (used in Phase 6)
    config,
    scanner,
    classifier,
    organizer,
    reporter,
    mel_bridge,
)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(scope_mode, execution_mode, ignore_string="",
        pre_hook="", post_hook=""):
    """Run the full pipeline and return a RunResult dict.

    Parameters
    ----------
    scope_mode : str
        config.ALL_SCENE, config.SELECTED, or config.VISIBLE.
    execution_mode : str
        config.DRY_RUN or config.APPLY.
    ignore_string : str
        User-defined preservation pattern.  Empty string disables.
    pre_hook : str
        Optional MEL procedure name to call before the pipeline.
    post_hook : str
        Optional MEL procedure name to call after the pipeline.

    Returns
    -------
    dict
        RunResult dict.  The UI must read only this object; it must not
        open or parse report files to determine execution state.
    """
    if scope_mode not in config.SCOPE_MODES:
        raise ValueError("Unsupported scope_mode: {0}".format(scope_mode))
    if execution_mode not in config.EXECUTION_MODES:
        raise ValueError("Unsupported execution_mode: {0}".format(execution_mode))

    mel_hook_status = _build_disabled_hook_status(pre_hook, post_hook)

    if execution_mode == config.APPLY:
        object_records = scanner.scan(scope_mode, ignore_string)
        route_decisions = classifier.classify(
            object_records, execution_mode, scope_mode, ignore_string
        )
        route_decisions = organizer.apply_routes(route_decisions)
        planned_count = len([
            item for item in route_decisions
            if (item.get("apply_preflight") or {}).get("eligible")
        ])
        blocked_count = len(route_decisions) - planned_count
        message = (
            "Apply preflight completed without scene changes. "
            "Planned moves: {0}. Blocked: {1}."
        ).format(planned_count, blocked_count)
        run_result = _build_run_result(
            scope_mode, execution_mode, ignore_string, object_records,
            route_decisions, {}, mel_hook_status, True, message,
        )
        report_paths = reporter.write_reports(run_result, route_decisions)
        run_result["report_paths"] = report_paths
        return run_result

    object_records = scanner.scan(scope_mode, ignore_string)
    route_decisions = classifier.classify(
        object_records, execution_mode, scope_mode, ignore_string
    )
    run_result = _build_run_result(
        scope_mode, execution_mode, ignore_string, object_records,
        route_decisions, {}, mel_hook_status, True,
        "Dry Run completed without scene changes.",
    )
    report_paths = reporter.write_reports(run_result, route_decisions)
    run_result["report_paths"] = report_paths
    return run_result


# ---------------------------------------------------------------------------
# Internal helpers (stubs)
# ---------------------------------------------------------------------------

def _build_run_result(scope_mode, execution_mode, ignore_string,
                      object_records, route_decisions,
                      report_paths, mel_hook_status,
                      success, message):
    """Assemble and return a RunResult dict.

    """
    warnings = []
    warning_events = []
    for record in object_records:
        for warning in record.get("warnings") or []:
            warnings.append(str(warning))
            warning_events.append({
                "code": "SCANNER_WARNING",
                "message": str(warning),
                "source": "scanner",
            })
    for decision in route_decisions:
        for warning in decision.get("warnings") or []:
            warnings.append(str(warning))
            warning_events.append({
                "code": "CLASSIFIER_WARNING",
                "message": str(warning),
                "source": "classifier",
            })

    ignore_matches = [
        record for record in object_records
        if record.get("matches_ignore_string")
    ]
    if len(ignore_matches) > config.IGNORE_MATCH_WARNING_THRESHOLD:
        warning_message = "Ignore string matched {0} objects.".format(
            len(ignore_matches)
        )
        warnings.append(warning_message)
        warning_events.append({
            "code": config.WARNING_IGNORE_MATCH_HIGH,
            "message": warning_message,
            "source": "pipeline",
        })

    return {
        "route_decisions": route_decisions,
        "summary": _build_summary(route_decisions, len(object_records)),
        "warnings": warnings,
        "warning_events": warning_events,
        "report_paths": report_paths or {"txt": None, "json": None},
        "mel_hook_status": mel_hook_status,
        "execution_mode": execution_mode,
        "scope_mode": scope_mode,
        "ignore_string": ignore_string,
        "success": bool(success),
        "message": message,
        "route_decisions_count": len(route_decisions),
        "preview_routes": _build_preview_routes(
            route_decisions, config.MAX_UI_PREVIEW_ITEMS
        ),
        "max_ui_preview_items": config.MAX_UI_PREVIEW_ITEMS,
    }


def _build_disabled_hook_status(pre_hook="", post_hook=""):
    """Return hook status for the initial read-only runtime slice.

    MEL hooks are implemented in mel_bridge.py but intentionally not called by
    the first Dry Run runtime because user-defined hooks can mutate a scene.
    """
    errors = []
    pre_status = _disabled_single_hook_status(pre_hook)
    post_status = _disabled_single_hook_status(post_hook)
    if pre_status["error"]:
        errors.append(pre_status["error"])
    if post_status["error"]:
        errors.append(post_status["error"])
    return {"pre": pre_status, "post": post_status, "errors": errors}


def _disabled_single_hook_status(hook_name=""):
    """Return neutral or disabled status for one optional MEL hook."""
    if not hook_name:
        return {"called": False, "success": True, "error": None}
    return {
        "called": False,
        "success": False,
        "error": "MEL hooks are disabled in the initial Dry Run runtime.",
    }


def _build_summary(route_decisions, scanned_count=0):
    """Return a summary dict with counters derived from *route_decisions*.

    """
    summary = {
        "scanned": scanned_count,
        "planned": len(route_decisions),
        "would_move": 0,
        "moved": 0,
        "already_in_target": 0,
        "preserved": 0,
        "warnings": 0,
        "failed": 0,
    }
    for decision in route_decisions:
        if decision.get("would_move"):
            summary["would_move"] += 1
        if decision.get("did_move"):
            summary["moved"] += 1
        if decision.get("operation_status") == config.STATUS_ALREADY_IN_TARGET:
            summary["already_in_target"] += 1
        if decision.get("report_only") or not decision.get("can_move"):
            summary["preserved"] += 1
        if decision.get("operation_status") == config.STATUS_FAILED_PARENTING:
            summary["failed"] += 1
        summary["warnings"] += len(decision.get("warnings") or [])
    return summary


def _build_preview_routes(route_decisions, max_items):
    """Return a trimmed list of route preview dicts for the UI.

    Each item contains: object_name, route, target_group, operation_status,
    can_move.

    """
    preview = []
    for decision in route_decisions[:max_items]:
        preview.append({
            "object_name": decision.get("object_name"),
            "route": decision.get("route"),
            "target_group": decision.get("target_group"),
            "operation_status": decision.get("operation_status"),
            "can_move": decision.get("can_move"),
        })
    return preview
