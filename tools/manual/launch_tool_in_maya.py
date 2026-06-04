"""
launch_tool_in_maya.py
======================
Paste into the Maya Script Editor (Python tab) or add as a shelf button.

If pasted directly, __file__ is not defined — set REPO_ROOT manually below.
If run as a file (shelf button pointing to this file), REPO_ROOT is resolved
automatically from the file location.
"""
import sys
import importlib

# Set this manually when pasting into the Script Editor.
# Leave as None when running as a file — it is resolved automatically.
# Example: REPO_ROOT = "C:/Projects/Maya-Production-Pipeliner"
REPO_ROOT = None

try:
    from pathlib import Path
    REPO_ROOT = str(Path(__file__).resolve().parents[2])
except NameError:
    pass  # __file__ not available; REPO_ROOT must be set above

if not REPO_ROOT:
    raise RuntimeError(
        "REPO_ROOT is not set. "
        "Set REPO_ROOT at the top of this script before running."
    )

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import maya_production_pipeliner.ui as _ui
import maya_production_pipeliner.launcher as _launcher

importlib.reload(_ui)
importlib.reload(_launcher)

_launcher.launch()
