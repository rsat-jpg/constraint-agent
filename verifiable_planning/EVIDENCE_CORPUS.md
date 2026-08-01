# Evidence Corpus — LLM-shaped Validate fixtures

Deterministic proof that the v0.1 structural Validate surface stays **high-signal** against plans shaped like common LLM planner defects.

Companion to Expansion Gate G2 and Decision D1. No live model, no network.

Last updated: 2026-07-31

---

## Purpose

- Exercise every current finding code with inspectable fixtures
- Record **expected** fires and **known overlaps** (optional codes)
- Keep Plan→Validate separable: fixtures are static JSON; two also round-trip through `plan_from_llm_text`

## How to run

From `verifiable_planning/`:

```bash
python3 -m pytest -q tests/test_evidence_corpus.py
python3 -m pytest -q
```

Fixtures live in [`tests/fixtures/llm_shaped/`](tests/fixtures/llm_shaped/).  
Loader: [`tests/corpus_loader.py`](tests/corpus_loader.py).  
Tests: [`tests/test_evidence_corpus.py`](tests/test_evidence_corpus.py).

Each fixture JSON has `meta` + `plan`. Tests assert:

- `expected_codes ⊆ observed`
- clean fixture (`clean_chain`) has **zero** findings
- no codes outside `expected_codes ∪ optional_codes`
- ERROR codes only from `expected_codes`

## Coverage matrix

| Fixture | Expected codes | Optional (overlaps) | Notes |
|---------|----------------|---------------------|-------|
| `clean_chain` | _(none)_ | — | Linear gather→extract→write |
| `empty_plan` | `EMPTY_PLAN` | — | Empty `steps` |
| `duplicate_step_id` | `DUPLICATE_STEP_ID` | `ISOLATED_STEP`, `MISSING_TERMINAL_OUTCOME` | Graph collapses duplicate ids |
| `unknown_dep` | `UNKNOWN_DEPENDENCY` | `ISOLATED_STEP`, `MULTIPLE_TERMINALS` | Hallucinated depends_on target |
| `self_dep` | `SELF_DEPENDENCY` | — | No `DEPENDENCY_CYCLE` (length-1 owned here) |
| `cycle` | `DEPENDENCY_CYCLE` | — | Terminal checks skipped on cycles |
| `duplicate_dep` | `DUPLICATE_DEPENDENCY` | — | Repeated id in depends_on |
| `redundant_dep` | `REDUNDANT_DEPENDENCY` | — | Ancestor + parent both listed |
| `isolate_bag` | `ISOLATED_STEP`, `MULTIPLE_TERMINALS` | — | Pure isolate bag; not `DISCONNECTED_GRAPH` |
| `two_chains` | `DISCONNECTED_GRAPH`, `MULTIPLE_TERMINALS` | — | Separate chains; not `ISOLATED_STEP` |
| `fork_without_join` | `MULTIPLE_TERMINALS` | — | One component, two sinks; not `DISCONNECTED_GRAPH` |
| `precond_mismatch` | `PRECONDITION_NOT_IN_DEPENDS_ON` | `ISOLATED_STEP`, `MULTIPLE_TERMINALS` | Precondition without edge |
| `no_terminal_outcome` | `MISSING_TERMINAL_OUTCOME` | — | Chain with no sink outcome |
| `irreversible_no_outcome` | `IRREVERSIBLE_NO_OUTCOME` | — | Destructive step; terminal still has outcome |

**All 13 finding codes** appear in at least one fixture’s `expected_codes`.

## D1 path

Fixtures `clean_chain` and `unknown_dep` also serialize `plan` → `plan_from_llm_text` → `validate_plan` and assert the same expected/optional sets. Still no LLM SDK.

## What this does not prove

- Semantic correctness of step text vs goal
- Behavior of a live model or any cloud API
- Runtime / execution-trace verification
- That the rule set is minimal — only that it is measurable and currently covers these shapes

## Maintenance

When adding a finding code: add or extend a fixture, update this table, keep `test_corpus_covers_all_finding_codes` green.  
When ownership/overlap rules change: update `optional_codes` / notes — prefer a dedicated commit over silent corpus edits mixed with validator changes.
