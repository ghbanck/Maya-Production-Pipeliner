# Manual Test Checklist - Maya Production Pipeliner

This checklist validates the v1.1.3 Final Hardened scope of Maya Production Pipeliner during implementation.

It is intended for manual verification inside Autodesk Maya. Do not mark any item as passed unless it was executed or directly verified in Maya.

## Status Legend

| Mark    | Meaning                                     |
| ------- | ------------------------------------------- |
| PASS    | Verified and working                        |
| FAIL    | Tested and failing                          |
| PENDING | Not tested yet                              |
| REVIEW  | Partially working or requires investigation |

## Validation Rules

* Dry Run must not modify the Maya scene.
* Apply may only move objects cleared by the safety gate.
* A feature is not considered functional until code and manual test evidence exist in the repository.
* Reports must reflect actual execution data.
* UI feedback must come from `RunResult`, not from parsing report files.
* If behavior differs from expected behavior, mark it as `FAIL` or `REVIEW` and document the difference.
* Keep observations short and specific.

---

## Test 1 - Repository / Import Smoke Test

**Purpose:** Verify that the package can be loaded safely before any scene operation is executed.

**Preconditions:** Maya is open. The repository root is available on Maya's Python path.

| Step                                    | Expected                                          | Status  | Observations |
| --------------------------------------- | ------------------------------------------------- | ------- | ------------ |
| Import `maya_production_pipeliner`      | Package imports without errors                    | PENDING |              |
| Import `launcher.py`                    | Import succeeds without modifying the scene       | PENDING |              |
| Import `pipeline.py`                    | Import succeeds without modifying the scene       | PENDING |              |
| Check `launcher.launch()`               | Callable entry point exists                       | PENDING |              |
| Check `pipeline.run_pipeline(settings)` | Callable entry point exists                       | PENDING |              |
| Import with MEL bridge disabled         | Disabled or missing MEL hooks do not break import | PENDING |              |
| Import package in an empty scene        | No groups or objects are created on import        | PENDING |              |

**Expected result:** The project can be loaded without destructive or mutating scene operations.

---

## Test 2 - Empty Scene Behavior

**Purpose:** Verify that empty scenes are handled gracefully.

**Preconditions:** Start a new empty Maya scene.

| Step                               | Expected                                                   | Status  | Observations |
| ---------------------------------- | ---------------------------------------------------------- | ------- | ------------ |
| Run Dry Run with scope = All Scene | No crash; clear empty or no-content result                 | PENDING |              |
| Run Dry Run with scope = Selected  | No crash; clear empty-selection result                     | PENDING |              |
| Run Dry Run with scope = Visible   | No crash; clear empty or no-visible-content result         | PENDING |              |
| Inspect Outliner after Dry Run     | No `Pipeline_Organized` group created                      | PENDING |              |
| Check RunResult                    | `success` and/or `message` clearly describes empty state   | PENDING |              |
| Check report behavior              | Report is generated or clear no-content result is returned | PENDING |              |

**Expected result:** Empty scenes and empty selections do not raise unhandled exceptions.

---

## Test 3 - Scope-Based Scanning

**Purpose:** Verify that the scanner collects the correct scene content for each scope mode.

**Preconditions:** Open a scene containing at least one mesh, one locator, one camera or light, one referenced node, and one instanced mesh.

| Step                                                       | Expected                                                 | Status  | Observations |
| ---------------------------------------------------------- | -------------------------------------------------------- | ------- | ------------ |
| Run with scope = All Scene                                 | Relevant transforms appear in ObjectRecord output        | PENDING |              |
| Run with scope = Selected after selecting two objects      | Only selected processable candidates appear              | PENDING |              |
| Select a shape node directly                               | Scanner normalizes to transform candidate when practical | PENDING |              |
| Select a child node under a transform                      | Scanner records safe transform candidate behavior        | PENDING |              |
| Select component-level data if supported by Maya selection | Scanner handles or reports unsupported selection safely  | PENDING |              |
| Compare RunResult count to expected scene content          | `summary['scanned']` or equivalent count is accurate     | PENDING |              |

