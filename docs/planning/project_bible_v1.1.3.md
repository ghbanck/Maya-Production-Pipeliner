# Project Bible v1.1.3 - Maya Production Pipeliner

> Before validation, production needs readable structure.

## Purpose

This document provides the public project bible for Maya Production Pipeliner.

It explains the product rationale, production problem, design direction, source inspiration, planned scope, architecture, and quality bar for the v1.1.3 Final Hardened build.

This is a planning and implementation guide. The tool is currently in scaffold / implementation phase. Functional behavior should only be considered implemented when the corresponding code and manual test evidence exist in the repository.

## Project Identity

| Area                   | Description                                                           |
| ---------------------- | --------------------------------------------------------------------- |
| Project name           | Maya Production Pipeliner                                             |
| Package name           | `maya_production_pipeliner`                                           |
| Tool type              | Maya Python production utility                                        |
| Primary DCC            | Autodesk Maya                                                         |
| API layer              | `maya.cmds`                                                           |
| Optional compatibility | Isolated MEL bridge                                                   |
| Primary users          | Technical artists, pipeline artists, 3D artists, production reviewers |
| Main purpose           | Scene organization for production handoff                             |
| Scope status           | v1.1.3 Final Hardened scope locked                                    |
| Current status         | Scaffold / implementation in progress                                 |

Maya Production Pipeliner is a lightweight Python-first Maya utility being built to organize scene content into clean production handoff groups.

The tool is designed around scope-based scanning, Dry Run and Apply modes, user-defined ignore-string preservation, safety-aware routing, material-aware review routing, unclear-case routing, idempotent repeated execution, simple Outliner organization, optional MEL hook compatibility, lightweight `RunResult` feedback, and traceable TXT/JSON reports.

## Why This Tool Exists

Production Maya scenes often become hard to read before they become technically invalid.

A scene may contain production meshes, cameras, lights, locators, joints, references, imported assets, namespaces, temporary helpers, default material assignments, multi-material meshes, instanced objects, skinned meshes, blend shapes, hidden content, display layers, previous tool outputs, duplicate short names, and objects that should remain untouched.

Without a predictable organization pass, a technical artist or downstream user has to manually inspect the Outliner and infer what is ready, what is auxiliary, what needs review, what is referenced, what is rig-sensitive, what changed, what remained untouched, and what should be preserved.

Maya Production Pipeliner is designed to solve this first layer: readable production structure before deeper validation, export, review, or integration begins.

## Core Philosophy

Scene organization is not a replacement for validation.

It is the step that makes validation safer to perform.

```text
Before validation, production needs readable structure.
```

The project follows a production-first principle:

```text
Facts before routing.
Route plan before scene changes.
Reports before trust.
```

## Origin and Translation

The project is inspired by `Collection_Wizard`, a Blender add-on created around production cleanup and handoff.

The original tool organized scene objects into collections, preserved bypass content, routed review cases, supported dry-run execution, handled material-related conditions, generated action logs, tracked stats, and wrote reports.

The value being carried forward is not Blender-specific implementation. The value is the production logic:

1. Scan scene content.
2. Classify objects.
3. Preserve intentional exceptions.
4. Route objects into predictable destinations.
5. Identify review cases.
6. Avoid destructive assumptions.
7. Provide a dry-run path.
8. Generate a traceable report.
9. Support handoff clarity.

The Maya version translates those ideas into Maya-native concepts:

| Original concept    | Maya Production Pipeliner translation |
| ------------------- | ------------------------------------- |
| Blender collections | Maya Outliner groups                  |
| Bypass naming       | User-defined ignore string            |
| Dry-run mode        | Read-only route planning and reports  |
| Review collections  | Review groups in the Outliner         |
| Action log          | TXT/JSON reports                      |
| Scene organization  | Production handoff structure          |

The original Blender source is treated as conceptual reference only. It is not a 1:1 port target.

## Product Definition

Maya Production Pipeliner is being built as a small production utility that will:

