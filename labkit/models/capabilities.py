"""
Capability definition models for Labbook specification
"""

from typing import List, Dict, Any, Optional, Union
from enum import Enum
from pydantic import Field, validator
from .base import BaseLabbookModel


class CapabilityType(str, Enum):
    """Capability types"""
    EVENT = "event"
    QUERY = "query"
    MONITOR = "monitor"


class AssertionRule(str, Enum):
    """Assertion rule types"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"


class Assertion(BaseLabbookModel):
    """Assertion definition for query results"""
    path: str = Field(..., description="JSON path to the value to check")
    rule: AssertionRule = Field(..., description="Assertion rule")
    value: Optional[Any] = Field(None, description="Expected value (not needed for exists/not_exists)")


class BaseCapability(BaseLabbookModel):
    """Base capability definition - self-contained task with all necessary information"""
    name: str = Field(..., description="Capability name (e.g., 'query.check-primary-path')")
    description: str = Field(..., description="Detailed description of what this capability does")
    type: CapabilityType = Field(..., description="Type of capability: event, query, or monitor")
    target: str = Field(..., description="Target node ID where this capability will be executed")
    with_params: Optional[Dict[str, Any]] = Field(
        None, 
        alias="with", 
        description="Execution parameters - all parameters needed for this specific task"
    )
    assert_conditions: Optional[List[Assertion]] = Field(
        None, 
        alias="assert", 
        description="Assertion conditions for validating results (mainly for queries)"
    )
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "name": "query.check-primary-path",
                "description": "Check if route to 8.8.8.8 is on primary path",
                "type": "query",
                "target": "core-router-1",
                "with": {"destination": "8.8.8.8"},
                "assert": [
                    {
                        "path": "result.nexthop",
                        "rule": "equals", 
                        "value": "10.0.1.2"
                    }
                ]
            }
        }


class Event(BaseCapability):
    """Event capability definition"""
    type: CapabilityType = Field(CapabilityType.EVENT, description="Capability type")
    
    @validator('assert_conditions')
    def validate_event_assertions(cls, v):
        if v is not None:
            raise ValueError('Events should not have assertions')
        return v


class Query(BaseCapability):
    """Query capability definition"""
    type: CapabilityType = Field(CapabilityType.QUERY, description="Capability type")


class Monitor(BaseCapability):
    """Monitor capability definition - continuous monitoring with time-based parameters"""
    type: CapabilityType = Field(CapabilityType.MONITOR, description="Capability type")
    interval: Optional[str] = Field(
        None, 
        description="Monitoring interval (time expression like '5s', '1m') - how often to check"
    )
    duration: Optional[str] = Field(
        None, 
        description="Monitoring duration (time expression like '10m', '1h') - how long to monitor"
    )
    max_samples: Optional[int] = Field(
        None,
        description="Maximum number of samples to collect during monitoring"
    )
    threshold: Optional[Dict[str, Any]] = Field(
        None,
        description="Threshold conditions for alerting (e.g., {'cpu_usage': '>80%'})"
    )
    
    @validator('max_samples')
    def validate_max_samples(cls, v):
        if v is not None and v <= 0:
            raise ValueError('max_samples must be positive')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "monitor.cpu-usage",
                "description": "Monitor CPU usage on target node",
                "type": "monitor",
                "target": "server-1",
                "with": {"metric": "cpu_usage"},
                "interval": "5s",
                "duration": "10m",
                "max_samples": 120,
                "threshold": {"cpu_usage": ">80%"}
            }
        } 