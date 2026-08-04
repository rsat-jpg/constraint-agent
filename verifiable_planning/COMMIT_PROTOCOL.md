# Commit Protocol — Verifiable Planning

Cadence and rules for when (and when not) to commit.  
Companion to [`KNOWLEDGE_RUBRIC.md`](KNOWLEDGE_RUBRIC.md).

Last updated: 2026-08-03

---

## Purpose

Commits should mark **proven increments**, not WIP noise.  
Each commit should be justifiable against the knowledge rubric and leave the tree runnable.

---

## Commit triggers (do commit)

| Trigger | Example | Suggested message focus |
|---------|---------|-------------------------|
| **Baseline** | First snapshot of a working v0.1 core | `chore: baseline v0.1 structural validate core` |
| **Validator added/changed** | New structural check + failure case | `feat: add <CODE> structural validator` |
| **Schema change** | Plan/Finding/Result fields that affect contracts | `feat:` / `fix:` — note schema version impact |
| **Evidence locked** | Tests that cover pos+neg for a validator | `test: cover <CODE> positive and negative cases` |
| **Docs contract change** | Rubric, scope, freeze policy, or protocol updates that bind the build | `docs: update knowledge contract / commit protocol` |
| **Packaging** | `requirements.txt`, `pyproject.toml`, license | `chore: add install/packaging surface` |
| **Bugfix** | Validator false positive/negative with repro | `fix: <what was wrong and why>` |

---

## Do not commit

- Half-finished validators with no pos+neg evidence
- Experiments that break `python3 examples.py`, `python3 examples_runtime.py`, or `python3 examples_llm.py`
- Scope leaks (LLM, PDDL, multi-agent, UI) without an explicit expansion decision recorded in the rubric or a short decision note
- Secrets, credentials, local env files
- Generated noise (`__pycache__/`, `.venv/`, `.pytest_cache/`)

---

## Pre-commit checklist

Before every commit:

1. **Essential rubric rows** still hold for the touched area.
2. `python3 examples.py` runs from `verifiable_planning/` (good plan VALID; deliberate failures still produce expected findings).
3. `python3 examples_runtime.py` runs from `verifiable_planning/` (structural VALID → happy runtime VALID; deliberate runtime failure shows `RUNTIME_DEPENDENCY_ORDER`).
4. `python3 examples_llm.py` runs from `verifiable_planning/` (happy path VALID; deliberate failure shows `UNKNOWN_DEPENDENCY`).
5. If a validator changed: at least one positive and one negative case exist (examples and/or tests).
6. Diff is one logical increment — split unrelated changes.
7. Message explains **why**, not a file list.

---

## Message format

```
<type>: <short why>

Optional body: what changed for the Validate stage / contracts, and any deliberate non-goals.
```

**Types:** `feat` · `fix` · `test` · `docs` · `chore` · `refactor`

Keep subject ≤ ~72 chars. No trailing period on the subject line.

---

## Schedule (v0.1 → next)

| # | Milestone | Commit when | Status |
|---|-----------|-------------|--------|
| 0 | Baseline core | models + validators + examples + rubric + README runnable | done 2026-07-28 |
| 1 | Evidence layer | formal tests (pos+neg per validator) | done 2026-07-28 |
| 2 | Install surface | `requirements.txt` or minimal `pyproject.toml` | done 2026-07-28 |
| 3 | Richer structural rules | only after 1–2; one rule (or tight set) per commit | done 2026-07-28 |
| 4 | Expansion gate | written criteria for LLM/PDDL/runtime adapters | done 2026-07-28 |
| 5 | Open-source readiness | MIT LICENSE, stranger quickstart, public package exports, schema stability note | done 2026-07-28 |
| 6 | LLM→Plan adapter (D1) | Thin optional adapter: goal + injected completer → `Plan`; core stays LLM-free | done 2026-07-28 |
| 7 | DUPLICATE_DEPENDENCY | Warn when a step repeats an id in depends_on | done 2026-07-28 |
| 8 | DISCONNECTED_GRAPH | Warn when depends_on graph has multiple weakly connected components | done 2026-07-28 |
| 9 | Finding noise / evidence | Clarify ISOLATED_STEP vs DISCONNECTED_GRAPH ownership; centralize finding codes | done 2026-07-28 |
| 10 | REDUNDANT_DEPENDENCY | Warn when depends_on lists an ancestor already implied by another dep | done 2026-07-28 |
| 11 | MULTIPLE_TERMINALS | Warn when a multi-step DAG has more than one sink (fork without join) | done 2026-07-28 |
| 12 | Evidence corpus | LLM-shaped fixtures + expected codes / overlaps matrix (no new rules) | done 2026-07-31 |
| 13 | v0.1 Validate surface freeze | Freeze 13 finding codes for 0.1.x; policy docs + lock test; no new rules | done 2026-08-01 |
| 14 | Runtime verify adapter (D2) | Thin `verify_trace` + `linear_trace`; `RUNTIME_*` codes; structural freeze intact | done 2026-08-02 |
| 15 | Runtime e2e demo | `examples_runtime.py` + docs: Plan → Validate → Runtime happy path + deliberate failure; no new Decision/codes | done 2026-08-02 |
| 16 | LLM e2e demo | `examples_llm.py` + docs: goal → plan_from_goal → validate happy path + deliberate UNKNOWN_DEPENDENCY; no new Decision/codes | done 2026-08-03 |

Update the **Status** column when a milestone lands (`done` + date).

Later milestones (LLM adapter, PDDL, runtime hooks) each get their own row only after an approved decision in [`EXPANSION_GATE.md`](EXPANSION_GATE.md).

---

## Cadence rules

- **Prefer small, vertical commits** over end-of-day dumps.
- **One validator family per commit** when adding checks.
- **Docs-only commits are fine** when the knowledge contract changes.
- **No commit required** for pure exploration that you discard.
- **Ask before committing** unless the user explicitly requested a commit in the current turn.

---

## Agent / collaborator duty

When work finishes an open milestone row:

1. Run the pre-commit checklist.
2. Propose a commit (status + message + file list).
3. Commit only after explicit user approval (or an explicit “commit this” request).

---

## How to use

- Before an increment: peek at the next pending milestone.
- After a working change: check triggers + checklist.
- Before open-source push: milestones 0–2 done; Architecture/Implementation at Strong+.
