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

| Check                    | Severity | Description                                      |
|--------------------------|----------|--------------------------------------------------|
| EMPTY_PLAN               | error    | No steps present                                 |
| DUPLICATE_STEP_ID        | error    | Repeated step identifiers                        |
| UNKNOWN_DEPENDENCY       | error    | depends_on references a non-existent step        |
| DEPENDENCY_CYCLE         | error    | Cycle in the dependency graph                    |
| ISOLATED_STEP            | warning  | Step with no edges in a multi-step plan          |
| IRREVERSIBLE_NO_OUTCOME  | warning  | Irreversible step lacks expected_outcome         |

## Project layout

```
verifiable_planning/
├── KNOWLEDGE_RUBRIC.md   # Governing knowledge contract
├── COMMIT_PROTOCOL.md    # Commit cadence and milestones
├── README.md             # This file
├── models.py             # Plan, Step, ValidationFinding, ValidationResult
├── validators.py         # Structural validators + graph construction
├── examples.py           # Positive + deliberate failure cases
├── pytest.ini
└── tests/
    └── test_validators.py  # Pos + neg case per structural check
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

Requires: Python 3.10+, pydantic, networkx, pytest.

## Knowledge contract

All design decisions are governed by [`KNOWLEDGE_RUBRIC.md`](KNOWLEDGE_RUBRIC.md).  
Read it before expanding the system.

## Commit protocol

When and how to commit is defined in [`COMMIT_PROTOCOL.md`](COMMIT_PROTOCOL.md).  
Commits mark proven increments; run the pre-commit checklist before each one.

## Scope discipline (v0.1)

- Structural validation only
- No LLM planner
- No PDDL / classical planner integration
- No multi-agent orchestration
- No UI

Expansion only after the core is proven useful and remains high-signal.

## Next natural increments

- Richer structural rules (missing goal coverage, precondition consistency)
- Thin LLM planner adapter that emits the Plan schema
- Optional PDDL export / import
- Runtime verification hooks

## License / openness

Intended as clean open-source foundation.  
Core contracts are kept stable so adapters can be added without rewriting the foundation.
