"""
Goal → Plan → Validate demo (Expansion Gate Decision D1).

Uses an injected fake completer — no LLM SDK, no API keys, no network.
Validate stays a separate stage after plan_from_goal.
"""

from __future__ import annotations

import json

from verifiable_planning import ValidationResult, validate_plan
from verifiable_planning.adapters.llm_planner import plan_from_goal


def print_result(result: ValidationResult) -> None:
    status = "VALID" if result.is_valid else "INVALID"
    print(f"\n{'='*60}")
    print(f"Plan: {result.plan_id}  →  {status}")
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


def print_plan_summary(plan_id: str, step_ids: list[str]) -> None:
    print(f"\nEmitted plan id: {plan_id}")
    print(f"Step ids: {step_ids}")


def main() -> None:
    goal = "Prepare a research summary"

    # ------------------------------------------------------------------
    # A. Happy path: goal → plan_from_goal (fake complete) → validate
    # ------------------------------------------------------------------
    print("\n" + "#" * 60)
    print("# LLM Plan → Validate — happy path (fake completer)")
    print("#" * 60)

    good_payload = {
        "id": "llm-demo-good",
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

    def complete_good(prompt: str) -> str:
        assert goal in prompt
        return json.dumps(good_payload)

    plan = plan_from_goal(goal, complete_good, plan_id="llm-demo-good")
    print_plan_summary(plan.id, [s.id for s in plan.steps])
    result = validate_plan(plan)
    print_result(result)
    if not result.is_valid:
        raise SystemExit(
            "Happy-path plan is INVALID; fix fake completer payload before continuing."
        )

    # ------------------------------------------------------------------
    # B. Deliberate failure: LLM-shaped unknown dependency
    # ------------------------------------------------------------------
    print("\n" + "#" * 60)
    print("# LLM Plan → Validate — deliberate failure (UNKNOWN_DEPENDENCY)")
    print("#" * 60)

    broken_payload = {
        "id": "llm-demo-broken",
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

    def complete_broken(_prompt: str) -> str:
        return json.dumps(broken_payload)

    bad_plan = plan_from_goal("Finish somehow", complete_broken)
    print_plan_summary(bad_plan.id, [s.id for s in bad_plan.steps])
    print_result(validate_plan(bad_plan))


if __name__ == "__main__":
    main()
