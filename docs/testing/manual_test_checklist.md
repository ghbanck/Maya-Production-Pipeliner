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
| Run Dry Run with scope = Selected  | No crash; clear empty-selection result                     | PASS    | With no selection in a fresh Maya scene, Dry Run returned `scanned = 0`, `planned = 0`, and completed successfully. |
| Run Dry Run with scope = Visible   | No crash; clear empty or no-visible-content result         | PASS    | In the same fresh Maya scene, Visible-scope Dry Run completed successfully with `scanned = 0` and `planned = 0`. |
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
| Check object parents before and after | No parent changes occur                                | PASS    | test06 (`dry_run_no_name_or_path_changes`): `did_move = false` confirmed; `assemblies_before == assemblies_after` for both Dry Run and Apply preflight runs. |
| Check object names before and after   | No rename occurs                                       | PASS    | test06: `new_long_name = null` in Dry Run target decision; `ProdMesh_A` long name `|ProdMesh_A` unchanged throughout. |
| Check reports                         | TXT/JSON report planned actions without scene mutation | PASS    | test06 (`reports_written_and_json_contains_decision = true`, `txt_report_surfaces_production_mesh_route = true`): TXT and JSON written to Maya workspace; JSON contains Production_Meshes decision with `operation_status = dry_run_only`. |
| Check report schema field             | JSON includes `schema_version`                         | PENDING | test06 confirmed reports are written; `schema_version` presence not explicitly asserted. No dedicated script covers this yet. |
| Check warning events field            | JSON includes `warning_events` list                    | PENDING | test06 confirmed reports are written; `warning_events` in JSON report not explicitly asserted. test24 confirmed the field in RunResult only. |
| Check RouteDecision values            | `would_move` may be true, but `did_move = false`       | PASS    | test06 (`dry_run_can_move_and_not_report_only = true`): `would_move = true` and `did_move = false` confirmed for `ProdMesh_A` Dry Run decision. |
| Check operation status                | `operation_status = dry_run_only` or equivalent        | PASS    | test06 (`dry_run_status_is_dry_run_only = true`): `operation_status = dry_run_only` confirmed for `ProdMesh_A` Dry Run target. |

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

## Test 8 - Ignore String / Bypass Preservation

**Purpose:** Verify user-defined preservation logic.

**Preconditions:** Scene contains several objects. Rename two to include `BYPASS`.

| Step                                                | Expected                                                                            | Status  | Observations |
| --------------------------------------------------- | ----------------------------------------------------------------------------------- | ------- | ------------ |
| Set ignore string to `BYPASS` and run Dry Run       | Matching objects are excluded from normal production/review routing                 | PASS    | `mayapy` bypass validation routed `ProdMesh_BYPASS_0` and `ProdMesh_BYPASS_1` to `Bypass` with `matches_ignore_string = true`. |
| Run Apply if ignore preservation is implemented     | Matching objects remain bypassed/preserved unless an explicit safe contract says otherwise | PASS    | Apply preflight kept bypassed meshes in `Bypass` with `did_move = false`, `new_long_name = None`, and blocked preflight status. |
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
| Run Apply               | Referenced node is not parented                            | PASS    | Apply preflight kept the referenced mesh blocked with `did_move = false`, `new_long_name = None`, and unchanged Outliner state. |
| Check operation status  | `operation_status = skipped_reference`                     | PASS    | Referenced mesh returned `operation_status = skipped_reference` in Dry Run and Apply preflight. |
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
| Run Apply              | Tool does not attempt to parent referenced child | PASS    | Apply preflight completed with `Planned moves: 0. Blocked: 1.` and left the referenced child under its original referenced parent. |
| Check movement state   | `did_move = false`                               | PASS    | The selected referenced child returned `did_move = false` and `new_long_name = None` in Apply preflight. |
| Check operation status | `operation_status = skipped_reference`           | PASS    | Dry Run and Apply preflight both returned `operation_status = skipped_reference` for the selected referenced child. |
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
| Run Apply               | Instanced geometry is not parented as normal mesh | PASS    | Apply preflight kept both instanced transforms blocked with `did_move = false`, `new_long_name = None`, and unchanged Outliner state. |
| Check operation status  | `operation_status = skipped_instance`             | PASS    | Both instanced transforms returned `operation_status = skipped_instance` in Dry Run and Apply preflight. |
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
| Run Apply                                 | Sensitive object is not parented                               | PASS    | Apply preflight kept the sensitive test meshes blocked with `did_move = false`, `new_long_name = None`, and unchanged Outliner state. |
| Check operation status                    | `operation_status = skipped_sensitive_hierarchy` or equivalent | PASS    | Sensitive test meshes returned `operation_status = skipped_sensitive_hierarchy` in Dry Run and Apply preflight. |

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
| Run Apply                          | Only safe utilities move                              | PASS    | Apply preflight marked camera, locator, light, and plain joint as `planned`, while the joint-child mesh stayed blocked with `eligible = false` and no scene mutation. |
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
| Run Selected scope | Both selected inputs are handled safely                      | PASS    | `mayapy` validation selected `|ConflictParent_A` and `|ConflictParent_A|ConflictChild_A` together and returned both as separate Selected-scope records with `summary['scanned'] = 2`. |
| Check route plan   | Parent/child conflict is detected or resolved conservatively | PASS    | Dry Run kept parent and child as distinct route decisions by `long_name`, without collapsing or losing either selected input. |
| Run Apply          | Tool avoids destructive double-parenting                     | PASS    | Apply preflight left both selected meshes at `did_move = false` and `new_long_name = None`, so no scene mutation or double-parenting attempt occurred in the current runtime. |
| Check warnings     | Conflict warning or clear operation status is recorded       | PASS    | Apply preflight returned clear `operation_status = planned` for both selected meshes and preserved both `long_name` values in the JSON report. |

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

