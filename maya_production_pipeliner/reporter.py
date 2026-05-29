"""
reporter.py
===========
Report writing module for the Maya Production Pipeliner.

Responsibility
--------------
Receive a RunResult and a list of RouteDecision dicts, then write TXT and
JSON report files.  This module must never modify the Maya scene and must
never drive the UI.

Report path priority
---------------------
1. Directory of the saved Maya scene file.
2. Maya workspace directory.
3. System temporary directory (fallback).

Dependencies
------------
- maya.cmds  (Maya runtime; guarded import — used only for scene path and
              workspace queries; safe outside Maya)
- config     (report file name constants)

Public API
----------
    write_reports(run_result, route_decisions) -> dict
        Write TXT and JSON reports and return a dict with keys 'txt' and
        'json' containing the written file paths (or None on failure).
"""

import json
import os
import tempfile
from datetime import datetime

try:
    import maya.cmds as cmds
except ImportError:
    cmds = None  # Running outside Maya; stubs will raise NotImplementedError.

from maya_production_pipeliner import config  # noqa: F401  (used in Phase 3)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def write_reports(run_result, route_decisions):
    """Write TXT and JSON reports derived from *run_result* and *route_decisions*.

    Parameters
    ----------
    run_result : dict
        RunResult dict as produced by pipeline.py.
    route_decisions : list[dict]
        Full RouteDecision list for per-object detail.

    Returns
    -------
    dict
        {'txt': <path or None>, 'json': <path or None>}
    """
    directory = _resolve_output_directory()
    expected_paths = {
        "txt": os.path.join(directory, config.REPORT_TXT_NAME),
        "json": os.path.join(directory, config.REPORT_JSON_NAME),
    }
    report_result = dict(run_result)
    report_result["report_paths"] = expected_paths

    txt_content = _format_txt_report(report_result, route_decisions)
    json_payload = _format_json_payload(report_result, route_decisions)

    txt_path = _write_file(directory, config.REPORT_TXT_NAME, txt_content, mode="w")
    json_path = _write_file(
        directory,
        config.REPORT_JSON_NAME,
        json.dumps(json_payload, indent=2, sort_keys=True),
        mode="w",
    )
    return {"txt": txt_path, "json": json_path}


# ---------------------------------------------------------------------------
# Internal helpers (stubs)
# ---------------------------------------------------------------------------

def _resolve_output_directory():
    """Return the best available output directory for reports.

    Priority: scene file directory > workspace directory > temp directory.

    """
    if cmds is not None:
        try:
            scene_path = cmds.file(query=True, sceneName=True)
        except Exception:
            scene_path = ""
        if scene_path:
            scene_directory = os.path.dirname(scene_path)
            if scene_directory:
                return scene_directory

        try:
            workspace_directory = cmds.workspace(query=True, rootDirectory=True)
        except Exception:
            workspace_directory = ""
        if workspace_directory:
            return workspace_directory

    return tempfile.gettempdir()


def _format_txt_report(run_result, route_decisions):
    """Return a formatted TXT string describing the full execution.

    """
    lines = [
        config.TOOL_NAME,
        "Schema version: {0}".format(config.REPORT_SCHEMA_VERSION),
        "Report generated: {0}".format(_timestamp()),
        "",
        "Execution",
        "---------",
        "Mode: {0}".format(run_result.get("execution_mode")),
        "Scope: {0}".format(run_result.get("scope_mode")),
        "Ignore string: {0}".format(run_result.get("ignore_string") or ""),
        "Success: {0}".format(run_result.get("success")),
        "Message: {0}".format(run_result.get("message") or ""),
        "",
        "Summary",
        "-------",
    ]

    summary = run_result.get("summary") or {}
    for key in sorted(summary):
        lines.append("{0}: {1}".format(key, summary[key]))

    warnings = run_result.get("warnings") or []
    lines.extend(["", "Warnings", "--------"])
    if warnings:
        lines.extend("- {0}".format(warning) for warning in warnings)
    else:
        lines.append("None")

    lines.extend(["", "Route Decisions", "---------------"])
    sorted_decisions = _sorted_route_decisions(route_decisions)
    if sorted_decisions:
        for decision in sorted_decisions:
            lines.append(
                "- {object_name} | route={route} | target={target_group} | "
                "can_move={can_move} | status={operation_status} | "
                "preflight={preflight} | reason={reason}".format(
                    **_txt_decision(decision)
                )
            )
    else:
        lines.append("No route decisions.")

    return "\n".join(lines) + "\n"


def _format_json_payload(run_result, route_decisions):
    """Return a JSON-serialisable dict for the full execution.

    """
    payload = {
        "tool": config.TOOL_NAME,
        "schema_version": config.REPORT_SCHEMA_VERSION,
        "generated_at": _timestamp(),
        "run_result": run_result,
        "route_decisions": _sorted_route_decisions(route_decisions),
    }
    return _json_safe(payload)


def _write_file(directory, filename, content, mode="w"):
    """Write *content* to *filename* inside *directory*.

    """
    try:
        if not os.path.isdir(directory):
            os.makedirs(directory)
        path = os.path.join(directory, filename)
        with open(path, mode, encoding="utf-8") as handle:
            handle.write(content)
        return path
    except OSError:
        return None


def _timestamp():
    """Return an ISO-like local timestamp for reports."""
    return datetime.now().replace(microsecond=0).isoformat()


def _txt_decision(decision):
    """Return text-safe defaults for one route decision."""
    return {
        "object_name": decision.get("object_name") or "",
        "route": decision.get("route") or "",
        "target_group": decision.get("target_group") or "",
        "can_move": decision.get("can_move"),
        "operation_status": decision.get("operation_status") or "",
        "preflight": _txt_preflight(decision),
        "reason": decision.get("reason") or "",
    }


def _txt_preflight(decision):
    """Return a compact preflight label for TXT route rows."""
    preflight = decision.get("apply_preflight") or {}
    if not preflight:
        return "n/a"
    return "eligible" if preflight.get("eligible") else "blocked"


def _json_safe(value):
    """Convert common values into JSON-safe containers."""
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _sorted_route_decisions(route_decisions):
    """Return route decisions in a stable output order."""
    return sorted(
        route_decisions or [],
        key=lambda item: (
            item.get("long_name") or "",
            item.get("route") or "",
            item.get("target_group") or "",
        ),
    )
