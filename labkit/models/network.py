"""
Network topology models for Labbook specification
"""

from typing import List, Dict, Any, Optional, Union
from enum import Enum
from pydantic import Field, validator, model_validator
from .base import BaseLabbookModel, ValidationError


class InterfaceMode(str, Enum):
    """Interface working modes"""
    DIRECT = "direct"
    SWITCHED = "switched" 
    GATEWAY = "gateway"
    HOST = "host"


class VolumeMount(BaseLabbookModel):
    """Volume mount configuration"""
    source: str = Field(..., description="Source path")
    destination: str = Field(..., description="Destination path")
    mode: str = Field(default="rw", description="Mount mode (rw, ro, etc.)")


class Interface(BaseLabbookModel):
    """Network interface definition"""
    name: str = Field(..., description="Interface name")
    mode: InterfaceMode = Field(..., description="Interface working mode")
    ip: Optional[Union[str, List[str]]] = Field(None, description="IP address(es)")
    gateway: Optional[str] = Field(None, description="Gateway interface (for host mode)")
    
    @validator('gateway')
    def validate_gateway(cls, v, values):
        if v is not None and values.get('mode') != InterfaceMode.HOST:
            raise ValueError('Gateway field is only valid for host mode interfaces')
        return v


class Node(BaseLabbookModel):
    """Compute node definition"""
    id: str = Field(..., description="Node identifier")
    image: str = Field(..., description="Docker image to use")
    interfaces: List[Interface] = Field(..., description="Network interfaces")
    volumes: Optional[List[Union[str, VolumeMount]]] = Field(None, description="Volume mounts")
    
    @validator('volumes')
    def validate_volumes(cls, v):
        if v is None:
            return v
        
        validated_volumes = []
        for volume in v:
            if isinstance(volume, str):
                # Parse Docker-style shorthand: "src:dest:mode"
                parts = volume.split(':')
                if len(parts) == 2:
                    validated_volumes.append(VolumeMount(source=parts[0], destination=parts[1]))
                elif len(parts) == 3:
                    validated_volumes.append(VolumeMount(source=parts[0], destination=parts[1], mode=parts[2]))
                else:
                    raise ValueError(f'Invalid volume format: {volume}')
            else:
                validated_volumes.append(volume)
        
        return validated_volumes


class Switch(BaseLabbookModel):
    """Virtual switch definition (L2 broadcast domain)"""
    id: str = Field(..., description="Switch identifier")
    description: Optional[str] = Field(None, description="Switch description")


class Link(BaseLabbookModel):
    """Logical communication path between nodes"""
    endpoints: List[str] = Field(..., description="Node interface endpoints")
    switch: Optional[str] = Field(None, description="Associated switch for switched connections")
    
    @validator('endpoints')
    def validate_endpoints(cls, v):
        if len(v) != 2:
            raise ValueError('Link must have exactly 2 endpoints')
        return v


class ImageSource(BaseLabbookModel):
    """Docker image source definition"""
    registry: Optional[str] = Field(None, description="Registry URL")
    tar: Optional[str] = Field(None, description="Local tar file path")
    
    @validator('registry', 'tar')
    def validate_source(cls, v, values):
        if v is None and not any(values.values()):
            raise ValueError('Image source must specify either registry or tar')
        return v


class Topology(BaseLabbookModel):
    """Network topology definition"""
    images: Dict[str, ImageSource] = Field(..., description="Image source definitions")
    nodes: List[Node] = Field(..., description="Compute nodes")
    switches: List[Switch] = Field(..., description="Virtual switches")
    links: List[Link] = Field(..., description="Logical links")
    
    @model_validator(mode='after')
    def validate_topology(self):
        """Validate topology consistency"""
        nodes = self.nodes
        switches = self.switches
        links = self.links
        
        # Validate node IDs are unique
        node_ids = [node.id for node in nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValidationError("Node IDs must be unique")
        
        # Validate switch IDs are unique
        switch_ids = [switch.id for switch in switches]
        if len(switch_ids) != len(set(switch_ids)):
            raise ValidationError("Switch IDs must be unique")
        
        # Validate link endpoints reference valid nodes
        for link in links:
            for endpoint in link.endpoints:
                if endpoint not in node_ids:
                    raise ValidationError(f"Link endpoint '{endpoint}' references non-existent node")
        
        # Validate link switches reference valid switches
        for link in links:
            if link.switch and link.switch not in switch_ids:
                raise ValidationError(f"Link switch '{link.switch}' references non-existent switch")
        
        return self 