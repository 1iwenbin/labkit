"""
Playbook models for Labbook specification

This module defines the dynamic workflow models for Labbook experiments:
- Playbook: Complete experiment workflow definition
- Timeline: Background asynchronous events
- Procedure: Synchronous test sequences  
- Step: Individual execution steps with conditions
- Condition: Reusable declarative or command-based conditions
- Action: References to capability definition files

The playbook implements strict validation to ensure:
- Timeline steps must have 'at' field (time-based execution)
- Procedure steps cannot have 'at' field (trigger-based execution)
- All referenced conditions must exist
- Unique IDs for conditions and procedures
- Proper condition type validation
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import Field, validator, model_validator
from .base import BaseLabbookModel, TimeExpression


class ConditionType(str, Enum):
    """Condition types for reusable condition definitions"""
    
    DECLARATIVE = "declarative"  # Query-based conditions with rules
    COMMAND = "command"          # Command execution conditions


class Condition(BaseLabbookModel):
    """
    Reusable condition definition for conditional execution and waiting
    
    Conditions can be either declarative (query-based) or command-based:
    - Declarative: Uses queries and rules for complex state checking
    - Command: Executes commands on target nodes for simple checks
    """
    
    id: str = Field(..., description="Unique condition identifier")
    type: ConditionType = Field(ConditionType.DECLARATIVE, description="Condition type")
    query: Optional[str] = Field(None, description="Query to execute (for declarative conditions)")
    rule: Optional[str] = Field(None, description="Rule to apply (for declarative conditions)")
    command: Optional[str] = Field(None, description="Command to execute (for command conditions)")
    target: Optional[str] = Field(None, description="Target node ID (for command conditions)")
    description: Optional[str] = Field(None, description="Human-readable description")

    @validator("query", "rule")
    def validate_declarative_fields(cls, v, values):
        """Validate declarative condition has required fields"""
        if values.get("type") == ConditionType.DECLARATIVE:
            if not v:
                raise ValueError("Declarative conditions must have both query and rule")
        return v

    @validator("command", "target")
    def validate_command_fields(cls, v, values):
        """Validate command condition has required fields"""
        if values.get("type") == ConditionType.COMMAND:
            if not v:
                raise ValueError("Command conditions must have both command and target")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "network_ready",
                "type": "command",
                "command": "ping -c 1 8.8.8.8",
                "target": "client-1",
                "description": "Check if network connectivity is established"
            }
        }


class Action(BaseLabbookModel):
    """
    Action definition referencing capability files
    
    Actions point to capability definition files in events/, queries/, or monitors/
    directories that contain the actual execution logic.
    """
    
    source: str = Field(..., description="Path to capability definition file (e.g., 'events/start_traffic.yaml')")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Optional parameters to override capability defaults")

    class Config:
        json_schema_extra = {
            "example": {
                "source": "events/start_background_traffic.yaml",
                "parameters": {"duration": "30s", "rate": "1000pps"}
            }
        }


class Step(BaseLabbookModel):
    """
    Step definition in timeline or procedure
    
    Steps can be used in both Timeline (background events) and Procedure (test sequences)
    with different validation rules:
    - Timeline steps: Must have 'at' field, cannot use 'wait_for'
    - Procedure steps: Cannot have 'at' field, can use 'wait_for'
    """
    
    description: Optional[str] = Field(None, description="Human-readable step description")
    at: Optional[TimeExpression] = Field(None, description="Execution time (timeline only, time expression)")
    action: Optional[Action] = Field(None, description="Action to execute")
    run_if: Optional[str] = Field(None, description="Condition ID for conditional execution")
    wait_for: Optional[str] = Field(None, description="Condition ID to wait for (procedure only)")
    timeout: Optional[TimeExpression] = Field(None, description="Step execution timeout")

    class Config:
        json_schema_extra = {
            "example": {
                "description": "Test client to server connectivity",
                "action": {
                    "source": "queries/test_connectivity.yaml"
                },
                "timeout": "30s"
            }
        }


class Timeline(BaseLabbookModel):
    """
    Background timeline definition for asynchronous events
    
    Timeline steps are executed at specific times and run in the background.
    They cannot use wait_for conditions since they are time-based.
    """
    
    steps: List[Step] = Field(..., description="Timeline steps with execution times")

    @validator("steps")
    def validate_timeline_steps(cls, v):
        """Validate timeline steps have required 'at' field and no 'wait_for'"""
        for i, step in enumerate(v):
            if step.at is None:
                raise ValueError(f"Timeline step {i} must have 'at' field")
            if step.wait_for is not None:
                raise ValueError(f"Timeline step {i} cannot use 'wait_for'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "steps": [
                    {
                        "at": "5s",
                        "description": "Start background traffic",
                        "action": {"source": "events/start_background_traffic.yaml"}
                    }
                ]
            }
        }


class Procedure(BaseLabbookModel):
    """
    Procedure definition for synchronous test sequences
    
    Procedures are triggered at specific times and execute steps sequentially.
    They can use wait_for conditions but cannot have 'at' fields on individual steps.
    """
    
    id: str = Field(..., description="Unique procedure identifier")
    trigger_at: TimeExpression = Field(..., description="Procedure trigger time (time expression)")
    steps: List[Step] = Field(..., description="Procedure steps to execute sequentially")
    description: Optional[str] = Field(None, description="Human-readable procedure description")
    timeout: Optional[TimeExpression] = Field(None, description="Overall procedure timeout")

    @validator("steps")
    def validate_procedure_steps(cls, v):
        """Validate procedure steps don't have 'at' field"""
        for i, step in enumerate(v):
            if step.at is not None:
                raise ValueError(f"Procedure step {i} cannot have 'at' field")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "connectivity_test",
                "trigger_at": "10s",
                "description": "Test network connectivity between nodes",
                "steps": [
                    {
                        "description": "Wait for network to be ready",
                        "wait_for": "network_ready"
                    },
                    {
                        "description": "Test client to server connectivity",
                        "action": {"source": "queries/test_connectivity.yaml"}
                    }
                ]
            }
        }