**Expected result:** Scanner gathers facts according to scope and does not classify or move objects.

---

## Test 4 - Visible Scope: Basic Visibility

**Purpose:** Verify that Visible scope is more than a raw scene scan.

**Preconditions:** Scene contains visible and hidden objects.

| Step                                    | Expected                                                                 | Status  | Observations |
| --------------------------------------- | ------------------------------------------------------------------------ | ------- | ------------ |
| Hide one object using object visibility | Hidden object is excluded from Visible scope when practical              | PENDING |              |
| Keep another object visible             | Visible object is included                                               | PENDING |              |
| Run Visible scope                       | Report records `scope_mode = Visible`                                    | PENDING |              |
| Inspect visibility fields               | Visibility-related fields appear in ObjectRecord/report when implemented | PENDING |              |

**Expected result:** Visible scope respects resolved scene visibility where practical.

---

## Test 5 - Visible Scope: Parent, Layer, and Native Visibility

**Purpose:** Verify that visibility resolution is not based only on `.visibility`.

**Preconditions:** Create three cases: hidden object, visible child under hidden parent, and visible object inside a hidden display layer.

| Step                                 | Expected                                                                                                      | Status  | Observations |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------- | ------- | ------------ |
| Hide parent transform                | Child is excluded or flagged through resolved visibility                                                      | PENDING |              |
| Hide display layer                   | Object is excluded or flagged through resolved visibility                                                     | PENDING |              |
| Check visibility cache behavior      | Ancestor visibility is not repeatedly queried inefficiently                                                   | PENDING |              |
| Check native visibility confirmation | Native Maya visibility confirmation is used when practical                                                    | PENDING |              |
| Check output fields                  | `hierarchy_visible`, `display_layer_visible`, `native_visible`, or `resolved_visible` appear when implemented | PENDING |              |

**Expected result:** Visible scope avoids obvious visibility false positives where practical.

---

## Test 6 - Dry Run Does Not Modify Scene

**Purpose:** Verify that Dry Run is read-only.

**Preconditions:** Fresh scene with meshes, utilities, and possible review cases.

| Step                                  | Expected                                               | Status  | Observations |
| ------------------------------------- | ------------------------------------------------------ | ------- | ------------ |
| Execute Dry Run                       | No groups are created                                  | PENDING |              |
| Inspect Outliner after Dry Run        | `Pipeline_Organized` does not exist                    | PENDING |              |
| Check object parents before and after | No parent changes occur                                | PENDING |              |
| Check object names before and after   | No rename occurs                                       | PENDING |              |
| Check reports                         | TXT/JSON report planned actions without scene mutation | PENDING |              |
| Check RouteDecision values            | `would_move` may be true, but `did_move = false`       | PENDING |              |
| Check operation status                | `operation_status = dry_run_only` or equivalent        | PENDING |              |

**Expected result:** Dry Run previews the route plan without modifying the Maya scene.

---

## Test 7 - Basic Apply Organization

**Purpose:** Verify that Apply can organize simple movable objects safely.

**Preconditions:** Scene contains one movable polygon mesh with an acceptable material and one simple utility object.

| Step                   | Expected                                      | Status  | Observations |
| ---------------------- | --------------------------------------------- | ------- | ------------ |
| Execute Apply          | `Pipeline_Organized` is created or reused     | PENDING |              |
| Check child groups     | Planned child groups are created or reused    | PENDING |              |
| Check production mesh  | Mesh routes to `Production_Meshes` if safe    | PENDING |              |
| Check utility object   | Utility routes to `Scene_Utilities` if safe   | PENDING |              |
| Check can_move gate    | Only objects with `can_move = true` move      | PENDING |              |
| Check report           | TXT/JSON reflects actual movement             | PENDING |              |
| Check operation status | Moved objects have `operation_status = moved` | PENDING |              |

**Expected result:** Apply organizes simple safe content and records what happened.

---

## Test 8 - Ignore String / Bypass Behavior

**Purpose:** Verify user-defined preservation logic.

