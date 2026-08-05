"""
Tests for Decision D3 PDDL export adapter (export-only, no planner).
"""

from __future__ import annotations

import pytest

from verifiable_planning import Plan, Step, validate_plan
from verifiable_planning.adapters.pddl_bridge import (
    LOSSY_EDGES,
    free_form_precondition_labels,
    plan_to_pddl,
    pddl_atom,
)


def test_lossy_edges_document_non_effect_outcomes() -> None:
    assert "expected_outcome" in LOSSY_EDGES
    assert "not compiled" in LOSSY_EDGES.lower() or "NON-effect" in LOSSY_EDGES or "non-effect" in LOSSY_EDGES


def test_pddl_atom_sanitizes() -> None:
    assert pddl_atom("data_licensed", kind="pred") == "data_licensed"
    assert pddl_atom("Data Licensed!", kind="pred") == "data_licensed"
    assert pddl_atom("123", kind="pred").startswith("n")


def test_clean_chain_export_contains_actions_and_done_preds() -> None:
    plan = Plan(
        id="clean-export",
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
    assert validate_plan(plan).is_valid
    text = plan_to_pddl(plan)
    assert "act_gather" in text
    assert "act_write" in text
    assert "(done_gather)" in text
    assert "(done_write)" in text
    assert ":precondition (and\n      (done_gather)" in text
    # Free-text outcome is comment only, not an effect predicate from prose words
    assert "expected_outcome (not an effect)" in text
    assert "Markdown summary ready" in text
    assert free_form_precondition_labels(plan) == []


def test_label_unreachable_structurally_valid_but_visible_in_export() -> None:
    """D3 success signal: VALID structurally; export shows unestablished label."""
    plan = Plan(
        id="label-gap",
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
    result = validate_plan(plan)
    assert result.is_valid
    assert "PRECONDITION_NOT_IN_DEPENDS_ON" not in {f.code for f in result.findings}

    assert free_form_precondition_labels(plan) == ["data_licensed"]
    text = plan_to_pddl(plan)

    assert "(p_data_licensed)" in text
    assert "(:action act_b" in text
    # Label required on b; never produced as an effect (effects are done_* only)
    assert "      (p_data_licensed)" in text
    assert "(:init)" in text
    effect_lines = [ln for ln in text.splitlines() if ":effect" in ln]
    assert effect_lines
    assert all("p_data_licensed" not in ln for ln in effect_lines)


def test_empty_plan_export_raises() -> None:
    plan = Plan(id="empty", goal="Nothing", steps=[])
    with pytest.raises(ValueError, match="at least one step"):
        plan_to_pddl(plan)


def test_step_id_precondition_not_emitted_as_label_pred() -> None:
    plan = Plan(
        id="precond-step",
        goal="Extract",
        steps=[
            Step(id="gather", description="Collect"),
            Step(
                id="extract",
                description="Extract",
                depends_on=["gather"],
                preconditions=["gather"],
                expected_outcome="Done",
            ),
        ],
    )
    text = plan_to_pddl(plan)
    assert "p_gather" not in text
    assert "(done_gather)" in text
