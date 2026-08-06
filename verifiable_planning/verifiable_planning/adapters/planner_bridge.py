"""
Thin planner-gated formal adapter (Expansion Gate Decision D4 / Candidate B).

Job: run an injected classical planner over D3-exported PDDL and emit
``PLANNER_*`` findings. Never replaces ``validate_plan``. Never imports a
planner SDK/binary — callers inject ``run_planner(pddl) -> PlannerOutcome``.
Core stays free of this module — callers import it explicitly.

Distinct from convention-``FORMAL_*`` (Decision D3 deepen). Analysis is over
the lossy D3 export — not a claim of sound full PDDL semantics. Import sync
and required planner binaries are out of scope.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from verifiable_planning.adapters.pddl_bridge import plan_to_pddl
from verifiable_planning.models import (
    Plan,
    Severity,
    ValidationFinding,
    ValidationResult,
)

# Planner namespace — not part of the frozen structural set or FORMAL_CODES.
PLANNER_GOAL_UNREACHABLE = "PLANNER_GOAL_UNREACHABLE"
PLANNER_UNAVAILABLE = "PLANNER_UNAVAILABLE"
PLANNER_ERROR = "PLANNER_ERROR"

PLANNER_CODES = frozenset(
    {
        PLANNER_GOAL_UNREACHABLE,
        PLANNER_UNAVAILABLE,
        PLANNER_ERROR,
    }
)


class PlannerStatus(str, Enum):
    """Outcome of an injected planner run over exported PDDL text."""

    SOLVABLE = "solvable"
    UNSAT = "unsat"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


@dataclass(frozen=True)
class PlannerOutcome:
    status: PlannerStatus
    detail: str = ""


RunPlannerFn = Callable[[str], PlannerOutcome]


def check_plan_with_planner(
    plan: Plan,
    run_planner: RunPlannerFn,
) -> ValidationResult:
    """
    Emit ``PLANNER_*`` findings from an injected planner over D3 PDDL export.

    Empty plans yield no planner findings (structural ``EMPTY_PLAN`` owns that
    case). Does not call ``validate_plan``. Never silently succeeds when the
    runner reports unavailable/error or raises.
    """
    if not plan.steps:
        return ValidationResult(plan_id=plan.id, is_valid=True, findings=[])

    try:
        pddl = plan_to_pddl(plan)
    except Exception as exc:  # noqa: BLE001 — surface as planner error finding
        finding = ValidationFinding(
            code=PLANNER_ERROR,
            severity=Severity.ERROR,
            message=f"PDDL export failed before planner run: {exc}",
            step_ids=[],
            suggested_repair=(
                "Fix the plan so plan_to_pddl can export, or inspect LOSSY_EDGES."
            ),
        )
        return ValidationResult(
            plan_id=plan.id, is_valid=False, findings=[finding]
        )

    try:
        outcome = run_planner(pddl)
    except Exception as exc:  # noqa: BLE001 — never silent success
        finding = ValidationFinding(
            code=PLANNER_ERROR,
            severity=Severity.ERROR,
            message=f"Injected planner raised: {exc}",
            step_ids=[],
            suggested_repair=(
                "Fix the planner runner, or pass a runner that returns "
                "PlannerOutcome instead of raising."
            ),
        )
        return ValidationResult(
            plan_id=plan.id, is_valid=False, findings=[finding]
        )

    findings: list[ValidationFinding] = []
    if outcome.status == PlannerStatus.SOLVABLE:
        pass
    elif outcome.status == PlannerStatus.UNSAT:
        detail = outcome.detail.strip()
        suffix = f" ({detail})" if detail else ""
        findings.append(
            ValidationFinding(
                code=PLANNER_GOAL_UNREACHABLE,
                severity=Severity.ERROR,
                message=(
                    "Injected planner reported no plan for the D3-exported "
                    f"PDDL problem{suffix}."
                ),
                step_ids=[s.id for s in plan.steps],
                suggested_repair=(
                    "Remove or adjust free-form preconditions that map to "
                    "unestablished p_* predicates, or change the plan so the "
                    "exported goal is reachable under LOSSY_EDGES."
                ),
            )
        )
    elif outcome.status == PlannerStatus.UNAVAILABLE:
        detail = outcome.detail.strip() or "planner unavailable"
        findings.append(
            ValidationFinding(
                code=PLANNER_UNAVAILABLE,
                severity=Severity.ERROR,
                message=(
                    "Planner check was requested but the injected runner "
                    f"reported unavailable: {detail}"
                ),
                step_ids=[],
                suggested_repair=(
                    "Provide a working run_planner callable, or skip "
                    "check_plan_with_planner when no planner is configured."
                ),
            )
        )
    elif outcome.status == PlannerStatus.ERROR:
        detail = outcome.detail.strip() or "planner error"
        findings.append(
            ValidationFinding(
                code=PLANNER_ERROR,
                severity=Severity.ERROR,
                message=f"Injected planner reported an error: {detail}",
                step_ids=[],
                suggested_repair=(
                    "Inspect planner logs / detail; fix the runner or the "
                    "exported PDDL input."
                ),
            )
        )
    else:  # pragma: no cover — defensive for unexpected enum/extension
        findings.append(
            ValidationFinding(
                code=PLANNER_ERROR,
                severity=Severity.ERROR,
                message=f"Unknown PlannerStatus: {outcome.status!r}",
                step_ids=[],
                suggested_repair="Return a supported PlannerStatus from run_planner.",
            )
        )

    errors = [f for f in findings if f.severity == Severity.ERROR]
    return ValidationResult(
        plan_id=plan.id,
        is_valid=len(errors) == 0,
        findings=findings,
    )
