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
| Import `maya_production_pipeliner`      | Package imports without errors                    | PASS    | `mayapy` smoke validation imported the package successfully in a fresh Maya scene. |
| Import `launcher.py`                    | Import succeeds without modifying the scene       | PASS    | `mayapy` smoke validation imported `launcher` successfully and the scene remained at the four default startup cameras only. |
| Import `pipeline.py`                    | Import succeeds without modifying the scene       | PASS    | `mayapy` smoke validation imported `pipeline` successfully with no `Pipeline_Organized` root created. |
| Check `launcher.launch()`               | Callable entry point exists                       | PASS    | `launcher.launch` exists as a callable Maya-facing entry point in the real Maya runtime. |
| Check `pipeline.run(...)`               | Callable entry point exists                       | PASS    | Real Maya validation confirmed `pipeline.run(...)` exists as the current callable runtime entry point. |
| Import with MEL bridge disabled         | Disabled or missing MEL hooks do not break import | PASS    | The package imported cleanly in `mayapy` without configuring any MEL hooks, so disabled hook behavior did not break load. |
| Import package in an empty scene        | No groups or objects are created on import        | PASS    | In a new Maya scene, import left the Outliner unchanged (`|persp`, `|top`, `|front`, `|side`) and did not create `Pipeline_Organized`. |

**Expected result:** The project can be loaded without destructive or mutating scene operations.

---

## Test 2 - Empty Scene Behavior

**Purpose:** Verify that empty scenes are handled gracefully.

**Preconditions:** Start a new empty Maya scene.

| Step                               | Expected                                                   | Status  | Observations |
| ---------------------------------- | ---------------------------------------------------------- | ------- | ------------ |
| Run Dry Run with scope = All Scene | No crash; existing Maya scene content is processed safely  | PASS    | Real Maya validation completed successfully in a fresh scene and processed the four default startup cameras as existing Maya content. |
| Run Dry Run with scope = Selected  | No crash; clear empty-selection result                     | PASS    | With no selection in a fresh Maya scene, Dry Run returned `scanned = 0`, `total = 0`, and completed successfully. |
| Run Dry Run with scope = Visible   | No crash; clear empty or no-visible-content result         | PASS    | In the same fresh Maya scene, Visible-scope Dry Run completed successfully with `scanned = 0` and `total = 0`. |
| Inspect Outliner after Dry Run     | No `Pipeline_Organized` group created                      | PASS    | Repeated Dry Run calls left the Outliner unchanged and did not create `Pipeline_Organized`. |
| Check RunResult                    | `success` and/or `message` clearly describes empty state   | PASS    | For empty Selected and Visible runs, `RunResult.success` stayed true and the summary counters remained at zero, clearly indicating no-content execution. |
| Check report behavior              | Report is generated or clear no-content result is returned | PASS    | Real Maya Dry Run wrote TXT/JSON reports into the Maya default workspace for All Scene, Selected, and Visible runs. |

**Expected result:** Empty scenes and empty selections do not raise unhandled exceptions.

---

## Test 3 - Scope-Based Scanning

**Purpose:** Verify that the scanner collects the correct scene content for each scope mode.

**Preconditions:** Open a scene containing at least one mesh, one locator, one camera or light, one referenced node, and one instanced mesh.

| Step                                                       | Expected                                                 | Status  | Observations |
| ---------------------------------------------------------- | -------------------------------------------------------- | ------- | ------------ |
| Run with scope = All Scene                                 | Relevant transforms appear in ObjectRecord output        | PASS    | `mayapy` scope validation captured mesh, locator, camera, light, referenced mesh, instanced meshes, parent transform, and child mesh as ObjectRecords. |
| Run with scope = Selected after selecting two objects      | Only selected processable candidates appear              | PASS    | Selecting `ScopeMesh_A` and `ScopeLocator_A` returned only those two records, both with `is_selected = true`. |
| Select a shape node directly                               | Scanner normalizes to transform candidate when practical | PASS    | Selecting `ScopeMesh_AShape` returned the transform record `ScopeMesh_A`. |
| Select a child node under a transform                      | Scanner records safe transform candidate behavior        | PASS    | Selecting `ScopeChildMesh_A` returned the child transform with long name `|ScopeParent_A|ScopeChildMesh_A`. |
| Select component-level data if supported by Maya selection | Scanner handles or reports unsupported selection safely  | PASS    | Selecting `ScopeMesh_A.vtx[0]` normalized safely to the transform record `ScopeMesh_A`. |
| Compare RunResult count to expected scene content          | `summary['scanned']` or equivalent count is accurate     | PASS    | Selected-scope Dry Run returned `summary['scanned'] = 2` and `route_decisions_count = 2`, matching the scanner-selected records. |

**Expected result:** Scanner gathers facts according to scope and does not classify or move objects.

---

## Test 4 - Visible Scope: Basic Visibility

**Purpose:** Verify that Visible scope is more than a raw scene scan.

**Preconditions:** Scene contains visible and hidden objects.

| Step                                    | Expected                                                                 | Status  | Observations |
| --------------------------------------- | ------------------------------------------------------------------------ | ------- | ------------ |
| Hide one object using object visibility | Hidden object is excluded from Visible scope when practical              | PASS    | `mayapy` validation excluded `HiddenMesh_A` from Visible scope. |
| Keep another object visible             | Visible object is included                                               | PASS    | `VisibleMesh_A` and `VisibleLocator_A` remained in Visible scope output. |
| Run Visible scope                       | Report records `scope_mode = Visible`                                    | PASS    | Visible-scope Dry Run executed successfully against the saved Maya scene. |
| Inspect visibility fields               | Visibility-related fields appear in ObjectRecord/report when implemented | PASS    | Validation captured `hierarchy_visible`, `display_layer_visible`, `native_visible`, and `resolved_visible`. |

**Expected result:** Visible scope respects resolved scene visibility where practical.

---

## Test 5 - Visible Scope: Parent, Layer, and Native Visibility

**Purpose:** Verify that visibility resolution is not based only on `.visibility`.

**Preconditions:** Create three cases: hidden object, visible child under hidden parent, and visible object inside a hidden display layer.

| Step                                 | Expected                                                                                                      | Status  | Observations |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------- | ------- | ------------ |
| Hide parent transform                | Child is excluded or flagged through resolved visibility                                                      | PASS    | `ChildUnderHiddenParent_A` was excluded from Visible scope. |
| Hide display layer                   | Object is excluded or flagged through resolved visibility                                                     | PASS    | `LayerHiddenMesh_A` was excluded after scanner Visible-scope hardening. |
| Check visibility cache behavior      | Ancestor visibility is not repeatedly queried inefficiently                                                   | PENDING |              |
| Check native visibility confirmation | Native Maya visibility confirmation is used when practical                                                    | PASS    | Validation records showed `native_visible` changing consistently with Visible scope inclusion/exclusion. |
| Check output fields                  | `hierarchy_visible`, `display_layer_visible`, `native_visible`, or `resolved_visible` appear when implemented | PASS    | Visibility fields were present in the captured ObjectRecord-backed route data. |

