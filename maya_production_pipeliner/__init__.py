"""
Maya Production Pipeliner
=========================
A lightweight, Maya-native Python utility for organizing scene content
into readable production handoff groups.

Before validation, production needs readable structure.

Public entry point
------------------
    from maya_production_pipeliner import launcher
    launcher.launch()

Modules
-------
config      — Constants, group names, scope/execution modes and defaults.
scanner     — Scene scanning; produces ObjectRecord data only.
classifier  — Route decisions; produces RouteDecision data only.
organizer   — Apply-mode scene mutations; consumes RouteDecision data.
reporter    — TXT/JSON report writing; does not modify the scene.
mel_bridge  — Optional isolated MEL hook execution.
pipeline    — Coordinates all modules; returns RunResult.
ui          — Maya-native UI; reads RunResult only.
launcher    — Public launch() entry point.
"""

__all__ = ["launcher"]
