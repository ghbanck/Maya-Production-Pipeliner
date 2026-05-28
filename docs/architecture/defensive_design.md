# Defensive Design - Maya Production Pipeliner

> Before validation, production needs readable structure.

## Purpose

This document describes the defensive architecture behind Maya Production Pipeliner.

It consolidates the pre-implementation risk review and the final design decisions used to protect the v1.1.3 scope from common Maya runtime problems.

The goal is not to describe a large validation framework. The goal is to explain why this small scene organization utility is structured around scanning facts, classifying safely, building a route plan, applying only safe changes, and leaving traceable reports.

## Design Thesis

Maya scene organization can become unsafe when a tool assumes every object can be freely moved.

A production scene can contain referenced content, instanced geometry, rigged meshes, deformers, display layers, hidden hierarchy states, duplicate short names, material review cases, utility nodes, previous tool output, and content that should be preserved by explicit user intent.

Maya Production Pipeliner is designed around a defensive flow:

```text
Maya Scene Graph
-> Scanner
-> ObjectRecord cache
-> Classifier + safety gate
-> RouteDecision plan
-> Organizer
-> RunResult + TXT/JSON reports
```

This separation keeps reading, decision-making, scene mutation, UI feedback, and disk reporting isolated.

---

## Architectural Model

The pipeline follows a separated-responsibility model.

| Layer      | Responsibility                                                              |
| ---------- | --------------------------------------------------------------------------- |
| Scanner    | Reads the Maya scene and creates factual `ObjectRecord` data                |
| Classifier | Applies routing priority, safety gates, and creates `RouteDecision` records |
| Organizer  | Executes the route plan in Apply mode, moving only safe objects             |
| Reporter   | Writes TXT/JSON reports from the result data                                |
| Pipeline   | Orchestrates scan, classify, organize, report, and `RunResult` generation   |
| UI         | Displays lightweight feedback from `RunResult` only                         |

The UI and launcher should call the pipeline. They should not call scanner, classifier, organizer, or reporter directly in a coupled way.

---

## Pre-implementation Risk Review

The v1.1.3 planning phase identified runtime risks that are common in Maya production scenes.

The most important risks were:

* default material state being mistaken for valid production material;
* multi-material assignments requiring review instead of automated fixes;
* rig/deformer-sensitive objects being parented unsafely;
* referenced nodes being treated as local mutable nodes;
* instanced geometry being moved as if it were ordinary mesh content;
* long names changing after `cmds.parent`;
* duplicate short names losing traceability after movement;
* hierarchy depth being misread by simple string length;
* display-layer visibility contradicting direct node visibility;
* previous `Pipeline_Organized` output causing nested duplicate groups;
* heavy scenes freezing the UI through full route-list rendering;
* UI feedback depending on report-file parsing.

The defensive design turns those risks into explicit rules, fields, statuses, and tests.

---

## Scanner: Facts Only

`scanner.py` collects facts about objects in scope. It must not decide routes and must not modify the scene.

Expected scanner responsibilities include:

* resolving scope: All Scene, Selected, or Visible;
* normalizing selected shapes, components, or child nodes into processable transform candidates when practical;
* building object records;
* recording long names and short names;
* collecting shape nodes and node types;
* detecting mesh state;
* collecting material data;
* detecting default material assignment;
* detecting multi-material assignment;
* detecting referenced nodes;
* detecting instanced geometry;
* detecting rig/deformer indicators;
* detecting whether an object is inside previous tool output;
* detecting whether an object is a structural group created by the tool;
* resolving visibility for Visible scope;
* recording warnings.

Scanner output should remain JSON-safe. It should store names, strings, booleans, lists, dictionaries, and simple values, not live Maya objects.

---

## Classifier: Route Decisions Only

`classifier.py` evaluates each `ObjectRecord` and creates a `RouteDecision`.

It applies classification priority and conservative safety gates.

Classification priority:

1. Internal tool structural groups.
2. User ignore string.
3. Referenced or locked content.
4. Instanced geometry.
5. Rig/deformer-sensitive content.
6. Scene utilities.
7. Material review cases.
8. Production meshes.
9. Unclear cases.

The classifier must not modify the scene.

---

## Organizer: Scene Mutation Only in Apply

`organizer.py` executes the route plan in Apply mode.

It should:

* create or reuse `Pipeline_Organized`;
* create or reuse required child groups;
* move only transform candidates with `can_move = true`;
* preserve report-only objects;
* validate node existence before movement;
* avoid destructive parent/child conflicts;
* detect objects already in the correct destination;
* update `new_long_name` after parenting;
* set `did_move`;
* set `operation_status`;
* record warnings when movement cannot be completed safely.

The organizer should not reclassify objects. It executes the plan produced by the classifier.

---

## Output Layer: RunResult and Reports

The output layer has two different responsibilities.

`RunResult` is lightweight in-memory feedback for UI and launcher.

TXT/JSON reports contain full object-level details for review and debugging.

The UI should use only `RunResult` fields such as:

```text
summary
warnings
report_paths
route_decisions_count
preview_routes
message
success
```

The UI should not parse TXT/JSON reports to determine state, and it should not render every route decision in heavy scenes.

---

## Material Review Safety

### Default or Missing Material

In Maya, missing material should not be detected only by checking for no material connection.

A mesh connected directly to `initialShadingGroup` is treated as a review case.