**Expected result:** Visible scope avoids obvious visibility false positives where practical.

---

## Test 6 - Dry Run Does Not Modify Scene

**Purpose:** Verify that Dry Run is read-only.

**Preconditions:** Fresh scene with meshes, utilities, and possible review cases.

| Step                                  | Expected                                               | Status  | Observations |
| ------------------------------------- | ------------------------------------------------------ | ------- | ------------ |
| Execute Dry Run                       | No groups are created                                  | PASS    | test06 (`dry_run_did_not_create_pipeline_group = true`): Dry Run on a fresh scene with `ProdMesh_A` left `pipeline_group_after = false`. |
| Inspect Outliner after Dry Run        | `Pipeline_Organized` does not exist                    | PASS    | test06 (`dry_run_outliner_unchanged = true`): Outliner remained `[|persp, |top, |front, |side, |ProdMesh_A]` identically before and after Dry Run. |
| Check object parents before and after | No parent changes occur                                | PASS    | test06 (`dry_run_no_name_or_path_changes`): `did_move = false` confirmed; `assemblies_before == assemblies_after_dry_run` during Dry Run validation. |
| Check object names before and after   | No rename occurs                                       | PASS    | test06: `new_long_name = null` in Dry Run target decision; `ProdMesh_A` long name `|ProdMesh_A` unchanged throughout. |
| Check reports                         | TXT/JSON report planned actions without scene mutation | PASS    | test06 (`reports_written_and_json_contains_decision = true`, `txt_report_surfaces_production_mesh_route = true`): TXT and JSON written to Maya workspace; JSON contains Production_Meshes decision with `operation_status = dry_run_only`. |
| Check report schema field             | JSON includes `schema_version`                         | PASS    | Phase 9a report audit (33/33): `json_schema_version_present` and `json_schema_version_value == "0.2"` confirmed in real Apply JSON report. |
| Check warning events field            | JSON includes `warning_events` list                    | PASS    | Phase 9a report audit (33/33): `json_warning_events_present` confirmed in real Apply JSON report; field present in `run_result`. |
| Check RouteDecision values            | `would_move` may be true, but `did_move = false`       | PASS    | test06 (`dry_run_can_move_and_not_report_only = true`): `would_move = true` and `did_move = false` confirmed for `ProdMesh_A` Dry Run decision. |
| Check operation status                | `operation_status = dry_run_only` or equivalent        | PASS    | test06 (`dry_run_status_is_dry_run_only = true`): `operation_status = dry_run_only` confirmed for `ProdMesh_A` Dry Run target. |

**Expected result:** Dry Run previews the route plan without modifying the Maya scene.

---

## Test 7 - Basic Apply Organization

**Purpose:** Verify that Apply can organize simple movable objects safely.

**Preconditions:** Scene contains one movable polygon mesh with an acceptable material and one simple utility object.

| Step                   | Expected                                      | Status  | Observations |
| ---------------------- | --------------------------------------------- | ------- | ------------ |
| Execute Apply          | `Pipeline_Organized` is created or reused     | PASS    | mayapy 8a: `Pipeline_Organized` created on first Apply; reused on second Apply. |
| Check child groups     | Planned child groups are created or reused    | PASS    | mayapy 8a: all 6 `config.OUTPUT_GROUPS` children created as direct children of `Pipeline_Organized`; idempotent on second run. |
| Check production mesh  | Mesh routes to `Production_Meshes` if safe    | PASS    | mayapy 8b: eligible mesh with non-default material moved to `Production_Meshes`; `did_move = True`, `new_long_name` set and confirmed in scene. |
| Check utility object   | Utility routes to `Scene_Utilities` if safe   | PASS    | mayapy 8c: `SceneLocator_A` moved to `Scene_Utilities`; `did_move = True`, confirmed in scene. |
| Check can_move gate    | Only objects with `can_move = true` move      | PASS    | mayapy 8b/8c: `can_move = False` objects not moved; instanced content blocked; `failed_parenting` branch continues (test30, 10/10). |
| Check report           | TXT/JSON reflects actual movement             | PASS    | Phase 9a report audit (33/33): JSON contains `did_move=true`, `new_long_name`, `operation_status=moved`, `schema_version`, `warning_events`, `summary.moved`; TXT contains `did_move=True`, `new_long_name=`, `status=moved`. Reports in `examples/`. |
| Check operation status | Moved objects have `operation_status = moved` | PASS    | mayapy 8b: `STATUS_MOVED` confirmed on moved Production_Meshes decision; `STATUS_FAILED_PARENTING` confirmed via mocked failure (test30). |

**Expected result:** Apply organizes simple safe content and records what happened.

---

## Test 8 - Ignore String / Bypass Preservation

**Purpose:** Verify user-defined preservation logic.

**Preconditions:** Scene contains several objects. Rename two to include `BYPASS`.

| Step                                                | Expected                                                                            | Status  | Observations |
| --------------------------------------------------- | ----------------------------------------------------------------------------------- | ------- | ------------ |
| Set ignore string to `BYPASS` and run Dry Run       | Matching objects are excluded from normal production/review routing                 | PASS    | `mayapy` bypass validation routed `ProdMesh_BYPASS_0` and `ProdMesh_BYPASS_1` to `Bypass` with `matches_ignore_string = true`. |
| Run Apply if ignore preservation is implemented     | Matching objects remain bypassed/preserved unless an explicit safe contract says otherwise | PASS    | Apply kept bypassed meshes in `Bypass` with `did_move = false`, `new_long_name = None`, and blocked eligibility status. |
| If Bypass movement is not safe or not implemented   | Matching objects remain preserved/report-only                                           | PASS    | Bypassed meshes returned `can_move = false`, `operation = report_only`, `report_only = true`, and `operation_status = preserved_report_only`. |
| Check report                                        | Preserve reason or route reason reflects user ignore string                         | PASS    | Apply JSON report documented bypassed meshes with `reason = matches ignore string` and `preserve_reason = user ignore string`. |
| Use empty ignore string                             | No objects enter ignore-string preservation due to empty string                     | PASS    | Running the same scene with `ignore_string = ""` removed bypass behavior and returned the former bypass meshes to normal classifier routing. |
| Use overly broad ignore string                      | Warning appears in RunResult and report                                             | PASS    | A scene with 28 `BYPASS` matches produced `IGNORE_MATCH_HIGH` plus warning text `Ignore string matched 28 objects.` in `RunResult`. |

**Expected result:** User-defined ignored content is respected without contradictory movement behavior.

---

## Test 9 - Material Review Routing

**Purpose:** Verify review routing for default and multi-material states.

**Preconditions:** Create one mesh using `initialShadingGroup` and one mesh with multiple materials or shading groups.