**Preconditions:** Scene contains several objects. Rename two to include `BYPASS`.

| Step                                                | Expected                                                                            | Status  | Observations |
| --------------------------------------------------- | ----------------------------------------------------------------------------------- | ------- | ------------ |
| Set ignore string to `BYPASS` and run Dry Run       | Matching objects are excluded from normal production/review routing                 | PENDING |              |
| Run Apply if Bypass movement is implemented as safe | Matching objects route to `Bypass` only if implementation marks this operation safe | PENDING |              |
| If Bypass movement is not safe or not implemented   | Matching objects remain preserved/report-only                                       | PENDING |              |
| Check report                                        | Preserve reason or route reason reflects user ignore string                         | PENDING |              |
| Use empty ignore string                             | No objects route through Bypass due to empty string                                 | PENDING |              |
| Use overly broad ignore string                      | Warning appears in RunResult and report                                             | PENDING |              |

**Expected result:** User-defined ignored content is respected without contradictory movement behavior.

---

## Test 9 - Material Review Routing

**Purpose:** Verify review routing for default and multi-material states.

**Preconditions:** Create one mesh using `initialShadingGroup` and one mesh with multiple materials or shading groups.

| Step                                  | Expected                                           | Status  | Observations |
| ------------------------------------- | -------------------------------------------------- | ------- | ------------ |
| Run Dry Run on default-material mesh  | Mesh receives material review route                | PENDING |              |
| Check default-material route          | Object routes to `Review_MissingMaterial`          | PENDING |              |
| Check default-material reason         | Reason mentions default or missing material review | PENDING |              |
| Run Dry Run on multi-material mesh    | Mesh receives multi-material review route          | PENDING |              |
| Check multi-material route            | Object routes to `Review_MultiMaterial`            | PENDING |              |
| Check multi-material reason           | Reason describes handoff review, not failure       | PENDING |              |
| Run Apply if objects are safe to move | Objects move only if `can_move = true`             | PENDING |              |

**Expected result:** Material issues route to review buckets without being treated as fatal errors.

---

## Test 10 - Referenced Object Preservation

**Purpose:** Verify that referenced nodes are never treated as normal movable content.

**Preconditions:** Reference an external Maya file containing at least one mesh.

| Step                    | Expected                                                   | Status  | Observations |
| ----------------------- | ---------------------------------------------------------- | ------- | ------------ |
| Run Dry Run             | Referenced object is detected as referenced                | PENDING |              |
| Check route             | `route = References`                                       | PENDING |              |
| Check safety            | `can_move = false`                                         | PENDING |              |
| Check report-only state | `report_only = true`                                       | PENDING |              |
| Check preserve reason   | `preserve_reason = Immutable reference node` or equivalent | PENDING |              |
| Run Apply               | Referenced node is not parented                            | PENDING |              |
| Check operation status  | `operation_status = skipped_reference`                     | PENDING |              |
| Check report            | Referenced object is documented as preserved               | PENDING |              |

**Expected result:** Referenced content is never falsely reported as moved.

---

## Test 11 - Selected Child Node Inside Reference

**Purpose:** Verify that selected referenced child nodes are preserved.

**Preconditions:** Select a child node inside a referenced file.

| Step                   | Expected                                         | Status  | Observations |
| ---------------------- | ------------------------------------------------ | ------- | ------------ |
| Run Selected scope     | Selected child is detected safely                | PENDING |              |
| Check reference state  | Node is classified as referenced/report-only     | PENDING |              |
| Run Apply              | Tool does not attempt to parent referenced child | PENDING |              |
| Check movement state   | `did_move = false`                               | PENDING |              |
| Check operation status | `operation_status = skipped_reference`           | PENDING |              |
| Check report           | Preservation reason is clear                     | PENDING |              |

**Expected result:** Selected referenced children are preserved and reported honestly.

---

## Test 12 - Instanced Geometry Preservation

**Purpose:** Verify that instanced geometry is preserved by default.

**Preconditions:** Create or import instanced geometry with shared shape / multiple parents.

