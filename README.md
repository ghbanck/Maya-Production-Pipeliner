<h1 align="center">Maya Production Pipeliner</h1>

<p align="center">
  <strong>Safety-aware Maya scene organization for production handoff</strong>
</p>

<p align="center">
  A lightweight, Maya-native Python utility being built to turn messy scene hierarchies into readable production handoff structure.
</p>

<p align="center">
  <em>Before validation, production needs readable structure.</em>
</p>

---

## Overview

Maya Production Pipeliner is a production-oriented Maya Python tool currently being implemented in small, controlled vertical slices.

The project focuses on one practical production problem: Maya scenes often become hard to read before they become technically invalid. Production meshes, utilities, references, review cases, ignored content, rig-sensitive objects, instanced geometry, material issues, duplicate names, hidden visibility states, and previous tool output can all live together in the same Outliner.

This tool is being built to make that first layer readable before deeper validation, export, review, or downstream handoff begins.

The planned workflow is:

```text
Scan scene facts
-> classify objects
-> build a route plan
-> preserve unsafe content
-> preview with Dry Run
-> apply only safe changes
-> write traceable reports
```

This is not intended to be a full validation framework, exporter, rig validator, material fixer, publisher, or studio pipeline replacement. It is a small production utility for scene organization, route planning, preservation, review grouping, and reportable handoff structure.

The project favors explicit limitations and conservative behavior over broad automation. Future mutating behavior is expected to be documented and gated before implementation.

---

## At a Glance

| Area                   | Description                                                           |
| ---------------------- | --------------------------------------------------------------------- |
| Tool type              | Maya Python production utility                                        |
| Main purpose           | Scene organization for production handoff                             |
| Primary users          | Technical artists, pipeline artists, 3D artists, production reviewers |
| Main value             | Readable scene structure before validation, export, or handoff        |
| DCC target             | Autodesk Maya                                                         |
| API layer              | `maya.cmds`                                                           |
| Optional compatibility | Isolated MEL bridge                                                   |
| Current status         | Scaffold / implementation in progress                                 |
| Scope status           | v1.1.3 Final Hardened scope locked                                    |
| License                | MIT                                                                   |

---

## Current Status

This project is in its initial implementation phase.

A module should only be considered functional when its implementation and manual test evidence exist in the repository. Documentation may describe planned behavior, but planned behavior should not be treated as verified runtime behavior until the corresponding code and tests are present.

| Area                    | Status                               |
| ----------------------- | ------------------------------------ |
| Frozen scope            | Locked                               |
| Repository scaffold     | In progress                          |
| Maya package structure  | Scaffold                             |
| Import safety           | Required before functional milestone |
| Data contracts          | Initial                              |
| TXT/JSON reporter       | Initial Dry Run output               |
| Scene scanner           | Early implementation                 |
| Safety-aware classifier | Early implementation                 |
| Dry Run pipeline        | Early implementation                 |
| Maya UI                 | Planned                              |
| Safe Apply organizer    | Planned / gated                      |
| Validation and release polish | Planned                        |

---

## Why It Exists

Scene organization is not glamorous, but it is where production risk starts becoming visible.

A Maya scene may contain final meshes, old test assets, cameras, lights, locators, joints, referenced content, instanced geometry, skinned meshes, blend shapes, hidden objects, display layers, default material assignments, multi-material objects, namespaced assets, duplicate short names, and previous tool output.

Before anyone can validate, export, review, or hand off that scene, the team needs to understand what is safe, what needs review, what is referenced, what should be preserved, and what actually changed.

Maya Production Pipeliner is designed to solve that first step: readable production structure before deeper validation begins.

---

## Core Goals

* Make Maya scene structure easier to read before handoff.
* Separate production meshes, utilities, references, review cases, and ignored content.
* Preview route decisions before modifying the scene.
* Move only objects cleared by a conservative safety gate.
* Preserve referenced, instanced, rig/deformer-sensitive, or unclear-unsafe content by default.
* Generate TXT/JSON reports that describe what was planned, moved, preserved, skipped, or left for review.
* Keep the UI lightweight by using `RunResult` summaries instead of rendering full object-level route lists.
* Keep the implementation small, modular, Maya-native, and public-repo friendly.

---

## Planned v0.1.0 Behavior

The v1.1.3 frozen scope defines a small Maya production utility that will:

* scan scene content by scope: **All Scene**, **Selected**, or **Visible**;
* classify objects into production handoff routes;
* build a route plan before any scene modification;
* support **Dry Run** before **Apply**;
* use a safety gate before moving objects;
* define safe Apply behavior before scene mutation is implemented;
* preserve referenced, instanced, rig-sensitive, or unclear-unsafe content;
* preserve user-defined ignored content through an editable ignore string;
* route material and unclear cases into review groups;
* organize movable objects into predictable Outliner groups;
* generate traceable TXT and JSON reports;
* return lightweight `RunResult` feedback to the UI;
* support optional MEL hooks through an isolated compatibility bridge.

