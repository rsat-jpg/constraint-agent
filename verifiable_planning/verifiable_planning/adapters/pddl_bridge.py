"""
Thin PDDL / convention-formal adapter (Expansion Gate Decision D3 / Candidate B).

Job: (1) map a ``Plan`` to inspectable PDDL domain+problem text; (2) emit
convention-``FORMAL_*`` findings for free-form precondition labels that are
unestablished under documented ``LOSSY_EDGES``. Never replaces
``validate_plan``. Never imports a planner. Core stays free of this module —
callers import it explicitly.

Convention-``FORMAL_*`` checks are static over Plan + mapping conventions —
not classical/PDDL planner reachability and not sound w.r.t. full PDDL
semantics. Import sync and planner-backed checks are out of scope (separate
Decision/deepen).
"""

from __future__ import annotations

import re

from verifiable_planning.models import (
    Plan,
    Severity,
    Step,
    ValidationFinding,
    ValidationResult,
)

# Convention-FORMAL namespace — not part of the frozen structural finding_codes set.
FORMAL_UNESTABLISHED_PRECONDITION = "FORMAL_UNESTABLISHED_PRECONDITION"

FORMAL_CODES = frozenset({FORMAL_UNESTABLISHED_PRECONDITION})

# Documented lossy edges (Decision D3). Keep in sync with README adapter section.
LOSSY_EDGES = """
Mapping conventions (lossy by design):
- Step ids → PDDL action names ``act_<id>`` and completion predicates ``done_<id>``.
- ``depends_on`` → action preconditions ``(done_<dep>)`` (ordering as predicates).
- Free-form (non-step-id) ``preconditions`` entries → predicates ``(p_<sanitized>)``.
- Step-id strings in ``preconditions`` that also appear in ``depends_on`` are
  covered by ``done_*`` only (not duplicated as ``p_*``).
- ``description``, ``goal``, and free-text ``expected_outcome`` are NOT compiled
  into PDDL effects or goals (documented non-effect / non-goal). Use comments.
- ``:init`` is empty — no world facts are inferred from prose.
- Problem ``:goal`` is ``(and (done_<terminal>) ...)`` for sinks, or ``(and)`` if none.
- Sanitization lowercases and replaces non-alphanumeric runs with ``_``; leading
  digits get an ``n`` prefix. Distinct strings may collide after sanitize.
"""


def pddl_atom(raw: str, *, kind: str) -> str:
    """
    Sanitize a plan string into a PDDL name fragment.

    ``kind`` is a short prefix tag used only when the sanitized body would be
    empty (``pred``, ``act``, ``done``).
    """
    body = re.sub(r"[^a-zA-Z0-9]+", "_", raw.strip().lower()).strip("_")
    if not body:
        body = kind
    if body[0].isdigit():
        body = f"n{body}"
    return body


def _done_pred(step_id: str) -> str:
    return f"done_{pddl_atom(step_id, kind='step')}"


def _act_name(step_id: str) -> str:
    return f"act_{pddl_atom(step_id, kind='step')}"


def _label_pred(label: str) -> str:
    return f"p_{pddl_atom(label, kind='pred')}"


def free_form_precondition_labels(plan: Plan) -> list[str]:
    """Non-step-id precondition strings in plan order (may repeat)."""
    known = plan.step_ids()
    labels: list[str] = []
    for step in plan.steps:
        for p in step.preconditions:
            if p not in known:
                labels.append(p)
    return labels


def check_unestablished_preconditions(plan: Plan) -> ValidationResult:
    """
    Emit convention-``FORMAL_*`` findings for free-form precondition labels.

    Under current D3 ``LOSSY_EDGES``, free-form labels map to ``p_*`` predicates
    that no action establishes (effects are ``done_*`` only; ``:init`` empty;
    ``expected_outcome`` is not an effect). v1 therefore has no "established
    free-form" green path — only plans with no free-form precondition labels
    are formal-clean.

    This is not planner reachability. Empty plans yield no formal findings
    (structural ``EMPTY_PLAN`` owns that case). Does not call ``validate_plan``.
    """
    findings: list[ValidationFinding] = []
    if not plan.steps:
        return ValidationResult(plan_id=plan.id, is_valid=True, findings=[])

    known = plan.step_ids()
    for step in plan.steps:
        for label in step.preconditions:
            if label in known:
                continue
            pred = _label_pred(label)
            findings.append(
                ValidationFinding(
                    code=FORMAL_UNESTABLISHED_PRECONDITION,
                    severity=Severity.ERROR,
                    message=(
                        f"Step '{step.id}' requires free-form precondition "
                        f"{label!r} (mapped as ({pred})), which no step "
                        f"establishes under current D3 mapping conventions."
                    ),
                    step_ids=[step.id],
                    suggested_repair=(
                        "Remove or adjust the free-form precondition, or add "
                        "prior work that would establish the condition under a "
                        "future establishment convention (v1 has none)."
                    ),
                )
            )

    errors = [f for f in findings if f.severity == Severity.ERROR]
    return ValidationResult(
        plan_id=plan.id,
        is_valid=len(errors) == 0,
        findings=findings,
    )


