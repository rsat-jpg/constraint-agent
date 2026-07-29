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

### Finding overlap (graph warnings)

- Pure isolate bags (every step has no edges): `ISOLATED_STEP` only — not `DISCONNECTED_GRAPH`.
- Two or more real subgraphs (at least one component with ≥2 steps): `DISCONNECTED_GRAPH` only for steps outside the largest component.
- Chain + orphan: `DISCONNECTED_GRAPH` owns the orphan; `ISOLATED_STEP` is suppressed for those step ids.
- A single weakly connected component: neither graph warning.

## Schema stability

- Package version: `0.1.0` (`verifiable_planning.__version__`)
- Plan schema version field: `Plan.version` defaults to `"0.1.0"` (`SCHEMA_VERSION`)
- Within **0.1.x**, public models (`Plan`, `Step`, `ValidationFinding`, `ValidationResult`) and `validate_plan` keep additive-compatible shapes. Breaking field or finding-code changes bump the version and are called out in the commit message.

## Project layout

```
verifiable_planning/                 # this project root
├── LICENSE
├── KNOWLEDGE_RUBRIC.md              # Governing knowledge contract
├── COMMIT_PROTOCOL.md               # Commit cadence and milestones
├── EXPANSION_GATE.md                # When / when-not to add adapters
├── README.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── examples.py                      # Positive + deliberate failure cases
├── verifiable_planning/             # Installable package
│   ├── __init__.py                  # Public exports (Validate core only)
│   ├── models.py                    # Plan, Step, findings, result
│   ├── validators.py                # Structural validators + graph
│   └── adapters/
│       └── llm_planner.py           # Optional LLM→Plan (Decision D1)
└── tests/
    ├── test_validators.py
    └── test_llm_planner_adapter.py
```

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

Optional extra (no pinned SDK): `pip install -e ".[llm]"`.

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
- No PDDL / classical planner integration
- No multi-agent orchestration
- No UI

Further expansion still requires a Decision in [`EXPANSION_GATE.md`](EXPANSION_GATE.md).

## Next natural increments

_Only after an approved decision in `EXPANSION_GATE.md`:_

- Optional PDDL export / import
- Runtime verification hooks

Still inside Validate (no gate decision required): one tighter structural rule family at a time.

## License

MIT — see [`LICENSE`](LICENSE).