This behavior is the planned implementation target. Current implementation status is tracked above.

---

## Core Workflow

```text
Maya Scene
   |
   v
Scanner
   |
   v
ObjectRecord cache
   |
   v
Classifier + safety gate
   |
   v
RouteDecision plan
   |
   v
Dry Run report or safe Apply
   |
   v
RunResult summary + TXT/JSON reports
```

The route plan is central. Even in Apply mode, the tool should first decide what it intends to do, then execute only the safe subset of that plan.

Dry Run is always observational and non-mutating. Apply is planned as a gated execution of an existing route plan, not as an opportunity to classify or improvise movement while mutating the scene.

> Facts before routing. Route plan before scene changes. Reports before trust.

---

## Design Principles

* **Preserve first.**
* **Dry Run before Apply.**
* **Facts before routing.**
* **Route plan before scene changes.**
* **Reports before trust.**
* **Readable structure before validation.**
* **When safety and convenience conflict, choose preservation.**

---

## Defensive Design

Maya scene organization can become unsafe when a tool assumes every object can be freely moved.

This project was planned around common Maya production risks before implementation: immutable references, instancing, rigs, deformers, long-name mutation after parenting, duplicate short names, hierarchy depth, display-layer visibility, previous tool output, parent/child selection conflicts, heavy scene UI feedback, and report/UI coupling.

The v1.1.3 design includes:

* report-only behavior for referenced nodes;
* preservation rules for instanced geometry;
* preservation rules for rig/deformer-sensitive content;
* review routing for default material and multi-material cases;
* explicit routing for unclear cases;
* `can_move` as the movement gate;
* `preserve_reason` for reportable preservation;
* `new_long_name` tracking after parenting operations;
* explicit `operation_status` values;
* idempotent repeated execution;
* limited `RunResult.preview_routes` for responsive UI behavior;
* resolved scene visibility for Visible scope where practical;
* optional MEL hooks isolated from the core Python workflow.

The detailed architecture rationale lives in [`docs/architecture/defensive_design.md`](docs/architecture/defensive_design.md).

The authoritative scope contract lives in [`docs/planning/frozen_scope_contract_v1.1.3.md`](docs/planning/frozen_scope_contract_v1.1.3.md). It defines mutation boundaries, Safe Move expectations, Apply failure policy, reporting contracts, and explicit limitations.

---

## Planned Output Groups

Apply mode is scoped to create or reuse a root group:

```text
Pipeline_Organized
```

Inside it, the planned child groups are:

```text
Production_Meshes
Scene_Utilities
References
Review_MissingMaterial
Review_MultiMaterial
Review_UnclearCases
Bypass
```

These groups are designed to make the Outliner readable at handoff time.

`Bypass` is reserved for explicit user ignore-string intent. It is not a generic ambiguity bucket.

`Review_UnclearCases` is reserved for safe-to-move ambiguous content. Unsafe unclear content remains preserved/report-only.

---

## Architecture Overview

The project is structured around separated responsibilities:

```text
scanner.py      -> reads Maya scene data and builds object records
classifier.py   -> evaluates records and creates route decisions
organizer.py    -> applies safe route decisions in Apply mode
reporter.py     -> writes TXT/JSON reports
pipeline.py     -> orchestrates scan -> classify -> organize/report
ui.py           -> provides a lightweight Maya interface
launcher.py     -> exposes the public launch entry point
mel_bridge.py   -> isolates optional MEL compatibility hooks
config.py       -> centralizes names, defaults, modes, and constants
```

The architecture separates scene reading, decision-making, scene mutation, reporting, and UI feedback. This keeps the tool easier to review, test, and harden.

---

## Key Data Concepts

The project is designed around three lightweight data concepts.

### `ObjectRecord`

A cached description of what the scanner found in the Maya scene.

Planned fields include object identity, long name, transform node, shape nodes, type, material state, namespace, visibility state, reference state, instance state, rig/deformer indicators, tool-output state, and warnings.

### `RouteDecision`

A classifier output describing what should happen to an object.

Planned fields include route, target group, reason, warnings, `can_move`, `report_only`, `preserve_reason`, `would_move`, `did_move`, `new_long_name`, and `operation_status`.

### `RunResult`

A lightweight execution summary for the UI and launcher.

Planned fields include summary, warnings, report paths, execution mode, scope mode, ignore string, route decision count, preview routes, maximum preview item count, and success message.

Full object-level details belong in TXT/JSON reports, not in the UI.

---

## Operation Status Model

The Apply workflow is designed to record explicit operation states instead of vague success/failure language.

Planned status values include:

```text
planned
dry_run_only
moved
already_in_target
preserved_report_only
skipped_reference
skipped_instance
skipped_sensitive_hierarchy
skipped_tool_structure
skipped_missing_node
failed_parenting
```

