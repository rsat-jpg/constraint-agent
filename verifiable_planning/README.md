# Verifiable Planning — Plan-Validate-Execute Core

Minimal, inspectable, framework-agnostic structural validation for multi-step agent plans.

## Purpose

Early planning errors are a dominant cause of long-horizon agent failure.  
This core implements the **Validate** stage of Plan-Validate-Execute:

1. Accept a typed plan
2. Run deterministic structural checks
3. Return structured findings + suggested repairs
4. Allow execution only when the plan is structurally sound

No LLM. No external planners. Pure Python + pydantic + networkx.

## Quickstart

Python 3.10+. From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Validate a plan in a few lines:

```python
from verifiable_planning import Plan, Step, validate_plan

plan = Plan(
    id="demo",
    goal="Ship a checked summary",
    steps=[
        Step(id="gather", description="Collect sources"),
        Step(id="write", description="Draft summary", depends_on=["gather"],
             expected_outcome="Markdown summary ready for review"),
    ],
)
result = validate_plan(plan)
print(result.is_valid, [f.code for f in result.findings])
```

Or run the bundled demos and tests:

```bash
python3 examples.py
python3 examples_runtime.py
python3 examples_llm.py
python3 examples_pddl.py
python3 examples_planner.py
python3 -m pytest -q
```

Runtime-only install (no pytest): `pip install -r requirements.txt` then keep this directory on `PYTHONPATH`, or use `pip install -e .`.

## Current status (v0.1)

Structural validators only:

| Check                         | Severity | Description                                                      |
|-------------------------------|----------|------------------------------------------------------------------|
| EMPTY_PLAN                    | error    | No steps present                                                 |
| DUPLICATE_STEP_ID             | error    | Repeated step identifiers                                        |
| UNKNOWN_DEPENDENCY            | error    | depends_on references a non-existent step                        |
| SELF_DEPENDENCY               | error    | Step lists its own id in depends_on                              |
| DEPENDENCY_CYCLE              | error    | Cycle in the dependency graph (multi-node; self-loops use SELF_DEPENDENCY) |
| DUPLICATE_DEPENDENCY          | warning  | depends_on lists the same step id more than once                 |
| REDUNDANT_DEPENDENCY          | warning  | depends_on lists an ancestor already implied by another dep      |
| ISOLATED_STEP                 | warning  | Step with no edges in a multi-step plan                          |
| DISCONNECTED_GRAPH            | warning  | depends_on graph has multiple weakly connected components        |
| IRREVERSIBLE_NO_OUTCOME       | warning  | Irreversible step lacks expected_outcome                         |
| PRECONDITION_NOT_IN_DEPENDS_ON| warning  | Precondition names a step id omitted from depends_on             |
| MISSING_TERMINAL_OUTCOME      | warning  | No terminal step declares expected_outcome (goal-coverage proxy) |
| MULTIPLE_TERMINALS            | warning  | Multi-step DAG has more than one sink (fork without join)        |

Free-form (non-step-id) strings in `Step.preconditions` are **ignored** by structural Validate; Decision D3 PDDL export makes them inspectable, and convention-`FORMAL_*` (`check_unestablished_preconditions`) emits findings for them under documented mapping conventions.

### Finding overlap (graph warnings)

- Pure isolate bags (every step has no edges): `ISOLATED_STEP` only — not `DISCONNECTED_GRAPH`.
- Two or more real subgraphs (at least one component with ≥2 steps): `DISCONNECTED_GRAPH` only for steps outside the largest component.
- Chain + orphan: `DISCONNECTED_GRAPH` owns the orphan; `ISOLATED_STEP` is suppressed for those step ids.
- A single weakly connected component: neither graph warning.
- Fork without join (one component, multiple sinks): `MULTIPLE_TERMINALS` — may also co-fire with isolate bags or disconnected multi-sink plans.

## Schema stability & Validate surface freeze

- Package version: `0.1.0` (`verifiable_planning.__version__`)
- Plan schema version field: `Plan.version` defaults to `"0.1.0"` (`SCHEMA_VERSION`)
- Within **0.1.x**, public models (`Plan`, `Step`, `ValidationFinding`, `ValidationResult`) and `validate_plan` / `build_graph` keep additive-compatible shapes.

**Validate surface freeze (v0.1):** the **13 structural** finding codes in [`verifiable_planning/finding_codes.py`](verifiable_planning/finding_codes.py) (and their error vs warning severity classes) are the stable structural Validate contract for `0.1.x`. Coverage and known overlaps are locked in [`EVIDENCE_CORPUS.md`](EVIDENCE_CORPUS.md); an invariant test refuses silent code-set drift. Optional adapter namespaces (e.g. `RUNTIME_*` behind Decision D2) are **not** part of this frozen structural set.

| Frozen for `0.1.x` | Still allowed in `0.1.x` |
|--------------------|-------------------------|
| Those 13 structural finding code strings + severity classes | Docs, examples, evidence fixtures, tests that do not change Validate outcomes |
| Public Validate API shapes (additive-compatible only) | Bug fixes that restore documented intent (`fix:` + evidence) |
| Default: **no new structural finding codes** | Thin adapters only behind an [`EXPANSION_GATE.md`](EXPANSION_GATE.md) Decision (may use separate code namespaces) |

