"""
Evidence for Expansion Gate Decision D1 (thin LLM→Plan adapter).

Uses an injected fake completer — no LLM SDK, no network.
"""

from __future__ import annotations

import json

import pytest

from verifiable_planning import validate_plan
from verifiable_planning.adapters.llm_planner import (
    build_plan_prompt,
    plan_from_goal,
    plan_from_llm_text,
)


def _good_payload(goal: str = "Prepare a research summary") -> dict:
    return {
        "id": "llm-good",
        "goal": goal,
        "version": "0.1.0",
        "steps": [
            {
                "id": "gather",
                "description": "Collect sources",
                "depends_on": [],
            },
            {
                "id": "write",
                "description": "Draft summary",
                "depends_on": ["gather"],
                "expected_outcome": "Markdown summary ready",
            },
        ],
    }


def test_plan_from_goal_with_fake_completer_is_valid():
    payload = _good_payload()

    def complete(prompt: str) -> str:
        assert "Prepare a research summary" in prompt
        return json.dumps(payload)

    plan = plan_from_goal("Prepare a research summary", complete, plan_id="llm-good")
    result = validate_plan(plan)
    assert plan.id == "llm-good"
    assert result.is_valid
    assert result.findings == []


def test_broken_llm_plan_is_caught_by_validate():
    """Planner defects stay visible — Validate does not get bypassed."""
    broken = {
        "id": "llm-broken",
        "goal": "Finish somehow",
        "steps": [
            {"id": "start", "description": "Begin", "depends_on": []},
            {
                "id": "finish",
                "description": "End",
                "depends_on": ["missing_step"],
            },
        ],
    }

    def complete(_prompt: str) -> str:
        return json.dumps(broken)

    plan = plan_from_goal("Finish somehow", complete)
    result = validate_plan(plan)
    assert not result.is_valid
    assert "UNKNOWN_DEPENDENCY" in {f.code for f in result.findings}


def test_invalid_json_fails_visibly():
    with pytest.raises(ValueError, match="not valid JSON"):
        plan_from_llm_text("not json at all")


def test_markdown_fenced_json_is_accepted():
    body = json.dumps(_good_payload())
    plan = plan_from_llm_text(f"```json\n{body}\n```")
    assert plan.id == "llm-good"
    assert validate_plan(plan).is_valid


def test_empty_goal_rejected():
    with pytest.raises(ValueError, match="non-empty"):
        plan_from_goal("  ", lambda _p: "{}")


def test_build_plan_prompt_includes_schema_hint():
    prompt = build_plan_prompt("Ship docs", plan_id="p1")
    assert "Ship docs" in prompt
    assert "depends_on" in prompt
    assert "p1" in prompt


def test_core_public_api_does_not_export_adapter():
    import verifiable_planning as vp

    assert not hasattr(vp, "plan_from_goal")
    assert "adapters" not in vp.__all__
