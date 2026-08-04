"""
Evidence for Expansion Gate Decision D2 (thin runtime verification).

Uses linear_trace and hand-crafted event lists — no live executor.
"""

from __future__ import annotations

import pytest

from verifiable_planning import Plan, Step, Severity, validate_plan
import verifiable_planning.finding_codes as structural_codes
from verifiable_planning.adapters.runtime_verify import (
    RUNTIME_CODES,
    RUNTIME_DEPENDENCY_ORDER,
    RUNTIME_INCOMPLETE,
    RUNTIME_MISSING_CHECKPOINT,
    RUNTIME_UNKNOWN_STEP,
    StepEvent,
    StepEventType,
    linear_trace,
    verify_trace,
)
from test_surface_freeze import FROZEN_V0_1_FINDING_CODES


def _chain_plan() -> Plan:
    return Plan(
        id="runtime-chain",
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


def test_linear_trace_on_clean_plan_has_no_runtime_errors():
    plan = _chain_plan()
    assert validate_plan(plan).is_valid
    events = linear_trace(plan)
    result = verify_trace(plan, events)
    assert result.is_valid is True
    assert result.findings == []
    assert [e.type for e in events] == [
        StepEventType.STARTED,
        StepEventType.COMPLETED,
    ] * 3


def test_dependency_order_violation():
    plan = _chain_plan()
    events = [
        StepEvent(step_id="write", type=StepEventType.STARTED),
        StepEvent(step_id="write", type=StepEventType.COMPLETED),
    ]
    result = verify_trace(plan, events)
    assert result.is_valid is False
    codes = {f.code for f in result.findings}
    assert RUNTIME_DEPENDENCY_ORDER in codes
    assert RUNTIME_INCOMPLETE in codes
    finding = next(f for f in result.findings if f.code == RUNTIME_DEPENDENCY_ORDER)
    assert finding.severity == Severity.ERROR
    assert "write" in finding.step_ids
    assert finding.suggested_repair


def test_unknown_step_event():
    plan = _chain_plan()
    events = [
        StepEvent(step_id="gather", type=StepEventType.STARTED),
        StepEvent(step_id="gather", type=StepEventType.COMPLETED),
        StepEvent(step_id="missing_step", type=StepEventType.COMPLETED),
    ]
    result = verify_trace(plan, events)
    assert result.is_valid is False
    assert RUNTIME_UNKNOWN_STEP in {f.code for f in result.findings}
    finding = next(f for f in result.findings if f.code == RUNTIME_UNKNOWN_STEP)
    assert finding.step_ids == ["missing_step"]


def test_incomplete_trace_warning_only():
    plan = _chain_plan()
    events = [
        StepEvent(step_id="gather", type=StepEventType.STARTED),
        StepEvent(step_id="gather", type=StepEventType.COMPLETED),
    ]
    result = verify_trace(plan, events)
    assert result.is_valid is True  # warnings only
    assert RUNTIME_INCOMPLETE in {f.code for f in result.findings}
    finding = next(f for f in result.findings if f.code == RUNTIME_INCOMPLETE)
    assert finding.severity == Severity.WARNING
    assert set(finding.step_ids) == {"extract", "write"}


def test_empty_events_incomplete():
    plan = _chain_plan()
    result = verify_trace(plan, [])
    assert result.is_valid is True
    assert RUNTIME_INCOMPLETE in {f.code for f in result.findings}


def test_linear_trace_rejects_cyclic_plan():
    plan = Plan(
        id="cycle",
        goal="Cyclic",
        steps=[
            Step(id="a", description="A", depends_on=["c"]),
            Step(id="b", description="B", depends_on=["a"]),
            Step(id="c", description="C", depends_on=["b"]),
        ],
    )
    with pytest.raises(ValueError, match="acyclic"):
        linear_trace(plan)


def _irreversible_plan() -> Plan:
    return Plan(
        id="runtime-irreversible",
        goal="Publish after review checkpoint",
        steps=[
            Step(id="draft", description="Write draft", depends_on=[]),
            Step(
                id="publish",
                description="Publish artifact",
                depends_on=["draft"],
                expected_outcome="Artifact published",
                is_irreversible=True,
            ),
        ],
    )


def test_linear_trace_emits_checkpoint_before_irreversible_start():
    plan = _irreversible_plan()
    assert validate_plan(plan).is_valid
    events = linear_trace(plan)
    assert events == [
        StepEvent(step_id="draft", type=StepEventType.STARTED),
        StepEvent(step_id="draft", type=StepEventType.COMPLETED),
        StepEvent(step_id="publish", type=StepEventType.CHECKPOINT),
        StepEvent(step_id="publish", type=StepEventType.STARTED),
        StepEvent(step_id="publish", type=StepEventType.COMPLETED),
    ]
    result = verify_trace(plan, events)
    assert result.is_valid is True
    assert RUNTIME_MISSING_CHECKPOINT not in {f.code for f in result.findings}


def test_missing_checkpoint_on_irreversible_started():
    plan = _irreversible_plan()
    events = [
        StepEvent(step_id="draft", type=StepEventType.STARTED),
        StepEvent(step_id="draft", type=StepEventType.COMPLETED),
        StepEvent(step_id="publish", type=StepEventType.STARTED),
        StepEvent(step_id="publish", type=StepEventType.COMPLETED),
    ]
    result = verify_trace(plan, events)
    assert result.is_valid is False
    codes = [f.code for f in result.findings]
    assert codes.count(RUNTIME_MISSING_CHECKPOINT) == 2  # STARTED + COMPLETED
    finding = next(f for f in result.findings if f.code == RUNTIME_MISSING_CHECKPOINT)
    assert finding.severity == Severity.ERROR
    assert finding.step_ids == ["publish"]
    assert finding.suggested_repair


def test_missing_checkpoint_on_completed_without_prior_checkpoint():
    plan = _irreversible_plan()
    events = [
        StepEvent(step_id="draft", type=StepEventType.STARTED),
        StepEvent(step_id="draft", type=StepEventType.COMPLETED),
        StepEvent(step_id="publish", type=StepEventType.COMPLETED),
    ]
    result = verify_trace(plan, events)
    assert result.is_valid is False
    assert RUNTIME_MISSING_CHECKPOINT in {f.code for f in result.findings}


def test_core_public_api_does_not_export_runtime_adapter():
    import verifiable_planning as vp

    assert not hasattr(vp, "verify_trace")
    assert not hasattr(vp, "linear_trace")
    assert "adapters" not in vp.__all__


def test_runtime_codes_disjoint_from_structural_freeze():
    assert RUNTIME_CODES.isdisjoint(FROZEN_V0_1_FINDING_CODES)
    structural = {
        value
        for name, value in vars(structural_codes).items()
        if name.isupper() and isinstance(value, str)
    }
    assert RUNTIME_CODES.isdisjoint(structural)
    assert all(code.startswith("RUNTIME_") for code in RUNTIME_CODES)
