"""
launcher.py
===========
Public entry point for the Maya Production Pipeliner.

Responsibility
--------------
Provide a single launch() function that initialises the tool window from
any Maya script, shelf button, or command line.  This module must not
contain pipeline logic; it delegates entirely to ui.show().

Usage
-----
From a Maya script editor or shelf button::

    from maya_production_pipeliner import launcher
    launcher.launch()

From a Maya Python command line::

    import maya_production_pipeliner.launcher as launcher
    launcher.launch()

Dependencies
------------
- ui  (show)
"""

from maya_production_pipeliner import ui


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def launch():
    """Initialise and display the Maya Production Pipeliner window.

    Safe to call multiple times within the same Maya session; the UI module
    handles window reuse.
    """
    # TODO: Phase 7 — confirm any required pre-flight checks (e.g. Maya
    #       version guard) then call ui.show().  Keep this function minimal.
    ui.show()