def _action_preconditions(step: Step, known: set[str]) -> list[str]:
    preds: list[str] = []
    for dep in step.depends_on:
        if dep in known:
            preds.append(_done_pred(dep))
    for p in step.preconditions:
        if p in known:
            # Step-id preconditions: only via depends_on → done_*; structural
            # Validate owns missing-edge cases. Do not emit p_* for step ids.
            continue
        preds.append(_label_pred(p))
    # Stable unique while preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for pred in preds:
        if pred not in seen:
            seen.add(pred)
            ordered.append(pred)
    return ordered


def _terminal_ids(plan: Plan) -> list[str]:
    """Steps nothing else lists in depends_on (order = plan.steps order)."""
    known = plan.step_ids()
    depended_on: set[str] = set()
    for step in plan.steps:
        for dep in step.depends_on:
            if dep in known:
                depended_on.add(dep)
    return [s.id for s in plan.steps if s.id not in depended_on]


def plan_to_pddl(plan: Plan) -> str:
    """
    Export ``plan`` to a single PDDL string (domain then problem).

    Does not call ``validate_plan``. Raises ``ValueError`` if the plan has no
    steps (nothing useful to export).
    """
    if not plan.steps:
        raise ValueError(
            "plan_to_pddl requires at least one step; "
            "empty plans are owned by structural EMPTY_PLAN."
        )

    known = plan.step_ids()
    domain_name = f"domain_{pddl_atom(plan.id, kind='plan')}"
    problem_name = f"problem_{pddl_atom(plan.id, kind='plan')}"

    predicates: list[str] = []
    pred_seen: set[str] = set()

    def add_pred(name: str) -> None:
        if name not in pred_seen:
            pred_seen.add(name)
            predicates.append(name)

    for step in plan.steps:
        add_pred(_done_pred(step.id))
    for label in free_form_precondition_labels(plan):
        add_pred(_label_pred(label))

    lines: list[str] = []
    lines.append(f";; PDDL export of plan id={plan.id!r} (Decision D3)")
    lines.append(";; Lossy edges: see LOSSY_EDGES in verifiable_planning.adapters.pddl_bridge")
    lines.append(f";; goal (prose, not compiled): {plan.goal}")
    lines.append("")
    lines.append(f"(define (domain {domain_name})")
    lines.append("  (:requirements :strips)")
    lines.append("  (:predicates")
    for pred in predicates:
        lines.append(f"    ({pred})")
    lines.append("  )")

    for step in plan.steps:
        pre = _action_preconditions(step, known)
        act = _act_name(step.id)
        lines.append(f"  ;; step {step.id!r}: {step.description}")
        if step.expected_outcome:
            lines.append(
                f"  ;; expected_outcome (not an effect): {step.expected_outcome}"
            )
        lines.append(f"  (:action {act}")
        if pre:
            lines.append("    :precondition (and")
            for p in pre:
                lines.append(f"      ({p})")
            lines.append("    )")
        else:
            lines.append("    :precondition (and)")
        lines.append(f"    :effect (and ({_done_pred(step.id)}))")
        lines.append("  )")

    lines.append(")")
    lines.append("")
    lines.append(f"(define (problem {problem_name})")
    lines.append(f"  (:domain {domain_name})")
    lines.append("  (:init)")
    terminals = _terminal_ids(plan)
    if terminals:
        lines.append("  (:goal (and")
        for tid in terminals:
            lines.append(f"    ({_done_pred(tid)})")
        lines.append("  ))")
    else:
        lines.append("  (:goal (and))")
    lines.append(")")
    lines.append("")
    return "\n".join(lines)
