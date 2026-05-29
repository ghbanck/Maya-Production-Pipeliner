# Frozen Scope Contract v1.1.3 - Maya Production Pipeliner

> Before validation, production needs readable structure.

## Purpose

This document defines the locked public scope for Maya Production Pipeliner.

It describes what the v1.1.3 Final Hardened build is intended to deliver, which behaviors must remain protected, which data contracts must be respected, and which boundaries should prevent scope creep during implementation.

This is a planning and implementation contract. It should not be read as proof that every feature is already implemented. A feature is considered functional only when code and manual test evidence exist in the repository.

## Scope Status

| Area                   | Status                                |
| ---------------------- | ------------------------------------- |
| Scope label            | v1.1.3 Final Hardened                 |
| Tool status            | Scaffold / implementation in progress |
| Primary DCC            | Autodesk Maya                         |
| Primary language       | Python                                |
| Maya API layer         | `maya.cmds`                           |
| Optional compatibility | Isolated MEL bridge                   |
| Repository target      | Public Git repository                 |
| License target         | MIT                                   |

The `v1.1.3` label identifies the frozen scope document. It does not imply that the software has been released, tagged, deployed, validated, or production-tested.

## Product Identity

Maya Production Pipeliner is a lightweight Maya Python utility being built to organize scene content into readable production handoff groups.

The tool exists to solve the first layer of a common production problem: before a scene can be validated, exported, reviewed, or integrated, artists and technical artists need a predictable way to understand what is in the scene.

The project is intentionally small. It focuses on scene organization, safety-aware routing, review grouping, Dry Run visibility, Apply execution, and traceable reporting.

## Product Thesis

```text
Messy scene
-> scan
-> classify
-> safety gate
-> route plan
-> Dry Run report or safe Apply
-> readable handoff structure
```

The tool should demonstrate practical Technical Art / Tools & Pipeline thinking: converting a real DCC production pain into a small, readable, modular, testable, safety-aware utility.

## Public Behavior Target

The v1.1.3 scope defines a Maya utility that will provide:

* simple Maya-native UI;
* scope modes: All Scene, Selected, Visible;
* execution modes: Dry Run and Apply;
* editable ignore string field;
* scene scanning;
* object classification;
* safety gate based on `can_move`;
* route plan before scene mutation;
* central pipeline orchestrator;
* in-memory `RunResult`;
* lightweight UI summary and limited preview routes;
* predictable Outliner group organization;
* production mesh grouping;
* scene utility grouping;
* review groups for material and unclear cases;
* report-only handling for protected content;
* idempotent repeated execution;
* protection against long-name mutation during parenting;
* resolved scene visibility for Visible scope where practical;
* TXT report;
* JSON report;
* optional isolated MEL pre-run and post-run hooks;
* public README;
* MIT license;
* example reports;
* manual test checklist;
* simple install and launch instructions.

## Implementation Latitude

The scope defines required behavior, data semantics, safety rules, and public-facing expectations.

Implementation details may evolve if they preserve the contract. This includes helper function names, internal file organization inside a module, whether records are implemented as dataclasses or dictionaries, exact UI wording, report formatting details, and import-guard strategy.

The implementation must not add broader product features, hidden pipeline dependencies, destructive scene operations, complex external systems, or new user-facing responsibilities without explicit scope approval.

Future architecture notes are directional guidance, not automatic implementation mandates. Findings from architecture review should be classified before action and should not widen scope by default.

## Architecture Laws

The implementation must preserve these module boundaries:

* `scanner.py` reads scene facts only and never mutates the scene;
* `classifier.py` creates route decisions only and never mutates the scene;
* `reporter.py` writes reports only and never mutates the scene;
* `ui.py` and `launcher.py` never mutate the scene directly;
* `pipeline.py` coordinates execution but does not perform scene operations directly;
* `organizer.py` is the only module allowed to mutate scene hierarchy, and only in Apply mode.

Dry Run is always observational and non-mutating. It must not create groups, parent nodes, rename nodes, edit attributes, execute mutating hooks, or call Apply-only organizer behavior.

Apply must execute a route plan that already exists. It must not improvise classification or routing while mutating the scene.

