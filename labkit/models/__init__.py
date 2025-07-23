"""
Data models for Labbook specification

This package contains all the Pydantic models that define the data contract
for Labbook experiments.

The models are organized into several categories:
- Base models: Core validation and utility classes
- Core models: Main experiment definition models (Labbook, NetworkConfig, Playbook)
- Capabilities models: Event, query, and monitor capability definitions
- Network models: Network topology and configuration models
- Event models: Event-specific argument and property models
"""

# Import all models for easy access
from .base import BaseLabbookModel, ValidationError, TimeExpression
from .labbook import Labbook, API_VERSION, KIND
from .network import (
    NetworkConfig, Node, Interface, L2Switch, Link, VolumeMount, 
    InterfaceMode, Image, ImageType, SwitchProperties
)
from .playbook import (
    Playbook, TimelineItem, Procedure, Step, Condition, Action,
    RunIf, WaitFor, ConditionType
)
from .events import (
    EventType, NodeExecArgs, NodeCreateArgs, LinkCreateArgs, 
    LinkProperties, InterfaceCreateArgs, SwitchProperties as EventSwitchProperties
)

__all__ = [
    # Base models
    "BaseLabbookModel",
    "ValidationError", 
    "TimeExpression",
    
    # Core models
    "Labbook",
    "API_VERSION",
    "KIND",
    "NetworkConfig",
    "Playbook",
    
    # Playbook models
    "TimelineItem",
    "Procedure", 
    "Step",
    "Condition",
    "Action",
    "RunIf",
    "WaitFor",
    "ConditionType",
    
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
    "EventType",
    "NodeExecArgs",
    "NodeCreateArgs", 
    "LinkCreateArgs",
    "LinkProperties",
    "InterfaceCreateArgs",
    "EventSwitchProperties",
]
