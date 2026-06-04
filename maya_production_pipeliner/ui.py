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

import os
import subprocess
import sys

try:
    import maya.cmds as cmds
except ImportError:
    cmds = None  # Running outside Maya; stubs will raise NotImplementedError.

from maya_production_pipeliner import config, pipeline


# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_WINDOW_ID = "MayaProductionPipelinerWindow"

_ctrl = {}  # Widget path registry — populated by show(), read by callbacks.


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def show():
    """Build and display the Maya Production Pipeliner window.

    Creates a new window or raises the existing one.  Keeps UI state
    (scope, execution mode, ignore string) between calls within the same
    Maya session.
    """
    if cmds is None:
        raise RuntimeError("maya.cmds is not available outside Maya.")

    if cmds.window(_WINDOW_ID, exists=True):
        cmds.showWindow(_WINDOW_ID)
        return

    cmds.window(
        _WINDOW_ID,
        title="Maya Production Pipeliner",
        widthHeight=(500, 720),
        sizeable=True,
    )
    cmds.columnLayout(adjustableColumn=True, rowSpacing=6)

    # -- Scope ----------------------------------------------------------------
    cmds.frameLayout(label="Scope", collapsable=False,
                     marginWidth=6, marginHeight=4)
    cmds.columnLayout(adjustableColumn=True)
    _ctrl["scope"] = cmds.radioButtonGrp(
        numberOfRadioButtons=3,
        labelArray3=["All Scene", "Selected", "Visible"],
        select=1,
    )
    cmds.setParent("..")
    cmds.setParent("..")

    # -- Execution Mode -------------------------------------------------------
    # "Apply Preflight" label reflects that mutating Apply is not yet active;
    # pipeline runs apply_routes() read-only and reports planned moves.
    cmds.frameLayout(label="Execution Mode", collapsable=False,
                     marginWidth=6, marginHeight=4)
    cmds.columnLayout(adjustableColumn=True)
    _ctrl["mode"] = cmds.radioButtonGrp(
        numberOfRadioButtons=2,
        labelArray2=["Dry Run", "Apply"],
        select=1,
    )
    cmds.setParent("..")
    cmds.setParent("..")

    # -- Ignore String --------------------------------------------------------
    cmds.frameLayout(label="Ignore String", collapsable=False,
                     marginWidth=6, marginHeight=4)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=2)
    cmds.text(label="Preserve objects whose name contains:", align="left")
    _ctrl["ignore"] = cmds.textField(placeholderText="e.g. BYPASS")
    cmds.setParent("..")
    cmds.setParent("..")

    # -- Run ------------------------------------------------------------------
    cmds.button(label="Run", height=36, command=_on_run_clicked)

    # -- Results --------------------------------------------------------------
    cmds.frameLayout(label="Results", collapsable=False,
                     marginWidth=6, marginHeight=4)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=2)

    _ctrl["message"] = cmds.text(
        label="(run pipeline to see results)", align="left", wordWrap=True)
    _ctrl["summary"] = cmds.text(label="", align="left", wordWrap=True)

    cmds.separator(height=4, style="none")
    cmds.text(label="Warnings:", align="left")
    _ctrl["warnings"] = cmds.scrollField(
        editable=False, wordWrap=True, height=70, text="")

    cmds.separator(height=4, style="none")
    cmds.text(label="Reports:", align="left")
    _ctrl["txt_path_text"] = cmds.text(label="", align="left", wordWrap=True)
    _ctrl["txt_btn"] = cmds.button(
        label="Open TXT Report",
        enable=False,
        command=lambda *a: _on_open_report_clicked(_ctrl.get("_txt_path", "")),
    )
    _ctrl["json_path_text"] = cmds.text(label="", align="left", wordWrap=True)
    _ctrl["json_btn"] = cmds.button(
        label="Open JSON Report",
        enable=False,
        command=lambda *a: _on_open_report_clicked(_ctrl.get("_json_path", "")),
    )

    cmds.separator(height=4, style="none")
    _ctrl["preview_label"] = cmds.text(label="Preview:", align="left")
    _ctrl["preview"] = cmds.scrollField(
        editable=False, wordWrap=False, height=130, text="")

    cmds.setParent("..")
    cmds.setParent("..")

    cmds.showWindow(_WINDOW_ID)


# ---------------------------------------------------------------------------
# Internal callbacks
# ---------------------------------------------------------------------------

