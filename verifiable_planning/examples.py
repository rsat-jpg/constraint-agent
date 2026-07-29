"""
Simple runner and demonstration of the Validate stage.
"""

from __future__ import annotations

from verifiable_planning import Plan, Step, ValidationResult, validate_plan


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


def main() -> None:
    # ------------------------------------------------------------------
    # Good plan
    # ------------------------------------------------------------------
    good = Plan(
        id="plan-good-001",
        goal="Prepare a clean research summary",
        steps=[
            Step(id="gather", description="Collect source documents", depends_on=[]),
            Step(id="extract", description="Extract key claims", depends_on=["gather"]),
            Step(
                id="synthesize",
                description="Write summary",
                depends_on=["extract"],
                expected_outcome="A structured markdown summary",
            ),
        ],
    )

    # ------------------------------------------------------------------
    # Broken plans (deliberate failure cases)
    # ------------------------------------------------------------------
    empty = Plan(id="plan-empty", goal="Do nothing useful", steps=[])

    cycle = Plan(
        id="plan-cycle",
        goal="Circular dependency demo",
        steps=[
            Step(id="a", description="Step A", depends_on=["c"]),
            Step(id="b", description="Step B", depends_on=["a"]),
            Step(id="c", description="Step C", depends_on=["b"]),
        ],
    )

    unknown_dep = Plan(
        id="plan-unknown",
        goal="Missing dependency",
        steps=[
            Step(id="start", description="Start", depends_on=[]),
            Step(id="finish", description="Finish", depends_on=["missing_step"]),
        ],
    )

    self_dep = Plan(
        id="plan-self-dep",
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

    dup_dep = Plan(
        id="plan-dup-dep",
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

    isolated = Plan(
        id="plan-isolated",
        goal="Isolated step warning",
        steps=[
            Step(id="main", description="Main work", depends_on=[]),
            Step(id="orphan", description="Orphaned step", depends_on=[]),
        ],
    )

    disconnected = Plan(
        id="plan-disconnected",
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

    irreversible = Plan(
        id="plan-irreversible",
        goal="Irreversible without outcome description",
        steps=[
            Step(
                id="delete",
                description="Delete production data",
                depends_on=[],
                is_irreversible=True,
                # expected_outcome deliberately left empty
            ),
        ],
    )

    precond_mismatch = Plan(
        id="plan-precond",
        goal="Precondition without depends_on edge",
        steps=[
            Step(id="gather", description="Collect sources", depends_on=[]),
            Step(
                id="extract",
                description="Extract claims",
                depends_on=[],
                preconditions=["gather"],
                expected_outcome="Claim list",
            ),
        ],
    )

    no_terminal_outcome = Plan(
        id="plan-no-terminal-outcome",
        goal="Steps without a stated terminal outcome",
        steps=[
            Step(id="a", description="Step A", depends_on=[]),
            Step(id="b", description="Step B", depends_on=["a"]),
        ],
    )

    print("=== GOOD PLAN ===")
    print_result(validate_plan(good))

    print("\n=== EMPTY PLAN ===")
    print_result(validate_plan(empty))

    print("\n=== CYCLE ===")
    print_result(validate_plan(cycle))

    print("\n=== UNKNOWN DEPENDENCY ===")
    print_result(validate_plan(unknown_dep))

    print("\n=== SELF DEPENDENCY ===")
    print_result(validate_plan(self_dep))

    print("\n=== DUPLICATE DEPENDENCY ===")
    print_result(validate_plan(dup_dep))

    print("\n=== ISOLATED STEP ===")
    print_result(validate_plan(isolated))

    print("\n=== DISCONNECTED GRAPH ===")
    print_result(validate_plan(disconnected))

    print("\n=== IRREVERSIBLE WITHOUT OUTCOME ===")
    print_result(validate_plan(irreversible))

    print("\n=== PRECONDITION NOT IN DEPENDS_ON ===")
    print_result(validate_plan(precond_mismatch))

    print("\n=== MISSING TERMINAL OUTCOME ===")
    print_result(validate_plan(no_terminal_outcome))


if __name__ == "__main__":
    main()
