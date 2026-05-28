# Maya Production Pipeliner

> **Before validation, production needs readable structure.**

A lightweight, Maya-native Python utility for organising scene content into
clean production handoff groups.

---

## What it does

Maya Production Pipeliner scans a Maya scene and routes each object to a
clearly named Outliner group based on its type, material state, and safety
profile.  It supports:

- **Scope modes** — All Scene, Selected, or Visible objects.
- **Dry Run** — read-only planning with full reports; nothing in the scene changes.
- **Apply** — safe, plan-first execution that moves only objects cleared by
  the route planner.
- **Ignore string** — user-defined pattern to preserve named objects in a
  `Bypass` group.
- **Output groups** — `Production_Meshes`, `Scene_Utilities`, `References`,
  `Review_MissingMaterial`, `Review_MultiMaterial`, `Review_UnclearCases`,
  `Bypass` inside a root `Pipeline_Organized` group.
- **Safety gates** — referenced nodes, instanced geometry, rig/deformer
  content, and ambiguous objects are preserved by default.
- **Idempotency** — repeated runs are safe; already-organised objects are
  detected and skipped.
- **Reports** — TXT and JSON reports written next to the scene file (or
  workspace / temp fallback).

---

## Installation

> **Note:** The installation helper is not yet implemented.  Manual setup
> instructions will be added in a later phase.

1. Clone or download this repository.
2. Add the repository root to Maya's Python path (via `userSetup.py` or a
   `.pth` file in your Maya scripts directory).
3. Open Maya and run the following in the Script Editor (Python tab):

```python
from maya_production_pipeliner import launcher
launcher.launch()
```

---

## Project status

This tool is **under active development**.  Modules are being implemented
phase by phase.  A module is considered functional only when its
implementation and manual test results exist in the repository.

| Module          | Status          |
|-----------------|-----------------|
| config.py       | Scaffold only   |
| scanner.py      | Scaffold only   |
| classifier.py   | Scaffold only   |
| organizer.py    | Scaffold only   |
| reporter.py     | Scaffold only   |
| mel_bridge.py   | Scaffold only   |
| pipeline.py     | Scaffold only   |
| ui.py           | Scaffold only   |
| launcher.py     | Scaffold only   |
| install.py      | Scaffold only   |

---

## Repository layout

```
maya_production_pipeliner/   ← Python package
    __init__.py
    config.py
    scanner.py
    classifier.py
    organizer.py
    reporter.py
    mel_bridge.py
    pipeline.py
    ui.py
    launcher.py
docs/
    manual_test_checklist.md
examples/
    example_report.txt
    example_report.json
install.py
README.md
LICENSE
.gitignore
```

---

## License

See [LICENSE](LICENSE).
