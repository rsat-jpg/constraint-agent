"""
Plan → Validate → planner-gated check demo (Expansion Gate D4).

Injected fake planner only — no planner binary, no network.
Structural Validate stays the offline gate. PLANNER_* is distinct from
convention-FORMAL_*.
"""

from __future__ import annotations

from verifiable_planning import Plan, Step, ValidationResult, validate_plan
from verifiable_planning.adapters.pddl_bridge import (
    FORMAL_UNESTABLISHED_PRECONDITION,
    check_unestablished_preconditions,
    plan_to_pddl,
)
from verifiable_planning.adapters.planner_bridge import (
    PLANNER_GOAL_UNREACHABLE,
    PLANNER_UNAVAILABLE,
    PlannerOutcome,
    PlannerStatus,
    check_plan_with_planner,
)


def print_result(result: ValidationResult, *, title: str | None = None) -> None:
    status = "VALID" if result.is_valid else "INVALID"
    label = title or f"Plan: {result.plan_id}"
    print(f"\n{'='*60}")
    print(f"{label}  →  {status}")
    print(f"{'='*60}")
    if not result.findings:
        print("No findings.")
        return
    for f in result.findings:
        print(f"[{f.severity.value.upper():7}] {f.code}")
        print(f"         {f.message}")
        if f.suggested_repair:
            print(f"         Repair: {f.suggested_repair}")
        if f.step_ids:
            print(f"         Steps:  {f.step_ids}")
        print()


def _fake_planner_for_demo(pddl: str) -> PlannerOutcome:
    """
    Deterministic stand-in: unsat iff exported PDDL mentions a free-form p_*
    predicate (matches D3 v1 mapping where p_* is never established).
    """
    if "(p_" in pddl:
        return PlannerOutcome(
            status=PlannerStatus.UNSAT,
            detail="demo fake planner: free-form p_* present",
        )
    return PlannerOutcome(status=PlannerStatus.SOLVABLE)


def main() -> None:
    print("\n" + "#" * 60)
    print("# D4 planner-gated checks — injected runner (no binary)")
    print("#" * 60)

    # ------------------------------------------------------------------
    # A. Happy path: clean chain → structural VALID + planner solvable
    # ------------------------------------------------------------------
    print("\n" + "#" * 60)
    print("# Plan → Validate → planner — happy path (clean chain)")
    print("#" * 60)

    clean = Plan(
        id="planner-clean",
        goal="Ship a summary",
        steps=[
            Step(id="gather", description="Collect sources"),
            Step(
                id="write",
                description="Draft summary",
                depends_on=["gather"],
                expected_outcome="Markdown summary ready",
            ),
        ],
    )
    structural = validate_plan(clean)
    print_result(structural, title="Structural validate (clean)")
    if not structural.is_valid:
        raise SystemExit("Expected clean plan to be structurally VALID.")

    planner = check_plan_with_planner(clean, _fake_planner_for_demo)
    print_result(planner, title="Planner-gated check (clean)")
    if not planner.is_valid:
        raise SystemExit("Expected clean plan to pass injected planner check.")
    if PLANNER_GOAL_UNREACHABLE in {f.code for f in planner.findings}:
        raise SystemExit("Unexpected PLANNER_GOAL_UNREACHABLE on clean chain.")

    # ------------------------------------------------------------------
    # B. Label-gap: structural VALID; convention FORMAL_*; planner UNSAT
    # ------------------------------------------------------------------
    print("\n" + "#" * 60)
    print("# Label-gap: structural VALID; FORMAL_*; PLANNER_GOAL_UNREACHABLE")
    print("#" * 60)

    gap = Plan(
        id="planner-label-gap",
        goal="Publish licensed data summary",
        steps=[
            Step(
                id="a",
                description="Gather raw notes",
                expected_outcome="Notes collected",
            ),
            Step(
                id="b",
                description="Publish summary",
                depends_on=["a"],
                preconditions=["data_licensed"],
                expected_outcome="Summary published",
            ),
        ],
    )
    structural_gap = validate_plan(gap)
    print_result(structural_gap, title="Structural validate (label-gap)")
    if not structural_gap.is_valid:
        raise SystemExit("Expected label-gap plan to be structurally VALID.")

    formal = check_unestablished_preconditions(gap)
    print_result(formal, title="Convention-FORMAL_* (label-gap)")
    if FORMAL_UNESTABLISHED_PRECONDITION not in {f.code for f in formal.findings}:
        raise SystemExit(
            f"Expected {FORMAL_UNESTABLISHED_PRECONDITION}; "
            f"got {[f.code for f in formal.findings]}."
        )

    pddl = plan_to_pddl(gap)
    if "p_data_licensed" not in pddl:
        raise SystemExit("Expected p_data_licensed in export for demo fake planner.")

    planner_gap = check_plan_with_planner(gap, _fake_planner_for_demo)
    print_result(planner_gap, title="Planner-gated check (label-gap)")
    planner_codes = [f.code for f in planner_gap.findings]
    if PLANNER_GOAL_UNREACHABLE not in planner_codes:
        raise SystemExit(
            f"Expected {PLANNER_GOAL_UNREACHABLE}; got {planner_codes}."
        )
    if FORMAL_UNESTABLISHED_PRECONDITION in planner_codes:
        raise SystemExit("Planner path must not emit convention-FORMAL_* codes.")

    # ------------------------------------------------------------------
    # C. Unavailable runner — never silent success
    # ------------------------------------------------------------------
    print("\n" + "#" * 60)
    print("# Unavailable injected runner → PLANNER_UNAVAILABLE")
    print("#" * 60)

    def unavailable(_pddl: str) -> PlannerOutcome:
        return PlannerOutcome(
            status=PlannerStatus.UNAVAILABLE,
            detail="no planner binary configured (demo)",
        )

    unavailable_result = check_plan_with_planner(clean, unavailable)
    print_result(unavailable_result, title="Planner-gated check (unavailable)")
    if PLANNER_UNAVAILABLE not in {f.code for f in unavailable_result.findings}:
        raise SystemExit(
            f"Expected {PLANNER_UNAVAILABLE}; "
            f"got {[f.code for f in unavailable_result.findings]}."
        )
    if unavailable_result.is_valid:
        raise SystemExit("Unavailable planner must not report is_valid=True.")

    print("\n" + "#" * 60)
    print("# Demo complete — PLANNER_* optional; no binary required.")
    print("#" * 60 + "\n")


if __name__ == "__main__":
    main()
