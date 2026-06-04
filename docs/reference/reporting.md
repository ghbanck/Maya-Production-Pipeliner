# Reporting

This document summarizes the reporting model used by Maya Production Pipeliner.

For the broader safety contract behind reporting, see [`../architecture/defensive_design.md`](../architecture/defensive_design.md).

## Report Formats

The tool writes:

* TXT reports for readable review;
* JSON reports for structured inspection.

Reports are intended to make each run traceable rather than decorative.

## Expected Report Content

Current report structure is designed to capture:

* tool name and timestamp;
* execution mode and scope mode;
* ignore string;
* summary counters;
* warnings;
* route decisions;
* target groups;
* operation status;
* `new_long_name` when relevant;
* preservation and preflight context when relevant;
* report paths;
* warning events in structured form;
* optional MEL hook status when present in runtime output.

For validated unclear-case routing, TXT and JSON reports should reflect `route`, `target_group`, `can_move`, `report_only`, `operation_status`, and `preserve_reason` when present. For Apply preflight runs, they should also reflect `apply_preflight`. Safe unclear review content may appear as movable review content in Dry Run and as `planned` in Apply preflight, while unsafe or sensitive unclear content remains preserved/report-only. No schema version bump is needed unless the JSON structure changes.

## TXT Reports

TXT reports are intended for quick human review.

Current TXT output focuses on:

* run header;
* summary counters;
* warning section;
* one row per route decision with route, target, safety state, operation state, and preservation context.

TXT should remain readable even when the JSON report contains deeper structure.

## JSON Reports

JSON reports are intended for structured review and future tooling compatibility.

Current JSON output includes:

* top-level `schema_version`;
* top-level `route_decisions`;
* structured `run_result`;
* warning events as dictionaries with fields such as `code`, `message`, and `source`.

The presence of JSON structure does not mean the schema is permanently integration-stable. Schema/version behavior should still be treated conservatively.

## Warning Model

Warnings should be visible in both TXT and JSON outputs when they occur.

The project is moving toward explicit warning events so validation can inspect warnings without relying only on free-form text.

## Report Path Fallback

Current report path fallback is intended to follow this order:

```text
saved scene directory
-> Maya workspace directory
-> user-safe temp fallback
```

## Examples

The `examples/` directory contains report examples and previews. Treat them as examples unless they are clearly identified as generated from current runtime behavior.