**Unfreeze (structural):** new structural finding code, severity flip, or breaking model field → bump package version (prefer `0.2.0` for surface expansion; `0.1.x` patch only for true bug fixes that do not expand the surface) and call it out in the commit message. Known finding overlaps are documented, not “fixed,” under this freeze.

## Project layout

```
verifiable_planning/                 # this project root
├── LICENSE
├── CHANGELOG.md                     # Release / freeze notes
├── KNOWLEDGE_RUBRIC.md              # Governing knowledge contract
├── COMMIT_PROTOCOL.md               # Commit cadence and milestones
├── EXPANSION_GATE.md                # When / when-not to add adapters
├── EVIDENCE_CORPUS.md               # LLM-shaped fixture matrix (high-signal proof)
├── README.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── examples.py                      # Positive + deliberate failure cases (Validate)
├── examples_runtime.py              # Plan → Validate → Runtime demo (Decision D2)
├── examples_llm.py                  # Goal → Plan → Validate demo (Decision D1)
├── examples_pddl.py                 # Plan → Validate → formal → PDDL demo (Decision D3)
├── examples_planner.py              # Plan → Validate → planner-gated demo (Decision D4)
├── verifiable_planning/             # Installable package
│   ├── __init__.py                  # Public exports (Validate core only)
│   ├── models.py                    # Plan, Step, findings, result
│   ├── finding_codes.py             # Frozen 0.1.x finding code strings
│   ├── validators.py                # Structural validators + graph
│   └── adapters/
│       ├── llm_planner.py           # Optional LLM→Plan (Decision D1)
│       ├── runtime_verify.py        # Optional trace verify (Decision D2)
│       ├── pddl_bridge.py           # Optional Plan→PDDL export + convention-FORMAL_* (Decision D3)
│       └── planner_bridge.py        # Optional planner-gated PLANNER_* (Decision D4)
└── tests/
    ├── corpus_loader.py
    ├── fixtures/llm_shaped/         # Evidence corpus JSON plans
    ├── test_validators.py
    ├── test_llm_planner_adapter.py
    ├── test_evidence_corpus.py
    ├── test_surface_freeze.py       # 0.1.x structural finding-code set lock
    ├── test_runtime_verify_adapter.py
    ├── test_pddl_bridge_adapter.py
    └── test_planner_bridge_adapter.py
```

## Evidence corpus

LLM-shaped plan fixtures with expected finding codes and documented overlaps: [`EVIDENCE_CORPUS.md`](EVIDENCE_CORPUS.md).  
Run: `python3 -m pytest -q tests/test_evidence_corpus.py` (no live model).

## Optional: LLM → Plan adapter (Decision D1)

Approved in [`EXPANSION_GATE.md`](EXPANSION_GATE.md). Emits a `Plan` from a goal via an **injected** `complete(prompt) -> str` callable — no SDK in core, and `validate_plan` stays the gate.

```python
from verifiable_planning import validate_plan
from verifiable_planning.adapters.llm_planner import plan_from_goal

def complete(prompt: str) -> str:
    # Wrap your model SDK here; must return Plan-shaped JSON.
    ...

plan = plan_from_goal("Prepare a research summary", complete)
result = validate_plan(plan)   # always Validate separately
```

Runnable demo: `python3 examples_llm.py` (fake completer happy path + deliberate `UNKNOWN_DEPENDENCY` failure; no API keys).  
Optional extra (no pinned SDK): `pip install -e ".[llm]"`.

## Optional: runtime trace verification (Decision D2)

Approved in [`EXPANSION_GATE.md`](EXPANSION_GATE.md). Compares an inspectable step-event stream to plan `depends_on` order and irreversible checkpoints. Structural `validate_plan` stays the offline gate; runtime codes use the `RUNTIME_*` namespace.

```python
from verifiable_planning import validate_plan
from verifiable_planning.adapters.runtime_verify import linear_trace, verify_trace

plan = ...  # structurally sound Plan
assert validate_plan(plan).is_valid

events = linear_trace(plan)          # demo/test emitter (topo start/complete)
# or inject events from your executor
result = verify_trace(plan, events)
print(result.is_valid, [f.code for f in result.findings])
```

Checks: `RUNTIME_UNKNOWN_STEP`, `RUNTIME_DEPENDENCY_ORDER`, `RUNTIME_INCOMPLETE`, `RUNTIME_MISSING_CHECKPOINT` (irreversible step without prior `CHECKPOINT` event).  
`linear_trace` emits `CHECKPOINT` immediately before `STARTED` for `is_irreversible` steps.  
Runnable demo: `python3 examples_runtime.py` (happy path + deliberate `RUNTIME_DEPENDENCY_ORDER` + irreversible checkpoint happy/missing failure).  
Optional extra: `pip install -e ".[runtime]"`.

## Optional: PDDL export + convention-FORMAL_* (Decision D3)

