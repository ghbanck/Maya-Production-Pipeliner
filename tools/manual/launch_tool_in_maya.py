"""
launch_tool_in_maya.py
======================
Paste into the Maya Script Editor (Python tab) or add as a shelf button.

Resolves the repo root from this file's location, adds it to sys.path,
reloads ui and launcher so edits are picked up without restarting Maya,
then opens the tool window.
"""
import sys
from pathlib import Path

# Repo root is two levels up from tools/manual/
_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import importlib
import maya_production_pipeliner.ui as _ui
import maya_production_pipeliner.launcher as _launcher

importlib.reload(_ui)
importlib.reload(_launcher)

_launcher.launch()
