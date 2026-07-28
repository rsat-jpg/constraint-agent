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

## Why this exists

- Makes plan quality measurable before execution begins
- Provides a clean, open foundation others can extend (LLM planner, PDDL, runtime checks)
- Demonstrates systems thinking and reliability orientation
- Stays small enough to remain inspectable and energy-compatible

## Current status (v0.1)

Structural validators only:

| Check                         | Severity | Description                                                      |
|-------------------------------|----------|------------------------------------------------------------------|
| EMPTY_PLAN                    | error    | No steps present                                                 |
| DUPLICATE_STEP_ID             | error    | Repeated step identifiers                                        |
| UNKNOWN_DEPENDENCY            | error    | depends_on references a non-existent step                        |
| DEPENDENCY_CYCLE              | error    | Cycle in the dependency graph                                    |
| ISOLATED_STEP                 | warning  | Step with no edges in a multi-step plan                          |
| IRREVERSIBLE_NO_OUTCOME       | warning  | Irreversible step lacks expected_outcome                         |
| PRECONDITION_NOT_IN_DEPENDS_ON| warning  | Precondition names a step id omitted from depends_on             |
| MISSING_TERMINAL_OUTCOME      | warning  | No terminal step declares expected_outcome (goal-coverage proxy) |

## Project layout

```
verifiable_planning/
├── KNOWLEDGE_RUBRIC.md   # Governing knowledge contract
├── COMMIT_PROTOCOL.md    # Commit cadence and milestones
├── EXPANSION_GATE.md     # When / when-not to add adapters
├── README.md             # This file
├── pyproject.toml        # Package metadata + dependencies
├── requirements.txt      # Runtime deps (pip -r)
├── requirements-dev.txt  # Runtime + pytest
├── models.py             # Plan, Step, ValidationFinding, ValidationResult
├── validators.py         # Structural validators + graph construction
├── examples.py           # Positive + deliberate failure cases
├── pytest.ini
└── tests/
    └── test_validators.py  # Pos + neg case per structural check
```

## Install

Python 3.10+. From this directory (venv recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# runtime only
pip install -r requirements.txt

# or editable install with test tooling
pip install -e ".[dev]"
```

## Run

```bash
cd verifiable_planning
python3 examples.py
```

## Test

```bash
cd verifiable_planning
python3 -m pytest -q
```

## Knowledge contract

All design decisions are governed by [`KNOWLEDGE_RUBRIC.md`](KNOWLEDGE_RUBRIC.md).  
Read it before expanding the system.

## Commit protocol

When and how to commit is defined in [`COMMIT_PROTOCOL.md`](COMMIT_PROTOCOL.md).  
Commits mark proven increments; run the pre-commit checklist before each one.

## Expansion gate

Criteria for LLM / PDDL / runtime / multi-agent / UI work: [`EXPANSION_GATE.md`](EXPANSION_GATE.md).

## Scope discipline (v0.1)

- Structural validation only
- No LLM planner
- No PDDL / classical planner integration
- No multi-agent orchestration
- No UI

Expansion is governed by [`EXPANSION_GATE.md`](EXPANSION_GATE.md).  
Do not add adapters until that gate’s preconditions and decision record are satisfied.

## Next natural increments

_Only after an approved decision in `EXPANSION_GATE.md`:_

- Thin LLM planner adapter that emits the Plan schema
- Optional PDDL export / import
- Runtime verification hooks

## License / openness

Intended as clean open-source foundation.  
Core contracts are kept stable so adapters can be added without rewriting the foundation.
