"""
Evidence for Expansion Gate Decision D4 (planner-gated formal checks).

Injected fake planner only — no planner binary, no network.
"""

from __future__ import annotations

from verifiable_planning import Plan, Step, validate_plan
from verifiable_planning.adapters.pddl_bridge import (
    FORMAL_CODES,
    FORMAL_UNESTABLISHED_PRECONDITION,
    check_unestablished_preconditions,
)
from verifiable_planning.adapters.planner_bridge import (
    PLANNER_CODES,
    PLANNER_ERROR,
    PLANNER_GOAL_UNREACHABLE,
    PLANNER_UNAVAILABLE,
    PlannerOutcome,
    PlannerStatus,
    check_plan_with_planner,
)


def _clean_chain() -> Plan:
    return Plan(
        id="clean-planner",
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


def _label_gap() -> Plan:
    return Plan(
        id="label-gap-planner",
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


def test_planner_codes_disjoint_from_freeze_and_formal() -> None:
    from test_surface_freeze import FROZEN_V0_1_FINDING_CODES

    assert PLANNER_CODES.isdisjoint(FROZEN_V0_1_FINDING_CODES)
    assert PLANNER_CODES.isdisjoint(FORMAL_CODES)
    assert PLANNER_GOAL_UNREACHABLE in PLANNER_CODES
    assert PLANNER_UNAVAILABLE in PLANNER_CODES
    assert PLANNER_ERROR in PLANNER_CODES


def test_clean_chain_solvable_no_planner_unreachable() -> None:
    plan = _clean_chain()
    assert validate_plan(plan).is_valid

    def run_planner(pddl: str) -> PlannerOutcome:
        assert "act_gather" in pddl
        return PlannerOutcome(status=PlannerStatus.SOLVABLE)

    result = check_plan_with_planner(plan, run_planner)
    assert result.is_valid
    assert all(f.code != PLANNER_GOAL_UNREACHABLE for f in result.findings)


def test_label_gap_structurally_valid_planner_unsat() -> None:
    plan = _label_gap()
    assert validate_plan(plan).is_valid
    formal = check_unestablished_preconditions(plan)
    assert not formal.is_valid
    assert FORMAL_UNESTABLISHED_PRECONDITION in {f.code for f in formal.findings}

    def run_planner(pddl: str) -> PlannerOutcome:
        assert "p_data_licensed" in pddl
        return PlannerOutcome(
            status=PlannerStatus.UNSAT,
            detail="no plan found",
        )

    result = check_plan_with_planner(plan, run_planner)
    assert not result.is_valid
    codes = [f.code for f in result.findings]
    assert codes == [PLANNER_GOAL_UNREACHABLE]
    assert FORMAL_UNESTABLISHED_PRECONDITION not in codes


def test_unavailable_never_silent_success() -> None:
    plan = _clean_chain()

    def run_planner(_pddl: str) -> PlannerOutcome:
        return PlannerOutcome(
            status=PlannerStatus.UNAVAILABLE,
            detail="no binary configured",
        )

    result = check_plan_with_planner(plan, run_planner)
    assert not result.is_valid
    assert [f.code for f in result.findings] == [PLANNER_UNAVAILABLE]


def test_runner_error_status() -> None:
    plan = _clean_chain()

    def run_planner(_pddl: str) -> PlannerOutcome:
        return PlannerOutcome(status=PlannerStatus.ERROR, detail="parse failed")

    result = check_plan_with_planner(plan, run_planner)
    assert not result.is_valid
    assert [f.code for f in result.findings] == [PLANNER_ERROR]


def test_runner_raises_becomes_planner_error() -> None:
    plan = _clean_chain()

    def run_planner(_pddl: str) -> PlannerOutcome:
        raise RuntimeError("boom")

    result = check_plan_with_planner(plan, run_planner)
    assert not result.is_valid
    assert [f.code for f in result.findings] == [PLANNER_ERROR]
    assert "boom" in result.findings[0].message


def test_empty_plan_no_planner_findings() -> None:
    plan = Plan(id="empty", goal="n/a", steps=[])

    def run_planner(_pddl: str) -> PlannerOutcome:
        raise AssertionError("runner must not be called for empty plans")

    result = check_plan_with_planner(plan, run_planner)
    assert result.is_valid
    assert result.findings == []
