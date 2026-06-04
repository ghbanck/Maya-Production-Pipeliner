# Pipeline Overview

This document summarizes the intended pipeline shape and the module boundaries used by Maya Production Pipeliner.

For defensive rationale and safety framing, see [`defensive_design.md`](defensive_design.md).

## Pipeline Flow

```text
Maya scene
-> scanner
-> ObjectRecord facts
-> classifier
-> RouteDecision plan
-> Dry Run or Apply preflight
-> reporter
-> RunResult
```

The route plan is central. The tool should decide what it intends to do before any future scene mutation is allowed to happen.

## Current Implementation Boundary

Current validated slices support:

* scene scanning;
* route classification;
* Dry Run reporting;
* Apply preflight reporting without mutation;
* utility routing;
* unclear-case routing;
* manual validation slices recorded in the checklist.

Mutating Apply remains out of the current runtime.

## Implementation Status Snapshot

The repository is no longer only scaffold. The current state is better understood in three buckets:

### Runtime code already in use

* `scanner.py` performs real scene scanning;
* `classifier.py` produces real route decisions;
* `reporter.py` writes real TXT/JSON reports;
* `pipeline.py` runs the end-to-end Dry Run and Apply-preflight flow;
* `organizer.py` performs non-mutating Apply preflight checks;
* `config.py` defines the active constants and contracts used by runtime modules.

### Partial or scaffold-heavy modules

* `ui.py` implements the Phase 7 minimal UI; Dry Run and Apply Preflight flows smoke validated in Maya 2027.1;
* `launcher.py` is the intended entry point and smoke validated alongside `ui.py`;
* `mel_bridge.py` is isolated but still depends on broader optional-behavior validation;
* `install.py` is a setup helper, not the core runtime workflow.

### Planned but not implemented behavior

* mutating Apply;
* real Outliner reparenting/group creation as runtime Apply behavior;
* mutation outcomes such as `moved` and `failed_parenting`;
* UI flow for mutating Apply (depends on mutating Apply implementation).

## Module Responsibilities

```text
config.py      -> names, constants, modes, routes, and status values
scanner.py     -> reads scene facts and builds ObjectRecord data
classifier.py  -> creates RouteDecision data from factual records
organizer.py   -> runs Apply preflight today; future mutation boundary
reporter.py    -> writes TXT/JSON reports
pipeline.py    -> orchestrates scan, classify, organize, report, RunResult
ui.py          -> lightweight Maya-facing interface
launcher.py    -> public launch entry point
mel_bridge.py  -> isolates optional MEL compatibility hooks
```

## Output Group Model

The architecture targets a readable Outliner structure rooted under:

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

This is the intended output structure for future Safe Apply, not a claim that object movement is already implemented.

Ignored content matched by the user-defined ignore string should be preserved outside the normal organized output buckets unless a future contract explicitly says otherwise.

## Architecture Graph

The current visual architecture graph is included here:

![Pipeline Graph](./pipeline-graph.png)

Use the graph as a visual overview. Treat implementation status as tracked separately by the checklist, planning docs, and current runtime code.
