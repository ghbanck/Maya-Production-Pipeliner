# Usage

This document describes the public usage model for Maya Production Pipeliner without overstating current implementation maturity.

For frozen scope authority, see [`docs/planning/frozen_scope_contract_v1.1.3.md`](planning/frozen_scope_contract_v1.1.3.md).

## Maturity Note

Current usage maturity is mixed:

* Dry Run is real runtime behavior and has focused manual validation evidence.
* Apply currently means non-mutating preflight, not scene reorganization.
* The minimal UI is implemented and smoke validated in Maya 2027.1 for Dry Run and Apply Preflight; installation maturity should still be treated conservatively.

## Working Model

The tool is intended to help artists and technical users understand scene organization before deeper downstream work begins.

High-level flow:

```text
scan scene facts
-> classify route decisions
-> preserve unsafe content
-> preview through Dry Run or Apply preflight
-> review TXT/JSON reports
```

## Scope Modes

### All Scene

Scans all transform candidates in the current Maya scene.

### Selected

Scans only the currently selected candidates, normalizing shapes or child selections to transforms when practical.

### Visible

Scans candidates that Maya reports as visible, then applies additional resolved-visibility checks where implemented.

## Execution Modes

### Dry Run

Dry Run is the current read-only execution path.

Expected behavior:

* collects scene facts;
* classifies route decisions;
* writes reports;
* returns a lightweight `RunResult`;
* does not create, parent, rename, delete, or otherwise mutate scene nodes.

### Apply

Apply is currently implemented as non-mutating preflight.

Current behavior:

* evaluates whether route decisions would be eligible for future Apply;
* annotates decisions with preflight eligibility and reasons;
* keeps `did_move = false` and `new_long_name = None`;
* writes reports describing the preflight outcome;
* does not mutate the Maya scene.

Future mutating Apply is planned separately and remains gated by documented safety contracts.

## Ignore String

The ignore string is a user-defined preservation hint.

Current intent:

* matching objects should not be treated as normal production routing candidates;
* matching objects remain explicit and reportable;
* matching objects are preserved outside the normal organized output groups by default;
* broad ignore usage can generate warnings when the match count becomes suspiciously high.

## Planned Output Structure

When Safe Apply is eventually implemented, the intended output root is:

```text
Pipeline_Organized
```

Planned child groups:

```text
Production_Meshes
Scene_Utilities
References
Review_MissingMaterial
Review_MultiMaterial
Review_UnclearCases
```

This structure should be treated as target architecture, not as evidence that mutating Apply is already available.

Ignored content matched by the user-defined ignore string should be bypassed/preserved rather than treated as its own organized class by default.

## Launch Note

Current intended launch pattern:

```python
from maya_production_pipeliner import launcher
launcher.launch()
```

Treat this as the intended public entry point while installation and UI maturity continue to evolve.