| Step                    | Expected                                          | Status  | Observations |
| ----------------------- | ------------------------------------------------- | ------- | ------------ |
| Run Dry Run             | Instance state is detected when practical         | PENDING |              |
| Check safety            | `can_move = false`                                | PENDING |              |
| Check report-only state | Preserved/report-only behavior is recorded        | PENDING |              |
| Run Apply               | Instanced geometry is not parented as normal mesh | PENDING |              |
| Check operation status  | `operation_status = skipped_instance`             | PENDING |              |
| Check report            | Instance preservation reason is recorded          | PENDING |              |

**Expected result:** Instanced geometry is preserved by default.

---

## Test 13 - Rig / Deformer Safety

**Purpose:** Verify that rig-sensitive and deformer-sensitive content is preserved.

**Preconditions:** Scene contains a joint chain, a mesh bound via `skinCluster`, and a mesh with `blendShape`.

| Step                                      | Expected                                                       | Status  | Observations |
| ----------------------------------------- | -------------------------------------------------------------- | ------- | ------------ |
| Run Dry Run on skinCluster mesh           | SkinCluster history is detected when practical                 | PENDING |              |
| Run Dry Run on blendShape mesh            | BlendShape history is detected when practical                  | PENDING |              |
| Run Dry Run on mesh under joint hierarchy | Sensitive hierarchy is detected when practical                 | PENDING |              |
| Check safety                              | Sensitive object receives `can_move = false`                   | PENDING |              |
| Check preserve reason                     | Preserve reason identifies rig/deformer sensitivity            | PENDING |              |
| Run Apply                                 | Sensitive object is not parented                               | PENDING |              |
| Check operation status                    | `operation_status = skipped_sensitive_hierarchy` or equivalent | PENDING |              |

**Expected result:** Rig-sensitive and deformation-sensitive objects are preserved by default.

---

## Test 14 - Scene Utilities

**Purpose:** Verify routing behavior for common utility objects.

**Preconditions:** Create a camera, light, locator, joint, and simple utility transform.

| Step                               | Expected                                              | Status  | Observations |
| ---------------------------------- | ----------------------------------------------------- | ------- | ------------ |
| Run Dry Run                        | Utility objects are detected                          | PENDING |              |
| Check movable camera/light/locator | Safe utilities route to `Scene_Utilities`             | PENDING |              |
| Check joint behavior               | Joints are treated conservatively if sensitive        | PENDING |              |
| Run Apply                          | Only safe utilities move                              | PENDING |              |
| Check report                       | Utility route and subtype are recorded when available | PENDING |              |

**Expected result:** Utility objects are organized or preserved according to safety state.

---

## Test 15 - Duplicate Short Names / Long Names

**Purpose:** Verify that duplicate short names do not cause incorrect moves.

**Preconditions:** Create two objects with the same short name under different parents.

| Step                     | Expected                                           | Status  | Observations |
| ------------------------ | -------------------------------------------------- | ------- | ------------ |
| Run Dry Run              | Scanner records long names                         | PENDING |              |
| Check route decisions    | Objects are distinguishable by path                | PENDING |              |
| Run Apply                | Correct objects are moved                          | PENDING |              |
| Check report             | Original long names are traceable                  | PENDING |              |
| Check collision handling | Maya auto-renames, if any, are reflected in output | PENDING |              |

**Expected result:** Duplicate short names do not break routing or reporting.

---

## Test 16 - Long Name Mutation After Parenting

**Purpose:** Verify that path changes after parenting are tracked.

**Preconditions:** Create a movable object outside `Pipeline_Organized`.

| Step                              | Expected                                        | Status  | Observations |
| --------------------------------- | ----------------------------------------------- | ------- | ------------ |
| Run Apply                         | Object is parented if safe                      | PENDING |              |
| Validate before move              | Organizer checks node existence before movement | PENDING |              |
| Capture parenting result          | Returned Maya path is captured when available   | PENDING |              |
| Check `new_long_name`             | New path is recorded after move                 | PENDING |              |
| Check report                      | Original long name and new long name appear     | PENDING |              |
| Simulate failed move if practical | `did_move = false` and warning are recorded     | PENDING |              |

