"""
Structural validators for plans.

Deterministic, pure-Python checks. No LLM. No external planners.
These form the Validate stage of Plan-Validate-Execute.
"""

from __future__ import annotations

import networkx as nx
from verifiable_planning import finding_codes as codes
from verifiable_planning.models import Plan, ValidationFinding, ValidationResult, Severity


def build_graph(plan: Plan) -> nx.DiGraph:
    """Construct a directed graph from plan steps and depends_on edges."""
    g = nx.DiGraph()
    for step in plan.steps:
        g.add_node(step.id, step=step)
    for step in plan.steps:
        for dep in step.depends_on:
            g.add_edge(dep, step.id)
    return g


def validate_plan(plan: Plan) -> ValidationResult:
    """
    Run all structural validators and return a structured result.
    is_valid is True only when there are zero ERROR findings.
    """
    findings: list[ValidationFinding] = []

    findings.extend(_check_empty_plan(plan))
    findings.extend(_check_duplicate_ids(plan))
    findings.extend(_check_unknown_dependencies(plan))
    findings.extend(_check_self_dependencies(plan))
    findings.extend(_check_duplicate_dependencies(plan))
    findings.extend(_check_cycles(plan))

    # Graph warnings: DISCONNECTED_GRAPH owns orphans outside the largest
    # multi-node component; ISOLATED_STEP covers pure isolate bags.
    disconnected = _check_disconnected_graph(plan)
    findings.extend(disconnected)
    covered_by_disconnected = {
        sid
        for f in disconnected
        for sid in f.step_ids
    }
    findings.extend(
        f for f in _check_unreachable_steps(plan)
        if not f.step_ids or f.step_ids[0] not in covered_by_disconnected
    )

    findings.extend(_check_irreversible_without_context(plan))
    findings.extend(_check_precondition_depends_on(plan))
    findings.extend(_check_missing_terminal_outcome(plan))

    errors = [f for f in findings if f.severity == Severity.ERROR]
    return ValidationResult(
        plan_id=plan.id,
        is_valid=len(errors) == 0,
        findings=findings,
    )


# ---------------------------------------------------------------------------
# Individual validators
# ---------------------------------------------------------------------------

def _check_empty_plan(plan: Plan) -> list[ValidationFinding]:
    if not plan.steps:
        return [ValidationFinding(
            code=codes.EMPTY_PLAN,
            severity=Severity.ERROR,
            message="Plan contains no steps.",
            suggested_repair="Add at least one step that advances the goal.",
        )]
    return []


def _check_duplicate_ids(plan: Plan) -> list[ValidationFinding]:
    seen: set[str] = set()
    dups: list[str] = []
    for s in plan.steps:
        if s.id in seen:
            dups.append(s.id)
        seen.add(s.id)
    if dups:
        return [ValidationFinding(
            code=codes.DUPLICATE_STEP_ID,
            severity=Severity.ERROR,
            message=f"Duplicate step id(s): {sorted(set(dups))}",
            step_ids=sorted(set(dups)),
            suggested_repair="Ensure every step has a unique id.",
        )]
    return []


def _check_unknown_dependencies(plan: Plan) -> list[ValidationFinding]:
    known = plan.step_ids()
    findings = []
    for step in plan.steps:
        unknown = [d for d in step.depends_on if d not in known]
        if unknown:
            findings.append(ValidationFinding(
                code=codes.UNKNOWN_DEPENDENCY,
                severity=Severity.ERROR,
                message=f"Step '{step.id}' depends on unknown id(s): {unknown}",
                step_ids=[step.id],
                suggested_repair="Remove the unknown dependency or add the missing step.",
            ))
    return findings


def _check_self_dependencies(plan: Plan) -> list[ValidationFinding]:
    """A step must not list its own id in depends_on (trivial deadlock)."""
    findings = []
    for step in plan.steps:
        if step.id in step.depends_on:
            findings.append(ValidationFinding(
                code=codes.SELF_DEPENDENCY,
                severity=Severity.ERROR,
                message=f"Step '{step.id}' depends on itself.",
                step_ids=[step.id],
                suggested_repair="Remove the step's own id from depends_on.",
            ))
    return findings


def _check_duplicate_dependencies(plan: Plan) -> list[ValidationFinding]:
    """Repeated ids in depends_on are noise (graph collapses them to one edge)."""
    findings = []
    for step in plan.steps:
        seen: set[str] = set()
        dups: list[str] = []
        for dep in step.depends_on:
            if dep in seen and dep not in dups:
                dups.append(dep)
            seen.add(dep)
        if dups:
            findings.append(ValidationFinding(
                code=codes.DUPLICATE_DEPENDENCY,
                severity=Severity.WARNING,
                message=(
                    f"Step '{step.id}' lists duplicate depends_on id(s): {dups}."
                ),
                step_ids=[step.id],
                suggested_repair="Deduplicate depends_on so each dependency appears once.",
            ))
    return findings


def _check_cycles(plan: Plan) -> list[ValidationFinding]:
    g = build_graph(plan)
    try:
        cycles = list(nx.simple_cycles(g))
    except nx.NetworkXNoCycle:
        cycles = []
    if cycles:
        # Length-1 cycles are SELF_DEPENDENCY; report multi-node cycles here.
        reported = []
        for cycle in cycles:
            if len(cycle) < 2:
                continue
            cyc_str = " -> ".join(cycle + [cycle[0]])
            reported.append(ValidationFinding(
                code=codes.DEPENDENCY_CYCLE,
                severity=Severity.ERROR,
                message=f"Dependency cycle detected: {cyc_str}",
                step_ids=cycle,
                suggested_repair="Break the cycle by removing or reordering one of the depends_on edges.",
            ))
        return reported
    return []


