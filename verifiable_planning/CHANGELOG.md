# Changelog

## 0.1.0 — 2026-08-02

- Structural Validate core: typed `Plan` / findings, deterministic `validate_plan`
- Thin optional LLM→Plan adapter (Expansion Gate Decision D1)
- Thin optional runtime trace verification (Expansion Gate Decision D2): `verify_trace` / `linear_trace`, `RUNTIME_*` codes
- D2 deepen (2026-08-04): `StepEventType.CHECKPOINT` + `RUNTIME_MISSING_CHECKPOINT` for irreversible steps; `linear_trace` emits checkpoints before irreversible `STARTED`
- Runnable Plan → Validate → Runtime demo: `examples_runtime.py` (happy path + deliberate `RUNTIME_DEPENDENCY_ORDER` + missing-checkpoint failure)
- Runnable LLM Plan → Validate demo: `examples_llm.py` (injected fake completer; no API keys; deliberate `UNKNOWN_DEPENDENCY` failure)
- Thin optional PDDL export (Expansion Gate Decision D3, 2026-08-04): `plan_to_pddl`; lossy edges documented; no planner; structural freeze intact
- D3 deepen (2026-08-05): convention-`FORMAL_*` via `check_unestablished_preconditions` (`FORMAL_UNESTABLISHED_PRECONDITION`); not planner reachability; no planner required
- Runnable Plan → Validate → formal → PDDL demo: `examples_pddl.py` (clean path + deliberate free-form `data_licensed` label gap)
- Thin optional planner-gated checks (Expansion Gate Decision D4, 2026-08-06): `check_plan_with_planner` + `PLANNER_*`; injected runner; distinct from convention-`FORMAL_*`; no required binary
- Runnable Plan → Validate → planner demo: `examples_planner.py` (injected fake planner; clean solvable + label-gap `PLANNER_GOAL_UNREACHABLE` + unavailable path)
- Evidence corpus of LLM-shaped fixtures with expected codes and overlaps
- **Structural Validate surface freeze:** 13 finding codes locked for package `0.1.x` (see README); runtime / formal / planner codes are separate namespaces