**Expected result:** Path mutation after parenting is tracked accurately.

---

## Test 17 - Parent / Child Conflict Handling

**Purpose:** Verify that parent/child overlap does not cause conflicting movement.

**Preconditions:** Create a hierarchy and select both a parent and one child.

| Step               | Expected                                                     | Status  | Observations |
| ------------------ | ------------------------------------------------------------ | ------- | ------------ |
| Run Selected scope | Both selected inputs are handled safely                      | PENDING |              |
| Check route plan   | Parent/child conflict is detected or resolved conservatively | PENDING |              |
| Run Apply          | Tool avoids destructive double-parenting                     | PENDING |              |
| Check warnings     | Conflict warning or clear operation status is recorded       | PENDING |              |

**Expected result:** Parent/child overlap does not create duplicate or destructive movement.

---

## Test 18 - Repeated Execution / Idempotency

**Purpose:** Verify that previous tool output does not create recursive nesting.

**Preconditions:** Run Apply once or manually create the expected output group structure.

| Step                            | Expected                                                            | Status  | Observations |
| ------------------------------- | ------------------------------------------------------------------- | ------- | ------------ |
| Run Apply again                 | No duplicate `Pipeline_Organized` group is created                  | PENDING |              |
| Check structural groups         | Tool-created structural groups are not routed as production content | PENDING |              |
| Check objects already in target | `operation_status = already_in_target`                              | PENDING |              |
| Check moved count               | Second run does not move already-correct objects                    | PENDING |              |
| Check report                    | Idempotent behavior is documented                                   | PENDING |              |

**Expected result:** Repeated execution is safe and does not duplicate structure.

---

## Test 19 - Leaf Object Reclassification Inside Pipeline_Organized

**Purpose:** Verify that objects already organized can still be reclassified after user edits.

**Preconditions:** Run Apply once. Then change a leaf object's material or state.

| Step                                         | Expected                                               | Status  | Observations |
| -------------------------------------------- | ------------------------------------------------------ | ------- | ------------ |
| Edit leaf object inside `Pipeline_Organized` | Object state changes                                   | PENDING |              |
| Run Dry Run or Apply again                   | Leaf object is rescanned                               | PENDING |              |
| Check route                                  | Object may reclassify to a new bucket                  | PENDING |              |
| If already correct                           | `operation_status = already_in_target`                 | PENDING |              |
| If target changes and safe                   | Object moves only if `can_move = true`                 | PENDING |              |
| Check structural groups                      | Structural groups remain ignored as production content | PENDING |              |

**Expected result:** Idempotency does not block useful reprocessing.

---

## Test 20 - Unclear Case Routing

**Purpose:** Verify both safe and unsafe unclear-case behavior.

**Preconditions:** Create one ambiguous object that is safe to move and one ambiguous object with unsafe movement indicators.

| Step                                 | Expected                               | Status  | Observations |
| ------------------------------------ | -------------------------------------- | ------- | ------------ |
| Run Dry Run on safe unclear object   | Object receives unclear route          | PENDING |              |
| Check safe unclear target            | Object routes to `Review_UnclearCases` | PENDING |              |
| Check safe unclear movement          | Object moves only if `can_move = true` | PENDING |              |
| Run Dry Run on unsafe unclear object | Object is preserved/report-only        | PENDING |              |
| Check unsafe unclear safety          | `can_move = false`                     | PENDING |              |
| Check report                         | Reason explains uncertainty or risk    | PENDING |              |

**Expected result:** Safe ambiguity has a review destination; unsafe ambiguity is preserved.

---

## Test 21 - Operation Status Values

**Purpose:** Verify consistent status values in reports.

**Preconditions:** Use scenes covering moved, skipped, already-in-target, and failed cases where practical.