## User Flow

The intended user flow is:

1. Open the tool from a launcher command.
2. Choose scope: All Scene, Selected, or Visible.
3. Choose execution mode: Dry Run or Apply.
4. Define an ignore string when needed.
5. Run the tool.
6. Review the UI summary and report paths.
7. Inspect TXT/JSON reports when full details are needed.

Dry Run performs scanning, classification, safety gating, route planning, `RunResult` generation, and reporting without modifying the scene.

Apply uses the route plan, creates or reuses the output group structure, moves only objects with `can_move = true`, preserves report-only objects, records operation status, updates `new_long_name` when needed, and writes reports.

The UI must use `RunResult` for feedback. It must not parse TXT/JSON report files to decide what happened.

## Scope Modes

### All Scene

All Scene scans relevant scene content.

Structural groups created by the tool must not be treated as normal production content. Leaf objects already inside `Pipeline_Organized` may still be scanned and reclassified so repeated runs remain useful after user edits.

### Selected

Selected scans selected content.

Component, shape, and child selections should normalize to processable transform candidates when practical. If a selected node belongs to a referenced file, it must be classified as reference/report-only and preserved.

If a parent and child are both in scope, route planning must avoid conflicting movement.

### Visible

Visible scans objects considered visible by resolved scene visibility.

Visible scope must not rely only on `node.visibility`. It should combine cached hierarchy visibility, display-layer visibility when available, shape visibility when relevant, and native Maya visibility confirmation when practical.

Viewport-only isolate select is not the authoritative visibility source for v1.1.3.

## Execution Modes

### Dry Run

Dry Run is read-only.

It builds a route plan and reports what Apply would do. It must not create groups, parent objects, rename objects, modify materials, or change scene hierarchy.

Expected Dry Run behavior:

```text
would_move may be true
did_move must remain false
operation_status should reflect dry-run-only behavior
```

### Apply

Apply executes the route plan.

It creates or reuses the output group structure and parents only movable transform candidates. It must preserve protected content, record operation status, update `new_long_name` when parenting changes paths, and mark objects already in the correct destination as `already_in_target`.

Apply must not improvise movement outside the route plan.

Apply is not considered contract-complete until the Safe Move contract, failure policy, long-name policy, deterministic ordering policy, and manual test evidence are present.

## Ignore String

The UI includes an editable ignore string field.

Default value may be:

```text
BYPASS
```

The user may replace it with any string used by the scene or pipeline. An empty ignore string is treated as disabled.

The string should be evaluated against object name, long name, and hierarchy path when available.

Matching objects are preserved outside normal production/review routing. If Bypass movement is implemented, it must remain safe and explicit. Bypass must not become a generic ambiguity bucket.

The tool should emit a warning when the ignore string matches an unusually high percentage of scanned objects.

## Output Group Structure

Apply mode creates or reuses the root group:

```text
Pipeline_Organized
```

Default child groups:

```text
Production_Meshes
Scene_Utilities
References
Review_MissingMaterial
Review_MultiMaterial
Review_UnclearCases
Bypass
```

Group names must be centralized in `config.py`.

`Bypass` reflects explicit user ignore-string intent.

`Review_UnclearCases` is reserved for safe-to-move ambiguous content.

## Repeated Run and Idempotency

The tool must be safe to run more than once.

The scanner must identify tool-created structural groups and avoid routing those groups as normal production content.

Leaf objects already inside `Pipeline_Organized` may be scanned and reclassified. This allows a user to fix an object state, rerun the tool, and get updated routing without manually extracting the object from the organized structure.

The organizer must avoid duplicate nesting. If an object is already under its correct target group, it records:

```text
operation_status = already_in_target
```

and does not move it again.

If an object is under an old target and now belongs somewhere else, it may move only if:

```text
can_move = true
```

## Classification Policy

Classification priority, from highest to lowest:

1. Internal tool structural groups.
2. User ignore string.
3. Referenced or locked content.
4. Instanced geometry.
5. Rig/deformer-sensitive content.
6. Scene utilities.
7. Material review cases.
8. Production meshes.
9. Unclear cases.

### References

Referenced nodes are preserved by default.

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