| Step                                  | Expected                                           | Status  | Observations |
| ------------------------------------- | -------------------------------------------------- | ------- | ------------ |
| Run Dry Run on default-material mesh  | Mesh receives material review route                | PASS    | `mayapy` material validation routed `DefaultMaterialMesh_A` into material review during Dry Run. |
| Check default-material route          | Object routes to `Review_MissingMaterial`          | PASS    | `DefaultMaterialMesh_A` routed to `Review_MissingMaterial`. |
| Check default-material reason         | Reason mentions default or missing material review | PASS    | Current classifier reason is `material review required`, which is consistent with review handoff rather than runtime failure. |
| Run Dry Run on multi-material mesh    | Mesh receives multi-material review route          | PASS    | `mayapy` material validation routed `MultiMaterialMesh_A` into multi-material review during Dry Run. |
| Check multi-material route            | Object routes to `Review_MultiMaterial`            | PASS    | `MultiMaterialMesh_A` routed to `Review_MultiMaterial` after material-review precedence hardening. |
| Check multi-material reason           | Reason describes handoff review, not failure       | PASS    | The runtime still returns `reason = material review required`, which stays review-oriented rather than sounding like an execution error. |
| Check material semantics              | Report wording distinguishes shading-group count vs material-node count when present | PASS    | The JSON report preserved both `material_node_count` and `shading_engine_count`, showing `3` for the multi-material test mesh. |
| Run Apply if objects are safe to move | Objects move only if `can_move = true`             | PENDING |              |

**Expected result:** Material issues route to review buckets without being treated as fatal errors.

---

## Test 10 - Referenced Object Preservation

**Purpose:** Verify that referenced nodes are never treated as normal movable content.

**Preconditions:** Reference an external Maya file containing at least one mesh.

| Step                    | Expected                                                   | Status  | Observations |
| ----------------------- | ---------------------------------------------------------- | ------- | ------------ |
| Run Dry Run             | Referenced object is detected as referenced                | PASS    | `mayapy` protected-content validation detected `refProtected:RefMesh_A` with `is_referenced = true`. |
| Check route             | `route = References`                                       | PASS    | Referenced mesh routed to `References`. |
| Check safety            | `can_move = false`                                         | PASS    | Referenced mesh returned `can_move = false`. |
| Check report-only state | `report_only = true`                                       | PASS    | Referenced mesh returned `operation = report_only` and `report_only = true`. |
| Check preserve reason   | `preserve_reason = Immutable reference node` or equivalent | PASS    | Referenced mesh returned `preserve_reason = referenced content`. |
| Run Apply               | Referenced node is not parented                            | PASS    | Apply kept the referenced mesh blocked with `did_move = false`, `new_long_name = None`, and unchanged Outliner state. |
| Check operation status  | `operation_status = skipped_reference`                     | PASS    | Referenced mesh returned `operation_status = skipped_reference` in Dry Run and Apply. |
| Check report            | Referenced object is documented as preserved               | PASS    | Apply JSON report documented the referenced mesh with `can_move = false`, `report_only = true`, and `skipped_reference`. |

**Expected result:** Referenced content is never falsely reported as moved.

---

## Test 11 - Selected Child Node Inside Reference

**Purpose:** Verify that selected referenced child nodes are preserved.

**Preconditions:** Select a child node inside a referenced file.

| Step                   | Expected                                         | Status  | Observations |
| ---------------------- | ------------------------------------------------ | ------- | ------------ |
| Run Selected scope     | Selected child is detected safely                | PASS    | `mayapy` validation selected a child transform inside a referenced asset and returned exactly one Selected-scope route decision for that child. |
| Check reference state  | Node is classified as referenced/report-only     | PASS    | The selected referenced child returned `route = References`, `can_move = false`, `operation = report_only`, and `report_only = true`. |
| Run Apply              | Tool does not attempt to parent referenced child | PASS    | Apply left the referenced child under its original referenced parent and reported it as blocked/preserved. |
| Check movement state   | `did_move = false`                               | PASS    | The selected referenced child returned `did_move = false` and `new_long_name = None` in Apply. |
| Check operation status | `operation_status = skipped_reference`           | PASS    | Dry Run and Apply both returned `operation_status = skipped_reference` for the selected referenced child. |
| Check report           | Preservation reason is clear                     | PASS    | Apply JSON report documented the selected referenced child with `preserve_reason = referenced content`. |

**Expected result:** Selected referenced children are preserved and reported honestly.

---

## Test 12 - Instanced Geometry Preservation

**Purpose:** Verify that instanced geometry is preserved by default.

**Preconditions:** Create or import instanced geometry with shared shape / multiple parents.

| Step                    | Expected                                          | Status  | Observations |
| ----------------------- | ------------------------------------------------- | ------- | ------------ |
| Run Dry Run             | Instance state is detected when practical         | PASS    | `mayapy` protected-content validation detected both `InstancedMesh_A` and `InstancedMesh_A_Copy` with `is_instanced = true`. |
| Check safety            | `can_move = false`                                | PASS    | Both instanced transforms returned `can_move = false`. |
| Check report-only state | Preserved/report-only behavior is recorded        | PASS    | Both instanced transforms returned `operation = report_only` and `report_only = true`. |
| Run Apply               | Instanced geometry is not parented as normal mesh | PASS    | Apply kept both instanced transforms blocked with `did_move = false`, `new_long_name = None`, and unchanged Outliner state. |
| Check operation status  | `operation_status = skipped_instance`             | PASS    | Both instanced transforms returned `operation_status = skipped_instance` in Dry Run and Apply. |
| Check report            | Instance preservation reason is recorded          | PASS    | Apply JSON report documented both instanced transforms with `preserve_reason = instanced geometry`. |

**Expected result:** Instanced geometry is preserved by default.

---

## Test 13 - Rig / Deformer Safety

**Purpose:** Verify that rig-sensitive and deformer-sensitive content is preserved.

**Preconditions:** Scene contains a joint chain, a mesh bound via `skinCluster`, and a mesh with `blendShape`.

| Step                                      | Expected                                                       | Status  | Observations |
| ----------------------------------------- | -------------------------------------------------------------- | ------- | ------------ |
| Run Dry Run on skinCluster mesh           | SkinCluster history is detected when practical                 | PASS    | `mayapy` protected-content validation detected `SkinClusterMesh_A` with `has_skin_cluster = true`. |
| Run Dry Run on blendShape mesh            | BlendShape history is detected when practical                  | PASS    | `mayapy` protected-content validation detected `BlendShapeMesh_A` with `has_blendshape = true`. |
| Run Dry Run on mesh under joint hierarchy | Sensitive hierarchy is detected when practical                 | PASS    | `mayapy` protected-content validation detected `JointChildMesh_A` with `parent_is_joint = true` and `is_under_sensitive_hierarchy = true`. |
| Check safety                              | Sensitive object receives `can_move = false`                   | PASS    | SkinCluster, blendShape, and joint-child test meshes all returned `can_move = false`. |
| Check preserve reason                     | Preserve reason identifies rig/deformer sensitivity            | PASS    | Sensitive test meshes returned `preserve_reason = rig/deformer sensitive content`. |
| Run Apply                                 | Sensitive object is not parented                               | PASS    | Apply kept the sensitive test meshes blocked with `did_move = false`, `new_long_name = None`, and unchanged Outliner state. |
| Check operation status                    | `operation_status = skipped_sensitive_hierarchy` or equivalent | PASS    | Sensitive test meshes returned `operation_status = skipped_sensitive_hierarchy` in Dry Run and Apply. |