* scan the current Maya scene;
* support All Scene, Selected, and Visible scope modes;
* classify scene objects by production handoff status;
* apply a safety gate before movement;
* organize movable objects into predictable Outliner groups;
* preserve content matching a user-defined ignore string;
* preserve referenced, instanced, rig-sensitive, unclear-unsafe, or non-movable content;
* route review cases into dedicated review groups;
* support repeated execution without duplicate nesting;
* support Dry Run and Apply modes;
* return lightweight in-memory `RunResult` feedback for the UI;
* generate TXT and JSON reports;
* provide a simple Maya UI;
* include an optional MEL bridge for legacy pipeline hooks;
* remain modular, readable, lightweight, and public-repo friendly.

## Target v1.1.3 Scope

The v1.1.3 Final Hardened scope includes:

* Maya Python package structure;
* simple Maya UI;
* scope selection: All Scene, Selected, Visible;
* execution mode: Dry Run or Apply;
* editable ignore string field;
* scene scanning;
* object classification;
* safety gate;
* route plan;
* `RunResult`;
* lightweight UI summary and limited preview;
* pipeline orchestrator;
* Outliner group creation;
* idempotent repeated execution;
* safe object routing;
* review groups;
* scene utility separation;
* production mesh grouping;
* default/missing material review;
* multi-material review;
* unclear case review;
* ignore/bypass preservation;
* reference preservation;
* instanced geometry preservation;
* rig/deformer preservation;
* long-name update after parenting;
* cached scene-visibility resolution for Visible scope;
* TXT report;
* JSON report;
* optional MEL pre-run and post-run hooks;
* README;
* MIT license;
* example report;
* manual test checklist;
* install/launch instructions.

## User Experience

The intended user flow is simple.

1. The user launches the tool in Maya.
2. The user chooses a scope: All Scene, Selected, or Visible.
3. The user chooses an execution mode: Dry Run or Apply.
4. The user defines an ignore string when needed.
5. The tool scans the scene and builds object records.
6. The classifier produces route decisions.
7. Dry Run previews the route plan without modifying the scene.
8. Apply creates or reuses output groups and moves only safe objects.
9. Reports are written.
10. The UI displays lightweight `RunResult` feedback.

The UI should not try to render every object-level route in large scenes. Full detail belongs in TXT/JSON reports.

## Main Workflow

```text
Load configuration
-> read UI settings
-> optionally run pre-run MEL hook
-> scan scene objects
-> normalize scanned nodes to transform candidates
-> resolve scene visibility when Visible scope is used
-> build ObjectRecord data
-> classify objects
-> apply safety gate
-> build RouteDecision plan
-> write reports in Dry Run
-> create/reuse groups and route safe objects in Apply
-> update new_long_name after parenting
-> build lightweight RunResult
-> optionally run post-run MEL hook
-> display UI summary
```

The route plan is the central authority. Apply should execute the plan, not improvise scene changes.

## Scope Modes

### All Scene

Processes relevant scene objects.

Tool-created structural groups should not be routed as production content. Leaf objects already inside `Pipeline_Organized` may still be scanned and reclassified so repeated runs remain useful after user edits.

### Selected

Processes selected content.

Component, shape, or child selections should normalize into processable transform candidates when practical. If a selected node belongs to a referenced file, it should classify as reference/report-only and remain preserved.

### Visible

Processes objects considered visible by resolved scene-visibility logic.

Visible mode should not rely only on direct node visibility. It should combine cached hierarchy visibility, display-layer visibility when available, shape visibility when relevant, and native Maya visibility confirmation when practical.

Viewport-only isolate select is not the authoritative visibility source for v1.1.3.

## Output Group Structure

Apply mode is scoped to create or reuse this root group:

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

These groups are designed to make the Outliner readable at handoff time.

## Repeated Run and Idempotency Policy

The tool must be safe to run more than once.

The scanner should identify tool-created structural groups and prevent them from being routed as production content.

Leaf objects inside `Pipeline_Organized` may be scanned and reclassified. This allows a user to fix a material, rerun the tool, and get updated routing without manually extracting the object.

The organizer must avoid duplicate nesting.

If an object is already under its correct target group, it records:

```text
operation_status = already_in_target
```

If an object is under an old target and now belongs somewhere else, it may move only if:

```text
can_move = true
```

## Classification Rules

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

### Production Meshes

Movable production candidates route to:

```text
Production_Meshes
```

### Scene Utilities

Movable cameras, lights, locators, and simple utility transforms route to:

```text
Scene_Utilities
```

Sensitive utility objects are preserved and reported.

### References

Referenced content is detected and preserved by default.

Expected route decision for referenced nodes:

```text
route = "References"
can_move = false
report_only = true
preserve_reason = "Immutable reference node"
did_move = false
operation_status = skipped_reference
```

### Default or Missing Material

Objects with default material assignment or no production material detected route to:

```text
Review_MissingMaterial
```

### Multi-material

Objects with more than one material or shading group route to:

```text
Review_MultiMaterial
```

Multi-material routing indicates handoff review, not failure.

### Ignored Content

Objects matching the user-defined ignore string are preserved through the ignore/bypass flow.

### Unclear Cases

Safe unclear objects route to:

```text
Review_UnclearCases
```

Unsafe unclear objects remain preserved/report-only with a clear preservation reason.

## Maya-specific Safety Handling

### Material Detection

Use shadingEngine connections where practical.

`initialShadingGroup` and default material assignment are material review cases. Per-face assignments should be interpreted conservatively through detectable shading groups.

### Reference Handling

Referenced nodes are report-only by default.

A selected child node inside a reference should never be reported as moved unless a safe local wrapper transform is actually moved.

### Instanced Geometry

Instanced geometry is preserved by default and documented with a preservation reason.

### Rig and Deformer Safety

Common sensitivity indicators include:

* `skinCluster` history;
* `blendShape` history;
* parent joint;
* obvious sensitive hierarchy conditions.

Objects with these indicators should be preserved by default.

### Long-name Mutation

Maya long names can change after parenting.

The organizer should validate node existence before each move, capture actual results from Maya parenting operations, update `new_long_name`, and record `operation_status`.

### Visible Scope Resolution

Visible scope uses cached scene-visibility resolution.

It should combine hierarchy visibility, display-layer visibility when available, shape visibility when relevant, and native Maya visibility confirmation when practical.

## Route Plan

The route plan represents classification, target, operation, movement safety, warnings, preservation reason, and operation status.

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

The organizer executes only decisions with:

```text
can_move = true
```

## Operation Status Values

`operation_status` should use explicit values:

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

Explicit statuses make reports easier to audit and safer for future pipeline integration.

## Pipeline Orchestrator and RunResult

`pipeline.py` coordinates scanning, classification, route planning, organization, reporting, and `RunResult` creation.

This prevents UI/reporter coupling and keeps execution testable.

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

The UI consumes summary, warnings, report paths, route decision count, and preview routes.

The UI must not render the complete object-by-object route list for heavy scenes. Full detail remains in TXT/JSON reports.

## Reporting

TXT and JSON reports should include:

* tool name;
* timestamp;
* execution mode;
* scope mode;
* ignore string used;
* total objects scanned;
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
* report path;
* optional MEL hook status when enabled.

Report path priority:

1. Current scene directory when the scene is saved.
2. Maya workspace directory when available.
3. User-safe temp fallback.

## Optional MEL Bridge

The MEL bridge is isolated in `mel_bridge.py`.

It is optional, disabled by default, and used for pre-run/post-run hook compatibility with existing Maya pipelines. Hook status should return in reports and `RunResult`.

## Repository Architecture

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

Stores constants, group names, report defaults, material identifiers, safety thresholds, visibility settings, and `max_ui_preview_items`.

### `scanner.py`

Builds object records from scoped scene content, including transform normalization, cached scene-visibility resolution, display-layer visibility when available, native scene visibility confirmation when practical, material data, references, instances, sensitive deformers, previous tool output, and leaf objects inside `Pipeline_Organized`.

### `classifier.py`

Applies classification priority and safety gate, assigns routes, `can_move`, `preserve_reason`, `report_only`, and warnings.

### `organizer.py`