### Instanced Geometry

Instanced geometry is preserved by default.

Expected behavior:

```text
can_move = false
report_only = true
operation_status = skipped_instance
```

### Rig and Deformer-sensitive Content

Objects with `skinCluster` history, `blendShape` history, parent joints, or obvious sensitive hierarchy conditions are preserved by default.

Expected behavior:

```text
can_move = false
report_only = true
operation_status = skipped_sensitive_hierarchy
```

### Default or Missing Material

Objects using the Maya default material/shading group, or without a production material detected, route to:

```text
Review_MissingMaterial
```

### Multi-material Cases

Objects with multiple materials or shading groups route to:

```text
Review_MultiMaterial
```

Multi-material routing indicates handoff review, not failure.

Material fields must state what they measure. If a value counts shadingEngine connections, it should be documented as such. If a value counts unique material nodes, it should be documented separately. Classifier logic and reports must not rely on ambiguous material-count semantics.

### Scene Utilities

Movable cameras, lights, locators, and simple utility transforms route to:

```text
Scene_Utilities
```

Sensitive utility objects are preserved and reported.

### Production Meshes

Movable production mesh candidates route to:

```text
Production_Meshes
```

### Unclear Cases

Safe unclear objects route to:

```text
Review_UnclearCases
```

Unsafe unclear objects remain preserved/report-only with:

```text
can_move = false
```

and a clear `preserve_reason`.

## Route Plan and Safety Gate

Every object receives a route decision before Apply.

The organizer moves only route decisions with:

```text
can_move = true
```

Objects with:

```text
can_move = false
```

are preserved and documented.

RouteDecision fields:

```text
object_name
long_name
new_long_name
route
target_group
reason
warnings
execution_mode
scope_mode
can_move
operation
preserve_reason
report_only
would_move
did_move
operation_status
```

The classifier is responsible for conservative routing and safety decisions. The organizer is responsible for executing only the safe subset of the plan.

## Safe Move Contract

A route decision may be moved only when all required conditions are true at Apply time:

```text
can_move = true
report_only = false
source node exists
source node is not referenced
source node is not instanced
source node is not rig/deformer-sensitive
source node is not a tool structural group
target group is valid
parenting does not create an invalid or cyclic hierarchy
post-parent validation succeeds
```

If any condition is unknown or false, the object must be preserved and reported instead of moved.

## Operation Status Values

`operation_status` should use explicit values to avoid vague reporting:

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

Do not create alternate status names for the same state unless the scope is explicitly revised.

## Long-name Mutation During Apply

Long names can change when Maya reparents objects.

The organizer must not assume that all long names collected during scan remain valid throughout Apply.

The organizer must:

* validate node existence before each move;
* reduce parent/child route conflicts before movement;
* execute parenting only on a valid current identifier;
* capture the return value of Maya parenting operations when available;
* store the resulting path in `new_long_name`;
* record `operation_status` for every attempted operation;
* set `did_move = false` and add a warning when a move cannot be completed safely.

The original `long_name` remains the scanned identity for reporting. The updated path after successful parenting belongs in `new_long_name`. If a node is renamed, missing, or failed during Apply, reports should preserve the original scanned value and record the final known state.

## Apply Failure Policy

Maya scene operations are not transactional. Apply must therefore favor safe partial handling over pretending that rollback is guaranteed.

Expected failure behavior:

* continue safely when one failed object does not invalidate independent decisions;
* record `failed_parenting` when parenting fails;
* record `skipped_missing_node` when a node disappears before movement;
* leave failed objects in their original location when possible;
* surface failures in `RunResult` and reports;
* avoid reporting full success when partial failures occurred.

Rollback is not guaranteed by this scope. Any future rollback-like behavior must be explicitly designed and documented before implementation.

## Movement Order

When applying route decisions, object order must be handled conservatively.

Do not rely only on string length to decide hierarchy order. When hierarchy depth matters, use the count of the Maya path separator:

```text
|
```

to reason about depth.

The implementation should avoid destructive parent/child conflicts and should preserve hierarchy integrity over convenience.

Route decisions and reports should use deterministic ordering where practical. Stable order reduces noisy diffs, supports manual review, and makes future regression checks easier.

