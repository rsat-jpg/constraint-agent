"""
Plan → Validate → Runtime demo (Expansion Gate Decision D2).

Not a full executor: uses linear_trace as a demo emitter, then verify_trace.
"""

from __future__ import annotations

from verifiable_planning import Plan, Step, ValidationResult, validate_plan
from verifiable_planning.adapters.runtime_verify import (
    StepEvent,
    StepEventType,
    linear_trace,
    verify_trace,
)


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


def print_events(events: list[StepEvent]) -> None:
    print("\nTrace events:")
    for e in events:
        print(f"  {e.step_id}: {e.type.value}")


def main() -> None:
    plan = Plan(
        id="runtime-demo-chain",
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

    # ------------------------------------------------------------------
    # A. Happy path: validate → linear_trace → verify_trace
    # ------------------------------------------------------------------
    print("\n" + "#" * 60)
    print("# Structural validate (offline gate)")
    print("#" * 60)
    struct = validate_plan(plan)
    print_result(struct)
    if not struct.is_valid:
        raise SystemExit(
            "Structural plan is INVALID; fix validate_plan findings before linear_trace."
        )

    print("\n" + "#" * 60)
    print("# Runtime verify — happy path (linear_trace)")
    print("#" * 60)
    events = linear_trace(plan)
    print_events(events)
    runtime_ok = verify_trace(plan, events)
    print_result(runtime_ok)

    # ------------------------------------------------------------------
    # B. Deliberate runtime failure: write before dependencies complete
    # ------------------------------------------------------------------
    print("\n" + "#" * 60)
    print("# Runtime verify — deliberate failure (dependency order)")
    print("#" * 60)
    bad_events = [
        StepEvent(step_id="write", type=StepEventType.STARTED),
        StepEvent(step_id="write", type=StepEventType.COMPLETED),
    ]
    print_events(bad_events)
    runtime_bad = verify_trace(plan, bad_events)
    print_result(runtime_bad)


if __name__ == "__main__":
    main()
