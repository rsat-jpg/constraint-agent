"""
Positive + negative evidence for each structural validator.

Failure injection is first-class: each negative case proves what v0.1 catches.
"""

from __future__ import annotations

from verifiable_planning import Plan, Step, Severity, validate_plan


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
# SELF_DEPENDENCY
# ---------------------------------------------------------------------------

def test_self_dependency_negative():
    plan = Plan(
        id="self-dep",
        goal="Step depends on itself",
        steps=[
            Step(
                id="loop",
                description="Cannot start",
                depends_on=["loop"],
                expected_outcome="Should never run",
            ),
        ],
    )
    result = validate_plan(plan)
    assert result.is_valid is False
    assert "SELF_DEPENDENCY" in _codes(result)
    assert "DEPENDENCY_CYCLE" not in _codes(result)
    finding = next(f for f in result.findings if f.code == "SELF_DEPENDENCY")
    assert finding.step_ids == ["loop"]
    assert finding.suggested_repair


def test_self_dependency_positive():
    result = validate_plan(_chain_plan())
    assert "SELF_DEPENDENCY" not in _codes(result)


# ---------------------------------------------------------------------------
# DUPLICATE_DEPENDENCY
# ---------------------------------------------------------------------------

def test_duplicate_dependency_negative():
    plan = Plan(
        id="dup-dep",
        goal="Repeated depends_on entry",
        steps=[
            Step(id="gather", description="Collect sources", depends_on=[]),
            Step(
                id="write",
                description="Draft summary",
                depends_on=["gather", "gather"],
                expected_outcome="Markdown summary ready",
            ),
        ],
    )
    result = validate_plan(plan)
    assert "DUPLICATE_DEPENDENCY" in _codes(result)
    assert result.is_valid is True  # warning only
    finding = next(f for f in result.findings if f.code == "DUPLICATE_DEPENDENCY")
    assert finding.severity == Severity.WARNING
    assert finding.step_ids == ["write"]
    assert finding.suggested_repair


def test_duplicate_dependency_positive():
    result = validate_plan(_chain_plan())
    assert "DUPLICATE_DEPENDENCY" not in _codes(result)


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
        steps=[
            Step(
                id="only",
                description="Only step",
                depends_on=[],
                expected_outcome="Goal advanced",
            ),
        ],
    )
    result = validate_plan(plan)
    assert "ISOLATED_STEP" not in _codes(result)
    assert result.is_valid is True


# ---------------------------------------------------------------------------
# DISCONNECTED_GRAPH
# ---------------------------------------------------------------------------

def test_disconnected_graph_negative_two_chains():
    plan = Plan(
        id="two-chains",
        goal="Two separate workstreams",
        steps=[
            Step(id="a", description="Chain A start", depends_on=[]),
            Step(
                id="b",
                description="Chain A end",
                depends_on=["a"],
                expected_outcome="A done",
            ),
            Step(id="c", description="Chain C start", depends_on=[]),
            Step(
                id="d",
                description="Chain C end",
                depends_on=["c"],
                expected_outcome="C done",
            ),
        ],
    )
    result = validate_plan(plan)
    assert "DISCONNECTED_GRAPH" in _codes(result)
    assert "ISOLATED_STEP" not in _codes(result)
    assert result.is_valid is True
    finding = next(f for f in result.findings if f.code == "DISCONNECTED_GRAPH")
    assert finding.severity == Severity.WARNING
    assert finding.step_ids == ["c", "d"]
    assert finding.suggested_repair


def test_disconnected_graph_positive_connected():
    result = validate_plan(_chain_plan())
    assert "DISCONNECTED_GRAPH" not in _codes(result)
    assert "ISOLATED_STEP" not in _codes(result)


def test_disconnected_graph_edge_chain_plus_isolated():
    plan = Plan(
        id="chain-plus-orphan",
        goal="Connected chain with an orphan",
        steps=[
            Step(id="a", description="Start", depends_on=[]),
            Step(
                id="b",
                description="Finish",
                depends_on=["a"],
                expected_outcome="Done",
            ),
            Step(id="orphan", description="Unrelated", depends_on=[]),
        ],
    )
    result = validate_plan(plan)
    assert "DISCONNECTED_GRAPH" in _codes(result)
    assert "ISOLATED_STEP" not in _codes(result)
    finding = next(f for f in result.findings if f.code == "DISCONNECTED_GRAPH")
    assert finding.step_ids == ["orphan"]


