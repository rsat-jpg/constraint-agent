"""
Plan models for the Verifiable Planning core.

Typed, framework-agnostic representation of a multi-step plan.
v0.1 focuses exclusively on structural properties.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class StepStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    BLOCKED = "blocked"
    COMPLETE = "complete"
    FAILED = "failed"


class Step(BaseModel):
    """A single step in a plan."""

    id: str = Field(..., description="Unique step identifier")
    description: str = Field(..., min_length=1)
    preconditions: list[str] = Field(
        default_factory=list,
        description="Step IDs or condition labels that must be satisfied before this step can run",
    )
    expected_outcome: str = Field(
        default="",
        description="What success looks like for this step (structural description only in v0.1)",
    )
    depends_on: list[str] = Field(
        default_factory=list,
        description="Explicit step IDs this step depends on (edges in the plan graph)",
    )
    is_irreversible: bool = Field(
        default=False,
        description="If True, a checkpoint is recommended before execution",
    )
    status: StepStatus = StepStatus.PENDING

    @field_validator("id")
    @classmethod
    def id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Step id cannot be empty")
        return v.strip()


class Plan(BaseModel):
    """A complete multi-step plan."""

    id: str
    goal: str = Field(..., min_length=1)
    steps: list[Step] = Field(default_factory=list)
    version: str = Field(default="0.1.0", description="Plan schema version")

    def step_ids(self) -> set[str]:
        return {s.id for s in self.steps}

    def get_step(self, step_id: str) -> Optional[Step]:
        for s in self.steps:
            if s.id == step_id:
                return s
        return None


class Severity(str, Enum):
    ERROR = "error"      # Hard structural failure — plan should not proceed
    WARNING = "warning"  # Soft issue — review recommended
    INFO = "info"


class ValidationFinding(BaseModel):
    """A single structured finding from validation."""

    code: str
    severity: Severity
    message: str
    step_ids: list[str] = Field(default_factory=list, description="Steps implicated")
    suggested_repair: str = Field(
        default="",
        description="Actionable suggestion for fixing this finding",
    )


class ValidationResult(BaseModel):
    """Complete result of validating a plan."""

    plan_id: str
    is_valid: bool
    findings: list[ValidationFinding] = Field(default_factory=list)

    @property
    def errors(self) -> list[ValidationFinding]:
        return [f for f in self.findings if f.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[ValidationFinding]:
        return [f for f in self.findings if f.severity == Severity.WARNING]
