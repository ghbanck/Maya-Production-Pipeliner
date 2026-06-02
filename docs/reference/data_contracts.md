# Data Contracts

This document summarizes the lightweight runtime data surfaces used by Maya Production Pipeliner.

For frozen scope semantics and the broader contract language, see [`../planning/frozen_scope_contract_v1.1.3.md`](../planning/frozen_scope_contract_v1.1.3.md).

## ObjectRecord

`ObjectRecord` is the scanner output.

It is designed to hold factual scene observations only, including:

* object identity and long name;
* transform and shape information;
* material and shading state;
* visibility resolution fields;
* reference and instance state;
* rig/deformer sensitivity indicators;
* previous tool output markers;
* warnings.

`ObjectRecord` should not contain route decisions or scene mutation outcomes.

## RouteDecision

`RouteDecision` is the classifier output.

It is designed to describe what the tool plans or preserves for one object, including:

* route and target group;
* reason and preservation reason;
* warnings;
* `can_move`;
* `report_only`;
* `would_move`;
* `did_move`;
* `new_long_name`;
* `operation_status`.

During current Apply preflight, these decisions can also include eligibility annotations without mutating scene state.

## RunResult

`RunResult` is the lightweight execution summary returned to the UI or launcher.

It is intended to include:

* summary counters;
* warnings and warning events;
* report paths;
* execution and scope mode;
* ignore string;
* route decision count;
* preview routes;
* status message.

Full object-level details belong in reports rather than in heavy UI state.

## Operation Status Values

The project uses explicit operation status values instead of vague success/failure wording.

Current status model:

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

Not every status is currently reachable in the runtime. The checklist tracks which statuses have been validated in Maya and which remain gated behind future mutating Apply work.