def test_all_isolates_use_isolated_step_not_disconnected():
    plan = Plan(
        id="all-isolates",
        goal="Two unconnected degree-zero steps",
        steps=[
            Step(id="main", description="Main work", depends_on=[]),
            Step(id="orphan", description="Orphaned step", depends_on=[]),
        ],
    )
    result = validate_plan(plan)
    assert "ISOLATED_STEP" in _codes(result)
    assert "DISCONNECTED_GRAPH" not in _codes(result)
    assert {f.step_ids[0] for f in result.findings if f.code == "ISOLATED_STEP"} == {
        "main",
        "orphan",
    }


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
# PRECONDITION_NOT_IN_DEPENDS_ON
# ---------------------------------------------------------------------------

def test_precondition_not_in_depends_on_negative():
    plan = Plan(
        id="precond-mismatch",
        goal="Precondition without edge",
        steps=[
            Step(id="gather", description="Collect sources", depends_on=[]),
            Step(
                id="extract",
                description="Extract claims",
                depends_on=[],  # missing edge
                preconditions=["gather"],
                expected_outcome="Claim list",
            ),
        ],
    )
    result = validate_plan(plan)
    assert result.is_valid is True
    assert "PRECONDITION_NOT_IN_DEPENDS_ON" in _codes_of(result, Severity.WARNING)
    finding = next(f for f in result.findings if f.code == "PRECONDITION_NOT_IN_DEPENDS_ON")
    assert finding.step_ids == ["extract"]
    assert finding.suggested_repair


def test_precondition_not_in_depends_on_positive_aligned():
    plan = Plan(
        id="precond-ok",
        goal="Aligned precondition",
        steps=[
            Step(id="gather", description="Collect sources", depends_on=[]),
            Step(
                id="extract",
                description="Extract claims",
                depends_on=["gather"],
                preconditions=["gather"],
                expected_outcome="Claim list",
            ),
        ],
    )
    result = validate_plan(plan)
    assert "PRECONDITION_NOT_IN_DEPENDS_ON" not in _codes(result)


def test_precondition_not_in_depends_on_positive_freeform_label():
    """Non-step condition labels are ignored by this structural check."""
    plan = Plan(
        id="precond-label",
        goal="Free-form precondition",
        steps=[
            Step(
                id="only",
                description="Work",
                depends_on=[],
                preconditions=["sources_available"],
                expected_outcome="Done",
            ),
        ],
    )
    result = validate_plan(plan)
    assert "PRECONDITION_NOT_IN_DEPENDS_ON" not in _codes(result)


# ---------------------------------------------------------------------------
# MISSING_TERMINAL_OUTCOME
# ---------------------------------------------------------------------------

def test_missing_terminal_outcome_negative():
    plan = Plan(
        id="no-terminal-outcome",
        goal="Reach a goal without stating outcomes",
        steps=[
            Step(id="a", description="A", depends_on=[]),
            Step(id="b", description="B", depends_on=["a"]),
        ],
    )
    result = validate_plan(plan)
    assert result.is_valid is True
    assert "MISSING_TERMINAL_OUTCOME" in _codes_of(result, Severity.WARNING)
    finding = next(f for f in result.findings if f.code == "MISSING_TERMINAL_OUTCOME")
    assert finding.step_ids == ["b"]
    assert finding.suggested_repair


def test_missing_terminal_outcome_positive():
    result = validate_plan(_chain_plan())
    assert "MISSING_TERMINAL_OUTCOME" not in _codes(result)


def test_missing_terminal_outcome_skipped_on_cycle():
    plan = Plan(
        id="cycle-skip-terminal",
        goal="Cycle owns the failure",
        steps=[
            Step(id="a", description="A", depends_on=["c"]),
            Step(id="b", description="B", depends_on=["a"]),
            Step(id="c", description="C", depends_on=["b"]),
        ],
    )
    result = validate_plan(plan)
    assert "DEPENDENCY_CYCLE" in _codes(result)
    assert "MISSING_TERMINAL_OUTCOME" not in _codes(result)


# ---------------------------------------------------------------------------
# Aggregate: good plan is clean
# ---------------------------------------------------------------------------

def test_good_plan_has_no_findings():
    result = validate_plan(_chain_plan("plan-good"))
    assert result.is_valid is True
    assert result.findings == []
    assert result.errors == []
    assert result.warnings == []
