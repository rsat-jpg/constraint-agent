# Commit Protocol — Verifiable Planning

Cadence and rules for when (and when not) to commit.  
Companion to [`KNOWLEDGE_RUBRIC.md`](KNOWLEDGE_RUBRIC.md).

Last updated: 2026-07-28

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
| **Docs contract change** | Rubric, scope, or protocol updates that bind the build | `docs: update knowledge contract / commit protocol` |
| **Packaging** | `requirements.txt`, `pyproject.toml`, license | `chore: add install/packaging surface` |
| **Bugfix** | Validator false positive/negative with repro | `fix: <what was wrong and why>` |

---

## Do not commit

- Half-finished validators with no pos+neg evidence
- Experiments that break `python3 examples.py`
- Scope leaks (LLM, PDDL, multi-agent, UI) without an explicit expansion decision recorded in the rubric or a short decision note
- Secrets, credentials, local env files
- Generated noise (`__pycache__/`, `.venv/`, `.pytest_cache/`)

---

## Pre-commit checklist

Before every commit:

1. **Essential rubric rows** still hold for the touched area.
2. `python3 examples.py` runs from `verifiable_planning/` (good plan VALID; deliberate failures still produce expected findings).
3. If a validator changed: at least one positive and one negative case exist (examples and/or tests).
4. Diff is one logical increment — split unrelated changes.
5. Message explains **why**, not a file list.

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
