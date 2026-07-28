# Expansion Gate — When (and When Not) to Grow Beyond Structural Validation

Written criteria for adding capabilities after the v0.1 Validate core.  
Companion to [`KNOWLEDGE_RUBRIC.md`](KNOWLEDGE_RUBRIC.md) and [`COMMIT_PROTOCOL.md`](COMMIT_PROTOCOL.md).

Last updated: 2026-07-28

---

## Purpose

Prevent scope leak into another generic agent stack.  
Expansion is allowed only when it **preserves core contracts**, **raises measurable plan quality**, and **stays energy-compatible**.

The core stays: typed `Plan` → deterministic structural `validate_plan` → structured `ValidationResult`.

---

## Preconditions to open the gate

All of the following must be true before any non-structural capability:

| # | Gate check | Evidence |
|---|------------|----------|
| G1 | Milestones 0–3 complete | Commit protocol schedule |
| G2 | Core remains high-signal | `examples.py` + tests still demonstrate real catches; no flaky or opaque checks |
| G3 | Contracts stable | `Plan`, `ValidationFinding`, `ValidationResult` change only with explicit version note |
| G4 | One purpose, one adapter | Proposed work has a single job and a thin boundary (no framework rewrite) |
| G5 | Rubric Strong still holds | Architecture + Implementation rows scored Strong; Purpose Alignment still clear |

If any check fails → **do not expand**; fix the core or write a decision note explaining the exception.

---

## Candidate expansions

### A. Thin LLM planner adapter

**Job:** Emit a `Plan` (schema-valid) from a goal/prompt. Never replace Validate.

| Add when | Do not add when |
|----------|-----------------|
| You need plans to test Validate against without hand-authoring every fixture | The goal is “build an agent” rather than improve plan measurability |
| Adapter is optional (`extras` / separate module); core imports stay LLM-free | Core would import an SDK, require API keys, or call models inside `validate_plan` |
| Failures of the planner are visible as bad `Plan`s that Validate can catch | Planner silently “fixes” or bypasses validation findings |
| Cost/latency are acceptable for experimentation only | Energy budget can’t afford nondeterministic dependency churn |

**Acceptance:** Adapter returns `Plan`; Validate remains the gate; no LLM inside validators.

---

### B. PDDL / classical planner bridge

**Job:** Export/import or map between `Plan` and a formal planning representation for semantic/formal checks.

| Add when | Do not add when |
|----------|-----------------|
| A concrete semantic property can’t be expressed structurally (e.g. resource axioms, true reachability) | Structural checks still cover the failure mode cheaply |
| Mapping is explicit and lossy edges are documented | Bidirectional “magic” sync that obscures the source of truth |
| Formal tools stay behind an adapter; core stays runnable without them | PDDL toolchain becomes required to run examples/tests |
| You can show one finding type that structural validation cannot catch | Expansion is motivated only by résumé keywords |

**Acceptance:** Structural Validate still runs with zero PDDL deps; formal checks are additive findings with distinct codes/namespace.

---

### C. Runtime verification hooks

**Job:** Compare execution traces to plan structure (step order, declared deps, irreversible checkpoints).

| Add when | Do not add when |
|----------|-----------------|
| You have a real executor producing inspectable step events | There is no executor — designing hooks in the abstract |
| Hooks consume `Plan` + event stream; they don’t reimplement planning | Runtime layer starts owning plan mutation or “auto-repair” without review |
| Findings reuse `ValidationFinding`-shaped records (or a thin sibling schema) | A second incompatible result model appears without migration path |

**Acceptance:** Offline structural Validate remains usable alone; runtime is an optional stage after Validate passes (or with explicit override).

---

### D. Multi-agent orchestration / UI

**Default: closed.**

| Add when | Do not add when |
|----------|-----------------|
| A specific multi-agent failure mode needs shared plan validation (documented) | “Agents collaborating” is the product idea, not a Validate need |
| UI is a thin viewer over `ValidationResult` for demos | UI drives architecture or becomes the primary interface to the core |
| Core package stays headless and framework-agnostic | LangGraph/Crew/etc. types leak into `models.py` / `validators.py` |

---

## Hard non-negotiables (never open for these)

1. **No LLM inside structural validators** — Validate stays deterministic and inspectable.
2. **No binary-only gates** — findings must remain structured with suggested repairs.
3. **No framework lock-in** — adapters depend inward on core contracts, not the reverse.
4. **No silent success** — if an adapter can’t map cleanly, it must fail visibly or emit findings.
5. **Core working-memory size** — if the default path can’t be held in one short reading session, split or refuse.

---

## Decision record (required per expansion)

Before implementing an expansion, add a short note (in this file under **Decisions**, or a one-file entry in commit message + README link) answering:

1. **Which candidate** (A–D) and **which failure mode** it attacks  
2. **Why structural validation is insufficient**  
3. **Adapter boundary** (what core will never import)  
4. **Success signal** (demo or test that proves value)  
5. **Rollback** (how to remove the adapter without rewriting core)

### Decisions

_None yet. Gate is open for proposals; no adapter approved._

---

## How to use

1. Propose an expansion → check **Preconditions** (G1–G5).  
2. Match a **Candidate** table → confirm “Add when” and none of “Do not add when.”  
3. Write a **Decision** entry.  
4. Add a commit-protocol milestone row for that adapter.  
5. Implement as a thin module; keep `python3 examples.py` and structural tests green with adapters uninstalled.

This gate is the Advanced Scope Discipline artifact. Expanding without it is out of contract.