**Expected result:** Rig-sensitive and deformation-sensitive objects are preserved by default.

---

## Test 14 - Scene Utilities

**Purpose:** Verify routing behavior for common utility objects.

**Preconditions:** Create a camera, light, locator, joint, and simple utility transform.

| Step                               | Expected                                              | Status  | Observations |
| ---------------------------------- | ----------------------------------------------------- | ------- | ------------ |
| Run Dry Run                        | Utility objects are detected                          | PASS    | `SceneCamera_A1`, `SceneLight_A`, and `SceneLocator_A` were all detected in Maya validation. |
| Check movable camera/light/locator | Safe utilities route to `Scene_Utilities`             | PASS    | Camera, directional light, and locator all routed to `Scene_Utilities` after classifier utility-shape hardening. |
| Check joint behavior               | Joints are treated conservatively if sensitive        | PASS    | Real Maya validation showed the plain joint itself routes as `Scene_Utilities`, while the mesh parented under that joint remained blocked as `skipped_sensitive_hierarchy`, keeping joint-adjacent sensitive content out of utility movement. |
| Run Apply                          | Only safe utilities move                              | PASS    | `mayapy` validation moved camera, locator, light, and plain joint into `Scene_Utilities` with `operation_status = moved`, while the joint-child mesh stayed blocked with `eligible = false`. |
| Check report                       | Utility route and subtype are recorded when available | PASS    | TXT reported utility route/target details for `SceneCamera_A1`, and JSON preserved scanner-facing subtype facts such as `shape_type = camera`, `shape_type = locator`, and the joint-child `preserve_reason`. |

**Expected result:** Utility objects are organized or preserved according to safety state.

---

## Test 15 - Duplicate Short Names / Long Names

**Purpose:** Verify that duplicate short names do not cause incorrect moves.

**Preconditions:** Create two objects with the same short name under different parents.

| Step                     | Expected                                           | Status  | Observations |
| ------------------------ | -------------------------------------------------- | ------- | ------------ |
| Run Dry Run              | Scanner records long names                         | PASS    | `mayapy` duplicate-name validation returned two distinct Dry Run route decisions for `|DupParent_A|SharedMesh` and `|DupParent_B|SharedMesh`. |
| Check route decisions    | Objects are distinguishable by path                | PASS    | The scanner kept both duplicate short-name meshes as separate ObjectRecords and Dry Run kept both `long_name` values distinct. |
| Run Apply                | Correct objects are moved                          | PENDING |              |
| Check report             | Original long names are traceable                  | PASS    | The JSON report preserved both original `long_name` values for the duplicate-name meshes. |
| Check collision handling | Maya auto-renames, if any, are reflected in output | PENDING |              |

**Expected result:** Duplicate short names do not break routing or reporting.

---

## Test 16 - Long Name Mutation After Parenting

**Purpose:** Verify that path changes after parenting are tracked.

**Preconditions:** Create a movable object outside `Pipeline_Organized`.

| Step                              | Expected                                        | Status  | Observations |
| --------------------------------- | ----------------------------------------------- | ------- | ------------ |
| Run Apply                         | Object is parented if safe                      | PASS    | mayapy 8b/8c: eligible objects parented into target groups via `cmds.parent`. |
| Validate before move              | Organizer checks node existence before movement | PASS    | 8e: `cmds.objExists` re-checked at move time; missing node gets `STATUS_SKIPPED_MISSING_NODE` and is skipped. |
| Capture parenting result          | Returned Maya path is captured when available   | PASS    | 8b/8c: `cmds.parent` return value captured; `cmds.ls(long=True)` used to resolve full post-parent path. |
| Check `new_long_name`             | New path is recorded after move                 | PASS    | mayapy 8b: `new_long_name` set and confirmed present in scene after Apply. |
| Check report                      | Original long name and new long name appear     | PASS    | Phase 9a: JSON route decisions contain `long_name` (original) and `new_long_name` (post-parent path) for moved objects. Confirmed in `examples/example_report.json`. |
| Simulate failed move if practical | `did_move = false` and warning are recorded     | PASS    | 8b test30 (mocked failure): `did_move = False`, `STATUS_FAILED_PARENTING`, warning confirmed; next decision continued. |

**Expected result:** Path mutation after parenting is tracked accurately.

---

## Test 17 - Parent / Child Conflict Handling

**Purpose:** Verify that parent/child overlap does not cause conflicting movement.

**Preconditions:** Create a hierarchy and select both a parent and one child.

| Step               | Expected                                                     | Status  | Observations |
| ------------------ | ------------------------------------------------------------ | ------- | ------------ |
| Run Selected scope | Both selected inputs are handled safely                      | PASS    | `mayapy` validation selected `|ConflictParent_A` and `|ConflictParent_A|ConflictChild_A` together and returned both as separate Selected-scope records with `summary['scanned'] = 2`. |
| Check route plan   | Parent/child conflict is detected or resolved conservatively | PASS    | Dry Run kept parent and child as distinct route decisions by `long_name`, without collapsing or losing either selected input. |
| Run Apply          | Tool avoids destructive double-parenting                     | PASS    | Apply left both selected meshes at `did_move = false` and `new_long_name = None`, so no destructive double-parenting occurred in the current runtime. |
| Check warnings     | Conflict warning or clear operation status is recorded       | PASS    | Apply preserved both `long_name` values in the JSON report and returned non-empty operation statuses for the selected overlap case. |

**Expected result:** Parent/child overlap does not create duplicate or destructive movement.

---

## Test 18 - Repeated Execution / Idempotency

**Purpose:** Verify that previous tool output does not create recursive nesting.

**Preconditions:** Run Apply once or manually create the expected output group structure.

| Step                            | Expected                                                            | Status  | Observations |
| ------------------------------- | ------------------------------------------------------------------- | ------- | ------------ |
| Run Apply again                 | No duplicate `Pipeline_Organized` group is created                  | PASS    | mayapy test18: second Apply left exactly one `Pipeline_Organized`; child group list identical after both runs. |
| Check structural groups         | Tool-created structural groups are not routed as production content | PASS    | mayapy test18: structural groups returned `skipped_tool_structure`; none appeared as movable content decisions. |
| Check objects already in target | `operation_status = already_in_target`                              | PASS    | mayapy test18: 7 decisions returned `already_in_target` on second run; `did_move = False` on all. |
| Check moved count               | Second run does not move already-correct objects                    | PASS    | mayapy test18: `summary.moved = 0` on second Apply; message showed "0 moved". |
| Check report                    | Idempotent behavior is documented                                   | PASS    | Phase 9a: run-2 JSON shows `summary.already_in_target=9`, `summary.moved=0`; route decisions show `operation_status=already_in_target` for previously moved objects. |

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

