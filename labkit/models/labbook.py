"""
Top-level Labbook model for experiment specification

This module defines the top-level Labbook model that represents a labbook.yaml file.
The Labbook defines the structure and metadata of a network experiment.

Required fields:
- apiVersion: Defines the version of the labbook specification being used (e.g., "labbook.io/v1")
  This is crucial for tool compatibility - execution engines check this version before parsing
  to ensure they can handle the structure, preventing parsing errors with unknown formats.

- kind: Specifies the type of object this YAML describes, always "Labbook" for this specification
  This follows Kubernetes-style design patterns, allowing tools to handle multiple object types
  and enabling future extensibility (e.g., LabbookResult, LabbookTemplate)

- metadata: Contains all descriptive information for both human and machine consumption
  - name: Unique identifier for the experiment, used primarily by machines and automation tools
    Should be concise and script-friendly (lowercase, numbers, hyphens only)
    Examples: "bgp-convergence-test-case-1", "ospf-failover-scenario-2"
  - description: Detailed human-readable description of the experiment's background, assumptions, goals
    Helps with collaboration and future reference without needing to parse the entire timeline
  - author: Records the experiment designer or team for traceability and collaboration
  - tags: Array of strings for categorizing and discovering experiments
    Essential for managing large collections of labbooks (e.g., ["bgp", "fault-tolerance", "convergence"])
"""

from typing import Optional, Dict, Any, List
from pydantic import Field
from .base import BaseLabbookModel


# Constants for Labbook specification
API_VERSION = "labbook.io/v1"
KIND = "Labbook"


class Labbook(BaseLabbookModel):
    """
    Top-level Labbook experiment definition
    
    Represents a labbook.yaml file that defines the structure and metadata of a network experiment.
    Follows Kubernetes-style design patterns for consistency and extensibility.
    """
    
    api_version: str = Field(API_VERSION, alias="apiVersion", description="Labbook specification version")
    kind: str = Field(KIND, alias="kind", description="Object type, always 'Labbook'")
    metadata: Dict[str, Any] = Field(..., alias="metadata", description="Experiment metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "apiVersion": "labbook.io/v1",
                "kind": "Labbook",
                "metadata": {
                    "name": "bgp-convergence-test-case-1",
                    "description": "Test BGP convergence time under link failure scenarios",
                    "author": "Network Engineering Team",
                    "tags": ["bgp", "fault-tolerance", "convergence"]
                }
            }
        }

    @property
    def name(self) -> str:
        """Get experiment name from metadata"""
        return self.metadata.get("name", "")

    @property
    def description(self) -> str:
        """Get experiment description from metadata"""
        return self.metadata.get("description", "")

    @property
    def author(self) -> Optional[str]:
        """Get experiment author from metadata"""
        return self.metadata.get("author")

    @property
    def tags(self) -> List[str]:
        """Get experiment tags from metadata"""
        return self.metadata.get("tags", [])

    @property
    def version(self) -> str:
        """Get labbook version (apiVersion)"""
        return self.api_version