Approved in [`EXPANSION_GATE.md`](EXPANSION_GATE.md). **Export** maps a `Plan` to inspectable PDDL domain+problem text. **Convention-`FORMAL_*`** (`check_unestablished_preconditions`) emits structured findings for free-form precondition labels that are unestablished under documented mapping conventions. This is **not** planner reachability and is **not** sound w.r.t. full PDDL semantics. No planner binary; core stays PDDL-free.

```python
from verifiable_planning import validate_plan
from verifiable_planning.adapters.pddl_bridge import (
    plan_to_pddl,
    check_unestablished_preconditions,
    LOSSY_EDGES,
)

plan = ...  # may be structurally sound yet have free-form label gaps
assert validate_plan(plan).is_valid
formal = check_unestablished_preconditions(plan)  # FORMAL_* if free-form labels
print(plan_to_pddl(plan))   # see LOSSY_EDGES for what is / is not compiled
```

**v1 green path:** under current conventions no step establishes free-form (`p_*`) predicates — the only formal-clean plans are those with **no** free-form precondition labels.

Conventions (lossy): `depends_on` → `(done_*)` preconditions; non-step-id `preconditions` → `(p_*)`; `expected_outcome` / goal prose are comments only (not effects). `:init` is empty.  
Check: `FORMAL_UNESTABLISHED_PRECONDITION` (ERROR) for each free-form precondition label.  
Runnable demo: `python3 examples_pddl.py` (clean export + formal clean; deliberate `data_licensed` gap stays structurally VALID and fires formal ERROR).  
Optional extra: `pip install -e ".[pddl]"`.

## Optional: planner-gated checks (Decision D4)

Approved in [`EXPANSION_GATE.md`](EXPANSION_GATE.md). Runs an **injected** `run_planner(pddl) -> PlannerOutcome` over D3-exported PDDL and emits **`PLANNER_*`** findings. Distinct from convention-`FORMAL_*`. Not sound full PDDL semantics (lossy export). No required planner binary; core stays planner-free.

```python
from verifiable_planning import validate_plan
from verifiable_planning.adapters.pddl_bridge import plan_to_pddl
from verifiable_planning.adapters.planner_bridge import (
    check_plan_with_planner,
    PlannerOutcome,
    PlannerStatus,
)

def run_planner(pddl: str) -> PlannerOutcome:
    # Wrap your classical planner here; demos/tests inject a fake.
    ...

plan = ...
assert validate_plan(plan).is_valid
result = check_plan_with_planner(plan, run_planner)  # PLANNER_* if unsat / unavailable
_ = plan_to_pddl(plan)  # same export the runner receives
```

Codes: `PLANNER_GOAL_UNREACHABLE` (ERROR) when the runner reports unsat; `PLANNER_UNAVAILABLE` / `PLANNER_ERROR` (ERROR) when the runner is missing or fails — never silent success.  
v1 may overlap convention-`FORMAL_*` on the same label-gap fixture; namespaces stay distinct.  
Runnable demo: `python3 examples_planner.py` (injected fake planner only).  
Optional extra: `pip install -e ".[planner]"`.

## Knowledge contract

All design decisions are governed by [`KNOWLEDGE_RUBRIC.md`](KNOWLEDGE_RUBRIC.md).  
Read it before expanding the system.

## Commit protocol

When and how to commit is defined in [`COMMIT_PROTOCOL.md`](COMMIT_PROTOCOL.md).  
Commits mark proven increments; run the pre-commit checklist before each one.

## Expansion gate

Criteria for LLM / PDDL / runtime / multi-agent / UI work: [`EXPANSION_GATE.md`](EXPANSION_GATE.md).

## Scope discipline (v0.1)

- Structural **Validate** core stays LLM-free (no model calls inside validators)
- Optional LLM→Plan adapter exists behind Decision D1; core `__init__` does not import it
- Optional runtime trace verify exists behind Decision D2; core `__init__` does not import it
- Optional PDDL **export** + convention-`FORMAL_*` check exist behind Decision D3; no planner required; core `__init__` does not import them
- Optional planner-gated `PLANNER_*` check exists behind Decision D4; injected runner only; no required binary; core `__init__` does not import it
- No PDDL import sync / establishment convention for free-form labels (separate later Decisions)
- No multi-agent orchestration
- No UI

Further expansion still requires a Decision in [`EXPANSION_GATE.md`](EXPANSION_GATE.md).

## Next natural increments

The v0.1 structural Validate surface is **frozen** (see above). Default next work is **not** another structural finding code.

_Still adapter-side; each needs its own Decision or deepen — do not lump:_

- **Convention-`FORMAL_*` extensions** (D3): e.g. an explicit establishment convention so some free-form labels can be green without a planner; sanitize-collision findings
- **PDDL import sync** (D3 / Candidate B): separate job from findings
- Optional real classical planner binary wrapper behind the D4 injected `run_planner` seam (still never required for default demos/tests)

_Or deepen Decision D2 further (still adapter-side):_

- Richer event producers beyond `linear_trace`; additional execute-time checks

_Or after an explicit structural unfreeze / version bump:_

- New structural finding codes or severity/ownership retunes (including overlap coalescing)

## License

MIT — see [`LICENSE`](LICENSE).