This is intended to make reports easier to audit and safer for future pipeline integration.

---

## Planned Report Data

TXT and JSON reports are part of the planned workflow.

Reports are intended to make each run traceable by recording:

* tool name;
* timestamp;
* execution mode;
* scope mode;
* ignore string;
* scanned object count;
* classification summary;
* route decisions;
* target groups;
* safety state;
* preservation reasons;
* report-only state;
* operation status;
* `new_long_name` when relevant;
* visibility resolution fields when relevant;
* warnings;
* MEL hook status when used;
* report paths.

JSON reports are planned to use explicit schema/version semantics before the format is treated as integration-stable. Warning fields are expected to mature toward stable categories or codes for testing and filtering.

Report path fallback should follow this order:

```text
saved scene directory
-> Maya workspace directory
-> user-safe temp fallback
```

Example reports may be included before the reporter is fully implemented and should be treated as format previews until generated by the tool.

---

## Development Roadmap

The repository is being built in vertical slices.

| Phase              | Goal                                                 |
| ------------------ | ---------------------------------------------------- |
| Phase 1            | Repository scaffold                                  |
| Import safety      | Import-safe scaffold modules                         |
| Phase 2            | Data contracts and configuration                     |
| Phase 3            | TXT/JSON reporter                                    |
| Phase 4            | Scene scanner                                        |
| Phase 5            | Safety-aware classifier                              |
| Phase 6            | Dry Run pipeline                                     |
| Phase 7            | Minimal Maya UI and launcher                         |
| Phase 8            | Safe Apply organizer                                 |
| Phase 9            | Hardening, examples, screenshots, and release polish |

The first functional milestone is the **Dry Run vertical slice**:

```text
scan a simple scene
-> classify route decisions
-> return lightweight RunResult
-> write TXT/JSON reports
-> make no scene modifications
```

Apply work is intentionally gated behind documented safety contracts, including Safe Move rules, deterministic ordering, long-name mutation handling, failure policy, and manual test evidence.

The full implementation plan is documented in [`docs/planning/implementation_plan.md`](docs/planning/implementation_plan.md).

---

## Repository Layout

```text
maya_production_pipeliner/
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
    planning/
        project_bible_v1.1.3.md
        frozen_scope_contract_v1.1.3.md
        implementation_plan.md
    architecture/
        defensive_design.md
    testing/
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

## Documentation

The documentation is split between public overview, planning, architecture, and testing.

| Document                                                                                         | Purpose                                                       |
| ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------- |
| [`docs/planning/project_bible_v1.1.3.md`](docs/planning/project_bible_v1.1.3.md)                 | Product rationale, technical context, and development intent  |
| [`docs/planning/frozen_scope_contract_v1.1.3.md`](docs/planning/frozen_scope_contract_v1.1.3.md) | Scope authority, data semantics, safety rules, and boundaries |
| [`docs/planning/implementation_plan.md`](docs/planning/implementation_plan.md)                   | Build phases, delivery order, and implementation milestones   |
| [`docs/architecture/defensive_design.md`](docs/architecture/defensive_design.md)                 | Defensive architecture and pre-implementation risk review     |
| [`docs/testing/manual_test_checklist.md`](docs/testing/manual_test_checklist.md)                 | Manual validation checklist for implementation slices         |

---

## Installation

> **Note:** Functional installation and launch instructions will be finalized as implementation lands.

Planned manual setup:

1. Clone or download this repository.
2. Add the repository root to Maya's Python path using `userSetup.py`, a `.pth` file, or another local Maya path setup.
3. Open Maya and run the launcher from the Script Editor.

Planned launch pattern:

```python
from maya_production_pipeliner import launcher
launcher.launch()
```

This command should be treated as the intended launch interface until verified by implementation and manual testing.

The `install.py` file is a setup/helper script, not the same thing as the implementation plan. The implementation plan documents build phases and project execution; `install.py` belongs to the code/scaffold side of the repository.

---

## Current Limitations

This repository is currently in scaffold / implementation phase.

The tool is not yet a finished Maya utility. Features described in the planned scope should not be treated as implemented until the corresponding modules and manual test results are present.

The project is focused on scene organization for production handoff. It does not replace full asset validation, export validation, publishing, rig repair, material fixing, dependency management, database integration, or broad studio pipeline systems.

The current scope does not guarantee corrupted reference recovery, rig correctness validation, shader graph validation, namespace conflict resolution, animation semantic correctness, resumable execution, historical replay, telemetry, or generalized pipeline runtime behavior.

---

## Rights and Notice

Designed and developed by **Gustavo Henrique Banck**.

This is a public development repository for a Maya production tooling project. Implementation status is tracked openly as the tool is built in vertical slices.

---

## License

MIT License. See [LICENSE](LICENSE).
