"""
Thin LLM planner adapter (Expansion Gate Decision D1 / Candidate A).

Job: turn a goal (+ injected text completer) into a schema-valid ``Plan``.
Never replaces Validate. Never imports an LLM SDK — callers inject
``complete(prompt) -> str``. Core validators remain deterministic and LLM-free.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Any

from verifiable_planning.models import Plan

CompleteFn = Callable[[str], str]


PLAN_JSON_INSTRUCTIONS = """\
Return ONLY a single JSON object (no markdown fences, no prose) with this shape:
{
  "id": "<plan id string>",
  "goal": "<goal string>",
  "version": "0.1.0",
  "steps": [
    {
      "id": "<unique step id>",
      "description": "<what to do>",
      "depends_on": ["<step id>", "..."],
      "preconditions": [],
      "expected_outcome": "<success looks like, especially on terminal steps>",
      "is_irreversible": false
    }
  ]
}
Rules: every depends_on target must be a step id in this plan; no cycles;
at least one step; terminal steps should set expected_outcome.
"""


def build_plan_prompt(goal: str, *, plan_id: str = "llm-plan") -> str:
    """Prompt fragment that asks a completer for Plan-shaped JSON."""
    return (
        f"Create a multi-step plan for this goal.\n"
        f"Suggested plan id: {plan_id}\n"
        f"Goal: {goal}\n\n"
        f"{PLAN_JSON_INSTRUCTIONS}"
    )


def _strip_fences(text: str) -> str:
    text = text.strip()
    fence = re.match(
        r"^```(?:json)?\s*\n?(.*?)\n?```\s*$",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if fence:
        return fence.group(1).strip()
    return text


def plan_from_llm_text(text: str, *, default_goal: str | None = None) -> Plan:
    """
    Parse completer output into a ``Plan``.

    Raises ``ValueError`` with a visible message when JSON/schema mapping fails.
    Does not call ``validate_plan`` — callers run Validate as a separate stage.
    """
    raw = _strip_fences(text)
    try:
        payload: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM planner output is not valid JSON: {exc}. "
            "Completer must return a Plan-shaped JSON object."
        ) from exc

    if not isinstance(payload, dict):
        raise ValueError(
            "LLM planner output must be a JSON object matching the Plan schema."
        )

    if "goal" not in payload or not str(payload.get("goal", "")).strip():
        if default_goal:
            payload = {**payload, "goal": default_goal}
        else:
            raise ValueError("LLM planner JSON is missing a non-empty 'goal'.")

    if "id" not in payload or not str(payload.get("id", "")).strip():
        payload = {**payload, "id": "llm-plan"}

    if "version" not in payload:
        payload = {**payload, "version": "0.1.0"}

    try:
        return Plan.model_validate(payload)
    except Exception as exc:
        raise ValueError(
            f"LLM planner JSON could not be mapped to Plan: {exc}"
        ) from exc


def plan_from_goal(
    goal: str,
    complete: CompleteFn,
    *,
    plan_id: str = "llm-plan",
) -> Plan:
    """
    Ask ``complete`` for Plan JSON for ``goal``, then parse to ``Plan``.

    ``complete`` is any callable ``(prompt: str) -> str`` (SDK wrapper, stub, etc.).
    """
    if not goal.strip():
        raise ValueError("goal must be non-empty")
    prompt = build_plan_prompt(goal, plan_id=plan_id)
    text = complete(prompt)
    if not isinstance(text, str) or not text.strip():
        raise ValueError("completer returned empty output; cannot build a Plan")
    return plan_from_llm_text(text, default_goal=goal)
