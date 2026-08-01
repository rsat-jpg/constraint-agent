"""
v0.1 Validate surface freeze lock.

Fails if finding codes are added/removed/renamed without updating
the freeze policy (README) and this expected set.
"""

from __future__ import annotations

import verifiable_planning.finding_codes as codes

# Explicit 0.1.x contract — update only with an unfreeze / version decision.
FROZEN_V0_1_FINDING_CODES = frozenset(
    {
        "EMPTY_PLAN",
        "DUPLICATE_STEP_ID",
        "UNKNOWN_DEPENDENCY",
        "SELF_DEPENDENCY",
        "DEPENDENCY_CYCLE",
        "DUPLICATE_DEPENDENCY",
        "REDUNDANT_DEPENDENCY",
        "ISOLATED_STEP",
        "DISCONNECTED_GRAPH",
        "IRREVERSIBLE_NO_OUTCOME",
        "PRECONDITION_NOT_IN_DEPENDS_ON",
        "MISSING_TERMINAL_OUTCOME",
        "MULTIPLE_TERMINALS",
    }
)


def test_v0_1_finding_code_surface_frozen():
    module_codes = {
        value
        for name, value in vars(codes).items()
        if name.isupper() and isinstance(value, str)
    }
    assert module_codes == FROZEN_V0_1_FINDING_CODES, (
        "Finding-code surface drifted from the v0.1 freeze. "
        "If intentional: update README freeze policy, CHANGELOG, "
        "evidence corpus, and this frozenset; bump package version "
        "when expanding the surface (prefer 0.2.0)."
    )
    assert len(module_codes) == 13
