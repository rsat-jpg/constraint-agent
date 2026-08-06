"""
Plan → Validate → PDDL export + convention-FORMAL_* demo (Expansion Gate D3).

No planner binary, no network. Structural Validate stays the offline gate.
Convention-FORMAL_* is static over Plan + LOSSY_EDGES — not planner reachability.
"""

from __future__ import annotations

from verifiable_planning import Plan, Step, ValidationResult, validate_plan
from verifiable_planning.adapters.pddl_bridge import (
    FORMAL_UNESTABLISHED_PRECONDITION,
    LOSSY_EDGES,
    check_unestablished_preconditions,
    free_form_precondition_labels,
    plan_to_pddl,
)


def print_result(result: ValidationResult, *, title: str | None = None) -> None:
    status = "VALID" if result.is_valid else "INVALID"
    label = title or f"Plan: {result.plan_id}"
    print(f"\n{'='*60}")
    print(f"{label}  →  {status}")
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
    print("\n" + "#" * 60)
    print("# PDDL export — lossy edges (documented)")
    print("#" * 60)
    print(LOSSY_EDGES)

    # ------------------------------------------------------------------
    # A. Happy path: structurally clean chain → export + formal clean
    # ------------------------------------------------------------------
    print("\n" + "#" * 60)
    print("# Plan → Validate → formal → PDDL — happy path (clean chain)")
    print("#" * 60)

    clean = Plan(
        id="pddl-demo-clean",
        goal="Ship a checked summary",
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
    structural = validate_plan(clean)
    print_result(structural, title="Structural")
    if not structural.is_valid:
        raise SystemExit("Clean plan must be structurally VALID.")

    formal_clean = check_unestablished_preconditions(clean)
    print_result(formal_clean, title="Convention-FORMAL")
    if not formal_clean.is_valid:
        raise SystemExit("Clean plan (no free-form labels) must be formal-clean.")

    export = plan_to_pddl(clean)
    print("\n--- PDDL export (truncated) ---")
    print(export)

    # ------------------------------------------------------------------
    # B. Deliberate semantic gap: structural VALID, formal ERROR
    # ------------------------------------------------------------------
    print("\n" + "#" * 60)
    print("# Deliberate label gap — structural VALID, formal ERROR")
    print("#" * 60)

    gap = Plan(
        id="pddl-demo-label-gap",
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
    structural_gap = validate_plan(gap)
    print_result(structural_gap, title="Structural")
    if not structural_gap.is_valid:
        raise SystemExit("Label-gap plan must remain structurally VALID.")
    if "PRECONDITION_NOT_IN_DEPENDS_ON" in {f.code for f in structural_gap.findings}:
        raise SystemExit(
            "Free-form label must not fire PRECONDITION_NOT_IN_DEPENDS_ON."
        )

    labels = free_form_precondition_labels(gap)
    print(f"Free-form precondition labels: {labels}")

    formal_gap = check_unestablished_preconditions(gap)
    print_result(formal_gap, title="Convention-FORMAL")
    if formal_gap.is_valid:
        raise SystemExit("Label-gap plan must be formal INVALID.")
    formal_codes = {f.code for f in formal_gap.findings}
    if FORMAL_UNESTABLISHED_PRECONDITION not in formal_codes:
        raise SystemExit(
            f"Expected {FORMAL_UNESTABLISHED_PRECONDITION}; got {formal_codes}."
        )

    gap_export = plan_to_pddl(gap)
    print("\n--- PDDL export (label gap) ---")
    print(gap_export)

    if "p_data_licensed" not in gap_export:
        raise SystemExit("Export must mention predicate p_data_licensed.")
    if any(
        "p_data_licensed" in ln and ":effect" in ln for ln in gap_export.splitlines()
    ):
        raise SystemExit("p_data_licensed must not appear as an effect.")

    print(
        "\nDemo complete: structural Validate unchanged; "
        "convention-FORMAL_* and PDDL export are optional (no planner)."
    )


if __name__ == "__main__":
    main()
