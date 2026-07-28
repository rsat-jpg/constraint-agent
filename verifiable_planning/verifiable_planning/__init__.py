"""
Verifiable Planning — structural Validate core (Plan-Validate-Execute).

Public API for v0.1. Schema fields on Plan / ValidationFinding / ValidationResult
are treated as stable within the 0.1.x line; breaking changes bump the minor
or major package version and note the impact in the commit message.
"""

from verifiable_planning.models import (
    Plan,
    Severity,
    Step,
    StepStatus,
    ValidationFinding,
    ValidationResult,
)
from verifiable_planning.validators import build_graph, validate_plan

__version__ = "0.1.0"
SCHEMA_VERSION = "0.1.0"

__all__ = [
    "Plan",
    "Step",
    "StepStatus",
    "Severity",
    "ValidationFinding",
    "ValidationResult",
    "build_graph",
    "validate_plan",
    "SCHEMA_VERSION",
    "__version__",
]
