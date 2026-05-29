"""
mel_bridge.py
=============
Optional MEL hook execution module for the Maya Production Pipeliner.

Responsibility
--------------
Execute user-defined MEL procedures before and after the main pipeline run.
Hooks are entirely optional; their absence or failure must never interrupt
the pipeline.  All errors are captured and stored in mel_hook_status.

Rules
-----
- No pipeline logic may live in this module.
- Errors are caught, stored, and returned — never raised to the caller.
- This module is the only place where MEL is executed.

Dependencies
------------
- maya.mel  (Maya runtime; guarded import — safe outside Maya)

Public API
----------
    run_pre_hook(hook_name="") -> dict
        Execute the pre-run MEL hook and return a status dict.

    run_post_hook(hook_name="") -> dict
        Execute the post-run MEL hook and return a status dict.
"""

try:
    from maya import mel as maya_mel
except ImportError:
    maya_mel = None  # Running outside Maya; hooks will report not_configured.


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def run_pre_hook(hook_name=""):
    """Execute the optional pre-run MEL hook.

    Parameters
    ----------
    hook_name : str
        Name of the MEL procedure to call.  Empty string means no hook.

    Returns
    -------
    dict
        {'called': bool, 'success': bool, 'error': str or None}
    """
    if not hook_name:
        return {"called": False, "success": True, "error": None}
    success, error = _call_mel_procedure(hook_name)
    return {"called": True, "success": success, "error": error}


def run_post_hook(hook_name=""):
    """Execute the optional post-run MEL hook.

    Parameters
    ----------
    hook_name : str
        Name of the MEL procedure to call.  Empty string means no hook.

    Returns
    -------
    dict
        {'called': bool, 'success': bool, 'error': str or None}
    """
    if not hook_name:
        return {"called": False, "success": True, "error": None}
    success, error = _call_mel_procedure(hook_name)
    return {"called": True, "success": success, "error": error}


# ---------------------------------------------------------------------------
# Internal helpers (stubs)
# ---------------------------------------------------------------------------

def _call_mel_procedure(procedure_name):
    """Call a MEL procedure by name and return (success, error_string).

    """
    if maya_mel is None:
        return False, "Maya MEL runtime is not available."
    try:
        maya_mel.eval(procedure_name + "()")
        return True, None
    except Exception as exc:
        return False, str(exc)