def _on_run_clicked(*args):
    """Read UI controls, call pipeline.run(), and update the result display."""
    if cmds is None:
        raise RuntimeError("maya.cmds is not available outside Maya.")

    scope_index = cmds.radioButtonGrp(_ctrl["scope"], query=True, select=True)
    scope_mode = (config.ALL_SCENE, config.SELECTED, config.VISIBLE)[scope_index - 1]

    mode_index = cmds.radioButtonGrp(_ctrl["mode"], query=True, select=True)
    execution_mode = (config.DRY_RUN, config.APPLY)[mode_index - 1]

    ignore_string = cmds.textField(_ctrl["ignore"], query=True, text=True) or ""

    try:
        run_result = pipeline.run(scope_mode, execution_mode, ignore_string)
    except Exception as exc:
        _clear_result_display()
        cmds.text(_ctrl["message"], edit=True, label="ERROR: {0}".format(exc))
        return

    _update_result_display(run_result)


def _update_result_display(run_result):
    """Update the UI summary section from *run_result*.

    Reads only: summary, warnings, report_paths, preview_routes, message.
    Does not open or parse report files.
    """
    if cmds is None:
        raise RuntimeError("maya.cmds is not available outside Maya.")

    message = run_result.get("message") or ""
    cmds.text(_ctrl["message"], edit=True, label=message)

    summary = run_result.get("summary") or {}
    summary_line = (
        "Scanned: {scanned}  Planned: {planned}  "
        "Would Move: {would_move}  Preserved: {preserved}  "
        "Warnings: {warnings}  Failed: {failed}"
    ).format(
        scanned=summary.get("scanned", 0),
        planned=summary.get("planned", 0),
        would_move=summary.get("would_move", 0),
        preserved=summary.get("preserved", 0),
        warnings=summary.get("warnings", 0),
        failed=summary.get("failed", 0),
    )
    cmds.text(_ctrl["summary"], edit=True, label=summary_line)

    warnings = run_result.get("warnings") or []
    cmds.scrollField(
        _ctrl["warnings"], edit=True,
        text="\n".join(warnings) if warnings else "(no warnings)",
    )

    report_paths = run_result.get("report_paths") or {}
    txt_path = report_paths.get("txt") or ""
    json_path = report_paths.get("json") or ""
    _ctrl["_txt_path"] = txt_path
    _ctrl["_json_path"] = json_path
    cmds.text(_ctrl["txt_path_text"], edit=True,
              label=txt_path if txt_path else "(not written)")
    cmds.button(_ctrl["txt_btn"], edit=True, enable=bool(txt_path))
    cmds.text(_ctrl["json_path_text"], edit=True,
              label=json_path if json_path else "(not written)")
    cmds.button(_ctrl["json_btn"], edit=True, enable=bool(json_path))

    preview_routes = run_result.get("preview_routes") or []
    total = run_result.get("route_decisions_count", 0)
    shown = len(preview_routes)
    cmds.text(
        _ctrl["preview_label"], edit=True,
        label="Preview ({0} of {1}):".format(shown, total),
    )
    lines = [
        "{name}  ->  {group}  [{status}]".format(
            name=item.get("object_name", ""),
            group=item.get("target_group", ""),
            status=item.get("operation_status", ""),
        )
        for item in preview_routes
    ]
    cmds.scrollField(
        _ctrl["preview"], edit=True,
        text="\n".join(lines) if lines else "(no items)",
    )


def _clear_result_display():
    """Reset all result widgets to empty/disabled state.

    Called before showing a pipeline error so stale results are never
    presented as current.
    """
    cmds.text(_ctrl["message"], edit=True, label="")
    cmds.text(_ctrl["summary"], edit=True, label="")
    cmds.scrollField(_ctrl["warnings"], edit=True, text="")
    _ctrl["_txt_path"] = ""
    _ctrl["_json_path"] = ""
    cmds.text(_ctrl["txt_path_text"], edit=True, label="")
    cmds.button(_ctrl["txt_btn"], edit=True, enable=False)
    cmds.text(_ctrl["json_path_text"], edit=True, label="")
    cmds.button(_ctrl["json_btn"], edit=True, enable=False)
    cmds.text(_ctrl["preview_label"], edit=True, label="Preview:")
    cmds.scrollField(_ctrl["preview"], edit=True, text="")


def _on_open_report_clicked(path, *args):
    """Open a report file in the system default text viewer."""
    if not path:
        return
    if sys.platform == "win32":
        os.startfile(path)  # noqa: S606
    else:
        subprocess.Popen(["xdg-open", path])