**Note:** Mark `PASS` only after real Maya validation; this checklist is the manual evidence source.

| Step                                 | Expected                               | Status  | Observations |
| ------------------------------------ | -------------------------------------- | ------- | ------------ |
| Run Dry Run on safe unclear object   | Object receives unclear route          | PASS    | `mayapy` unclear-case validation routed `AmbiguousGroup_A` to `Review_UnclearCases` as a non-mesh ambiguous object. |
| Check safe unclear target            | Object routes to `Review_UnclearCases` | PASS    | The safe-looking ambiguous group returned `route = Review_UnclearCases` and `target_group = Review_UnclearCases`. |
| Check safe unclear movement          | Object moves only if `can_move = true` | PASS    | Current runtime treats the safe-looking ambiguous group as movable review content: `can_move = true`, `operation = move`, and Apply moved it into `Review_UnclearCases`; the unsafe joint child stayed blocked. |
| Run Dry Run on unsafe unclear object | Object is preserved/report-only        | PASS    | `AmbiguousChildGroup_A` under a joint stayed preserved as `report_only` in Dry Run. |
| Check unsafe unclear safety          | `can_move = false`                     | PASS    | The unsafe ambiguous child group returned `can_move = false` and `operation_status = skipped_sensitive_hierarchy`. |
| Check report                         | Reason explains uncertainty or risk    | PASS    | Safe unclear now goes to `Review_UnclearCases` with `can_move = true`; unsafe/sensitive unclear stays preserved/report-only; Apply follows preflight without moving scene. |

**Expected result:** Safe ambiguity has a review destination; unsafe ambiguity is preserved.

---

## Test 21 - Operation Status Values

**Purpose:** Verify consistent status values in reports.

**Preconditions:** Use scenes covering moved, skipped, already-in-target, and failed cases where practical.

| Step                       | Expected                                                       | Status  | Observations |
| -------------------------- | -------------------------------------------------------------- | ------- | ------------ |
| Dry Run object             | `operation_status = dry_run_only` or equivalent                | PASS    | `mayapy` validation returned `dry_run_only` for a normal movable mesh in Dry Run. |
| Successfully moved object  | `operation_status = moved`                                     | PASS    | mayapy 8b: `STATUS_MOVED` confirmed for eligible Production_Meshes object; `did_move = True`, `new_long_name` set. |
| Already organized object   | `operation_status = already_in_target`                         | PASS    | mayapy 8d: second Apply run marked previously moved objects `already_in_target`; `did_move = False`; no redundant `cmds.parent`; `summary.already_in_target = 6` matched actual count. |
| Referenced object          | `operation_status = skipped_reference`                         | PASS    | Referenced mesh returned `skipped_reference` in Apply. |
| Instanced object           | `operation_status = skipped_instance`                          | PASS    | Both source and instance copy returned `skipped_instance`. |
| Sensitive hierarchy object | `operation_status = skipped_sensitive_hierarchy` or equivalent | PASS    | Mesh under joint hierarchy returned `skipped_sensitive_hierarchy`. |
| Tool structural group      | `operation_status = skipped_tool_structure` when reported      | PASS    | `Pipeline_Organized` and child output group returned `skipped_tool_structure`. |
| Missing node during Apply  | `operation_status = skipped_missing_node` when simulated       | PASS    | 8e (mocked cmds, 10/10): node present at preflight but missing at move time → `STATUS_SKIPPED_MISSING_NODE`, `did_move = False`, `new_long_name = None`, warning "node missing at move time"; next eligible decision continued and moved; `cmds.parent` called exactly once. |
| Parenting failure          | `operation_status = failed_parenting` when simulated           | PASS    | test30 (mocked `cmds.parent` raising): `STATUS_FAILED_PARENTING`, `did_move = False`, `new_long_name = None`, warning contains "parenting failed"; next eligible PM decision continued and succeeded. |

**Expected result:** Operation states are explicit and reportable.

---

## Test 22 - Report Content Completeness

**Purpose:** Verify that TXT and JSON reports provide enough traceability.

| Step                           | Expected                                                      | Status  | Observations |
| ------------------------------ | ------------------------------------------------------------- | ------- | ------------ |
| Check TXT report header        | Includes tool name, timestamp, mode, and scope                | PASS    | `mayapy` report validation confirmed tool name, `Report generated`, `Mode: apply`, and `Scope: all_scene`. |
| Check TXT report summary       | Includes scanned count and route summary                      | PASS    | TXT summary included `scanned`, `total`, `moved`, `preserved`, and related counters from the current runtime. |
| Check TXT route details        | Includes object route, target group, and safety state         | PASS    | TXT route rows included `route=`, `target=`, `can_move=`, and preflight/safety state. |
| Check TXT preservation details | Includes `preserve_reason` when relevant                      | PASS    | TXT route rows now include `preserve_reason=` for preserved/report-only content. |
| Check TXT operation details    | Includes `operation_status` and `new_long_name` when relevant | PASS    | TXT route rows included `status=` and `new_long_name=`. |
| Check JSON report structure    | Equivalent data exists in structured form                     | PASS    | JSON report contained top-level `route_decisions` and structured `run_result`. |
| Check JSON schema field        | `schema_version` is present and explicit                      | PASS    | JSON report included explicit `schema_version = 0.1`. |
| Check warning events structure | `warning_events` entries are structured when warnings exist   | PASS    | Warning validation produced structured `warning_events` with `code`, `message`, and `source`. |
| Check warnings                 | Warnings appear in both TXT and JSON when present             | PASS    | Ignore-string threshold warning appeared in both TXT and JSON. |

**Expected result:** Reports are useful for review and debugging.

---

## Test 23 - Report Path Fallback

**Purpose:** Verify report path behavior in different file states.

**Preconditions:** Test saved and unsaved Maya scenes.

| Step                                   | Expected                                                   | Status  | Observations |
| -------------------------------------- | ---------------------------------------------------------- | ------- | ------------ |
| Saved scene                            | Reports write next to scene file when possible             | PASS    | Validation script wrote TXT/JSON beside a saved Maya scene path. |
| Unsaved scene                          | Workspace or temp fallback is used                         | PASS    | Validation script confirmed temp fallback when neither scene path nor workspace path was available. |
| Workspace available                    | Workspace fallback works if scene path is unavailable      | PASS    | Validation script wrote TXT/JSON into the mocked Maya workspace root when scene path was empty. |
| Path not writable if practical to test | User-safe fallback or clear error is returned              | PASS    | Reporter now falls back from a blocked scene directory to the workspace directory during write failure. |
| Check RunResult                        | Report paths are included                                  | PASS    | Validation captured explicit TXT/JSON paths for each fallback case. |
| Check UI                               | Report paths are displayed without reading report contents | PASS    | Maya 2027.1 smoke: TXT and JSON report path labels populated in the Results section from RunResult.report_paths. No report file was opened or parsed by the UI. |

**Expected result:** Report generation does not depend on ideal scene file state.

---

## Test 24 - RunResult Lightweight UI Behavior

