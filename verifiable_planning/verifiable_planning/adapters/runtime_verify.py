"""
Thin runtime verification adapter (Expansion Gate Decision D2 / Candidate C).

Job: compare an inspectable step-event stream to a Plan's dependency structure
and irreversible checkpoints. Never replaces structural ``validate_plan``.
Never mutates the plan. Core stays free of this module — callers import it
explicitly.
"""

from __future__ import annotations

from enum import Enum

import networkx as nx
from pydantic import BaseModel, Field

from verifiable_planning.models import (
    Plan,
    Severity,
    ValidationFinding,
    ValidationResult,
)
from verifiable_planning.validators import build_graph

# Runtime namespace — not part of the frozen structural finding_codes set.
RUNTIME_UNKNOWN_STEP = "RUNTIME_UNKNOWN_STEP"
RUNTIME_DEPENDENCY_ORDER = "RUNTIME_DEPENDENCY_ORDER"
RUNTIME_INCOMPLETE = "RUNTIME_INCOMPLETE"
RUNTIME_MISSING_CHECKPOINT = "RUNTIME_MISSING_CHECKPOINT"

RUNTIME_CODES = frozenset(
    {
        RUNTIME_UNKNOWN_STEP,
        RUNTIME_DEPENDENCY_ORDER,
        RUNTIME_INCOMPLETE,
        RUNTIME_MISSING_CHECKPOINT,
    }
)


class StepEventType(str, Enum):
    CHECKPOINT = "checkpoint"
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"


class StepEvent(BaseModel):
    """One inspectable execution event. Stream list order is execution order."""

    step_id: str = Field(..., min_length=1)
    type: StepEventType


def linear_trace(plan: Plan) -> list[StepEvent]:
    """
    Deterministic demo/test emitter: topo-order STARTED then COMPLETED per step.

    For ``is_irreversible`` steps, emits CHECKPOINT immediately before STARTED.
    Not an agent runtime. Raises ``ValueError`` if the known-step graph is not a DAG
    (caller should run structural Validate first).
    """
    if not plan.steps:
        return []
    known = plan.step_ids()
    irreversible = {s.id for s in plan.steps if s.is_irreversible}
    g = build_graph(plan)
    step_nodes = [n for n in g.nodes if n in known]
    subgraph = g.subgraph(step_nodes)
    if not nx.is_directed_acyclic_graph(subgraph):
        raise ValueError(
            "linear_trace requires an acyclic plan among known step ids; "
            "run validate_plan first and fix DEPENDENCY_CYCLE / SELF_DEPENDENCY."
        )
    order = list(nx.topological_sort(subgraph))
    events: list[StepEvent] = []
    for step_id in order:
        if step_id in irreversible:
            events.append(StepEvent(step_id=step_id, type=StepEventType.CHECKPOINT))
        events.append(StepEvent(step_id=step_id, type=StepEventType.STARTED))
        events.append(StepEvent(step_id=step_id, type=StepEventType.COMPLETED))
    return events


def verify_trace(
    plan: Plan,
    events: list[StepEvent],
    *,
    plan_id: str | None = None,
) -> ValidationResult:
    """
    Check ``events`` against ``plan`` depends_on structure and irreversible
    checkpoints.

    ``is_valid`` is True only when there are zero ERROR findings.
    Does not call or replace ``validate_plan``.
    """
    findings: list[ValidationFinding] = []
    known = plan.step_ids()
    irreversible = {s.id for s in plan.steps if s.is_irreversible}
    completed: set[str] = set()
    # failed steps are recorded but do not satisfy dependents in this slice
    failed: set[str] = set()
    checkpointed: set[str] = set()

    depends: dict[str, list[str]] = {
        step.id: list(step.depends_on) for step in plan.steps
    }

    for event in events:
        sid = event.step_id.strip()
        if sid not in known:
            findings.append(ValidationFinding(
                code=RUNTIME_UNKNOWN_STEP,
                severity=Severity.ERROR,
                message=f"Event references unknown step id '{sid}'.",
                step_ids=[sid],
                suggested_repair="Emit events only for step ids present in the plan.",
            ))
            continue

        if event.type == StepEventType.CHECKPOINT:
            checkpointed.add(sid)
            continue

        if event.type in (StepEventType.STARTED, StepEventType.COMPLETED):
            if sid in irreversible and sid not in checkpointed:
                findings.append(ValidationFinding(
                    code=RUNTIME_MISSING_CHECKPOINT,
                    severity=Severity.ERROR,
                    message=(
                        f"Irreversible step '{sid}' {event.type.value} without "
                        f"a prior CHECKPOINT event for that step."
                    ),
                    step_ids=[sid],
                    suggested_repair=(
                        "Emit a CHECKPOINT event for this step_id before "
                        "STARTED (or COMPLETED) on an irreversible step."
                    ),
                ))

            missing_deps = [
                d for d in depends.get(sid, [])
                if d in known and d not in completed
            ]
            if missing_deps:
                findings.append(ValidationFinding(
                    code=RUNTIME_DEPENDENCY_ORDER,
                    severity=Severity.ERROR,
                    message=(
                        f"Step '{sid}' {event.type.value} before completed "
                        f"depends_on: {missing_deps}."
                    ),
                    step_ids=[sid, *missing_deps],
                    suggested_repair=(
                        "Complete prerequisite steps before starting or "
                        "completing this step."
                    ),
                ))

        if event.type == StepEventType.COMPLETED:
            completed.add(sid)
            failed.discard(sid)
        elif event.type == StepEventType.FAILED:
            failed.add(sid)

    incomplete = sorted(known - completed)
    if incomplete:
        findings.append(ValidationFinding(
            code=RUNTIME_INCOMPLETE,
            severity=Severity.WARNING,
            message=(
                f"Plan step(s) never completed in the trace: {incomplete}."
            ),
            step_ids=incomplete,
            suggested_repair=(
                "Emit COMPLETED for remaining steps, or use a partial-run "
                "override intentionally."
            ),
        ))

    errors = [f for f in findings if f.severity == Severity.ERROR]
    return ValidationResult(
        plan_id=plan_id if plan_id is not None else plan.id,
        is_valid=len(errors) == 0,
        findings=findings,
    )
