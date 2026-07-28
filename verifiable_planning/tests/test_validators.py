"""
Positive + negative evidence for each structural validator.

Failure injection is first-class: each negative case proves what v0.1 catches.
"""

from __future__ import annotations

from models import Plan, Step, Severity
from validators import validate_plan


def _codes(result) -> set[str]:
    return {f.code for f in result.findings}


def _codes_of(result, severity: Severity) -> set[str]:
    return {f.code for f in result.findings if f.severity == severity}


def _chain_plan(plan_id: str = "plan-ok") -> Plan:
    """Connected multi-step plan that should produce zero findings."""
    return Plan(
        id=plan_id,
        goal="Produce a research summary",
        steps=[
            Step(id="gather", description="Collect sources", depends_on=[]),
            Step(id="extract", description="Extract claims", depends_on=["gather"]),
            Step(
                id="write",
                description="Write summary",
                depends_on=["extract"],
                expected_outcome="Structured markdown summary",
            ),
        ],
    )


# ---------------------------------------------------------------------------
# EMPTY_PLAN
# ---------------------------------------------------------------------------

def test_empty_plan_negative():
    result = validate_plan(Plan(id="empty", goal="Nothing", steps=[]))
    assert result.is_valid is False
    assert "EMPTY_PLAN" in _codes(result)
    assert all(f.suggested_repair for f in result.findings if f.code == "EMPTY_PLAN")


def test_empty_plan_positive():
    result = validate_plan(_chain_plan())
    assert "EMPTY_PLAN" not in _codes(result)
    assert result.is_valid is True


# ---------------------------------------------------------------------------
# DUPLICATE_STEP_ID
# ---------------------------------------------------------------------------

def test_duplicate_step_id_negative():
    plan = Plan(
        id="dups",
        goal="Duplicate ids",
        steps=[
            Step(id="a", description="First A", depends_on=[]),
            Step(id="a", description="Second A", depends_on=[]),
        ],
    )
    result = validate_plan(plan)
    assert result.is_valid is False
    assert "DUPLICATE_STEP_ID" in _codes(result)
    finding = next(f for f in result.findings if f.code == "DUPLICATE_STEP_ID")
    assert "a" in finding.step_ids
    assert finding.suggested_repair


def test_duplicate_step_id_positive():
    result = validate_plan(_chain_plan())
    assert "DUPLICATE_STEP_ID" not in _codes(result)


# ---------------------------------------------------------------------------
# UNKNOWN_DEPENDENCY
# ---------------------------------------------------------------------------

def test_unknown_dependency_negative():
    plan = Plan(
        id="unknown",
        goal="Missing dependency",
        steps=[
            Step(id="start", description="Start", depends_on=[]),
            Step(id="finish", description="Finish", depends_on=["missing_step"]),
        ],
    )
    result = validate_plan(plan)
    assert result.is_valid is False
    assert "UNKNOWN_DEPENDENCY" in _codes(result)
    finding = next(f for f in result.findings if f.code == "UNKNOWN_DEPENDENCY")
    assert finding.step_ids == ["finish"]
    assert finding.suggested_repair


def test_unknown_dependency_positive():
    result = validate_plan(_chain_plan())
    assert "UNKNOWN_DEPENDENCY" not in _codes(result)


# ---------------------------------------------------------------------------
# DEPENDENCY_CYCLE
# ---------------------------------------------------------------------------

def test_dependency_cycle_negative():
    plan = Plan(
        id="cycle",
        goal="Circular dependency",
        steps=[
            Step(id="a", description="A", depends_on=["c"]),
            Step(id="b", description="B", depends_on=["a"]),
            Step(id="c", description="C", depends_on=["b"]),
        ],
    )
    result = validate_plan(plan)
    assert result.is_valid is False
    assert "DEPENDENCY_CYCLE" in _codes(result)
    finding = next(f for f in result.findings if f.code == "DEPENDENCY_CYCLE")
    assert set(finding.step_ids) == {"a", "b", "c"}
    assert finding.suggested_repair


def test_dependency_cycle_positive():
    result = validate_plan(_chain_plan())
    assert "DEPENDENCY_CYCLE" not in _codes(result)


# ---------------------------------------------------------------------------
# ISOLATED_STEP
# ---------------------------------------------------------------------------

def test_isolated_step_negative():
    plan = Plan(
        id="isolated",
        goal="Isolated steps",
        steps=[
            Step(id="main", description="Main", depends_on=[]),
            Step(id="orphan", description="Orphan", depends_on=[]),
        ],
    )
    result = validate_plan(plan)
    # Warnings only — still structurally valid
    assert result.is_valid is True
    assert "ISOLATED_STEP" in _codes_of(result, Severity.WARNING)
    assert {f.step_ids[0] for f in result.findings if f.code == "ISOLATED_STEP"} == {
        "main",
        "orphan",
    }


def test_isolated_step_positive_connected_graph():
    result = validate_plan(_chain_plan())
    assert "ISOLATED_STEP" not in _codes(result)


def test_isolated_step_positive_single_step_exempt():
    """A lone step cannot be 'isolated' in a multi-step sense."""
    plan = Plan(
        id="solo",
        goal="One step",
        steps=[Step(id="only", description="Only step", depends_on=[])],
    )
    result = validate_plan(plan)
    assert "ISOLATED_STEP" not in _codes(result)
    assert result.is_valid is True


# ---------------------------------------------------------------------------
# IRREVERSIBLE_NO_OUTCOME
# ---------------------------------------------------------------------------

def test_irreversible_no_outcome_negative():
    plan = Plan(
        id="irreversible",
        goal="Dangerous step",
        steps=[
            Step(
                id="delete",
                description="Delete production data",
                depends_on=[],
                is_irreversible=True,
            ),
        ],
    )
    result = validate_plan(plan)
    assert result.is_valid is True
    assert "IRREVERSIBLE_NO_OUTCOME" in _codes_of(result, Severity.WARNING)
    finding = next(f for f in result.findings if f.code == "IRREVERSIBLE_NO_OUTCOME")
    assert finding.step_ids == ["delete"]
    assert finding.suggested_repair


def test_irreversible_no_outcome_positive():
    plan = Plan(
        id="irreversible-ok",
        goal="Dangerous but documented",
        steps=[
            Step(
                id="delete",
                description="Delete production data",
                depends_on=[],
                is_irreversible=True,
                expected_outcome="Named table removed; backup verified",
            ),
        ],
    )
    result = validate_plan(plan)
    assert "IRREVERSIBLE_NO_OUTCOME" not in _codes(result)
    assert result.is_valid is True


# ---------------------------------------------------------------------------
# Aggregate: good plan is clean
# ---------------------------------------------------------------------------

def test_good_plan_has_no_findings():
    result = validate_plan(_chain_plan("plan-good"))
    assert result.is_valid is True
    assert result.findings == []
    assert result.errors == []
    assert result.warnings == []
