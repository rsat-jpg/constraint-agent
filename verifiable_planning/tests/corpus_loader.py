"""Load LLM-shaped evidence fixtures from tests/fixtures/llm_shaped/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verifiable_planning.models import Plan

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "llm_shaped"


def iter_fixture_paths() -> list[Path]:
    return sorted(FIXTURES_DIR.glob("*.json"))


def load_fixture(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "meta" not in data or "plan" not in data:
        raise ValueError(f"Fixture {path.name} must have 'meta' and 'plan' keys")
    meta = data["meta"]
    for key in ("id", "expected_codes"):
        if key not in meta:
            raise ValueError(f"Fixture {path.name} meta missing '{key}'")
    meta.setdefault("optional_codes", [])
    meta.setdefault("title", meta["id"])
    meta.setdefault("llm_shape_notes", "")
    meta.setdefault("overlaps_notes", "")
    return data


def plan_from_fixture(data: dict[str, Any]) -> Plan:
    return Plan.model_validate(data["plan"])