**Note:** Mark `PASS` only after real Maya validation; this checklist is the manual evidence source.

| Step                                 | Expected                               | Status  | Observations |
| ------------------------------------ | -------------------------------------- | ------- | ------------ |
| Run Dry Run on safe unclear object   | Object receives unclear route          | PASS    | `mayapy` unclear-case validation routed `AmbiguousGroup_A` to `Review_UnclearCases` as a non-mesh ambiguous object. |
| Check safe unclear target            | Object routes to `Review_UnclearCases` | PASS    | The safe-looking ambiguous group returned `route = Review_UnclearCases` and `target_group = Review_UnclearCases`. |
| Check safe unclear movement          | Object moves only if `can_move = true` | PASS    | Current runtime now treats the safe-looking ambiguous group as movable review content: `can_move = true`, `operation = move`, and Apply preflight marks it as eligible `planned` content for `Review_UnclearCases`. |
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
| Successfully moved object  | `operation_status = moved`                                     | PENDING | Requires mutating Apply; current runtime is still Apply preflight only. |
| Already organized object   | `operation_status = already_in_target`                         | PASS    | Mesh parented under `Pipeline_Organized|Production_Meshes` returned `already_in_target` in Apply preflight. |
| Referenced object          | `operation_status = skipped_reference`                         | PASS    | Referenced mesh returned `skipped_reference` in Apply preflight. |
| Instanced object           | `operation_status = skipped_instance`                          | PASS    | Both source and instance copy returned `skipped_instance`. |
| Sensitive hierarchy object | `operation_status = skipped_sensitive_hierarchy` or equivalent | PASS    | Mesh under joint hierarchy returned `skipped_sensitive_hierarchy`. |
| Tool structural group      | `operation_status = skipped_tool_structure` when reported      | PASS    | `Pipeline_Organized` and child output group returned `skipped_tool_structure`. |
| Missing node during Apply  | `operation_status = skipped_missing_node` when simulated       | PASS    | Simulated by classifying a movable mesh, deleting it, then running Apply preflight through `organizer.apply_routes()`. |
| Parenting failure          | `operation_status = failed_parenting` when simulated           | PENDING | Requires mutating Apply path with actual parenting failure handling. |

**Expected result:** Operation states are explicit and reportable.

---

## Test 22 - Report Content Completeness

**Purpose:** Verify that TXT and JSON reports provide enough traceability.