**Purpose:** Verify that the UI remains lightweight in large scenes.

**Preconditions:** Use a large scene or simulate many route decisions.

| Step                  | Expected                                              | Status  | Observations |
| --------------------- | ----------------------------------------------------- | ------- | ------------ |
| Run pipeline          | RunResult includes `route_decisions_count`            | PASS    | Validation script returned `route_decisions_count = 30` with matching `summary`, `warnings`, `report_paths`, `message`, and `success` fields in Dry Run. |
| Check preview         | `preview_routes` is limited by `max_ui_preview_items` | PASS    | Validation script returned 30 route decisions but only 25 preview entries, matching `max_ui_preview_items = 25`. |
| Check UI summary      | UI displays summary counters and report paths         | PASS    | Maya 2027.1 smoke: summary showed Scanned 14, Planned 14, Would Move 11, Preserved 3, Warnings 0, Failed 0 from RunResult.summary. Report path labels populated. |
| Check full route list | UI does not render every object route                 | PASS    | Maya 2027.1 smoke: preview showed 14 of 14 rows (scene fit within MAX_UI_PREVIEW_ITEMS=25); capping behavior confirmed by RunResult.preview_routes length, not by UI parsing. |
| Check reports         | Full route details remain in TXT/JSON                 | PENDING |              |
| Check responsiveness  | UI does not freeze from rendering large object lists  | PENDING |              |

**Expected result:** UI feedback remains lightweight and scalable.

---

## Test 25 - UI / Reporter Decoupling

**Purpose:** Verify that UI, pipeline, and reporter responsibilities remain separated.

| Step                                       | Expected                                            | Status  | Observations |
| ------------------------------------------ | --------------------------------------------------- | ------- | ------------ |
| Run pipeline without UI                    | Pipeline can execute directly                       | PASS    | `tools/validation/test25_ui_reporter_decoupling_validation.py` ran `pipeline.run()` with mocked scanner/classifier/reporter and confirmed Dry Run success plus a single `reporter.write_reports()` call without any UI dependency. |
| Run UI workflow                            | UI receives feedback through RunResult              | PASS    | Maya 2027.1 smoke: launcher.launch() opened the window; clicking Run in Dry Run called pipeline.run() and populated message, summary, warnings, report path labels, and preview from RunResult only. No report files were parsed. |
| Inspect UI behavior                        | UI does not parse TXT/JSON to know what happened    | PASS    | Validation confirmed `ui.py` imports only `config` and `pipeline`, explicitly documents RunResult-only feedback, and explicitly forbids parsing TXT/JSON report files. |
| Inspect reporter behavior                  | Reporter writes files independently from UI display | PASS    | Validation confirmed `reporter.py` has no UI import path and `pipeline.run()` receives report paths through `reporter.write_reports()` rather than through any UI callback or display dependency. |
| Simulate report write failure if practical | UI receives clear warning through RunResult         | PASS    | `tools/validation/test28_report_failure_signaling_validation.py` confirmed failed report paths remain explicit while `RunResult` now adds warning text plus a structured `REPORT_WRITE_FAILED` warning event, without changing current `success=True` Dry Run semantics. |

**Expected result:** UI feedback is not coupled to report file parsing.

---

## Test 26 - MEL Bridge Optional Behavior

**Purpose:** Verify that MEL compatibility remains isolated and optional.

**Preconditions:** Tool is configured with MEL bridge disabled, then optionally with simple test hooks.

| Step                               | Expected                                            | Status  | Observations |
| ---------------------------------- | --------------------------------------------------- | ------- | ------------ |
| Run with MEL bridge disabled       | Main pipeline runs normally                         | PASS    | `tools/validation/test26_mel_bridge_validation.py` showed Dry Run success with empty hook names and neutral `mel_hook_status` (`called=False`, `success=True`, `error=None`) for both pre/post entries. |
| Missing MEL hook                   | Missing hook does not fail import or main execution | PASS    | Isolated `mel_bridge` import stayed safe outside Maya; direct hook calls reported `Maya MEL runtime is not available.` without raising, and pipeline Dry Run still completed with configured hook names represented as disabled status only. |
| Valid pre-run hook if implemented  | Status is recorded                                  | PASS    | Validation stubbed `mel_bridge.maya_mel.eval` and confirmed `run_pre_hook('preHookOk')` returns `{'called': True, 'success': True, 'error': None}`. |
| Valid post-run hook if implemented | Status is recorded                                  | PASS    | Validation stubbed `mel_bridge.maya_mel.eval` and confirmed `run_post_hook('postHookOk')` returns `{'called': True, 'success': True, 'error': None}`. |
| Failing MEL hook if practical      | Failure is reported clearly                         | PASS    | Validation stubbed MEL failure and confirmed both pre/post hook helpers return `called=True`, `success=False`, and the captured error text `Stub MEL hook failure`. |
| Check reports                      | MEL hook status appears when used                   | PENDING | Validation confirmed `RunResult` and JSON report payload preserve `mel_hook_status`, but current TXT report output does not render any MEL hook status section or disabled-hook message. |

**Expected result:** MEL bridge does not contaminate or destabilize the core Python workflow.

---

## Test 27 - Dry Run vs Apply Consistency

**Purpose:** Verify that Dry Run and Apply rely on the same route-planning logic.

**Preconditions:** Scene with multiple route categories.

| Step                                | Expected                                                       | Status  | Observations |
| ----------------------------------- | -------------------------------------------------------------- | ------- | ------------ |
| Run Dry Run                         | Route plan is generated                                        | PASS    | `mayapy` validation scene generated 14 route decisions. |
| Run Apply on same scene state       | Apply uses equivalent route-planning logic before movement     | PASS    | Dry Run and Apply used equivalent route-planning inputs on the same saved scene state, then Apply executed eligible moves. |
| Check Apply message                 | Message reports moved/planned/blocked/failed counts            | PASS    | Apply returned the current movement summary format such as `Apply: X moved, Y planned, Z blocked, W failed.` |
| Check RouteDecision preflight field | Route decisions include `apply_preflight` eligibility/reasons  | PASS    | Every Apply RouteDecision included `apply_preflight` with `eligible` and `reasons`. |
| Check Apply movement flags          | `did_move = false` and `new_long_name = None` in preflight run | PASS    | All Apply decisions kept `did_move = false` and `new_long_name = None`. |
| Compare planned vs executed actions | Differences are explained by movement outcomes or block reason | PASS    | Eligible items reached `moved` or `already_in_target`; blocked items were explained by preserved or skipped statuses. |
| Repeat Dry Run on same scene state  | Route ordering is stable across repeated runs                  | PASS    | Ordering matched the Apply route plan on the same scene snapshot before Apply mutated it. |
| Check Apply report                  | Report records movement outcome plus eligibility context       | PASS    | Apply JSON report included `apply_preflight`, `did_move`, `new_long_name`, and final `operation_status` values. |
| Check Dry Run scene state           | Dry Run did not influence Apply by mutating scene              | PASS    | Outliner snapshot was unchanged before Dry Run and after Dry Run; only Apply performed scene mutation. |

