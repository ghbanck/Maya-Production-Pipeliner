# Apply Safety Contract

This document isolates the Apply boundary for Maya Production Pipeliner.

For the broader defensive rationale, see [`defensive_design.md`](defensive_design.md). For frozen scope authority, see [`../planning/frozen_scope_contract_v1.1.3.md`](../planning/frozen_scope_contract_v1.1.3.md).

## Current State

Apply is currently non-mutating preflight.

Current Apply behavior:

* evaluates route-decision eligibility;
* records preflight reasons;
* updates reportable operation state for preflight outcomes;
* keeps `did_move = false`;
* keeps `new_long_name = None`;
* does not create groups or move scene nodes.

This means current Apply is real runtime code, but it is still preflight-only runtime code.

## Mutation Boundary

Only `organizer.py` should own future scene-hierarchy mutation.

The scanner, classifier, reporter, pipeline, UI, and launcher should not silently widen Apply behavior by introducing mutation on their own.

## Safe Move Contract

A future move should be considered safe only when all required conditions are true at the moment of Apply:

* the route decision belongs to the current plan;
* `can_move = true`;
* `report_only = false`;
* the source node still exists;
* the source node is not referenced;
* the source node is not instanced geometry;
* the source node is not rig/deformer-sensitive;
* the source node is not internal tool structure;
* the target group exists or can be created safely;
* parenting will not create cyclic or invalid hierarchy;
* the object is not already in the target group unless reported as `already_in_target`;
* the post-parenting result can be validated.

If any required condition is false or unknown, the object should be preserved and reported rather than moved.

## Future Apply Lifecycle

The intended mutating lifecycle is:

```text
build route plan
-> validate move candidates
-> create or reuse groups
-> execute safe moves
-> validate outcomes
-> write reports
-> return RunResult
```

Maya is not transactional, so future Apply should assume partial failure is possible.

## Failure Policy

When mutating Apply is eventually implemented, it should:

* continue only when remaining decisions can still be handled independently;
* record `failed_parenting` when parenting fails;
* record `skipped_missing_node` when a node disappears before movement;
* avoid hiding partial failure behind a vague success summary;
* surface failures and warnings in reports and `RunResult`.

Rollback is not part of the current scope and should not be implied.