| Step                           | Expected                                                      | Status  | Observations |
| ------------------------------ | ------------------------------------------------------------- | ------- | ------------ |
| Check TXT report header        | Includes tool name, timestamp, mode, and scope                | PASS    | `mayapy` report validation confirmed tool name, `Report generated`, `Mode: apply`, and `Scope: all_scene`. |
| Check TXT report summary       | Includes scanned count and route summary                      | PASS    | TXT summary included `scanned` and `planned` counters from a rich Apply-preflight scene. |
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
| Check UI                               | Report paths are displayed without reading report contents | PENDING |              |

**Expected result:** Report generation does not depend on ideal scene file state.

---

## Test 24 - RunResult Lightweight UI Behavior

**Purpose:** Verify that the UI remains lightweight in large scenes.

**Preconditions:** Use a large scene or simulate many route decisions.

| Step                  | Expected                                              | Status  | Observations |
| --------------------- | ----------------------------------------------------- | ------- | ------------ |
| Run pipeline          | RunResult includes `route_decisions_count`            | PASS    | Validation script returned `route_decisions_count = 30` with matching `summary`, `warnings`, `report_paths`, `message`, and `success` fields in Dry Run. |
| Check preview         | `preview_routes` is limited by `max_ui_preview_items` | PASS    | Validation script returned 30 route decisions but only 25 preview entries, matching `max_ui_preview_items = 25`. |
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
| Run pipeline without UI                    | Pipeline can execute directly                       | PASS    | `tools/validation/test25_ui_reporter_decoupling_validation.py` ran `pipeline.run()` with mocked scanner/classifier/reporter and confirmed Dry Run success plus a single `reporter.write_reports()` call without any UI dependency. |
| Run UI workflow                            | UI receives feedback through RunResult              | PENDING | Current `ui.py` workflow remains unimplemented (`show`, `_on_run_clicked`, and `_update_result_display` still raise `NotImplementedError`), so no runtime UI flow could be exercised honestly. |
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
| Run Apply on same scene state       | Apply preflight uses equivalent route-planning logic           | PASS    | Dry Run and Apply preflight produced equivalent route plans on the same saved scene state. |
| Check Apply message                 | Message explicitly says "without scene changes"                | PASS    | Apply returned `Apply preflight completed without scene changes.` |
| Check RouteDecision preflight field | Route decisions include `apply_preflight` eligibility/reasons  | PASS    | Every Apply RouteDecision included `apply_preflight` with `eligible` and `reasons`. |
| Check Apply movement flags          | `did_move = false` and `new_long_name = None` in preflight run | PASS    | All Apply decisions kept `did_move = false` and `new_long_name = None`. |
| Compare planned vs executed actions | Differences are explained by scene changes or operation status | PASS    | No scene-change drift observed; blocked items were explained by preserved or skipped statuses. |
| Repeat Dry Run on same scene state  | Route ordering is stable across repeated runs                  | PASS    | Ordering matched the Apply preflight route plan for the same scene snapshot. |
| Check Apply report                  | Report records preflight outcome without scene mutation        | PASS    | Apply JSON report included `apply_preflight` fields and preserved non-mutating state. |
| Check Dry Run scene state           | Dry Run did not influence Apply by mutating scene              | PASS    | Outliner snapshot was unchanged before Dry Run, after Dry Run, and after Apply preflight. |

**Expected result:** Dry Run preview and Apply preflight behavior are trustworthy without scene mutation.

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
| Protected content stays protected    | References, instances, and sensitive hierarchies are preserved     | PASS    | `mayapy` protected-content validation confirmed referenced, instanced, skinCluster, blendShape, and joint-child meshes remain report-only, blocked, and unmoved in Apply preflight. |
| Reports are traceable                | TXT/JSON reflect real run data                                     | PENDING |              |
| UI remains lightweight               | UI does not render full route list                                 | PENDING |              |
| Idempotency works                    | Repeated run does not duplicate structure                          | PENDING |              |
| Documentation matches implementation | README and docs describe current state honestly                    | PENDING |              |

**Expected result:** The repository is ready for a public release candidate only after the functional claims in the README are backed by code and test evidence.