Creates or reuses groups, safely parents movable objects, validates node existence, avoids duplicate nesting, detects `already_in_target`, updates `new_long_name`, and records `operation_status`.

### `reporter.py`

Writes TXT and JSON reports from execution data.

### `mel_bridge.py`

Runs optional MEL hooks and returns status/errors.

### `pipeline.py`

Central orchestration layer returning lightweight `RunResult`.

### `ui.py`

Maya UI that calls pipeline execution and displays lightweight `RunResult` feedback.

### `launcher.py`

Public `launch()` entry point.

### `install.py`

Simple setup/launch helper.

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

## Naming Standards

Function names should be clear and descriptive:

```text
scan_scene_objects()
get_selected_transforms()
get_visible_transforms()
build_visibility_cache()
resolve_scene_visibility()
normalize_to_transform_candidate()
get_mesh_materials()
detect_default_material_assignment()
detect_reference_state()
detect_instanced_geometry()
detect_sensitive_deformers()
detect_tool_structural_group()
classify_object_record()
build_route_plan()
ensure_group_structure()
apply_route_plan()
run_pipeline()
build_run_result()
write_txt_report()
write_json_report()
run_pre_mel_hook()
run_post_mel_hook()
launch()
```

## Safety Principles

* Dry Run does not modify the scene.
* Apply moves only objects marked `can_move = true`.
* Ignored content is preserved.
* Referenced content is preserved.
* Instanced geometry is preserved.
* Rig/deformer-sensitive content is preserved.
* Safe unclear cases go to `Review_UnclearCases`.
* Unsafe unclear cases are report-only.
* Structural tool groups are not treated as production content.
* Leaf objects inside `Pipeline_Organized` may be rescanned and reclassified.
* Objects already in the correct target receive `already_in_target`.
* Visible scope uses cached resolved scene visibility where practical.
* Moved object paths are updated in `new_long_name`.
* The UI consumes lightweight `RunResult` fields instead of parsing reports from disk or rendering full route lists.

## Build Strategy

1. Architecture lock: repository, modules, data model, route plan, `RunResult`, safety gate, idempotency.
2. Core package: `config`, `scanner`, `classifier`, `organizer`, `reporter`, `mel_bridge`, `pipeline`, `launcher`.
3. UI: simple `maya.cmds` window calling pipeline and showing lightweight `RunResult`.
4. Reports: TXT and JSON.
5. Production readiness pass: imports, scopes, visibility cache, display layer visibility, native visibility confirmation, references, instances, deformers, unclear cases, safe parenting, idempotent rerun, long-name updates, previous output, UI/reporter decoupling.
6. GitHub package: README, LICENSE, examples, manual test checklist, install instructions.
7. Visual proof: screenshot or GIF after core works.

## Build Quality Bar

The tool should meet this minimum quality bar before being presented as a functional release:

* importable package;
* clear launch function;
* simple Maya UI;
* works with `maya.cmds`;
* supports All Scene, Selected, Visible;
* has Dry Run and Apply;
* has editable ignore string;
* creates predictable groups;
* includes `Review_UnclearCases`;
* detects default/missing material review cases;
* detects multi-material review cases;
* preserves referenced content;
* preserves instanced geometry;
* preserves rig/deformer-sensitive content;
* uses `can_move` gate;
* updates `new_long_name` when movement changes path;
* supports idempotent repeated execution;
* returns lightweight `RunResult`;
* generates TXT and JSON reports;
* has optional MEL bridge;
* has manual test checklist;
* uses no unnecessary dependencies.

## Success Criteria

The v1.1.3 implementation is successful if:

* the value can be understood in under one minute;
* the tool shows how it organizes Maya scenes and protects sensitive structures;
* moved and preserved content are reported accurately;
* references are not falsely reported as moved;
* path changes after parenting are tracked;
* repeated execution does not duplicate structure or lock edited leaf objects out of reclassification;
* Visible scope avoids obvious display-layer false positives where practical;
* UI feedback stays lightweight in large scenes;
* the code is modular and readable;
* the tool remains small, useful, safe, and professionally packaged.
