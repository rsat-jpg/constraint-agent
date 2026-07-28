# Knowledge Rubric — Verifiable Planning Build

Governing knowledge contract for the Plan-Validate-Execute core and its purposes.
Last updated: 2026-07-28

## 1. Domain Understanding

| Level | Criteria |
|-------|----------|
| Essential | Clearly distinguishes ReAct, Plan-then-Execute, Plan-Validate-Execute, and neuro-symbolic hybrids. Knows that early planning errors are a dominant cause of long-horizon failure. |
| Strong | Articulates the difference between structural verification (graph consistency, completeness, cycles, declared preconditions) and semantic/formal verification (PDDL + classical planners, policy engines, cryptographic checks). Knows the practical limits of each. |
| Advanced | Can map current research gaps (silent failures, root-cause attribution across trajectories, temporal consistency) directly onto design decisions in the core. |

## 2. Architectural Judgment

| Level | Criteria |
|-------|----------|
| Essential | Separates Plan → Validate → Execute into distinct stages with explicit interfaces. Core remains framework-agnostic. |
| Strong | Plan model and validators deliver value with zero LLM dependency. Validation returns structured findings + actionable repair signals, not binary pass/fail. |
| Advanced | Later backends (LLM planner, PDDL, runtime checks, multi-agent) require only thin adapters. Core contracts stay stable. |

## 3. Implementation Quality

| Level | Criteria |
|-------|----------|
| Essential | Typed models (pydantic), explicit graph representation, deterministic structural validators, fully inspectable state. |
| Strong | Includes deliberate failure cases that prove validators catch real problems. Code + examples are understandable by a competent stranger without oral explanation. |
| Advanced | Extensible validator registry, versioned plan schema, clear separation of structural vs semantic checks, ready for clean open-source packaging. |

## 4. Evidence & Testability

| Level | Criteria |
|-------|----------|
| Essential | Every validator has at least one positive and one negative test case. |
| Strong | Failure injection is first-class; the system can demonstrate what it catches and what it currently cannot. |
| Advanced | Validation results themselves are structured and queryable, supporting later evaluation harnesses or learning loops. |

## 5. Scope Discipline

| Level | Criteria |
|-------|----------|
| Essential | v0.1 stays strictly within structural validation. No LLM, no PDDL, no multi-agent, no UI. |
| Strong | Expansion only occurs after the core is proven useful and remains high-signal. |
| Advanced | Clear written criteria exist for when (and when not) to add the next capability. |

## 6. Purpose Alignment

| Purpose | Success Signal |
|---------|----------------|
| Important / high-leverage | Directly attacks a real reliability bottleneck (cascading planning errors) rather than building another generic agent loop. |
| Discovery & innovation | Makes plan quality measurable and improvable, lowering the cost of experimenting with better planners or verification methods. |
| Open-source usefulness | A competent developer can adopt the core, plug in their own planner or rules, and receive immediate value without rewriting foundations. |
| Job / openness signal | Demonstrates flexible systems thinking, reliability orientation, and clean extensibility — not rigid personal constraints or opaque frameworks. |
| Energy & durability | Remains mid-complexity, pauseable, and inspectable. Core stays small enough to hold in working memory. |

## 7. Living Knowledge Gaps

- Exact boundary of what pure structural validation can reliably catch
- Minimal powerful set of validation rules
- Clean schema for "finding + suggested repair" (v0.1 shape exists; may refine with use)
- Packaging and documentation practices that make an open-source release actually usable
- ~~When structural verification should hand off to semantic or formal methods~~ → see [`EXPANSION_GATE.md`](EXPANSION_GATE.md)

---

## How to use

- Before each increment: check the Essential rows.
- After each working version: score against Strong.
- Before considering open-source or outreach: require Advanced on Architecture and Implementation, plus clear Purpose Alignment.

This rubric is the knowledge contract for the build. Everything implemented should be justifiable against it.