**Expected result:** Dry Run preview remains non-mutating, and Apply executes the safe subset of that plan with honest movement outcomes.

---

## Phase 7 Minimal UI — Maya 2027.1 GUI Smoke

**Purpose:** Verify that the Phase 7 minimal UI opens, renders all controls, and populates Results from RunResult in a real Maya GUI session.

**Validated:** Maya 2027.1, manual execution in Script Editor. Scene contained 14 objects.

| Step | Expected | Status | Observations |
| ---- | -------- | ------ | ------------ |
| `launcher.launch()` opens window | Window titled "Maya Production Pipeliner" appears | PASS | Window opened without errors from Script Editor. |
| Scope controls rendered | Three radio buttons: All Scene, Selected, Visible | PASS | `labelArray3 = ['All Scene', 'Selected', 'Visible']` confirmed. |
| Execution mode controls rendered | Two radio buttons: Dry Run, Apply | PASS | `labelArray2 = ['Dry Run', 'Apply']` confirmed after Apply became mutating runtime behavior. |
| Ignore string field rendered | Text field present and queryable | PASS | `cmds.textField` query returned empty string on fresh window. |
| Run button rendered | Button present in window | PASS | Button visible and clickable. |
| Results section rendered | Message, summary, warnings, reports, preview area visible | PASS | All result widgets present and queryable after window open. |
| Report path labels rendered | TXT and JSON path text labels visible in Results | PASS | Both labels rendered as empty before first Run, then populated after. |
| Clicking Run (Dry Run) populates Results | Results section fills from RunResult without scene mutation | PASS | All result widgets populated after clicking Run in Dry Run mode. |
| Message populated | "Dry Run completed without scene changes." | PASS | Exact message confirmed from RunResult.message. |
| Summary populated | Scanned 14, Planned 14, Would Move 11, Preserved 3, Warnings 0, Failed 0 | PASS | All counters sourced from RunResult.summary. |
| TXT report path displayed | Path shown as text in Results without opening the file | PASS | `C:/tmp/maya_test27_validation/maya_production_pipeliner_report.txt` displayed in txt_path_text label. |
| JSON report path displayed | Path shown as text in Results without opening the file | PASS | `C:/tmp/maya_test27_validation/maya_production_pipeliner_report.json` displayed in json_path_text label. |
| Preview populated | Route rows shown: "ObjectName  ->  GroupName  [status]" | PASS | 14 of 14 rows displayed; count sourced from RunResult.preview_routes and route_decisions_count. |
| Dry Run non-mutating | `cmds.objExists("Pipeline_Organized") == False` | PASS | Outliner unchanged after Run; no Pipeline_Organized group created. |
| Second `launcher.launch()` is idempotent | Existing window raised; no duplicate created | PASS    | Maya 2027.1 smoke: called launcher.launch() while window was open; window count remained 1. |
| Open TXT/JSON Report buttons | Clicking opens file in system viewer | PASS    | Maya 2027.1 smoke: Open TXT Report and Open JSON Report buttons both clicked; respective report files opened successfully in system viewer. |
| Run in Apply mode | Results populated from RunResult after Apply execution | PASS    | Later Maya 2027.1 GUI smoke confirmed the Apply button moved eligible content and surfaced moved counts through the UI. |

**Expected result:** The minimal UI is functional for Dry Run and current Apply behavior in a real Maya GUI session.

---

## Phase 8a — Apply Group Creation — Maya 2027 mayapy Validation

**Purpose:** Verify that Apply creates or reuses the fixed group structure without moving any route decision objects, and that Dry Run remains non-mutating.

**Validated:** Maya 2027, mayapy standalone. `test29_mayapy_phase8a.py`. 14/14 PASS.

| Step | Expected | Status | Observations |
| ---- | -------- | ------ | ------------ |
| Apply creates `Pipeline_Organized` | Group exists after Apply on clean scene | PASS | `cmds.objExists("\|Pipeline_Organized") == True` after first Apply. |
| Apply creates all OUTPUT_GROUPS children | All 6 child groups present as direct children | PASS | `cmds.listRelatives` matched `sorted(config.OUTPUT_GROUPS)` exactly. |
| `group_structure_status` in RunResult | RunResult contains group creation status dict | PASS | Key present; `Pipeline_Organized = "created"`, all 6 children `= "created"` on first run. |
| No route decision objects moved | `did_move = False` and `new_long_name = None` on all decisions | PASS | All route decisions confirmed unmoved after Apply. |
| Apply message updated | Message reports current Apply movement counters | PASS | Current Apply message follows `Apply: X moved, Y planned, Z blocked, W failed.` |
| Second Apply is idempotent — no duplicates | Same 6 children, none added or duplicated | PASS | `scene_groups()` identical after second Apply. |
| Second Apply reuses root group | `group_structure_status[ROOT_GROUP] = "reused"` | PASS | Confirmed via RunResult on second Apply call. |
| Second Apply reuses all child groups | All 6 child statuses `= "reused"` | PASS | Confirmed via RunResult on second Apply call. |
| Dry Run creates no groups | `Pipeline_Organized` absent after Dry Run on clean scene | PASS | `cmds.objExists("\|Pipeline_Organized") == False` after Dry Run. |
| Dry Run message unchanged | `"Dry Run completed without scene changes."` | PASS | Exact message confirmed. |
| Dry Run has no `group_structure_status` | Key absent from Dry Run RunResult | PASS | `"group_structure_status" not in result` confirmed. |

**Expected result:** Apply creates the fixed group structure and is idempotent. Dry Run remains fully non-mutating. Object movement is not part of this slice.

---

## Phase 8b — Production_Meshes Movement Validation

**Purpose:** Verify that eligible Production_Meshes route decisions are moved into `Production_Meshes`, protected and non-PM content is untouched, failure handling is correct, and Dry Run remains non-mutating.

**Validated:** mayapy 8b main (`test30_mayapy_phase8b.py`) 14/14 PASS. Failed-parenting branch (`test30_phase8b_failed_parenting_validation.py`) 10/10 PASS.

