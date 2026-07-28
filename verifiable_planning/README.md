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
| DEPENDENCY_CYCLE              | error    | Cycle in the dependency graph                                    |
| ISOLATED_STEP                 | warning  | Step with no edges in a multi-step plan                          |
| IRREVERSIBLE_NO_OUTCOME       | warning  | Irreversible step lacks expected_outcome                         |
| PRECONDITION_NOT_IN_DEPENDS_ON| warning  | Precondition names a step id omitted from depends_on             |
| MISSING_TERMINAL_OUTCOME      | warning  | No terminal step declares expected_outcome (goal-coverage proxy) |

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
│   ├── __init__.py                  # Public exports
│   ├── models.py                    # Plan, Step, findings, result
│   └── validators.py                # Structural validators + graph
└── tests/
    └── test_validators.py
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

Still inside Validate (no gate decision required): one tighter structural rule family at a time.

## License

MIT — see [`LICENSE`](LICENSE).