| Step                       | Expected                                                       | Status  | Observations |
| -------------------------- | -------------------------------------------------------------- | ------- | ------------ |
| Dry Run object             | `operation_status = dry_run_only` or equivalent                | PENDING |              |
| Successfully moved object  | `operation_status = moved`                                     | PENDING |              |
| Already organized object   | `operation_status = already_in_target`                         | PENDING |              |
| Referenced object          | `operation_status = skipped_reference`                         | PENDING |              |
| Instanced object           | `operation_status = skipped_instance`                          | PENDING |              |
| Sensitive hierarchy object | `operation_status = skipped_sensitive_hierarchy` or equivalent | PENDING |              |
| Tool structural group      | `operation_status = skipped_tool_structure` when reported      | PENDING |              |
| Missing node during Apply  | `operation_status = skipped_missing_node` when simulated       | PENDING |              |
| Parenting failure          | `operation_status = failed_parenting` when simulated           | PENDING |              |

**Expected result:** Operation states are explicit and reportable.

---

## Test 22 - Report Content Completeness

**Purpose:** Verify that TXT and JSON reports provide enough traceability.

| Step                           | Expected                                                      | Status  | Observations |
| ------------------------------ | ------------------------------------------------------------- | ------- | ------------ |
| Check TXT report header        | Includes tool name, timestamp, mode, and scope                | PENDING |              |
| Check TXT report summary       | Includes scanned count and route summary                      | PENDING |              |
| Check TXT route details        | Includes object route, target group, and safety state         | PENDING |              |
| Check TXT preservation details | Includes `preserve_reason` when relevant                      | PENDING |              |
| Check TXT operation details    | Includes `operation_status` and `new_long_name` when relevant | PENDING |              |
| Check JSON report structure    | Equivalent data exists in structured form                     | PENDING |              |
| Check warnings                 | Warnings appear in both TXT and JSON when present             | PENDING |              |

**Expected result:** Reports are useful for review and debugging.

---

## Test 23 - Report Path Fallback

**Purpose:** Verify report path behavior in different file states.

**Preconditions:** Test saved and unsaved Maya scenes.

| Step                                   | Expected                                                   | Status  | Observations |
| -------------------------------------- | ---------------------------------------------------------- | ------- | ------------ |
| Saved scene                            | Reports write next to scene file when possible             | PENDING |              |
| Unsaved scene                          | Workspace or temp fallback is used                         | PENDING |              |
| Workspace available                    | Workspace fallback works if scene path is unavailable      | PENDING |              |
| Path not writable if practical to test | User-safe fallback or clear error is returned              | PENDING |              |
| Check RunResult                        | Report paths are included                                  | PENDING |              |
| Check UI                               | Report paths are displayed without reading report contents | PENDING |              |

**Expected result:** Report generation does not depend on ideal scene file state.

---

## Test 24 - RunResult Lightweight UI Behavior

**Purpose:** Verify that the UI remains lightweight in large scenes.

**Preconditions:** Use a large scene or simulate many route decisions.

| Step                  | Expected                                              | Status  | Observations |
| --------------------- | ----------------------------------------------------- | ------- | ------------ |
| Run pipeline          | RunResult includes `route_decisions_count`            | PENDING |              |
| Check preview         | `preview_routes` is limited by `max_ui_preview_items` | PENDING |              |
| Check UI summary      | UI displays summary counters and report paths         | PENDING |              |
| Check full route list | UI does not render every object route                 | PENDING |              |
| Check reports         | Full route details remain in TXT/JSON                 | PENDING |              |
| Check responsiveness  | UI does not freeze from rendering large object lists  | PENDING |              |

**Expected result:** UI feedback remains lightweight and scalable.

---

## Test 25 - UI / Reporter Decoupling

**Purpose:** Verify that UI, pipeline, and reporter responsibilities remain separated.

| Step                                       | Expected                                            | Status  | Observations |
| ------------------------------------------ | --------------------------------------------------- | ------- | ------------ |
| Run pipeline without UI                    | Pipeline can execute directly                       | PENDING |              |
| Run UI workflow                            | UI receives feedback through RunResult              | PENDING |              |
| Inspect UI behavior                        | UI does not parse TXT/JSON to know what happened    | PENDING |              |
| Inspect reporter behavior                  | Reporter writes files independently from UI display | PENDING |              |
| Simulate report write failure if practical | UI receives clear warning through RunResult         | PENDING |              |