class Playbook(BaseLabbookModel):
    """
    Complete playbook definition for experiment workflow
    
    The playbook contains all dynamic workflow components:
    - conditions: Reusable conditions for conditional execution
    - timeline: Background asynchronous events
    - procedures: Synchronous test sequences
    
    Implements comprehensive validation to ensure consistency.
    """
    
    conditions: Optional[List[Condition]] = Field(None, description="Reusable conditions")
    timeline: Optional[Timeline] = Field(None, description="Background timeline")
    procedures: List[Procedure] = Field(..., description="Test procedures")
    description: Optional[str] = Field(None, description="Overall playbook description")

    @model_validator(mode="after")
    def validate_playbook(self):
        """Validate playbook consistency and references"""
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
        
        # Collect references from procedures
        for proc in procedures:
            for step in proc.steps:
                if step.run_if:
                    all_condition_refs.add(step.run_if)
                if step.wait_for:
                    all_condition_refs.add(step.wait_for)

        # Collect references from timeline
        if self.timeline:
            for step in self.timeline.steps:
                if step.run_if:
                    all_condition_refs.add(step.run_if)

        # Check all references exist
        for cond_ref in all_condition_refs:
            if cond_ref not in condition_ids:
                raise ValueError(f"Referenced condition '{cond_ref}' does not exist")

        return self

    class Config:
        json_schema_extra = {
            "example": {
                "description": "Network connectivity test playbook",
                "conditions": [
                    {
                        "id": "network_ready",
                        "type": "command",
                        "command": "ping -c 1 8.8.8.8",
                        "target": "client-1"
                    }
                ],
                "timeline": {
                    "steps": [
                        {
                            "at": "5s",
                            "description": "Start background traffic",
                            "action": {"source": "events/start_background_traffic.yaml"}
                        }
                    ]
                },
                "procedures": [
                    {
                        "id": "connectivity_test",
                        "trigger_at": "10s",
                        "steps": [
                            {
                                "description": "Wait for network to be ready",
                                "wait_for": "network_ready"
                            },
                            {
                                "description": "Test connectivity",
                                "action": {"source": "queries/test_connectivity.yaml"}
                            }
                        ]
                    }
                ]
            }
        }
