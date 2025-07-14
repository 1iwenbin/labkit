"""
Playbook models for Labbook specification
"""

from typing import List, Optional
from enum import Enum
from pydantic import Field, validator, model_validator
from .base import BaseLabbookModel


class ConditionType(str, Enum):
    """Condition types"""

    DECLARATIVE = "declarative"
    COMMAND = "command"


class Condition(BaseLabbookModel):
    """Reusable condition definition"""

    id: str = Field(..., description="Condition identifier")
    type: ConditionType = Field(ConditionType.DECLARATIVE, description="Condition type")
    query: Optional[str] = Field(None, description="Query to execute (for declarative)")
    rule: Optional[str] = Field(None, description="Rule to apply (for declarative)")
    command: Optional[str] = Field(None, description="Command to execute (for command)")
    target: Optional[str] = Field(None, description="Target node (for command)")

    @validator("query", "rule")
    def validate_declarative_fields(cls, v, values):
        if values.get("type") == ConditionType.DECLARATIVE:
            if not v:
                raise ValueError("Declarative conditions must have both query and rule")
        return v

    @validator("command", "target")
    def validate_command_fields(cls, v, values):
        if values.get("type") == ConditionType.COMMAND:
            if not v:
                raise ValueError("Command conditions must have both command and target")
        return v


class Action(BaseLabbookModel):
    """Action definition"""

    source: str = Field(..., description="Path to capability definition file")


class Step(BaseLabbookModel):
    """Step definition in timeline or procedure"""

    description: Optional[str] = Field(None, description="Step description")
    at: Optional[str] = Field(None, description="Execution time (timeline only, time expression)")
    action: Optional[Action] = Field(None, description="Action to execute")
    run_if: Optional[str] = Field(None, description="Condition ID for conditional execution")
    wait_for: Optional[str] = Field(None, description="Condition ID to wait for (procedure only)")
    # 移除at和wait_for的validator，交由Timeline和Procedure的validator整体校验


class Timeline(BaseLabbookModel):
    """Background timeline definition"""

    steps: List[Step] = Field(..., description="Timeline steps")

    @validator("steps")
    def validate_timeline_steps(cls, v):
        for step in v:
            if step.at is None:
                raise ValueError("Timeline steps must have at field")
            if step.wait_for is not None:
                raise ValueError("Timeline steps cannot use wait_for")
        return v


class Procedure(BaseLabbookModel):
    """Procedure definition"""

    id: str = Field(..., description="Procedure identifier")
    trigger_at: str = Field(..., description="Procedure trigger time (time expression)")
    steps: List[Step] = Field(..., description="Procedure steps")

    @validator("steps")
    def validate_procedure_steps(cls, v):
        for step in v:
            if step.at is not None:
                raise ValueError("Procedure steps cannot have at field")
        return v


class Playbook(BaseLabbookModel):
    """Playbook definition"""

    conditions: Optional[List[Condition]] = Field(None, description="Reusable conditions")
    timeline: Optional[Timeline] = Field(None, description="Background timeline")
    procedures: List[Procedure] = Field(..., description="Test procedures")

    @model_validator(mode="after")
    def validate_playbook(self):
        """Validate playbook consistency"""
        conditions = self.conditions or []
        procedures = self.procedures

        # Validate condition IDs are unique
        condition_ids = [cond.id for cond in conditions]
        if len(condition_ids) != len(set(condition_ids)):
            raise ValueError("Condition IDs must be unique")

        # Validate procedure IDs are unique
        procedure_ids = [proc.id for proc in procedures]
        if len(procedure_ids) != len(set(procedure_ids)):
            raise ValueError("Procedure IDs must be unique")

        # Validate all referenced conditions exist
        all_condition_refs = set()
        for proc in procedures:
            for step in proc.steps:
                if step.run_if:
                    all_condition_refs.add(step.run_if)
                if step.wait_for:
                    all_condition_refs.add(step.wait_for)

        if self.timeline:
            for step in self.timeline.steps:
                if step.run_if:
                    all_condition_refs.add(step.run_if)

        for cond_ref in all_condition_refs:
            if cond_ref not in condition_ids:
                raise ValueError(f"Referenced condition '{cond_ref}' does not exist")

        return self
