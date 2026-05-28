"""
install.py
==========
Installation helper placeholder for the Maya Production Pipeliner.

Current status
--------------
This file is part of the initial repository scaffold. The installation helper
is not implemented yet and intentionally raises NotImplementedError.

Planned usage
-------------
When implemented, this helper is intended to be runnable from the Maya Script
Editor (Python tab)::

    import runpy
    runpy.run_path("/path/to/maya_production_pipeliner/install.py")

It may also support execution from the system Python shipped with Maya::

    mayapy install.py

Planned behavior
----------------
1. Locate the user's Maya scripts directory in a platform-aware way.
2. Register the package directory on Maya's Python path for the current user.
3. Print a confirmation message with the registered path.

The helper is intended to avoid copying files, modifying system directories,
or requiring admin rights.
"""

import os
import platform
import sys


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def install():
    """Register the package directory in the Maya user scripts path.

    TODO: Phase 9 (hardening) — implement platform-aware Maya scripts
    directory lookup, write userSetup.py sys.path entry or .pth file,
    and verify the package is importable after registration.
    """
    raise NotImplementedError("install() is not yet implemented.")


# ---------------------------------------------------------------------------
# Internal helpers (stubs)
# ---------------------------------------------------------------------------

def _find_maya_scripts_dir():
    """Return the platform-appropriate Maya user scripts directory path.

    TODO: Phase 9 — handle Windows (%USERPROFILE%/Documents/maya/<ver>/scripts),
    macOS (~/Library/Preferences/Autodesk/maya/<ver>/scripts), and
    Linux (~/.maya/<ver>/scripts).
    """
    raise NotImplementedError


def _register_path(scripts_dir, package_parent_dir):
    """Append sys.path registration to userSetup.py inside *scripts_dir*.

    TODO: Phase 9 — avoid duplicate entries; create userSetup.py if absent.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Script entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    install()
