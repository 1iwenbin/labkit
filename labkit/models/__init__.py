"""
Data models for Labbook specification

This package contains all the Pydantic models that define the data contract
for Labbook experiments.
"""

# Import all models for easy access
from .base import BaseLabbookModel, ValidationError, TimeExpression
from .labbook import Labbook
from .network import NetworkConfig, Node, Interface, L2Switch, Link, VolumeMount, InterfaceMode, Image, ImageType, SwitchProperties
from .playbook import Playbook
from .capabilities import CapabilityType, AssertionRule, Assertion, BaseCapability, Event as CapabilityEvent, Query, Monitor
from .events import (
    Event, EventType, NodeExecArgs, NodeCreateArgs, LinkCreateArgs, 
    LinkProperties, InterfaceCreateArgs, SwitchProperties as EventSwitchProperties
)

__all__ = [
    # Base models
    "BaseLabbookModel",
    "ValidationError", 
    "TimeExpression",
    
    # Core models
    "Labbook",
    "NetworkConfig",
    "Playbook",
    # Capabilities models
    "CapabilityType",
    "AssertionRule",
    "Assertion",
    "BaseCapability",
    "CapabilityEvent",
    "Query",
    "Monitor",
    
    # Network models
    "Node",
    "Interface", 
    "L2Switch",
    "Link",
    "VolumeMount",
    "InterfaceMode",
    "Image",
    "ImageType",
    "SwitchProperties",
    
    # Event models
    "Event",
    "EventType",
    "NodeExecArgs",
    "NodeCreateArgs", 
    "LinkCreateArgs",
    "LinkProperties",
    "InterfaceCreateArgs",
    "EventSwitchProperties",
]