## Pipeline Orchestrator

The repository includes `pipeline.py` as the central orchestrator.

UI and launcher call the pipeline module. The UI must not directly call scanner, classifier, organizer, or reporter in a coupled way.

`pipeline.py` receives settings, calls scan/classify/organize/report, builds `RunResult`, and returns it to UI or launcher.

## RunResult

`RunResult` is an in-memory execution result used by UI and launcher.

The reporter writes TXT/JSON independently and is not the UI source of truth.

RunResult fields:

```text
route_decisions
summary
warnings
report_paths
mel_hook_status
execution_mode
scope_mode
ignore_string
success
message
route_decisions_count
preview_routes
max_ui_preview_items
```

The UI consumes:

```text
summary
warnings
report_paths
route_decisions_count
preview_routes
```

The UI must not render the complete object-by-object route list for heavy scenes. Full detail remains in TXT/JSON reports.

## Reporting

Reports must include:

* tool name;
* timestamp;
* execution mode;
* scope mode;
* ignore string;
* total scanned objects;
* classification summary;
* object routes;
* target groups;
* `can_move`;
* `preserve_reason`;
* `report_only`;
* `new_long_name`;
* `operation_status`;
* visibility resolution fields when relevant;
* warnings;
* MEL hook status when used;
* report paths.

Report path priority:

1. Current scene directory when the scene is saved.
2. Maya workspace directory when available.
3. User-safe temp fallback.

JSON reports should include a simple schema version before the report format is treated as integration-stable.

Warnings should support stable categories or warning codes as reporting matures. Human-readable warning text is useful for review, but stable identifiers are safer for tests, filtering, and future tooling.

All report payloads must remain JSON-safe at the source record and route decision level. Late serialization cleanup may exist as a defensive fallback, but it should not be the primary data contract.

## Optional MEL Bridge

The MEL bridge is optional, isolated in `mel_bridge.py`, and disabled by default.

It is used only for pre-run/post-run hook compatibility with existing Maya pipelines.

MEL hook status and failures are reported through `RunResult` and reports.

Main pipeline logic must not depend on MEL hooks.

## Import Safety

The package should be safe to import outside a live Maya runtime when possible.

Modules may use guarded Maya imports or lazy imports, as long as package import does not immediately execute Maya scene operations or open UI.

Importing the package must not:

* scan the scene;
* modify the scene;
* create groups;
* write reports;
* open UI;
* require a live Maya scene.

Runtime functions that require Maya may fail clearly or remain unavailable outside Maya, but import-time side effects should be avoided.

## Repository Architecture

Expected package structure:

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

examples/
    example_report.txt
    example_report.json

docs/
    planning/
    architecture/
    testing/

