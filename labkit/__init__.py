"""
Labkit - Python SDK for Labbook experiment specification

This package provides a Python SDK for creating and managing Labbook experiments.
It implements the three-layer architecture model with focus on usability and flexibility.
"""

from .models.labbook import Labbook
from .models.network import Topology, Node, Interface, Switch, Link, ImageSource, InterfaceMode
from .models.playbook import Playbook, Timeline, Procedure, Condition, Step, Action, ConditionType
from .models.capabilities import Event, Query, Monitor, CapabilityType, AssertionRule
from .generators.labbook import LabbookGenerator

__version__ = "0.1.0"
__all__ = [
    "Labbook",
    "Topology",
    "Node",
    "Interface",
    "Switch",
    "Link",
    "ImageSource",
    "InterfaceMode",
    "Playbook",
    "Timeline",
    "Procedure",
    "Condition",
    "Step",
    "Action",
    "ConditionType",
    "Event",
    "Query",
    "Monitor",
    "CapabilityType",
    "AssertionRule",
    "LabbookGenerator",
]
