<h1 align="center">Maya Production Pipeliner</h1>

<p align="center">
  <strong>Safety-aware Maya scene organization for production handoff</strong>
</p>

<p align="center">
  A lightweight Maya Python utility being built to turn hard-to-read scene hierarchies into reviewable handoff structure.
</p>

<p align="center">
  <em>Before validation, production needs readable structure.</em>
</p>

---

## What It Is

Maya Production Pipeliner is a small Maya-native tooling project focused on one practical problem: making scene structure easier to read before deeper validation, export, review, or downstream handoff begins.

The tool is being built to:

* scan scene facts;
* classify objects into handoff routes;
* preserve unsafe content by default;
* preview planned actions through Dry Run;
* gate future Apply behavior behind explicit safety rules;
* write traceable TXT and JSON reports.

This repository is not a general validation framework, exporter, publisher, rig repair tool, material fixer, or studio pipeline replacement.

---

## Why It Exists

Maya scenes often become operationally messy before they become technically invalid. Production meshes, utilities, references, hidden objects, instanced geometry, rig-sensitive content, material issues, duplicate names, and previous tool output can all coexist in the same Outliner.

This project exists to make that first layer readable and reportable before anyone trusts later pipeline steps.

---

## Current Status

This repository is still in controlled implementation.

| Area | Status |
| --- | --- |
| Scope contract | Locked at v1.1.3 |
| Core runtime | Implemented in slices |
| Dry Run | Implemented and validated in focused checklist slices |
| Apply | Non-mutating preflight only |
| Mutating Apply | Not implemented |
| UI | Early / partial |
| Release status | Not release-ready |

Treat planned behavior as planned until code and manual Maya validation evidence are both present in the repository.

---

## Core Workflow

```text
Scan scene facts
-> classify route decisions
-> build a route plan
-> preserve unsafe content
-> preview through Dry Run or Apply preflight
-> write TXT/JSON reports
```

Current safety posture:

* Dry Run is strictly observational and non-mutating.
* Apply currently runs as preflight and reports eligibility without scene mutation.
* Future mutating Apply remains gated behind explicit safety contracts and additional validation.

---

## Safety Posture

This project favors preservation over convenience.

Unsafe or unclear content should be preserved and reported rather than moved. Referenced nodes, instanced geometry, rig/deformer-sensitive content, internal tool structure, and other unsafe cases are intentionally handled conservatively.

For the architecture rationale and future Apply boundaries, see the linked docs below rather than treating this README as the full contract.

---

## Documentation

The README is the public entry point. Deeper material lives in focused docs.

| Document | Purpose |
| --- | --- |
| [`docs/usage.md`](docs/usage.md) | Public usage model, scope modes, execution modes, and launch expectations |
| [`docs/architecture/pipeline_overview.md`](docs/architecture/pipeline_overview.md) | Pipeline flow, module boundaries, output structure, and architecture graph |
| [`docs/reference/data_contracts.md`](docs/reference/data_contracts.md) | `ObjectRecord`, `RouteDecision`, `RunResult`, and operation status reference |
| [`docs/reference/reporting.md`](docs/reference/reporting.md) | TXT/JSON report structure, warning model, and report path behavior |
| [`docs/architecture/apply_safety_contract.md`](docs/architecture/apply_safety_contract.md) | Current Apply preflight boundary and future Safe Apply contract |
| [`docs/architecture/defensive_design.md`](docs/architecture/defensive_design.md) | Defensive design rationale and risk framing |
| [`docs/planning/frozen_scope_contract_v1.1.3.md`](docs/planning/frozen_scope_contract_v1.1.3.md) | Scope authority, boundaries, and frozen contract details |
| [`docs/planning/implementation_plan.md`](docs/planning/implementation_plan.md) | Build order, gates, and implementation phases |
| [`docs/testing/manual_test_checklist.md`](docs/testing/manual_test_checklist.md) | Manual Maya validation evidence by slice |
| [`docs/planning/project_bible_v1.1.3.md`](docs/planning/project_bible_v1.1.3.md) | Original product rationale and development context |

---

## Installation and Launch

Functional installation guidance is still conservative by design.

Current intended manual setup:

1. Clone or download this repository.
2. Add the repository root to Maya's Python path using a local Maya path setup method such as `userSetup.py` or a `.pth` file.
3. Launch Maya and call the public launcher from the Script Editor.

Intended launch pattern:

```python
from maya_production_pipeliner import launcher
launcher.launch()
```

Treat that launch path as the intended public interface, not as proof of a finished end-user installation flow.

---

## Limitations

Current limitations include:

* mutating Apply is not implemented;
* no claim of production-ready or release-ready behavior;
* no promise of full validation, publishing, export correctness, shader repair, namespace conflict resolution, telemetry, or generalized pipeline runtime features;
* no guarantee that every planned feature in the frozen scope is already implemented.

Examples and planning docs may describe target behavior. The manual checklist and runtime code are the sources to consult for what has actually been validated.

---

## License

MIT License. See [LICENSE](LICENSE).

---

## Author Notice

Designed and developed by **Gustavo Henrique Banck**.

This is a public development repository. Implementation status is tracked openly as the tool is built in small vertical slices.