README.md
LICENSE
install.py
```

## Module Responsibilities

### `config.py`

Constants, defaults, group names, report filenames, default material identifiers, safety thresholds, visibility settings, and `max_ui_preview_items`.

### `scanner.py`

Scene reading, scope resolution, transform normalization, visibility cache, display-layer visibility when available, native scene visibility confirmation when practical, material data, references, instances, rig/deformer sensitivity, previous tool output detection, and object records.

Scanner collects facts only. It must not decide routes or modify the scene.

### `classifier.py`

Classification priority, route decisions, `can_move`, `preserve_reason`, `report_only`, unclear case routing, and warnings.

Classifier decides routes and safety. It must not modify the scene.

### `organizer.py`

Group creation, safe parenting, idempotent repeated execution, `already_in_target` detection, node existence validation, `new_long_name` updates, `operation_status`, and report-only preservation.

Organizer modifies the scene only in Apply.

### `reporter.py`

TXT/JSON reports, summaries, route records, warnings, and report paths.

Reporter writes reports. It must not direct the UI or mutate scene hierarchy.

### `mel_bridge.py`

Optional pre-run/post-run MEL hooks, error capture, and hook status.

### `pipeline.py`

Central orchestration and `RunResult` generation.

### `ui.py`

Simple Maya UI that calls pipeline execution and displays lightweight `RunResult` feedback.

### `launcher.py`

Public `launch()` entry point.

### `install.py`

Simple installation/path/launch helper.

## Data Model

### ObjectRecord Fields

```text
name
long_name
input_node
transform_node
shape_nodes
node_type
shape_type
is_mesh
is_visible
is_selected
namespace
materials
material_count
uses_default_material
matches_ignore_string
is_referenced
is_instanced
has_skin_cluster
has_blendshape
parent_is_joint
is_under_sensitive_hierarchy
is_inside_tool_output
is_tool_structural_group
hierarchy_visible
display_layer_visible
native_visible
resolved_visible
warnings
```

### RouteDecision Fields

```text
object_name
long_name
new_long_name
route
target_group
reason
warnings
execution_mode
scope_mode
can_move
operation
preserve_reason
report_only
would_move
did_move
operation_status
```

### RunResult Fields

```text
route_decisions
summary
warnings
report_paths
mel_hook_status
execution_mode
scope_mode
ignore_string
success
message
route_decisions_count
preview_routes
max_ui_preview_items
```

All structures should remain JSON-safe.

## Safety Principles

* Dry Run does not modify the scene.
* Apply moves only transform candidates with `can_move = true`.
* Referenced content is preserved/report-only by default.
* Instanced geometry is preserved by default.
* Rig/deformer-sensitive content is preserved by default.
* User-ignored content is preserved.
* Safe unclear cases go to `Review_UnclearCases`.
* Unsafe unclear cases are preserved/report-only.
* Structural tool groups are not treated as production content.
* Leaf objects inside `Pipeline_Organized` may be rescanned and reclassified.
* Objects already in the correct target receive `already_in_target`.
* Visible scope uses cached resolved scene visibility, including display layer and native visibility checks where practical.
* The organizer updates `new_long_name` when parenting changes paths.
* UI feedback comes from lightweight `RunResult` fields, not report parsing or full object-list rendering.
* When safety and convenience conflict, choose preservation.

## Manual Test Coverage

The manual test checklist should cover at minimum:

* import safety;
* empty scene;
* empty selection;
* selected basic mesh;
* visible-only scene state;
* hidden parent visibility;
* hidden display layer visibility;
* native visible query mismatch;
* mesh with default material;
* mesh with one production material;
* multi-material mesh;
* ignored object by user string;
* referenced object;
* selected child node inside reference;
* instanced mesh;
* skinned mesh;
* mesh under joint hierarchy;
* duplicate short names;
* long-name update after parenting;
* parent/child conflict handling;
* unclear safe object;
* unclear unsafe object;
* previous `Pipeline_Organized` output present;
* leaf object inside `Pipeline_Organized` reclassified after user edit;
* object already in correct target;
* heavy-scene `RunResult` summary without full UI list rendering;
* UI feedback from `RunResult`;
* report path fallback;
* MEL bridge optional behavior.

## Success Criteria

The v1.1.3 scope is successful when:

* the value can be understood in under one minute;
* the tool clearly shows hands-on Maya tooling and pipeline reasoning;
* sensitive production structures are preserved and reported accurately;
* references are never falsely reported as moved;
* long-name mutation during Apply is tracked through `new_long_name` and `operation_status`;
* repeated execution does not duplicate structure or lock edited leaf objects out of reclassification;
* Visible scope avoids obvious display-layer false positives where practical;
* UI feedback stays lightweight in large scenes;
* package imports are safe and side-effect free where practical;
* the tool remains small, safe, modular, readable, and public-GitHub-ready.

## Scope Boundaries

The v1.1.3 scope is focused on scene organization for production handoff.

It does not expand into full asset validation, export validation, publishing, rig repair, material fixing, dependency management, database integration, or broad studio pipeline replacement.

Future additions may be considered later, but they should not enter v1.1.3 without explicit scope approval.

## Explicit Limitations

The scope does not guarantee:

* corrupted reference recovery;
* rig correctness validation;
* shader graph validation;
* namespace conflict resolution;
* animation semantic correctness;
* resumable execution;
* historical replay;
* telemetry;
* generalized pipeline runtime behavior.

These limitations do not reduce the value of the tool. They keep the project focused on safe scene organization, conservative routing, and traceable handoff reports.