def _check_unreachable_steps(plan: Plan) -> list[ValidationFinding]:
    """
    Steps that have no path from any root (steps with no incoming edges)
    and are not themselves roots are considered unreachable in a simple sense.
    For v0.1 we flag steps that are isolated (no edges at all) when the plan
    has more than one step — usually a sign of a missing dependency.
    """
    if len(plan.steps) <= 1:
        return []
    g = build_graph(plan)
    findings = []
    for node in g.nodes:
        if g.in_degree(node) == 0 and g.out_degree(node) == 0:
            findings.append(ValidationFinding(
                code=codes.ISOLATED_STEP,
                severity=Severity.WARNING,
                message=f"Step '{node}' has no dependencies and nothing depends on it.",
                step_ids=[node],
                suggested_repair="Connect it via depends_on or confirm it is intentionally independent.",
            ))
    return findings


def _check_disconnected_graph(plan: Plan) -> list[ValidationFinding]:
    """
    Multi-step plans should form one weakly connected dependency graph.
    Separate chains (a→b and c→d) are a common LLM planning defect that
    ISOLATED_STEP misses because those steps still have edges.

    Pure isolate bags (all components size 1) are owned by ISOLATED_STEP.
    """
    if len(plan.steps) <= 1:
        return []
    known = plan.step_ids()
    g = build_graph(plan)
    step_nodes = [n for n in g.nodes if n in known]
    if len(step_nodes) <= 1:
        return []
    subgraph = g.subgraph(step_nodes)
    components = [
        sorted(comp)
        for comp in nx.weakly_connected_components(subgraph)
    ]
    if len(components) <= 1:
        return []
    if max(len(c) for c in components) < 2:
        return []
    components.sort(key=lambda c: (-len(c), c))
    extra_ids = sorted(
        step_id
        for comp in components[1:]
        for step_id in comp
    )
    return [ValidationFinding(
        code=codes.DISCONNECTED_GRAPH,
        severity=Severity.WARNING,
        message=(
            f"Plan dependency graph has {len(components)} disconnected "
            f"components; steps outside the largest component: {extra_ids}."
        ),
        step_ids=extra_ids,
        suggested_repair=(
            "Connect the subgraphs via depends_on, or split into separate plans."
        ),
    )]


def _check_irreversible_without_context(plan: Plan) -> list[ValidationFinding]:
    """Soft check: irreversible steps should ideally have clear expected outcomes."""
    findings = []
    for step in plan.steps:
        if step.is_irreversible and not step.expected_outcome.strip():
            findings.append(ValidationFinding(
                code=codes.IRREVERSIBLE_NO_OUTCOME,
                severity=Severity.WARNING,
                message=f"Irreversible step '{step.id}' has no expected_outcome described.",
                step_ids=[step.id],
                suggested_repair="Add a clear expected_outcome so the step can be reviewed before execution.",
            ))
    return findings


def _check_precondition_depends_on(plan: Plan) -> list[ValidationFinding]:
    """
    Preconditions that name known step IDs must also appear in depends_on.
    Free-form condition labels (not matching any step id) are ignored in v0.1.
    """
    known = plan.step_ids()
    findings = []
    for step in plan.steps:
        missing_edges = [
            p for p in step.preconditions
            if p in known and p not in step.depends_on
        ]
        if missing_edges:
            findings.append(ValidationFinding(
                code=codes.PRECONDITION_NOT_IN_DEPENDS_ON,
                severity=Severity.WARNING,
                message=(
                    f"Step '{step.id}' lists precondition step id(s) {missing_edges} "
                    f"but omits them from depends_on."
                ),
                step_ids=[step.id],
                suggested_repair="Add the precondition step id(s) to depends_on, or use a non-step condition label.",
            ))
    return findings


def _check_missing_terminal_outcome(plan: Plan) -> list[ValidationFinding]:
    """
    Structural proxy for goal coverage: at least one terminal step
    (no dependents) should declare an expected_outcome.
    Skipped when the graph has cycles — DEPENDENCY_CYCLE owns that case.
    """
    if not plan.steps:
        return []
    g = build_graph(plan)
    known = plan.step_ids()
    # Only consider nodes that are real plan steps (unknown deps may add ghost nodes).
    step_nodes = [n for n in g.nodes if n in known]
    if not step_nodes:
        return []
    subgraph = g.subgraph(step_nodes)
    if not nx.is_directed_acyclic_graph(subgraph):
        return []
    terminals = [n for n in step_nodes if subgraph.out_degree(n) == 0]
    if not terminals:
        return []
    lacking: list[str] = []
    for n in terminals:
        step = plan.get_step(n)
        if step is not None and not step.expected_outcome.strip():
            lacking.append(n)
    if len(lacking) == len(terminals):
        return [ValidationFinding(
            code=codes.MISSING_TERMINAL_OUTCOME,
            severity=Severity.WARNING,
            message=(
                "No terminal step declares an expected_outcome — "
                "goal coverage is not structurally evidenced."
            ),
            step_ids=sorted(terminals),
            suggested_repair=(
                "Add expected_outcome on at least one terminal step "
                "(a step nothing else depends on)."
            ),
        )]
    return []
