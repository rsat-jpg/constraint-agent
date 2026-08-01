"""
Evidence corpus: LLM-shaped plan fixtures → validate_plan.

Static JSON under tests/fixtures/llm_shaped/. No live LLM / network.
"""

from __future__ import annotations

import json

import pytest

from verifiable_planning import Severity, validate_plan
from verifiable_planning import finding_codes as codes
from verifiable_planning.adapters.llm_planner import plan_from_llm_text

from corpus_loader import (
    FIXTURES_DIR,
    iter_fixture_paths,
    load_fixture,
    plan_from_fixture,
)

ALL_FINDING_CODES = {
    codes.EMPTY_PLAN,
    codes.DUPLICATE_STEP_ID,
    codes.UNKNOWN_DEPENDENCY,
    codes.SELF_DEPENDENCY,
    codes.DEPENDENCY_CYCLE,
    codes.DUPLICATE_DEPENDENCY,
    codes.REDUNDANT_DEPENDENCY,
    codes.ISOLATED_STEP,
    codes.DISCONNECTED_GRAPH,
    codes.IRREVERSIBLE_NO_OUTCOME,
    codes.PRECONDITION_NOT_IN_DEPENDS_ON,
    codes.MISSING_TERMINAL_OUTCOME,
    codes.MULTIPLE_TERMINALS,
}

D1_ROUNDTRIP_IDS = frozenset({"clean_chain", "unknown_dep"})


def _fixture_ids() -> list[str]:
    return [p.stem for p in iter_fixture_paths()]


@pytest.mark.parametrize("fixture_id", _fixture_ids())
def test_corpus_fixture_expected_codes(fixture_id: str):
    path = FIXTURES_DIR / f"{fixture_id}.json"
    data = load_fixture(path)
    meta = data["meta"]
    assert meta["id"] == fixture_id

    plan = plan_from_fixture(data)
    result = validate_plan(plan)
    observed = {f.code for f in result.findings}
    expected = set(meta["expected_codes"])
    optional = set(meta.get("optional_codes") or [])

    missing = expected - observed
    assert not missing, f"{fixture_id}: missing expected codes {sorted(missing)}; got {sorted(observed)}"

    if not expected:
        assert result.findings == [], (
            f"{fixture_id}: clean fixture must have zero findings; got {sorted(observed)}"
        )

    # ERROR findings must be accounted for in expected_codes
    error_codes = {f.code for f in result.findings if f.severity == Severity.ERROR}
    unexpected_errors = error_codes - expected
    assert not unexpected_errors, (
        f"{fixture_id}: unexpected ERROR codes {sorted(unexpected_errors)}"
    )

    # Anything beyond expected∪optional is a corpus surprise (fail closed)
    allowed = expected | optional
    surprise = observed - allowed
    assert not surprise, (
        f"{fixture_id}: unexpected codes {sorted(surprise)}; "
        f"expected={sorted(expected)} optional={sorted(optional)}"
    )


def test_corpus_covers_all_finding_codes():
    covered: set[str] = set()
    for path in iter_fixture_paths():
        meta = load_fixture(path)["meta"]
        covered |= set(meta["expected_codes"])
    missing = ALL_FINDING_CODES - covered
    assert not missing, f"Corpus expected_codes miss: {sorted(missing)}"


@pytest.mark.parametrize("fixture_id", sorted(D1_ROUNDTRIP_IDS))
def test_corpus_d1_roundtrip_same_expected_codes(fixture_id: str):
    path = FIXTURES_DIR / f"{fixture_id}.json"
    data = load_fixture(path)
    expected = set(data["meta"]["expected_codes"])
    optional = set(data["meta"].get("optional_codes") or [])

    text = json.dumps(data["plan"])
    plan = plan_from_llm_text(text)
    result = validate_plan(plan)
    observed = {f.code for f in result.findings}

    assert expected <= observed
    if not expected:
        assert result.findings == []
    surprise = observed - (expected | optional)
    assert not surprise


def test_two_chains_does_not_emit_isolated_step():
    data = load_fixture(FIXTURES_DIR / "two_chains.json")
    result = validate_plan(plan_from_fixture(data))
    assert "ISOLATED_STEP" not in {f.code for f in result.findings}


def test_fork_without_join_does_not_emit_disconnected():
    data = load_fixture(FIXTURES_DIR / "fork_without_join.json")
    result = validate_plan(plan_from_fixture(data))
    assert "DISCONNECTED_GRAPH" not in {f.code for f in result.findings}


def test_isolate_bag_does_not_emit_disconnected():
    data = load_fixture(FIXTURES_DIR / "isolate_bag.json")
    result = validate_plan(plan_from_fixture(data))
    assert "DISCONNECTED_GRAPH" not in {f.code for f in result.findings}


def test_self_dep_does_not_emit_dependency_cycle():
    data = load_fixture(FIXTURES_DIR / "self_dep.json")
    result = validate_plan(plan_from_fixture(data))
    codes_seen = {f.code for f in result.findings}
    assert "SELF_DEPENDENCY" in codes_seen
    assert "DEPENDENCY_CYCLE" not in codes_seen