Expected route:

```text
Review_MissingMaterial
```

This is a handoff review route, not an automatic fix.

### Multi-material

Objects with multiple shadingEngine connections are routed to:

```text
Review_MultiMaterial
```

The tool should not attempt to split meshes, fix material assignments, or alter shading. Multi-material cases are recorded for manual review.

---

## Rig and Deformer Safety

Objects with rig or deformer indicators are preserved by default.

Common indicators include:

* `skinCluster` history;
* `blendShape` history;
* parent joint;
* sensitive hierarchy conditions.

Expected behavior:

```text
can_move = false
report_only = true
operation_status = skipped_sensitive_hierarchy
```

The tool should preserve local hierarchy integrity over convenience.

---

## Reference Safety

Referenced nodes are immutable by default.

Expected route decision:

```text
route = "References"
can_move = false
report_only = true
preserve_reason = "Immutable reference node"
did_move = false
operation_status = skipped_reference
```

The organizer must not call `parent` on referenced nodes.

If the user selects a child node inside a reference, it must still be classified as referenced/report-only and preserved.

---

## Instanced Geometry Safety

Instanced geometry is preserved by default.

Moving or reorganizing instances as ordinary meshes can damage shape-sharing assumptions or produce misleading reports.

Expected behavior:

```text
can_move = false
report_only = true
operation_status = skipped_instance
```

---

## Long-name Mutation

Maya long names change after reparenting.

Any Apply workflow that relies on long names collected during scanning must account for path mutation.

Organizer rules:

* validate node existence before movement;
* execute parenting only on a current valid identifier;
* capture the return value of `cmds.parent` when available;
* store the resulting path in `new_long_name`;
* record `operation_status`;
* set `did_move = false` and add a warning if movement fails.

---

## Duplicate Names and Hierarchy Depth

Maya allows duplicate short names under different parents.

The tool should use long names to preserve identity and traceability.

Movement order should not rely on raw string length. When hierarchy depth matters, depth should be determined through Maya path separators:

```text
|
```

This helps avoid processing a long-named shallow node before a deeply nested node.

---

## Visible Scope Resolution

Visible scope must not rely only on direct `node.visibility`.

A visible object can be hidden through a parent hierarchy state or display layer. A direct visibility attribute can therefore be misleading.

The Visible scope design should consider:

* direct node visibility;
* hierarchy visibility;
* display-layer visibility when available;
* shape visibility when relevant;
* native Maya visibility confirmation when practical.

Resolved visibility should be cached where practical to avoid heavy repeated hierarchy queries.

Viewport isolate select is not the authoritative visibility source for v1.1.3.

---

## Previous Tool Output and Idempotency

The tool must be safe to run repeatedly.

`Pipeline_Organized` and its structural child groups are tool infrastructure. They should not be routed as production content.

However, leaf objects already inside `Pipeline_Organized` may be rescanned and reclassified after user edits.

This allows a user to fix a material, rerun the tool, and have the object move to the correct review or production bucket when safe.

Repeated execution should avoid:

* duplicate `Pipeline_Organized` roots;
* nested duplicate tool groups;
* moving objects already in the correct target;
* blocking useful reclassification of leaf objects.

Expected status for an already-correct object:

```text
operation_status = already_in_target
```

---

## Heavy Scene UI Safety

Large Maya scenes can include thousands of objects.

The UI should not attempt to render complete object-level route lists.

The design uses `RunResult` to keep UI feedback lightweight:

```text
route_decisions_count
summary
warnings
report_paths
preview_routes
max_ui_preview_items
```

Full object-level details belong in TXT/JSON reports.

---

## MEL Bridge Isolation

The MEL bridge is optional and disabled by default.

It exists only for pre-run/post-run compatibility hooks.

Main pipeline logic must not depend on MEL hooks.

Hook results and failures should be captured in:

```text
mel_hook_status
```

and surfaced through `RunResult` and reports.

---

## Report Path Fallback

Report generation should not depend on ideal file state.

Report path priority:

1. Current scene directory when the scene is saved.
2. Maya workspace directory when available.
3. User-safe temp fallback.

The selected paths must be returned in `RunResult.report_paths`.

---

## Operation Status Model

Explicit operation statuses make the tool easier to test and safer for future pipeline integration.

Core statuses include:

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

---

## Validation Focus

The manual test checklist should verify at minimum:

* empty scene behavior;
* empty selection behavior;
* Dry Run read-only behavior;
* Apply on simple safe objects;
* default material review;
* multi-material review;
* ignore string behavior;
* referenced object preservation;
* selected child inside reference preservation;
* instanced geometry preservation;
* rig/deformer preservation;
* duplicate short names;
* long-name update after parenting;
* parent/child conflict handling;
* previous tool output idempotency;
* leaf object reclassification;
* Visible scope with hidden parent and display layer;
* RunResult lightweight UI behavior;
* report path fallback;
* MEL bridge optional behavior;
* public documentation status accuracy.

---

## Design Outcome

The result of the defensive design is a small, public-repo-friendly Maya utility with a conservative runtime model.

The tool is planned to organize scene content, not to repair it.

It preserves when uncertain, routes review cases explicitly, moves only safe objects, and writes reports that explain what happened.

That is the core value of Maya Production Pipeliner:

```text
Readable structure before validation.
Safety-aware routing before scene mutation.
Traceable reports before trust.
```
