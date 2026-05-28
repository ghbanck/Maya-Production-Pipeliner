"""
ui.py
=====
Maya-native UI for the Maya Production Pipeliner.

Responsibility
--------------
Collect user options (scope mode, execution mode, ignore string), call
pipeline.run(), and display the RunResult summary.  The UI must:

- Read only RunResult fields (summary, warnings, report_paths,
  preview_routes, message).
- Never parse TXT or JSON report files to determine execution state.
- Never call scanner, classifier, organizer, or reporter directly.
- Remain lightweight and responsive regardless of scene size.

Dependencies
------------
- maya.cmds  (Maya runtime; guarded import — safe outside Maya)
- pipeline   (run)
- config     (mode constants, MAX_UI_PREVIEW_ITEMS)

Public API
----------
    show() -> None
        Build and display the tool window.  Create a new window if none
        exists; reuse the existing one otherwise.
"""

try:
    import maya.cmds as cmds
except ImportError:
    cmds = None  # Running outside Maya; stubs will raise NotImplementedError.

from maya_production_pipeliner import config, pipeline  # noqa: F401


# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_WINDOW_ID = "MayaProductionPipelinerWindow"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def show():
    """Build and display the Maya Production Pipeliner window.

    Creates a new window or raises the existing one.  Keeps UI state
    (scope, execution mode, ignore string) between calls within the same
    Maya session.
    """
    # TODO: Phase 7 — implement window creation/reuse, layout controls,
    #       scope radio buttons, execution mode radio buttons, ignore string
    #       field, run button, and result summary section.
    raise NotImplementedError("ui.show() is not yet implemented.")


# ---------------------------------------------------------------------------
# Internal callbacks (stubs)
# ---------------------------------------------------------------------------

def _on_run_clicked(*args):
    """Read UI controls, call pipeline.run(), and update the result display.

    TODO: Phase 7 — gather scope_mode, execution_mode, ignore_string from
    controls, call pipeline.run(), pass RunResult to _update_result_display().
    """
    raise NotImplementedError


def _update_result_display(run_result):
    """Update the UI summary section from *run_result*.

    Reads only: summary, warnings, report_paths, message.
    Does not open or parse report files.

    TODO: Phase 7 — format and display counters, warnings, and report paths.
    """
    raise NotImplementedError


def _on_open_report_clicked(path, *args):
    """Open a report file in the system default text viewer.

    TODO: Phase 7 — use cmds.launchImageEditor or os.startfile/subprocess
    depending on platform.
    """
    raise NotImplementedError
