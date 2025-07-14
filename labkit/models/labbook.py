"""
Top-level Labbook model for experiment specification
"""

from typing import Optional
from pydantic import Field
from .base import BaseLabbookModel
from .network import Topology
from .playbook import Playbook


class Labbook(BaseLabbookModel):
    """Top-level Labbook experiment definition"""

    name: str = Field(..., description="Experiment name")
    description: str = Field(..., description="Experiment description")
    version: str = Field(default="1.0", description="Labbook version")
    author: Optional[str] = Field(None, description="Experiment author")
    created_at: Optional[str] = Field(None, description="Creation timestamp")

    # Core components
    topology: Topology = Field(..., description="Network topology")
    playbook: Playbook = Field(..., description="Experiment playbook")