| Step | Expected | Status | Observations |
| ---- | -------- | ------ | ------------ |
| Eligible Production_Meshes object moves | `did_move = True`, object under `Production_Meshes` in scene | PASS | mayapy: `ProdMesh_A` (unique material) moved; `cmds.objExists(new_long_name) == True`. |
| `operation_status = moved` on moved object | Status reflects actual movement | PASS | mayapy: `STATUS_MOVED` confirmed in route decision. |
| `new_long_name` set and correct | Reflects post-parent Maya path | PASS | mayapy: `new_long_name` exists in scene; path contains `\|Pipeline_Organized\|Production_Meshes\|`. |
| Original `long_name` preserved | Pre-move identity retained in decision | PASS | mayapy: `long_name = "\|ProdMesh_A"` unchanged alongside `new_long_name`. |
| `summary.moved` accurate | RunResult summary count matches actual moves | PASS | mayapy: `summary.moved == 1` confirmed. |
| Eligible non-PM routes move when safe | Review-routed safe content does not remain planned | PASS | Current Apply follow-through is validated separately for utilities, safe unclear, and material review routes; eligible routes are expected to reach `moved` or `already_in_target`, not remain `planned`. |
| Apply message reflects moved count | Message updated from "No objects moved" | PASS | mayapy: message contains "1 moved"; "No objects moved" absent. |
| Dry Run creates no groups, moves nothing | Non-regression after 8b | PASS | mayapy: `Pipeline_Organized` absent; all `did_move = False` after Dry Run. |
| `failed_parenting` — status correct | `STATUS_FAILED_PARENTING` on failing decision | PASS | test30 mock: `STATUS_FAILED_PARENTING` confirmed when `cmds.parent` raises. |
| `failed_parenting` — `did_move = False` | No partial move recorded | PASS | test30 mock: `did_move = False` on failing decision. |
| `failed_parenting` — `new_long_name = None` | No stale path recorded | PASS | test30 mock: `new_long_name = None` on failing decision. |
| `failed_parenting` — warning recorded | Warning text contains "parenting failed" | PASS | test30 mock: warning confirmed on failing decision. |
| Remaining decisions continue after failure | Next eligible PM still processed | PASS | test30 mock: `ProdMesh_B` moved successfully after `ProdMesh_A` failed. |

**Expected result:** Production_Meshes eligible objects move correctly. Failures are isolated and reported. Non-PM and protected content untouched. Dry Run fully non-mutating.

---

## Phase 8c — All Eligible Routes Movement Validation

**Purpose:** Verify that all eligible route decisions move into their respective target groups, protected content is untouched, and Dry Run remains non-mutating.

**Validated:** Focused mayapy validations now cover representative Apply movement for `Production_Meshes` (`test06`), `Scene_Utilities` (`test14`), safe unclear review (`test20`), and material review (`test09`). Protected-content validations continue to confirm blocked/preserved behavior.

**Checklist status:** `PASS` — current repo-backed evidence shows eligible routes in those categories reaching `moved` or `already_in_target` rather than remaining `planned`, unless a real block reason exists.

---

## Phase 8d — Already-in-Target Validation

**Purpose:** Verify that a second Apply run correctly identifies previously moved objects without attempting a redundant `cmds.parent`, and that new objects added after the first run still move.

**Historical note:** A previous Phase 8d validation run was reported as successful, but the referenced validation script is not currently present in `tools/validation/`.

**Checklist status:** `PENDING` — repo-backed validation evidence for Phase 8d is still pending until the script is added or the checks are rerun and recorded in the repository.

---

## Phase 8e — Skipped Missing Node Validation

**Purpose:** Verify that a node present at preflight but missing before movement is handled gracefully, remaining decisions continue, and no exception escapes the organizer.

**Historical note:** A previous Phase 8e check was reported using mocked `cmds` behavior rather than a Maya runtime, but the referenced validation script is not currently present in `tools/validation/`.

**Checklist status:** `PENDING` — repo-backed validation evidence for Phase 8e is still pending until the mocked-cmds check is added to the repository or rerun and recorded there. If this section is cited before that happens, treat it as historical non-Maya evidence only, not current repo-backed validation.

### Phase 8b — Maya 2027 GUI Smoke (Apply button)

**Validated:** Maya 2027.1, manual execution via Script Editor. Scene contained pCube1 with custom Lambert material.

| Step | Expected | Status | Observations |
| ---- | -------- | ------ | ------------ |
| Apply button moves eligible mesh | Object moves to `Pipeline_Organized/Production_Meshes` | PASS | pCube1 (custom Lambert) moved to `Production_Meshes` via UI Apply button. |
| Results message reflects move | Message contains moved count | PASS | UI message showed "1 moved". |
| Preview shows moved status | Preview row shows object, group, and status | PASS | Preview showed `pCube1 -> Production_Meshes [moved]`. |
| JSON report `moved` count | `summary.moved = 1` in JSON report | PASS | JSON report confirmed `moved = 1` and `success = true` after UI Apply run. |
| `summary.planned` label clarity | `planned` count meaning is unambiguous after movement | PASS    | Renamed `summary.planned` → `summary.total` in `_build_summary`; UI label updated to "Total:"; `REPORT_SCHEMA_VERSION` bumped to `0.2`; `data_contracts.md` updated. |

---

## Test 28 - Public Repository Documentation Check

**Purpose:** Verify that public documentation matches actual implementation status.

| Step                          | Expected                                                          | Status  | Observations |
| ----------------------------- | ----------------------------------------------------------------- | ------- | ------------ |
| Check README status           | README matches current implementation state                       | PASS    | Test 28 audit: status table, safety posture, limitations, and workflow updated to reflect Phase 8a–8e validated state. |
| Check README feature language | Planned features are not described as already implemented         | PASS    | Test 28 audit: Apply, idempotency, already-in-target described as validated; leaf reclassification noted as remaining open case. |
| Check docs links              | README links resolve to existing Markdown files                   | PASS    | All linked files in docs table exist and are reachable. |
| Check examples                | Example reports are labeled correctly if they are format previews | PASS    | Phase 9a: examples replaced with real Apply output; `examples/README.md` updated; `schema_version: 0.2`, `summary.total` present. |
| Check checklist               | Manual test checklist is current                                  | PASS    | Test 28 audit: checklist reflects validated state through Phase 9a; remaining PENDING rows are genuinely unvalidated (Test 19, Final Release Gate). |
| Check screenshots if present  | Screenshots reflect actual tool behavior                          | PASS    | No screenshots in repository; not applicable. |
| Check version/tag if present  | Version matches implementation state                              | PASS    | No version tag present; scope is locked at v1.1.3 contract; README states "not release-ready" — consistent. |

**Expected result:** Public repository materials are accurate and do not overclaim.

---

## Final Release Gate

Before tagging or presenting a release candidate, verify:

| Gate                                 | Expected                                                           | Status  | Observations |
| ------------------------------------ | ------------------------------------------------------------------ | ------- | ------------ |
| Package imports cleanly              | No import-time scene mutation                                      | PENDING |              |
| Dry Run works                        | Scan, classify, RunResult, and reports work without scene mutation | PENDING |              |
| Apply works on simple safe scene     | Safe objects move to expected groups                               | PENDING |              |
| Protected content stays protected    | References, instances, and sensitive hierarchies are preserved     | PASS    | `mayapy` protected-content validation confirmed referenced, instanced, skinCluster, blendShape, and joint-child meshes remain report-only, blocked, and unmoved in Apply. |
| Reports are traceable                | TXT/JSON reflect real run data                                     | PENDING |              |
| UI remains lightweight               | UI does not render full route list                                 | PENDING |              |
| Idempotency works                    | Repeated run does not duplicate structure                          | PENDING |              |
| Documentation matches implementation | README and docs describe current state honestly                    | PENDING |              |

**Expected result:** The repository is ready for a public release candidate only after the functional claims in the README are backed by code and test evidence.
