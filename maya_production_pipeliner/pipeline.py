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
5. If Apply:   run organizer.apply_routes(), write reports, build RunResult.
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
    # TODO: Phase 6 — implement full coordination:
    #   1. mel_bridge.run_pre_hook(pre_hook)
    #   2. scanner.scan(scope_mode, ignore_string)
    #   3. classifier.classify(records, execution_mode, scope_mode, ignore_string)
    #   4. organizer.apply_routes(decisions) if Apply
    #   5. reporter.write_reports(run_result, decisions)
    #   6. mel_bridge.run_post_hook(post_hook)
    #   7. return _build_run_result(...)
    raise NotImplementedError("pipeline.run() is not yet implemented.")


# ---------------------------------------------------------------------------
# Internal helpers (stubs)
# ---------------------------------------------------------------------------

def _build_run_result(scope_mode, execution_mode, ignore_string,
                      object_records, route_decisions,
                      report_paths, mel_hook_status,
                      success, message):
    """Assemble and return a RunResult dict.

    TODO: Phase 6 — populate all RunResult fields defined by the
    project data contracts, including summary counters,
    warnings, preview_routes (limited by MAX_UI_PREVIEW_ITEMS), and
    route_decisions_count.
    """
    raise NotImplementedError


def _build_summary(route_decisions):
    """Return a summary dict with counters derived from *route_decisions*.

    TODO: Phase 6 — count scanned, planned, moved, already_in_target,
    preserved, warnings, and failed.
    """
    raise NotImplementedError


def _build_preview_routes(route_decisions, max_items):
    """Return a trimmed list of route preview dicts for the UI.

    Each item contains: object_name, route, target_group, operation_status,
    can_move.

    TODO: Phase 6 — slice to max_items and format each item.
    """
    raise NotImplementedError