**Expected result:** UI feedback is not coupled to report file parsing.

---

## Test 26 - MEL Bridge Optional Behavior

**Purpose:** Verify that MEL compatibility remains isolated and optional.

**Preconditions:** Tool is configured with MEL bridge disabled, then optionally with simple test hooks.

| Step                               | Expected                                            | Status  | Observations |
| ---------------------------------- | --------------------------------------------------- | ------- | ------------ |
| Run with MEL bridge disabled       | Main pipeline runs normally                         | PENDING |              |
| Missing MEL hook                   | Missing hook does not fail import or main execution | PENDING |              |
| Valid pre-run hook if implemented  | Status is recorded                                  | PENDING |              |
| Valid post-run hook if implemented | Status is recorded                                  | PENDING |              |
| Failing MEL hook if practical      | Failure is reported clearly                         | PENDING |              |
| Check reports                      | MEL hook status appears when used                   | PENDING |              |

**Expected result:** MEL bridge does not contaminate or destabilize the core Python workflow.

---

## Test 27 - Dry Run vs Apply Consistency

**Purpose:** Verify that Dry Run and Apply rely on the same route-planning logic.

**Preconditions:** Scene with multiple route categories.

| Step                                | Expected                                                       | Status  | Observations |
| ----------------------------------- | -------------------------------------------------------------- | ------- | ------------ |
| Run Dry Run                         | Route plan is generated                                        | PENDING |              |
| Run Apply on same scene state       | Apply uses equivalent route-planning logic                     | PENDING |              |
| Compare planned vs executed actions | Differences are explained by scene changes or operation status | PENDING |              |
| Check Apply report                  | Report records the plan actually executed                      | PENDING |              |
| Check Dry Run scene state           | Dry Run did not influence Apply by mutating scene              | PENDING |              |

**Expected result:** Dry Run preview and Apply behavior are trustworthy.

---

## Test 28 - Public Repository Documentation Check

**Purpose:** Verify that public documentation matches actual implementation status.

| Step                          | Expected                                                          | Status  | Observations |
| ----------------------------- | ----------------------------------------------------------------- | ------- | ------------ |
| Check README status           | README matches current implementation state                       | PENDING |              |
| Check README feature language | Planned features are not described as already implemented         | PENDING |              |
| Check docs links              | README links resolve to existing Markdown files                   | PENDING |              |
| Check examples                | Example reports are labeled correctly if they are format previews | PENDING |              |
| Check checklist               | Manual test checklist is current                                  | PENDING |              |
| Check screenshots if present  | Screenshots reflect actual tool behavior                          | PENDING |              |
| Check version/tag if present  | Version matches implementation state                              | PENDING |              |

**Expected result:** Public repository materials are accurate and do not overclaim.

---

## Final Release Gate

Before tagging or presenting a release candidate, verify:

| Gate                                 | Expected                                                           | Status  | Observations |
| ------------------------------------ | ------------------------------------------------------------------ | ------- | ------------ |
| Package imports cleanly              | No import-time scene mutation                                      | PENDING |              |
| Dry Run works                        | Scan, classify, RunResult, and reports work without scene mutation | PENDING |              |
| Apply works on simple safe scene     | Safe objects move to expected groups                               | PENDING |              |
| Protected content stays protected    | References, instances, and sensitive hierarchies are preserved     | PENDING |              |
| Reports are traceable                | TXT/JSON reflect real run data                                     | PENDING |              |
| UI remains lightweight               | UI does not render full route list                                 | PENDING |              |
| Idempotency works                    | Repeated run does not duplicate structure                          | PENDING |              |
| Documentation matches implementation | README and docs describe current state honestly                    | PENDING |              |

**Expected result:** The repository is ready for a public release candidate only after the functional claims in the README are backed by code and test evidence.
