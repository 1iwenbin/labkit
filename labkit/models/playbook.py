"""
Playbook models for Labbook specification

This module defines the dynamic workflow models for Labbook experiments:
- Playbook: Complete experiment workflow definition
- TimelineItem: Background asynchronous events
- Procedure: Synchronous test sequences  
- Step: Individual execution steps with conditions
- Condition: Reusable declarative or command-based conditions
- Action: References to capability definition files
- RunIf: Conditional execution structure
- WaitFor: Waiting condition structure

The playbook implements validation to ensure:
- All referenced conditions exist
- Unique IDs for conditions and procedures
- Proper condition type validation
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import Field, validator, model_validator
from .base import BaseLabbookModel


class ConditionType(str, Enum):
    """Condition types for reusable condition definitions"""
    
    DECLARATIVE = "declarative"  # Query-based conditions with rules
    SCRIPTED = "scripted"        # Script-based conditions
    COMMAND = "command"          # Command execution conditions


class Condition(BaseLabbookModel):
    """
    Reusable condition definition for conditional execution and waiting
    
    Conditions can be declarative, scripted, or command-based:
    - Declarative: Uses queries and rules for complex state checking
    - Scripted: Uses scripts for custom logic
    - Command: Executes commands on target nodes for simple checks
    """
    
    type: ConditionType = Field(..., description="Condition type: declarative, scripted, command")
    description: Optional[str] = Field(None, description="Human-readable description")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "command",
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


class RunIf(BaseLabbookModel):
    """
    Conditional execution structure
    
    Defines a condition and action to execute if the condition is met.
    """
    
    condition: str = Field(..., description="Condition expression")
    action: Action = Field(..., description="Action to execute if condition is met")

    class Config:
        json_schema_extra = {
            "example": {
                "condition": "network_ready",
                "action": {
                    "source": "queries/test_connectivity.yaml"
                }
            }
        }


class WaitFor(BaseLabbookModel):
    """
    Waiting condition structure
    
    Defines a condition to wait for before proceeding.
    """
    
    condition: str = Field(..., description="Condition expression to wait for")

    class Config:
        json_schema_extra = {
            "example": {
                "condition": "network_ready"
            }
        }


class Step(BaseLabbookModel):
    """
    Step definition in procedure
    
    Steps are used in procedures for test sequences.
    """
    
    description: Optional[str] = Field(None, description="Human-readable step description")
    run_if: Optional[RunIf] = Field(None, description="Conditional execution structure")
    wait_for: Optional[WaitFor] = Field(None, description="Waiting condition structure")
    action: Optional[Action] = Field(None, description="Action to execute")

    class Config:
        json_schema_extra = {
            "example": {
                "description": "Test client to server connectivity",
                "action": {
                    "source": "queries/test_connectivity.yaml"
                }
            }
        }


class TimelineItem(BaseLabbookModel):
    """
    Timeline item definition for background asynchronous events
    
    Timeline items are executed at specific times and run in the background.
    """
    
    at: int = Field(..., description="Event occurrence time (uint64)")
    description: Optional[str] = Field(None, description="Event description")
    action: Optional[Action] = Field(None, description="Action to execute")

    class Config:
        json_schema_extra = {
            "example": {
                "at": 5000,
                "description": "Start background traffic",
                "action": {"source": "events/start_background_traffic.yaml"}
            }
        }


class Procedure(BaseLabbookModel):
    """
    Procedure definition for synchronous test sequences
    
    Procedures are triggered at specific times and execute steps sequentially.
    """
    
    id: str = Field(..., description="Unique procedure identifier")
    description: Optional[str] = Field(None, description="Human-readable procedure description")
    steps: List[Step] = Field(..., description="Procedure steps to execute sequentially")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "connectivity_test",
                "description": "Test network connectivity between nodes",
                "steps": [
                    {
                        "description": "Wait for network to be ready",
                        "wait_for": {"condition": "network_ready"}
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
    - conditions: Reusable conditions for conditional execution (id -> condition)
    - timeline: Background asynchronous events
    - procedures: Synchronous test sequences (id -> procedure)
    
    Implements validation to ensure consistency.
    """
    
    timeline: Optional[List[TimelineItem]] = Field(None, description="Background timeline")
    conditions: Optional[Dict[str, Condition]] = Field(None, description="Reusable conditions (id -> condition)")
    procedures: Optional[Dict[str, Procedure]] = Field(None, description="Test procedures (id -> procedure)")
    description: Optional[str] = Field(None, description="Overall playbook description")

    @model_validator(mode="after")
    def validate_playbook(self):
        """Validate playbook consistency and references"""
        conditions = self.conditions or {}
        procedures = self.procedures or {}

        # Validate all referenced conditions exist
        all_condition_refs = set()
        
        # Collect references from procedures
        for proc in procedures.values():
            for step in proc.steps:
                if step.run_if:
                    all_condition_refs.add(step.run_if.condition)
                if step.wait_for:
                    all_condition_refs.add(step.wait_for.condition)

        # Check all references exist
        for cond_ref in all_condition_refs:
            if cond_ref not in conditions:
                raise ValueError(f"Referenced condition '{cond_ref}' does not exist")

        return self

    class Config:
        json_schema_extra = {
            "example": {
                "description": "Network connectivity test playbook",
                "conditions": {
                    "network_ready": {
                        "type": "command",
                        "description": "Check if network connectivity is established"
                    }
                },
                "timeline": [
                    {
                        "at": 5000,
                        "description": "Start background traffic",
                        "action": {"source": "events/start_background_traffic.yaml"}
                    }
                ],
                "procedures": {
                    "connectivity_test": {
                        "id": "connectivity_test",
                        "description": "Test network connectivity between nodes",
                        "steps": [
                            {
                                "description": "Wait for network to be ready",
                                "wait_for": {"condition": "network_ready"}
                            },
                            {
                                "description": "Test connectivity",
                                "action": {"source": "queries/test_connectivity.yaml"}
                            }
                        ]
                    }
                }
            }
        }
