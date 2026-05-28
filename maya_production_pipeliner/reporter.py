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
    # TODO: Phase 3 — resolve output directory, format and write TXT report,
    #       serialise and write JSON report, return path dict.
    raise NotImplementedError("reporter.write_reports() is not yet implemented.")


# ---------------------------------------------------------------------------
# Internal helpers (stubs)
# ---------------------------------------------------------------------------

def _resolve_output_directory():
    """Return the best available output directory for reports.

    Priority: scene file directory > workspace directory > temp directory.

    TODO: Phase 3 — implement priority lookup using cmds.file and
    cmds.workspace, fall back to tempfile.gettempdir().
    """
    raise NotImplementedError


def _format_txt_report(run_result, route_decisions):
    """Return a formatted TXT string describing the full execution.

    TODO: Phase 3 — include header, summary counters, warnings, hook status,
    and per-object route detail.
    """
    raise NotImplementedError


def _format_json_payload(run_result, route_decisions):
    """Return a JSON-serialisable dict for the full execution.

    TODO: Phase 3 — mirror TXT content in structured form; ensure all values
    are JSON-safe (strings, ints, floats, bools, lists, dicts).
    """
    raise NotImplementedError


def _write_file(directory, filename, content, mode="w"):
    """Write *content* to *filename* inside *directory*.

    TODO: Phase 3 — handle IOError gracefully and return the full path or
    None on failure.
    """
    raise NotImplementedError
